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
    # first pass to see if they have similar letters
    if similar_letters(s1,s2):
        pass
    # FIXME
    # check if they are similar
    # or if they contain a similar sequence of characters
    return False 

# returns true is two strings have similar letters
# helper function for is_alias()
def similar_letters(s1, s2):
    list1 = list(set(s1))
    list2 = list(set(s2))
    similarity = 0
    for el in list1:
        if el in list2:
            similarity += 1
    if (similarity > 1): # might need to set threshold here instead of hardcoding the value
        return True
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