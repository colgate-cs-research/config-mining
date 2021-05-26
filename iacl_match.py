import re
import json

#returns boolean indicating 
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
def write_to_outfile(IToACL, total_num_interfaces, out_acl_ref, filename):
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
    return   

#
def intraconfig_refs(cfile):
    IToACL = {} #dictionary in form of {interface name: [ACL references]}
    infile = open(cfile, "r")
    infile.readline() #go past empty line
    line = True;
    #iterating over each line in file
    total_num_interfaces = 0;
    out_acl_ref = 0;

    while line:
        line = infile.readline()
        #look for interface names
        if is_regex_match('^interface [a-zA-Z0-9\-]+', line):
            total_num_interfaces += 1;
            iName = getName(line, 1)
            references = []
            line = infile.readline()
            found_ref = False
            while (line.strip() != "!"):
                #look for ACL names
                if (is_regex_match('ip access-group [a-zA-Z0-9\-]+ ', line)):
                    found_ref = True
                    ACLName = getName(line, 2)
                    references.append(ACLName)
                line = infile.readline()
            #at least one reference
            if found_ref:
                IToACL[iName] = references
                #check for two references
                if len(references) > 1:
                    out_acl_ref += 1;

    write_to_outfile(IToACL, total_num_interfaces, out_acl_ref, 'data.txt')

    return IToACL


intraconfig_refs("/shared/configs/northwestern/core1.conf")
