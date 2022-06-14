import argparse
import ipaddress
import json
import networkx as nx
import os
import time
from queue import Queue


# function that calculates Euclidean distance in an len(l1)-dimensional space
# Inputs: l1 and l2 are lists
# Output: Distance/len(l1) (distance as a fraction of the length of the vectors)
def distance(l1, l2):
    d = 0
    for i in range(len(l1)):
        if l1[i] != l2[i]:
            d += 1
    return d/len(l1)

def get_closest_nodes(node_lst,vector_dict):
    closest_nodes_dict = {}
    for i in range(len(node_lst)):
        closest_nodes_dict[node_lst[i]] = []
    for i in range(len(node_lst)):
        for j in range(i+1, len(node_lst)):
            d = distance(vector_dict[node_lst[i]], vector_dict[node_lst[j]])
            if (d > 0.5):
                closest_nodes_dict[node_lst[i]].append(node_lst[j])
                closest_nodes_dict[node_lst[j]].append(node_lst[i])
    return get_closest_nodes

def main():
    start = time.time()
    parser = argparse.ArgumentParser(description='Get the list of most similar neighbors')
    parser.add_argument('vector_path', help='Path for a file (or directory) containing a JSON representation of configuration(s)')
    #parser.add_argument('out_path', help='Name of file (or directory) to write JSON file(s) containing keywords')
    arguments = parser.parse_args()

    #get dictionary where keys are interfaces and values are the vectors (list of numbers)
    infile = open(arguments.vector_path, 'r')
    vector_dict = {}
    node_lst = []
    line = infile.readline().strip().split(",")
    typ = line[0]
    lst_of_possible_neighbors = line[1:]
    for line in infile:
        l = line.strip().split(",")
        name = l[0]
        node_lst.append(name)
        vector_dict[name] = l[1:]
    infile.close()

    closest_nodes_dict = get_closest_nodes(node_lst,vector_dict)

    for key in get_closest_nodes:
        print("Key: " + key)
        print(get_closest_nodes[key])
    
    end = time.time()
    print("Time taken: " + str(end - start))




if __name__ == "__main__":
    main()