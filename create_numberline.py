#!/usr/bin/env python3

import argparse
import glob
import ipaddress
import json

def main():
    #parsing command-line arguments
    parser = argparse.ArgumentParser(description='Analyze confidence for vlan pairs')
    parser.add_argument('config_path', help='Path for a directory containing a JSON representation of configurations')
    #parser.add_argument('out_path', help='Name of file (or directory) to write JSON file(s) containing vlan confidence values')

    arguments = parser.parse_args()

    numberline = {}
    files = glob.glob(arguments.config_path + '/**/*.json', recursive=True)
    for filepath in files:
        device, addresses = extract_addresses(filepath)
        append_to_numberline(numberline, device, addresses)

    for addr in sorted(numberline.keys()):
        print(addr, numberline[addr])

"""Extract addresses for all interfaces from a configuration JSON"""
def extract_addresses(filepath):
    with open(filepath, 'r') as infile:
        config = json.load(infile)

    addresses = {}
    for iface in config["interfaces"].values():
        if iface["address"] is not None:
            addresses[iface["name"]] = (ipaddress.ip_interface(iface["address"]), iface["description"])

    return config["name"], addresses

def append_to_numberline(numberline, device, addresses):
    for iface, metadata in addresses.items():
        addr, description = metadata
        if addr not in numberline:
            numberline[addr] = []
        numberline[addr].append((device, iface, description))

if __name__ == "__main__":
    main()