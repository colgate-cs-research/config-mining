#!/usr/bin/env python3

import argparse
import fileinput
import ipaddress
import json
import os
import sys

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('snapshot_path', help='provide path to the network snapshot')
    arguments = parser.parse_args()

    # Determine paths
    configs_path = os.path.join(arguments.snapshot_path, "configs")
    
    # Parse each configuration
    for filename in sorted(os.listdir(configs_path)):
        node = filename.replace(".colgate.edu.json", "")
        print(node)
        infilepath = os.path.join(configs_path, filename)
        fix_aruba_json(infilepath)

def fix_aruba_json(filepath):
    with fileinput.FileInput(filepath, inplace='True') as conf_file:
        for line in conf_file:
            if "%2F" in line:
                line = line.replace("%2F","/")
            if '"cfg_version"' in line and line.count('"') != 4:
                pre, post = line.rstrip().split(':')
                print('{}: "{}",'.format(pre, post[1:-1]))
            elif '"name"' in line and line.count('"') != 4:
                pre, post = line.rstrip(",\n").split(':')
                print('{}: {}"{}'.format(pre, post[1:], ("," if line[-2] == "," else "")))
            else:
                print(line, end='')

if __name__ == "__main__":
    main()