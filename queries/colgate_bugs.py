import argparse
import networkx as nx
import os
import sys
import tqdm

queries_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.dirname(queries_dir))
import graphs.graph_utils as graph_utils

def ems_vlans_bug(graph):
    vlans = graph_utils.get_neighbors("ems", graph, "vlan")
    print("VLANs with keyword 'ems'", vlans)
    interfaces = {}
    for vlan in vlans:
        interfaces[vlan] = graph_utils.get_neighbors(vlan, graph, "interface")

    print("VLAN 474 only:",  interfaces["Vlan474"].difference(interfaces["Vlan478"]))
    print("VLAN 478 only:",  interfaces["Vlan478"].difference(interfaces["Vlan474"]))

def simplivity_vlans_bug(graph):
    vlans = graph_utils.get_neighbors("simplivity", graph, "vlan")
    print("VLANs with keyword 'simplivity'", vlans)
    interfaces = {}
    for vlan in vlans:
        interfaces[vlan] = graph_utils.get_neighbors(vlan, graph, "interface")

    print("VLAN 520 only:",  interfaces["Vlan520"].difference(interfaces["Vlan540"]))
    print("VLAN 540 only:",  interfaces["Vlan540"].difference(interfaces["Vlan520"]))

def keyword_pair_bug(graph, keyword, middle_type, other_type):
    vlans = list(graph_utils.get_neighbors(keyword, graph, middle_type))
    print((middle_type + " with keyword " + keyword), vlans)
    interfaces = {}
    for vlan in vlans:
        interfaces[vlan] = graph_utils.get_neighbors(vlan, graph, other_type)

    print((vlans[0] + " only:"),  interfaces[vlans[0]].difference(interfaces[vlans[1]]))
    print((vlans[1] + " only:"),  interfaces[vlans[1]].difference(interfaces[vlans[0]]))


def vlan_pair_bug(graph, vlan1, vlan2):
    # do the vlans share the anchor node? (anchor == type interface)
    interfaces1 = graph_utils.get_neighbors(vlan1, graph, "interface")
    interfaces2 = graph_utils.get_neighbors(vlan2, graph, "interface")
    print((vlan1 + " only:"),  interfaces1.difference(interfaces2))

def get_relevant_cycles(graph, path="/shared/configs/colgate/daily/2022-03-06/cycles_jun13/consider", threshold=5):
    for file in os.listdir(path):
        print(file)
        get_relevant_cycles_file(graph, os.path.join(path, file), threshold)

def get_relevant_cycles_file(graph, filepath, threshold):
    vlan_tuples = []
    f = open(filepath, 'r')
    for line in f:
        lst = line.strip().split(',')
        nodes = lst[0].split()
        # vlan1 = lst[0].split()[1]
        # vlan2 = lst[0].split()[-1]
        # middle_node = lst[0].split()[-2]
        # vlan_tuple = (vlan1, vlan2)
        if True or (vlan2,vlan1) not in vlan_tuples:
            #vlan_tuples.append(vlan_tuple)
            cycle_percent = float(lst[-1])
            diff = float(lst[-2]) - float(lst[-3])
            if ((cycle_percent < 100) and (cycle_percent > 90)):
                if diff <= threshold:
                    print(line, end='')
                    # check which type of cycle it is
                    if nodes[1].startswith('Vlan') and nodes[3].startswith('Vlan'):
                        #(vlan1 != 'vlan') and (vlan2 != 'vlan'):
                        pass
                        vlan_pair_bug(graph, nodes[1], nodes[3])
                    elif nodes[0].startswith('Vlan') and nodes[2].startswith('Vlan'):
                        pass
                        vlan_pair_bug(graph, nodes[2], nodes[0])
                    elif (nodes.count('vlan') == 2):
                        keyword_pair_bug(graph, nodes[1], 'vlan', 'interface')
                    elif (nodes.count('interface') == 2):
                        keyword_pair_bug(graph, nodes[2], 'interface', 'vlan')
    # check if the % is between 95 and 100

    # check if difference is < 100

    # print to file
    f.close()


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Analyze subgraphs involving VLANs')
    parser.add_argument('graph_path',type=str, 
            help='Path for a file containing a JSON representation of graph')
    #parser.add_argument('cycles_path',type=str, 
        #help='Path for a folder containing csv files of cycles and their frequencies')
    arguments = parser.parse_args()

    graph = graph_utils.load_graph(arguments.graph_path)
    #ems_vlans_bug(graph)
    #simplivity_vlans_bug(graph)
    #vlans_bug(graph, 'simplivity', 'Vlan520','Vlan540')
    get_relevant_cycles(graph)
    

if __name__ == "__main__":
    main()
