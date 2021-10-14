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
        print(node)
        with open(os.path.join(configs_path, filename), "r") as conf_file:
            conf = json.load(conf_file)
        parts = extract_node(node, conf)
        with open(os.path.join(json_path, node + ".json"), 'w') as json_file:
            json.dump(parts, json_file, indent=4, sort_keys=True)

def extract_node(node, conf):
    parts = {
        "name" : node,
        "interfaces" : extract_interfaces(conf),
        "acls" : extract_acls(conf),
        "vlans" : extract_vlans(conf),
    }
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
            "allowed_vlans" : (sorted([int(v) for v in port["vlan_trunks"]]) if "vlan_trunks" in port else None),
            "in_acl" : None, # FIXME
            "out_acl" : None # FIXME
        }

        interfaces[interface["name"]] = interface

    return interfaces

def extract_acls(conf):
    """Extract details for all ACLs on a node"""
    acls = {}
    for acl_conf in conf["ACL"].values():
        lines, remarks = extract_acl_parts(acl_conf["cfg_aces"])
        acl  = {
            "name" : acl_conf["name"],
            "lines" : lines,
            "remarks" : remarks
        }

        acls[acl["name"]] = acl
    
    return acls

def extract_acl_parts(acl_conf):
    """Extract match criteria for all lines in an ACL"""
    lines = []
    remarks = []

    for priority in sorted([int(prio) for prio in acl_conf.keys()]):
        line_conf = acl_conf[str(priority)]

        if "action" in line_conf:
            srcIps = None
            if "src_ip" in line_conf:
                try:
                    srcIps = str(ipaddress.ip_network(line_conf["src_ip"]))
                except ValueError as err:
                    print(err)

            dstIps = None
            if "dst_ip" in line_conf:
                try:
                    dstIps = str(ipaddress.ip_network(line_conf["dst_ip"]))
                except ValueError as err:
                    print(err)

            line = {
                "action" : (line_conf["action"] if "action" in line_conf else None),
                "srcIps" : srcIps,
                "dstIps" : dstIps,
            }

            lines.append(line)

        if "comment" in line_conf:
            remarks.append(line_conf["comment"])
    
    return lines, remarks

def extract_vlans(conf):
    """Extract all VLAN names from all VLANs on a node"""
    vlans = {}
    for vlan_conf in conf["VLAN"].values():
        vlan = {
            "num" : vlan_conf["id"],
            "name" : (vlan_conf["name"] if "name" in vlan_conf else None)
        }
        
        vlans[vlan["num"]] = vlan

    return vlans

if __name__ == "__main__":
    main()