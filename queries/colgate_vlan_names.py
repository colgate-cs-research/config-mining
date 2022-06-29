import argparse
import networkx as nx
import os
import sys
import tqdm
import pprint
import json

def main():
    with open("/shared/configs/colgate/daily/2022-03-06/configs/ocon6410.colgate.edu.json", 'r') as cfg_file:
        config = json.load(cfg_file)

    print("vlan_num","vlan_name")
    vlan_nums = sorted([int(v) for v in config["VLAN"].keys()])
    for vlan_num in vlan_nums:
        vlan_name = config["VLAN"][str(vlan_num)]["name"]
        print("{},{}".format(vlan_num, vlan_name))

if __name__ == "__main__":
    main()
