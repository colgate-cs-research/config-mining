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
    print("going into check_path")
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
    IfaceName2AppliedAclNames, IfaceIp2AppliedAclNames, AclName2IpsInRules, total_num_interfaces, out_acl_ref, in_acl_ref = intraconfig_refs(infile)
    
    two_way_references, total_ACL_IP_refs= ACL_Interface(AclName2IpsInRules, IfaceIp2AppliedAclNames)

    fourth_association(AclName2IpsInRules, IfaceIp2AppliedAclNames)

    write_to_outfile(IfaceName2AppliedAclNames, IfaceIp2AppliedAclNames, AclName2IpsInRules, total_num_interfaces, out_acl_ref, in_acl_ref, outfile, two_way_references, total_ACL_IP_refs)


#computes confidence (same as the old write to outfile)
#retuns 3 dicts a,b,c
def data_computation(IToACL, total_num_interfaces, out_acl_ref, in_acl_ref, two_way_references, total_ACL_IP_refs):

    a={}
    a["message"]="C(Interface -> Have ACL references)"
    a["n"]="Interfaces with ACL reference(s): " + str(len(IToACL))    # n ~ Numerator
    a["d"]="Support (num interfaces): " + str(total_num_interfaces)   # d ~ Denominator 
    if total_num_interfaces != 0:
        a["c"]="Confidence: " + str(len(IToACL)/total_num_interfaces) # c ~ Confidence
    b={}
    b["message"]="C('in' access list -> 'out' access list)"
    both_acl_ref = 0
    for iface, acls in IToACL.items():
        if len(acls) == 2:
            both_acl_ref += 1
        else:
            print(iface)
    b["n"]="Interfaces with 'in' & 'out' access lists: " + str(both_acl_ref) 
    b["d"]="Support (num interfaces with 'in' access list): " + str(in_acl_ref) 
    if in_acl_ref != 0:
        b["c"]="Confidence: " + str(both_acl_ref/in_acl_ref)
    b2={}
    b2["message"]="C('out' access list -> 'in' access list)"
    b2["n"]="Interfaces with 'in' & 'out' access lists: " + str(both_acl_ref) 
    b2["d"]="Support (num interfaces with 'out' access list): " + str(out_acl_ref) 
    if out_acl_ref != 0:
        b2["c"]="Confidence: " + str(both_acl_ref/out_acl_ref)
    c={}
    c["message"]= "C(ACL covers interfaces IP -> interface has that ACL applied"
    c["n"]="Two way ACL-Interface references: " + str(two_way_references)
    c["d"]="Support (num IP addresses covered in ACL): " + str(total_ACL_IP_refs)
    if total_ACL_IP_refs != 0:
        c["c"]="Confidence: " + str(two_way_references/total_ACL_IP_refs)

    return a,b,b2,c


#writes confidence/support for association rules as well as IToACL dictionary  
#contents to argument file
def write_to_outfile(IToACL, interfaceIP, ACLtoI, total_num_interfaces, out_acl_ref, in_acl_ref, filename, two_way_references, total_ACL_IP_refs):
    with open(filename, 'w') as outfile:
        a,b,b2,c=data_computation(IToACL, total_num_interfaces, out_acl_ref, in_acl_ref, two_way_references, total_ACL_IP_refs)
        to_dump= [a,b,b2,c,IToACL, interfaceIP, ACLtoI, total_num_interfaces, out_acl_ref]                          # single json dump in list
        json.dump(to_dump, outfile, indent=4, sort_keys=True)
    return   

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
def ACL_Interface(ACLNametoIpsInRules, InterfaceIptoAppliedAclNames):
    two_way = 0
    one_way = 0
    for (ACL, ips) in ACLNametoIpsInRules.items():
        for (interface_ip, ACL_list) in InterfaceIptoAppliedAclNames.items():
            #single ip address
            #if (ip_list[1] == "0.0.0.0"): 
            #    if (ip_list[0] in InterfaceIptoAppliedAclNames): 
            #        one_way += 1
            #        if (ACL in InterfaceIptoAppliedAclNames[ip_list[0]]):
            #            two_way += 1
            # range of ip address
            #else:
            for ip_list in ips:
                address = ipaddress.IPv4Address(interface_ip)
                network = make_network_obj(ip_list[0], ip_list[1])
                if (address in network):
                    one_way += 1
                    if ACL in ACL_list:
                        two_way += 1
                    break
    return two_way, one_way

#Returns a boolean to see whether the IP address is in range or not
##argument interface_ip is a string representation of an ip address  
#argument ip_list is a list of strings representing a range in the form [min address, max address]           
def is_in_range(interface_ip, ip_list):
    start = ip_list[0].split(".")
    end = ip_list[1].split(".")
    currIP = interface_ip.split(".")
    
    for i in range(len(currIP)):
        if (int(currIP[i]) < int(start[i]) or int(currIP[i]) > int(end[i])):
            return False

    return True

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
def interfaces_with_ACL(ACL, interfaceIP):
    ilist = []
    #print(interfaceIP)
    for interface in interfaceIP:
        #print("interface acls: " + str(interfaceIP[interface]))
        #print("acl: " + ACL)
        #print()
        for acl in interfaceIP[interface]:
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
def interfaces_in_range(interfaceIP, IPrange):
    ilist = []
    #print("given/calculated range: ", IPrange)
    for interface in interfaceIP:
        if is_in_range(str(interface), IPrange):
            ilist.append(interface)
    #print("interfaces in range: ", ilist)
    return ilist

#compute percentage of interfaces that are in range and have ACL applied
def compute_confidence(numerator, denominator):
    confidence = numerator / denominator
    return confidence
 
#4
# fourth association rule:    
#Specific ACL applied to an interface => interface's IP falls within a range
def fourth_association(ACL, interfaceIP):
    ilist = interfaces_with_ACL(ACL, interfaceIP)
    if len(ilist) == 0:
        return 0
    irange = compute_range(ilist)
    itotal = interfaces_in_range(interfaceIP, irange)
    if len(itotal) == 0:
        return 0
    return len(ilist), len(itotal)

#creates and returns a dictionary representing intra-config references between
#interfaces (keys) and ACLs (values) in argument config file
def intraconfig_refs(cfile):
    IfaceName2AppliedAclNames = {} #dictionary in form of {interface name: [ACL references]}
    AclName2IpsInRules = {} #dictionary in form of {ACL name: [interface names]}
    IfaceIp2AppliedAclNames = {} #dictionary in form of {interface IP: [ACL references]}

    # Load config
    with open(cfile, "r") as infile:
        config = json.load(infile)

    #iterating over each line in file
    total_num_interfaces = 0
    out_acl_ref = 0
    in_acl_ref = 0

    # Iterate over interfaces
    for iface in config["interfaces"].values():
        total_num_interfaces += 1
        iName = iface["name"]
        references = []
        found_ref = False
        found_ip = False
        # Extract ACL references
        if iface["in_acl"] is not None:
            found_ref = True
            references.append(iface["in_acl"])
            in_acl_ref += 1
        if iface["out_acl"] is not None:
            found_ref = True
            references.append(iface["out_acl"])
            out_acl_ref += 1
        # Extract IP address
        if iface["address"] is not None:
            found_ip = True
            IP_address = iface["address"].split("/")[0]
        #at least one reference
        if found_ref:
            IfaceName2AppliedAclNames[iName] = references
        #interface ip address and reference(s) exists 
        if found_ip and found_ref:
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


    return IfaceName2AppliedAclNames, IfaceIp2AppliedAclNames, AclName2IpsInRules, total_num_interfaces, out_acl_ref, in_acl_ref 

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