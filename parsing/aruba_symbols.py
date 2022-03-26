#!/usr/bin/env python3

import argparse
import json
import os
import pprint
import ipaddress

TOP_LEVEL_TYPES = [
    "ACL", 
    "Interface", 
    "Port", 
    "VLAN", 
    "User", 
    "User_Group", 
    "VRF"
]
IGNORED_TYPES = [
    "cfg_version"
]
TYPEDEFS = {
    "aclmac_in_cfg": "acl", 
    "aclv4_control_plane_cfg": "acl", 
    "aclv4_routed_out_cfg": "acl", 
    "aclmac_in_cfg_version": "cfg_version", 
    "aclv4_control_plane_cfg_version": "cfg_version",
    "aclv4_routed_out_cfg_version": "cfg_version",
    "interfaces": "interface",
    "active_interfaces": "interface",
    "source_interface": "interface",
    "ip_address" : "ip4_address",
    "dst_ip": "ip4_address",
    "src_ip": "ip4_address",
    "vsx_virtual_ip4": "ip4_address",
    "dns_host_v4_address_mapping": "ip4_address",
    "loop_protect_vlan": "vlan", 
    "vlan_tag": "vlan", 
    "vlan_trunks": "vlan",
    "id": "vlan",
    "dst_l4_port_min": "l4_port",
    "dst_l4_port_max": "l4_port",
    "src_l4_port_min": "l4_port",
    "src_l4_port_max": "l4_port",
    "dst_mac": "mac_address",
    "src_mac": "mac_address"
}
SUB_TYPES = [
    "dns_host_v4_address_mapping",
    "dns_name_servers",
    "source_interface",
    "pim_mode",
    "source_ip",
]

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('snapshot_path', help='provide path to the network snapshot')
    arguments = parser.parse_args()

    # Determine paths
    configs_path = os.path.join(arguments.snapshot_path, "configs")
    
    # Parse each configuration
    symbol_table = {}
    for filename in sorted(os.listdir(configs_path)):
        node = filename.replace(".colgate.edu.json", "")
        filepath = os.path.join(configs_path, filename)
        try:
            with open(filepath, "r") as config_file:
                config = json.load(config_file)
        except:
            print("Failed to parse {}".format(filepath))
            continue
        parse_config(config, symbol_table)

    # Determine all types
#    types = set()
#    for symbol_types in symbol_table.values():
#        types.update(symbol_types)
#    pprint.PrettyPrinter().pprint(types)

    symbols_filepath = os.path.join(arguments.snapshot_path, "symbols.json")  
    with open(symbols_filepath, 'w') as symbols_file:
        json.dump(symbol_table, symbols_file, indent=4, sort_keys=True)

def parse_config(config, symbol_table):
    # Iterate over top-level types of interest (e.g., ACLs, interfaces, etc.)
    for symbol_type in TOP_LEVEL_TYPES:
        if symbol_type not in config:
            continue
        extract_symbols_key_name(symbol_type, config[symbol_type], symbol_table)

def extract_symbols_key_name(symbol_type, symbols_dict, symbol_table):
    # Treat keys as symbol names
    for symbol_name, sub_symbols_dict in symbols_dict.items():
        add_to_symbol_table(symbol_name, symbol_type, symbol_table)
        extract_symbols_key_type_value_name(sub_symbols_dict, symbol_table)

def extract_symbols_value_name(symbol_type, symbols_dict, symbol_table):
    # Treat values as symbol names
    #print("extract_symbols_value_name({}, {})".format(symbol_type, symbols_dict))
    for symbol_name in symbols_dict.values():
        add_to_symbol_table(symbol_name, symbol_type, symbol_table)

def extract_symbols_key_type_value_name(sub_symbols_dict, symbol_table):
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
            if symbol_type in SUB_TYPES:
                extract_symbols_value_name(symbol_type, symbol_value, symbol_table)
            else:
                extract_symbols_key_type_value_name(symbol_value, symbol_table)

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