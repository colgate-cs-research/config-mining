#using apriori function
import analyze
import argparse
import json
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori

def main():
    #parsing command-line arguments
    parser = argparse.ArgumentParser(description='Analyze confidence for vlan pairs')
    parser.add_argument('config_path', help='Path for a file (or directory) containing a JSON representation of configuration(s)')
    parser.add_argument('out_path', help='Name of file (or directory) to write JSON file(s) containing vlan confidence values')
    parser.add_argument('-s', '--min_support', type=float, default=0.5, help ='Minimum support threshold')
    arguments = parser.parse_args()
    analyze.process_configs(analyze_configuration, arguments.config_path, arguments.out_path, arguments.min_support)
    
    return

def format_confidence_ouput(vlan_pair_freq, single_vlan_freq):
    rules = []
    for (vpair, freq) in vlan_pair_freq.items():
        vlans = vpair.split(", ")
        for i in range(2):
            vlan = vlans[i]
            otherv = vlans[(i+1)%2]
            message = "C(interface accepts vlan " + str(vlan) + "-> interface also accepts vlan "+ str(otherv) + ")" 
            rules.append(analyze.create_rule(message, freq, single_vlan_freq[vlan]))
    return rules

'''returns --------'''
def analyze_configuration(file, outfile, min_support):
    print("Current working FILE: "+file)
    accepted_vlans = []
    
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
            accepted_vlans.append(vlan_list)   
    
    te = TransactionEncoder()
    te_ary = te.fit(accepted_vlans).transform(accepted_vlans)
    df = pd.DataFrame(te_ary, columns=te.columns_)
    frequent = apriori(df, min_support = min_support, use_colnames=True)
    frequent['length'] = frequent['itemsets'].apply(lambda x: len(x))
    frequent = frequent[frequent["length"] >= 2]
    print(frequent)
    
    return 

if __name__ == "__main__":
    main()
