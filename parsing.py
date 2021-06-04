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

    json_path = os.path.join(snapshot_path, "configs_json")
    os.makedirs(json_path, exist_ok=True)

    # Get list of devices
    nodes = bfq.nodeProperties().answer().frame()
    for node in nodes["Node"]:
        parts = extract_node(node)
        with open(os.path.join(json_path, node + ".json"), 'w') as json_file:
            json.dump(parts, json_file, indent=4)

def extract_node(node):
    parts = {
        "name" : node,
        "interfaces" : extract_interfaces(node),
        "acls" : extract_acls(node)
    }
    return parts

def extract_interfaces(node):
    interfaces = {}
    
    data = bfq.interfaceProperties(nodes=node, excludeShutInterfaces=False).answer().frame()

    for i,row in data.iterrows():
        interface = {
            "name" : row["Interface"].interface,
            "in_acl" : row["Incoming_Filter_Name"],
            "out_acl" : row["Outgoing_Filter_Name"],
            "description" : row["Description"],
            "address" : row["Primary_Address"]
        }
        interfaces[interface["name"]] = interface

    return interfaces

def extract_acls(node):
    acls = {}

    data = bfq.namedStructures(nodes=node,structureTypes="IP_ACCESS_LIST").answer().frame()

    for i,row in data.iterrows():
        acl = {
            "name" : row["Structure_Name"],
            "lines" : extract_acl_lines(row["Structure_Definition"]["lines"])
        }
        acls[acl["name"]] = acl

    return acls

def extract_acl_lines(data):
    lines = []

    

    for row in data:
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

if __name__ == "__main__":
    main()