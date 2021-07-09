#!/usr/bin/env python3

import json
import networkx as nx
import os
import sys

# Load code to test
testing_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.dirname(testing_dir))
import link_prediction

def load_graph(filename):
    # Flush caches
    link_prediction.clear_caches()

    graphs_path = os.path.join(testing_dir, "analysis", "expected", "generate_graph", filename)
    with open(graphs_path, 'r') as graph_file:
        graph_json = json.load(graph_file)
    return nx.readwrite.json_graph.node_link_graph(graph_json)

def test_get_nodes_all():
    graph = load_graph("acls.json")
    expected = ["aclA", "aclB", "aclC", "aclD",
        "GigabitEthernet0/1", "GigabitEthernet0/2", "GigabitEthernet0/3", "GigabitEthernet0/4", 
        "GigabitEthernet0/5", "GigabitEthernet0/6", "GigabitEthernet0/7", "GigabitEthernet0/8",
        "10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24", "10.0.4.0/24", "10.0.5.0/24", 
        "20.0.2.0/24", "20.0.3.0/24", "20.0.4.0/24"]
    actual = link_prediction.get_nodes(graph)
    assert sorted(actual) == sorted(expected)

def test_get_nodes_acls():
    graph = load_graph("acls.json")
    expected = ["aclA", "aclB", "aclC", "aclD"]
    actual = link_prediction.get_nodes(graph, "acl")
    assert sorted(actual) == sorted(expected)

def test_get_nodes_vlans():
    graph = load_graph("vlans.json")
    expected = ["Vlan100", "Vlan200", "Vlan300", "Vlan400"]
    actual = link_prediction.get_nodes(graph, "vlan")
    assert sorted(actual) == sorted(expected)

def test_get_edges_ge02():
    graph = load_graph("acls.json")
    expected = [("GigabitEthernet0/2", "aclA"), ("GigabitEthernet0/2", "10.0.2.0/24")]
    actual = link_prediction.get_edges("GigabitEthernet0/2", graph)
    assert sorted(actual) == sorted(expected)

def test_get_edges_ge02_acl():
    graph = load_graph("acls.json")
    expected = [("GigabitEthernet0/2", "aclA")]
    actual = link_prediction.get_edges("GigabitEthernet0/2", graph, "acl")
    assert sorted(actual) == sorted(expected)

def test_get_edges_ge01():
    graph = load_graph("vlans.json")
    expected = [("GigabitEthernet0/1", "Vlan100"), ("GigabitEthernet0/1", "Vlan200"), ("GigabitEthernet0/1", "Vlan300")]
    actual = link_prediction.get_edges("GigabitEthernet0/1", graph)
    assert sorted(actual) == sorted(expected)

def test_get_edges_ge03():
    graph = load_graph("vlans.json")
    expected = [("GigabitEthernet0/3", "Vlan100"), ("GigabitEthernet0/3", "Vlan200")]
    actual = link_prediction.get_edges("GigabitEthernet0/3", graph)
    assert sorted(actual) == sorted(expected)

def test_similarity_proportions_all_single():
    graph = load_graph("acls.json")
    actual = link_prediction.similarity_proportions("GigabitEthernet0/3", "GigabitEthernet0/5", graph)
    expected = (1/2, 1/3)
    print(actual[2])
    assert actual[0] == expected[0]
    assert actual[1] == expected[1]

def test_similarity_proportions_all_multiple():
    graph = load_graph("vlans.json")
    actual = link_prediction.similarity_proportions("GigabitEthernet0/1", "GigabitEthernet0/3", graph)
    expected = (2/3, 2/2)
    print(actual[2])
    assert actual[0] == expected[0]
    assert actual[1] == expected[1]

def test_similarity_proportions_acls_single():
    graph = load_graph("acls.json")
    actual = link_prediction.similarity_proportions("GigabitEthernet0/3", "GigabitEthernet0/5", graph, "acl")
    expected = (1/1, 1/2)
    print(actual[2])
    assert actual[0] == expected[0]
    assert actual[1] == expected[1]