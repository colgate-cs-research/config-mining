#!/usr/bin/env python3

import argparse
import json
import os
import sys

association_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.dirname(association_dir))
import analyze

def main():
    #parsing command-line arguments
    parser = argparse.ArgumentParser(description='Extract selected results from confidence output')
    parser.add_argument('confidence_path', help='Path for a file (or directory) containing a JSON representation of confidence results')
    parser.add_argument('out_path', help='Name of file (or directory) to write JSON file(s) containing selected confidence results')
    parser.add_argument("-c", "--confidence", type=float, default=1.0, help='Minimum confidence')
    parser.add_argument("-n", "--numerator", type=int, default=1, help='Minimum numerator')
    parser.add_argument("-d", "--denominator", type=int, default=1, help='Minimum denominator')

    arguments = parser.parse_args()
    analyze.process_configs(filter_confidence, arguments.confidence_path, arguments.out_path, arguments)

def filter_confidence(infile_path, outfile_path, arguments):
    print("Current working FILE: "+infile_path)
    with open(infile_path, 'r') as infile:
        all = json.load(infile)

    selected = []
    for result in all:
        if (result["c"] is not None and result["c"] >= arguments.confidence
            and result["n"] >= arguments.numerator
            and result["d"] >= arguments.denominator):
            selected.append(result)

    with open(outfile_path, 'w') as outfile:
        json.dump(selected, outfile, indent=4)

if __name__ == "__main__":
    main()