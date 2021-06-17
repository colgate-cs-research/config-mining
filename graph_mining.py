import argparse
import json
import analyze
import networkx as nx

def load_file(file):
    # Load config
    with open(file, "r") as infile:
        config = json.load(infile)
    return config


#constructs a node in 
def fill_graph(edges, file, graph):
    for interface in file["interfaces"]:
        graph.add_node(interface, type="interface")
        for edge in edges:
            node_type = edge[:-1]
            if file["interfaces"][interface][edge] is not None:
                graph.add_node(file["interfaces"][interface][edge], type=node_type)
                graph.add_edge(interface, file["interfaces"][interface][edge])
    return 

    #file[access_name] == file["interfaces"]
    #file[vlans == file["vlans"]] ---> file[interfaces][vlans]

def make_edges(group, edges, graph, file):
    for stanza in list(graph):
        if file[group][stanza][edges] is not None:
            for newnode in file[group][stanza][edges]:
                graph.add_node(newnode)
                graph.add_edge(stanza, newnode)
                #add more attributes to the nodes like the name alonged with it
                #set node attributes
    return graph


def main():
    config = load_file("/shared/configs/uwmadison/2014-10-core/configs_json/r-432nm-b3a-1-core.json")
    graph = nx.Graph() 
    edges = [ "access_vlan", "address", "description"]
    fill_graph(edges, config, graph)
    #print(graph.nodes())
    print(graph.edges())

    #make_edges("interfaces", "allowed_vlans", graph, config)

if __name__ == "__main__":
    main()