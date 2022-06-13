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


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Analyze subgraphs involving VLANs')
    parser.add_argument('graph_path',type=str, 
            help='Path for a file containing a JSON representation of graph')
    arguments = parser.parse_args()

    graph = graph_utils.load_graph(arguments.graph_path)
    ems_vlans_bug(graph)
    simplivity_vlans_bug(graph)
    

if __name__ == "__main__":
    main()
