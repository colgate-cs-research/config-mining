#

import argparse

def get_rules(f, rules_dict):


    lst = f.read().split('\n')

    rules_list = []

    i = 0
    while i < len(lst):
        line = lst[i]
        if ('.csv' not in line) and (line!=""):
            if '[' in line:
                while ']' not in line:
                    i += 1
                    line = lst[i]
            else:
                rule = (line, lst[i+1])
                rules_list.append(rule)
                i += 1
        
        i += 1



    fname = f.name
    print(fname)
    rules_dict[fname] = rules_list




def main():

    parser = argparse.ArgumentParser(description='Generate a graph')
    parser.add_argument('bugs_path',type=str, help='Path for a file (or directory) containing a text files of bugs.')
    arguments = parser.parse_args()

    rules_dict = {} #key is filename, value is list of rules from file
    f = open(arguments.bugs_path, 'r')
    get_rules(f, rules_dict)

    print(rules_dict)

    #for file in arguments.bugs_path:
        #get_rules(file, rules_dict)

if __name__=="__main__":
    main()