#!/usr/bin/env python3

import argparse
import os
import json
import sys
import ciscoconfparse
import pprint
import logging

TOP_LEVEL_PREFIXES = [
    "ip access-list standard",
    "ip access-list extended"
]

CHILD_FLAT_PREFIXES = [
    ('description',),
    ('switchport','mode'),
    ('standby','version'),
    ('ip','address'),
    ('ip','helper-address'),
    ('ip','flow'),
    ('ipv6','address'),
]

CHILD_NESTED_PREFIXES = {
    ('spanning-tree',): 1,
    ('logging','event'): 2,
    ('switchport', 'trunk'): 2,
    ('storm-control',): 2,
    ('channel-group',): 2,
    ('ip', 'access-group'): 2,
    ('ip', 'multicast'): 2,
    ('ip', 'igmp'): 2,
    ('ip', 'pim'): 2,
    ('ipv6', 'nd'): 2,
    ('ipv6', 'pim'): 2,
    ('standby',): 2,
}

def jsonify_config(config_filepath, output_dir):
    """Create a JSON-ified version of a single Cisco configuration"""
    logging.info("JSONifying {}...".format(os.path.basename(config_filepath)))

    parse = ciscoconfparse.CiscoConfParse(config_filepath)

    raw_config = parse.objs
    json_config = {}
    parents, non_parents = raw_config.config_hierarchy()

    logging.debug("PARENTS")
    for parent in parents:
        line = parent.text
        if line.count(" ") == 1:
            logging.debug(line.split(" "))
        else:
            logging.debug(line)
        details = add_to_config(json_config, line.split(" "))
        children = parent.children
        add_children(details, children)
        

    logging.debug("NON_PARENTS")
    for non_parent in non_parents:
        logging.debug(non_parent.text)


    with open(os.path.join(output_dir, os.path.basename(config_filepath).replace(".cfg", ".json")), 'w') as out_file:
        json.dump(json_config, out_file, indent=4, sort_keys=False)

def add_to_config(dct, parts):
    if parts[0] not in dct:
        dct[parts[0]] = {}
    if len(parts) > 1:
        return add_to_config(dct[parts[0]], parts[1:])
    else:
        return dct[parts[0]]

def add_children(parent, children):
    for child in children:
        child = child.text.strip()
        if child.startswith("no "):
            child = child[len("no "):]
            enabled = False
        else:
            enabled = True
        parts = child.split(' ')
        if len(parts) > 1 and (parts[0],) in CHILD_FLAT_PREFIXES:
            parent[parts[0]] = ' '.join(parts[1:])
        elif len(parts) > 2 and (parts[0],parts[1]) in CHILD_FLAT_PREFIXES:
            parent['-'.join(parts[:2])] = ' '.join(parts[2:])
        elif len(parts) > 1 and (parts[0],) in CHILD_NESTED_PREFIXES:
            prefix = (parts[0],)
            add_child_nested(prefix, parts, parent)
        elif len(parts) > 2 and (parts[0],parts[1]) in CHILD_NESTED_PREFIXES:
            prefix = (parts[0],parts[1])
            add_child_nested(prefix, parts, parent)
        elif len(parts) == 1:
            parent[parts[0]] = enabled
        elif len(parts) == 2:
            parent[parts[0]] = parts[1]
        else:
            parent[child] = None

def add_child_nested(prefix, parts, parent):
    splitpoint = CHILD_NESTED_PREFIXES[prefix]
    if splitpoint == 2 and len(prefix) == 1:
        joinchar = ' '
    else:
        joinchar = '-'
    outer_key = joinchar.join(parts[:splitpoint])
    if outer_key not in parent:
        parent[outer_key] = {}
    nested = parent[outer_key]

    remain = parts[splitpoint:]
    if len(remain) == 1:
        nested[remain[0]] = True
    elif len(remain) == 2:
        nested[remain[0]] = remain[1]
    else:
        nested[' '.join(remain)] = None 

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Convert Cisco IOS configs to JSON format')
    parser.add_argument('config_path',type=str, help='Path to a (directory of) Cisco configuration file(s)')
    parser.add_argument('output_dir',type=str, help='Directory in which to store the JSONified configuration(s)')
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

    # Create output directory
    os.makedirs(arguments.output_dir, exist_ok=True)

    # Determine whether to process a single configuration or a directory of configurations
    if os.path.isfile(arguments.config_path):
        jsonify_config(arguments.config_path, arguments.output_dir)
    else:
        for filename in os.listdir(arguments.config_path):
            jsonify_config(os.path.join(arguments.config_path, filename), arguments.output_dir)

if __name__ == "__main__":
    main()
