#!/usr/bin/env python3

import argparse
import json
from analyze_refs import intraconfig_refs

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

def get_common_keywords(keywords, stanza, threshold=10): #stanza="interfaces"
    all_words = {}
    for iface_name in keywords[stanza]:
        iface_words = keywords[stanza][iface_name]
        for word in iface_words:
            if word not in all_words:
                all_words[word] = 1
            else:
                all_words[word] += 1

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
    interface_to_ACL, _, _ = (intraconfig_refs(file))
    return interface_to_ACL

# For each common keyword, for each interface, check if that interface's ACL exists in list of ACLs with that keyword
#interface i has keyword k => interface i has ACL a
def keyword_association(interface_to_ACL, keyword_interface_dict, keyword_ACL_dict):
    keyword_associations = {}
    #iterating by keyword
    for keyword,interfaces_with_keyword in keyword_interface_dict.items():
        acls_with_keyword = keyword_ACL_dict[keyword]
        for ACL in acls_with_keyword:  # Iterates number of ACLs with keyword k 
            all_three = 0
            antecedent = 0
            for interface in interfaces_with_keyword:  # Iterates number of interfaces with keyword k              
                antecedent += 1
                if interface in interface_to_ACL and ACL in interface_to_ACL[interface].values(): 
                    all_three += 1
            keyword_associations[(keyword, ACL)] = (all_three, antecedent)
           
    return keyword_associations

def data_computation(keyword_interfaces):
    a={}
    a["message"]="C(Keyword ---> interface)"

    b={}
    b["message"]="C(Keyword ---> ACL)"

def write_to_outfile(filename, keyword_interfaces):
    with open(filename, 'w') as outfile:
        a = data_computation(keyword_interfaces)
        to_dump= [a,keyword_interfaces]
        json.dump(to_dump, outfile, indent=4, sort_keys=True)
    return 


def main():
    #parsing command-line arguments
    parser = argparse.ArgumentParser(description='Perform keyword-based analysis')
    parser.add_argument('keyword_path', help="Path for a file containing a JSON representation of keywords (produced by keywords.py)")
    parser.add_argument('config_path', help="Path for a file containing a JSON representation of a configuration")
    parser.add_argument("-t", "--threshold", type=int, help="Minimum number of types a keyword must occur", default=10)

    arguments=parser.parse_args()

    keywords = load_keywords(arguments.keyword_path)
    common_iface_words = get_common_keywords(keywords, "interfaces", arguments.threshold)
    keyword_interface_dictionary = keyword_stanza(common_iface_words, keywords, "interfaces")
    keyword_ACL_dictionary = keyword_stanza(common_iface_words, keywords, "acls")
    interface_to_ACLnames = interface_to_applied_ACLs(arguments.config_path)
    keyword_dictionary = keyword_association(interface_to_ACLnames, keyword_interface_dictionary, keyword_ACL_dictionary)

    #print(common_iface_words)
    #print(keyword_interface_dictionary)
    #print(keyword_ACL_dictionary)
    #print(interface_to_ACLnames)
    print(keyword_dictionary)

    

    #with open("output/analyze_keywords", 'w') as outfile:
        #keyword_ACL_dictionary

    write_to_outfile("output/analyze_keywords", keyword_interface_dictionary)

if __name__ == "__main__":
    main()