import argparse
import json
import analyze
import networkx as nx

def load_file(file):
    # Load config
    with open(file, "r") as infile:
        config = json.load(infile)
    return config

#node is what the vertice is if it is interfaces or acl etc.
def make_nodes(node, file):
    graph = nx.Graph()
    for stanza in file[node]:
        graph.add_node(stanza)
    return graph

def make_edges(group, edges, graph, file):
    for iface in list(graph):
        allowed_vlans = file[group][iface][edges]
        if allowed_vlans is not None:
            for vlan in allowed_vlans:
                graph.add_node(vlan)
                graph.add_edge(iface, vlan)
    return graph


def main():
    config = load_file("/shared/configs/uwmadison/2014-10-core/configs_json/r-432nm-b3a-1-core.json")
    graph = make_nodes("interfaces", config)
    make_edges("interfaces", "allowed_vlans", graph, config)
   # print("Nodes of graph: ")
    #print(graph.nodes())
    #print("edges of graph: ")
    #print(graph.edges())

if __name__ == "__main__":
    main()