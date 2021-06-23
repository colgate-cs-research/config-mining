import argparse
import json
from analyze_keywords import load_keywords, count_keywords, get_common_keywords
import analyze_refs

#how many have the ospf over all the interfaces
def keywords_to_ospf(file, keyword):
    config = load_keywords(file)
    interface_keyword_dict = {}
    count_keywords(config, "interfaces", interface_keyword_dict)
    common_keywords = get_common_keywords(interface_keyword_dict, threshold=10)
    keywords_to_ospf_dict = {}
    ospf_interfaces = []

    for ospf in config["ospf"].values():
        interfaces = ospf["interfaces"]
        for interface in interfaces:
            ospf_interfaces.append(interface)

    for iface_name in config["interfaces"]:
        iface_keyword = 0
        iface_keyword_ospf = 0
        result = []
        iface_words = config["interfaces"][iface_name]
        for word in common_keywords:
            if word in iface_words:
                iface_keyword += 1
                if iface_name in ospf_interfaces:
                    iface_keyword_ospf += 1

        result.append(iface_keyword_ospf) 
        result.append(iface_keyword)
        keywords_to_ospf_dict[iface_name] = result

    return keywords_to_ospf_dict


def main():
    dictionary = keywords_to_ospf("/shared/configs/northwestern/configs_json/core1.json", "network")
    #print(dictionary)


if __name__ == "__main__":
    main()