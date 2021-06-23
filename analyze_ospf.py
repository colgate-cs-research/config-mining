import argparse
import json
from analyze_keywords import load_keywords, count_keywords, get_common_keywords, interface_ip_dictionary
import analyze_refs


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
def keywords_to_ospf(file, keyword):
    config = load_keywords(file)
    interface_keyword_dict = {}
    count_keywords(config, "interfaces", interface_keyword_dict)
    common_keywords = get_common_keywords(interface_keyword_dict, threshold=10)
    keywords_to_ospf_dict = {}
    ospf_interface = ospf_interfaces(config)

    for iface_name in config["interfaces"]:
        iface_keyword = 0
        iface_keyword_ospf = 0
        result = []
        iface_words = config["interfaces"][iface_name]
        for word in common_keywords:
            if word in iface_words:
                iface_keyword += 1
                if iface_name in ospf_interface:
                    iface_keyword_ospf += 1

        result.append(iface_keyword_ospf) 
        result.append(iface_keyword)
        keywords_to_ospf_dict[iface_name] = result

    return keywords_to_ospf_dict

def make_ospf_interface_dictionary(config):
    ospf_interface_dictionary = {}
    for ospf in config["ospf"].values():
        interfaces = ospf["interfaces"]
        ospf_interface_dictionary[ospf["name"]] = interfaces

    return ospf_interface_dictionary


def address_in_range_ospf(file):
    iface_ipaddress_dictionary = interface_ip_dictionary(file)
    ospf_dictionary = make_ospf_interface_dictionary(file)

    range_dictionary,_ = keyword_ipaddress_range(ospf_interface_dict, interface_IPaddress_dict)
    print(range_dictionary)

def main():
    file = "/shared/configs/northwestern/configs_json/core1.json"
    config = load_keywords(file)
    dictionary = keywords_to_ospf("/shared/configs/northwestern/configs_json/core1.json", "network")
    ip_dictionary = interface_ip_dictionary(file)
    ospf_dictionary = make_ospf_interface_dictionary(config)
    #print(ospf_dictionary)
    #address_in_range_ospf(config)


if __name__ == "__main__":
    main()