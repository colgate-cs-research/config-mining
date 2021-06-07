#!/usr/bin/env python3

import argparse
import glob
import json
import os

def main():
    #parsing command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('config_path', help='Path for a file (or directory) containing a JSON representation of configuration(s)')
    parser.add_argument('out_path', help='Name of file (or directory) to write to')

    arguments = parser.parse_args()
    process_configs(arguments.config_path,arguments.out_path)

def process_configs(config_path,out_path):
    print("INPUT: "+config_path+" OUTPUT: "+out_path)
    if os.path.isfile(config_path):
        print("Input is a file")
        get_description(config_path, out_path)
    else:
        if os.path.isdir(out_path):
            files = glob.glob(config_path + '/**/*.json', recursive=True)
            for file in files:
                print("Current working FILE: "+file)
                get_descriptions(file,os.path.join(out_path, os.path.basename(file).replace(".json", ".out")))
        else:
            print("ERROR: input path is a directory; output path is not a directory")

#returns a dictionary with {interface name: [list of words in description]} 
def get_descriptions(file, outf):
    # Load config
    with open(file, "r") as infile:
        config = json.load(infile)
    desc_dict = {}
    vlan_names = []

    # Iterate over interfaces
    for iface in config["interfaces"].values():
        iName = iface["name"]
        if (iface["description"] is not None):
            desc_dict[iName] = iface["description"].split()

    # Iterate over VLANs
    for vlan in config["vlans"].values():
        vlan_names.append(vlan["name"])

    with open(outf, 'w') as outfile:
        outfile.write("desc_dict\n")
        json.dump(desc_dict, outfile, indent = 4)

        outfile.write("\n\n-----------------------------------\n")

        outfile.write("vlan_names\n")
        outfile.write(str(vlan_names))

    return desc_dict, vlan_names


if __name__ == "__main__":
    main()