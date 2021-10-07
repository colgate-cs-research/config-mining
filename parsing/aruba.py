#!/usr/bin/env python3

import argparse
import ipaddress
import json
import os

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('snapshot_path', help='provide path to the network snapshot')
    parser.add_argument('-v', '--verbose', action='store_true', help="Display verbose output")
    arguments = parser.parse_args()

    # Determine paths
    configs_path = os.path.join(arguments.snapshot_path, "configs")
    json_path = os.path.join(arguments.snapshot_path, "configs_json")
    os.makedirs(json_path, exist_ok=True)
    
    # Parse each configuration
    for filename in sorted(os.listdir(configs_path)):
        node = filename.replace(".colgate.edu.json", "")
        with open(os.path.join(configs_path, filename), "r") as conf_file:
            conf = json.load(conf_file)
        parts = extract_node(node, conf)
        with open(os.path.join(json_path, node + ".json"), 'w') as json_file:
            json.dump(parts, json_file, indent=4, sort_keys=True)
        break

def extract_node(node, conf):
    parts = {
        "name" : node,
        "interfaces" : extract_interfaces(conf),
#        "acls" : extract_acls(conf),
#        "vlans" : extract_vlans(conf),
    }
#    extract_acl_remarks(parts, raw_lines)
#    resolve_acls_aliases(parts["acls"])
    return parts

def extract_interfaces(conf):
    """Extract details for all interfaces on a node"""
    interfaces = {}
    
    for port in conf["Port"].values():
        html_name = port["name"].replace("/", "%2F")
        iface = (conf["Interface"][html_name] if html_name in conf["Interface"] else {})   

        interface = {
            "name" : port["name"],
            "description" : (iface["description"] if "description" in iface else None),
            "address" : (port["ip4_address"] if "ip4_address" in port else None),
            "switchport" : (None if len(port) == 0 else ("trunk" if "vlan_trunks" in port else "access")),
            "access_vlan" : (port["vlan_tag"] if "vlan_tag" in port else None),
            "allowed_vlans" : (sorted([int(v) for v in port["vlan_trunks"]]) if "vlan_trunks" in port else None)
        }

        interfaces[interface["name"]] = interface

    return interfaces

if __name__ == "__main__":
    main()