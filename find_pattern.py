import argparse
import networkx as nx
from link_prediction import load_graph

#find vlans that are connected to both argument keyword and acl 110
def find_pattern(graph, keyword):
    pattern_vlans = []
    if keyword in graph:
        print(keyword, "present in graph.")
        acl_neighbors = list(n for n in graph.neighbors(keyword) if graph.nodes[n]["type"] == "acl")
        for device_acl in acl_neighbors:
            acl = device_acl.split("_")[-1]  #separate acl from device name
            if acl == "110":
                print("ACL 110 FOUND:", device_acl)
                vlan_neighbors = list(n for n in graph.neighbors(device_acl) if graph.nodes[n]["type"] == "vlan")
                for vlan in vlan_neighbors:
                    if graph.has_edge(vlan, keyword):
                        pattern_vlans.append(vlan)
                break
    print("Vlans connected to both", keyword, "and acl 110:", pattern_vlans)
    return pattern_vlans

def main():
    #Parse command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    #required
    parser.add_argument('graph_path',type=str, 
            help='Path for a file (or directory) containing a JSON representation of graph(s)')
    parser.add_argument('keyword',type=str, 
            help='keyword to search for')
    arguments= parser.parse_args()
    graph = load_graph(arguments.graph_path)
    find_pattern(graph, arguments.keyword)


if __name__ == "__main__":
    main()
