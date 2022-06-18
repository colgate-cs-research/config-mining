#!/usr/bin/env python3

import argparse
import json
import os
import ipaddress
import logging
import ast

TOP_LEVEL_TYPES_JUNIPER = [
    #"groups", 
    #"interfaces", 
    "policy-options", 
    #"firewall", 
]
TOP_LEVEL_TYPES_ARUBA = [
    "Port", 
    "Interface", 
    "ACL", 
    "VLAN", 
]
TOP_LEVEL_TYPES = TOP_LEVEL_TYPES_JUNIPER
#TOP_LEVEL_TYPES = TOP_LEVEL_TYPES_ARUBA

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('configs_path', help='Path to directory of configurations')
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
    with open(os.path.join(arguments.symbols_dir, "inverted.json"), 'r') as inverted_file:
        inverted_table = json.load(inverted_file)
    with open(os.path.join(arguments.symbols_dir, "keykinds.json"), 'r') as keykinds_file:
        pickle_keykinds = json.load(keykinds_file) 
    keykinds = {ast.literal_eval(k) : v for k, v in pickle_keykinds.items()}
    
    # Load configurations
    all_configs = {} # keys are device names and values are config jsons
    for filename in sorted(os.listdir(arguments.configs_path)):
        node = filename.replace(".json", "")
        filepath = os.path.join(arguments.configs_path, filename)
        try:
            with open(filepath, "r") as config_file:
                config = json.load(config_file)
                all_configs[node] = config
        except:
            logging.debug("Failed to parse {}".format(filepath))
            continue

    extractor = RelationshipExtractor(all_configs, symbol_table, inverted_table, keykinds)

class RelationshipExtractor:
    def __init__(self, config, symbol_table, inverted_table, keykinds):
        self.config = config
        self.symbol_table = symbol_table
        self.inverted_table = inverted_table
        self.keykinds = keykinds

        # Iterate over top-level types of interest (e.g., ACLs, interfaces, etc.)
        for node in config:
            for symbol_type in TOP_LEVEL_TYPES:
                if symbol_type not in config[node]:
                    continue
                self.parse_dict(config[node][symbol_type], [("name", node), ("type", symbol_type)], [])

    def parse_dict(self, dct, path, symbols):
        logging.debug("Processing {}...".format(path))
        path_signature = self.get_path_signature(path)
        if path_signature not in self.keykinds:
            logging.error("!Unknown keykind for {}".format(path_signature))
            return

        kind = self.keykinds[path_signature]

        logging.debug("Dict keys are {}s".format(kind))
        if (kind == "name"):
            self.extract_relationships_key_name(dct, path, symbols)
        elif (kind == "type"):
            self.extract_relationships_key_type(dct, path, symbols)

    def parse_list(self, lst, path, symbols):
        logging.debug("Processing {}...".format(path))
        path_signature = self.get_path_signature(path)
        if path_signature not in self.keykinds:
            logging.error("!Unknown keykind for {}".format(path_signature))
            return

        kind = self.keykinds[path_signature]

        logging.debug("List values are {}s".format(kind))
        if (kind == "name"):
            self.extract_relationships_list_name(lst, path, symbols)
        elif (kind == "type"):
            logging.warning("!Not extracting relationships from list of types: {}".format(path))

    def get_path_signature(self, path):
        signature = []
        for component in path:
            if component[0] == "name":
                signature.append(("name", "*"))
            else:
                signature.append(component)
        return tuple(signature)

    def get_symbol(self, symbol_name, symbol_type):
        # Check if symbol_type needs to be inferred
        if symbol_type is None:
            if symbol_name not in self.symbol_table:
                logging.warning("!Cannot infer type for symbol {}: symbol not in table".format(symbol_name))
                return None 
            if len(self.symbol_table[symbol_name]) > 1:
                logging.warning("!Cannot infer type for symbol {}: {} possible types".format(symbol_name, len(self.symbol_table[symbol_name])))
                return None 
            
            symbol_type = self.symbol_table[symbol_name][0] 

        # Check if symbol_type exists
        if symbol_type not in self.inverted_table:
            return None

        # Check if symbol_type is a typedef
        if isinstance(self.inverted_table[symbol_type], str):
            return self.get_symbol(symbol_name, self.inverted_table[symbol_type])

        # Check if symbol_name exists
        if symbol_name in self.inverted_table[symbol_type]:
            return (symbol_type, symbol_name)

        return None
   
    def extract_relationships_key_name(self, dct, path, symbols):
        # Treat keys as symbol names
        symbol_type = None
        if path[-1][0] == "type":
            symbol_type = path[-1][1]
        for symbol_name, symbol_value in dct.items():
            symbol = self.get_symbol(symbol_name, symbol_type)
            if symbol != None:
                if len(symbols) >= 1:
                    logging.info("{} --- {}".format(symbols[-1], symbol))
            else:
                logging.debug("No matching symbol for {} : {}".format(symbol_type, symbol_name))
            if isinstance(symbol_value, dict):
                self.parse_dict(symbol_value, path + [('name', symbol_name)], (symbols + [symbol] if symbol != None else symbols))
            elif isinstance(symbol_value, list):
                self.parse_list(symbol_value, path + [('name', symbol_name)], (symbols + [symbol] if symbol != None else symbols))

    def extract_relationships_key_type(self, dct, path, symbols):
        # Treat keys as symbol types 
        for symbol_type, value in dct.items():
            if isinstance(value, bool) or value == "true" or value == "false":
                continue
            elif isinstance(value, dict):
                self.parse_dict(value, path + [('type', symbol_type)], symbols)
            elif isinstance(value, str) or isinstance(value, int):
                symbol = self.get_symbol(value, symbol_type)
                if symbol != None:
                    if len(symbols) >= 1:
                        logging.info("{} --- {}".format(symbols[-1], symbol)) 
                else:
                    logging.debug("No matching symbol for {} : {}".format(symbol_type, value))
            elif isinstance(value, list):
                for subvalue in value:
                    logging.debug("Check for matching symbol for {} : {}".format(symbol_type, subvalue))

    def extract_relationships_list_name(self, lst, path, symbols):
        # Treat values as symbol names
        symbol_type = None
        if path[-1][0] == "type":
            symbol_type = path[-1][1]
        for symbol_name in lst:
            symbol = self.get_symbol(symbol_name, symbol_type)
            if symbol != None:
                if len(symbols) >= 1:
                    logging.info("{} --- {}".format(symbols[-1], symbol))
            else:
                logging.debug("No matching symbol for {} : {}".format(symbol_type, symbol_name))

if __name__ == "__main__":
    main()