#!/usr/bin/env python3

import argparse
import fileinput
import os

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('configs_path', help='Path to directory of Aruba configs')
    arguments = parser.parse_args()
    
    # Parse each configuration
    for filename in sorted(os.listdir(arguments.configs_path)):
        node = filename.replace(".colgate.edu.json", "")
        print(node)
        infilepath = os.path.join(arguments.configs_path, filename)
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