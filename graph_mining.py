import argparse
import json

from networkx.algorithms.components.connected import connected_components, number_connected_components
import analyze
import networkx as nx
import pydot
import ipaddress
import re
from extract_keywords import get_keywords, add_keywords, analyze_configuration

def load_file(file):
    # Load config
    with open(file, "r") as infile:
        config = json.load(infile)
    return config


#constructs nodes to fill in argument graph
def fill_graph(file, graph):
    for acl in file["acls"]:
        graph.add_node(acl, type= "acl")
        #print(graph.nodes[acl])

    regex = re.compile('Vlan\d+')
    for interface in file["interfaces"]:
        if regex.match(interface):
            graph.add_node(interface, type="vlan")
        else:    
            graph.add_node(interface, type="interface")
        
        if file["interfaces"][interface]["address"] is not None:
            address = file["interfaces"][interface]["address"]
            network_obj = ipaddress.IPv4Interface(address)
            graph.add_node(str(network_obj.network), type="subnet")
            graph.add_edge(interface, str(network_obj.network))

        if file["interfaces"][interface]["allowed_vlans"] is not None:
            for vlan in file["interfaces"][interface]["allowed_vlans"]:
                graph.add_edge(interface, "Vlan" + str(vlan))

        if file["interfaces"][interface]["in_acl"] is not None:
            graph.add_edge(interface, file["interfaces"][interface]["in_acl"])
        if file["interfaces"][interface]["out_acl"] is not None:
            graph.add_edge(interface, file["interfaces"][interface]["out_acl"])

    return 

#Adding individual keywords to each interface
def add_keywords(file, graph):
    iface2keywords,_ = analyze_configuration(file, "output/testing.out")
    for interface, keywords in iface2keywords.items():
        graph.add_node(interface, type="interface")
        for word in keywords:
            graph.add_node(str(word), type="keyword")
            graph.add_edge(interface, str(word))

#
#def create_visual(graph):


def main():
    config = load_file("/shared/configs/northwestern/configs_json/core1.json")
    graph = nx.Graph() 
    fill_graph(config, graph)
    #print(graph.edges())
    print("\nComponents in graph: " + str(number_connected_components(graph)))
    
    #for component in connected_components(graph):
    #    print(component)
    #add_keywords("/shared/configs/uwmadison/2014-10-core/configs_json/r-432nm-b3a-1-core.json", graph)
    
    #print(graph.edges())
    #print(graph.nodes())

    #create_visual(graph)
    pydot_graph = nx.drawing.nx_pydot.to_pydot(graph)
    pydot_graph.write_png('output2.png')


if __name__ == "__main__":
    main()