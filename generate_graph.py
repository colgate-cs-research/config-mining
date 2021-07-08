import argparse
import json

from networkx.algorithms.components.connected import connected_components, number_connected_components
import networkx as nx
#import pydot
import ipaddress
import re
from extract_keywords import analyze_configuration

def load_file(file):
    # Load config
    with open(file, "r") as infile:
        config = json.load(infile)
    return config

#constructs graph based on argument config file
def make_graph(config):
    graph = nx.Graph()
    for acl in config["acls"]:
        graph.add_node(acl, type= "acl")
        #print(graph.nodes[acl])

    regex = re.compile(r'Vlan\d+')
    for interface in config["interfaces"]:
        if regex.match(interface):
            print(interface, "vlan")
            graph.add_node(interface, type="vlan")
        else:    
            print(interface, "interface")
            graph.add_node(interface, type="interface")
        
        if config["interfaces"][interface]["address"] is not None:
            address = config["interfaces"][interface]["address"]
            network_obj = ipaddress.IPv4Interface(address)
            graph.add_node(str(network_obj.network), type="subnet")
            graph.add_edge(interface, str(network_obj.network))

        #added create node line (undefined allowed vlans???????)
        if config["interfaces"][interface]["allowed_vlans"] is not None:
            for vlan in config["interfaces"][interface]["allowed_vlans"]:
                graph.add_node( "Vlan" + str(vlan), type="vlan")
                graph.add_edge(interface, "Vlan" + str(vlan))

        if config["interfaces"][interface]["in_acl"] is not None:
            graph.add_edge(interface, config["interfaces"][interface]["in_acl"], type = "in_acl")
        if config["interfaces"][interface]["out_acl"] is not None:
            graph.add_edge(interface, config["interfaces"][interface]["out_acl"], type = "out_acl")

    return graph

#Adding individual keywords to each interface
def add_keywords(keyword_path, graph):
    with open(keyword_path, 'r') as keyword_file:
        keyword_json = json.load(keyword_file)
    for interface, keywords in keyword_json["interfaces"].items():
        #graph.add_node(interface, type="interface")
        for word in keywords:
            graph.add_node(str(word), type="keyword")
            graph.add_edge(interface, str(word))

def generate_graph(config_path, keyword_path):
    config = load_file(config_path)
    #config = load_file("/shared/configs/uwmadison/2014-10-core/configs_json/r-432nm-b3a-1-core.json") 
    graph = make_graph(config)
    add_keywords(keyword_path, graph)
    
    #---------------------------------------------------
   
    #print("\nComponents in graph: " + str(number_connected_components(graph)))
    #for component in connected_components(graph):
    #print(component)
    
    #pydot_graph = nx.drawing.nx_pydot.to_pydot(graph)
    #pydot_graph.write_png('generated_graph.png')
    return graph

'''
if __name__ == "__main__":
    main()
'''