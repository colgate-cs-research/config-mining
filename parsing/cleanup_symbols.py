#!/usr/bin/python
import argparse
import ipaddress
import json
import networkx as nx
import os
import time
from queue import Queue
import logging


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

def invert_table(symbol_table):
    inverted_table = {}
    for symbol_name, symbol_types in symbol_table.items():
        for symbol_type in symbol_types:
            if symbol_type not in inverted_table:
                inverted_table[symbol_type] = set()
            inverted_table[symbol_type].add(symbol_name)
    return inverted_table

def main():
    start = time.time()
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Cleanup inferred symbols")
    #parser.add_argument('configs_path', help='Path to directory of configurations')
    parser.add_argument('symbols_dir', help='Path to directory containing symbol files')
    parser.add_argument('output_dir', help='Path to directory in which to store output')
    parser.add_argument('-v', '--verbose', action='count', help="Display verbose output", default=0)
    arguments = parser.parse_args()

    # module-wide logging
    if (arguments.verbose == 0):
        logging.basicConfig(level=logging.WARNING)
    elif (arguments.verbose == 1):
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)
    logging.getLogger(__name__)

    # Load symbols results
    with open(os.path.join(arguments.symbols_dir, "symbols.json"), 'r') as symbols_file:
        symbol_table = json.load(symbols_file)

    inverted_table = invert_table(symbol_table)

    # Save results
    with open(os.path.join(arguments.output_dir, "inverted.json"), 'w') as inverted_file:
        json.dump(inverted_table, inverted_file, indent=4, sort_keys=True)

    end = time.time()
    print("Time taken: " + str(end - start))

if __name__ == "__main__":
    main()