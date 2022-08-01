import argparse


# function for printing

# function for getting cycle

# function for removing duplicates

# check duplicates to see how the ratios change based on anchor node

def main():
    parser = argparse.ArgumentParser(description='Generate a graph')
    parser.add_argument('bugs_path',type=str, help='Path for a file (or directory) containing a text files of bugs.')
    arguments = parser.parse_args()

    f = open(arguments.bugs_path, 'r')

    f3_less = open("three_less9.txt", 'w')
    f3_9_100 = open("three_9_100.txt", 'w')
    f3_100 = open("three_100.txt", 'w')
    f4_less = open("four_less9.txt", 'w')
    f4_9_100 = open("four_9_100.txt", 'w')
    f4_100 = open("four_100.txt", 'w')
    f5_less = open("five_less9.txt", 'w')
    f5_9_100 = open("five_9_100.txt", 'w')
    f5_100 = open("five_100.txt", 'w')

    num_three = 0
    num_three_9 = 0
    num_three_9_100 = 0
    num_three_100 = 0
    num_four = 0
    num_four_9 = 0
    num_four_9_100 = 0
    num_four_100 = 0
    num_five = 0
    num_five_9 = 0
    num_five_9_100 = 0
    num_five_100 = 0

    total = 0
    counted = 0

    sig_dict = {}  # stores unique path signatures 
    gen_sig_dict = {} # stores unique general path signatures

    for line in f:

        total += 1

        l = line.strip().split(',')

        cycle = l[0].split()
        cycle_len = len(cycle)
        existence_ratio   = float(l[-1])

        if (cycle_len == 3) or (cycle_len == 6):
            counted += 1
            num_three += 1
            if (existence_ratio < 90):
                num_three_9 += 1
                f3_less.write(line)
            elif (existence_ratio == 100):
                num_three_100 += 1
                f3_100.write(line)
            else:
                num_three_9_100 += 1
                f3_9_100.write(line)

            #track sig
            sig = ''
            gen_sig = ''
            if (cycle_len == 3):
                sig += cycle[0] +  ", " + cycle[1] + ", " + cycle[2]
            if (cycle_len == 6):
                sig += cycle[0] +  ", " + cycle[1] + ", " + cycle[2]
                gen_sig += cycle[3] +  ", " + cycle[4] + ", " + cycle[5]
            if sig not in sig_dict:
                sig_dict[sig] = 0
            sig_dict[sig] += 1
            if gen_sig != '':
                if gen_sig not in sig_dict:
                    gen_sig_dict[gen_sig] = 0
                gen_sig_dict[gen_sig] += 1

            

        if (cycle_len == 4) or (cycle_len == 8):
            counted += 1
            num_four += 1
            if (existence_ratio < 90):
                num_four_9 += 1
                f4_less.write(line)
            elif (existence_ratio == 100):
                num_four_100 += 1
                f4_100.write(line)
            else:
                num_four_9_100 += 1
                f4_9_100.write(line)

            #track sig
            sig = ''
            gen_sig = ''
            if (cycle_len == 4):
                sig += cycle[0] +  ", " + cycle[1] + ", " + cycle[2] + ", " + cycle[3]
            if (cycle_len == 8):
                sig += cycle[0] +  ", " + cycle[1] + ", " + cycle[2] + ", " + cycle[3]
                gen_sig += cycle[4] +  ", " + cycle[5] + ", " + cycle[6] + ", " + cycle[7]
            if sig not in sig_dict:
                sig_dict[sig] = 0
            sig_dict[sig] += 1
            if gen_sig != '':
                if gen_sig not in gen_sig_dict:
                    gen_sig_dict[gen_sig] = 0
                gen_sig_dict[gen_sig] += 1
        
        if (cycle_len == 5) or (cycle_len == 10):
            counted += 1
            num_five += 1
            if (existence_ratio < 90):
                num_five_9 += 1
                f5_less.write(line)
            elif (existence_ratio == 100):
                num_five_100 += 1
                f5_100.write(line)
            else:
                num_five_9_100 += 1
                f5_9_100.write(line)

            #track sig
            sig = ''
            gen_sig = ''
            if (cycle_len == 5):
                sig += cycle[0] +  ", " + cycle[1] + ", " + cycle[2] + ", " + cycle[3] + ", " + cycle[4]
            if (cycle_len == 10):
                sig += cycle[0] +  ", " + cycle[1] + ", " + cycle[2] + ", " + cycle[3] + ", " + cycle[4]
                gen_sig += cycle[5] +  ", " + cycle[6] + ", " + cycle[7] + ", " + cycle[8] + ", " + cycle[9]
            if sig not in sig_dict:
                sig_dict[sig] = 0
            sig_dict[sig] += 1
            if gen_sig != '':
                if gen_sig not in gen_sig_dict:
                    gen_sig_dict[gen_sig] = 0
                gen_sig_dict[gen_sig] += 1


    f.close()

    f3_less.close()
    f3_9_100.close()
    f3_100.close()
    f4_less.close()
    f4_9_100.close()
    f4_100.close()
    f5_less.close()
    f5_9_100.close()
    f5_100.close()

    print("Total number of cycles found: " + str(total))

    print("Number of cycles counted: " + str(counted))

    print("Number of 3-node cycles found: " + str(num_three))
    print("Number of 3-node cycles with less than 90% existence_ratio: " + str(num_three_9))
    print("Number of 3-node cycles with 90-100% existence_ratio: " + str(num_three_9_100))
    print("Number of 3-node cycles with 100% existence_ratio: " + str(num_three_100))
   
    print("Number of 4-node cycles found: " + str(num_four))
    print("Number of 4-node cycles with less than 90% existence_ratio: " + str(num_four_9))
    print("Number of 4-node cycles with 90-100% existence_ratio: " + str(num_four_9_100))
    print("Number of 4-node cycles with 100% existence_ratio: " + str(num_four_100))

    print("Number of 5-node cycles found: " + str(num_five))
    print("Number of 5-node cycles with less than 90% existence_ratio: " + str(num_five_9))
    print("Number of 5-node cycles with 90-100% existence_ratio: " + str(num_five_9_100))
    print("Number of 5-node cycles with 100% existence_ratio: " + str(num_five_100))

    '''print()
    print("Total specific signatures found: ")
    print("Path\t\t\t\t  Count")
    total = 0
    for key in sig_dict:
        count = sig_dict[key]
        total += count
        if count > 40:
            print(key+"  "+str(count))
    print("Total count of specific signatures: " + str(total))'''

    set_lst = []
    to_remove = []
    for key in gen_sig_dict:
        s = set(key.split(","))
        if s not in set_lst:
            set_lst.append(s)
        else:
            to_remove.append(key)
    for key in to_remove:
        gen_sig_dict.pop(key)


    print()
    print("Unique general paths found: " + str(len(gen_sig_dict)))
    print("Gen_Path\t\t\t\t\t\t\t\t\t\t  Count")
    total = 0
    for key in gen_sig_dict:
        count = gen_sig_dict[key]
        total += count
        if count > 40:
            print(key+"  "+str(count))
    print("Total count = " + str(total))


if __name__=="__main__":
    main()
