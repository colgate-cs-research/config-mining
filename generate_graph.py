import analyze
import argparse
import ipaddress
import json
import networkx as nx
import re

def main():
    #Parse command-line arguments
    parser = argparse.ArgumentParser(description='Generate a graph')
    parser.add_argument('config_path',type=str, help='Path for a file (or directory) containing a JSON representation of configuration(s)')
    parser.add_argument('keyword_path',type=str,help='Path for a file (or directory) containing a JSON representation of keywords from config(s)')
    parser.add_argument('out_path',type=str,help='Path for a file (or directory) in which to store a JSON representation (and image) of the graph(s)')
    parser.add_argument('-i', '--images', action='store_true', default=False)
    arguments = parser.parse_args()

    analyze.process_configs(analyze_configuration, [arguments.config_path, arguments.keyword_path], arguments.out_path, arguments.images)

def analyze_configuration(in_paths, out_path=None, generate_image=False):
    print("Current working files: %s" % (in_paths))
    config_path, keyword_path = in_paths
    config = load_config(config_path)
    graph = make_graph(config)
    add_keywords(keyword_path, graph)

    # Save graph
    if out_path is not None:
        # Save graph
        analyze.write_to_outfile(out_path, nx.readwrite.json_graph.node_link_data(graph))

        # Save image
        if generate_image:
            pydot_graph = nx.drawing.nx_pydot.to_pydot(graph)
            pydot_graph.write_png(out_path.replace(".json", ".png"))
    
    return graph

def generate_graph(config_path, keyword_path):
    return analyze_configuration([config_path, keyword_path])

def load_config(file):
    # Load config
    with open(file, "r") as infile:
        config = json.load(infile)
    return config

#constructs graph based on argument config file
def make_graph(config):
    graph = nx.Graph()
    for acl in config["acls"]:
        graph.add_node(acl, type= "acl")
        #print(graph.nodes[acl])

    regex = re.compile(r'Vlan\d+')
    for interface in config["interfaces"]:
        if regex.match(interface):
            graph.add_node(interface, type="vlan")
        else:    
            graph.add_node(interface, type="interface")
        
        if config["interfaces"][interface]["address"] is not None:
            address = config["interfaces"][interface]["address"]
            network_obj = ipaddress.IPv4Interface(address)
            graph.add_node(str(network_obj.network), type="subnet")
            graph.add_edge(interface, str(network_obj.network))

        #added create node line (undefined allowed vlans???????)
        if config["interfaces"][interface]["allowed_vlans"] is not None:
            for vlan in config["interfaces"][interface]["allowed_vlans"]:
                graph.add_node( "Vlan" + str(vlan), type="vlan")
                graph.add_edge(interface, "Vlan" + str(vlan), type="allowed")

        if config["interfaces"][interface]["in_acl"] is not None:
            graph.add_edge(interface, config["interfaces"][interface]["in_acl"], type = "in")
        if config["interfaces"][interface]["out_acl"] is not None:
            graph.add_edge(interface, config["interfaces"][interface]["out_acl"], type = "out")

    return graph

#Adding individual keywords to each interface
def add_keywords(keyword_path, graph):
    # Load keywords
    with open(keyword_path, 'r') as keyword_file:
        keyword_json = json.load(keyword_file)

    # Add keyword nodes and edges
    for interface, keywords in keyword_json["interfaces"].items():
        #graph.add_node(interface, type="interface")
        for word in keywords:
            graph.add_node(str(word), type="keyword")
            graph.add_edge(interface, str(word))

if __name__ == "__main__":
    main()
