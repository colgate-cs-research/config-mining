#!/usr/bin/env python3

import argparse
import json
import os
import pandas as pd
from pybatfish.client.commands import *
from pybatfish.datamodel import *
from pybatfish.datamodel.answer import *
from pybatfish.datamodel.flow import *
from pybatfish.question import *
from pybatfish.question import bfq
import re

def main():
     #parsing command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('snapshot_path', help='provide path to the network snapshot')
    arguments = parser.parse_args()

    # Reformat snapshot path, if necessary
    snapshot_path = arguments.snapshot_path
    if arguments.snapshot_path[-1] == '/':
        snapshot_path = snapshot_path[:len(snapshot_path)-1]

    # Parse configurations using Batfish
    bf_session.host = 'localhost'
    bf_set_network(os.path.basename(os.path.dirname(snapshot_path)))
    bf_init_snapshot(snapshot_path, name=os.path.basename(snapshot_path), overwrite=True)
    load_questions()

    configs_path = os.path.join(snapshot_path, "configs")
    json_path = os.path.join(snapshot_path, "configs_json")
    os.makedirs(json_path, exist_ok=True)

    # Create dictionary mapping nodes to files
    files = {}
    data = bfq.fileParseStatus().answer().frame()
    for i,row in data.iterrows():
        if (len(row["Nodes"]) == 1):
            files[row["Nodes"][0]] = row["File_Name"]

    # Get list of devices
    nodes = bfq.nodeProperties().answer().frame()
    for node in nodes["Node"]:
        with open(os.path.join(snapshot_path, files[node]), "r") as conf_file:
            raw_lines = conf_file.readlines()
        parts = extract_node(node, raw_lines)
        with open(os.path.join(json_path, node + ".json"), 'w') as json_file:
            json.dump(parts, json_file, indent=4, sort_keys=True)

def extract_node(node, raw_lines):
    parts = {
        "name" : node,
        "interfaces" : extract_interfaces(node),
        "acls" : extract_acls(node),
        "vlans" : extract_vlans(raw_lines)
    }
    extract_acl_remarks(parts, raw_lines)
    return parts

"""Extract details for all interfaces on a node"""
def extract_interfaces(node):
    interfaces = {}
    
    data = bfq.interfaceProperties(nodes=node, excludeShutInterfaces=False).answer().frame()

    for i,row in data.iterrows():
        interface = {
            "name" : row["Interface"].interface,
            "in_acl" : row["Incoming_Filter_Name"],
            "out_acl" : row["Outgoing_Filter_Name"],
            "description" : row["Description"],
            "address" : row["Primary_Address"],
            "switchport" : (None if row["Switchport_Mode"] == "NONE" else row["Switchport_Mode"].lower()),
            "access_vlan" : row["Access_VLAN"],
            "allowed_vlans" : convert_allowed_vlans(row["Allowed_VLANs"])
        }
        interfaces[interface["name"]] = interface

    return interfaces

"""Convert a string of allowed VLANs into a list"""
def convert_allowed_vlans(raw_string):
    # Handle empty string
    if len(raw_string) == 0:
        return None
       
    # Iterate over each item in the string of allowed VLANs
    full_list = []
    raw_list = raw_string.strip().split(",")
    for item in raw_list:
        # Range of VLANs
        if "-" in item:
            start, end = item.split("-")
            full_list.extend(list(range(int(start), int(end)+1)))
        # Single VLAN
        else:
            full_list.append(int(item))
    return full_list

"""Extract details for all ACLs on a node"""
def extract_acls(node):
    acls = {}

    data = bfq.namedStructures(nodes=node,structureTypes="IP_ACCESS_LIST").answer().frame()

    for i,row in data.iterrows():
        lines = None
        if "lines" in row["Structure_Definition"]:
            lines = extract_acl_lines(row["Structure_Definition"]["lines"])

        acl = {
            "name" : row["Structure_Name"],
            "lines" : lines,
            "remarks" : []
        }
        acls[acl["name"]] = acl

    return acls

"""Extract match criteria for all lines in an ACL"""
def extract_acl_lines(data):
    lines = []

    for row in data:
        if "conjuncts" in row["matchCondition"]:
            for conjunct in row["matchCondition"]["conjuncts"]:
                if "headerSpace" in conjunct:
                    match = conjunct["headerSpace"]
                    break
        else:
            match = row["matchCondition"]["headerSpace"]
        srcIps = None
        if "srcIps" in match and "ipWildcard" in match["srcIps"]:
            srcIps = match["srcIps"]["ipWildcard"]
        dstIps = None
        if "dstIps" in match and "ipWildcard" in match["dstIps"]:
            dstIps = match["dstIps"]["ipWildcard"]

        line = {
            "action" : row["action"],
            "srcIps" : srcIps,
            "dstIps" : dstIps
        }
        lines.append(line)

    return lines

#returns boolean indicating if argument regex pattern exists in argument string
def is_regex_match(pattern, line):
    p = re.compile(pattern)
    iList = p.findall(line)
    return (len(iList) > 0)

"""Extract all remarks from all ACLs on a node"""
def extract_acl_remarks(parts, raw_lines):
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i].strip()
        i += 1
        if is_regex_match('^ip access-list', line):
            name = line.split()[-1]
            line = raw_lines[i].strip()
            i += 1
            while (line != "!"):
                if is_regex_match('^remark ', line):
                    parts["acls"][name]["remarks"].append(line[7:])
                line = raw_lines[i].strip()
                i += 1

"""Extract all VLAN names from all VLANs on a node"""
def extract_vlans(raw_lines):
    vlans = {}
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        if (is_regex_match('^vlan \d+$', line)):
            temp = line.strip().split()
            num = int(temp[1])
            i += 1
            line = raw_lines[i]
            temp = line.strip().split()
            if temp[0] == "name":
                name = temp[1]
                vlans[num] = { "num" : num, "name" : name }
        i += 1

    return vlans

if __name__ == "__main__":
    main()