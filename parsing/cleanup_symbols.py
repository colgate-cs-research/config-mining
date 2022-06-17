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

# Function for taking the union of lists
def union(l1, l2):
    l3 =  l1.copy()
    for el in l2:
        if el not in l1:
            l3.append(el)
    return l3


# Function to determine a type may not be a type because there are very few names associated with it
# Do we really need a function for this?
# It sounds like we just need a threshold for how many "names" a "type" needs to be associated with
# in order to be considered a "type", 
# which is just one if-statement and maybe a final variable the hardcoded threshold?

def main():
    start = time.time()

    # parser = argparse.ArgumentParser(description='Get the list of most similar neighbors')
    # parser.add_argument('inverted_path', help='Path for a file (or directory) containing a JSON representation of configuration(s)')
    # parser.add_argument('out_path', help='Name of file (or directory) to write JSON file(s) containing keywords')
    # output path for inverted_cleaned.json files
    # arguments = parser.parse_args()


    # test for union
    # l1 = ['abc', 'def', 'ghi']
    # l2 = ['ghi', 'lmn']
    # print(union(l1, l2))

   
    end = time.time()
    print("Time taken: " + str(end - start))




if __name__ == "__main__":
    main()