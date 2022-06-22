stanza_type = ["ACL",
                "Interface",
                "PKI_TA_Profile",
                "Port",
                "SNMP_Trap",
                "System",
                "User",
                "User_Group",
                "VLAN",
                "VRF"]

'''def add_names():
    f = open("time_period_matrix.csv", 'r')
    line = f.readline()
    s = line[1:-1]
    f.close()

    f2 = open("time_period_matrix_cleaned.csv", 'w')
    header = "Time-periods, "
    for el in stanza_type:
        header += el + ", "
    header = header[:-2] + "\n"
    f2.write(header)
    i = 0
    t = 0
    while i < len(s):
        if s[i] == '[':
            t += 1
            s2 = "T" + str(t)
            s3 = ""
            i += 1
            while s[i] != ']':
                s3 += s[i]
                i += 1
            lst = s3.split(", ")
            for el in lst:
                s2 += ", " + el
            s2 += "\n"
            f2.write(s2)
        i += 1
    f2.close()'''


def add_stanza_names():
    f = open('144days.csv', 'r')
    s = f.read()
    s2 = ''
    i = 1
    while i < (len(s) -1):
        if s[i]=='[':
            i += 1
            while s[i] != ']':
                if (s[i] != '\n') and (s[i] != ' '):
                    s2 += s[i]
                i += 1
            s2 += '\n'
        i += 1
    s2 = s2[:-1]
    #print(s2)
    f.close()

    f = open("144days_cleaned.csv", 'w')
    header = "Time-periods, "
    for el in stanza_type:
        header += el + ", "
    header = header[:-2] + "\n"
    f.write(header)
    s2_lst = s2.split('\n')
    i = 1
    for el in s2_lst:
        line = 'T' + str(i) + "," + el + '\n'
        f.write(line)
        i += 1
    f.close()




def add_names_to_summary():
    f = open('144days_and_matrix.csv', 'r')
    f2 = open('144days_and_matrix_edited.csv','w')
    header = "Stanzas, "
    for el in stanza_type:
        header += el + ", "
    header = header[:-2] + "\n"
    f2.write(header)
    for i in range(len(stanza_type)):
        l = stanza_type[i] + ", " + f.readline()
        f2.write(l)
    f.close()
    f2.close()

def get_possibly_related_pairs():
    f = open('144days_and_matrix_edited.csv','r')
    f.readline()
    stanza_pairs1 = []
    stanza_pairs2 = []
    line_num = 1
    for line in f:
        lst = line.strip().split(',')
        #print(lst[1:])
        for i in range(1,len(lst)):
            if int(lst[i]) > 0:
                print(lst[i], end= ',')
                t1 = stanza_type[line_num-1].lower()
                t2 = stanza_type[i-1].lower()
                stanza_pairs1.append((t1,t2))
                print(str((t1, t2)), end = ',')
            else:
                t1 = stanza_type[line_num-1].lower()
                t2 = stanza_type[i-1].lower()
                stanza_pairs2.append((t1,t2))
        line_num += 1
        print()
    f.close()
    f = open('important_pairs.txt','w')
    f2= open('important_pairs_zero_reg.txt','w')
    stanza_pairs1 = get_rid_of_duplicates(stanza_pairs1)
    #stanza_pairs2 = get_rid_of_duplicates(stanza_pairs2)
    #print(stanza_pairs1)
    for i in range(len(stanza_pairs1)):
        s = 'reg ' + stanza_pairs1[i][0] + ' '+ stanza_pairs1[i][1] + '\n' + 'outreg2 using greater_than_zero.doc, append\n'
        f.write(str(stanza_pairs1[i]) + '\n')
        #f2.write(s)
    for i in range(len(stanza_pairs2)):
        s = 'reg ' + stanza_pairs2[i][0] + ' '+ stanza_pairs2[i][1] + '\n' + 'outreg2 using zero.doc, append\n'
        f2.write(s)
    f.close()
    f2.close()
    #return stanza_pairs1.extend(stanz_pairs2)

# helper function for getting relevant pairs of stanza_types
def get_rid_of_duplicates(list_of_tuples):
    duplicate_free_list = []
    for t in list_of_tuples:
        t1, t2 = t
        if (t2,t1) not in duplicate_free_list:
            duplicate_free_list.append(t)
    return duplicate_free_list

def combinations_per_timeperiod():
    pass

# function to calculate frequencies of each of the four points (0,0), (0,1), (1,1), (1,0)
def get_point_freq():
    point_freq_dict = {}
    points = [(0,0), (0,1), (1,1), (1,0)]

    # initial values
    for i in range(len(stanza_type)):
        t1 = stanza_type[i]
        for j in range(i+1, len(stanza_type)):
            t2 = stanza_type[j]
            t = (t1,t2)
            point_freq_dict[t] = {}
            for point in points:
                point_freq_dict[t][point] = 0 # initial count for each point for each pair
    #print(point_freq_dict)

    # iterate for each time period
    f = open('144days_cleaned.csv','r')
    f.readline()
    # for each time period
    for line in f:
        lst = line.strip().split(',')
        #print(lst[1:])
        # check each unique pair of stanza_types 
        # and increment count of the coordinate found from time_period matrix
        for i in range(1,len(lst)):
            t1 = stanza_type[i-1]
            change1 = int(lst[i])
            for j in range(i+1, len(lst)):
                t2 = stanza_type[j-1]
                change2 = int(lst[j-1])
                stanza_tuple = (t1, t2)
                change_tuple = (change1, change2)
                point_freq_dict[stanza_tuple][change_tuple] += 1
            
            # t1 = stanza_type[line_num-1].lower()
            # t2 = stanza_type[i-1].lower()
    f.close()
    #print(point_freq_dict)
    return point_freq_dict



def main():
    #add_stanza_names()
    #add_names_to_summary()
    #all_pairs = get_possibly_related_pairs()
    # function to calculate frequencies
    point_freq_dict = get_point_freq()

    # print frequencies
    f = open('point_frequencies.csv', 'w')
    f.write("Pairs, (0,0), (0,1), (1,1), (1,0)\n")
    for key in point_freq_dict:
        s = str(key) + ',' + str(point_freq_dict[key][(0,0)]) + ',' + str(point_freq_dict[key][(0,1)]) + ',' + str(point_freq_dict[key][(1,1)]) + ',' + str(point_freq_dict[key][(1,0)]) + '\n'
        f.write(s)
    f.close()





if __name__ == "__main__":
    main()
