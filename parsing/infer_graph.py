#!/usr/bin/env python3

import argparse
import json
import os
import logging
import networkx

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Generate a graph based on inferred symbols and relationships')
    parser.add_argument('infer_dir', help='Path to directory containing symbol and relationship files')
    parser.add_argument('output_dir', help='Path to directory in which to store output')
    parser.add_argument('-v', '--verbose', action='count', help="Display verbose output", default=0)
    arguments = parser.parse_args()

    # module-wide logging
    if (arguments.verbose == 0):
        logging.basicConfig(level=logging.WARNING)
    elif (arguments.verbose == 1):
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)
    logging.getLogger(__name__)

    # Load inference results
    with open(os.path.join(arguments.infer_dir, "symbols.json"), 'r') as symbols_file:
        symbol_table = json.load(symbols_file)
    with open(os.path.join(arguments.infer_dir, "relationships.json"), 'r') as relationships_file:
        relationships = json.load(relationships_file)

    generator = GraphGenerator(symbol_table, relationships)

    # Create output directory
    os.makedirs(arguments.output_dir, exist_ok=True)

    with open(os.path.join(arguments.output_dir, "graph.json"), 'w') as graph_file:
        json.dump(networkx.readwrite.json_graph.node_link_data(generator.graph), 
                graph_file, indent=4, sort_keys=True)

class GraphGenerator:
    def __init__(self, symbol_table, relationships):
        self.symbol_table = symbol_table
        self.relationships = relationships
        self.graph = networkx.Graph()

        for edge in relationships:
            self.add_edge(edge)

    def add_edge(self, edge):
        source, target = edge

        source_type, source_name, source_parent = source
        if source_parent is not None:
            source_name = source_parent + "_" + source_name

        target_type, target_name, target_parent = target
        if target_parent is not None:
            target_name = target_parent + "_" + target_name

        source_node_name = "{}_{}".format(source_type, source_name)
        target_node_name = "{}_{}".format(target_type, target_name)

        self.graph.add_node(source_node_name, type=source_type)
        self.graph.add_node(target_node_name, type=target_type)
        self.graph.add_edge(source_node_name, target_node_name)

if __name__ == "__main__":
    main()