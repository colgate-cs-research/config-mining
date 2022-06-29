#!/usr/bin/env python3

import argparse
import os
import json

from pydantic import NoneBytes

def interfaces_cleanup(interfaces):
    for iface in interfaces.values():
        attrib_names = list(iface.keys())
        for attrib_name in attrib_names:
            if attrib_name.startswith("description "):
                iface["description"] = attrib_name[len("description "):].strip('"')
                del iface[attrib_name]
            elif attrib_name.startswith("unit ") or attrib_name.startswith("inactive: unit "):
                unit = iface[attrib_name]
                unit_cleanup(unit)
                unit_name = attrib_name.replace("unit ", "")
                if "unit" not in iface:
                    iface["unit"] = {}
                iface["unit"][unit_name] = unit
                del iface[attrib_name]
            elif attrib_name == "unit":
                unit_num = iface[attrib_name]
                iface[attrib_name] = {unit_num: {}}
    return interfaces

def unit_cleanup(unit):
    keys = list(unit.keys())
    for attrib_name in keys:
        if attrib_name.startswith("description "):
            unit["description"] = attrib_name[len("description "):].strip('"')
            del unit[attrib_name]
        elif attrib_name == "family" and isinstance(unit[attrib_name], str):
            new_name = attrib_name + " " + unit[attrib_name]
            family_name = unit[attrib_name]
            unit["family"] = {family_name : {}}
            unit[new_name] = {}
            del unit[attrib_name]
        elif attrib_name.startswith("family "):
            if isinstance(unit[attrib_name], dict):
                unit[attrib_name] = family_cleanup(unit[attrib_name])
            #family_name = attrib_name.replace("family ", "") 
            #if "family" not in unit:
            #    unit["family"] = {}
            #elif isinstance(unit["family"], str):
            #    unit["family"] = {unit["family"] : {}} 
            #unit["family"][family_name] = unit[attrib_name]
            #del unit[attrib_name]
        elif attrib_name.startswith("vlan-tags "):
            parts = attrib_name.split(" ")
            unit["vlan-tags"] = {"inner": parts[2], "outer": parts[4]}
            del unit[attrib_name]

def family_cleanup(family):
    keys = list(family.keys())
    addresses = {}
    for attrib_name in keys:
        attrib_value = family[attrib_name]
        if attrib_name == "address":
            addresses[attrib_value] = {}
        elif attrib_name.startswith("address ") or attrib_name.startswith("inactive: address "):
            addr = attrib_name.replace("address ", "")
            addresses[addr] = attrib_value
            del family[attrib_name]
        elif attrib_name.startswith("rpf-check "):
            family["rpf-check"] = attrib_name[len("rpf-check "):]
            del family[attrib_name]
    if len(addresses) > 0:
        family["address"] = addresses
    return family
            

def protocols_cleanup(protocols):
    #if "mpls" in protocols:
    #    protocols["mpls"] = mpls_cleanup(protocols["mpls"])
    #if "bgp" in protocols:
    #    protocols["bgp"] = bgp_cleanup(protocols["bgp"])
    #if "isis" in protocols:
    #    protocols["isis"] = isis_cleanup(protocols["isis"])
    return protocols

def mpls_cleanup(mpls):
    new_mpls = {}
    lsps = {}
    paths = []
    for key, value in mpls.items():
        if key.startswith("label-switched-path "):
            key = key[len("label-switched-path "):]
            lsps[key] = label_switched_path_cleanup(value)
        elif key == "path":
            paths.append(value)
        elif key.startswith("path "):
            paths.append(key.split(" ")[1])
        else:
            new_mpls[key] = value
    new_mpls["label-switched-path"] = lsps
    new_mpls["path"] = paths
    return new_mpls

def label_switched_path_cleanup(lsp):
    for key, value in lsp.items():
        if key.startswith("secondary"):
            new_key, new_value = key.split(" ")
            lsp[new_key] = new_value
            del lsp[key]
            break
    return lsp

def bgp_cleanup(bgp):
    new_bgp = {}
    groups = {}
    for key, value in bgp.items():
        if key.startswith("group "):
            key = key[len("group "):]
            groups[key] = bgp_group_cleanup(value)
        else:
            new_bgp[key] = value
    new_bgp["group"] = groups
    return new_bgp

def bgp_group_cleanup(group):
    new_group = {}
    neighbors = {}
    for key, value in group.items():
        if key.startswith("neighbor "):
            key = key[len("neighbor "):]
            neighbors[key] = bgp_neighbor_cleanup(value)
        else:
            new_group[key] = value
    new_group["neighbor"] = neighbors
    return new_group

def bgp_neighbor_cleanup(neighbor):
    new_neighbor = {}
    for key, value in neighbor.items():
        if key.startswith("description "):
            value = key[len("description "):].strip('"')
            new_neighbor["description"] = value
        else:
            new_neighbor[key] = value
    return new_neighbor

def isis_cleanup(isis):
    new_isis = {}
    interfaces = {}
    for key, value in isis.items():
        if key.startswith("interface "):
            key = key[len("interface "):]
            interfaces[key] = value
        else:
            new_isis[key] = value
    new_isis["interface"] = interfaces
    return new_isis

def policy_options_cleanup(policy_options):
    # Determine types of policy options
    new_grouped_policy_options = {}
    new_flat_policy_options = {}
    for key, value in policy_options.items():
        # Identify type of policy option (e.g., prefix-list)
        parts = key.split(' ')
        typ = parts[0]

        # First time seeing a specific type of policy option
        if typ not in new_grouped_policy_options:
            new_grouped_policy_options[typ] = {}

        # If policy option has details
        if len(parts) > 1:
            name = parts[1]
            new_key = typ + " " + name
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
            new_grouped_policy_options[typ][name] = new_value
            new_flat_policy_options[new_key] = new_value
        # Policy option is just a name
        else:
            if typ == "prefix-list":
                name = value
                new_key = typ + " " + name
                new_value = []
                new_grouped_policy_options[typ][name] = [] # changed this to a list
                new_flat_policy_options[new_key] = new_value
            else:
                print("!Policy-options of type", typ, "not cleaned up")

    return new_grouped_policy_options
    #return new_flat_policy_options

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
    then = None
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
            then = [key[5:]]
            if dict[key] != None:
                if isinstance(dict[key], str):
                    then = [key[5:] + dict[key]]
                else:
                    then = []
                    for subkey, subval in dict[key].items():
                        subval = (subkey + " " + subval if subval is not None else subkey)
                        then.append(subval)

    new_dict = {"term" : new_value}
    if then != None:
        new_dict["then"] = then
    return new_dict

def firewall_cleanup(firewall):
    if "family inet" in firewall:
        new_family_inet = {}
        for key, value in firewall["family inet"].items():
            if key.startswith("filter "):
                key = key[len("filter "):]
                value = firewall_filter_cleanup(value)
                new_family_inet[key] = value
            else:
                print("!Unexpected key in firewall family inet:", key)
    firewall["family inet"] = {"filter": new_family_inet}
    return firewall

def firewall_filter_cleanup(filter):
    new_filter = {}
    for key, value in filter.items():
        if key.startswith("term "):
            key = key[len("term "):]
            value = firewall_term_cleanup(value)
            if "term" not in new_filter:
                new_filter["term"] = {}
            new_filter["term"][key] = value
        else:
            new_filter[key] = value
    return new_filter

def firewall_term_cleanup(term):
    if "then" in term:
        new_then = []
        if isinstance(term["then"], dict):
            for key, value in term["then"].items():
                if value is not None:
                    key += " " + value
                new_then.append(key)
        else:
            new_then = [term["then"]]
        term["then"] = new_then

    if "from" in term:
        for key, value in term["from"].items():
            if isinstance(value, dict):
                term["from"][key] = list(value.keys())
    return term

def cleanup_config(config_filepath, output_dir):
    with open(config_filepath, 'r') as cfg_file:
        config = json.load(cfg_file)

    config["interfaces"] = interfaces_cleanup(config["interfaces"])
    config["protocols"] = protocols_cleanup(config["protocols"])
    config["policy-options"] = policy_options_cleanup(config["policy-options"])
    config["firewall"] = firewall_cleanup(config["firewall"])

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
