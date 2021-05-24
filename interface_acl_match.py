import re
import json

def regex_matcher(pattern, input):
    p = re.compile(pattern,re.IGNORECASE)
    if len(p.findall(input))!= 0:
        print(p.findall(input))
    return


def intraconfig_refs(cfile):
    infile = open(cfile, "r")
    infile.readline() #go past empty line
    line=True;
    #iterating over each line in file
    while line:
        line = infile.readline()
        regex_matcher('Interface',line)
    return


intraconfig_refs("/shared/configs/northwestern/core1.conf")




