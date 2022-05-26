#!/usr/bin/env python3

import argparse
import ipaddress
import json
import os
import pandas as pd
import pybatfish
from pybatfish.client.commands import *
from pybatfish.datamodel import *
from pybatfish.datamodel.answer import *
from pybatfish.datamodel.flow import *
from pybatfish.question import *
from pybatfish.question import bfq
import re

def main():
     #parsing command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('snapshot_path', help='provide path to the network snapshot')
    parser.add_argument('-v', '--verbose', action='store_true', help="Display verbose output")
    arguments = parser.parse_args()

    # Reformat snapshot path, if necessary
    snapshot_path = arguments.snapshot_path
    if arguments.snapshot_path[-1] == '/':
        snapshot_path = snapshot_path[:len(snapshot_path)-1]

    # Parse configurations using Batfish
    bf_session.host = 'localhost'
    load_questions()
    bf_set_network(os.path.basename(os.path.dirname(snapshot_path)))
    bf_init_snapshot(snapshot_path, name=os.path.basename(snapshot_path), overwrite=True)
    check_parsing(arguments.verbose)

    json_path = os.path.join(snapshot_path, "configs_json")
    os.makedirs(json_path, exist_ok=True)

    # Create dictionary mapping nodes to files
    files = {}
    data = bfq.fileParseStatus().answer().frame()
    for _,row in data.iterrows():
        if (len(row["Nodes"]) == 1):
            files[row["Nodes"][0]] = row["File_Name"]
            print(row["Nodes"], row["File_Name"])

    # Get list of devices
    nodes = bfq.nodeProperties().answer().frame()
    print(nodes)
    for node in nodes["Node"]:
        if node not in files:
            continue
        with open(os.path.join(snapshot_path, files[node]), "r") as conf_file:
            raw_lines = conf_file.readlines()
        parts = extract_node(node, raw_lines)
        with open(os.path.join(json_path, node + ".json"), 'w') as json_file:
            json.dump(parts, json_file, indent=4, sort_keys=True)

"""Check for parsing errors"""
def check_parsing(verbose=False):
    # Determine which files did not completely parse
    parse_status = bfq.fileParseStatus().answer().frame()
    not_passed = parse_status[parse_status['Status'] != 'PASSED']
    if (len(not_passed) == 0):
        print("All files successfully parsed")
        return
    print("%d files failed to parse:" % (len(not_passed)))
    print(not_passed.loc[:, 'File_Name':'Status'])

    # Determine which init issues occurred
    init_issues = bfq.initIssues().answer().frame()
    print("%d init issues occurred:" % (len(init_issues)))
    if (verbose):
        config_format = bfq.nodeProperties(
                properties="Configuration_Format").answer().frame()
        print(config_format)

        for i,row in init_issues.iterrows():
            if row['Type'].startswith('Parse'):
                print('%s %s' % (row['Type'], row['Source_Lines']))
                print('\t' + (row['Line_Text'].replace('\n', '\n\t') if row['Line_Text'] is not None else 'None'))
                print('\t%s\n' % row['Parser_Context'])
                print('\t' + row['Details'])
            elif row['Type'].startswith('Convert warning'):
                print('%s %s' % (row['Type'], row['Nodes']))
                print('\t' + row['Details'])

#    errors = init_issues[init_issues['Type'] == 'Parse error']
#    if (verbose):
#        for i,row in errors.iterrows():
#            print('%s %s' % (row['Type'], row['Source_Lines']))
#            print('\t' + (row['Line_Text'].replace('\n', '\n\t') if row['Line_Text'] is not None else 'None'))
#            print('\t' + row['Parser_Context'] + '\n')

        # Obtain parse trees
        pybatfish.client._diagnostics._INIT_INFO_QUESTION['instance']['description'] = 'Initialize information for debugging'
        _, initInfo = pybatfish.question.question._load_question_dict(
                pybatfish.client._diagnostics._INIT_INFO_QUESTION,
                pybatfish.client.commands.bf_session)
        print(initInfo().answer())


    # Determine which lines failed to parse
    parse_warning = bfq.parseWarning().answer().frame()
    print("%d parsing errors occurred:" % (len(parse_warning)))
#    if (verbose):
#        for i,row in parse_warning.iterrows():
#            print('%s:%d %s' % (row['Filename'], row['Line'], row['Text']))
#            print(row['Comment'])
#            print(row['Parser_Context'] + "\n")
#    else:
    print(parse_warning.loc[:,'Filename':'Line'])

def extract_node(node, raw_lines):
    parts = {
        "name" : node,
        "interfaces" : extract_interfaces(node),
        "acls" : extract_acls(node),
        "vlans" : extract_vlans(raw_lines),
        "ospf" : extract_ospf(node, raw_lines)
    }
    extract_acl_remarks(parts, raw_lines)
    resolve_acls_aliases(parts["acls"])
    return parts

"""Extract details for all interfaces on a node"""
def extract_interfaces(node):
    interfaces = {}
    
    data = bfq.interfaceProperties(nodes=node, excludeShutInterfaces=False).answer().frame()

    for i,row in data.iterrows():
        interface = {
            "name" : row["Interface"].interface,
            "in_acl" : row["Incoming_Filter_Name"],
            "out_acl" : row["Outgoing_Filter_Name"],
            "description" : row["Description"],
            "address" : row["Primary_Address"],
            "switchport" : (None if row["Switchport_Mode"] == "NONE" else row["Switchport_Mode"].lower()),
            "access_vlan" : row["Access_VLAN"],
            "allowed_vlans" : convert_allowed_vlans(row["Allowed_VLANs"])
        }
        interfaces[interface["name"]] = interface

    return interfaces

"""Convert a string of allowed VLANs into a list"""
def convert_allowed_vlans(raw_string):
    # Handle empty string
    if len(raw_string) == 0:
        return None
       
    # Iterate over each item in the string of allowed VLANs
    full_list = []
    raw_list = raw_string.strip().split(",")
    for item in raw_list:
        # Range of VLANs
        if "-" in item:
            start, end = item.split("-")
            full_list.extend(list(range(int(start), int(end)+1)))
        # Single VLAN
        else:
            full_list.append(int(item))
    return full_list

"""Extract details for all ACLs on a node"""
def extract_acls(node):
    acls = {}

    data = bfq.namedStructures(nodes=node,structureTypes="IP_ACCESS_LIST").answer().frame()

    for i,row in data.iterrows():
        lines = None
        if "lines" in row["Structure_Definition"]:
            lines = extract_acl_lines(row["Structure_Definition"]["lines"], row["Structure_Name"])

        if isinstance(lines, str):
            acl = {
                "name" : row["Structure_Name"],
                "alias" : lines
            }
        else:
            acl = {
                "name" : row["Structure_Name"],
                "lines" : lines,
                "remarks" : []
            }
        acls[acl["name"]] = acl
    return acls

def resolve_acls_aliases(acls):
    """Copy lines and remarks from one ACL to another when an ACL is an alias of another ACL"""
    for acl in acls.values():
        if "alias" in acl:
            alias = acl["alias"]
            if alias in acls:
                acl["lines"] = acls[alias]["lines"]
                acl["remarks"] = acls[alias]["remarks"]

def extract_acl_lines(data, name):
    """Extract match criteria for all lines in an ACL"""
    lines = []

    for row in data:
        if "matchCondition" in row and "conjuncts" in row["matchCondition"]:
            match = None
            for conjunct in row["matchCondition"]["conjuncts"]:
                if "headerSpace" in conjunct:
                    match = conjunct["headerSpace"]
                    break
            if match is None:
                print(name, row)
                continue
        elif "matchCondition" in row and "headerSpace" in row["matchCondition"]:
            match = row["matchCondition"]["headerSpace"]
        elif "matchCondition" in row and row["matchCondition"]["class"] == "org.batfish.datamodel.acl.TrueExpr":
            match = {
                "srcIps" : {"ipWildcard" : "0.0.0.0/0"},
                "dstIps" : {"ipWildcard" : "0.0.0.0/0"}
            }
        elif row["class"] == "org.batfish.datamodel.AclAclLine" and "aclName" in row:
            return row["aclName"] # Alias
        else:
            print(name, row)
            continue

        srcIps = None
        if "srcIps" in match and "ipWildcard" in match["srcIps"]:
            srcIps = match["srcIps"]["ipWildcard"]
        dstIps = None
        if "dstIps" in match and "ipWildcard" in match["dstIps"]:
            dstIps = match["dstIps"]["ipWildcard"]

        line = {
            "action" : row["action"],
            "srcIps" : srcIps,
            "dstIps" : dstIps
        }
        lines.append(line)

    return lines

#returns boolean indicating if argument regex pattern exists in argument string
def is_regex_match(pattern, line):
    p = re.compile(pattern)
    iList = p.findall(line)
    return (len(iList) > 0)

#Extract all remarks from all ACLs on a node
def extract_acl_remarks(parts, raw_lines):
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i].strip()
        if is_regex_match('^access-list \d+ remark', line):
            name = line.split()[1]
            start_idx = line.find("remark") + 7
            parts["acls"][name]["remarks"].append(line[start_idx:])
            i += 1
            line = raw_lines[i].strip()
        #elif is_regex_match('^(ip|ipv6) access-list', line):
        elif is_regex_match('^ip access-list', line):
            name = line.split()[-1]
            i += 1
            line = raw_lines[i].strip()
            while (line != "!"):
                if line[:2] == "ip":
                    i -= 1
                    break
                if is_regex_match('^remark ', line):
                    if (len(line) < 11) or (line[10] != "-"): #check for meaningful remark
                        start_idx = 7
                        if line[7:10] == "---":
                            start_idx = 11
                        parts["acls"][name]["remarks"].append(line[start_idx:])
                i += 1
                if i >= len(raw_lines):
                    break
                line = raw_lines[i].strip()     
        i += 1


"""Extract all VLAN names from all VLANs on a node"""
def extract_vlans(raw_lines):
    vlans = {}
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        if (is_regex_match('^vlan \d+$', line)):
            temp = line.strip().split()
            num = int(temp[1])
            i += 1
            line = raw_lines[i]
            temp = line.strip().split()
            if temp[0] == "name":
                name = temp[1]
                vlans[num] = { "num" : num, "name" : name }
        i += 1

    return vlans

"""Extract OSPF information on a node"""
def extract_ospf(node, raw_lines):
    processes = {}
    
    data = bfq.ospfProcessConfiguration(nodes=node).answer().frame()

    for _,row in data.iterrows():
        process = {
            "name" : row["Process_ID"],
            "vrf" : row["VRF"],
            "areas" : {},
            "interfaces" : []
        }
        processes[process["name"]] = process
        
    extract_ospf_areas(node, processes)
    extract_ospf_raw(raw_lines, processes)

    return processes

"""Extract OSPF areas"""
def extract_ospf_areas(node, processes):
    data = bfq.ospfAreaConfiguration(nodes=node).answer().frame()

    for _,row in data.iterrows():
        area = {
            "name" : row["Area"],
            "type" : row["Area_Type"],
            "networks" : []
        }
        processes[row["Process_ID"]]["areas"][area["name"]] = area

"""Extract OSPF networks"""
def extract_ospf_raw(raw_lines, processes):
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i].strip()
        i += 1
        if is_regex_match('^router ospf ', line):
            process_name = line.split()[2]
            process = processes[process_name]
            line = raw_lines[i].strip()
            i += 1
            while (line != "!"):
                if is_regex_match('^network ', line):
                    parts = line.split()
                    # Adjust mask to match expectations of Python IPv4Network constructor
                    mask = parts[2]
                    if mask == "0.0.0.0":
                        mask = "255.255.255.255"
                    elif mask == "255.255.255.255":
                        mask = "0.0.0.0"
                    network = str(ipaddress.IPv4Network("%s/%s" % (parts[1], mask)))
                    area_name = parts[4]
                    if area_name not in processes[process_name]["areas"]:
                        print("Unknown area: %s" % (area_name))
                    else:
                        process["areas"][area_name]["networks"].append(network)
                elif is_regex_match("^no passive-interface ", line):
                    parts = line.split()
                    interface_name = parts[2]
                    process["interfaces"].append(interface_name)
                line = raw_lines[i].strip()
                i += 1

        
if __name__ == "__main__":
    main()