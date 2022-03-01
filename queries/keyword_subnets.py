#!/usr/bin/env python3

import argparse
import ipaddress
import json
import os

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Get all subnets associated with a keyword')
    parser.add_argument('config_path',type=str, help='Path for a file (or directory) containing a JSON representation of configuration(s)')
    parser.add_argument('keyword',type=str, help='Keyword to search for')
    parser.add_argument('-v', '--verbose', action='store_true', help="Display verbose output")
    arguments = parser.parse_args()

    if (arguments.verbose):
        print("DeviceName,IfaceName,IfaceDescription,IfaceAddress")

    if os.path.isdir(arguments.config_path):
        all_addresses = process_dir(arguments.config_path, arguments.keyword, arguments.verbose)
    else:
        all_addresses = process_file(arguments.config_path, arguments.keyword, arguments.verbose)

    aggregated_prefixes = aggregate_addresses(all_addresses)
    for prefix in aggregated_prefixes:
        print(str(prefix))

def process_dir(dirpath, keyword, verbose=False):
    all_addresses = []
    for filename in os.listdir(dirpath):
        device_addresses = process_file(os.path.join(dirpath, filename), keyword, verbose)
        all_addresses.extend(device_addresses)
    return all_addresses

def process_file(filepath, keyword, verbose=False):
    print(filepath)
    with open(filepath) as json_file:
        config = json.load(json_file)

    hostname = config["name"]
    addresses = []

    # Find interfaces with keyword
    for iface in config["interfaces"].values():
        if (iface["description"] is not None 
                and keyword.lower() in iface["description"].lower()):
            address = iface["address"]
            if (verbose):
                print("{},{},{},{}".format(hostname,iface["name"], iface["description"], address))
            if (address is not None):
                addresses.append(ipaddress.ip_interface(iface["address"]))

    return addresses

def aggregate_addresses(all_addresses):
    all_prefixes = []
    for address in sorted(all_addresses):
        if address.network not in all_prefixes:
            all_prefixes.append(address.network)
    #return all_prefixes

    aggregated_prefixes = aggregate_prefixes(all_prefixes) 
    while len(all_prefixes) > len(aggregated_prefixes):
        all_prefixes = aggregated_prefixes
        aggregated_prefixes = aggregate_prefixes(all_prefixes) 
    return aggregated_prefixes

def aggregate_prefixes(all_prefixes):
    aggregated_prefixes = []
    i = 0
    while (i < len(all_prefixes)-1):
        curr_prefix = all_prefixes[i]
        next_prefix = all_prefixes[i+1]
        if (next_prefix.subnet_of(curr_prefix)):
            aggregated_prefixes.append(curr_prefix)
            i += 2
        elif (curr_prefix.supernet() == next_prefix.supernet()):
            aggregated_prefixes.append(curr_prefix.supernet())
            i += 2
        else:
            aggregated_prefixes.append(curr_prefix)
            i += 1
    if (i == len(all_prefixes)-1):
        aggregated_prefixes.append(next_prefix)
    return aggregated_prefixes


if __name__ == "__main__":
    main()