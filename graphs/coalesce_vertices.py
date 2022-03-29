import argparse
import json
import networkx as nx
import pprint
import tqdm
import inspect
import os
import sys

currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 

import analyze

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

def get_nodes(graph, target_type=None):
    """Returns list of all nodes of target_type in graph"""
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

def get_node_type(node, graph):
    # Compute
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

def load_graph(graph_path):
    """Load a graph from a JSON representation"""
    with open(graph_path, 'r') as graph_file:
        graph_json = json.load(graph_file)
    return nx.readwrite.json_graph.node_link_graph(graph_json)

def find_vertices_to_coalesce(graph, target_type, verbose=False):
    coalesce = {}
    vertices = get_nodes(graph, target_type)
    degrees = graph.degree(vertices)
    pbar = tqdm.tqdm(range(len(vertices)))
    pbar.set_description("Finding vertices to coalesce")
    for i in pbar:
        u = vertices[i]

        # Ignore already coalesced vertices
        if u == None:
            continue

        u_degrees = degrees[u]
        u_neighbors = get_neighbors(u, graph)

        # Iterate over all other vertices
        for j in range(i+1, len(vertices)):
            v = vertices[j]

            # Ignore already coalesced vertices
            if v == None:
                continue

            # Vertices must have the same neighbors
            v_degrees = degrees[v]
            if u_degrees != v_degrees:
                continue
            v_neighbors = get_neighbors(v, graph)
            if (u_neighbors != v_neighbors):
                continue

            # Coalesce vertices
            if u not in coalesce:
                coalesce[u] = [u]
            coalesce[u].append(v)
            vertices[j] = None

    return list(coalesce.values())

def update_graph(graph, to_coalesce):
    for vertices in to_coalesce:
        # Add new vertex
        new_name = get_coalesced_name(vertices)
        new_type = get_node_type(vertices[0], graph)
        graph.add_node(new_name, type=new_type)

        # Add same edges as existing vertices
        for edge in graph.edges(vertices[0]):
            graph.add_edge(new_name, edge[1])

        # Remove existing vertices
        for vertex in vertices:
            graph.remove_node(vertex)

def get_coalesced_name(vertices):
    if vertices[0].startswith("Vlan"):
        return get_coalesced_vlan_name(vertices)

def get_coalesced_vlan_name(vlan_vertices):
    nums = [int(v[4:]) for v in vlan_vertices]
    num_ranges = ranges(nums)
    return "Vlan{" + ",".join([str(start) if start == end else "{}-{}".format(start,end) for start,end in num_ranges]) + "}"

def ranges(p):
    # https://stackoverflow.com/questions/4628333/converting-a-list-of-integers-into-range-in-python#answer-4628813
    q = sorted(p)
    i = 0
    for j in range(1,len(q)):
        if q[j] > 1+q[j-1]:
            yield (q[i],q[j-1])
            i = j
    yield (q[i], q[-1])

def process_graph(in_path, out_path, verbose=False):
    print("Current working file: %s" % (in_path))
    graph = load_graph(in_path)

    for vertex_type in ["vlan", "keyword", "interface", "subnet", "acl"]:
        clear_caches()
        to_coalesce = find_vertices_to_coalesce(graph, vertex_type, verbose)
        if (verbose):
            out = pprint.PrettyPrinter(compact=True)
            out.pprint(to_coalesce)

        if len(to_coalesce) > 0:
            update_graph(graph, to_coalesce)
            print("Replaced {} {} vertices with {} vertices".format(sum([len(v) for v in to_coalesce]), vertex_type, len(to_coalesce)))

    # Save graph
    analyze.write_to_outfile(out_path, nx.readwrite.json_graph.node_link_data(graph))

def main():
    #Parse command-line arguments
    parser = argparse.ArgumentParser(description='Coalesce vertices of the same type that have the same neighbors')
    parser.add_argument('graph_path',type=str,help='Path for a file (or directory) containing a JSON representation of the graph(s)')
    parser.add_argument('out_path',type=str,help='Path for a file (or directory) in which to store a JSON representation (and image) of the graph(s)')
    parser.add_argument('-v', '--verbose', action='store_true', help="Display verbose output")
    arguments = parser.parse_args()

    analyze.process_configs(process_graph, arguments.graph_path, arguments.out_path, arguments.verbose)



if __name__ == "__main__":
    main()
