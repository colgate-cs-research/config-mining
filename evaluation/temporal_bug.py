#

import argparse

def get_rules(f, rules_dict, date):


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
                crime_scene = get_bug_site_list(lst[i+1][2:-2])
                rule = (line, crime_scene)
                rules_list.append(rule)
                i += 1
        
        i += 1

    rules_dict[date] = rules_list

def get_bug_site_list(bug_site_str):
    bug_site_list = []
    for site in bug_site_str.split(','):
        bug_site_list.append(site.strip("' "))
    return bug_site_list

def main():

    #parser = argparse.ArgumentParser(description='Generate a graph')
    #parser.add_argument('bugs_path',type=str, help='Path for a file (or directory) containing a text files of bugs.')
    #arguments = parser.parse_args()

    rules_dict = {} #key is filename, value is list of rules from file
    time_periods = ['2021-09-01', '2021-12-01', '2022-02-01','2022-05-01']
    for date in time_periods:
        f = open(('bug_report_' + date + '.txt'), 'r')
        #f = open(arguments.bugs_path, 'r')
        get_rules(f, rules_dict,date)
        f.close()

    #print(rules_dict)

    rules_dict2 = {}
    for i in range(len(time_periods)):
        t1 = time_periods[i]
        rules_list_1 = rules_dict[t1]
        for rule in rules_list_1:
            if str(rule) not in rules_dict2:
                rules_dict2[str(rule)] = [i+1]
        for j in range(i+1,len(time_periods)):
            t2 = time_periods[j]
            rules_list_2 = rules_dict[t2]
            #delta_t = t1 + " - " + t2
            #delta_t = str(i+1) + " - " + str(j+1)
            for rule in rules_list_1:
                if rule in rules_list_2:
                    if j+1 not in rules_dict2[str(rule)]:
                        rules_dict2[str(rule)].append(j+1)

    #print(rules_dict2)

    #files = ['only1.txt', 'only2.txt', 'only3.txt', 'only4.txt', 'fixed_after_2.txt', 'fixed_after_3.txt', 'new_after_1', 'new_after_2', 'always_there.txt', 'one_three.txt', 'one_four.txt', 'two_four.txt', 'one_three_four.txt']
    #to_write = ['','','','','','','','','','','','','']
    files = ['fixed_after_1.txt', 'fixed_after_2.txt', 'fixed_after_3.txt', 'all.txt', 'others.txt']
    to_write = ['','','','','']

    '''for rule in rules_dict2:
        time_period_list = rules_dict2[rule]
        if 1 in time_period_list:
            if 2 in time_period_list:
                if 3 in time_period_list:
                    if 4 in time_period_list:
                        to_write[8] += rule + "\n"
                    else:
                        to_write[5] += rule + "\n"
                else:
                    to_write[4] += rule + "\n"
            else:
                if 3 in time_period_list:
                    if 4 in time_period_list:
                        to_write[12] += rule + "\n"
                    else:
                        to_write[9] += rule + "\n"
                elif 4 in time_period_list:
                    to_write[9] += rule + "\n"

        
        elif 2 in time_period_list:
            if 3 in time_period_list:
                if 4 in time_period_list:

        elif 3 in time_period_list:   
            if 4 in time_period_list:
                to_write[] += rule + "\n"
            else:
                to_write[2] += rule + "\n"

        elif 4 in time_period_list:
            to_write[3] += rule + "\n"'''

    for rule in rules_dict2:
        times = rules_dict2[rule]

        if (1 in times) and (2 in times) and (3 in times) and (4 in times):
            to_write[3] += rule + "\n"
        elif (1 in times) and (2 in times) and (3 in times):
            to_write[2] += rule + "\n"
        elif (1 in times) and (2 in times):
            to_write[1] += rule + "\n"
        elif (1 in times):
            to_write[0] += rule + "\n"
        else:
            to_write[4] += rule + "\n"

    for i in range(len(files)):
        f = open(files[i], 'w')
        f.write(to_write[i])
        f.close()


    #for file in arguments.bugs_path:
        #get_rules(file, rules_dict)

if __name__=="__main__":
    main()