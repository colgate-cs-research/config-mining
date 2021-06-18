import argparse
import json
import analyze
import networkx as nx
import ipaddress
import re
from extract_keywords import get_keywords, add_keywords, analyze_configuration

def load_file(file):
    # Load config
    with open(file, "r") as infile:
        config = json.load(infile)
    return config


#constructs nodes to fill in argument graph
def fill_graph(edges, file, graph):
    #for acl in file["acls"]:

    regex = re.compile('Vlan\d+')
    for interface in file["interfaces"]:
        #vlan
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
    return 

#Adding individual keywords to each interface
def add_keywords(file, graph):
    iface2keywords,_ = analyze_configuration(file, "output/testing.out")
    for interface, keywords in iface2keywords.items():
        graph.add_node(interface, type="interface")
        for word in keywords:
            graph.add_node(str(word), type="keyword")
            graph.add_edge(interface, str(word))

''''
def make_edges(group, edges, graph, file):
    for stanza in list(graph):
        if file[group][stanza][edges] is not None:
            for newnode in file[group][stanza][edges]:
                graph.add_node(newnode)
                graph.add_edge(stanza, newnode)
                #add more attributes to the nodes like the name alonged with it
                #set node attributes
    return graph
'''

def main():
    config = load_file("/shared/configs/uwmadison/2014-10-core/configs_json/r-432nm-b3a-1-core.json")
    graph = nx.Graph() 
    edges = ["address", "description", "allowed_vlans"]
    #fill_graph(edges, config, graph)
    #print(graph.edges())
    #make_edges("interfaces", "allowed_vlans", graph, config)

    add_keywords("/shared/configs/uwmadison/2014-10-core/configs_json/r-432nm-b3a-1-core.json", graph)
    
    #print(graph.edges())
    #print(graph.nodes())

if __name__ == "__main__":
    main()