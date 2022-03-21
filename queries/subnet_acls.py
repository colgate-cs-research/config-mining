#!/usr/bin/env python3

import argparse
import ipaddress
import json
import os

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Get applied ACLs for all interfaces whose address falls within a subnet')
    parser.add_argument('config_path',type=str, help='Path for a file (or directory) containing a JSON representation of configuration(s)')
    parser.add_argument('subnet',type=str, help='Subnet to search for')
    parser.add_argument('-v', '--verbose', action='store_true', help="Display verbose output")
    arguments = parser.parse_args()

    if (arguments.verbose):
        print("DeviceName,IfaceName,IfaceInAcl,IfaceOutAcl,IfaceAddress")

    subnet = ipaddress.ip_network(arguments.subnet)
    if os.path.isdir(arguments.config_path):
        all_acls = process_dir(arguments.config_path, subnet, arguments.verbose)
    else:
        all_acls = process_file(arguments.config_path, subnet, arguments.verbose)

    for acl in all_acls:
        print("{}".format(acl))

def process_dir(dirpath, subnet, verbose=False):
    all_acls = set()
    for filename in os.listdir(dirpath):
        device_acls = process_file(os.path.join(dirpath, filename), subnet, verbose)
        all_acls.update(device_acls)
    return all_acls

def process_file(filepath, subnet, verbose=False):
    with open(filepath) as json_file:
        config = json.load(json_file)

    hostname = config["name"]
    acls = set()

    # Find interfaces within subnet
    for iface in config["interfaces"].values():
        address = iface["address"]
        if (address is not None):
            iface_subnet = ipaddress.ip_interface(address).network
            if (iface_subnet.subnet_of(subnet)):
                in_acl = iface["in_acl"]
                out_acl = iface["out_acl"]
                if (verbose):
                    print("{},{},{},{}".format(hostname, iface["name"], in_acl, out_acl, address))
                if (in_acl is not None and in_acl not in acls):
                    acls.add(in_acl)
                if (out_acl is not None and out_acl not in acls):
                    acls.add(out_acl)

    return acls

if __name__ == "__main__":
    main()