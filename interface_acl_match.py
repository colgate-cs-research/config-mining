import re
import json

#returns boolean indicating 
def regex_matcher(pattern, line):
    p = re.compile(pattern)
    iList = p.findall(line)
    return (len(iList) > 0)
        

def getName(tokenNum)):
    if len(iList) > 0:
        splitLine = line.split()
        iName = splitLine[tokenNum]
    return iName  

def intraconfig_refs(cfile):
    infile = open(cfile, "r")
    infile.readline() #go past empty line
    line = True;
    #iterating over each line in file
    while line:
        line = infile.readline()
        regex_matcher('interface [a-zA-Z0-9\-]+', line, 1)
        regex_matcher('ip access-group [a-zA-Z0-9\-]+ ', line, 2)
    return


intraconfig_refs("/shared/configs/northwestern/core1.conf")




def intraconfig_refs(cfile):
    IToACL = {} #dictionary
    infile = open(cfile, "r")
    infile.readline() #go past empty line
    line = True;
    #iterating over each line in file
    while line:
        line = infile.readline()
        if regex_matcher('interface [a-zA-Z0-9\-]+', line):
            getName(1)
            #add interface name to dictionary (JSON)
            while line != "!\n":
                line =  infile.readline()
                if (regex_matcher('ip access-group [a-zA-Z0-9\-]+ ', line)):
                    getName(2)
                    #add name to dictionary as key
                    #
    return
