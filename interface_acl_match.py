import re
import json

#returns boolean indicating 
def is_regex_match(pattern, line):
    p = re.compile(pattern)
    iList = p.findall(line)
    return (len(iList) > 0)
        

def getName(line, tokenNum):
    splitLine = line.split()
    iName = splitLine[tokenNum]
    return iName  

def intraconfig_refs(cfile):
    IToACL = {} #dictionary in form of {interface name: [ACL references]}
    infile = open(cfile, "r")
    infile.readline() #go past empty line
    line = True;
    #iterating over each line in file
    while line:
        line = infile.readline()
        if is_regex_match('^interface [a-zA-Z0-9\-]+', line):
            iName = getName(line, 1)
            #print(iName)
            references = []
            line = infile.readline()
            while (line.strip() != "!"):
                if (is_regex_match('ip access-group [a-zA-Z0-9\-]+ ', line)):
                    ACLName = getName(line, 2)
                    references.append(ACLName)
                line = infile.readline()
            #print(references)
            IToACL[iName] = references  
    print(IToACL)           
    return IToACL


intraconfig_refs("/shared/configs/northwestern/core1.conf")





