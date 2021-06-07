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

def check_path(path,outfile):
    print("going into check_path")
    print("INPUT: "+path+" OUTPUT: "+outfile)
    if os.path.isfile(path):
        print("Input is a file")
        intraconfig_refs(path, outfile)
    else:
        if os.path.isdir(outfile):
            files = glob.glob(path + '/**/*.json', recursive=True)
            for file in files:
                print("CUrrent working FILE:   "+file)
                intraconfig_refs(file,outfile+"output_"+os.path.basename(file))
        else:
            print("Input Path is a Directory; output Path is not directory ")


#writes confidence/support for association rules as well as IToACL dictionary  
#contents to argument file
def write_to_outfile(IToACL, interfaceIP, ACLtoI, total_num_interfaces, out_acl_ref, filename, two_way_references, total_ACL_IP_refs):
    with open(filename, 'w') as outfile:
        outfile.write("C(Interface -> Have ACL references)\n")
        outfile.write("\tInterfaces with ACL reference(s): " + str(len(IToACL)) + "\n")
        outfile.write("\tSupport (num interfaces): " + str(total_num_interfaces) + "\n")
        if total_num_interfaces != 0:
            outfile.write("\tConfidence: " + str(len(IToACL)/total_num_interfaces) + "\n\n")
        
        outfile.write("C('in' access list -> 'out' access list)\n")
        outfile.write("\tInterfaces with 'out' access lists: " + str(out_acl_ref) + "\n")
        outfile.write("\tSupport (num interfaces with 'in' access list): " + str(len(IToACL)) + "\n")
        if len(IToACL) != 0:
            outfile.write("\tConfidence: " + str(out_acl_ref/len(IToACL)) + "\n\n")

        outfile.write("C(ACL covers interfaces IP -> interface has that ACL applied\n")
        outfile.write("\tTwo way ACL-Interface references: " + str(two_way_references) + "\n")
        outfile.write("\tSupport (num IP addresses covered in ACL): " + str(total_ACL_IP_refs) + "\n")
        if total_ACL_IP_refs != 0:
            outfile.write("\tConfidence: " + str(two_way_references/total_ACL_IP_refs) + "\n\n")

        outfile.write("IToACL\n")
        json.dump(IToACL, outfile, indent=4, sort_keys=True)  
        outfile.write("\n------------------------------------------------\n")

        outfile.write("interfaceIP\n")
        json.dump(interfaceIP, outfile, indent=4, sort_keys=True)
        outfile.write("\n------------------------------------------------\n")

        outfile.write("ACLtoI\n")
        json.dump(ACLtoI, outfile, indent=4, sort_keys=True)  
        outfile.write("\n------------------------------------------------\n")

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
def ACL_Interface(ACLtoI, interfaceIP):
    count = 0
    total = 0
    for (ACL, ips) in ACLtoI.items():
        for ip_list in ips:
            for (interface_ip, ACL_list) in interfaceIP.items():
                #CHANGED IS IN RANGE FUNCTION
                #print("ip list: ", str(ip_list))
                if isinstance(ip_list, list): #range of ip addresses
                    address = ipaddress.IPv4Address(interface_ip)
                    network = make_network_obj(ip_list[0], ip_list[1])
                    if (address in network):
                        total += 1
                        if ACL in ACL_list:
                            count += 1
                elif (len(ip_list) == 1 and ip_list in interfaceIP): #single ip address
                    count += 1
    confidence = "NA"
    if (total > 0):
        confidence = str(count/total)
    #print("count: " + str(count) + "      total: " + str(total) + "      confidence: " + confidence)
    return count, total

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
        net = ipaddress.IPv4Network(line[criteria])
        if net.prefixlen > 0:
            ret_val.append([str(net.network_address), str(net.hostmask)])
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
<<<<<<< Updated upstream
    #print(ilist)
=======
    print("ilist in range: " + str(ilist))
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
    #print("interfaces in range: ", ilist)
=======
    print("interfaces in range: ", ilist)
    print()
>>>>>>> Stashed changes
    return ilist

#compute percentage of interfaces that are in range and have ACL applied
def compute_confidence(numerator, denominator):
    confidence = numerator / denominator
    return confidence
 
#4
# fourth association rule:    
#Specific ACL applied to an interface => interface's IP falls within a range
def fourth_association(ACLtoI, interfaceIP):
    total_result = []
    for acl in ACLtoI:
        print("ACL: " + acl)
        ilist = interfaces_with_ACL(acl, interfaceIP)
        if len(ilist) > 0:                
            irange = compute_range(ilist)
            print("Range" + str(irange))
            itotal = interfaces_in_range(interfaceIP, irange)
            if len(itotal) == 0:
                return 0
        
            result = []
            result.append(len(ilist))
            result.append(len(itotal))

            total_result.append(result)
            print(result)
            print()
        print()
    return total_result

#creates and returns a dictionary representing intra-config references between
#interfaces (keys) and ACLs (values) in argument config file
def intraconfig_refs(cfile, writetofile):
    IToACL = {} #dictionary in form of {interface name: [ACL references]}
    ACLtoI = {} #dictionary in form of {ACL name: [interface names]}
    interfaceIP = {} #dictionary in form of {interface IP: [ACL references]}

    # Load config
    with open(cfile, "r") as infile:
        config = json.load(infile)

    #iterating over each line in file
    total_num_interfaces = 0
    out_acl_ref = 0

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
        if iface["out_acl"] is not None:
            found_ref = True
            references.append(iface["out_acl"])
        # Extract IP address
        if iface["address"] is not None:
            found_ip = True
            IP_address = iface["address"].split("/")[0]
        #at least one reference
        if found_ref:
            IToACL[iName] = references
            #check for two references
            if len(references) > 1:
                out_acl_ref += 1 #FIXME: Should there also be in_acl_ref?
        #interface ip address and reference(s) exists 
        if found_ip and found_ref:
            interfaceIP[IP_address] = references

    # Iterate over ACLs
    for acl in config["acls"].values():
        ACLName = acl["name"]
        references = []
        for line in acl["lines"]:
            references.extend(getAclLineIps(line))
        if (len(references) > 0):
            ACLtoI[ACLName] = references

    two_way_references, total_ACL_IP_refs= ACL_Interface(ACLtoI, interfaceIP)

    print()
    print("BEGINNING OF FOURTH RULE")
    #print("FOURTH ASSOCIATION PRINT: ")
    fourth_association(ACLtoI, interfaceIP)

    write_to_outfile(IToACL, interfaceIP, ACLtoI, total_num_interfaces, out_acl_ref, writetofile, two_way_references, total_ACL_IP_refs)

    return IToACL

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