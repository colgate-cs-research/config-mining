import re
import json
import argparse
from ipaddress import IPv4Address
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
            files = glob.glob(path + '/**/*.conf', recursive=True)
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
        json.dump(IToACL, outfile, indent = 4)  
        outfile.write("\n------------------------------------------------\n")

        outfile.write("interfaceIP\n")
        json.dump(interfaceIP, outfile, indent = 4)
        outfile.write("\n------------------------------------------------\n")

        outfile.write("ACLtoI\n")
        json.dump(ACLtoI, outfile, indent = 4)  
        outfile.write("\n------------------------------------------------\n")

    return   

#Calculates and returns number of two-way interface-ACL references (numerator in confidence calc)
def ACL_Interface(ACLtoI, interfaceIP):
    count = 0
    total = 0
    for (ACL, ips) in ACLtoI.items():
        for ip_list in ips:
            for (interface_ip, ACL_list) in interfaceIP.items():
                if isinstance(ip_list, list) and is_in_range(interface_ip, ip_list, True):
                    total += 1
                    if ACL in ACL_list:
                        count += 1
                elif (len(ip_list) == 1 and ip_list[0] in interfaceIP):
                    count += 1
    print("count: " + str(count) + "      total: " + str(total) + "      confidence: " + str(count/total))
    return count, total

#Returns a boolean to see whether the IP address is in range or not              
def is_in_range(interface_ip, ip_list, is_wildcard_mask):
    start = ip_list[0].split(".")
    end = []
    currIP = interface_ip.split(".")
    if is_wildcard_mask:
        wildcard_mask = ip_list[1].split(".")
        for i in range(len(start)):
            num = int(start[i]) + int(wildcard_mask[i])
            end.append(num)
    else:
        end = ip_list[1].split(".")
    
    for i in range(len(currIP)):
        if (int(currIP[i]) < int(start[i]) or int(currIP[i]) > int(end[i])):
            return False

    return True

#returns the ip address(es) in the argument line either as a string (if one) or a list (more than one)
def getIP(line):
    linelist = line.split()
    ret_val = []
    for token in linelist:
        if is_regex_match("\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", token):
            ret_val.append(token)
    if len(ret_val) == 1: #if single ip address and not a range
        return ret_val[0]
    return ret_val #range

#1 function
#find all interfaces with ACL applied
#iterate through interfaces and create a range
#return LIST of interfaces
def interfaces_with_ACL(ACL, interfaceIP):
    ilist = []
    for interface in interfaceIP:
        for acl in interfaceIP[interface]:
            if acl == ACL:
                ilist.append(interface)
    return ilist

#2
#computes a RANGE for argument list
#returns a list with first element = min and last = max
def compute_range(ilist):
    ip_range = []
    print(ilist)
    ip_range.append(min(ilist))
    ip_range.append(max(ilist))
    return ip_range

#3
#takes access control list and range
#finds all interfaces within this range (confidence denominator)
def interfaces_in_range(interfaceIP, IPrange):
    ilist = []
    print("given/calculated range: ", IPrange)
    for interface in interfaceIP:
        if is_in_range(str(interface), IPrange, False):
            ilist.append(interface)
    print("interfaces in range: ", ilist)
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
def intraconfig_refs(cfile, writetofile):
    IToACL = {} #dictionary in form of {interface name: [ACL references]}
    ACLtoI = {} #dictionary in form of {ACL name: [interface names]}
    interfaceIP = {} #dictionary in form of {interface IP: [ACL references]}
    infile = open(cfile, "r")
    infile.readline() #go past empty line
    line = True
    #iterating over each line in file
    total_num_interfaces = 0
    out_acl_ref = 0
    #look at each line in cfile
    while line:
        line = infile.readline()
        #look for interface definitions
        if is_regex_match('^interface [a-zA-Z0-9\-]+', line):
            total_num_interfaces += 1
            iName = line.split()[1]
            references = []
            line = infile.readline()
            found_ref = False
            found_ip = False
            while (line.strip() != "!"):
                #look for ACL references
                if (is_regex_match('ip access-group [a-zA-Z0-9\-]+ ', line)):
                    found_ref = True
                    ACLName = line.split()[2]
                    references.append(ACLName)

                elif (is_regex_match('ip address [0-9]+', line)):
                    found_ip = True
                    IP_address =  line.split()[2]
                line = infile.readline()
            #at least one reference
            if found_ref:
                IToACL[iName] = references
                #check for two references
                if len(references) > 1:
                    out_acl_ref += 1
            #interface ip address and reference(s) exists 
            if found_ip and found_ref:
                interfaceIP[IP_address] = references
        #look for ACL defs
        if is_regex_match('ip access-list', line):
            ACLName = line.split()[3]
            line = infile.readline()
            references = []
            while (is_regex_match('^ .+', line)):
                tokens = line.strip()
                if (is_regex_match('^ permit ',line)): 
                    temp = getIP(line)
                    if (len(temp) > 0):
                        references.append(temp)
                if (len(references) > 0):
                    ACLtoI[ACLName] = references
                line = infile.readline()

    two_way_references, total_ACL_IP_refs= ACL_Interface(ACLtoI, interfaceIP)

    print("PRINT 4th RULE: ", fourth_association("5mIrBOWI9", interfaceIP))
    write_to_outfile(IToACL, interfaceIP, ACLtoI, total_num_interfaces, out_acl_ref, writetofile, two_way_references, total_ACL_IP_refs)

    return IToACL

def main():
    #parsing command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('Path',metavar='path',type=str, help='provide path of the configration file to compute')
    parser.add_argument('outfile',metavar='outfile',type=str,help='provide name of file to write to')

    arguments=parser.parse_args()

    config_path = arguments.Path
    outfile = arguments.outfile


    check_path(config_path,outfile)

if __name__ == "__main__":
    main()