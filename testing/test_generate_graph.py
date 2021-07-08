#!/usr/bin/env python3

import difflib
import json
import networkx as nx
import os
import sys
import tempfile

from networkx.classes.function import edges

# Load code to test
testing_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.dirname(testing_dir))
import generate_graph
import extract_keywords

configs_dir = os.path.join(testing_dir, "analysis", "configs_json")
graphs_dir = os.path.join(testing_dir, "analysis", "expected", "generate_graph")

def helper_test_graph(filename):
    config_path = os.path.join(configs_dir, filename) 
    tmp_dir = tempfile.mkdtemp()
    keyword_path = os.path.join(tmp_dir, filename)
    extract_keywords.analyze_configuration(config_path, keyword_path, None)
    actual = generate_graph.generate_graph(config_path, keyword_path)
    graph_path = os.path.join(graphs_dir, filename)
    with open(graph_path, 'r') as graph_file:
        graph_json = json.load(graph_file)
    expected = nx.readwrite.json_graph.node_link_graph(graph_json)
    assert actual.nodes == expected.nodes
    assert actual.edges == expected.edges

def test_graph_acls():
    helper_test_graph("acls.json")

def test_graph_keywords():
    helper_test_graph("keywords.json")

def test_graph_vlans():
    helper_test_graph("vlans.json")