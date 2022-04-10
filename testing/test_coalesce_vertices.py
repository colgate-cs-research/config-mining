#!/usr/bin/env python3

import json
import networkx as nx
import os
import sys
import tempfile

# Load code to test
testing_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.dirname(testing_dir))
import graphs.coalesce_vertices as coalesce_vertices

graphs_dir = os.path.join(testing_dir, "graphs", "graphs")
expected_dir = os.path.join(testing_dir, "graphs", "expected", "coalesce_vertices")



def helper_compare_graphs(actual, expected):
    try:
        assert actual.nodes == expected.nodes
    except AssertionError as assert_error:
        for node in actual.nodes:
            if node not in expected.nodes:
                raise AssertionError(str(node) + " not in expected")
        for node in expected.nodes:
            if node not in actual.nodes:
                raise AssertionError(str(node) + " not in actual")
    try:
        assert actual.edges == expected.edges
    except AssertionError as assert_error:
        for edge in actual.edges:
            if edge not in expected.edges:
                raise AssertionError(str(edge) + " not in expected")
        for edge in expected.edges:
            if edge not in actual.edges:
                raise AssertionError(str(edge) + " not in actual") 

def test_find_vertices_to_coalesce():
    graph_path = os.path.join(graphs_dir, "common_vlans.json")
    with open(graph_path, 'r') as graph_file:
        graph_json = json.load(graph_file)
    graph = nx.readwrite.json_graph.node_link_graph(graph_json)
    coalesce = coalesce_vertices.find_vertices_to_coalesce(graph, "vlan")
    expected = [["Vlan100","Vlan200"],["Vlan400","Vlan401","Vlan405"]]
    assert(coalesce == expected)

def test_update_graph():
    graph_path = os.path.join(graphs_dir, "common_vlans.json")
    with open(graph_path, 'r') as graph_file:
        graph_json = json.load(graph_file)
    actual = nx.readwrite.json_graph.node_link_graph(graph_json)
    to_coalesce = [["Vlan100","Vlan200"],["Vlan400","Vlan401","Vlan405"]]
    coalesce_vertices.update_graph(actual, to_coalesce)

    expected_path = os.path.join(expected_dir, "common_vlans.json")
    with open(expected_path, 'r') as expected_file:
        expected_json = json.load(expected_file)
    expected = nx.readwrite.json_graph.node_link_graph(expected_json)
    helper_compare_graphs(actual, expected)