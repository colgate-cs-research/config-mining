#!/usr/bin/env python3

import argparse
import json
import os
import ipaddress
import logging
import ast
import pprint

TOP_LEVEL_TYPES_JUNIPER = [
    #"groups", 
    #"interfaces", 
    "policy-options", 
    #"firewall", 
]
TOP_LEVEL_TYPES_ARUBA = [
    #"AAA_Accounting_Attributes",
    #"AAA_Server_Group",
    #"AAA_Server_Group_Prio",
    "ACL", 
    "Class",
    "Interface", 
    "Port", 
    "VLAN", 
    "VRF"
]
TOP_LEVEL_TYPES = TOP_LEVEL_TYPES_JUNIPER + TOP_LEVEL_TYPES_ARUBA 
#TOP_LEVEL_TYPES = TOP_LEVEL_TYPES_ARUBA

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('configs_path', help='Path to directory of configurations')
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
    with open(os.path.join(arguments.symbols_dir, "new_symbols.json"), 'r') as symbols_file:
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

    # Create output directory
    os.makedirs(arguments.symbols_dir, exist_ok=True)

    # Save results
    with open(os.path.join(arguments.symbols_dir, "relationships.json"), 'w') as out_file:
        json.dump(extractor.relationships, out_file, indent=4, sort_keys=True)
    pickle_typekinds = {str(k) : v for k,v in extractor.typekinds.items()}
    with open(os.path.join(arguments.symbols_dir, "typekinds.json"), 'w') as out_file:
        json.dump(pickle_typekinds, out_file, indent=4, sort_keys=True)

class RelationshipExtractor:
    def __init__(self, config, symbol_table, inverted_table, keykinds):
        self.config = config
        self.symbol_table = symbol_table
        self.inverted_table = inverted_table
        self.keykinds = keykinds
        self.typekinds = {}
        self.relationships = []

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

        if kind == "name" and path_signature not in self.typekinds:
            logging.debug("Need to infer typekind for {}".format(path_signature))
            typekind = self.infer_typekind(path_signature)
            logging.debug("Type names are {}".format(typekind))
            self.typekinds[path_signature] = typekind

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
            logging.debug("!Not extracting relationships from list of types: {}".format(path))
        elif (kind == "mixed"):
            self.extract_relationships_list_mixed(lst, path, symbols)

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
            if len(self.symbol_table[symbol_name]) == 0:
                logging.debug("!Cannot infer type for symbol {}: no possible types".format(symbol_name, len(self.symbol_table[symbol_name])))
                return None 
            if len(self.symbol_table[symbol_name]) > 1:
                logging.warning("!Cannot infer type for symbol {}: {} possible types".format(symbol_name, len(self.symbol_table[symbol_name])))
                return None 
            
            symbol_type = self.symbol_table[symbol_name][0] 

        # Check if symbol_type exists
        symbol_type = symbol_type.lower()
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
        for symbol_name, symbol_value in dct.items():
            to_append = self.consider_edge(symbol_name, None, path, symbols)
            if isinstance(symbol_value, dict):
                self.parse_dict(symbol_value, path + [('name', symbol_name)], (symbols + to_append))
            elif isinstance(symbol_value, list):
                self.parse_list(symbol_value, path + [('name', symbol_name)], (symbols + to_append))

    def extract_relationships_key_type(self, dct, path, symbols):
        # Treat keys as symbol types 
        for symbol_type, value in dct.items():
            if isinstance(value, bool) or value == "true" or value == "false":
                continue
            elif isinstance(value, dict):
                self.parse_dict(value, path + [('type', symbol_type)], symbols)
            elif isinstance(value, str) or isinstance(value, int):
                self.consider_edge(value, symbol_type, path, symbols)
            elif isinstance(value, list):
                self.parse_list(value, path + [('type', symbol_type)], symbols)
                #for subvalue in value:
                #    logging.debug("Check for matching symbol for {} : {}".format(symbol_type, subvalue))

    def extract_relationships_list_name(self, lst, path, symbols):
        # Treat values as symbol names
        for symbol_name in lst:
            self.consider_edge(symbol_name, None, path, symbols)

    def extract_relationships_list_mixed(self, lst, path, symbols):
        # Treat values as combination of symbol type and symbol name
        for entry in lst:
            entry = entry.strip(' ')

            # Not a symbol type/name combination
            if ' ' not in entry:
                pass

            parts = entry.split(' ')
            symbol_type = parts[0]
            for symbol_name in parts[1:]:
                symbol_name = symbol_name.strip("""'"[), """)
                self.consider_edge(symbol_name, symbol_type, path, symbols)

            '''# Pair of symbol type and name
            elif symbol.count(' ') == 1:
                symbol_type, symbol_name = symbol.split(' ')
                self.add_to_symbol_table(symbol_type, symbol_name)
            # Symbol type and list of names
            elif ' [' in symbol and symbol[-1] == ']':
                symbol_type, symbol_names = symbol[:-1].split('[')
                symbol_type = symbol_type[:-1] # Strip space
                symbol_names = symbol_names.split(',')
                for symbol_name in symbol_names:
                    symbol_name = symbol_name.strip("', ")
                    self.add_to_symbol_table(symbol_type, symbol_name)
            # Symbol type and list of names
            elif ' (' in symbol and symbol[-1] == ')':
                symbol_type, symbol_names = symbol[:-1].split('(')
                symbol_type = symbol_type[:-1] # Strip space
                symbol_names = symbol_names.split("&&")
                for symbol_name in symbol_names:
                    symbol_name = symbol_name.strip("', ")
                    self.add_to_symbol_table(symbol_type, symbol_name)
            else:
                logging.debug("!Cannot infer symbol name/type for mixed value: {}".format(symbol))'''

    def consider_edge(self, symbol_name, symbol_type, path, symbols):
        if symbol_type == None and path[-1][0] == "type":
            symbol_type = path[-1][1]

        logging.debug("Lookup symbol {} {}".format(symbol_type, symbol_name))
        symbol = self.get_symbol(symbol_name, symbol_type)
        if symbol != None:
            # Determine parent name to include (if any)
            path_signature = self.get_path_signature(path)
            parent_name = None
            if path_signature in self.typekinds:
                typekind = self.typekinds[path_signature]
                if typekind == "unique":
                    for hop in reversed(path):
                        if hop[0] == "name":
                            parent_name = hop[1]
                            break

            symbol = symbol + (parent_name,)

            # Add an edge if a symbol has already been found
            if len(symbols) >= 1:
                self.relationships.append((symbols[-1], symbol))
                logging.info("{} --- {}".format(symbols[-1], symbol))
            return [symbol]
        else:
            logging.debug("No matching symbol for {} : {}".format(symbol_type, symbol_name))
            return []

    def get_nested_instances(self, dct, signature, instances, prefix):
        kind, id = signature[0]

        # Base case
        if len(signature) == 1:
            if kind == "type":
                raise Exception("Cannot get nested instances for signature {} which ends with a type".format(signature)) 
            elif kind == "name":
                instances[prefix] = dct
            else:
                raise Exception("Unknown kind {} in signature {}".format(kind, signature))
        # Recursive case
        else:
            kind, value = signature[0]
            if kind == "type":
                if value in dct and isinstance(dct[value], dict):
                    return self.get_nested_instances(dct[value], signature[1:], instances, prefix)
            elif kind == "name":
                for key, value in dct.items():
                    if isinstance(value, dict):
                        self.get_nested_instances(value, signature[1:], instances, key)
            else:
                raise Exception("Unknown kind {} in signature {}".format(kind, signature))

        return instances

    def infer_typekind(self, path_signature):
        nested_instances = {}
        self.get_nested_instances(self.config, path_signature + (("name", "*"),), nested_instances, "")
        #logging.debug(pprint.pformat(nested_instances))

        # Get number of outer_names with common inner_name
        inner_to_outer = {}
        for outer_name in nested_instances:
            for inner_name in nested_instances[outer_name]:
                if inner_name not in inner_to_outer:
                    inner_to_outer[inner_name] = []
                inner_to_outer[inner_name].append(outer_name)
        #logging.debug(pprint.pformat(inner_to_outer))

        # Determine how many instances are replicated
        num_singletons = 0
        num_few = 0
        num_replicated = 0
        num_unique = 0
        few_threshold = max(0.05 * len(nested_instances),3)
        for inner_name, outer_names in inner_to_outer.items():
            # Only one instance
            if len(outer_names) == 1:
                num_singletons += 1
                logging.debug("\t{} : singleton".format(inner_name))
            else:
                # Get the instances
                inner_instances = [nested_instances[outer_name][inner_name] for outer_name in outer_names]
                num_inner_instances = len(inner_instances)

                # Count the number of unique instances
                unique_instances = []
                for inner_instance in inner_instances:
                    if isinstance(inner_instance, dict) and "cfg_version" in inner_instance:
                        del inner_instance["cfg_version"]
                    if inner_instance not in unique_instances:
                        unique_instances.append(inner_instance)
                num_unique_inner_instances = len(unique_instances)

                #logging.debug("\t{}".format(pprint.pformat(unique_instances)))

                # All instances are unique
                if num_unique_inner_instances == num_inner_instances:
                    num_unique += 1
                    logging.debug("\t{} : all unique num_inner={}, num_unique={}".format(inner_name, num_inner_instances, num_unique_inner_instances))
                # All instances are replicated
                elif num_unique_inner_instances == 1:
                    num_replicated += 1
                    logging.debug("\t{} : all replicated num_inner={}, num_unique={}".format(inner_name, num_inner_instances, num_unique_inner_instances))
                # Exists on less than 5% of outer instances
                elif len(outer_names) < few_threshold:
                    num_few += 1
                    logging.debug("\t{} : only {} (num_unique={})".format(inner_name, len(outer_names), num_unique_inner_instances))
                elif num_unique_inner_instances <= few_threshold:
                    num_replicated += 1
                    logging.debug("\t{} : replicated num_inner={}, num_unique={}".format(inner_name, num_inner_instances, num_unique_inner_instances))
                else:
                    num_unique += 1
                    logging.debug("\t{} : unique num_inner={}, num_unique={}".format(inner_name, num_inner_instances, num_unique_inner_instances))
        logging.debug("\tnum_singletons={}, num_few={}, num_replicated={}, num_unique={}".format(num_singletons, num_few, num_replicated, num_unique))

        # All singletons
        if num_few == 0 and num_replicated == 0 and num_unique == 0:
            return "unique"
        # All singletons/few
        elif num_replicated == 0 and num_unique == 0:
            return "unknown"
        # No unique
        elif num_unique == 0:
            return "replicated"
        # More unique than not
        elif num_unique >= num_replicated:
            return "unique"
        # Mostly replicated
        elif num_unique/num_replicated < 0.15:
            return "replicated"
        else:
            return "unique"

if __name__ == "__main__":
    main()