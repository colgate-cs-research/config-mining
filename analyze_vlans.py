import argparse
import glob
import json
import os
import nltk
from nltk.corpus import stopwords
import re

def main():
    #parsing command-line arguments
    parser = argparse.ArgumentParser(description='Analyze confidence for vlan pairs')
    parser.add_argument('config_path', help='Path for a file (or directory) containing a JSON representation of configuration(s)')
    parser.add_argument('out_path', help='Name of file (or directory) to write JSON file(s) containing vlan confidence values')

    arguments = parser.parse_args()
    nltk.download('stopwords')
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



def write_to_outfile(filename, vlan_pair_freq, single_vlan_freq):
    with open(filename, 'w') as outfile:
        outfile.write("Vlan dict")
        json.dump(single_vlan_freq, outfile, indent=4, sort_keys=True)
        outfile.write("\n\nVlan Pair dict")
        json.dump(vlan_pair_freq, outfile, indent=4, sort_keys=True)
    return   



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
            
    write_to_outfile(outfile, vlan_pair_freq, single_vlan_freq)
    return 


if __name__ == "__main__":
    main()