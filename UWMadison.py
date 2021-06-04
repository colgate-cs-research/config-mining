import re
import json
import argparse
from ipaddress import IPv4Address


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

#returns a dictionary with {interface name: [list of words in description]} 
def get_descriptions(file, outf):
    infile = open(file, "r")
    line = infile.readline()
    desc_dict = {}
    vlan_names = []

    while line:
        if is_regex_match('^interface [a-zA-Z0-9\-]+', line):
            iName = getName(line, 1)
            while (line.strip() != "!"):
                if (is_regex_match('description', line)):
                    temp = line.split()
                    desc_dict[iName] = temp[1:]
                line = infile.readline()
                
        elif (is_regex_match('^vlan', line)):
            temp = line.split()
            if (len(temp) == 2):
                line = infile.readline()
                name = line.split()
                if name[0] == "name":
                    vlan_names.append(name[1])
        line = infile.readline()    

    with open(outf, 'w') as outfile:
        outfile.write("desc_dict\n")
        json.dump(desc_dict, outfile, indent = 4)

        outfile.write("\n\n-----------------------------------\n")

        outfile.write("vlan_names\n")
        outfile.write(str(vlan_names))

    return desc_dict, vlan_names

get_descriptions("/shared/configs/uwmadison/2014-10-core/configs/r-432nm-b3a-2-core.cfg", "UWM testing")