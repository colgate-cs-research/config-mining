from operator import index
from get_rule_coverage import *
import pandas as pd
import argparse
import time
import numpy as np
import re
import sys


def main():
    filename="./csl_output/colgate/spanning_rules/network_rules"+"_d2_vlan_Vlan56_1"+".pkl"
    rules_df = pd.read_pickle(filename)
    rules_df_record = rules_df.iloc[0]
    #print(type(rules_df_record))
    
    agg_df = pd.read_csv("./TO_REMOVE/graph_to_database/dataframes/pruned/network.csv")
    print(find_subset_df(agg_df,"vlan_Vlan56",int(rules_df_record['group']),rules_df_record["coverage"]))
    rules_df_record.to_csv("temppp.csv",index=False)





if __name__ == "__main__":
    #doctest.testmod()
    main()