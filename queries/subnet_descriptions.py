#!/usr/bin/env python3

import argparse
import ipaddress
import json
import os

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Get descriptions for all interfaces whose address falls within a subnet')
    parser.add_argument('config_path',type=str, help='Path for a file (or directory) containing a JSON representation of configuration(s)')
    parser.add_argument('subnet',type=str, help='Subnet to search for')
    parser.add_argument('-v', '--verbose', action='store_true', help="Display verbose output")
    arguments = parser.parse_args()

    if (arguments.verbose):
        print("DeviceName,IfaceName,IfaceDescription,IfaceAddress")

    subnet = ipaddress.ip_network(arguments.subnet)
    if os.path.isdir(arguments.config_path):
        all_ifaces = process_dir(arguments.config_path, subnet, arguments.verbose)
    else:
        all_ifaces = process_file(arguments.config_path, subnet, arguments.verbose)

    for subnet, description in all_ifaces:
        print("{} {}".format(subnet, description))

def process_dir(dirpath, subnet, verbose=False):
    all_ifaces = []
    for filename in os.listdir(dirpath):
        device_ifaces = process_file(os.path.join(dirpath, filename), subnet, verbose)
        all_ifaces.extend(device_ifaces)
    return all_ifaces

def process_file(filepath, subnet, verbose=False):
    with open(filepath) as json_file:
        config = json.load(json_file)

    hostname = config["name"]
    ifaces = []

    # Find interfaces within subnet
    for iface in config["interfaces"].values():
        address = iface["address"]
        if (address is not None):
            iface_subnet = ipaddress.ip_interface(address).network
            if (iface_subnet.subnet_of(subnet)):
                description = iface["description"]
                if (verbose):
                    print("{},{},{},{}".format(hostname, iface["name"], description, address))
                if (description is not None):
                    ifaces.append((address, description))

    return ifaces

if __name__ == "__main__":
    main()