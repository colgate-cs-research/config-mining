import argparse
import json
import networkx as nx
import os

def load_graph(graph_path):
    """Load a graph from a JSON representation"""
    with open(graph_path, 'r') as graph_file:
        graph_json = json.load(graph_file)
    return nx.readwrite.json_graph.node_link_graph(graph_json)

def main():
    #Parse command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('graph_path',type=str, 
            help='Path for a file containing a JSON representation of graph')
    parser.add_argument('image_path',type=str, 
            help='Path for a file in which to store graph drawing')
    arguments=parser.parse_args()

    graph = load_graph(arguments.graph_path)
    pydot_graph = nx.drawing.nx_pydot.to_pydot(graph)
    os.makedirs(os.path.dirname(arguments.image_path), exist_ok=True)
    pydot_graph.write_png(arguments.image_path)

if __name__ == "__main__":
    main()
