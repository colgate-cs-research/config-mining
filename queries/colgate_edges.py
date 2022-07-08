import argparse
import networkx as nx
import os
import sys
import tqdm
import pprint

queries_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.dirname(queries_dir))
import graphs.graph_utils as graph_utils

def vlan_iface2vlan(graph):
    vlans = graph_utils.get_nodes(graph, "vlan")
    for vlan in vlans:
        ports = graph_utils.get_neighbors(vlan, graph, "port")
        for port in ports:
            if "vlan" in port:
                print("{} - {}".format(vlan, port))

def lag_iface2lag(graph):
    lags = graph_utils.get_nodes(graph, "lacp-aggregation-key")
    for lag in lags:
        ifaces = graph_utils.get_neighbors(lag, graph, "interface")
        for iface in ifaces:
            if True or "lag" in iface:
                print("{} - {}".format(lag, iface))


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Check for presence of edges in a graph')
    parser.add_argument('graph_path',type=str, 
            help='Path for a file containing a JSON representation of graph')
    arguments = parser.parse_args()

    graph = graph_utils.load_graph(arguments.graph_path)
    vlan_iface2vlan(graph) 
    lag_iface2lag(graph) 

if __name__ == "__main__":
    main()
