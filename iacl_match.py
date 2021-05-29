import re
import json
import argparse

#returns boolean indicating if argument regex pattern exists in argument string
def is_regex_match(pattern, line):
    p = re.compile(pattern)
    iList = p.findall(line)
    return (len(iList) > 0)
        
#returns tokenNum token from argument line. Return value is a string
#representing an interface or ACL name
def getName(line, tokenNum):
    splitLine = line.split()
    iName = splitLine[tokenNum]
    return iName  

#writes confidence/support for association rules as well as IToACL dictionary  
#contents to argument file
def write_to_outfile(IToACL, interfaceIP, ACLtoI, total_num_interfaces, out_acl_ref, filename):
    with open(filename, 'w') as outfile:
        outfile.write("C(Interface -> Have ACL references)\n")
        outfile.write("\tInterfaces with ACL reference(s): " + str(len(IToACL)) + "\n")
        outfile.write("\tSupport (num interfaces): " + str(total_num_interfaces) + "\n")
        outfile.write("\tConfidence: " + str(len(IToACL)/total_num_interfaces) + "\n\n")
        
        outfile.write("C('in' access list -> 'out' access list)\n")
        outfile.write("\tInterfaces with 'out' access lists: " + str(out_acl_ref) + "\n")
        outfile.write("\tSupport (num interfaces with 'in' access list): " + str(len(IToACL)) + "\n")
        outfile.write("\tConfidence: " + str(out_acl_ref/len(IToACL)) + "\n\n")

        json.dump(IToACL, outfile, indent = 4)  

        json.dump(interfaceIP, outfile, indent = 4)

        json.dump(ACLtoI, outfile, indent = 4)  

    return   

#Calculates and returns number of two-way interface-ACL references (numerator in confidence calc)
def ACL_Interface(ACLtoI, interfaceIP):
    count = 0
    total = 0
    #interfaceIP = {"149.224.15.65": ["naArSbuXSGZ","ZL5LSHxVaqsG"], "164.77.128.65": ["WG8frRhR","Ejbiau4T3"]}
    #ACLtoI= {"naArSbuXSGZ": [["149.224.15.64", "0.0.0.31"]],"ZL5LSHxVaqsG": [["164.77.33.0", "0.0.0.255"], ["149.224.129.0", "0.0.0.255"], ["149.224.20.0", "0.0.0.255"], ["164.77.21.0", "0.0.0.255"]], "WG8frRhR": [ ["164.77.128.64", "0.0.0.63"] ], "Ejbiau4T3": [ ["164.77.21.0", "0.0.0.255"], ["149.224.20.0", "0.0.0.255"], ["149.224.44.0", "0.0.0.15"], ["149.224.44.32", "0.0.0.15"]]}
    for (ACL, ips) in ACLtoI.items():
        for ip_list in ips:
            for (interface_ip, ACL_list) in interfaceIP.items():
                if len(ip_list) > 1 and is_in_range(interface_ip, ip_list):
                    total += 1
                    if ACL in ACL_list:
                        count += 1
                elif (len(ip_list) == 1 and ip_list[0] in interfaceIP):
                    count += 1
    print("count: " + str(count) + "      total: " + str(total))
    return count    

#Returns a boolean to see whether the IP address is in range or not              
def is_in_range(interface_ip, ip_list):
    start = ip_list[0].split(".")
    wildcard_mask = ip_list[1].split(".")
    end = []
    currIP = interface_ip.split(".")
    for i in range(len(start)):
        num = int(start[i]) + int(wildcard_mask[i])
        end.append(num)
    for i in range(len(currIP)):
        if (int(currIP[i]) < int(start[i]) or int(currIP[i]) > int(end[i])):
            return False
    return True

#creates and returns a dictionary representing intra-config references between
#interfaces (keys) and ACLs (values) in argument config file
def intraconfig_refs(cfile, writetofile):
    IToACL = {} #dictionary in form of {interface name: [ACL references]}
    ACLtoI = {}
    interfaceIP = {}
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
            iName = getName(line, 1)
            references = []
            line = infile.readline()
            found_ref = False
            found_ip = False
            while (line.strip() != "!"):
                #look for ACL references
                if (is_regex_match('ip access-group [a-zA-Z0-9\-]+ ', line)):
                    found_ref = True
                    ACLName = getName(line, 2)
                    references.append(ACLName)

                elif (is_regex_match('ip address [0-9]+', line)):
                    found_ip = True
                    IP_address =  getName(line, 2)
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
            ACLName = getName(line, 3)
            line = infile.readline()
            references = []
            #print(line)
            while (is_regex_match('^ .+', line)):
                #print(line)
                tokens = line.strip()
                if (is_regex_match('^ permit',line)):
                    if (is_regex_match('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$',line)): #standard 
                        references.append(getName(line, 1))
                    else:                  #extended
                        range = [getName(line, 2)]
                        #print(range)
                        range.append(getName(line, 3))
                        references.append(range)
                ACLtoI[ACLName] = references
                line = infile.readline()
            
    write_to_outfile(IToACL, interfaceIP, ACLtoI, total_num_interfaces, out_acl_ref, writetofile)

    return IToACL

#parsing command-line arguments
parser = argparse.ArgumentParser(description='Commandline arguments')
parser.add_argument('Path',metavar='path',type=str, help='provide path of the configration file to compute')
parser.add_argument('outfile',metavar='outfile',type=str,help='provide name of file to write to')

arguments=parser.parse_args()

config_file = arguments.Path
outfile = arguments.outfile


intraconfig_refs(config_file, outfile)


