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
    parser.add_argument('graph_path',type=str, 
            help='Path for a file containing a JSON representation of graph')
    parser.add_argument('image_path',type=str, 
            help='Path for a file in which to store graph drawing')
    arguments=parser.parse_args()

    graph = graph_utils.load_graph(arguments.graph_path)
    pydot_graph = nx.drawing.nx_pydot.to_pydot(graph)
    os.makedirs(os.path.dirname(arguments.image_path), exist_ok=True)
    pydot_graph.write_png(arguments.image_path)

if __name__ == "__main__":
    main()
