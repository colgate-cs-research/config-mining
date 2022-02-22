#!/usr/bin/env python3

import argparse
import json
import os

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Cleanup anonymization')
    parser.add_argument('config_path',type=str, help='Path for a file (or directory) containing a JSON representation of configuration(s)')
    parser.add_argument('-v', '--verbose', action='store_true', help="Display verbose output")
    arguments = parser.parse_args()

    if os.path.isdir(arguments.config_path):
        process_dir(arguments.config_path)
    else:
        process_file(arguments.config_path)

def process_dir(dirpath):
    for filename in os.listdir(dirpath):
        process_file(os.path.join(dirpath, filename))

def process_file(filepath):
    print(filepath)
    with open(filepath) as json_file:
        config = json.load(json_file)
    
    # Remove anonymized keywords from ACL remarks
    for acl in config["acls"].values():
        orig_remarks = acl["remarks"]
        clean_remarks = [remark for remark in orig_remarks if remark != " REMOVED"]
        acl["remarks"] = clean_remarks

    # Remove anonymized descriptions from interfaces
    for iface in config["interfaces"].values():
        if iface["description"] == "REMOVED":
            iface["description"] = None
    
    with open(filepath, 'w') as json_file:
        json.dump(config, json_file, indent=4, sort_keys=True)



#    json_path = os.path.join(snapshot_path, "configs_json")
#    os.makedirs(json_path, exist_ok=True)

#        with open(os.path.join(json_path, node + ".json"), 'w') as json_file:
#            json.dump(parts, json_file, indent=4, sort_keys=True)

if __name__ == "__main__":
    main()