import argparse
import json
import networkx as nx
import tqdm

get_nodes_cache = {}
get_neighbors_cache = {}
types_cache = None

all_paths = []
set_paths = []

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


def count_patterns(tuple_of_node_types, last_link_found, pattern_table):
    '''
    1. Stores each sequence of node types found as a pattern
    2. Counts the number of paths found that follow each pattern
    3. Assumes patterns and path counts are stored in a global dictionary
    pattern_table, where the tuple of node types are the keys and the values are
    lists of two numbers. The first number in the lists are the number of *cycles*
    found and the second number is the number of *seqences* of these node types found.
    
    '''
    if pattern_table.get(tuple_of_node_types) != None:
        pattern_table.get(tuple_of_node_types)[1] += 1
        
    else:
        pattern_table[tuple_of_node_types] = [0,1]
    if last_link_found:
        pattern_table.get(tuple_of_node_types)[0] += 1
    return

def find_structural_rel(graph, degrees, node_type, pattern_table, verbose=False):
    """Do neighbors <degrees> degrees away from node X have a direct connection with node X?"""
    ifaces = get_nodes(graph, node_type)
    
    pbar = tqdm.tqdm(ifaces)
    pbar.set_description("Computing paths from interfaces")
    for iface in pbar:
        if (verbose):
            print(iface)
        structural_rel_helper([iface], graph, degrees)

    print("Computed paths")
        
    for path in all_paths:
        start_node = path[0]
        last_node = path[-1]
        types = []
        for node in path:
            if types_cache[node] == "keyword":
                types.append(node)
            else:
                types.append(types_cache[node])
        count_patterns(tuple(types), graph.has_edge(start_node, last_node), pattern_table)
              
    return

def structural_rel_helper(path, graph, max_degree):
    """helper function for find_structural_rel()
    generates lists of paths with <max_degree> number of nodes and
    aggregates all paths into global var (all_paths)"""
    #base case
    if len(path)-1 == max_degree:
        if set(path) not in set_paths:
            all_paths.append(path)
            set_paths.append(set(path))
        return 
    
    #recursive case
    neighbors = get_neighbors(path[-1], graph) #get neighbors of last node in path
    for neighbor in neighbors:
        if neighbor not in path:
            structural_rel_helper(path + [neighbor], graph, max_degree)
    return

def load_graph(graph_path):
    """Load a graph from a JSON representation"""
    with open(graph_path, 'r') as graph_file:
        graph_json = json.load(graph_file)
    return nx.readwrite.json_graph.node_link_graph(graph_json)

def main():
    #Parse command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')

    #required
    parser.add_argument('-d', '--degree', type=int, default=2,
        help='Degrees of separation between nodes')
    parser.add_argument('graph_path',type=str, 
            help='Path for a file containing a JSON representation of graph')
    parser.add_argument('-v', '--verbose', action='store_true', help="Display verbose output")
    arguments=parser.parse_args()

    graph = load_graph(arguments.graph_path)

    pattern_table = {}
    find_structural_rel(graph, arguments.degree, "interface", pattern_table, arguments.verbose)
    for key, val in pattern_table.items():
        if (val[1] > 1) and (val[0]*100/val[1]) > 20:
            print(str(key) + ":" + str(val) + " (" + str(round(val[0]*100/val[1],2)) + "%)")

if __name__ == "__main__":
    main()
