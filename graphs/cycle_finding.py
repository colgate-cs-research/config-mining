import argparse
import json
import networkx as nx
import tqdm
import concurrent.futures

get_nodes_cache = {}
get_neighbors_cache = {}
types_cache = None

#set_paths = []

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


def count_patterns(tuple_of_node_types, last_link_found, pattern_table, path):
    '''
    1. Stores each sequence of node types found as a pattern
    2. Counts the number of paths found that follow each pattern
    3. Assumes patterns and path counts are stored in a global dictionary
    pattern_table, where the tuple of node types are the keys and the values are
    lists of two numbers. The first number in the lists are the number of *cycles*
    found and the second number is the number of *seqences* of these node types found.
    
    '''
    if pattern_table.get(tuple_of_node_types) is None:
        if path is None:
            pattern_table[tuple_of_node_types] = [0,0]
        else:
            pattern_table[tuple_of_node_types] = [[],[]]

    if last_link_found:
        if path is None:
            pattern_table.get(tuple_of_node_types)[0] += 1
        else:
            pattern_table.get(tuple_of_node_types)[0].append(path)
    else:
        if path is None:
            pattern_table.get(tuple_of_node_types)[1] += 1
        else:
            pattern_table.get(tuple_of_node_types)[1].append(path)
    return

def merge_table(pattern_table, patterns):
    for key, val in patterns.items():
        if key not in pattern_table:
            pattern_table[key] = val
        else:
            curr = pattern_table[key]
            if isinstance(curr[0], list):
                curr[0].extend(val[0])
                curr[1].extend(val[1])
            else:
                curr[0] += val[0]
                curr[1] += val[1]

def find_structural_rel(graph, degrees, node_type, pattern_table, verbose=False):
    """Do neighbors <degrees> degrees away from node X have a direct connection with node X?"""
    nodes = get_nodes(graph, node_type)
    
#    all_paths = []
    pbar = tqdm.tqdm(total=len(nodes))
    pbar.set_description("Computing paths from {}s".format(node_type))
    with concurrent.futures.ProcessPoolExecutor() as executor:
        future_to_node = {executor.submit(compute_paths_start, node, graph, degrees, verbose) : node for node in nodes}
        for future in concurrent.futures.as_completed(future_to_node):
            try:
                patterns = future.result()
                merge_table(pattern_table, patterns)
                #paths = future.result()
                #all_paths.extend(paths)
                #if (verbose):
                #    print("\tComputed paths starting from {}".format(future_to_node[future]))
                pbar.update()
            except Exception as ex:
                print("\tFailed to compute paths starting from {}".format(future_to_node[future]))
    pbar.close()

#    pbar = tqdm.tqdm(all_paths)
#    pbar.set_description("Processing paths") 
#    for path in pbar:
#        count_path(path, graph, pattern_table, verbose)
              
    return

def count_path(path, graph, pattern_table, verbose=False):
    start_node = path[0]
    last_node = path[-1]
    types = []
    for node in path:
        if types_cache[node] == "keyword": #or types_cache[node] == "acl":
            types.append(node)
        else:
            types.append(types_cache[node])
    count_patterns(tuple(types), graph.has_edge(start_node, last_node), pattern_table, (path if verbose else None))

def compute_paths_start(node, graph, max_degree, verbose=False):
    #all_paths = []
    pattern_table = {}
    structural_rel_helper([node], graph, max_degree, pattern_table, verbose) #all_paths)
    return pattern_table
#    return all_paths

def structural_rel_helper(path, graph, max_degree, pattern_table, verbose=False): #all_paths):
    """helper function for find_structural_rel()
    generates lists of paths with <max_degree> number of nodes and
    aggregates all paths into global var (all_paths)"""
    #base case
    if len(path)-1 == max_degree:
        count_path(path, graph, pattern_table, verbose)
#        all_paths.append(path)
#        if set(path) not in set_paths:
#            set_paths.append(set(path))
        return 
    
    #recursive case
    neighbors = get_neighbors(path[-1], graph) #get neighbors of last node in path
    for neighbor in neighbors:
        if neighbor not in path:
            structural_rel_helper(path + [neighbor], graph, max_degree, pattern_table, verbose) #all_paths)
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
    parser.add_argument('output_path',type=str, 
            help='Path for a file in which to store the pattern table')
    parser.add_argument('-s', '--starting', type=str, default="interface",
        help='Type of starting node')
    parser.add_argument('-t', '--threshold', type=int, default=0.01,
        help="Miniminum precentage of paths that must have a cycle")
    parser.add_argument('-v', '--verbose', action='store_true', help="Display verbose output")
    arguments=parser.parse_args()

    graph = load_graph(arguments.graph_path)

    pattern_table = {}
    find_structural_rel(graph, arguments.degree, arguments.starting, pattern_table, arguments.verbose)
    with open(arguments.output_path, 'w') as outfile:
        for key, val in pattern_table.items():
            if isinstance(val[0], list):
                cycles = len(val[0])
                notcycles = len(val[1])
            else:
                cycles = val[0]
                notcycles = val[1]
            total = cycles + notcycles
            percentage = cycles*100/total
            if (percentage > arguments.threshold):
                path = " ".join([s.replace(',','_') for s in key])
                row = "{},{},{},{}".format(path, cycles, total, round(percentage, 2))
                outfile.write(row+"\n")

                if (arguments.verbose):
                    print(row)
                    for cycle in val[0]:
                        print("\tCycle\t{}".format(cycle))
                    for path in val[1]:
                        print("\tNo\t{}".format(path))



if __name__ == "__main__":
    main()