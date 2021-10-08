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
    expected = ["acls_aclA", "acls_aclB", "acls_aclC", "acls_aclD",
        "acls_GigabitEthernet0/1", "acls_GigabitEthernet0/2", 
        "acls_GigabitEthernet0/3", "acls_GigabitEthernet0/4", 
        "acls_GigabitEthernet0/5", "acls_GigabitEthernet0/6", 
        "acls_GigabitEthernet0/7", "acls_GigabitEthernet0/8",
        "10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24", "10.0.4.0/24", 
        "10.0.5.0/24", "0.0.0.0/0", "20.0.1.0/24", "20.0.1.128/25",
        "20.0.2.0/24", "20.0.2.1/32", "20.0.3.0/24", "20.0.4.0/24", 
        "20.0.4.1/32", "20.0.5.0/24", "20.0.6.1/32", "20.0.7.0/24", 
        "20.0.8.0/24", "20.0.9.1/32", "20.0.10.1/32", "20.0.11.0/24", 
        "20.0.12.1/32", "20.0.13.1/32", "20.0.14.0/24", "20.0.15.0/24", 
        "20.0.16.0/24", "20.0.17.0/24"]
    actual = link_prediction.get_nodes(graph)
    assert sorted(actual) == sorted(expected)

def test_get_nodes_acls():
    graph = load_graph("acls.json")
    expected = ["acls_aclA", "acls_aclB", "acls_aclC", "acls_aclD"]
    actual = link_prediction.get_nodes(graph, "acl")
    assert sorted(actual) == sorted(expected)

def test_get_nodes_vlans():
    graph = load_graph("vlans.json")
    expected = ["vlans_Vlan100", "vlans_Vlan200", "vlans_Vlan300", "vlans_Vlan400"]
    actual = link_prediction.get_nodes(graph, "vlan")
    assert sorted(actual) == sorted(expected)

def test_get_edges_ge02():
    graph = load_graph("acls.json")
    expected = [("acls_GigabitEthernet0/2", "acls_aclA"), ("acls_GigabitEthernet0/2", "10.0.2.0/24")]
    actual = link_prediction.get_edges("acls_GigabitEthernet0/2", graph)
    assert sorted(actual) == sorted(expected)

def test_get_edges_ge02_acl():
    graph = load_graph("acls.json")
    expected = [("acls_GigabitEthernet0/2", "acls_aclA")]
    actual = link_prediction.get_edges("acls_GigabitEthernet0/2", graph, "acl")
    assert sorted(actual) == sorted(expected)

def test_get_edges_ge01():
    graph = load_graph("vlans.json")
    expected = [("vlans_GigabitEthernet0/1", "vlans_Vlan100"), ("vlans_GigabitEthernet0/1", "vlans_Vlan200"), ("vlans_GigabitEthernet0/1", "vlans_Vlan300")]
    actual = link_prediction.get_edges("vlans_GigabitEthernet0/1", graph)
    assert sorted(actual) == sorted(expected)

def test_get_edges_ge03():
    graph = load_graph("vlans.json")
    expected = [("vlans_GigabitEthernet0/3", "vlans_Vlan100"), ("vlans_GigabitEthernet0/3", "vlans_Vlan200")]
    actual = link_prediction.get_edges("vlans_GigabitEthernet0/3", graph)
    assert sorted(actual) == sorted(expected)

def test_similarity_proportions_all_single():
    graph = load_graph("acls.json")
    actual = link_prediction.similarity_proportions("acls_GigabitEthernet0/3", "acls_GigabitEthernet0/5", graph)
    expected = (1/2, 1/3)
    print(actual[2])
    assert actual[0] == expected[0]
    assert actual[1] == expected[1]

def test_similarity_proportions_all_multiple():
    graph = load_graph("vlans.json")
    actual = link_prediction.similarity_proportions("vlans_GigabitEthernet0/1", "vlans_GigabitEthernet0/3", graph)
    expected = (2/3, 2/2)
    print(actual[2])
    assert actual[0] == expected[0]
    assert actual[1] == expected[1]

def test_similarity_proportions_acls_single():
    graph = load_graph("acls.json")
    actual = link_prediction.similarity_proportions("acls_GigabitEthernet0/3", "acls_GigabitEthernet0/5", graph, "acl")
    expected = (1/1, 1/2)
    print(actual[2])
    assert actual[0] == expected[0]
    assert actual[1] == expected[1]