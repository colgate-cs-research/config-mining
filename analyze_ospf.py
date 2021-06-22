import argparse
import json
from analyze_keywords import load_keywords, count_keywords, get_common_keywords
import analyze_refs


def keywords_to_ospf(file, keyword):
    config = load_keywords(file)
    interface_keyword_dict = {}
    count_keywords(config, "interfaces", interface_keyword_dict)
    common_keywords = get_common_keywords(interface_keyword_dict, threshold=10)

    if keyword in common_keywords: # interface runs ospf
        return 1
        

def main():
    keywords = keywords_to_ospf("/shared/configs/northwestern/configs_json/core1.json", "address")
    print(keywords)

if __name__ == "__main__":
    main()