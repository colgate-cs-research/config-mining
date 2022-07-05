import argparse
import networkx as nx
import os
import sys

graphs_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.dirname(graphs_dir))
import graphs.graph_utils as graph_utils

def main():
    #Parse command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('infer_path',type=str, 
            help='Path for a file containing an inferred graph')
    parser.add_argument('manual_path',type=str, 
            help='Path for a file containing a graph based on hand-written rules')
    arguments=parser.parse_args()

    inferred = graph_utils.load_graph(arguments.infer_path)
    manual = graph_utils.load_graph(arguments.manual_path)

    #manual_types = ["group", "acl", "interface", "unit", "subnet", "vlan", "keyword"]
    manual_types = ["acl", "interface", "subnet", "vlan", "keyword"]
    inferred_nodes = set()
    for typ in manual_types:
        nodes = graph_utils.get_nodes(inferred, typ)
        inferred_nodes.update(nodes)

    
    inferred_subgraph = inferred.subgraph(inferred_nodes)
    print(manual)
    print(inferred_subgraph)
    print(inferred)


if __name__ == "__main__":
    main()
