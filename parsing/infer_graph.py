#!/usr/bin/env python3

import argparse
import json
import os
import logging
import networkx
import re
import ipaddress
import queue

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Generate a graph based on inferred symbols and relationships')
    parser.add_argument('infer_dir', help='Path to directory containing symbol and relationship files')
    parser.add_argument('output_dir', help='Path to directory in which to store output')
    parser.add_argument('-p', '--prune', action='store_true')
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

    logging.info(generator.graph)

    if (arguments.prune):
        generator.prune_degree_one()
        logging.info("After pruning: {}".format(generator.graph))

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
        if source_type == "_address":
            source_name = self.generalize_address(source_name)
        if source_parent is not None:
            source_name = source_parent + "_" + source_name

        target_type, target_name, target_parent = target
        if target_type == "_address":
            target_name = self.generalize_address(target_name)
        if target_parent is not None:
            target_name = target_parent + "_" + target_name

        if source_type == "_description" or target_type == "_description":
            # FIXME: infer keywords
            return

        source_node_name = "{}_{}".format(source_type, source_name)
        target_node_name = "{}_{}".format(target_type, target_name)

        self.graph.add_node(source_node_name, type=source_type)
        self.graph.add_node(target_node_name, type=target_type)
        self.graph.add_edge(source_node_name, target_node_name)

    def generalize_address(self, symbol_name):
        # Handle IPv4 address compression
        uncompressed_name = symbol_name
        if (re.match("\d+\.\d+\.\.\d+\.\d+(/d+)?", symbol_name)):
            uncompressed_name = symbol_name.replace("..",".")
        elif (re.match("\d+\.\d+\.\.\d+(/d+)?", symbol_name)):
            uncompressed_name = symbol_name.replace("..",".0.")

        try:
            ip = ipaddress.ip_interface(uncompressed_name)
            logging.debug("Generalized {} to {}".format(symbol_name, ip.network))
            return str(ip.network)
        except:
            return uncompressed_name

    #remove & print nodes of type node_type that only appear once across the network
    #if node_type is None, then prune all nodes of degree one
    def prune_degree_one(self, node_type = None):
        q = queue.Queue(maxsize = 0)
        s = set()
        if node_type is not None:
            nodes = [node for node,attributes in self.graph.nodes(data=True) if attributes["type"] == node_type]
        else:
            nodes = list(self.graph.nodes)
            
        for node in nodes:
            q.put(node)
            s.add(node)

        while not q.empty():
            current_node = q.get() 
            if self.graph.degree(current_node) <= 1:
                neighbors = list(self.graph.neighbors(current_node))
                if len(neighbors) == 1 and neighbors[0] not in s:
                    if (node_type is None) or (self.graph.nodes[neighbors[0]]["type"] == node_type):
                        q.put(neighbors[0])
                        s.add(neighbors[0])
                self.graph.remove_node(current_node)
            s.discard(current_node)
        return

if __name__ == "__main__":
    main()