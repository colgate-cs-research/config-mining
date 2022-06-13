import json
import networkx as nx

def load_graph(graph_path):
    """Load a graph from a JSON representation"""
    with open(graph_path, 'r') as graph_file:
        graph_json = json.load(graph_file)
    return nx.readwrite.json_graph.node_link_graph(graph_json)

get_nodes_cache = {}
get_neighbors_cache = {}
types_cache = None

def clear_caches():
    global get_nodes_cache, get_neighbors_cache, types_cache
    get_nodes_cache = {}
    get_neighbors_cache = {}
    types_cache = None

def get_nodes(graph, target_type=None):
    """Returns list of all nodes of target_type in argument graph"""
    # Check if previously computed
    if target_type in get_nodes_cache:
        return get_nodes_cache[target_type]

    # Compute
    global types_cache
    if types_cache is None:
        types_cache = nx.get_node_attributes(graph, "type")
    node_list = []
    for node in graph:
        if target_type is None or types_cache[node] == target_type:
            node_list.append(node)

    # Cache and return result
    get_nodes_cache[target_type] = node_list
    return node_list

def get_type(node, graph):
    """Get a node's type"""
    global types_cache
    if types_cache is None:
        types_cache = nx.get_node_attributes(graph, "type")
    return types_cache[node]

def get_neighbors(node, graph, target_type=None):
    """Get a set of node's neighbors of target_type"""
    # Check if previously computed
    if target_type in get_neighbors_cache and node in get_neighbors_cache[target_type]:
        return get_neighbors_cache[target_type][node]

    # Compute
    global types_cache
    if types_cache is None:
        types_cache = nx.get_node_attributes(graph, "type")
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