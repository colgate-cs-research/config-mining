import argparse
import json
import networkx as nx
from networkx.classes.function import non_edges
import node2vec
import pprint
import random
import tqdm

get_nodes_cache = {}
get_edges_cache = {}
get_neighbors_cache = {}
types_cache = None

def clear_caches():
    global get_nodes_cache, get_edges_cache, get_neighbors_cache, types_cache
    get_nodes_cache = {}
    get_edges_cache = {}
    get_neighbors_cache = {}
    types_cache = None

#returns list of all nodes of target_type in argument graph
def get_nodes(graph, target_type=None):
    # Check if previously computed
    if target_type in get_nodes_cache:
        return get_nodes_cache[target_type]

    # Compute
    node_list = []
    for node in graph:
        if target_type is None or types_cache[node] == target_type:
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
    edge_list = []
    for edge in graph.edges(node):
        if target_type is None or types_cache[edge[1]] == target_type:
            edge_list.append(edge)

    # Cache and return result
    if target_type not in get_edges_cache:
        get_edges_cache[target_type] = {}
    get_edges_cache[target_type][node] = edge_list
    return edge_list

"""
Get a set of of node's neighbors of target_type
"""
def get_neighbors(node, graph, target_type=None):
    # Check if previously computed
    if target_type in get_neighbors_cache and node in get_neighbors_cache[target_type]:
        return get_neighbors_cache[target_type][node]

    # Compute
    all_neighbors = nx.neighbors(graph, node)
    if target_type is None:
        neighbor_list = set(all_neighbors)
    else:
        neighbor_list = set()
        for neighbor in all_neighbors:
            if types_cache[neighbor] == target_type:
                neighbor_list.add(neighbor)

    # Cache and return result
    if target_type not in get_neighbors_cache:
        get_neighbors_cache[target_type] = {}
    get_neighbors_cache[target_type][node] = neighbor_list
    return neighbor_list

"""
Get a list of all common neighbors of target_type for pair of nodes
"""
def get_common_neighbors(node1, node2, graph, target_type=None):
    # Compute common neighbors
    all_neighbors = nx.common_neighbors(graph, node1, node2)
    if target_type is None:
        return all_neighbors

    # Filter neighbors by type (if necessary)
    filtered_neighbors = []
    for neighbor in all_neighbors:
        if types_cache[neighbor] == target_type:
            filtered_neighbors.append(neighbor)
    return filtered_neighbors

#returns two floats indicating similarity of nodes' neighbors of ntype
def similarity_proportions(n1, n2, graph, ntype=None):
    n1_neighbors = get_neighbors(n1, graph, ntype)
    n2_neighbors = get_neighbors(n2, graph, ntype)
    total1 = len(n1_neighbors)
    total2 = len(n2_neighbors)
    matches = n1_neighbors.intersection(n2_neighbors)

    n1_similarity, n2_similarity = 0, 0
    if total1 > 0:
        n1_similarity = len(matches)/total1
    if total2 > 0:
        n2_similarity = len(matches)/total2

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
            if n1_similarity >= threshold and n2_similarity >= threshold and (n1_similarity != 1 or n2_similarity != 1):
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


#return dict containing the different neighboring nodes between
#larger (more neighbors) and smaller (fewer neighbors) argument nodes in graph
#ex return val: {"node1", "node2"}
def get_node_diff_between(larger, smaller, graph):
    larger_copy = nx.Graph()
    smaller_copy = nx.Graph()
    for edge in graph.edges(larger):
        larger_copy.add_node(edge[1])
    for edge in graph.edges(smaller):
        smaller_copy.add_node(edge[1])
    return larger_copy.nodes() - smaller_copy.nodes() 

#suggests links for common neighbors in graph
#return dict {node: {suggested neighbors}}
def suggest_links(neighbor_dictionary, graph):
    larger_copy = nx.Graph()
    smaller_copy = nx.Graph()
    sugg_dict = {}
    for pair, similarity in neighbor_dictionary.items():
        #same size
        if len(graph.edges(pair[0])) == len(graph.edges(pair[1])):
            sugg_dict[pair[0]] = get_node_diff_between(pair[1], pair[0], graph)
            sugg_dict[pair[1]] = get_node_diff_between(pair[0], pair[1], graph)
        else:
            if len(graph.edges(pair[0])) > len(graph.edges(pair[1])):
                larger = pair[0]
                smaller = pair[1]
            else: #len(graph.edges(pair[0])) < len(graph.edges(pair[1]))
                larger = pair[1]
                smaller = pair[0]
            sugg_dict[smaller] = get_node_diff_between(larger, smaller, graph)
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
        n2_similarity += n2_proportion * weight
    return n1_similarity, n2_similarity, ntype_dictionary


#takes argument dict {node: {suggested neighbors}} which suggests links for similar nodes
#returns ranked list of suggestions {int representing # of connections to ifaces: [link suggestions]} (higher key = higher priority suggestion)
def rank_suggestions_for_node(suggested_links, graph, node_type):
    ranked_suggestions = {}
    for suggestion in suggested_links:
        count = len(get_neighbors(suggestion, graph, node_type)) #returns a list of each pairing in a tuple 
        if count not in ranked_suggestions:
            ranked_suggestions[count] = [suggestion]
        else:
            ranked_suggestions[count].append(suggestion)
    return ranked_suggestions

def rank_suggestions(suggested_links, graph, node_type):
    for iface in suggested_links:
        suggested_links[iface] = rank_suggestions_for_node(suggested_links[iface], graph, node_type)
    return
    
#returns ranked list of top num suggestions in ranked_suggestions dict
def get_top_suggestions_for_node(ranked_suggestions, num):
    s_count = 0
    top_suggestions = []
    keys = sorted(ranked_suggestions.keys())
    while len(keys) > 0 and (num == 0 or s_count < num):
        highest_key = keys.pop()
        suggestions_list = ranked_suggestions[highest_key]
        for suggestion in suggestions_list:
            if (num > 0 and s_count >= num):
                break
            top_suggestions.append(suggestion)
            s_count += 1
    return top_suggestions

def get_top_suggestions(ranked_suggestions, num):
    top_suggestions = {}
    for node, suggestions in ranked_suggestions.items():
        top_suggestions[node] = get_top_suggestions_for_node(suggestions, num)
    return top_suggestions

#Calculates precision and recall for common neighbors
def precision_recall(graph, num_remove, similarity_threshold, similarity_options, similarity_function, num_suggs, node_type):
    pp = pprint.PrettyPrinter(indent=4)
    modified_graph, removed_edges = rand_remove(graph, num_remove, node_type)
    print("removed edges:")
    pp.pprint(removed_edges)
    print()
    _, neighbor_dict = similarity_function(modified_graph, node_type, similarity_threshold, similarity_options) #change back to modified_graph
    print("num similar pairs:", len(neighbor_dict))
    print("similar nodes:")
    pp.pprint(neighbor_dict)
    print()
    suggested = suggest_links(neighbor_dict, modified_graph)
    #suggested = suggest_links(neighbor_dict, modified_graph) #dictionary
    print("suggested links:")
    pp.pprint(suggested)
    print()
    rank_suggestions(suggested, modified_graph, node_type)
    print("ranked suggested links:")
    pp.pprint(suggested)
    print()
    top_suggestions = get_top_suggestions(suggested, num_suggs)
    print("top suggested links:")
    pp.pprint(top_suggestions)
    print()
    '''
    print("TOP", num_suggs, "link suggestions:")
    for suggestion in top_suggestions:
        print(suggestion)
    '''
    removed_and_predicted = 0
    #calculates number of removed edges that were predicted
    sugg_count = 0
    for node, values in top_suggestions.items():
        for value in values:
            sugg_count += 1
            if (node, value) in removed_edges:
                removed_and_predicted += 1
    if sugg_count > 0:
        print("precision:", removed_and_predicted/sugg_count)
    else:
        print("precision: 0.0")
    if len(removed_edges) > 0:
        print("recall:", removed_and_predicted/len(removed_edges))
    else:
        print("recall: 0.0")
    print()

#returns a copy of argument graph with num randomly removed links (always connected to an iface)
#also draws original and modified graphs to separate png files
def rand_remove(graph, num, node_type, seed="b"):
    random.seed(seed)
    copy = graph.copy()
    removed_edges = []

    #get all interface edges in graph
    nodetype_edges = []
    nodetype_nodes = get_nodes(graph, node_type)
    for node in nodetype_nodes:
        nodetype_edges += get_edges(node, graph)

    for i in range(num):
        del_edge = random.choice(nodetype_edges)
        nodetype_edges.remove(del_edge)
        removed_edges.append(del_edge)
        copy.remove_edge(del_edge[0], del_edge[1])

    '''
    #draw graphs in png files
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
    graph.add_node("E", type="interface")
    graph.add_node("F", type="interface")

    graph.add_node("v1", type="vlan")
    graph.add_node("v2", type="vlan")
    graph.add_node("v3", type="vlan")
    graph.add_node("v4", type="vlan")
    graph.add_node("v5", type="vlan")
    graph.add_node("v6", type="vlan")
    graph.add_node("v7", type="vlan")
    graph.add_node("celeb", type="vlan")
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
    graph.add_edge("B", "celeb")

    #C
    graph.add_edge("C", "v3")
    graph.add_edge("C", "v4")
    graph.add_edge("C", "v5")

    graph.add_edge("C","celeb")

    #D
    graph.add_edge("D", "v5")
    graph.add_edge("D", "v6")
    graph.add_edge("D", "v7")

    graph.add_edge("D", "v4")
    graph.add_edge("celeb", "E")
    graph.add_edge("celeb", "F")

    og_graph = nx.drawing.nx_pydot.to_pydot(graph)
    og_graph.write_png('original.png')
    return graph

def main():
    #Parse command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')

    #required
    parser.add_argument('graph_path',type=str, 
            help='Path for a file (or directory) containing a JSON representation of graph(s); use "TEST" to generate a test graph instead')
    #optional
    parser.add_argument('-t', '--threshold',type=float,help='threshold for common neighbor similarity', default = 0.9)
    parser.add_argument('-r', '--remove', type=int, help='number of links to randomly remove', default=20)
    parser.add_argument('-s', '--suggest', type=int, help='number of links to suggest', default=0)
    parser.add_argument('-y', '--nodetype', choices=['interface', 'vlan', 'acl', 'keyword'], default='interface')
  
    #choose one
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

    global types_cache
    types_cache = nx.get_node_attributes(graph, "type")
    '''
    config path: "/shared/configs/uwmadison/2014-10-core/configs_json/r-432nm-b3a-1-core.json"
    keyword path: "/shared/configs/uwmadison/2014-10-core/keywords/r-432nm-b3a-1-core.json"
    '''

    if len(arguments.common) > 0:
        similarity_options = arguments.common
        if "none" in similarity_options:
            similarity_options[None] = similarity_options["none"]
            del similarity_options["none"]
        similarity_function = similarity_common_neighbors
    elif len(arguments.node2vec) > 0:
        similarity_options = arguments.node2vec
        similarity_function = similarity_node2vec

    #print(similarity_options)
    #print(similarity_function) similarity_common_neighbors
    
    #---------------------------------------------------
    precision_recall(graph, arguments.remove, arguments.threshold, similarity_options, similarity_function, arguments.suggest, arguments.nodetype) #add arguments.nodetype
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
