#!/usr/bin/env python3

import argparse
import json
import os
import pprint
import ipaddress

# FIXME
TOP_LEVEL_TYPES = [
    #"groups", 
    "interfaces", 
    "policy-options", 
    #"firewall", 
]
IGNORED_TYPES = [
]
TYPEDEFS = {
    "apply-groups" : "group",
}
SUB_TYPES_VALUES = [
]
SUB_TYPES_KEYS = [
    "unit",
    "interfaces",
    "policy-statement",
]

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('snapshot_path', help='provide path to the network snapshot')
    parser.add_argument('-v', '--verbose', action='store_true', help="Display verbose output")
    arguments = parser.parse_args()

    # Determine paths
    configs_path = os.path.join(arguments.snapshot_path, "configs_cleaned")
    
    # Parse each configuration
    symbol_table = {}
    for filename in sorted(os.listdir(configs_path)):
        node = filename.replace(".cfg", "")
        filepath = os.path.join(configs_path, filename)
        try:
            with open(filepath, "r") as config_file:
                config = json.load(config_file)
        except:
            print("Failed to parse {}".format(filepath))
            continue
        if (arguments.verbose):
            print("Processing {}...".format(node))
#        parse_config(config, symbol_table, arguments.verbose)
        parse_dict(config, ["ROOT"], arguments.verbose)
        break

    # Determine all types
#    types = set()
#    for symbol_types in symbol_table.values():
#        types.update(symbol_types)
#    pprint.PrettyPrinter().pprint(types)

    symbols_filepath = os.path.join(arguments.snapshot_path, "symbols.json")  
    with open(symbols_filepath, 'w') as symbols_file:
        json.dump(symbol_table, symbols_file, indent=4, sort_keys=True)

def parse_config(config, symbol_table, verbose=False):
    # Iterate over top-level types of interest (e.g., ACLs, interfaces, etc.)
    for symbol_type in TOP_LEVEL_TYPES:
        if symbol_type not in config:
            continue
        if (verbose):
            print("\tProcessing {}...".format(symbol_type))
        if symbol_type in SUB_TYPES_KEYS:
            extract_symbols_key_name(symbol_type, config[symbol_type], symbol_table)
        else:
            extract_symbols_key_type(config[symbol_type], symbol_table)

def parse_dict(dct, path, verbose=False):
    if (verbose):
        print("Processing {}...".format(" > ".join(path)))
        infer_dict_keykind(dct)
        for key, value in dct.items():
            if isinstance(value, dict):
                parse_dict(value, path + [key], verbose)
    
def infer_dict_keykind(d):
    subdict_unique_keys = set()
    subdict_num_keys = 0
    subdict_num = 0
    not_subdict_num = 0
    for value in d.values():
        if isinstance(value, dict):
            subdict_num += 1
            subdict_num_keys += len(value.keys())
            subdict_unique_keys.update(value.keys())
        else:
            not_subdict_num += 1
    print("Total subdict:", subdict_num)
    print("Unique sub keys:", len(subdict_unique_keys))
    print("Total sub keys:", subdict_num_keys)
    print("Total non-subdict:", not_subdict_num)
    if subdict_num == 0 or subdict_num_keys == 0:
        print("Dict keys are types")
    elif (not_subdict_num > subdict_num):
        print("Dict keys are types")
    elif (len(subdict_unique_keys) / subdict_num_keys <= 0.75):
        print("Dict keys are names")
    else:
        print("Dict keys are types")
 
def extract_symbols_key_name(symbol_type, symbols_dict, symbol_table):
    # Treat keys as symbol names
    for symbol_name, sub_symbols_dict in symbols_dict.items():
        add_to_symbol_table(symbol_name, symbol_type, symbol_table)
        if sub_symbols_dict is not None:
            extract_symbols_key_type(sub_symbols_dict, symbol_table)

def extract_symbols_value_name(symbol_type, symbols_dict, symbol_table):
    # Treat values as symbol names
    #print("extract_symbols_value_name({}, {})".format(symbol_type, symbols_dict))
    for symbol_name in symbols_dict.values():
        add_to_symbol_table(symbol_name, symbol_type, symbol_table)

def extract_symbols_key_type(sub_symbols_dict, symbol_table):
    # Treat keys as symbol types and values as symbol names
    for symbol_type, symbol_value in sub_symbols_dict.items():
        if isinstance(symbol_value, bool) or symbol_value == "true" or symbol_value == "false":
            continue
        if isinstance(symbol_value, str) or isinstance(symbol_value, int):
            add_to_symbol_table(str(symbol_value), symbol_type, symbol_table)
        elif isinstance(symbol_value, list):
            for symbol_name in symbol_value:
                add_to_symbol_table(symbol_name, symbol_type, symbol_table)
        elif isinstance(symbol_value, dict):
            if symbol_type in SUB_TYPES_VALUES:
                extract_symbols_value_name(symbol_type, symbol_value, symbol_table)
            elif symbol_type in SUB_TYPES_KEYS:
                extract_symbols_key_name(symbol_type, symbol_value, symbol_table)
            else:
                extract_symbols_key_type(symbol_value, symbol_table)

def add_to_symbol_table(symbol_name, symbol_type, symbol_table):
    # Check if symbol type should be ignored
    symbol_type = symbol_type.lower()
    if symbol_type in IGNORED_TYPES:
        return

    # Handle type aliases
    if symbol_type in TYPEDEFS:
        symbol_type = TYPEDEFS[symbol_type]

    # Normalize IP addresses
    if symbol_type == "ip4_address":
        try:
            symbol_name = str(ipaddress.ip_interface(symbol_name))
        except:
            pass

    # Normalize descriptions and names
    if symbol_type == "description" or symbol_type == "name":
        symbol_name = symbol_name.strip(" *").lower()
        #.replace('-', " ").replace("_", " ")

    # Add to symbol table
    if symbol_name not in symbol_table:
        symbol_table[symbol_name] = []
    if symbol_type not in symbol_table[symbol_name]:
        symbol_table[symbol_name].append(symbol_type)



if __name__ == "__main__":
    main()