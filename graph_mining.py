import argparse
import json
import analyze
import networkx as nx
import ipaddress
import re

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
    fill_graph(edges, config, graph)
    #print(graph.edges())
    #make_edges("interfaces", "allowed_vlans", graph, config)

if __name__ == "__main__":
    main()