#!/usr/bin/env python3

import argparse
import os
import json
import sys
import ciscoconfparse
import pprint
import logging

TOP_LEVEL_PREFIXES = {
    ('router', 'ospf'): 3,
}

CHILD_SKIP = [
    '!',
    'exit-address-family',
]

CHILD_FLAT_PREFIXES = {
    ('description',): 1,
    ('switchport','mode'): 2,
    ('standby','version'): 2,
    ('ip','address'): 2,
    ('ip','helper-address'): 2,
    ('ip','flow'): 2,
    ('ipv6','address'): 2,
    ('spanning-tree','status'): 2,
    ('ip','redirects'): 2,
    ('ip','proxy-arp'): 2,
    ('passive-interface',): 2,
    ('location',): 1,
    ('contact',): 1,
    ('seq',): 2,
}

CHILD_NESTED_PREFIXES = {
    ('spanning-tree',): 1,
    ('logging','event'): 2,
    ('switchport', 'trunk'): 2,
    ('storm-control',): 2,
    ('channel-group',): 2,
    ('ip', 'access-group'): 2,
    ('ip', 'multicast'): 2,
    ('ip', 'igmp'): 2,
    ('pim',): 1,
    ('ipv6', 'nd'): 2,
    ('ipv6', 'pim'): 2,
    ('standby',): 2,
    ('neighbor',): 2,
    ('ip', 'rip'): 2,
    ('allowed','vlan'): 2,
    ('allowed','vlan','add'): 2,
    ('network',): 3,
    ('access-list',): (2,list),
    ('flow-export',): 1,
    ('prefix-list',): 2,
    ('snmp-server',): 1,
    ('radius-server',): 1,
    ('logging',): 1,
    ('service',): 2,
    ('ssh',): 1,
    ('telnet',): 1,
    ('tftp',): 1,
    ('login',): 1,
    ('mls',): 1,
    ('diagnostic',): 1,
    ('ntp',): 1,
    ('access-group',): 1,
    ('server',): 2,
    ('flow-cache',): 1,
    ('clock',): 1,
    ('aaa',): 1,
    ('ip',): 1,
    ('name-server',): (1,list),
    ('forward-protocol',): (1,list),
    ('route',): (1,list),
    ('http',): 1,
    ('errdisable',): 1,
    ('ipv6',): 1,
    ('standard'): (3, list),
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
        parts = parent.text.split(' ')
        details = add_to_config(json_config, parts)
        children = parent.children
        add_children(details, children)

    logging.debug("NON_PARENTS")
    for non_parent in non_parents:
        add_child(json_config, non_parent.text)


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
        if child.children:
            logging.debug("{} has children:".format(child))
            parts = child.text.strip().split(' ')
            details = add_to_config(parent, parts) 
            grandchildren = child.children
            add_children(details, grandchildren)
        else:
            add_child(parent, child.text.strip()) 

def add_child(parent, child, enabled=True):
    # Handle no commands
    if child.startswith("no "):
        child = child[len("no "):]
        enabled = False

    if child in CHILD_SKIP:
        return None

    # Infer how to add child
    parts = child.split(' ')
    if isinstance(parent, list):
        parent.append(child)
    elif len(parts) >= 2 and (parts[0],parts[1]) in CHILD_FLAT_PREFIXES:
        prefix = (parts[0],parts[1])
        add_child_flat(prefix, parts, parent, enabled)
    elif len(parts) >= 1 and (parts[0],) in CHILD_FLAT_PREFIXES:
        prefix = (parts[0],)
        add_child_flat(prefix, parts, parent, enabled)
    elif len(parts) > 3 and (parts[0],parts[1],parts[2]) in CHILD_NESTED_PREFIXES:
        prefix = (parts[0],parts[1],parts[2])
        return add_child_nested(prefix, parts, parent, enabled)
    elif len(parts) > 2 and (parts[0],parts[1]) in CHILD_NESTED_PREFIXES:
        prefix = (parts[0],parts[1])
        return add_child_nested(prefix, parts, parent, enabled)
    elif len(parts) > 1 and (parts[0],) in CHILD_NESTED_PREFIXES:
        prefix = (parts[0],)
        return add_child_nested(prefix, parts, parent, enabled)
    elif len(parts) == 1:
        parent[parts[0]] = enabled
    elif len(parts) == 2:
        parent[parts[0]] = parts[1]
    else:
        parent[child] = None

    return None

def add_child_flat(prefix, parts, parent, enabled):
    splitpoint = CHILD_FLAT_PREFIXES[prefix]
    if splitpoint > len(prefix):
        joinchar = ' '
    else:
        joinchar = '-'
    key = joinchar.join(parts[:splitpoint])
    remainpoint = max(splitpoint,len(prefix))
    value = ' '.join(parts[remainpoint:])
    parent[key] = value

def add_child_nested(prefix, parts, parent, enabled):
    if isinstance(CHILD_NESTED_PREFIXES[prefix], tuple):
        splitpoint, datastruct = CHILD_NESTED_PREFIXES[prefix]
    else:
        splitpoint = CHILD_NESTED_PREFIXES[prefix]
        datastruct = dict
    if splitpoint > len(prefix):
        joinchar = ' '
    else:
        joinchar = '-'
    outer_key = joinchar.join(parts[:splitpoint])
    if outer_key not in parent:
        parent[outer_key] = datastruct()
    nested = parent[outer_key]

    remainpoint = max(splitpoint,len(prefix)) 
    if parts[remainpoint:]:
        remain = ' '.join(parts[remainpoint:])
        add_child(nested, remain, enabled)

    return nested

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
