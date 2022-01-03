import json
import networkx as nx
import os
import sys
import argparse

# Load code to test
testing_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.dirname(testing_dir))
import generate_graph

aggregated_graph_path = os.path.join(testing_dir, "analysis", "network.json")
graphs_dir = os.path.join(testing_dir, "analysis", "expected", "generate_graph")

def main():
    with open(aggregated_graph_path, 'r') as aggregated_graph_file:
        actual_aggregate = json.load(aggregated_graph_file)
    
    expected_nodes = []
    expected_links = []
    for filename in os.listdir(graphs_dir):
        filepath = os.path.join(graphs_dir, filename)
        print("CURRENT FILEPATH:", filepath)
        with open(filepath, 'r') as file:
            component_json = json.load(file)
        expected_nodes += component_json["nodes"]
        expected_links += component_json["links"]

    for node in actual_aggregate["nodes"]:
        if node not in expected_nodes:
            raise AssertionError(str(node) + " not in expected")
    for node in expected_nodes:
        if node not in actual_aggregate["nodes"]:
            raise AssertionError(str(node) + " not in aggregate")

    for link in actual_aggregate["links"]:
        if link not in expected_links:
            source = link["source"]
            link["source"] = link["target"]
            link["target"] = source
            if link not in expected_links:
                raise AssertionError(str(link) + " not in expected")
    for link in expected_links:
        if link not in actual_aggregate["links"]:
            raise AssertionError(str(link) + " not in aggregate")

if __name__ == "__main__":
    main()