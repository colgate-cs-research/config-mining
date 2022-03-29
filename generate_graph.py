import analyze
import argparse
import ipaddress
import json
import networkx as nx

def main():
    #Parse command-line arguments
    parser = argparse.ArgumentParser(description='Generate a graph')
    parser.add_argument('config_path',type=str, help='Path for a file (or directory) containing a JSON representation of configuration(s)')
    parser.add_argument('keyword_path',type=str,help='Path for a file (or directory) containing a JSON representation of keywords from config(s)')
    parser.add_argument('out_path',type=str,help='Path for a file (or directory) in which to store a JSON representation (and image) of the graph(s)')
    parser.add_argument('-i', '--images', action='store_true')
    parser.add_argument('-a', '--aggregate', action='store_true')
    parser.add_argument('-p', '--prune', action='store_true')
    arguments = parser.parse_args()

    analyze.process_configs(analyze_configuration, [arguments.config_path, arguments.keyword_path], arguments.out_path, (arguments.images, arguments.prune), arguments.aggregate)

def analyze_configuration(in_paths, out_path=None, extras=(False,False)):
    generate_image, prune = extras
    print("Current working files: %s" % (in_paths))
    graph = nx.Graph()
    if not isinstance(in_paths[0], list):
        in_paths = [in_paths]
    for path in in_paths:
        config_path, keyword_path = path
        config = load_config(config_path)
        make_graph(config, graph)
        add_keywords(keyword_path, graph)
        if (prune):
            prune_keywords(graph)
            prune_all_degree_one(graph)
        #add_supernets(graph, prefix_length)

    # Save graph
    if out_path is not None:
        # Save graph
        analyze.write_to_outfile(out_path, nx.readwrite.json_graph.node_link_data(graph))

        # Save image
        if generate_image:
            pydot_graph = nx.drawing.nx_pydot.to_pydot(graph)
            pydot_graph.write_png(out_path.replace(".json", ".png"))
    
    return graph

def generate_graph(config_path, keyword_path, extras=(False, False)):
    return analyze_configuration([config_path, keyword_path], extras=extras)

def load_config(file):
    # Load config
    with open(file, "r") as infile:
        config = json.load(infile)
    return config

# constructs graph based on argument config file
# Nodetypes: acl, vlan, interface, subnet (call add_keywords to add keyword nodetype)
def make_graph(config, graph):
    device_name = config["name"]
    for acl in config["acls"]:
        device_acl = device_name +  "_" + acl
        graph.add_node(device_acl, type= "acl")
        if config["acls"][acl]["lines"] is not None:
            for line in config["acls"][acl]["lines"]:
                action = line["action"]
                if "dstIps" in line:
                    dst_address = ipaddress.IPv4Interface(line["dstIps"])
                    graph.add_node(str(dst_address.network), type ="subnet", subnet=True)
                    graph.add_edge(device_acl, str(dst_address.network), type=[action, "dst"])
                src_address = ipaddress.IPv4Interface(line["srcIps"])
                graph.add_node(str(src_address.network), type ="subnet", subnet=True)
                graph.add_edge(device_acl, str(src_address.network), type=[action, "src"])
    
    for interface in config["interfaces"]:
        if interface.startswith("Vlan"):
            node_name = interface
            graph.add_node(node_name, type="vlan")
        else:    
            node_name = device_name + "_" + interface
            graph.add_node(node_name, type="interface")
        
        if config["interfaces"][interface]["address"] is not None:
            address = config["interfaces"][interface]["address"]
            network_obj = ipaddress.IPv4Interface(address)
            graph.add_node(str(network_obj.network), type="subnet", subnet=True)
            graph.add_edge(node_name, str(network_obj.network))

        #added create node line (undefined allowed vlans???????)
        if config["interfaces"][interface]["allowed_vlans"] is not None:
            for vlan in config["interfaces"][interface]["allowed_vlans"]:
                vlan_name = "Vlan" + str(vlan)
                graph.add_node(vlan_name, type="vlan")
                graph.add_edge(node_name, vlan_name, type="allowed")

        if config["interfaces"][interface]["in_acl"] is not None:
            acl_name = device_name + "_" + config["interfaces"][interface]["in_acl"]
            graph.add_edge(node_name, acl_name, type = "in")
        if config["interfaces"][interface]["out_acl"] is not None:
            acl_name = device_name + "_" + config["interfaces"][interface]["out_acl"]
            graph.add_edge(node_name, acl_name, type = "out")

    return graph

#Adding individual keywords to each interface
def add_keywords(keyword_path, graph):
    # Load keywords
    with open(keyword_path, 'r') as keyword_file:
        keyword_json = json.load(keyword_file)
    device = keyword_json["name"]

    # Add interface keyword nodes and edges
    for interface, keywords in keyword_json["interfaces"].items():
        if interface.startswith("Vlan"):
            node_name = interface #remove device name from vlans
            graph.add_node(node_name, type="vlan")
        else: 
            node_name = device + "_" + interface
            graph.add_node(node_name, type="interface")
        for word in keywords:
            graph.add_node(word, type="keyword", keyword=True)
            graph.add_edge(node_name, str(word))

    # Add acl keyword nodes and edges
    for acl, keywords in keyword_json["acls"].items():
        device_acl = device + "_" + acl
        graph.add_node(device_acl, type="acl")
        for word in keywords:
            graph.add_node(word, type="keyword", keyword=True)
            graph.add_edge(device_acl, str(word))

#remove & print keywords that only appear once across the network
def prune_keywords(graph):
    keywords = list(nx.get_node_attributes(graph, 'keyword').keys())
    # print("KEYWORDS:")
    # print(keywords)
    # print()
    #print("*********** PRUNED: Words that only appear once ***********")
    for word in keywords:
        if graph.degree(word) <= 1:
            #print(word)
            graph.remove_node(word)

    # print()
    # print("KEYWORDS AFTER PRUNING:")
    # print(list(nx.get_node_attributes(graph, 'keyword').keys()))
    return

#remove & print nodes that only appear once across the network
def prune_all_degree_one(graph):
    nodes = list(graph.nodes)
    #print("*********** PRUNED NODES that only have one link ***********")
    for node in nodes:
        if graph.degree(node) <= 1:
            #print(node)
            graph.remove_node(node)
    #print()
    return

def add_supernets(graph, prefix_length):
    """add supernet subnet nodes to argument graph with specified prefix length"""
    subnets = list(nx.get_node_attributes(graph, 'subnet').keys())
    supernets = set()
    for subnet in subnets:
        supernet = ipaddress.IPv4Interface(subnet).network.supernet(new_prefix=prefix_length)
        if supernet not in supernets:
            supernets.add(supernet)
            graph.add_node(str(supernet), type="subnet", subnet=True)
            graph.add_edge(subnet, str(supernet))
    return

if __name__ == "__main__":
    main()
