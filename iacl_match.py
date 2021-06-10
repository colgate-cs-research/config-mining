import re
import json
import argparse
import ipaddress
import glob
import os

#returns boolean indicating if argument regex pattern exists in argument string
def is_regex_match(pattern, line):
    p = re.compile(pattern)
    iList = p.findall(line)
    return (len(iList) > 0)

"""Analyze a single configuration or a directory of configurations"""
def check_path(path,outfile):
    print("INPUT: "+path+" OUTPUT: "+outfile)
    if os.path.isfile(path):
        print("Input is a file")
        analyze_configuration(path, outfile)
    else:
        if os.path.isdir(outfile):
            files = glob.glob(path + '/**/*.json', recursive=True)
            for file in files:
                print("CUrrent working FILE:   "+file)
                analyze_configuration(file, os.path.join(outfile, os.path.basename(file)))
        else:
            print("Input Path is a Directory; output Path is not directory ")

"""Analyze a single configuration"""
def analyze_configuration(infile, outfile):
    # Extract relevant details
    IfaceName2AppliedAclNames, IfaceIp2AppliedAclNames, AclName2IpsInRules = intraconfig_refs(infile)

    rules = []

    # C(is interface => interface has ACL reference(s))
    num_ifaces, has_acl = assoc_iface_has_acl(IfaceName2AppliedAclNames)
    rule = {
        "message": "C(Interface -> Have ACL references)",
        "n" : "Interfaces with ACL reference(s): " + str(has_acl),    # n ~ Numerator
        "d" : "Support (num interfaces): " + str(num_ifaces),   # d ~ Denominator 
        "c": "Confidence: " + str(compute_confidence(has_acl, num_ifaces))
    }
    rules.append(rule)

    # C(interface has 'in' access list => interface has 'out' access list) 
    in_acl_ref, both_acl_ref = assoc_acl_directions("in", IfaceIp2AppliedAclNames)
    rule = {
        "message" : "C('in' access list -> 'out' access list)",
        "n" : "Interfaces with 'in' & 'out' access lists: " + str(both_acl_ref),
        "d" : "Support (num interfaces with 'in' access list): " + str(in_acl_ref),
        "c": "Confidence: " + str(compute_confidence(both_acl_ref, in_acl_ref))
    }
    rules.append(rule)

    # C(interface has 'out' access list => interface has 'in' access list) 
    out_acl_ref, both_acl_ref = assoc_acl_directions("out", IfaceIp2AppliedAclNames)
    rule = {
        "message" : "C('out' access list -> 'in' access list)",
        "n": "Interfaces with 'in' & 'out' access lists: " + str(both_acl_ref),
        "d": "Support (num interfaces with 'out' access list): " + str(out_acl_ref),
        "c": "Confidence: " + str(compute_confidence(both_acl_ref, out_acl_ref))
    }
    rules.append(rule)

    # C(ACL covers interface's IP => interface has that ACL applied) 
    two_way_references, total_ACL_IP_refs= ACL_Interface(AclName2IpsInRules, IfaceIp2AppliedAclNames)
    rule = {
        "message" : "C(ACL covers interfaces IP -> interface has that ACL applied",
        "n" : "Two way ACL-Interface references: " + str(two_way_references),
        "d" : "Support (num IP addresses covered in ACL): " + str(total_ACL_IP_refs),
        "c": "Confidence: " + str(compute_confidence(two_way_references, total_ACL_IP_refs))
    }
    rules.append(rule)

    for acl_name in AclName2IpsInRules:
        ifaces_with_acl, ifaces_in_range, irange = fourth_association(acl_name, IfaceIp2AppliedAclNames)
        rule = {
            "message" : "C(interface's IP falls within a range => ACL " + acl_name + " applied to the interface",
            "n" : "Num interfaces in range with ACL " + acl_name + " applied : " + str(ifaces_with_acl),
            "d" : "Support (num interfaces in range " + str(irange) + "): " + str(ifaces_in_range),
            "c": "Confidence: " + str(compute_confidence(ifaces_with_acl, ifaces_in_range))
        }
        rules.append(rule) 

    write_to_outfile(outfile, rules)

"""Writes confidence/support for association rules to JSON file"""
def write_to_outfile(filename, rules):
    with open(filename, 'w') as outfile:
        json.dump(rules, outfile, indent=4, sort_keys=True)
    return   

"""Calculate support for an interface having an ACL"""
def assoc_iface_has_acl(IfaceName2AppliedAclNames):
    has_acl = 0
    for acls in IfaceName2AppliedAclNames.values():
        if len(acls) >= 1:
            has_acl += 1
    num_ifaces = len(IfaceName2AppliedAclNames)
    return num_ifaces, has_acl

"""Calculate the support for an interface having an ACL applied in one direction (e.g., in) => the interface has an ACL applied in the opposite direction (e.g., out)"""
def assoc_acl_directions(direction, IfaceName2AppliedAclNames):
    both_acl_ref = 0
    one_acl_ref = 0
    for acls in IfaceName2AppliedAclNames.values():
        if direction in acls:
            one_acl_ref += 1
        if len(acls) == 2:
            both_acl_ref += 1

    return one_acl_ref, both_acl_ref

#constructs and returns network object
def make_network_obj(min_ip, wildcard_mask):
    wildcard_split = wildcard_mask.split(".") 
    netmask = []
    for i in wildcard_split:
        netmask.append(str(255-int(i)))
    netmask_str = ".".join(netmask) 
    network_str = min_ip + "/" + netmask_str
    #print(network_str)
    #print(ipaddress.IPv4Network(network_str))
    return ipaddress.IPv4Network(network_str)

#Calculates and returns number of two-way interface-ACL references (numerator in confidence calc)
def ACL_Interface(AclName2IpsInRules, IfaceIp2AppliedAclNames):
    two_way = 0
    one_way = 0
    for (ACL, ips) in AclName2IpsInRules.items():
        for (interface_ip, ACL_list) in IfaceIp2AppliedAclNames.items():
            for ip_list in ips:
                address = ipaddress.IPv4Address(interface_ip)
                network = make_network_obj(ip_list[0], ip_list[1])
                if (address in network):
                    one_way += 1
                    if ACL in ACL_list.values():
                        two_way += 1
                    break
    return two_way, one_way

#Returns a boolean to see whether the IP address is in range or not
##argument interface_ip is a string representation of an ip address  
#argument ip_list is a list of strings representing a range in the form [min address, max address]           
def is_in_range(interface_ip, ip_list):
    start = ipaddress.IPv4Address(ip_list[0])
    end = ipaddress.IPv4Address(ip_list[1])
    currIP = ipaddress.IPv4Address(interface_ip)
    return start <= currIP <= end

#returns a list of ip address(es)/network(s) in an ACL line
def getAclLineIps(line):
    ret_val = []
    for criteria in ["srcIps", "dstIps"]:
        try:
            net = ipaddress.IPv4Network(line[criteria])
            if net.prefixlen > 0:
                ret_val.append([str(net.network_address), str(net.hostmask)])
        except:
            print("ERROR parsing: "+line[criteria])
    return ret_val

#1 function
#find all interfaces with ACL applied
#iterate through interfaces and create a range
#return LIST of interfaces
def interfaces_with_ACL(ACL, IfaceIp2AppliedAclNames):
    ilist = []
    #print(interfaceIP)
    for interface in IfaceIp2AppliedAclNames:
        #print("interface acls: " + str(interfaceIP[interface]))
        #print("acl: " + ACL)
        #print()
        for acl in IfaceIp2AppliedAclNames[interface].values():
            if acl == ACL:
                ilist.append(interface)
    return ilist

#2
#computes a RANGE for argument list
#returns a list with first element = min and last = max
def compute_range(ilist):
    ip_range = []
    #print("ilist in range: " + str(ilist))
    ip_range.append(min(ilist))
    ip_range.append(max(ilist))
    return ip_range

#3
#takes access control list and range
#finds all interfaces within this range (confidence denominator)
def interfaces_in_range(IfaceIp2AppliedAclNames, IPrange):
    ilist = []
    #print("given/calculated range: ", IPrange)
    for interface in IfaceIp2AppliedAclNames:
        if is_in_range(str(interface), IPrange):
            ilist.append(interface)
    #print("interfaces in range: ", ilist)
    return ilist

#compute percentage of interfaces that are in range and have ACL applied
def compute_confidence(numerator, denominator):
    if (denominator > 0):
        return numerator / denominator
    return None
 
#4
# fourth association rule:    
#Specific ACL applied to an interface => interface's IP falls within a range
def fourth_association(ACL, IfaceIp2AppliedAclNames):
    ilist = interfaces_with_ACL(ACL, IfaceIp2AppliedAclNames)
    if len(ilist) == 0:
        return 0, 0, None
    irange = compute_range(ilist)
    itotal = interfaces_in_range(IfaceIp2AppliedAclNames, irange)
    return len(ilist), len(itotal), irange

#creates and returns a dictionary representing intra-config references between
#interfaces (keys) and ACLs (values) in argument config file
def intraconfig_refs(cfile):
    IfaceName2AppliedAclNames = {} #dictionary in form of {interface name: [ACL references]}
    AclName2IpsInRules = {} #dictionary in form of {ACL name: [interface names]}
    IfaceIp2AppliedAclNames = {} #dictionary in form of {interface IP: [ACL references]}

    # Load config
    with open(cfile, "r") as infile:
        config = json.load(infile)

    # Iterate over interfaces
    for iface in config["interfaces"].values():
        iName = iface["name"]
        references = {}
        found_ip = False
        # Extract ACL references
        if iface["in_acl"] is not None:
            references["in"] = iface["in_acl"]
        if iface["out_acl"] is not None:
            references["out"] = iface["out_acl"]
        # Extract IP address
        if iface["address"] is not None:
            found_ip = True
            IP_address = iface["address"].split("/")[0]
        IfaceName2AppliedAclNames[iName] = references
        #interface ip address and reference(s) exists 
        if found_ip:
            IfaceIp2AppliedAclNames[IP_address] = references

    # Iterate over ACLs
    for acl in config["acls"].values():
        ACLName = acl["name"]
        references = []
        if acl["lines"] is not None:
            for line in acl["lines"]:
                references.extend(getAclLineIps(line))
        if (len(references) > 0):
            AclName2IpsInRules[ACLName] = references

    return IfaceName2AppliedAclNames, IfaceIp2AppliedAclNames, AclName2IpsInRules 

def main():
    #parsing command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('Path',metavar='path',type=str, help='Path for a file (or directory) containing a JSON representation of configuration(s)')
    parser.add_argument('outfile',metavar='outfile',type=str,help='Name of file (or directory) to write to')

    arguments=parser.parse_args()

    config_path = arguments.Path
    outfile = arguments.outfile


    check_path(config_path,outfile)

if __name__ == "__main__":
    main()