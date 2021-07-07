import networkx as nx
import random
import json
import generate_graph

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
#return dict {node: {suggested neighbors}}
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


#Calculates precision and recall for common neighbors
def precision_recall(graph, threshold):
    modified_graph, removed_edges = rand_remove(graph, threshold)
    nodes, neighbor_dict = common_neighbors(modified_graph, "interface", 0.90)
    print("num common neighbors:", len(neighbor_dict))
    print("neighbor_dict:", neighbor_dict)
    print()
    suggested = suggest_links(neighbor_dict, modified_graph) #dictionary
    print("removed edges:", removed_edges)
    print()
    print("suggested neighbors:",  suggested)
    print()
    removed_and_predicted = 0
    #calculates number of removed edges that were predicted
    for edge in removed_edges:
        sugg_count = 0
        for node, values in suggested.items():
            for value in values:
                sugg_count += 1
                if edge[0] == node and edge[1] == value:
                    removed_and_predicted += 1
    print("precision:", removed_and_predicted/sugg_count)
    print("recall:", removed_and_predicted/len(removed_edges))
    print()
    
''' 
#arguments: a networkx graph, a dict of suggested links {node: {suggested neighbors}}
#adds suggested neighbors in argument dicitonary to argument graph
def add_suggested_links(graph, suggested):
    for node, suggestions in suggested.items():
        
        graph.add_edge()
    return 
 '''

#returns a copy of argsument graph with num randomly removed links
#also draws original and modified graphs to separate png files
def rand_remove(graph, num):
    copy = graph.copy()
    removed_edges = []
    for i in range(num):
        edges = list(copy.edges)
        del_edge = random.choice(edges)
        print("link", del_edge, "removed")
        copy.remove_edge(del_edge[0], del_edge[1])
        removed_edges.append(del_edge)
    print()
    #draw graphs in png files
    '''
    og_graph = nx.drawing.nx_pydot.to_pydot(graph)
    og_graph.write_png('original.png')
    modified = nx.drawing.nx_pydot.to_pydot(copy)
    modified.write_png('modified.png')
    '''
    return copy, removed_edges


def main():
    graph = generate_graph.generate_graph("/shared/configs/uwmadison/2014-10-core/configs_json/r-432nm-b3a-1-core.json")
    '''
    graph.add_node("A", type="interface")
    graph.add_node("B", type="interface")
    graph.add_node("C", type="interface")
    graph.add_node("D", type="interface")

    graph.add_node("v1", type="vlan")
    graph.add_node("v2", type="vlan")
    graph.add_node("v3", type="vlan")
    graph.add_node("v4", type="vlan")
    graph.add_node("v5", type="vlan")
    graph.add_node("v6", type="vlan")
    graph.add_node("v7", type="vlan")

    graph.add_node("in", type="in_acl")
    graph.add_node("outA", type="out_acl")
    graph.add_node("outB", type="out_acl")
    
    #A
    graph.add_edge("A", "in")
    graph.add_edge("A", "outA")
    graph.add_edge("A", "v1")
    graph.add_edge("A", "v2")

    #B
    graph.add_edge("B", "in")
    graph.add_edge("B", "outB")
    graph.add_edge("B", "v1")
    graph.add_edge("B", "v2")

    #C
    graph.add_edge("C", "v3")
    graph.add_edge("C", "v4")
    graph.add_edge("C", "v5")

    #D
    graph.add_edge("D", "v5")
    graph.add_edge("D", "v6")
    graph.add_edge("D", "v7")
    '''
    #---------------------------------------------------
    precision_recall(graph, 20)
    #---------------------------------------------------
    #nodes, neighbor_dict = common_neighbors(modified_graph, "interface", 0.75)
    #suggested = suggest_links(neighbor_dict, modified_graph)
    #print("suggested neighbors:",  suggested)
    #print(neighbor_dict)
    '''
    ntype_list = ["vlan", "in_acl", "out_acl", "subnet"] #add keywords
    similarity_dict = get_similarity(neighbor_dict, graph, ntype_list)
    for key, val in similarity_dict.items():
        print(key, val)
        print()
    '''    

if __name__ == "__main__":
    main()
