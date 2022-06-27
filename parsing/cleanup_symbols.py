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


# function to find stuff like the common_starts elements
def longest_shared_sequence(keyword1,keyword2):
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

 
# Function for aliasing
def is_alias(s1, s2, inverted_table, symbol_table):
    assert(s1!=s2)
    smaller = s1
    bigger = s2
    if len(s1) > len(s2):
        smaller = s2
        bigger = s1
    if (smaller in bigger) or len(longest_shared_sequence(smaller,bigger))>=5:
        names1 = set(inverted_table[smaller])
        names2 = set(inverted_table[bigger])
        names3 = list(names1.intersection(names2))
        if len(names3) > 1:
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

def remove_redundant_types(inverted_table, symbol_table):
    nodes_removed = 0
    types_to_remove = []
    for key in inverted_table:
        lst = inverted_table[key]
        if len(lst) < 4:
            #print(key + ": " + str(lst))
            types_to_remove.append(key)

    for typ in types_to_remove:
        lst = inverted_table[typ]
        inverted_table.pop(typ) #remove from inverted table
        #remove from symbol table
        for name in lst:
            symbol_table[name].remove(typ)
            nodes_removed += 1

    #print("Nodes removed: " + str(nodes_removed))


def infer_type_aliases(inverted_table, symbol_table):
    alias_dict = {}
    alias_typs = []
    typ_lst = list(inverted_table.keys())
    #print("Type list: " + str(typ_lst))

    for i in range(len(typ_lst)):
        if typ_lst[i] not in alias_typs:
            for j in range(i+1,len(typ_lst)):
                if is_alias(typ_lst[i], typ_lst[j],inverted_table, symbol_table):
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
    typs_kept = list(alias_dict.keys())

    #print(pprint.pformat(alias_dict))
    return alias_dict


def remove_type_aliases(inverted_table, symbol_table):
    aliases = infer_type_aliases(inverted_table, symbol_table)
    inverted_aliases = invert_table(aliases)
    #print(inverted_aliases)

    for key in aliases:
        for alias in aliases[key]:
            # fix the inverted table
            names_to_transfer = []
            set1 = set()
            if alias in inverted_table:
                names_to_transfer = inverted_table[alias]
                inverted_table.pop(alias)
            else:
                print("Weird type1:" + alias)
            if key in inverted_table:
                set1 = set(inverted_table[key])
            else:
                print("Weird type2: " + key)
            set2 = set(names_to_transfer)
            lst = list(set1.union(set2))
            aliases[key] = lst
            #inverted_table[key] += names_to_tranfer

            #fix the symbol table

def fix_address(inverted_table, symbol_table):
    inverted_table["_address"] = []
    toRemove = []
    for key in inverted_table:
        names = inverted_table[key]
        names2 = is_all_addr(names)
        if (len(names2) > 0):
            inverted_table["_address"] += names2
            toRemove.append(key)  # alias is being removed by the old key is not being stored anywhere
            for name in names:
                if key in symbol_table[name]:
                    symbol_table[name].remove(key)

    for key in toRemove:
        inverted_table.pop(key)

# helper function for fix_address
def is_all_addr(lst):
    to_return = []
    count_not_ip = 0
    for el in lst:
        if (el != ""):
            l = el.strip().split('.')
            if len(l) >= 4:
                if (l[2]==''):
                    l[2] += '0'
                elif (len(l) > 4) and (l[3] ==  ""):
                    l.remove("")
                s = (".").join(lst)
                try:
                    ip = ipaddress.ip_interface(s)
                    to_return.append(ip)
                except:
                    count_not_ip += 1
    if count_not_ip == 0:
        print(to_return)
        return to_return
    return []


def main():
    start = time.time()
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Cleanup inferred symbols")
    #parser.add_argument('configs_path', help='Path to directory of configurations')
    parser.add_argument('symbols_dir', help='Path to directory containing symbol files')
    #parser.add_argument('output_dir', help='Path to directory in which to store output')
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
    new_symbol_table = invert_table(inverted_table)
    # for key in symbol_table:
    #     symbol_table[key].sort()
    # for key in new_symbol_table:
    #     new_symbol_table[key].sort()
    # print(symbol_table==new_symbol_table)
    # k1 = list(symbol_table.keys())
    # k1.sort()
    # k2 = list(new_symbol_table.keys())
    # k2.sort()
    # print(k2==k1)
    # print(len(k1))
    # print(len(k2)) # THEY DON'T HAVE THE SAME SET OF KEYS, DON'T USE THE INVERT FUNCTION TO REVERSE IT
    #print(symbol_table)
    #print(new_symbol_table)

    # call functions here
    #print(len(list(symbol_table.keys())))

    #print("Number of keys in inverted_table BEFORE removing alias types: ",  end = "")
    #print(len(list(inverted_table.keys())))
    remove_type_aliases(inverted_table,symbol_table)
    #print("Number of keys in inverted_table AFTER removing alias types: ",  end = "")
    #print(len(list(inverted_table.keys())))


    #print("Keys in inverted_table BEFORE removing types with less than 10 instances: ",  end = "")
    #print(len(list(inverted_table.keys())))
    remove_redundant_types(inverted_table, symbol_table)
    #print(len(list(symbol_table.keys())))
    #print("Keys in inverted_table AFTER removing types with less than 10 instances: ",  end = "")
    #print(len(list(inverted_table.keys())))

    # function for special case of 
    #print("Keys in inverted_table BEFORE aggregating addresses: ",  end = "")
    #print(len(list(inverted_table.keys())))
    fix_address(inverted_table, symbol_table)
    #print("Keys in inverted_table AFTER aggregating addresses: ",  end = "")
    #print(len(list(inverted_table.keys())))
    

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