#!/usr/bin/env python3

import argparse
import os
import json

def find_match(symbols, lst, start, end):
    """Find index of matching curly brace, square bracket, etc."""
    occ = 1
    i = start + 1
    while (occ != 0 and i <= end):
        line = lst[i]
        if symbols[0] in line:
            occ += 1
        if symbols[1] in line:
            occ -= 1
        i += 1
    return i-1

def get_dict(lst, start, end, dict):
    """Create dictionary based on subset of lines"""
    i = start
    while i <= end:
        line = lst[i]
        if "{" in line:
            key = line.split('{')[0].strip()
            brace_start = i
            brace_end = find_match("{}", lst, i, end)
            subdict = {}
            get_dict(lst, brace_start + 1, brace_end - 1, subdict)
            dict[key] = subdict
            i = brace_end
        elif line[-1] == ';':
            line = line.strip(' ;')
            key = line
            # for lists of things as values for keys
            if "[" in line and line[-1] == "]":
                key = line.split('[')[0].strip();
                values = line.split('[')[1].strip()
                values = values.split(']')[0].strip()
                value = values.split(' ')
            else:
                if (len(line.split(' ')) > 1):
                    line = line.split(' ')
                    # the key is more than one word long
                    # if "\"" in line[-1]:
                    #     key = ' '.join(line[0:-1])
                    #     value = line[-1]
                    if len(line)==2 and line[0] not in dict:
                        key = line[0]
                        value = line[1]
                    else:
                        key = ' '.join(line)
                        value = None
                else:
                    value = None
            if key in dict:
                print("!Duplicate key {} on line {}".format(key, i))
            dict[key] = value

        # uncomment to include comments from config files in the .json file
        # elif line[-2:] == "*/":
        #     key = line.strip()
        #     dict[key] = None

        else:
            print("!Unhandled line {}: {}".format(i+1, line))
        i += 1

def jsonify_config(config_filepath, output_dir):
    """Create a JSON-ified version of a single Juniper configuration"""
    print("JSONifying {}...".format(os.path.basename(config_filepath)))
    with open(config_filepath, 'r') as cfg_file:
        lst = cfg_file.read().split("\n")

        # to debug
        # print('start')
        # for l in lst:
        #     print(l)
        # print('end')

        d = {}
        get_dict(lst, 0, len(lst)-1, d)
        with open(os.path.join(output_dir, os.path.basename(config_filepath).replace(".cfg", ".json")), 'w') as out_file:
            json.dump(d, out_file, indent=4, sort_keys=False)

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('config_path',type=str, help='Path to a (directory of) Juniper configuration file(s)')
    parser.add_argument('output_dir',type=str, help='Directory in which to store the JSONified configuration(s)')
    arguments = parser.parse_args()

    # Create output directory
    os.makedirs(arguments.output_dir, exist_ok=True)

    # Determine whether to process a single configuration or a directory of configurations
    if os.path.isfile(arguments.config_path):
        jsonify_config(arguments.config_path, arguments.output_dir)
    else:
        for filename in os.listdir(arguments.config_path):
            jsonify_config(os.path.join(arguments.config_path, filename), arguments.output_dir)




if __name__ == "__main__":
    main()
