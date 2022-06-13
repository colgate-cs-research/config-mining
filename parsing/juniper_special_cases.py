#!/usr/bin/env python3

import argparse
import os
import json

def interfaces_cleanup(interfaces):
    for iface in interfaces.values():
        attrib_names = list(iface.keys())
        for attrib_name in attrib_names:
            if attrib_name.startswith("description "):
                iface["description"] = attrib_name[len("description "):].strip('"')
                del iface[attrib_name]
            elif attrib_name.startswith("unit "):
                unit = iface[attrib_name]
                unit_cleanup(unit)
                unit_name = attrib_name[len("unit "):]
                if "unit" not in iface:
                    iface["unit"] = {}
                iface["unit"][unit_name] = unit
                del iface[attrib_name]
    return interfaces

def unit_cleanup(unit):
    for attrib_name in unit.keys():
        if attrib_name.startswith("description "):
            unit["description"] = attrib_name[len("description "):].strip('"')
            del unit[attrib_name]
            break

def policy_options_cleanup(policy_options):
    # Determine types of policy options
    new_policy_options = {}
    for key, value in policy_options.items():
        # Identify type of policy option (e.g., prefix-list)
        parts = key.split(' ')
        typ = parts[0]

        # First time seeing a specific type of policy option
        if typ not in new_policy_options:
            new_policy_options[typ] = {}

        # If policy option has details
        if len(parts) > 1:
            name = parts[1]
            # Clean-up value
            if typ == "as-path":
                new_value = as_path_cleanup(key)
            elif typ == "community":
                new_value = community_cleanup(parts[2:])
            elif typ == "prefix-list":
                new_value = prefix_list_cleanup(value)
            elif typ == "policy-statement":
                new_value = policy_statement_cleanup(value)
            else:
                print("!Policy-options of type", typ, "not cleaned up")
                new_value = value
            new_policy_options[typ][name] = new_value
            
        # Policy option is just a name
        else:
            name = policy_options[key]
            new_policy_options[typ][name] = [] # changed this to a list

    return new_policy_options

def as_path_cleanup(key):
    parts = key.split(' ')
    return " ".join(parts[2:]).strip('"')
    #return key[len("as-path "):]

def community_cleanup(details):
    key = details[0]
    value = " ".join(details[1:]).strip('"')
    return { key : value}

def prefix_list_cleanup(value):
    lst = []
    if value is not None:
        for key in value:
            lst.append(key.replace('"', "'"))
    #lst = value.keys()
    return lst

# hard codes for juniper specific syntax
def policy_statement_cleanup(dict):
    new_value = {}
    for key in dict:
        #print("Key1: " + key)
        # 1. "term"
        if "term " in key:
            new_key = key[5:]
            new_value[new_key] = {}
            for key2 in dict[key]:
                #print("Key2: " + key2)
                val2 = dict[key][key2]
                # 2. "from"
                # 3. "to"
                # 4. "then" nested inside a term
                lst2= []
                if type(val2) == str or val2 == None:
                    keyword = ""
                    for word in ["to","from", "then"]:
                        if word in key2:
                            keyword = word
                    #print("Keyword: " + keyword)
                    el = key2[len(keyword)+1:]
                    if val2 != None:
                        el += " " + val2
                    lst2.append(el)
                    #print("El: " + el)
                    new_value[new_key][keyword] = lst2
                    
                elif dict[key][key2] != None:
                    if isinstance(dict[key][key2], list):
                        lst2 = dict[key][key2]
                    else:
                        lst2 = []
                        for key3 in dict[key][key2]:
                            #print("Key3: " + key3)
                            el = key3
                            #print(key, key2, key3)
                            val3 = dict[key][key2][key3]
                            #print(key, val3)
                            if val3 != None:
                                el += " " + str(val3)
                            lst2.append(el)
                    new_value[new_key][key2] = lst2
        # 5. term "then"
        if "then" in key:
            new_value["then"] = [key[5:]]
            if dict[key] != None:
                if isinstance(dict[key], str):
                    new_value["then"] = [key[5:] + dict[key]]
                else:
                    new_value["then"] = []
                    for subkey, subval in dict[key].items():
                        subval = (subkey + " " + subval if subval is not None else subkey)
                        new_value["then"].append(subval)

    return new_value


def cleanup_config(config_filepath, output_dir):
    with open(config_filepath, 'r') as cfg_file:
        config = json.load(cfg_file)

    config["policy-options"] = policy_options_cleanup(config["policy-options"])
    config["interfaces"] = interfaces_cleanup(config["interfaces"])

    with open(os.path.join(output_dir, os.path.basename(config_filepath)), 'w') as out_file:
        json.dump(config, out_file, indent=4, sort_keys=False)

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('config_path',type=str, help='Path to a (directory of) JSON-ified Juniper configuration file(s)')
    parser.add_argument('output_dir',type=str, help='Directory in which to store the cleaned configuration(s)')
    arguments = parser.parse_args()

    # Create output directory
    os.makedirs(arguments.output_dir, exist_ok=True)

    # Determine whether to process a single configuration or a directory of configurations
    if os.path.isfile(arguments.config_path):
        cleanup_config(arguments.config_path, arguments.output_dir)
    else:
        for filename in os.listdir(arguments.config_path):
            cleanup_config(os.path.join(arguments.config_path, filename), arguments.output_dir)




if __name__ == "__main__":
    main()
