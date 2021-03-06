#!/usr/bin/python
import argparse
import ipaddress
import json
import networkx as nx
import os
import time
from queue import Queue
import logging
import pprint
import re

TYPES_PRESERVE_ARUBA = [
    "class",
]
TYPES_PRESERVE = TYPES_PRESERVE_ARUBA


# functions to find aliases that contain a subset of the names of a valid type 
# but do not mention the type in their section of the config
def is_names_total_subset(inverted_table):

    key_change_dict = {} # dictionary {alias_type: [list of possible "root types" that have all of the alias_type's names]}
    # values are lists instead of strings to allow for debugging, 
    # but ideally each list only have one element

    root_count_dict = {} # {root_types: number of times aliases refer to this root}
    key_lst = list(inverted_table.keys()) 

    for i in range(len(key_lst)):
        k1 = key_lst[i]

        # Skip over types that are already aliases
        if isinstance(inverted_table[k1], str):
            continue
            
        lst1 = set(inverted_table[k1])

        # Skip over types that are all numbers
        if all([name.isdigit() for name in lst1]):
            continue

        for j in range(len(key_lst)):
            k2 = key_lst[j]
            if k1==k2:
                continue #break

            # Skip over types that are already aliases
            if isinstance(inverted_table[k2], str):
                continue

            lst2 = set(inverted_table[k2])

            # Skip over types that are all numbers
            if all([name.isdigit() for name in lst2]):
                continue
            
            if lst1.issubset(lst2):
                if k2 not in root_count_dict:
                    root_count_dict[k2] = 0
                root_count_dict[k2] += 1
                if k1 not in key_change_dict:
                    key_change_dict[k1] = []
                key_change_dict[k1].append(k2)


    for key in key_change_dict:
        # pick the root that has the highest number of aliases, if there is more than one root
        if len(key_change_dict[key])>1:
            max_count = 0
            max_count_root = ""
            for el in key_change_dict[key]:
                if root_count_dict[el] > max_count:
                    max_count = root_count_dict[el]
                    max_count_root = el
            key_change_dict[key] = [max_count_root]

        # for debugging
        if len(key_change_dict[key])>0:
            logging.info("Names of type {} are a complete subset of type {}".format(key, key_change_dict[key][0]))

    # point to appropriate "root" type for each alias type
    # this is the step that actually changes the inverted_table
    for key in key_change_dict:
        if len(key_change_dict[key])==1:
            root_type = key_change_dict[key][0]
            alias_type_names = inverted_table[key]
            if isinstance(alias_type_names, str):
                continue
                #alias_type_names = inverted_table[alias_type_names]
            if isinstance(inverted_table[root_type], str):
                logging.error("!{} is already aliased to {}".format(root_type, inverted_table[root_type])) 
                continue
            inverted_table[root_type] = inverted_table[root_type] + alias_type_names
            inverted_table[key] = root_type


# function to find stuff like the common_starts elements
def longest_shared_sequence(keyword1, keyword2):
    """Returns the longest sequnece of characters that occurs in both strings"""
    longest_shared_seq = ""
    for i in range(len(keyword1)-1):
        for j in range(i+1,len(keyword1)):
            if keyword1[i:j] in keyword2 and len(keyword1[i:j])>len(longest_shared_seq):
                longest_shared_seq = keyword1[i:j]

    #logging.debug("\t\t words:{} {}| seq:{}| ".format(keyword1,keyword2,longest_shared_seq)) #commented out 6/24 11:30am
    return longest_shared_seq
            
def reduce_similarity(word,similar_words,min_len=3):
    to_return = []
    #print(type(similar_words))
    for i in similar_words:
        if len(longest_shared_sequence(word,i))>=min_len:
            to_return.append(i)
    return to_return

 
def is_alias(type1, type2, inverted_table):
    """Check if one symbol type (s1) is an alias of another symbol type (s2)"""
    assert(type1!=type2)
    smaller = type1
    bigger = type2
    if len(type1) > len(type2):
        smaller = type2
        bigger = type1

    # Symbol types are an alias if (1) one wholly contains the other 
    # or both contain the same sequence of 5 or more characters;
    # and (2) both contain at least one symbol_name in common
    if (smaller in bigger) or len(longest_shared_sequence(smaller, bigger))>=5:
        names1 = set(inverted_table[smaller])
        names2 = set(inverted_table[bigger])
        names_both = list(names1.intersection(names2))
        if names_both: 
            return True

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
                inverted_table[symbol_type] = []
            if symbol_name not in inverted_table[symbol_type]: #changed
                inverted_table[symbol_type].append(symbol_name)
    return inverted_table

def remove_small_types(inverted_table, symbol_table, threshold=4):
    """Remove symbol types with a small number of symbol names"""
    symbol_types = list(inverted_table.keys())
    for symbol_type in symbol_types:
        symbol_names = inverted_table[symbol_type]
        if isinstance(symbol_names, list) and len(symbol_names) < threshold and symbol_type not in TYPES_PRESERVE:
            logging.info("Remove type {} because it only has {} name(s)".format(symbol_type, len(symbol_names)))
            inverted_table.pop(symbol_type)
            for symbol_name in symbol_names:
                symbol_table[symbol_name].remove(symbol_type)

def infer_type_aliases(inverted_table):
    alias_dict = {}
    alias_typs = []
    typ_lst = sorted(inverted_table.keys(), key=len)
    #print("Type list: " + str(typ_lst))

    # Iterate over pairs of symbol_types
    for i in range(len(typ_lst)):
        if typ_lst[i] not in alias_typs:
            for j in range(i+1,len(typ_lst)):
                if is_alias(typ_lst[i], typ_lst[j],inverted_table):
                    logging.debug("{} and {} are aliases".format(typ_lst[i], typ_lst[j]))
                    old_key_lst = []
                    typ_to_keep = typ_lst[i]
                    alias_typ = typ_lst[j]
                    # which is the alias
                    if (len(typ_to_keep) > len(alias_typ)):
                        typ_to_keep = typ_lst[j]
                        alias_typ = typ_lst[i]
                    if (alias_typ in alias_dict):
                        old_key_lst = alias_dict[alias_typ]
                        alias_dict.pop(alias_typ)

                    alias_typs.append(alias_typ)

                    if typ_to_keep not in alias_dict:
                        alias_dict[typ_to_keep] = old_key_lst
                    alias_dict[typ_to_keep].append(alias_typ)

    return alias_dict

def remove_type_aliases(aliases, inverted_table, symbol_table):
    """Merge type aliases and create reference to primary type"""
    for primary_type in aliases:
        for alias in aliases[primary_type]:
            if isinstance(inverted_table[alias], str):
                logging.error("!{} is already aliased to {}".format(alias, inverted_table[alias]))
                continue

            names_to_transfer = set(inverted_table[alias])

            # Merge symbol names from alias with symbol names from primary type
            primary_names = set(inverted_table[primary_type])
            aliases[primary_type] = list(primary_names.union(names_to_transfer))

            # Remove alias type from symbol names
            for symbol_name in names_to_transfer:
                symbol_table[symbol_name].remove(alias)
            
            # Create reference to primary type
            inverted_table[alias] = primary_type

def fix_address(inverted_table, symbol_table):
    """Group all addresses under the special _address type"""
    all_addresses = []
    for symbol_type, symbol_names in inverted_table.items():
        # Skip over aliases
        if isinstance(symbol_names, str):
            continue

        if (is_all_addr(symbol_names)):
            logging.info("Type {} is an address type".format(symbol_type))
            all_addresses += symbol_names
            inverted_table[symbol_type] = "_address"
            for name in symbol_names:
                if symbol_type in symbol_table[name]:
                    symbol_table[name].remove(symbol_type)
                if "_address" not in symbol_table[name]:
                    symbol_table[name].append("_address")
    
    inverted_table["_address"] = all_addresses

def is_all_addr(list_of_names):
    """Checks if a list of symbol names only contains IP addresses"""
    for symbol_name in list_of_names:
        # Handle IPv4 address compression
        uncompressed_name = symbol_name.replace("inactive: ","")
        if (re.match("\d+\.\d+\.\.\d+\.\d+(/d+)?", symbol_name)):
            uncompressed_name = symbol_name.replace("..",".")
        elif (re.match("\d+\.\d+\.\.\d+(/d+)?", symbol_name)):
            uncompressed_name = symbol_name.replace("..",".0.")

        if (re.match("\d+\.\d+\.\d+\.\d+(/\d+)?", uncompressed_name)
            or re.match("\d+\.\d+\.\d+\.d(/\d+\.\d+\.\d+\.\d+)?", uncompressed_name)
            or re.match("("
                + "([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}"
                + "|([0-9a-fA-F]{1,4}:){1,7}:"
                + "|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}"
                + "|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}"
                + "|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}"
                + "|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}"
                + "|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}"
                + "|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})"
                + "|:((:[0-9a-fA-F]{1,4}){1,7}|:)"
                + ")(/\d+)?", uncompressed_name)):
            try:
                ipaddress.ip_interface(uncompressed_name)
            except:
                logging.debug("{} could not be parsed as an IPv4 interface address".format(uncompressed_name))
        else:
            return False
    return True

'''is_all_addr(["1.2.3.4", "12.34.56.78", "101.102.103.104", 
    "1.2.3.4/5", "1.2.3.4/24", "1.2.3.4/255.255.0.0",
    "10.11..1", "10.11..13/14", "10.11..12.13/14"])'''

def fix_description(inverted_table, symbol_table):
    """Group all descriptions under the special _description type"""
    all_descriptions = []
    for symbol_type, symbol_names in inverted_table.items():
        # Skip over aliases
        if isinstance(symbol_names, str):
            continue

        if symbol_type in ["description", "comment", "remark"]:
            logging.debug("{} is a description type".format(symbol_type))
            all_descriptions += symbol_names
            inverted_table[symbol_type] = "_description"
            for name in symbol_names:
                if symbol_type in symbol_table[name]:
                    symbol_table[name].remove(symbol_type)
                if "_description" not in symbol_table[name]:
                    symbol_table[name].append("_description")
    
    inverted_table["_description"] = all_descriptions

def prune_symbols(inverted_table, symbol_table):
    """Remove symbol names with no type"""
    symbol_names = list(symbol_table.keys())
    for symbol_name in symbol_names:
        if not symbol_table[symbol_name]:
            # Infer address type for symbol names that are addresses
            if is_all_addr([symbol_name]):
                inverted_table["_address"].append(symbol_name)
                symbol_table[symbol_name].append("_address")
            else:
                symbol_table.pop(symbol_name)
                logging.info("Removing name {} because it has no types".format(symbol_name))

def main():
    start = time.time()
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Cleanup inferred symbols")
    parser.add_argument('symbols_dir', help='Path to directory containing symbol files')
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

    logging.debug("Number of types BEFORE removing alias types: {}".format(len(inverted_table)))
    aliases = infer_type_aliases(inverted_table)
    logging.info("Type aliases:\n{}".format(pprint.pformat(aliases)))
    remove_type_aliases(aliases, inverted_table, symbol_table)
    logging.debug("Number of types AFTER removing alias types: {}".format(len(inverted_table)))

    logging.debug("Number of types BEFORE removing types with few names: {}".format(len(inverted_table)))
    remove_small_types(inverted_table, symbol_table)
    logging.debug("Number types AFTER removing types with few names: {}".format(len(inverted_table)))

    # function for special case of 
    #print("Keys in inverted_table BEFORE aggregating addresses: ",  end = "")
    #print(len(list(inverted_table.keys())))
    fix_address(inverted_table, symbol_table)
    #print("Keys in inverted_table AFTER aggregating addresses: ",  end = "")
    #print(len(list(inverted_table.keys())))

    fix_description(inverted_table, symbol_table)
    
    is_names_total_subset(inverted_table)

    prune_symbols(inverted_table, symbol_table)

    # Save results
    with open(os.path.join(arguments.symbols_dir, "inverted.json"), 'w') as inverted_file:
        json.dump(inverted_table, inverted_file, indent=4, sort_keys=True)

    # Save results
    with open(os.path.join(arguments.symbols_dir, "new_symbols.json"), 'w') as inverted_file:
        json.dump(symbol_table, inverted_file, indent=4, sort_keys=True)

    end = time.time()
    print("Time taken: " + str(end - start))

if __name__ == "__main__":
    main()
    