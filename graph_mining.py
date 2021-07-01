import argparse
import json

from networkx.algorithms.components.connected import connected_components, number_connected_components
import analyze
import networkx as nx
#import pydot
import ipaddress
import re
from extract_keywords import get_keywords, add_keywords, analyze_configuration
import random

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

        #added create node line (undefined allowed vlans???????)
        if file["interfaces"][interface]["allowed_vlans"] is not None:
            for vlan in file["interfaces"][interface]["allowed_vlans"]:
                graph.add_node( "Vlan" + str(vlan), type="vlan")
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

#returns list of all nodes of target_type in argument graph
def get_nodes(graph, target_type):
    types = nx.get_node_attributes(graph, "type")
    node_list = []
    for node in graph:
        if types[node] == target_type:
            node_list.append(node)
    return node_list

#returns two floats indicating similarity of nodes' neighbors
def compare_nodes(n1,n2,graph):
    n1_edges = graph.edges(n1)
    n2_edges = graph.edges(n2)
    if len(n1_edges) == 0 or len(n2_edges) == 0:
        return 0, 0
    count = 0
    for edges1 in n1_edges:
        node1 = edges1[1]
        for edges2 in n2_edges:
            node2 = edges2[1]
            if node1 == node2:
                count += 1
    n1_similarity = count / len(n1_edges)
    n2_similarity = count / len(n2_edges)

    return n1_similarity, n2_similarity


#determines which nodes meet similarity threshold
#returns a list of nodes of ntype
#Also returns a dict including similar node pairs {(n1,n2): [similarity of n1, similarity of n2]}
def common_neighbors(graph, ntype, threshold):
    neighbor_dictionary = {}
    nodes = get_nodes(graph, ntype)
    for i in range(len(nodes)):
        for j in range(i+1, len(nodes)):
            n1_similarity, n2_similarity = compare_nodes(nodes[i], nodes[j], graph)
            if n1_similarity >= threshold and n2_similarity >= threshold and (n1_similarity != 1 or n2_similarity != 1):
                node_list = (nodes[i], nodes[j])
                neighbor_dictionary[node_list] = [n1_similarity, n2_similarity]
    return nodes, neighbor_dictionary


#suggests links for common neighbors in graph
#return dict {node: {suggested neghbors}}
def suggest_links(neighbor_dictionary, graph):
    larger_copy = nx.Graph()
    smaller_copy = nx.Graph()
    sugg_dict = {}
    for pair, similarity in neighbor_dictionary.items():
        if len(graph.edges(pair[0])) > len(graph.edges(pair[1])):
            larger = pair[0]
            smaller = pair[1]
        else:
            larger = pair[1]
            smaller = pair[0]
 
        for edge in graph.edges(larger):
            larger_copy.add_node(edge[1])
        for edge in graph.edges(smaller):
            smaller_copy.add_node(edge[1])
        suggestions = larger_copy.nodes() - smaller_copy.nodes()
        sugg_dict[smaller] = suggestions

    return sugg_dict


#returns two floats indicating similarity of nodes' neighbors of ntype
def similarity_proportions(n1, n2, graph, ntype):
    type_list = get_nodes(graph, ntype)
    n1_edges = graph.edges(n1) #returns a list of each pairing in a tuple
    n2_edges = graph.edges(n2)
    match = 0
    total1 = len(n1_edges)
    total2 = len(n2_edges)

    for edges1 in n1_edges: 
        node1 = edges1[1] #get neighbor
        if node1 in type_list: #check type
            for edges2 in n2_edges:
                if edges1[1] == edges2[1]:
                    match += 1

    return match/total1, match/total2

#returns a dictionary {interface pair: {type: proportion of the type within the interface, ...}}
#Goes through all interfaces and finds the proportion of similarity between all the 
#types (vlan, subnet, out_acl, in_acl)
def get_similarity(neighbor_dict, graph, ntype_list):
    similarity_dict = {}
    for pair in neighbor_dict:
        ntype_dictionary = {}
        for ntype in ntype_list:
            proportion = similarity_proportions(pair[0], pair[1], graph, ntype)
            ntype_dictionary[ntype] = proportion
        similarity_dict[pair] = ntype_dictionary
    return similarity_dict

#Randomly deletes as many edges in a graph, threshold is how many edges user wants to delete
def random_delete(graph, threshold):
    edges = graph.edges()
    edge_list = []
    removed_edges = []

    for edge in edges:
        edge_list.append(edge)

    count = 0
    length = len(edge_list)

    while count < threshold:
        number = random.randint(0, length-1)
        delete = edge_list[number]
        graph.remove_edge(delete[0], delete[1])
        edge_list.remove(delete)
        removed_edges.append(delete)
        length -= 1
        count += 1
    return edges, removed_edges

#Calculates precision and recall for common neighbors
def precision_recall(graph, threshold):
    original_edge_list = graph.edges()
    print("original edge list: ", original_edge_list)
    nodes, neighbor_dict = common_neighbors(graph, "interface", 0.60)
    new_edge_list,removed_edges = random_delete(graph, threshold)
    print("new edge list: ", new_edge_list)
    print("removed edges: ", removed_edges)
    suggested = suggest_links(neighbor_dict, graph) #dictionary
    print("suggested neighbors:",  suggested)
    print()

    removed_and_predicted = 0

    #calculates number of removed edges that were predicted
    for edge in removed_edges:
        for node, values in suggested.items():
            for value in values:
                if edge[0] == node and edge[1] == value:
                    removed_and_predicted += 1
    print(removed_and_predicted)
    
def main():
    config = load_file("/shared/configs/northwestern/configs_json/core1.json")
    #config = load_file("/shared/configs/uwmadison/2014-10-core/configs_json/r-432nm-b3a-1-core.json")
    graph = nx.Graph() 
    #fill_graph(config, graph)
    
    graph.add_node("A", type="interface")
    graph.add_node("B", type="interface")
    graph.add_node("C", type="interface")
    graph.add_node("sn1", type="subnet")
    graph.add_node("sn2", type="subnet")
    graph.add_node("sn3", type="subnet")

    graph.add_edge("A", "sn1")
    graph.add_edge("A", "sn2")
    graph.add_edge("A", "sn3")
    graph.add_edge("B", "sn1")
    graph.add_edge("B", "sn2")
    
    precision_recall(graph, 1)

    #ntype_list = ["vlan", "in_acl", "out_acl", "subnet", "allowed_vlans"]
    #similarity_dict = get_similarity(neighbor_dict, graph, ntype_list)
    #print(similarity_dict)

    #print("\nComponents in graph: " + str(number_connected_components(graph)))
    
    #for component in connected_components(graph):
    #print(component)
    #add_keywords("/shared/configs/uwmadison/2014-10-core/configs_json/r-432nm-b3a-1-core.json", graph)
    
    #create_visual(graph)
    #pydot_graph = nx.drawing.nx_pydot.to_pydot(graph)
    #pydot_graph.write_png('output2.png')


if __name__ == "__main__":
    main()