#!/usr/bin/python
import argparse
import ipaddress
import json
import networkx as nx
import os
import time
from queue import Queue


# Function for aliasing
def is_alias(s1, s2):
    smalller = s1
    bigger = s2
    if len(s1) > len(s2):
        smaller = s2
        bigger = s1
    if smaller in bigger:
        return True
    # FIXME
    # check is they are similar
    # or if they contain a similar sequence of characters
    return False 


def main():
    start = time.time()

    # parser = argparse.ArgumentParser(description='Get the list of most similar neighbors')
    # parser.add_argument('inverted_path', help='Path for a file (or directory) containing a JSON representation of configuration(s)')
    # parser.add_argument('out_path', help='Name of file (or directory) to write JSON file(s) containing keywords')
    # output path for inverted_cleaned.json files
    # arguments = parser.parse_args()

   
    end = time.time()
    print("Time taken: " + str(end - start))




if __name__ == "__main__":
    main()