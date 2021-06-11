#!/usr/bin/env python3

import argparse
import glob
import json
import os
import nltk
from nltk.corpus import stopwords
import re

abbreviations = {
    "mgmt" : "management"
}

def main():
    #parsing command-line arguments
    parser = argparse.ArgumentParser(description='Extract keywords for interfaces and ACLs')
    parser.add_argument('config_path', help='Path for a file (or directory) containing a JSON representation of configuration(s)')
    parser.add_argument('out_path', help='Name of file (or directory) to write JSON file(s) containing keywords')

    arguments = parser.parse_args()
    nltk.download('stopwords')
    process_configs(arguments.config_path,arguments.out_path)

def process_configs(config_path,out_path):
    print("INPUT: "+config_path+" OUTPUT: "+out_path)
    if os.path.isfile(config_path):
        print("Input is a file")
        get_descriptions(config_path, out_path)
    else:
        if os.path.isdir(out_path):
            files = glob.glob(config_path + '/**/*.json', recursive=True)
            for file in files:
                print("Current working FILE: "+file)
                get_descriptions(file,os.path.join(out_path, os.path.basename(file)))
        else:
            print("ERROR: input path is a directory; output path is not a directory")

"""Get keywords from a phrase"""
def get_keywords(phrase, delims=[" "]):
    words = re.split("|".join(delims), phrase)
    words = [word.lower() for word in words]
    words = [word for word in words if not word in stopwords.words()]
    words = [(abbreviations[word] if word in abbreviations else word) for word in words]
    return words

"""Add keywords to a specific entry in a dictionary"""
def add_keywords(dictionary, key, words):
    if key not in dictionary:
        dictionary[key] = []
    for word in words:
        if word not in dictionary[key]:
            dictionary[key].append(word)

#returns a dictionary with {interface name: [list of words in description]} 
def get_descriptions(file, outf):
    # Load config
    with open(file, "r") as infile:
        config = json.load(infile)
    iface_dict = {}
    acl_dict = {}

    # Iterate over interfaces
    for iface in config["interfaces"].values():
        iName = iface["name"]
        if (iface["description"] is not None):
            add_keywords(iface_dict, iName, get_keywords(iface["description"]))

    # Iterate over VLANs
    for vlan in config["vlans"].values():
        iName = "Vlan%d" % vlan["num"]
        add_keywords(iface_dict, iName, get_keywords(vlan["name"], delims=[" ", "-"]))

    # Iterate over ACL names
    for name in config["acls"]:
        add_keywords(acl_dict, name, get_keywords(name, delims=[" ", "-"]))
        # Iterate over remarks
        for remark in config["acls"][name]["remarks"]:
            add_keywords(acl_dict, name, get_keywords(remark))

    aggregate = {
        "interfaces" : iface_dict,
        "acls" : acl_dict
    }

    with open(outf, 'w') as outfile:
        json.dump(aggregate, outfile, indent = 4)

    return iface_dict, acl_dict


if __name__ == "__main__":
    main()