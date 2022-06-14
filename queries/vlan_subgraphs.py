import argparse
import networkx as nx
import os
import sys
import tqdm

queries_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.dirname(queries_dir))
import graphs.graph_utils as graph_utils

def analyze_subgraphs(graph):
    share_I = {}
    share_IK = {}
    common_neighbor_types = {}

    # Iterate over all interfaces
    interfaces = graph_utils.get_nodes(graph, "interface")
    pbar = tqdm.tqdm(interfaces)
    pbar.set_description("Computing VLAN pair subgraphs")
    for interface in pbar:
        vlans = list(graph_utils.get_neighbors(interface, graph, "vlan"))

        # Iterate over all VLAN pairs
        for i in range(len(vlans)):
            for j in range(i+1, len(vlans)):
                v1 = vlans[i]
                v2 = vlans[j]
                pair = tuple(sorted([v1, v2]))
                if (pair not in share_I):
                    share_I[pair] = set()
                share_I[pair].add(interface)

                # Identify common keywords
                k1 = graph_utils.get_neighbors(v1, graph, "keyword")
                k2 = graph_utils.get_neighbors(v2, graph, "keyword")
                common_keywords = k1.intersection(k2)
                if common_keywords:
                    if pair not in share_IK:
                      share_IK[pair] = set()
                    share_IK[pair].add(interface)

                """
                # Identify public/private
                public_private = False
                if ("public" in k1 and "private" in k2) or ("private" in k1 and "public" in k2):
                    public_private = True
                    share_I_pubpriv.add(pair)
                    share_i_pubpriv.add(triple)

                if common_keywords and public_private:
                    multi_keyword_subgraphs.append(triple)
                """

                # Identify other commonalities
                n1 = graph_utils.get_neighbors(v1, graph)
                n2 = graph_utils.get_neighbors(v2, graph)
                common_neighbors = n1.intersection(n2)
                common_types = set([graph_utils.get_type(n, graph) for n in common_neighbors])
                for typ in common_types:
                    if typ not in common_neighbor_types:
                        common_neighbor_types[typ] = set()
                    common_neighbor_types[typ].add(pair)

    print(len(share_I.keys()), "subgraphs of", """
     V:v1
     /
    I
     \\
     V:v2""")
    
    share_I_distrib = {}
    for interfaces in share_I.values():
        if len(interfaces) not in share_I_distrib:
            share_I_distrib[len(interfaces)] = 0
        share_I_distrib[len(interfaces)] += 1
    print(share_I_distrib)

    print(str(len(share_IK)), "subgraphs of", """
     V:v1
     / \\
    I  K
     \\ /
     V:v2""")
    
    for pair in share_IK.keys():
      print(pair)
    
    for key,value in common_neighbor_types.items():
        print(len(value), "VLAN pairs with common", key)


def analyze_vlan_pairs(graph):
    common_neighbor_types = {}

    # Iterate over all vlan pairs
    vlans = list(sorted(graph_utils.get_nodes(graph, "vlan")))
    pbar = tqdm.tqdm(range(len(vlans)))
    pbar.set_description("Analyzing VLAN pairs")
    for i in pbar:
        for j in range(i+1, len(vlans)):
            v1 = vlans[i]
            v2 = vlans[j]
            pair = (v1, v2)

            # Identify commonalities
            n1 = graph_utils.get_neighbors(v1, graph)
            n2 = graph_utils.get_neighbors(v2, graph)
            common_neighbors = n1.intersection(n2)
            common_types = set([graph_utils.get_type(n, graph) for n in common_neighbors])
            for typ in common_types:
                if typ not in common_neighbor_types:
                    common_neighbor_types[typ] = set()
                common_neighbor_types[typ].add(pair)
   
    for key,value in common_neighbor_types.items():
        print(len(value), "VLAN pairs with common", key)

    print("Keyword in common")
    keyword_pairs = common_neighbor_types["keyword"]
    interface_pairs = common_neighbor_types["interface"]
    keyword_and_interface_pairs = keyword_pairs.intersection(interface_pairs)
    keyword_only_pairs = keyword_pairs.difference(interface_pairs)
    print(len(keyword_and_interface_pairs), "VLAN pairs with common interface AND keyword")
    for pair in keyword_and_interface_pairs:
      k1 = set(sorted(graph_utils.get_neighbors(pair[0], graph, "keyword")))
      k2 = set(sorted(graph_utils.get_neighbors(pair[1], graph, "keyword")))
      print(pair, k1.intersection(k2), k1, k2)
    print(len(keyword_only_pairs), "VLAN pairs with common keyword only")
    for pair in keyword_only_pairs:
      k1 = set(sorted(graph_utils.get_neighbors(pair[0], graph, "keyword")))
      k2 = set(sorted(graph_utils.get_neighbors(pair[1], graph, "keyword")))
      print(pair, k1.intersection(k2), k1, k2)

#    for vlan in ('Vlan995', 'Vlan2010', 'Vlan3244', 'Vlan300', 'Vlan1053', 'Vlan994'):
#      print(vlan, graph_utils.get_neighbors(vlan, graph, "keyword"))


def vlan_distance(graph):
    print("VlanX,VlanY,Common,Distance,Diff")
    # Iterate over all VLAN pairs
    vlans = graph_utils.get_nodes(graph, "vlan")
    for i in range(len(vlans)):
        for j in range(i+1, len(vlans)):
            v1 = vlans[i]
            v2 = vlans[j]

            # Identify common interfraces
            ifaces1 = graph_utils.get_neighbors(v1, graph, "interface")
            ifaces2 = graph_utils.get_neighbors(v2, graph, "interface")
            total_ifaces = ifaces1.union(ifaces2)
            common_ifaces = ifaces1.intersection(ifaces2)
            diff_ifaces = total_ifaces.difference(common_ifaces)
            print(",".join([str(v1),str(v2),str(len(common_ifaces)),str(len(total_ifaces)-len(common_ifaces))," ".join(diff_ifaces)]))

def keyword_neighbors(graph):
    keywords = graph_utils.get_nodes(graph, "keyword")
    neighbor_types = {}
    for keyword in keywords:
        neighbors = graph_utils.get_neighbors(keyword, graph)
        for neighbor in neighbors:
            neighbor_type = graph_utils.get_type(neighbor, graph)
            if neighbor_type not in neighbor_types:
                neighbor_types[neighbor_type] = 0
            neighbor_types[neighbor_type] += 1
    print(neighbor_types)
        

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Analyze subgraphs involving VLANs')
    parser.add_argument('graph_path',type=str, 
            help='Path for a file containing a JSON representation of graph')
    arguments = parser.parse_args()

    graph = graph_utils.load_graph(arguments.graph_path)
#    analyze_subgraphs(graph)
#    analyze_vlan_pairs(graph)
#    vlan_distance(graph)
    keyword_neighbors(graph)
    

if __name__ == "__main__":
    main()
