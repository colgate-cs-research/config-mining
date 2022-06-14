#!/usr/bin/env python3

import argparse
import json
import os
import ipaddress
import logging



# FIXME
TOP_LEVEL_TYPES = [
    #"groups", 
#    "interfaces", 
#    "policy-options", 
    "firewall", 
]
IGNORED_TYPES = [
]
TYPEDEFS = {
}
VALID_TYPES = [
    "interfaces",
    "unit",
    "description",
    "mtu",
    "vlan-id",
    "apply-groups",
    "encapsulation",
    "address",
    "802.3ad",
    "minimum-links",
    "link-speed",
    "input",
    "policy-statement",
    "term",
    "community",
    "members",
    "filter",
    "protocol",
    "icmp-type",
    "destination-port",
    "source-port",
    "ip-options",
    "destination-address",
]

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('configs_path', help='Path to directory of configurations')
    parser.add_argument('output_file', help='Path to file in which to store symbols')
    parser.add_argument('-v', '--verbose', action='store_true', help="Display verbose output")
    arguments = parser.parse_args()

    # module-wide logging
    if (arguments.verbose):
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)
    logging.getLogger(__name__)
    
    # Parse each configuration
    symbol_table = {}
    for filename in sorted(os.listdir(arguments.configs_path)):
        node = filename.replace(".json", "")
        filepath = os.path.join(arguments.configs_path, filename)
        try:
            with open(filepath, "r") as config_file:
                config = json.load(config_file)
        except:
            logging.debug("Failed to parse {}".format(filepath))
            continue
        logging.info("Processing {}...".format(node))
        parse_config(config, symbol_table)
        
        break

    # Determine all types
#    types = set()
#    for symbol_types in symbol_table.values():
#        types.update(symbol_types)

    with open(arguments.output_file, 'w') as symbols_file:
        json.dump(symbol_table, symbols_file, indent=4, sort_keys=True)

def parse_config(config, symbol_table):
    # Iterate over top-level types of interest (e.g., ACLs, interfaces, etc.)
    for symbol_type in TOP_LEVEL_TYPES:
        if symbol_type not in config:
            continue
        parse_dict(config[symbol_type], [("type", symbol_type)], symbol_table)

def parse_dict(dct, path, symbol_table):
    logging.debug("Processing {}...".format(path))
    kind = infer_dict_keykind(dct)
    logging.debug("Dict keys are {}s".format(kind))
    if (kind == "name"):
        extract_symbols_key_name(dct, path, symbol_table)
    elif (kind == "type"):
        extract_symbols_key_type(dct, path, symbol_table)
    
def infer_dict_keykind(dct):
    subdict_unique_keys = set()
    subdict_num_keys = 0
    subdict_num = 0
    not_subdict_num = 0
    for value in dct.values():
        if isinstance(value, dict):
            subdict_num += 1
            subdict_num_keys += len(value.keys())
            subdict_unique_keys.update(value.keys())
        else:
            not_subdict_num += 1
    logging.debug("\tTotal subdict: {}".format(subdict_num))
    logging.debug("\tUnique sub keys {}".format(len(subdict_unique_keys)))
    logging.debug("\tTotal sub keys {}".format(subdict_num_keys))
    logging.debug("\tTotal non-subdict {}".format(not_subdict_num))
    if subdict_num == 0 or subdict_num_keys == 0:
        return "type"
    elif (not_subdict_num > subdict_num):
        return "type"
    elif (len(subdict_unique_keys) / subdict_num_keys <= 0.75):
        return "name"
    else:
        return "type"
 
def extract_symbols_key_name(dct, path, symbol_table):
    # Treat keys as symbol names
    symbol_type = path[-1][1]
    for symbol_name, symbol_value in dct.items():
        add_to_symbol_table(symbol_name, symbol_type, symbol_table)
        if isinstance(symbol_value, dict):
            parse_dict(symbol_value, path + [('name', symbol_name)], symbol_table)

def extract_symbols_key_type(dct, path, symbol_table):
    # Treat keys as symbol typs 
    for symbol_type, value in dct.items():
        '''if isinstance(symbol_value, bool) or symbol_value == "true" or symbol_value == "false":
            continue'''
        if isinstance(value, dict):
            parse_dict(value, path + [('type', symbol_type)], symbol_table)
        elif isinstance(value, str) or isinstance(value, int):
            add_to_symbol_table(str(value), symbol_type, symbol_table)
        elif isinstance(value, list):
            for subvalue in value:
                add_to_symbol_table(str(subvalue), symbol_type, symbol_table)
        '''elif isinstance(symbol_value, dict):
            if symbol_type in SUB_TYPES_VALUES:
                extract_symbols_value_name(symbol_type, symbol_value, symbol_table)
            elif symbol_type in SUB_TYPES_KEYS:
                extract_symbols_key_name(symbol_type, symbol_value, symbol_table)
            else:
                extract_symbols_key_type(symbol_value, symbol_table)'''

def add_to_symbol_table(symbol_name, symbol_type, symbol_table):
    logging.debug("Adding {} {} to symbol table".format(symbol_type, symbol_name))
    # Check if symbol type should be ignored
    symbol_type = symbol_type.lower()
    if symbol_type in IGNORED_TYPES:
        return

    if symbol_type not in VALID_TYPES:
        logging.warning("!{} is not a valid symbol type".format(symbol_type))

    # Handle type aliases
    if symbol_type in TYPEDEFS:
        symbol_type = TYPEDEFS[symbol_type]

    # Normalize IP addresses
    if "address" in symbol_type:
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