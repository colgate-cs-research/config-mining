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

def vlans_bug(graph, keyword, vlan1, vlan2):
    vlans = graph_utils.get_neighbors(keyword, graph, "vlan")
    print(("VLANs with keyword " + keyword), vlans)
    interfaces = {}
    for vlan in vlans:
        interfaces[vlan] = graph_utils.get_neighbors(vlan, graph, "interface")

    print((vlan1 + " only:"),  interfaces[vlan1].difference(interfaces[vlan2]))
    print((vlan2 + " only:"),  interfaces[vlan2].difference(interfaces[vlan1]))

def vlans_bug(graph, keyword, vlan1, vlan2):
    interfaces1 = graph_utils.get_neighbors(vlan1, graph, "interface")
    interfaces2 = graph_utils.get_neighbors(vlan2, graph, "interface")
    print(("Interfaces that allow " + vlan1), interfaces1)
    print(("Interfaces that allow " + vlan2), interfaces2)
    interfaces = {}
    for vlan in vlans:
        interfaces[vlan] = graph_utils.get_neighbors(vlan, graph, "interface") # returns a set

    print((vlan1 + " only:"),  interfaces[vlan1].difference(interfaces[vlan2]))
    print((vlan2 + " only:"),  interfaces[vlan2].difference(interfaces[vlan1]))

def get_relevant_cycles(graph):
    vlan_tuples = []
    f = open('d-3_s-interface_t-90_n-vlan.csv', 'r')
    for line in f:
        lst = line.strip().split(',')
        vlan1 = lst[0].split()[1]
        vlan2 = lst[0].split()[-1]
        keyword = lst[0].split()[-2]
        vlan_tuple = (vlan1, vlan2)
        if (vlan2,vlan1) not in vlan_tuples:
            vlan_tuples.append(vlan_tuple)
            cycle_percent = float(lst[-1])
            diff = float(lst[-2]) - float(lst[-3])
            if ((cycle_percent < 100) and (cycle_percent > 90)):
                if diff < 50:
                    print(line, end='')
                    #vlans_bug(graph, keyword, vlan1, vlan2)
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
