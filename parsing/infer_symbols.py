#!/usr/bin/env python3

import argparse
import json
import os
import ipaddress
import logging
import pprint

TOP_LEVEL_TYPES_JUNIPER = [
    #"groups", 
    "interfaces", 
    "policy-options", 
    "firewall", 
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
    parser.add_argument('output_dir', help='Path to directory in which to store symbol files')
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

    inverted_table = summarize_types(symbol_table)

    with open(os.path.join(arguments.output_dir, "symbols.json"), 'w') as symbols_file:
        json.dump(symbol_table, symbols_file, indent=4, sort_keys=True)
    with open(os.path.join(arguments.output_dir, "inverted.json"), 'w') as inverted_file:
        json.dump(inverted_table, inverted_file, indent=4, sort_keys=True)
    pickle_keykinds = {str(k) : v for k,v in extractor.keykinds.items()}
    with open(os.path.join(arguments.output_dir, "keykinds.json"), 'w') as keykinds_file:
        json.dump(pickle_keykinds, keykinds_file, indent=4, sort_keys=True)

def summarize_types(symbol_table):
    inverted_symbol_table = {}
    for symbol_name, symbol_types in symbol_table.items():
        for symbol_type in symbol_types:
            if symbol_type not in inverted_symbol_table:
                inverted_symbol_table[symbol_type] = set()
            inverted_symbol_table[symbol_type].add(symbol_name)

    logging.info("Symbol table summary")
    for symbol_type, symbol_names in inverted_symbol_table.items():
        inverted_symbol_table[symbol_type] = list(symbol_names)
        logging.info("{} unique symbols of type {}".format(len(symbol_names), symbol_type))
    return inverted_symbol_table

class SymbolExtractor:
    def __init__(self, config, symbol_table={}):
        self.config = config
        self.symbol_table = symbol_table
        self.keykinds = {
            (('name', '*'), ('type', 'firewall'), ('type', 'family inet'), ('type', 'filter')) : "name",
            (('name', '*'), ('type', 'policy-options'), ('type', 'as-path')) : "name",
            (('name', '*'), ('type', 'policy-options'), ('type', 'policy-statement'), ('name', '*'), ('type', 'term'), ('name', '*'), ('type', 'to')): "mixed",
            (('name', '*'), ('type', 'groups')) : "name",
        }
        self.mixedkinds = {}

        # Iterate over top-level types of interest (e.g., ACLs, interfaces, etc.)
        for node in config:
            for symbol_type in TOP_LEVEL_TYPES:
                if symbol_type not in config[node]:
                    continue
                self.parse_dict(config[node][symbol_type], [("name", node), ("type", symbol_type)])

        logging.info("Key kind summary")
        logging.info("\t{}".format(pprint.pformat(self.keykinds)))

    def parse_dict(self, dct, path):
        logging.debug("Processing dict {}...".format(path))
        path_signature = self.get_path_signature(path)
        if path_signature in self.keykinds:
            kind = self.keykinds[path_signature]
        else:
            logging.debug("Need to infer keykind for {}".format(path_signature))
            dictionaries = self.get_instances(self.config, path_signature)

            logging.debug("Dictionaries:")
            for d in dictionaries:
                logging.debug("\t{}".format(d.keys()))

            kind = self.infer_keykind(dictionaries)
            self.keykinds[path_signature] = kind

            if kind == "unknown":
                logging.error("!Cannot infer key kind for {}".format(path))
        logging.debug("Dict keys are {}s".format(kind))
        if (kind == "name"):
            self.extract_symbols_key_name(dct, path)
        elif (kind == "type"):
            self.extract_symbols_key_type(dct, path)

    def parse_list(self, lst, path):
        logging.debug("Processing list {}...".format(path))
        path_signature = self.get_path_signature(path)
        if path_signature in self.keykinds:
            kind = self.keykinds[path_signature]
        else:
            logging.debug("Need to infer keykind for {}".format(path_signature))
            lists = self.get_instances(self.config, path_signature)

            logging.debug("Lists:")
            for l in lists:
                logging.debug("\t{}".format(l))

            kind = self.infer_keykind(lists)
            self.keykinds[path_signature] = kind

            if kind == "unknown":
                logging.error("!Cannot infer key kind for {}".format(path))
            #elif kind == "mixed":
            #    kinds = self.infer_mixedkinds(lists)
            #    self.mixedkinds[path_signature] = kinds
            #    logging.debug("Inferred kinds for mixed {}:\n{}".format(path, pprint.pformat(kinds))) 
        logging.debug("List values are {}s".format(kind))
        if (kind == "name"):
            self.extract_symbols_list_name(lst, path)
        elif (kind == "type"):
            logging.debug("!Not recursing on list of types: {}".format(path))
        elif (kind == "mixed"):
            self.extract_symbols_list_mixed(lst, path)

    def get_path_signature(self, path):
        signature = []
        for component in path:
            if component[0] == "name":
                signature.append(("name", "*"))
            else:
                signature.append(component)
        return tuple(signature)

    def get_instances(self, dct, signature):
        result = []
        kind, id = signature[0]

        # Base case
        if len(signature) == 1:
            if kind == "type":
                if id in dct and (isinstance(dct[id], dict) or isinstance(dct[id], list)):
                    #result.append({id : dct[id]})
                    result.append(dct[id])
            elif kind == "name":
                for key, value in dct.items():
                    #result.append({key: value})
                    if isinstance(value, dict):
                        result.append(value)
                    elif isinstance(value, list):
                        result.append(value)
            else:
                raise Exception("Unknown kind {} in signature {}".format(kind, signature))
        # Recursive case
        else:
            kind, value = signature[0]
            if kind == "type":
                if value in dct and isinstance(dct[value], dict):
                    result = self.get_instances(dct[value],signature[1:])
            elif kind == "name":
                for value in dct.values():
                    if isinstance(value, dict):
                        result.extend(self.get_instances(value, signature[1:]))
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

    def infer_keykind(self, instances):
        num_inst = len(instances)
        if (num_inst == 1):
            if isinstance(instances[0], dict):
                logging.debug("\tNeed to examine subdictionaries")   
                return self.infer_dict_keykind(instances[0])
            elif isinstance(instances[0], list):
                return "unknown"  
 
        unique_keys = set()
        num_keys = 0
        for inst in instances:
            if isinstance(inst, dict):
                num_keys += len(inst.keys())
                unique_keys.update(inst.keys())
            elif isinstance(inst, list):
                num_keys += len(inst)
                unique_keys.update(inst)
        num_unique_keys = len(unique_keys)
        logging.debug("\tTotal dict: {}".format(num_inst))
        logging.debug("\tUnique sub keys {}".format(num_unique_keys))
        logging.debug("\tTotal sub keys {}".format(num_keys))
        if (num_keys == 0):
            return "unknown"
        if (num_unique_keys / num_keys > 0.2) or num_unique_keys > 100:
            num_unique_keys_with_spaces = 0
            for key in unique_keys:
                if " " in key:
                   num_unique_keys_with_spaces += 1 
            logging.debug("\tUnique sub keys with spaces {}".format(num_unique_keys_with_spaces)) 
            if (num_unique_keys_with_spaces / num_unique_keys > 0.9):
                return "mixed"
            else:
                return "name"
        else:
            return "type"

    def infer_mixedkinds(self, instances):
        counts = {}
        for inst in instances:
            if isinstance(inst, dict):
                symbols = inst.keys()
            elif isinstance(inst, list):
                symbols = inst
            else:
                logging.error("!Cannot infer mixed kinds for {}".format(type(inst)))
                continue
            
            for symbol in symbols:
                parts = symbol.split(" ")
                for part in parts:
                    if part not in counts:
                        counts[part] = 0
                    counts[part] += 1

        denominator = max(counts.values())
        counts = { k : v / denominator for k, v in counts.items() }        
        return counts

        '''kinds = {}
        denominator = max(counts.values())
        for symbol, count in counts.items():
            if count/denominator > 0.15:
                kinds[symbol] = "type"
            else:
                kinds[symbol] = "name"

        return kinds'''
    
    def extract_symbols_key_name(self, dct, path):
        # Treat keys as symbol names
        symbol_type = None
        if path[-1][0] == "type":
            symbol_type = path[-1][1]
        for symbol_name, symbol_value in dct.items():
            self.add_to_symbol_table(symbol_name, symbol_type)
            if isinstance(symbol_value, dict):
                self.parse_dict(symbol_value, path + [('name', symbol_name)])
            elif isinstance(symbol_value, list):
                self.parse_list(symbol_value, path + [('name', symbol_name)])

    def extract_symbols_key_type(self, dct, path):
        # Treat keys as symbol types 
        for symbol_type, value in dct.items():
            '''if isinstance(symbol_value, bool) or symbol_value == "true" or symbol_value == "false":
                continue'''
            if isinstance(value, dict):
                self.parse_dict(value, path + [('type', symbol_type)])
            elif isinstance(value, str) or isinstance(value, int):
                self.add_to_symbol_table(str(value), symbol_type)
            elif isinstance(value, list):
                self.parse_list(value, path + [('type', symbol_type)])
                #for subvalue in value:
                #    self.add_to_symbol_table(str(subvalue), symbol_type)

    def extract_symbols_list_name(self, lst, path):
        # Treat values as symbol names
        symbol_type = None
        if path[-1][0] == "type":
            symbol_type = path[-1][1]
        for symbol_name in lst:
            self.add_to_symbol_table(symbol_name, symbol_type)

    def extract_symbols_list_mixed(self, lst, path):
        # Treat values as combination of symbol type and symbol name
        for symbol in lst:
            symbol = symbol.strip(' ')
            # Not a symbol type/name combination
            if ' ' not in symbol:
                pass
            # Pair of symbol type and name
            elif symbol.count(' ') == 1:
                symbol_type, symbol_name = symbol.split(' ')
                self.add_to_symbol_table(symbol_name, symbol_type)
            # Symbol type and list of names
            elif ' [' in symbol and symbol[-1] == ']':
                symbol_type, symbol_names = symbol[:-1].split('[')
                symbol_type = symbol_type[:-1] # Strip space
                symbol_names = symbol_names.split(',')
                for symbol_name in symbol_names:
                    symbol_name = symbol_name.strip("', ")
                    self.add_to_symbol_table(symbol_name, symbol_type)
            # Symbol type and list of names
            elif ' (' in symbol and symbol[-1] == ')':
                symbol_type, symbol_names = symbol[:-1].split('(')
                symbol_type = symbol_type[:-1] # Strip space
                symbol_names = symbol_names.split("&&")
                for symbol_name in symbol_names:
                    symbol_name = symbol_name.strip("', ")
                    self.add_to_symbol_table(symbol_name, symbol_type)
            else:
                logging.warning("!Cannot infer symbol name/type for mixed value: {}".format(symbol))

    def add_to_symbol_table(self, symbol_name, symbol_type):
        # Put type in canonical form
        if symbol_type != None:
            symbol_type = symbol_type.lower()

        # Don't add booleans
        if str(symbol_name).lower() in ["true", "false"]:
            return
        
        logging.debug("Adding {} {} to symbol table".format(symbol_type, symbol_name))

        # Sanity checking
        if symbol_type not in VALID_TYPES:
            logging.debug("!{} is not a valid symbol type".format(symbol_type))

        # Normalize IP addresses
        if symbol_type != None and "address" in symbol_type:
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
        if symbol_type != None and symbol_type not in self.symbol_table[symbol_name]:
            self.symbol_table[symbol_name].append(symbol_type)

if __name__ == "__main__":
    main()