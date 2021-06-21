#!/usr/bin/env python3

import analyze_refs
import argparse
import json
import analyze

#returns a list of keywords
def load_keywords(file):
    # Load config
    with open(file, "r") as infile:
        keywords = json.load(infile)

    #print((keywords)) # keys: 'interfaces', 'acls'
    #print((keywords["interfaces"])) #keys: Vlan18, Vlan...
    #print((keywords["interfaces"]["Vlan18"])) # list of words
    #print(len(keywords["interfaces"]))
    return keywords

def count_keywords(keywords, stanza, all_words): #stanza="interfaces"
    for iface_name in keywords[stanza]:
        iface_words = keywords[stanza][iface_name]
        for word in iface_words:
            if word not in all_words:
                all_words[word] = 1
            else:
                all_words[word] += 1

def get_common_keywords(all_words, threshold=10):
    common_words = []
    for word, count in all_words.items():
        if count >= threshold:
            common_words.append(word)

    return sorted(common_words)


    #1) interfaces have keywords keywords JSON file
    #2) ACLs have keywords keywords JSON file
    #3) interfaces have ACLs config JSON file
    #config JSON -> keywords.py -> keywords JSON
    #configs JSON & keywords JSON -> analyze_keywords.py -> confidence JSON
    #interface i has keyword k => interface i has ACL a
    #interface i has keyword k and ACL a has keyword k => interface i has ACL a

# For each common keyword, find all interfaces that have that keyword CREATE DICTIONARY, list of interface names
# For each common keyword, find all ACLs that have that keyword CREATE DICTIONARY
# TEST TO SEE IF THIS WORKS BY MAKING OWN DICTIONARY WITH WORDS ETC...
def keyword_stanza(words, keywords, stanza):
    keyword_item_dict = {}
    for word in words:
        item_list = []
        for item_name in keywords[stanza]:
            for keyword in keywords[stanza][item_name]:
                if keyword == word and item_name not in item_list:
                    item_list.append(item_name)
        keyword_item_dict[word] = item_list
    
    return keyword_item_dict 

# call iacl_match.intraconfig_refs to get mapping from interface names to applied ACLs
def interface_to_applied_ACLs(file):
    IfaceName2AppliedAclNames, _, _ = analyze_refs.intraconfig_refs(file)
    used_acls = []
    for acls in IfaceName2AppliedAclNames.values():
        for acl in acls.values():
            if acl not in used_acls:
                used_acls.append(acl)
    return IfaceName2AppliedAclNames, used_acls

# For each common keyword, for each interface, check if that interface's ACL exists in list of ACLs with that keyword
#interface i has keyword k => interface i has ACL a
def keyword_association(common_keywords, used_acls, interface_to_ACL, keyword_interface_dict):
    keyword_associations = {}
    #iterating by keyword
    for keyword in common_keywords:
        for acl in used_acls: # Iterates over all used ACLs
            keyword_associations[(keyword, acl)] = single_keyword_association(keyword, acl, interface_to_ACL, keyword_interface_dict)
           
    return keyword_associations

# For each common keyword, for each interface, check if that interface's ACL exists in list of ACLs with that keyword
#interface i has keyword k => interface i has ACL a
def single_keyword_association(keyword, acl, interface_to_ACL, keyword_interface_dict):
    all_three = 0
    antecedent = 0
    exceptions = []
    for device in keyword_interface_dict:
        for interface in keyword_interface_dict[device][keyword]:  # Iterates number of interfaces with keyword k              
            antecedent += 1
            if interface in interface_to_ACL[device] and acl in interface_to_ACL[device][interface].values(): 
                all_three += 1
            else:
                exceptions.append((device, interface))

    return (all_three, antecedent, exceptions)

#Returns a dictionary of interfaces associated with their IP addresses
#Returns a list of all the ip addresses from the interfaces within the file
def interface_ip_dictionary(cfile):
    IfaceName2address = {}
    with open(cfile, "r") as infile:
        config = json.load(infile)
    
    for iface in config["interfaces"].values():
        iName = iface["name"]
        if iface["address"] is not None:
            IP_address = iface["address"].split("/")[0]
            IfaceName2address[iName] = IP_address

    return IfaceName2address

#RULE
#interface's IP falls within a range => Specific keyword applied to an interface 

#returns two dictionaries
#keyword_range_dict{keyword: range of the IP's associated with the interfaces of that keyword}
#keyword_ip_list_dict{keword: list of IP's associated with the interfaces of that keyword}
def keyword_ipaddress_range(keyword_interface_dict, interface_IPaddress_dict):
    keyword_range_dict = {}
    keyword_ip_list_dict = {}

    # Iterate over all keywords and interfaces with those keywords
    for keyword, ilist in keyword_interface_dict.items():
        ip_list = []
        for interface in ilist:
            if interface in interface_IPaddress_dict:
                ip_address = interface_IPaddress_dict[interface]
                ip_list.append(ip_address)

        keyword_ip_list_dict[keyword] = ip_list
        ip_range = analyze_refs.compute_range(ip_list)
        if (ip_range is None):
            continue
        keyword_range_dict[keyword] = ip_range       
        
    return keyword_range_dict, keyword_ip_list_dict

#Returns a dictionary displaying the confidences of each keyword
def keyword_range_confidence(ip_list, keyword_range_dict, keyword_ip_list_dict):
    keyword_range_confidence_dict = {}

    for keyword in keyword_range_dict:
        confidence = []
        ip_range = keyword_range_dict[keyword]
        #out of the total ip addresses in the file which are in range
        interface_in_range = len(analyze_refs.interfaces_in_range(ip_list, ip_range))
        #know which ips are in range based on the ips in the dictionary associated with the keywords
        for keywords in keyword_ip_list_dict:
            if keyword == keywords:
                keyword_interfaces_in_range = len(keyword_ip_list_dict[keyword])
        
        #attach a list of the two values to the keyword in a dictionary 
        confidence.append(keyword_interfaces_in_range)
        confidence.append(interface_in_range)
        keyword_range_confidence_dict[keyword] = confidence

    return keyword_range_confidence_dict

def analyze_configuration(in_paths, out_path, threshold):
    print("Current working files: %s" % (in_paths))

    rules = []

    network_keywords = {}
    all_words = {}
    network_Keyword2IfaceName = {} #{device name : {keyword: interfaces}}
    network_IfaceName2AppliedAclNames = {}
    network_UsedAclNames = set()

    for device_in_paths in in_paths:
        config_path, keyword_path = device_in_paths

        # Load keywords for a device
        device_keywords = load_keywords(keyword_path)
        device_name = device_keywords["name"] 
        network_keywords[device_name] = device_keywords

        # Count keywords for a device
        count_keywords(device_keywords, "interfaces", all_words)

        #keyword_ACL_dictionary = keyword_stanza(common_iface_words, keywords, "acls")
        device_IfaceName2AppliedAclNames, device_UsedAclNames= interface_to_applied_ACLs(config_path)
        network_IfaceName2AppliedAclNames[device_name] = device_IfaceName2AppliedAclNames
        network_UsedAclNames.update(device_UsedAclNames)

    # Get common keywords
    common_iface_words = get_common_keywords(all_words, threshold)

    for device_name, device_keywords in network_keywords.items():
        # Get mapping from keywords to interface names
        device_Keyword2IfaceName = keyword_stanza(common_iface_words, device_keywords, "interfaces")
        network_Keyword2IfaceName[device_name] = device_Keyword2IfaceName

    keyword_dictionary = keyword_association(common_iface_words, network_UsedAclNames, network_IfaceName2AppliedAclNames, network_Keyword2IfaceName)
    
    for (keyword, acl), (numerator, denominator, exceptions) in keyword_dictionary.items():
        message = "C(interface has keyword '%s' -> ACL %s applied to interface)" % (keyword, acl)
        rules.append(analyze.create_rule(message, numerator, denominator, exceptions))

#    interface_IPaddress_dict = interface_ip_dictionary(config_path)
#    keyword_range, keyword_ip_list = keyword_ipaddress_range(keyword_interface_dictionary, interface_IPaddress_dict)
#    dictionary = keyword_range_confidence(interface_IPaddress_dict.values(), keyword_range, keyword_ip_list)
#    for keyword, (numerator, denominator) in dictionary.items():
#        ip_range = keyword_range[keyword]
#        message = "C(interface's IP falls within range %s => ACL %s applied to the interface)" % (ip_range, keyword)
#        rules.append(analyze.create_rule(message, numerator, denominator))

    analyze.write_to_outfile(out_path, rules)

def main():
    #parsing command-line arguments
    parser = argparse.ArgumentParser(description='Perform keyword-based analysis')
    parser.add_argument('config_path', help="Path for a file containing a JSON representation of a configuration")
    parser.add_argument('keyword_path', help="Path for a file containing a JSON representation of keywords (produced by keywords.py)")
    parser.add_argument('output_path', help="Path for a file containing a JSON representation of a configuration")
    parser.add_argument("-t", "--threshold", type=int, help="Minimum number of types a keyword must occur", default=10)

    arguments = parser.parse_args()

    analyze.process_configs(analyze_configuration, [arguments.config_path, arguments.keyword_path], arguments.output_path, arguments.threshold, True)

if __name__ == "__main__":
    main()