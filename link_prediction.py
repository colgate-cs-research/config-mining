import argparse
import json
import networkx as nx
import node2vec
import pprint
import random
import tqdm

get_nodes_cache = {}
get_edges_cache = {}

def clear_caches():
    global get_nodes_cache, get_edges_cache
    get_nodes_cache = {}
    get_edges_cache = {}

#returns list of all nodes of target_type in argument graph
def get_nodes(graph, target_type=None):
    # Check if previously computed
    if target_type in get_nodes_cache:
        return get_nodes_cache[target_type]

    # Compute
    types = nx.get_node_attributes(graph, "type")
    node_list = []
    for node in graph:
        if target_type is None or types[node] == target_type:
            node_list.append(node)

    # Cache and return result
    get_nodes_cache[target_type] = node_list
    return node_list

#return a list of all edges for node of target_type
def get_edges(node, graph, target_type=None):
    # Check if previously computed
    if target_type in get_edges_cache and node in get_edges_cache[target_type]:
        return get_edges_cache[target_type][node]

    # Compute
    types = nx.get_node_attributes(graph, "type")
    edge_list = []
    for edge in graph.edges(node):
        if target_type is None or types[edge[1]] == target_type:
            edge_list.append(edge)

    # Cache and return result
    if target_type not in get_edges_cache:
        get_edges_cache[target_type] = {}
    get_edges_cache[target_type][node] = edge_list
    return edge_list

#returns two floats indicating similarity of nodes' neighbors of ntype
def similarity_proportions(n1, n2, graph, ntype=None):
    type_list = get_nodes(graph, ntype)
    n1_edges = get_edges(n1, graph, ntype) #returns a list of each pairing in a tuple
    n2_edges = get_edges(n2, graph, ntype)
    match = 0
    total1 = len(n1_edges)
    total2 = len(n2_edges)

    matches = []
    for edges1 in n1_edges: 
        node1 = edges1[1] #get neighbor
        if node1 in type_list: #check type
            for edges2 in n2_edges:
                if edges1[1] == edges2[1]:
                    match += 1
                    matches.append(node1)

    n1_similarity, n2_similarity = 0, 0
    if total1 > 0:
        n1_similarity = match/total1
    if total2 > 0:
        n2_similarity = match/total2

    return n1_similarity, n2_similarity, matches

#determines which nodes meet similarity threshold
#returns a list of nodes of ntype
#Also returns a dict including similar node pairs {(n1,n2): [similarity of n1, similarity of n2]}
def similarity_common_neighbors(graph, ntype, threshold, ntype_dict):
    neighbor_dictionary = {}
    nodes = get_nodes(graph, ntype)
    pbar = tqdm.trange(len(nodes))
    pbar.set_description("Computing common neighbors")
    for i in pbar:
        for j in range(i+1, len(nodes)):
            n1_similarity, n2_similarity, per_type_similarity = get_similarity(nodes[i], nodes[j], graph, ntype_dict)
            if n1_similarity >= threshold and n2_similarity >= threshold:  #and (n1_similarity != 1 or n2_similarity != 1):
                node_list = (nodes[i], nodes[j])
                neighbor_dictionary[node_list] = [n1_similarity, n2_similarity]
    return nodes, neighbor_dictionary

def similarity_node2vec(graph, ntype, threshold, options):
    # Compute vectors
    if "dimensions" not in options:
        options["dimensions"] = 64
    if "walk_length" not in options:
        options["walk_length"] = 30
    if "num_walks" not in options:
        options["num_walks"] = 200
    n2v = node2vec.Node2Vec(graph, dimensions=options["dimensions"], walk_length=options["walk_length"], num_walks=options["num_walks"], workers=5)
    model = n2v.fit(window=10, min_count=1, batch_words=4)
    
    nodes = get_nodes(graph, ntype)
    neighbor_dictionary = {}
    pbar = tqdm.tqdm(nodes)
    pbar.set_description("Computing common neighbors")
    for n1 in pbar:
        for n2, similarity in model.wv.most_similar(n1):
            if similarity < threshold:
                break
            if n2 not in nodes:
                continue
            if (n2, n1) not in neighbor_dictionary:
                neighbor_dictionary[(n1, n2)] = similarity 
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



#returns a dictionary {interface pair: {type: proportion of the type within the interface, ...}}
#Goes through all interfaces and finds the proportion of similarity between all the 
#types (vlan, subnet, out_acl, in_acl)
# ntype_list = {"vlan" : 0.5, "acl" : 0.5}
def get_similarity(n1, n2, graph, ntype_list):
    n1_similarity = n2_similarity = 0
    ntype_dictionary = {}
    for ntype in ntype_list:
        n1_proportion, n2_proportion, _ = similarity_proportions(n1, n2, graph, ntype)
        ntype_dictionary[ntype] = n1_proportion, n2_proportion
        weight = ntype_list[ntype]
        n1_similarity += n1_proportion * weight
        #print("n1_similarity:", n1_similarity)
        n2_similarity += n2_proportion * weight
        #print("n2_similarity:", n2_similarity)
    return n1_similarity, n2_similarity, ntype_dictionary


#Calculates precision and recall for common neighbors
def precision_recall(graph, num_remove, similarity_threshold, similarity_options, similarity_function):
    modified_graph, removed_edges = rand_remove(graph, num_remove)
    _, neighbor_dict = similarity_function(modified_graph, "interface", similarity_threshold, similarity_options)
    print("num similar pairs:", len(neighbor_dict))
    pp = pprint.PrettyPrinter(indent=4)
    print("similar nodes:")
    pp.pprint(neighbor_dict)
    print()
    suggested = suggest_links(neighbor_dict, modified_graph) #dictionary
    print("removed edges:")
    pp.pprint(removed_edges)
    print()
    print("suggested links:")
    pp.pprint(suggested)
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
    if sugg_count > 0:
        print("precision:", removed_and_predicted/sugg_count)
    if len(removed_edges) > 0:
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
def rand_remove(graph, num, seed="b"):
    random.seed(seed)
    copy = graph.copy()
    removed_edges = []
    for i in range(num):
        edges = list(copy.edges)
        del_edge = random.choice(edges)
        #print("link", del_edge, "removed")
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

"""Load a graph from a JSON representation"""
def load_graph(graph_path):
    with open(graph_path, 'r') as graph_file:
        graph_json = json.load(graph_file)
    return nx.readwrite.json_graph.node_link_graph(graph_json)

"""Create a simple graph for testing purposes"""
def generate_test_graph():
    graph = nx.Graph()
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

    graph.add_node("in", type="in")
    graph.add_node("outA", type="out")
    graph.add_node("outB", type="out")
    
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
    return graph

def main():
    #Parse command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('graph_path',type=str, 
            help='Path for a file (or directory) containing a JSON representation of graph(s); use "TEST" to generate a test graph instead')
    parser.add_argument('-t', '--threshold',type=float,help='threshold for common neighbor similarity', default = 0.9)
    parser.add_argument('-r', '--remove', type=int, help='number of links to randomly remove', default=20)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', '--common', type=json.loads, nargs="?", 
        help="Use common neighbors when computing node similarity; optionally provide a dictionary of node types (key) and weights (value) to use when computing common neighbors", 
        default={}, const={None : 1})
    group.add_argument('-n', '--node2vec', type=json.loads, nargs="?",
        help="Use node2vec when computing node similarity; optionally provide a dictionary of options",
        default={}, const={"dimensions": 64, "walk_length": 30, "num_walks": 200})
    arguments=parser.parse_args()

    if arguments.graph_path == "TEST":
        graph = generate_test_graph()
    else:
        graph = load_graph(arguments.graph_path)
    '''
    config path: "/shared/configs/uwmadison/2014-10-core/configs_json/r-432nm-b3a-1-core.json"
    keyword path: "/shared/configs/uwmadison/2014-10-core/keywords/r-432nm-b3a-1-core.json"
    '''

    if len(arguments.common) > 0:
        similarity_options = arguments.common
        similarity_function = similarity_common_neighbors
    elif len(arguments.node2vec) > 0:
        similarity_options = arguments.node2vec
        similarity_function = similarity_node2vec

    print(similarity_options)
    print(similarity_function)
    
    #---------------------------------------------------
    precision_recall(graph, arguments.remove, arguments.threshold, similarity_options, similarity_function)
    #---------------------------------------------------
    #nodes, neighbor_dict = common_neighbors(graph, "interface", 0.75)
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

    #from networkx.algorithms.components.connected import connected_components, number_connected_components
    #print("\nComponents in graph: " + str(number_connected_components(graph)))
    #for component in connected_components(graph):
    #print(component)

if __name__ == "__main__":
    main()
