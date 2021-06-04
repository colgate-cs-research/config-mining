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
        "interfaces" : extract_interfaces(node)
    }
    return parts

def extract_interfaces(node):
    return {}

if __name__ == "__main__":
    main()