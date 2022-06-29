import argparse
import networkx as nx
import os
import sys
import tqdm

queries_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.dirname(queries_dir))
import graphs.graph_utils as graph_utils

def unit_share_subnet_not_vlan(graph):
    units = graph_utils.get_nodes(graph, "unit")
    subnets = graph_utils.get_nodes(graph, "unit")
    for i in range(len(units)):
        for j in range(i+1, len(units)):
            unitI = units[i]
            unitIsubnets = graph_utils.get_neighbors(unitI, graph, "subnet")
            unitIvlans = graph_utils.get_neighbors(unitI, graph, "vlan")
            unitJ = units[j]
            unitJsubnets = graph_utils.get_neighbors(unitJ, graph, "subnet")
            unitJvlans = graph_utils.get_neighbors(unitJ, graph, "vlan")
            sharedSubnets = unitIsubnets.intersection(unitJsubnets)
            sharedVlans = unitIvlans.intersection(unitJvlans)
            if (unitIvlans or unitJvlans) and sharedSubnets and not sharedVlans:
                print("{} and {} share {} but not {} and {}".format(
                    unitI, unitJ, sharedSubnets, unitIvlans, unitJvlans))
def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Analyze subgraphs involving VLANs')
    parser.add_argument('graph_path',type=str, 
            help='Path for a file containing a JSON representation of graph')
    #parser.add_argument('cycles_path',type=str, 
        #help='Path for a folder containing csv files of cycles and their frequencies')
    arguments = parser.parse_args()

    graph = graph_utils.load_graph(arguments.graph_path)
    unit_share_subnet_not_vlan(graph)
    

if __name__ == "__main__":
    main()
