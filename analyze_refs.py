import re
import json
import argparse
import analyze
import ipaddress

#returns boolean indicating if argument regex pattern exists in argument string
def is_regex_match(pattern, line):
    p = re.compile(pattern)
    iList = p.findall(line)
    return (len(iList) > 0)

"""Analyze a single configuration"""
def analyze_configuration(infile, outfile):
    print("Current working FILE: "+infile)
    # Extract relevant details
    IfaceName2AppliedAclNames, IfaceIp2AppliedAclNames, AclName2IpsInRules = intraconfig_refs(infile)

    rules = []

    # C(is interface => interface has ACL reference(s))
    num_ifaces, has_acl = assoc_iface_has_acl(IfaceName2AppliedAclNames)
    message = "C(interface => has ACL reference)"
    rules.append(analyze.create_rule(message, has_acl, num_ifaces))

    # C(interface has 'in' access list => interface has 'out' access list) 
    in_acl_ref, both_acl_ref = assoc_acl_directions("in", IfaceIp2AppliedAclNames)
    message = "C(interface has 'in' ACL applied => interface has 'out' ACL applied)"
    rules.append(analyze.create_rule(message, both_acl_ref, in_acl_ref))

    # C(interface has 'out' access list => interface has 'in' access list) 
    out_acl_ref, both_acl_ref = assoc_acl_directions("out", IfaceIp2AppliedAclNames)
    message = "C(interface has 'out' ACL applied => interface has 'in' ACL applied)"
    rules.append(analyze.create_rule(message, both_acl_ref, out_acl_ref))

    # C(ACL covers interface's IP => interface has that ACL applied) 
    two_way_references, total_ACL_IP_refs= ACL_Interface(AclName2IpsInRules, IfaceIp2AppliedAclNames)
    message = "C(ACL covers interface's IP => interface has that ACL applied)"
    rules.append(analyze.create_rule(message, two_way_references, total_ACL_IP_refs))

    for acl_name in AclName2IpsInRules:
        ifaces_with_acl, ifaces_in_range, irange = fourth_association(acl_name, IfaceIp2AppliedAclNames)
        message = "C(interface's IP falls within range %s => ACL %s applied to the interface)" % (irange, acl_name)
        rules.append(analyze.create_rule(message, ifaces_with_acl, ifaces_in_range))

    analyze.write_to_outfile(outfile, rules)

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
    if len(ilist) == 0:
        return None
    return [min(ilist), max(ilist)]

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

#4
# fourth association rule:    
#Specific ACL applied to an interface => interface's IP falls within a range
def fourth_association(ACL, IfaceIp2AppliedAclNames):
    ilist = interfaces_with_ACL(ACL, IfaceIp2AppliedAclNames)
    irange = compute_range(ilist)
    if irange is None:
        return 0, 0, None
    itotal = interfaces_in_range(IfaceIp2AppliedAclNames, irange)
    return len(ilist), len(itotal), irange

#creates and returns four dictionaries representing intra-config references between
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

    analyze.process_configs(analyze_configuration, config_path, outfile)

if __name__ == "__main__":
    main()