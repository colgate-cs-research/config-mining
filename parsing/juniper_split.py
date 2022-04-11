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
            key = line.split(' ')[0];
            if "[" in line and line[-1] == "]":
                values = line.split('[')[1].strip()
                values = values.split(']')[0].strip()
                value = values.split(' ')
            else:
                if (len(line.split(' ')) > 1):
                    value = ' '.join(line.split(' ')[1:])
                else:
                    value = None
            dict[key] = value
        elif line[-2:] == "*/":
            key = line.strip()
            dict[key] = None
        else:
            print("!Unhandled line: " + line)
        i += 1

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
        lst = cfg_file.read().split("\n")
        d = {}
        get_dict(lst, 0, len(lst)-1, d)
        with open(os.path.join(arguments.output_path, os.path.basename(arguments.config_filepath)), 'w') as out_file:
            json.dump(d, out_file, indent=4, sort_keys=True)

if __name__ == "__main__":
    main()
