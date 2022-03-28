#!/usr/bin/env python3

import argparse
import os

def get_dict(lst, d):
    i = 0
    while i < len(lst):
        #print(i)
        s = lst[i]
        if "{" in s:
            key = s.strip().split()[0]
            start = i + 1
            end = start
            occ = 1 #open curly brace count
            while (occ != 0):
                if "{" in s:
                    occ += 1
                if "}" in s:
                    occ -= 1
                end += 1
                i += 1
                if i< len(lst):
                    s = lst[i]
                else:
                    break
            #print("recursive call")
            d2 = {}
            lst2 = lst[start:end]
            get_dict(lst2,d2)
            d[key] = d2
        #base case
        else:
            key = s.strip()
            d[key] = None
        i+= 1
    return




def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('config_filepath',type=str, help='Path for a Juniper configuration file')
    parser.add_argument('output_path',type=str, help='Path in which to store the parts of the configuration')
    arguments = parser.parse_args()

    # Create output directory
    os.makedirs(arguments.output_path, exist_ok=True)

    # Open configuration file
    with open(arguments.config_filepath, 'r') as cfg_file:
        # TODO: iterate over configuration file and find sections

        # Sample code for writing to file
        '''section_name = "interfaces"
        section_contents = "interfaces {\n    testing\n}"'''
        section_name = arguments.config_filepath.split("/")[-1][0:-4] + "_dict"
        lst = cfg_file.read().split("\n")
        d = {}
        get_dict(lst, d)
        section_contents = str(d)
        with open(os.path.join(arguments.output_path, section_name+".cfg"), 'w') as out_file:
            out_file.write(section_contents)

if __name__ == "__main__":
    main()