#!/usr/bin/env python3

import argparse
import fileinput
import ipaddress
import json
import os
import sys

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
        infilepath = os.path.join(configs_path, filename)
        try:
            with open(infilepath, "r") as conf_file:
                conf = json.load(conf_file)
        except json.decoder.JSONDecodeError as ex:
            fix_aruba_json(infilepath)
            try:
                with open(infilepath, "r") as conf_file:
                    conf = json.load(conf_file)
            except json.decoder.JSONDecodeError as ex:
                print("Failed to parse {}: {}".format(filename, ex))
                continue
        parts = extract_node(node, conf)
        with open(os.path.join(json_path, node + ".json"), 'w') as json_file:
            json.dump(parts, json_file, indent=4, sort_keys=True)

def fix_aruba_json(filepath):
    with fileinput.FileInput(filepath, inplace='True') as conf_file:
        for line in conf_file:
            if '"cfg_version"' in line and line.count('"') != 4:
                pre, post = line.rstrip().split(':')
                print('{}: "{}",'.format(pre, post[1:-1]))
            elif '"name"' in line and line.count('"') != 4:
                pre, post = line.rstrip(",\n").split(':')
                print('{}: {}"{}'.format(pre, post[1:], ("," if line[-2] == "," else "")))
            else:
                print(line, end='')

def extract_node(node, conf):
    parts = {
        "name" : node,
        "interfaces" : extract_interfaces(conf),
        "acls" : extract_acls(conf),
        "vlans" : extract_vlans(conf),
        "lags" : extract_lags(conf),
    }
    return parts

def extract_interfaces(conf):
    """Extract details for all interfaces on a node"""
    interfaces = {}
    
    # Iterate over all ports in Aruba config
    for port in conf["Port"].values():
        # Attempt to find corresponding interface in Aruba config
        iface = {}
        if "interfaces" in port and len(port["interfaces"]) == 1:
            iface_name = port["interfaces"][0]
            if iface_name in conf["Interface"]:
                iface = conf["Interface"][iface_name]
            else:
                print("WARNING: interface '{}' associated with port '{}' does not exist".format(iface_name, port["name"]))

        # Extra interface details
        interface = {
            "name" : port["name"],
            "description" : (iface["description"] if "description" in iface else None),
            "address" : (port["ip4_address"] if "ip4_address" in port else None),
            "switchport" : (None if len(port) == 0 else ("trunk" if "vlan_trunks" in port else "access")),
            "access_vlan" : (int(port["vlan_tag"]) if "vlan_tag" in port else None),
            "allowed_vlans" : (sorted([int(v) for v in port["vlan_trunks"]]) if "vlan_trunks" in port else None),
            "in_acl" : None, # FIXME
            "out_acl" : (port["aclv4_routed_out_cfg"].split('/')[0] if "aclv4_routed_out_cfg" in port else None),
            "lag" : (int(iface["other_config"]["lacp-aggregation-key"]) if ("other_config" in iface and "lacp-aggregation-key" in iface["other_config"]) else None)
        }

        interfaces[interface["name"]] = interface

    # Iterate over interfaces that do not have a directly corresponding port
    remain = set(conf["Interface"].keys()) - set(interfaces.keys())
    for iface_name in remain:
        iface = conf["Interface"][iface_name]

        # Extract interface details
        interface = {
            "name" : iface["name"],
            "description" : (iface["description"] if "description" in iface else None),
            "address" : None,
            "switchport" : None,
            "access_vlan" : None,
            "allowed_vlans" : None,
            "in_acl" : None,
            "out_acl" : None,
            "lag" : (int(iface["other_config"]["lacp-aggregation-key"]) if ("other_config" in iface and "lacp-aggregation-key" in iface["other_config"]) else None)
        }

        interfaces[interface["name"]] = interface

    return interfaces

def extract_acls(conf):
    """Extract details for all ACLs on a node"""
    acls = {}
    for acl_conf in conf["ACL"].values():
        lines, remarks = extract_acl_parts(acl_conf["cfg_aces"], acl_conf["name"])
        acl  = {
            "name" : acl_conf["name"],
            "lines" : lines,
            "remarks" : remarks
        }

        acls[acl["name"]] = acl
    
    return acls

def extract_acl_parts(acl_conf, acl_name):
    """Extract match criteria for all lines in an ACL"""
    lines = []
    remarks = []

    for priority in sorted([int(prio) for prio in acl_conf.keys()]):
        line_conf = acl_conf[str(priority)]

        if "action" in line_conf:
            srcIps = "0.0.0.0/0"
            if "src_ip" in line_conf:
                try:
                    srcIps = str(ipaddress.ip_network(line_conf["src_ip"]))
                except ValueError as err:
                    print("WARNING: rule {} in ACL '{}': {}".format(priority, acl_name, err))

            dstIps = None
            if "dst_ip" in line_conf:
                try:
                    dstIps = str(ipaddress.ip_network(line_conf["dst_ip"]))
                except ValueError as err:
                    print("WARNING: rule {} in ACL '{}': {}".format(priority, acl_name, err))

            line = {
                "action" : (line_conf["action"] if "action" in line_conf else None),
                "srcIps" : srcIps,
            }
            if dstIps is not None:
                line["dstIps"] = dstIps

            lines.append(line)

        if "comment" in line_conf:
            remarks.append(line_conf["comment"])
    
    return lines, remarks

def extract_vlans(conf):
    """Extract all VLAN names from all VLANs on a node"""
    vlans = {}
    for vlan_conf in conf["VLAN"].values():
        vlan_num = vlan_conf["id"]
        iface_name = "vlan{}".format(vlan_num)
        vlan = {
            "num" : vlan_num,
            "name" : (vlan_conf["name"] if "name" in vlan_conf else None),
            "interface" : (iface_name if iface_name in conf["Port"] else None)
        }
        
        vlans[vlan["num"]] = vlan

    return vlans

def extract_lags(conf):
    """Extract all LAGs on a node"""
    lags = {}

    # Look for LAG ports
    for port_name in conf["Port"].keys():
        if port_name.startswith("lag"):
            lag = {
                "num" : int(port_name[3:]),
                "interface" : port_name,
            }
            lags[lag["num"]] = lag

    return lags

if __name__ == "__main__":
    main()