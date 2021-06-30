import argparse
import json
from analyze_keywords import load_keywords, count_keywords, get_common_keywords, interface_ip_dictionary
import analyze_refs 
import analyze
import ipaddress


def ospf_interfaces(config):
    ospf_interfaces = []

    for ospf in config["ospf"].values():
        interfaces = ospf["interfaces"]
        for interface in interfaces:
            ospf_interfaces.append(interface)
    return ospf_interfaces


#Association rule: If the interface has a specific keyword, does that interface also run ospf
#Returns a dictionary of interfaces as the key and a list of two numbers to determine the confidence
#The first number is if the interface has the keyword and runs ospf and the second number is if the interface has the keyword
def keywords_to_ospf(config_file, keyword_file):
    keywords = load_keywords(keyword_file)
    interface_keyword_dict = {}
    count_keywords(keywords, "interfaces", interface_keyword_dict)
    common_keywords = get_common_keywords(interface_keyword_dict, threshold=10)
    keywords_to_ospf_dict = {}
    
    with open(config_file, 'r') as cf:
        config = json.load(cf)
    ospf_interface = ospf_interfaces(config)

    for word in common_keywords:
        iface_keyword = 0
        iface_keyword_ospf = 0
        for iface_name in keywords["interfaces"]:
            iface_words = keywords["interfaces"][iface_name]
            if word in iface_words:
                iface_keyword += 1
                if iface_name in ospf_interface:
                    iface_keyword_ospf += 1

        keywords_to_ospf_dict[word] = [iface_keyword_ospf, iface_keyword]

    return keywords_to_ospf_dict

def make_ospf_interface_dictionary(file):
    with open(file, "r") as infile:
        config = json.load(infile)

    ospf_interface_dictionary = {}
    for ospf in config["ospf"].values():
        for interface in ospf["interfaces"]:
            ospf_interface_dictionary[interface] = ospf["name"]

    return ospf_interface_dictionary

def analyze_configuration(in_paths, out_path, extra=None):
    config_file, keyword_file = in_paths
    #config = load_keywords(file)
    dictionary = keywords_to_ospf(config_file, keyword_file)
    rules = []
    for keyword, values in dictionary.items():
        rule = analyze.create_rule("iface has keyword "+keyword+" => iface runs OSPF", values[0], values[1])
        rules.append(rule)

    analyze.write_to_outfile(out_path, rules)
    #ip_dictionary = interface_ip_dictionary(file)
    #ospf_dictionary = make_ospf_interface_dictionary(config)

#You use interfaces running OSPF to construct the range, then you compute:
#Numerator = number of interfaces in range that run OSPF
#Denominator = number of interfaces in range
def address_in_range_ospf(file):
    iface_ipaddress_dictionary = interface_ip_dictionary(file)
    ospf_dictionary = make_ospf_interface_dictionary(file)
    ip_list = []
    for interface in ospf_dictionary:    
        for iface, ip in iface_ipaddress_dictionary.items():
            if interface == iface:
                ip_list.append(ip)

    ip_range = [min(ip_list), max(ip_list)]
    interfaces_inrange_ospf = analyze_refs.interfaces_in_range(ip_list, ip_range)
    numerator = len(interfaces_inrange_ospf)
    denom = len(analyze_refs.interfaces_in_range(iface_ipaddress_dictionary.values(), ip_range))

    return numerator, denom

def main():
    file = "/shared/configs/uwmadison/2014-10-core/configs_json/r-432nm-b3a-1-core.json"
    address_in_range_ospf(file)

    #parsing command-line arguments
    '''
    parser = argparse.ArgumentParser(description='Analyze confidence for OSPF')
    parser.add_argument('config_path', help='Path for a file (or directory) containing a JSON representation of configuration(s)')
    parser.add_argument('keyword_path', help='Path for a file (or directory) containing a JSON representation of keyword(s)')
    parser.add_argument('out_path', help='Name of file (or directory) to write JSON file(s) containing vlan confidence values')

    arguments = parser.parse_args()
    analyze.process_configs(analyze_configuration, [arguments.config_path, arguments.keyword_path], arguments.out_path)
    '''



if __name__ == "__main__":
    main()