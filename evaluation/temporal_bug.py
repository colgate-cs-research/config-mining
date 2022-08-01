#

import argparse

def get_rules(f, cycles_dict, date):

    lst = f.read().split('\n')
    cycle_list = []

    i = 0
    while i < len(lst):
        line = lst[i]
        if ('.csv' not in line) and (line!=""):
            if '[' in line:
                while ']' not in line:
                    i += 1
                    line = lst[i]
            else:
                components = get_bug_site_list(lst[i+1][2:-2])
                cycle = (line, components)
                cycle_list.append(cycle)
                i += 1
        
        i += 1

    cycles_dict[date] = cycle_list

def get_bug_site_list(bug_site_str):
    bug_site_list = []
    for component in bug_site_str.split(','):
        bug_site_list.append(component.strip("' "))
    return bug_site_list

def fixed_after_one_period(matrix):
    if (matrix[0]==1):
        if (matrix[1]== 0) and (matrix[3]==0) and (matrix[3]==0):
            return True
    else:
        if ((matrix[1]==1) and (matrix[2]==0) and (matrix[3]==0)):
            return True
        else:
            if ((matrix[2]==1) and (matrix[3]==0)):
                return True
    return False

def fixed_after_two_periods(matrix):
    if (matrix[0]==1):
        if ((matrix[1]==1) and (matrix[2]==0) and (matrix[3]==0)):
            return True
    else:
        if ((matrix[1]==1) and (matrix[2]==1) and (matrix[3]==0)):
            return True
    return False

def fixed_after_three_periods(matrix):
    return ((matrix[0]==1) and (matrix[1]==1) and (matrix[2]==1) and (matrix[3]==0))

def not_fixed(matrix):
    sum  = 0
    for num in matrix:
        sum += num
    return sum==4

def main():

    #parser = argparse.ArgumentParser(description='Generate a graph')
    #parser.add_argument('bugs_path',type=str, help='Path for a file (or directory) containing a text files of bugs.')
    #arguments = parser.parse_args()

    cycles_dict = {} #key is filename, value is list of rules from file
    time_periods = ['2021-09-01', '2021-12-01', '2022-02-01','2022-05-01']
    for date in time_periods:
        f = open(('/shared/configs/colgate/mining/bug_reports/bug_report_' + date + '.txt'), 'r')
        #f = open(arguments.bugs_path, 'r')
        get_rules(f, cycles_dict,date)
        f.close()

    #print(rules_dict)

    # get each unique cycle found
    # make matrix where each index i is 1 if the cycle was there in period i+1 (or index i in time_periods)
    cycle_matrix_dict = {}
    for i in range(len(time_periods)):
        date = time_periods[i]
        for (cycle, components) in cycles_dict[date]:
            if cycle not in cycle_matrix_dict:
                cycle_matrix_dict[cycle] = [0,0,0,0]
            cycle_matrix_dict[cycle][i] = 1

    # count cycles in each category
    one = 0
    two = 0
    three = 0
    never = 0
    other = 0
    for cycle in cycle_matrix_dict:
        matrix = cycle_matrix_dict[cycle]
        # 1. fixed after one period
        if fixed_after_one_period(matrix):
            one += 1
        # 2. fixed after two periods
        elif fixed_after_two_periods(matrix):
            two += 1
        # 3. fixed after three periods
        elif fixed_after_three_periods(matrix):
            three += 1

        # 4. not fixed
        elif not_fixed(matrix):
            never += 1

        # 5. other 
        else:
            other += 1

    # make csv
    f = open('cycles_fixed.csv','w')
    f.write("One, Two, Three, Not Fixed, Other\n")
    line = "{}, {}, {}, {}, {}\n".format(one, two, three, never, other)
    f.write(line)
    f.close()


    '''rules_dict2 = {}
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
    files = ['fixed_after_1.txt', 'fixed_after_2.txt', 'fixed_after_3.txt', 'all.txt', 'others.txt', 'just4.tx']
    to_write = ['','','','','','']

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
        elif (4 in times) and (len(times)==1):
            to_write[5] += rule + "\n"
        else:
            to_write[4] += rule + "\n" + str(times) + "\n\n"

    for i in range(len(files)):
        f = open(files[i], 'w')
        f.write(to_write[i])
        f.close()


    #for file in arguments.bugs_path:
        #get_rules(file, rules_dict)'''

if __name__=="__main__":
    main()