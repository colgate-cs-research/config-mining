import argparse
import json
from attr import has
import networkx as nx
import os
import pandas as pd
import ipaddress
import logging
import numpy as np
# module-wide logging
logging.basicConfig(filename="./graph_to_db.log",level=logging.DEBUG)
logging.getLogger(__name__)

def one_hot_encode(node, graph, node_type):
    neighbor_nodes = get_neighbors(node, graph, node_type)
    all_nodes = get_nodes(graph, node_type)
    encoding = {}
    for node in all_nodes:
        if node in neighbor_nodes:
            encoding[node_type + "_" + str(node)] = 1
        else:
            encoding[node_type + "_" + str(node)] = 0
    return encoding

def col_prefixes(ip, startlen=20, endlen=32):
    """
    Generates prefixes of varying length from an IP address.
    #>>> col_prefixes("85.36.219.170", 20, 31)
    ['85.36.208.0/20', '85.36.216.0/21', '85.36.216.0/22', '85.36.218.0/23', '85.36.219.0/24', '85.36.219.128/25', '85.36.219.128/26', '85.36.219.160/27', '85.36.219.160/28', '85.36.219.168/29', '85.36.219.168/30', '85.36.219.170/31']
    """
    prefixes = {}       # the list of prefixes to be added to the one of the greater lists in the parent function
    if(ip!=None and "/" in ip):
        
        ip_original,subnet =ip.split("/")[0] ,ip.split("/")[1]
        
               

        #####################
        # starting the tendril search
        ###################
             
        
        powers_of_two =[128,64,32,16,8,4,2,1]

        # Figuring ou the starting point
        # Step1: find the maximun below-min value.
        remainder=int(ip_original.split(".")[3 -1]) # "3"rd is the octet we want to examine.
        for two in powers_of_two:
            if two ==8: # since we only examine the secnd part of the octet.
                break
            if two>remainder:
                pass
            else:
                remainder-=two
        
        start = int(ip_original.split(".")[3 -1]) - remainder

        #print("Start:"+str(start)+" Remainder:"+str(remainder)+"  original_IP: "+str(ip_original.split(".")[3 -1]))

        # We got the starting point, now we need to generate the list of subnets.
        # Step2: WE start the largets subnet;  from the middle of the third octet.

        
        #for two in powers_of_two[4:]:


        ########################
        #' IPv4Network nodeul Code (start)
        # #######################'    


        for prefixlen in range(startlen, endlen):
            prefix = ipaddress.IPv4Network(ip_original + "/" + str(prefixlen), strict=False) # generates subnet list
            prefixes["subnet_/"+str(prefixlen)] = str(prefix)

        # Now prefixes have all the subnets relavant for the current IP's situation.
        # print(prefixes)

        ##################"
        # Code (end)
        # ################"


        


        return prefixes
    else:
        # print("Goes here")
        for prefixlen in range(startlen, endlen):
            prefixes["subnet_/"+str(prefixlen)] = "n"

def create_dataframe(graph,has_type_toggle=False):
    nodes = get_nodes(graph, "interface")
    df_dict={}
    for node in nodes:
        logging.debug(" NODE: {}".format(node))

        vlans = one_hot_encode(node, graph, "vlan")
        logging.debug("     VLANS: {}".format(vlans))
        df_dict[node] = {**vlans}
        if len(np.unique(vlans.values())) >1 and has_type_toggle:
            temp = {"has_vlans":"1"}
            df_dict[node].update(temp) 
        elif has_type_toggle:
            df_dict[node] = {**vlans}
            logging.debug("\t\tNo VLANs found")
            df_dict[node].update({"has_vlans":0}) if has_type_toggle else None 



        keywords = one_hot_encode(node, graph, "keyword")
        logging.debug("     Keyword: {}".format(keywords))
        if len(np.unique(keywords.values())) >1 and has_type_toggle:
            df_dict[node].update(keywords)#, **keywords}
            df_dict[node].update({"has_keywords":"1"}) if has_type_toggle else None
        elif has_type_toggle:
            df_dict[node].update({"has_keywords":"0"}) if has_type_toggle else None 
            pass



        subnets = get_neighbors(node, graph, "subnet")
        if (len(subnets) != 1):
            logging.debug("     !Interface {} has {} subnets".format(node, len(subnets)))
            prefixes = col_prefixes(None)
            df_dict[node].update({"has_subnets":"0"}) if has_type_toggle else None  
        else:
            addr = list(subnets)[0]
            prefixes = col_prefixes(addr)
            df_dict[node].update(prefixes)
            df_dict[node].update({"has_subnets":"1"}) if has_type_toggle else None  
        logging.debug(" prefixes: {}".format(prefixes))

        # Adding elemnts to record
    logging.debug(" \ndf_dict[]:\n {}".format(df_dict))

    # Converting df_dict to dataframe
    records= []
    for key, value in df_dict.items():
        value["interface"] = key
        records.append(value)
    df = pd.DataFrame.from_records(records)
    df.set_index('interface')
    logging.info(" final df->\n{}".format(df.head))

    return df


        

def get_nodes(graph, target_type=None):
    """Returns list of all nodes of target_type in graph"""
    # Compute
    types_cache = nx.get_node_attributes(graph, "type")
    node_list = []
    for node in graph:
        if target_type is None or types_cache[node] == target_type:
            node_list.append(node)

    # return result
    return node_list

def get_neighbors(node, graph, target_type=None):
    """Get a set of node's neighbors of target_type"""
    # Compute
    types_cache = nx.get_node_attributes(graph, "type")
    all_neighbors = nx.neighbors(graph, node)
    if target_type is None:
        neighbor_list = set(all_neighbors)
    else:
        neighbor_list = set()
        for neighbor in all_neighbors:
            if types_cache[neighbor] == target_type:
                neighbor_list.add(neighbor)

    # Cache and return result
    return neighbor_list

def load_graph(graph_path):
    """Load a graph from a JSON representation"""
    with open(graph_path, 'r') as graph_file:
        graph_json = json.load(graph_file)
    return nx.readwrite.json_graph.node_link_graph(graph_json)

def main():
    #Parse command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('graph_path',type=str, 
            help='Path for a file containing a JSON representation of graph')
    parser.add_argument('out_path',type=str, 
        help='Path for a file containing a pandas Dataframe representation of graph')
    arguments=parser.parse_args()

    graph = load_graph(arguments.graph_path)
    dataframe = create_dataframe(graph,has_type_toggle=True)
    filename = arguments.graph_path.split("/")[-1] if arguments.graph_path.split("/")[-1] is not "" else arguments.graph_path.split("/")[-2]
    
    path = arguments.out_path+filename+'.csv'
    logging.info("  Saving dataframe @:{}".format(path))
    dataframe.to_csv(path, index=False)
    

if __name__ == "__main__":
    main()
