import analyze
import argparse
import json

def main():
    #parsing command-line arguments
    parser = argparse.ArgumentParser(description='Analyze confidence for vlan pairs')
    parser.add_argument('config_path', help='Path for a file (or directory) containing a JSON representation of configuration(s)')
    parser.add_argument('out_path', help='Name of file (or directory) to write JSON file(s) containing vlan confidence values')

    arguments = parser.parse_args()
    analyze.process_configs(analyze_configuration, arguments.config_path, arguments.out_path)

'''adds vlan pair frequencies to corresponding dictionary value '''
def generate_vlan_pairs(vlan_list, vlan_pair_freq, single_vlan_freq, freq=1): 
    if len(vlan_list) == 1:
        if (vlan_list[0] in single_vlan_freq):
            single_vlan_freq[vlan_list[0]] += freq
        else:
            single_vlan_freq[vlan_list[0]] = freq
        return
        
    for i in range(len(vlan_list)): #vlan1
        vlan1 = vlan_list[i]
        if vlan1 in single_vlan_freq:
            single_vlan_freq[vlan1] += freq
        else:
            single_vlan_freq[vlan1] = freq

        for j in range(i+1, len(vlan_list)): #vlan2
            vlan2 = vlan_list[j]
            pair = (vlan_list[i], vlan_list[j])
            if vlan_list[j] < vlan_list[i]:
                pair = (pair[1], pair[0])
            #pair already in dict->increment
            if (pair in vlan_pair_freq):
                vlan_pair_freq[pair] += freq
            #add pair to dict
            else:
                vlan_pair_freq[pair] = freq
    return

def format_confidence_ouput(vlan_pair_freq, single_vlan_freq):
    rules = []
    for (vpair, freq) in vlan_pair_freq.items():
        vlans = vpair
        for vlan in vlans:
            message = "C(iface accepts vlan " + str(vlan) + "-> iface accepts vlans "+ str(vpair) + ")" 
            rules.append(analyze.create_rule(message, freq, single_vlan_freq[vlan]))
    return rules

'''returns a dictionary with {vlan pair [x,y] : frequency accepted in an interface}'''
def analyze_configuration(file, outfile):
    print("Current working FILE: "+file)
    vlan_pair_freq = {}
    single_vlan_freq = {}
    # Load config
    with open(file, "r") as infile:
        config = json.load(infile)
    
    #iterate over interfaces to find unique sets of allowed VLANs
    for (iface, properties) in config["interfaces"].items():
        if properties["switchport"] == "trunk" and properties["allowed_vlans"] is not None:
            vlan_list = properties["allowed_vlans"]
            if len(vlan_list) > 1024:
                print("Skipping %s:%s which allows %d vlans"  % (config["name"], iface, len(vlan_list)))
                continue
            generate_vlan_pairs(vlan_list, vlan_pair_freq, single_vlan_freq)
            #if vlan_list in vlan_lists:
            #    vlan_lists[vlan_list] += 1
            #else:
            #    vlan_lists[vlan_list] = 1
    
    # Iterate over VLAN lists
    #for vlan_list, freq in vlan_lists.items():
        #generate_vlan_pairs(vlan_list, vlan_pair_freq, single_vlan_freq, freq)
    #print(single_vlan_freq)
    rules = format_confidence_ouput(vlan_pair_freq, single_vlan_freq)
    analyze.write_to_outfile(outfile, rules)

    return 


if __name__ == "__main__":
    main()