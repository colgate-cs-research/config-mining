#!/usr/bin/env python3

import argparse
import json
import os
import ipaddress
import logging
import pprint

TOP_LEVEL_TYPES_JUNIPER = [
    "groups", 
    #"interfaces", 
    #"policy-options", 
    #"firewall", 
]
TOP_LEVEL_TYPES_ARUBA = [
    "Port", 
    "Interface", 
    "ACL", 
    "VLAN", 
]
VALID_TYPES_JUNIPER = [
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
    "protocol-except",
    "icmp-type",
    "ip-options",
    "source-port",
    "destination-port",
    "source-address",
    "destination-address",
    "prefix-list",
    "source-prefix-list",
    "from",
    "then",
    "to",
]
VALID_TYPES_ARUBA = [
    "interface",
    "interfaces",
    "port",
    "name",
    "description",
    "vlan_tag",
    "vlan_trunks",
    "loop_protect_vlan",
    "lacp-aggregation-key",
    "mtu",
    "port_access_clients_limit",
    "admin",
    "ip4_address",
    "ip_mtu",
    "vlan_mode",
    "qos_trust",
    "type",
    "duplex",
    "autoneg",
    "lacp",
    "vrf",
    "speeds",
]
TOP_LEVEL_TYPES = TOP_LEVEL_TYPES_JUNIPER
VALID_TYPES = VALID_TYPES_JUNIPER
#TOP_LEVEL_TYPES = TOP_LEVEL_TYPES_ARUBA
#VALID_TYPES = VALID_TYPES_ARUBA

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('configs_path', help='Path to directory of configurations')
    parser.add_argument('output_file', help='Path to file in which to store symbols')
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
    
    # Parse each configuration
    symbol_table = {}
    all_configs = {}
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
#        logging.info("Processing {}...".format(node))
#        extractor = SymbolExtractor(config, symbol_table)

    extractor = SymbolExtractor(all_configs, symbol_table)

    summarize_types(symbol_table)

    with open(arguments.output_file, 'w') as symbols_file:
        json.dump(symbol_table, symbols_file, indent=4, sort_keys=True)

def summarize_types(symbol_table):
    inverted_symbol_table = {}
    for symbol_name, symbol_types in symbol_table.items():
        for symbol_type in symbol_types:
            if symbol_type not in inverted_symbol_table:
                inverted_symbol_table[symbol_type] = set()
            inverted_symbol_table[symbol_type].add(symbol_name)

    logging.info("Symbol table summary")
    for symbol_type, symbol_names in inverted_symbol_table.items():
        logging.info("{} unique symbols of type {}".format(len(symbol_names), symbol_type))

class SymbolExtractor:
    def __init__(self, config, symbol_table={}):
        self.config = config
        self.symbol_table = symbol_table
        self.keykinds = {
            (('name', '*'), ('type', 'firewall'), ('type', 'family inet'), ('type', 'filter')) : "name",
            (('name', '*'), ('type', 'policy-options'), ('type', 'as-path')) : "name",
            (('name', '*'), ('type', 'groups')) : "name",
        }

        # Iterate over top-level types of interest (e.g., ACLs, interfaces, etc.)
        for node in config:
            for symbol_type in TOP_LEVEL_TYPES:
                if symbol_type not in config[node]:
                    continue
                self.parse_dict(config[node][symbol_type], [("name", node), ("type", symbol_type)])

        logging.info("Key kind summary")
        logging.info("\t{}".format(pprint.pformat(self.keykinds)))

    def parse_dict(self, dct, path):
        logging.debug("Processing {}...".format(path))
        path_signature = self.get_path_signature(path)
        if path_signature in self.keykinds:
            kind = self.keykinds[path_signature]
        else:
            logging.debug("Need to infer keykind for {}".format(path_signature))
            dictionaries = self.get_dictionaries(self.config, path_signature)

            logging.debug("Dictionaries:")
            for d in dictionaries:
                logging.debug("\t{}".format(d.keys()))

            #kind = self.infer_dict_keykind(dct)
            kind = self.infer_dictionaries_keykind(dictionaries)
            self.keykinds[path_signature] = kind
        logging.debug("Dict keys are {}s".format(kind))
        if (kind == "name"):
            self.extract_symbols_key_name(dct, path)
        elif (kind == "type"):
            self.extract_symbols_key_type(dct, path)

    def get_path_signature(self, path):
        signature = []
        for component in path:
            if component[0] == "name":
                signature.append(("name", "*"))
            else:
                signature.append(component)
        return tuple(signature)

    def get_dictionaries(self, dct, signature):
        result = []
        kind, id = signature[0]

        # Base case
        if len(signature) == 1:
            if kind == "type":
                if id in dct and isinstance(dct[id], dict):
                    #result.append({id : dct[id]})
                    result.append(dct[id])
            elif kind == "name":
                for key, value in dct.items():
                    #result.append({key: value})
                    if isinstance(value, dict):
                        result.append(value)
            else:
                raise Exception("Unknown kind {} in signature {}".format(kind, signature))
        # Recursive case
        else:
            kind, value = signature[0]
            if kind == "type":
                if value in dct and isinstance(dct[value], dict):
                    result = self.get_dictionaries(dct[value],signature[1:])
            elif kind == "name":
                for value in dct.values():
                    if isinstance(value, dict):
                        result.extend(self.get_dictionaries(value, signature[1:]))
            else:
                raise Exception("Unknown kind {} in signature {}".format(kind, signature))

        return result
        
    def infer_dict_keykind(self, dct):
        subdict_num = 0
        subdict_num_keys = 0
        subdict_unique_keys = set()
        sublist_num = 0
        sublist_num_values = 0
        sublist_unique_values = set()
        not_sub_num = 0
        for value in dct.values():
            if isinstance(value, dict):
                subdict_num += 1
                subdict_num_keys += len(value.keys())
                subdict_unique_keys.update(value.keys())
            elif isinstance(value, list):
                sublist_num += 1
                sublist_num_values += len(value)
                sublist_unique_values.update(value)
            else:
                not_sub_num += 1
        logging.debug("\tTotal subdict: {}".format(subdict_num))
        logging.debug("\tUnique sub keys {}".format(len(subdict_unique_keys)))
        logging.debug("\tTotal sub keys {}".format(subdict_num_keys))
        logging.debug("\tTotal sublists: {}".format(sublist_num))
        logging.debug("\tUnique sub lists {}".format(len(sublist_unique_values)))
        logging.debug("\tTotal sub lists {}".format(sublist_num_values))
        logging.debug("\tTotal non-subdict {}".format(not_sub_num))
        if (sublist_num == 0 or sublist_num_values == 0) and (subdict_num == 0 or subdict_num_keys == 0):
            return "type"
        elif (not_sub_num > subdict_num + sublist_num):
            return "type"
        elif (subdict_num_keys > 0 and len(subdict_unique_keys) / subdict_num_keys <= 0.75):
            return "name"
        elif (sublist_num_values > 0 and len(sublist_unique_values) / sublist_num_values <= 0.75):
            return "name"
        else:
            return "type"

    def infer_dictionaries_keykind(self, dictionaries):
        num_dict = len(dictionaries)
        if (num_dict == 1):
            logging.debug("\tNeed to examine subdictionaries")   
            return self.infer_dict_keykind(dictionaries[0])

        unique_keys = set()
        num_keys = 0
        for dct in dictionaries:
            num_keys += len(dct.keys())
            unique_keys.update(dct.keys())
        num_unique_keys = len(unique_keys)
        logging.debug("\tTotal dict: {}".format(num_dict))
        logging.debug("\tUnique sub keys {}".format(num_unique_keys))
        logging.debug("\tTotal sub keys {}".format(num_keys))
        if (num_keys == 0):
            logging.error("Cannot infer key kind!")
            return "type"
        if (num_unique_keys / num_keys > 0.2) or num_unique_keys > 100:
            return "name"
        else:
            return "type"
    
    def extract_symbols_key_name(self, dct, path):
        # Treat keys as symbol names
        symbol_type = path[-1][1]
        for symbol_name, symbol_value in dct.items():
            self.add_to_symbol_table(symbol_name, symbol_type)
            if isinstance(symbol_value, dict):
                self.parse_dict(symbol_value, path + [('name', symbol_name)])

    def extract_symbols_key_type(self, dct, path):
        # Treat keys as symbol typs 
        for symbol_type, value in dct.items():
            '''if isinstance(symbol_value, bool) or symbol_value == "true" or symbol_value == "false":
                continue'''
            if isinstance(value, dict):
                self.parse_dict(value, path + [('type', symbol_type)])
            elif isinstance(value, str) or isinstance(value, int):
                self.add_to_symbol_table(str(value), symbol_type)
            elif isinstance(value, list):
                for subvalue in value:
                    self.add_to_symbol_table(str(subvalue), symbol_type)
            '''elif isinstance(symbol_value, dict):
                if symbol_type in SUB_TYPES_VALUES:
                    extract_symbols_value_name(symbol_type, symbol_value, symbol_table)
                elif symbol_type in SUB_TYPES_KEYS:
                    extract_symbols_key_name(symbol_type, symbol_value, symbol_table)
                else:
                    extract_symbols_key_type(symbol_value, symbol_table)'''

    def add_to_symbol_table(self, symbol_name, symbol_type):
        symbol_type = symbol_type.lower()

        # Don't add booleans
        if str(symbol_name).lower() in ["true", "false"]:
            return
        
        logging.debug("Adding {} {} to symbol table".format(symbol_type, symbol_name))

        # Sanity checking
        if symbol_type not in VALID_TYPES:
            logging.debug("!{} is not a valid symbol type".format(symbol_type))

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
        if symbol_name not in self.symbol_table:
            self.symbol_table[symbol_name] = []
        if symbol_type not in self.symbol_table[symbol_name]:
            self.symbol_table[symbol_name].append(symbol_type)

if __name__ == "__main__":
    main()