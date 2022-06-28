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
    #"security",
    #"routing-options",
    "protocols",
    "policy-options", 
    #"class-of-service",
    "firewall", 
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
KEYKINDS_JUNIPER = {
    (('name', '*'), ('type', 'firewall'), ('type', 'family inet'), ('type', 'filter')) : "name",
    (('name', '*'), ('type', 'policy-options'), ('type', 'as-path')) : "name",
    (('name', '*'), ('type', 'policy-options'), ('type', 'policy-statement'), ('name', '*'), ('type', 'term'), ('name', '*'), ('type', 'to')): "mixed",
    (('name', '*'), ('type', 'groups')) : "name",
    (('name', '*'), ('type', 'interfaces'), ('name', '*'), ('type', 'unit'), ('name', '*'), ('mixed', ('family', '*')), ('type', 'filter'), ('type', 'input-list')): "name",
    (('name', '*'), ('type', 'interfaces'), ('name', '*'), ('type', 'unit'), ('name', '*'), ('mixed', ('family', '*')), ('type', 'filter'), ('type', 'output-list')): "name",
#    (('name', '*'), ('type', 'security'), ('type', 'pki')): "mixed",
}
KEYKINDS_ARUBA = {
    (('name', '*'), ('type', 'AAA_Server_Group')) : "name",
    (('name', '*'), ('type', 'ACL')) : "name",
    (('name', '*'), ('type', 'Class'), ('name', '*')) : "type",
    (('name', '*'), ('type', 'Port'), ('name', '*')): "type",
    (('name', '*'), ('type', 'VRF')) : "name",
    (('name', '*'), ('type', 'VRF'), ('name', '*'), ('type', 'NTP_Association')): 'name',
    (('name', '*'), ('type', 'VRF'), ('name', '*'), ('type', 'Radius_Server')): 'name',
    (('name', '*'), ('type', 'VRF'), ('name', '*'), ('type', 'Radius_Dynamic_Authorization_Client')): "name",
    (('name', '*'), ('type', 'VRF'), ('name', '*'), ('type', 'Static_Route')): 'name',
    (('name', '*'), ('type', 'VRF'), ('name', '*'), ('type', 'Tacacs_Server')): 'name',
    (('name', '*'), ('type', 'VRF'), ('name', '*'), ('type', 'dns_host_v4_address_mapping')): "name",
    (('name', '*'), ('type', 'VRF'), ('name', '*'), ('type', 'ospf_routers'), ('name', '*'), ('type', 'areas')): "name",
    (('name', '*'), ('type', 'VRF'), ('name', '*'), ('type', 'pim_routers')): "type",
    (('name', '*'), ('type', 'VRF'), ('name', '*'), ('type', 'pim_routers'), ('type', 'ipv4')) : "type"
}
TOP_LEVEL_TYPES = TOP_LEVEL_TYPES_JUNIPER + TOP_LEVEL_TYPES_ARUBA
KEYKINDS = KEYKINDS_JUNIPER
KEYKINDS = KEYKINDS_ARUBA

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Infer symbols from network configurations")
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

    extractor = SymbolExtractor(all_configs, symbol_table)

    # Create output directory
    os.makedirs(arguments.output_dir, exist_ok=True)
    
    # Save output
    with open(os.path.join(arguments.output_dir, "symbols.json"), 'w') as symbols_file:
        json.dump(symbol_table, symbols_file, indent=4, sort_keys=True)
    pickle_keykinds = {str(k) : v for k,v in extractor.keykinds.items()}
    with open(os.path.join(arguments.output_dir, "keykinds.json"), 'w') as keykinds_file:
        json.dump(pickle_keykinds, keykinds_file, indent=4, sort_keys=True)
    with open(os.path.join(arguments.output_dir, "typescopes.json"), 'w') as typescopes_file:
        json.dump(extractor.typescopes, typescopes_file, indent=4, sort_keys=True)

class SymbolExtractor:
    def __init__(self, config, symbol_table={}):
        self.config = config
        self.symbol_table = symbol_table
        self.keykinds = KEYKINDS
        self.mixedkinds = {}
        self.typescopes = {}

        # Iterate over top-level types of interest (e.g., ACLs, interfaces, etc.)
        for node in config:
            for symbol_type in TOP_LEVEL_TYPES:
                if symbol_type not in config[node]:
                    continue
                self.parse_dict(config[node][symbol_type], [("name", node), ("type", symbol_type)])

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
                try:
                    logging.debug("\t{}".format(d.keys()))
                except Exception as ex:
                    logging.error("Mixed subinstances for {}".format(path))

            kind = self.infer_keykind(dictionaries)
            self.keykinds[path_signature] = kind

            if kind == "unknown":
                logging.error("!Cannot infer key kind for {}".format(path))
        logging.debug("Dict keys are {}s".format(kind))
        if (kind == "name"):
            self.extract_symbols_key_name(dct, path)
        elif (kind == "type"):
            self.extract_symbols_key_type(dct, path)
        elif (kind == "pair"):
            self.extract_symbols_key_pair(dct, path)
        elif (kind == "mixed"):
            self.extract_symbols_key_mixed(dct, path)
        else:
            logging.debug("!Not recursing on dict of {}s: {}".format(kind, path))

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
        else:
            logging.debug("!Not recursing on list of {}s: {}".format(kind, path))

    def get_path_signature(self, path):
        signature = []
        for component in path:
            if component[0] == "name":
                signature.append(("name", "*"))
            elif component[0] == "pair":
                signature.append(("pair", (component[1][0], "*")))
            elif component[0] == "mixed":
                if len(component[1]) == 2:
                    signature.append(("mixed", (component[1][0], "*")))
                else:
                    signature.append(("mixed", (component[1][0],)))
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
                    result.append(dct[id])
            elif kind == "pair":
                for key, value in dct.items():
                    id_type, id_name = key.replace("inactive: ", "").split(' ')
                    if id_type == id[0] and (isinstance(value, dict) or isinstance(value, list)):
                        result.append(dct[key])
            elif kind == "name":
                for value in dct.values():
                    if isinstance(value, dict) or isinstance(value, list):
                        result.append(value)
            elif kind == "mixed":
                for key, value in dct.items():
                    if key.replace("inactive: ", "").count(' ') == 1:
                        id_type, id_name = key.replace("inactive: ", "").split(' ')
                        if id_type == id[0] and (isinstance(value, dict) or isinstance(value, list)):
                            result.append(dct[key])
                    else:
                        id_type = key.replace("inactive: ", "")
                        if id_type == id[0] and (isinstance(value, dict) or isinstance(value, list)):
                            result.append(dct[key]) 
            else:
                raise Exception("Unknown kind {} in signature {}".format(kind, signature))
        # Recursive case
        else:
            if kind == "type":
                if id in dct and isinstance(dct[id], dict):
                    result = self.get_instances(dct[id],signature[1:])
            elif kind == "pair":
                for key, value in dct.items():
                    id_type, id_name = key.replace("inactive: ", "").split(' ')
                    if id_type == id[0] and isinstance(value, dict):
                        result.extend(self.get_instances(value, signature[1:]))
            elif kind == "name":
                for value in dct.values():
                    if isinstance(value, dict):
                        result.extend(self.get_instances(value, signature[1:]))
            elif kind == "mixed":
                for key, value in dct.items():
                    if key.replace("inactive: ", "").count(' ') == 1:
                        id_type, id_name = key.replace("inactive: ", "").split(' ')
                        if id_type == id[0] and isinstance(value, dict):
                            result.extend(self.get_instances(value, signature[1:]))
                    elif key.replace("inactive: ", "") == id[0] and isinstance(dct[key], dict):
                        result = self.get_instances(dct[key],signature[1:])
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
                subdict_unique_keys.update([(k.replace("inactive: ") if k.startswith("inactive: ") else k) for k in value.keys()])
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
                unique_keys.update([(k[len("inactive: "):] if k.startswith("inactive: ") else k) for k in inst.keys()])
            elif isinstance(inst, list):
                num_keys += len(inst)
                unique_keys.update(inst)
        num_unique_keys = len(unique_keys)
        num_unique_keys_with_spaces = 0
        num_unique_keys_with_single_space = 0
        for key in unique_keys:
            if " " in key:
                num_unique_keys_with_spaces += 1 
                logging.debug(key)
                if key.count(" ") == 1:
                    num_unique_keys_with_single_space += 1
        logging.debug("\tTotal dict: {}".format(num_inst))
        logging.debug("\tUnique sub keys {}".format(num_unique_keys))
        logging.debug("\tUnique sub keys with single space {}".format(num_unique_keys_with_single_space)) 
        logging.debug("\tUnique sub keys with spaces {}".format(num_unique_keys_with_spaces)) 
        logging.debug("\tTotal sub keys {}".format(num_keys))
        if (num_keys == 0):
            return "unknown"
        elif (num_unique_keys_with_single_space == num_unique_keys):
            return "pair"
        elif (num_unique_keys_with_spaces > 0):
            return "mixed"
        elif (num_unique_keys / num_keys > 0.2) or num_unique_keys > 25:
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
            self.add_to_symbol_table(symbol_type, symbol_name, path)
            if isinstance(symbol_value, dict):
                self.parse_dict(symbol_value, path + [('name', symbol_name)])
            elif isinstance(symbol_value, list):
                self.parse_list(symbol_value, path + [('name', symbol_name)])

    def extract_symbols_key_type(self, dct, path):
        # Treat keys as symbol types 
        for symbol_type, value in dct.items():
            if isinstance(value, dict):
                self.parse_dict(value, path + [('type', symbol_type.replace("inactive: ", ""))])
            elif isinstance(value, list):
                self.parse_list(value, path + [('type', symbol_type.replace("inactive: ", ""))])
            elif isinstance(value, str) or isinstance(value, int):
                self.add_to_symbol_table(symbol_type, str(value), path)
    
    def extract_symbols_key_pair(self, dct, path):
        # Treat keys as pairs of symbol type and name
        for symbol_pair, value in dct.items():
            symbol_type, symbol_name = symbol_pair.replace("inactive: ", "").split(" ")
            self.add_to_symbol_table(symbol_type, symbol_name, path)
            if isinstance(value, dict):
                self.parse_dict(value, path + [('pair', (symbol_type, symbol_name))])
            elif isinstance(value, list):
                self.parse_list(value, path + [('pair', (symbol_type, symbol_name))])

    def extract_symbols_key_mixed(self, dct, path):
        # Treat keys as symbol types or pairs of symbol type and name
        for key, value in dct.items():
            if key.replace("inactive: ", "").count(' ') == 1:
                symbol_type, symbol_name = key.replace("inactive: ", "").split(" ")
                self.add_to_symbol_table(symbol_type, symbol_name, path)
                if isinstance(value, dict):
                    self.parse_dict(value, path + [('mixed', (symbol_type, symbol_name))])
                elif isinstance(value, list):
                    self.parse_list(value, path + [('mixed', (symbol_type, symbol_name))])
            else:
                symbol_type = key.replace("inactive: ", "")
                if isinstance(value, dict):
                    self.parse_dict(value, path + [('mixed', (symbol_type,))])
                elif isinstance(value, list):
                    self.parse_list(value, path + [('mixed', (symbol_type,))])
                elif isinstance(value, str) or isinstance(value, int):
                    self.add_to_symbol_table(symbol_type, str(value), path)

    def extract_symbols_list_name(self, lst, path):
        # Treat values as symbol names
        symbol_type = None
        if path[-1][0] == "type":
            symbol_type = path[-1][1]
        for symbol_name in lst:
            self.add_to_symbol_table(symbol_type, symbol_name, path)

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
                self.add_to_symbol_table(symbol_type, symbol_name, path)
            # Symbol type and list of names
            elif ' [' in symbol and symbol[-1] == ']':
                symbol_type, symbol_names = symbol[:-1].split('[')
                symbol_type = symbol_type[:-1] # Strip space
                symbol_names = symbol_names.split(',')
                for symbol_name in symbol_names:
                    symbol_name = symbol_name.strip("', ")
                    self.add_to_symbol_table(symbol_type, symbol_name, path)
            # Symbol type and list of names
            elif ' (' in symbol and symbol[-1] == ')':
                symbol_type, symbol_names = symbol[:-1].split('(')
                symbol_type = symbol_type[:-1] # Strip space
                symbol_names = symbol_names.split("&&")
                for symbol_name in symbol_names:
                    symbol_name = symbol_name.strip("', ")
                    self.add_to_symbol_table(symbol_type, symbol_name, path)
            else:
                logging.warning("!Cannot infer symbol name/type for mixed value: {}".format(symbol))

    def add_to_symbol_table(self, symbol_type, symbol_name, path):
        # Put type in canonical form
        if symbol_type != None:
            symbol_type = symbol_type.lower()

        # Don't add booleans
        if str(symbol_name).lower() in ["true", "false"]:
            return
        
        logging.debug("Adding {} {} to symbol table".format(symbol_type, symbol_name))

        # Normalize descriptions and names
        if symbol_type == "description" or symbol_type == "name":
            symbol_name = symbol_name.strip(" *").lower()

        # Add to symbol table
        if symbol_name not in self.symbol_table:
            self.symbol_table[symbol_name] = []
        if symbol_type != None and symbol_type not in self.symbol_table[symbol_name]:
            self.symbol_table[symbol_name].append(symbol_type)

        if (symbol_type != None and symbol_type not in self.typescopes):
            path_signature = self.get_path_signature(path)
            typescope = self.infer_typescope(path_signature)
            if typescope == "replicated":
                self.typescopes[symbol_type] = "replicated"
            else:
                self.typescopes[symbol_type] = path_signature

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

    def infer_typescope(self, path_signature):
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