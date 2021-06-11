import argparse
import glob
import json
import os

def main():
    #parsing command-line arguments
    parser = argparse.ArgumentParser(description='Analyze confidence for vlan pairs')
    parser.add_argument('config_path', help='Path for a file (or directory) containing a JSON representation of configuration(s)')
    parser.add_argument('out_path', help='Name of file (or directory) to write JSON file(s) containing vlan confidence values')

    arguments = parser.parse_args()
    process_configs(arguments.config_path,arguments.out_path)


def process_configs(config_path,out_path):
    print("INPUT: "+config_path+" OUTPUT: "+out_path)
    if os.path.isfile(config_path):
        print("Input is a file")
        get_iface_accepted_vlans(config_path, out_path)
    else:
        if os.path.isdir(out_path):
            files = glob.glob(config_path + '/**/*.json', recursive=True)
            for file in files:
                print("Current working FILE: "+file)
                get_iface_accepted_vlans(file,os.path.join(out_path, os.path.basename(file)))
        else:
            print("ERROR: input path is a directory; output path is not a directory")

'''adds vlan pair frequencies to corresponding dictionary value '''
def generate_vlan_pairs(vlan_list, vlan_pair_freq, single_vlan_freq): 
    if len(vlan_list) == 1:
        if (vlan_list[0] in single_vlan_freq):
            single_vlan_freq[vlan_list[0]] += 1
        else:
            single_vlan_freq[vlan_list[0]] = 1
        return
        
    for i in range(len(vlan_list)): #vlan1
        vlan1 = vlan_list[i]
        if vlan1 in single_vlan_freq:
            single_vlan_freq[vlan1] += 1
        else:
            single_vlan_freq[vlan1] = 1

        for j in range(i+1, len(vlan_list)): #vlan2
            vlan2 = vlan_list[j]
            if vlan1 != vlan2:
                pair = str(vlan_list[i]) + ", " + str(vlan_list[j])
                reverse_pair = str(vlan_list[j]) + ", " + str(vlan_list[i])
                #pair already in dict->increment
                if (pair in vlan_pair_freq):
                    vlan_pair_freq[pair] += 1
                elif (reverse_pair in vlan_pair_freq):
                    vlan_pair_freq[reverse_pair] += 1
                #add pair to dict
                else:
                    vlan_pair_freq[pair] = 1
    return


'''Writes confidence/support for association rules to JSON file'''
def write_to_outfile(filename, rules):
    with open(filename, 'w') as outfile:         
        json.dump(rules, outfile, indent=4, sort_keys=True)
    return   


def format_confidence_ouput(vlan_pair_freq, single_vlan_freq):
    rules = []
    for (vpair, freq) in vlan_pair_freq.items():
        vlans = vpair.split(", ")
        for vlan in vlans:
            rule = {
                "message" : "C(interface accepts vlan " + str(vlan) + "-> interface accepts both vlans "+ str(vpair) + ")",
                "n" : "Num interfaces that accept both vlans "+ str(vpair) + ": " + str(freq),
                "d" : "Num interfaces that accept vlan " + str(vlan) + ": " + str(single_vlan_freq[int(vlan)]),
                "c": "Confidence: " + str(compute_confidence(freq, single_vlan_freq[int(vlan)]))
            }
            rules.append(rule)
    return rules

#compute percentage of interfaces that are in range and have ACL applied
def compute_confidence(numerator, denominator):
    if (denominator > 0):
        return round(numerator / denominator, 3)
    return None

'''returns a dictionary with {vlan pair [x,y] : frequency accepted in an interface}'''
def get_iface_accepted_vlans(file, outfile):
    vlan_pair_freq = {}
    single_vlan_freq = {}
    # Load config
    with open(file, "r") as infile:
        config = json.load(infile)
    
    #iterate over interfaces
    for (iface, properties) in config["interfaces"].items():
        if properties["switchport"] == "trunk" and properties["allowed_vlans"] is not None:
            vlan_list = properties["allowed_vlans"]
            generate_vlan_pairs(vlan_list, vlan_pair_freq, single_vlan_freq)
    #print(single_vlan_freq)
    rules = format_confidence_ouput(vlan_pair_freq, single_vlan_freq)
    write_to_outfile(outfile, rules)

    return 


if __name__ == "__main__":
    main()