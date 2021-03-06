#!/usr/bin/env python3

import argparse
import json
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
import re
import analyze
import time
import os

abbreviations = {
    "bldg" : "building",
    "mgmt" : "management",
    "pub" : "public"
}

# list of common keyword beginnings
common_starts = ["student", "ems", "bg", "voip"]

def main():

    start = time.time()

    #parsing command-line arguments
    parser = argparse.ArgumentParser(description='Extract keywords for interfaces and ACLs')
    parser.add_argument('config_path', help='Path for a file (or directory) containing a JSON representation of configuration(s)')
    parser.add_argument('out_path', help='Name of file (or directory) to write JSON file(s) containing keywords')

    arguments = parser.parse_args()
    os.makedirs(arguments.out_path, exist_ok=True)
    analyze.process_configs(analyze_configuration, arguments.config_path, arguments.out_path)

    end = time.time()
    print()
    print("Time taken: " + str(end - start))
    print()

"""Get keywords from a phrase"""
def get_keywords(phrase, delims=[" "]):
    words = re.split("|".join(delims), phrase)
    words = [word.lower() for word in words]

    # Skip stop words
    words = [word for word in words if not word in stopwords.words()]

    # Skip single-character words
    words = [word for word in words if len(word) > 1]

    # Replace abbreviations
    for i in range(len(words)):
        word = words[i]
        if word in abbreviations:
            words[i] = abbreviations[word]
    return words

"""Add keywords to a specific entry in a dictionary"""
def add_keywords(dictionary, key, words):
    if key not in dictionary:
        dictionary[key] = []
    for word in words:
        if word not in dictionary[key]:
            dictionary[key].append(word)

def make_dict(word):
    d = {}
    inner_d = d
    for ch in word:
        inner_d[ch] = {}
        inner_d = inner_d[ch]
    return d

def analyze_configuration(file, outf, extra=None):
    # print("Current working FILE: " + file)
    # Load config
    name = os.path.basename(file).split(".")[0]
    with open(file, "r") as infile:
        config = json.load(infile)
    iface_dict = {}
    acl_dict = {}

    # dictionary -  keywords are keys and values are lists of ifaces and vlans the keyword appears in
    keyword_dict = {}
    # Iterate over interfaces
    for iface in config["interfaces"]:  # removed .values()
        iName = iface  #in juniper, the keys are the names of the ifaces
        if ("description" in config["interfaces"][iface]):
            desc = config["interfaces"][iface]["description"]
            keywords = get_keywords(desc, " ")
            for word in keywords:
                if word not in keyword_dict:
                    keyword_dict[word] = []
                keyword_dict[word].append(iName)

        if "unit" in config["interfaces"][iface]:
            units = config["interfaces"][iface]["unit"]
            if isinstance(units, str):
                pass
            else:
                for unit in units:
                    if ((isinstance(units[unit], dict)) and ("description" in units[unit])):
                        keywords = get_keywords(units[unit]["description"], " |")
                        for word in keywords:
                            if word not in keyword_dict:
                                keyword_dict[word] = []
                            keyword_dict[word].append("vlan_" + unit)

    # extract keywords that are variations of a common term (hardcoded in list common_starts on line 17-18)
    common_keyword_dict = {}
    for word2 in common_starts:
        common_keyword_dict[word2] = []
    
    keys_to_remove = []
    for word in keyword_dict:
        for word2 in common_starts:
            if word2 in word:
                if word not in keys_to_remove:
                    keys_to_remove.append(word)
                for iface_or_vlan in keyword_dict[word]:
                    (common_keyword_dict[word2]).append(iface_or_vlan)

    for word in common_keyword_dict:
        keyword_dict[word] = common_keyword_dict[word]

    for word in keys_to_remove:
        keyword_dict.pop(word)

    # final list of keywords for Ifaces and Vlans
    for word in keyword_dict:
        for iName in keyword_dict[word]:
            add_keywords(iface_dict, iName, [word])

    # Iterate over ACL names
    if "firewall" in config:
        if "family inet" in config["firewall"]:
            if "filter" in config["firewall"]["family inet"]:
                for acl in config["firewall"]["family inet"]["filter"]:
                    acl_attributes = config["firewall"]["family inet"]["filter"][acl]
                    if ("term" in acl_attributes) and (isinstance(acl_attributes["term"], dict)):
                        for term_name in acl_attributes["term"].keys():
                            add_keywords(acl_dict, acl, get_keywords(term_name, delims=[" ", "-"]))

    aggregate = {
        "interfaces" : iface_dict,
        "acls" : acl_dict,
        "name" : name
    }

    with open(outf, 'w') as outfile:
        json.dump(aggregate, outfile, indent = 4)

    return iface_dict , acl_dict


if __name__ == "__main__":
    main()
