import json
import numpy as np
import pandas as pd
import sys
import logging
import argparse
import get_rule_coverage

logging.basicConfig(level=logging.WARNING)# ,filemode='w',filename="./TO_REMOVE/temp/spanning_rules.log")
logging.getLogger(__name__)
sys.path.append("/users/jchauhan/config-mining/")





def main():

    parser = argparse.ArgumentParser(description='Run rule_spanning on a dataset')
    parser.add_argument('org_df_path',type=str, help='Path for a CSV file containing the pruned dataframe')
    parser.add_argument('rules_path',type=str, help='Path for a CSV file which stores the rules')
    parser.add_argument('out_path',type=str, help='Path for a CSV file which stores MIN spanning rules')
    parser.add_argument('feature',type=str, help='Select the group-feature name.')
    parser.add_argument('-g','--group',type=str,default=-1, help='Select the group-feature value.')
    parser.add_argument('-d', '--depth', type=int, default=1, help="Maximum rule depth")
    parser.add_argument('-p', '--precision', type=float, default=0.950, help="Only select rules with precison above the given value")
    arguments = parser.parse_args()

    #outfile = "./vlan474_spanning_rules.csv"
    grp_feature = arguments.feature
    depth = arguments.depth
    group = arguments.group  # 0 for not present | 1 for present | -1 for both
    outfile = arguments.out_path

    


if __name__ == "__main__":
    #doctest.testmod()
    main()




violations = {}
db_path = "/users/jchauhan/config-mining/TO_REMOVE/graph_to_database/dataframes/pruned/network.csv"
rule_df_path = "/users/jchauhan/config-mining/csl_output/colgate/network_rules_d2_vlan_Vlan164.csv"
grp_feature = "vlan_Vlan164"
group = -1
precision = 0.05

# Getting coverage
rules_df = get_rule_coverage.main(db_path,rule_df_path,grp_feature,group)
# saving as pickle
#rules_df.to_pickle("./rules_df_temp.pkl")
# loading from pickle
#with open("users/jchauhan/config-mining/csl_output/colgate/spanning_rules/network_rules_d2_vlan_Vlan164_0.pkl", 'r') as coverage_csv:
coverage_reader = pd.read_pickle("./rules_df_temp.pkl")

print("Starting coverage violations")

# for i,record in coverage_reader.iterrows():
    
#     rows_not_covered = record["rows_not_covered"].split(",")
#     if rows_not_covered is not None and len(rows_not_covered) <=10 and rows_not_covered != "":
#         print(rows_not_covered)
        
#         for row in rows_not_covered:
#             print(row,type(row))
#             row = int(row)
#             if row not in violations:
#                 violations[row] = []
#             violations[row].append(record["rule"])
#     else:
#         pass
#         #print("-",end="")



#json(violations)
# with open("your_json_file.json", "w") as fp:
#     json.dump(violations,fp,indent=4) 

# with open("your_json_file.json","r") as fp:
#     violations = json.load(fp)

# for row_num in violations.keys():
#     # for each row/row_number
#     print("\t\ROW_NUM:{}".format(row_num))
#     rules_violated = violations[row_num]

#     single_length_rules =[]
#     for rule in rules_violated:
#         if len(rule)==1:
#             print("Found single-length rules for row:{}".format(row_num))
#             single_length_rules.append(rule)
#         else:
#             pass
#     if len(single_length_rules) ==0:
        
#         print("No single length rules")
#         continue
    
#     new_rules_violated =[]
#     for idv_rule in single_length_rules:
#         new_rules_violated.append(idv_rule)
#         rules_violated.remove(idv_rule)

#         key = list(idv_rule.keys())[0]
#         print(key)
#         for remaining_rule in rules_violated:
#             print("Curent_remaing_rule:{}".format(remaining_rule),end=" ")
#             if key in remaining_rule.keys():
#                 print(" \t\tDELETE")
#                 rules_violated.remove(remaining_rule)
#             else:
#                 new_rules_violated.append(remaining_rule)
#                 print("")
    
#     #print("rules_violated:{}".format(rules_violated))
#     violations[row_num] = new_rules_violated
#     #sys.exit()

# with open("your_json_file_cleaned.json", "w") as fp:
#     json.dump(violations,fp,indent=4) 

# Running rule CONDENSATION
with open("./your_json_file_cleaned.json","r") as fp:
    violations = json.load(fp)



for row in violations.keys():
    rules_violating_row = violations[row]
    # Now for each row list: 
    # FORMAT-> "row_num":[rule1,rul2,rule3]
    updated_row_violations = []
    
    records ={}
    for rule in rules_violating_row:
        
        if len(rule)==1:
            # Single length rule
            print("\t!Single length Rule:{}|".format(rule))
            updated_row_violations.append(rule)
            continue
        elif len(rule)==2:
            components = list(rule.items())
            k1,v1 = components[0]
            single_componenet1 = "|{}:{}|".format(k1,v1)
            k2,v2 = components[1]
            single_componenet2 = "|{}:{}|".format(k2,v2)


            if single_componenet1 not in records.keys():
                records[single_componenet1] = {}
            records[single_componenet1][single_componenet2] =1

            if single_componenet2 not in records.keys():
                records[single_componenet2] = {}
            #records[single_componenet2].append({single_componenet1:1})
            records[single_componenet2][single_componenet1] =1

    # I.e there are rules which can be condensed
    if len(records)>0:
        print("RECORDS: {}".format(records))
        #sys.exit()
        df_entry = [records[x] for x in records.keys()]
        # This is the index of the dataframe
        index=[x for x in records.keys()]

        # THE GRAPH ADJACENCY MATRIX GENERATED
        df = pd.DataFrame.from_records(df_entry).fillna(0).reindex(columns=index)
        # Df format->   column arragenment can be different./ WONT BE
        #       vlan1     vlan2   vlan3
        # vlan1    (0)       0       1
        # vlan2     0        (0)     1
        # vlan3     1         1       1
        print("\t\tindex:{}".format(index))
        print("\t\tdf_entry: {}\n ".format(df_entry))
        print("FINAL DF->\n{}".format(df.head))


        # Now  CUSTOM most-common VLAN heuristic
        print("Column_Sum:{}".format(df.sum().max()))
        while df.sum().max() >=1:
            location = df.sum().argmax()
            column_name = index[location]
            # find all the VLANs which 1 for a particular column
            column = df.iloc[:,location]
            # list of locations where values is 1.0
            index_locations = list(column.index[(column==1.0)])
            relevant_vlans = [index[x] for x in index_locations]
            if len(relevant_vlans)>0:
                updated_row_violations.append({column_name:relevant_vlans })
            else:
                updated_row_violations.append(column_name)
            #print("UPDATED_ROW_VIOLATION:{}".format(updated_row_violations))
            
            # REmoving the current selection from future pool
            df.iloc[:,location] = 0
            df.iloc[location,:] = 0


    violations[row] = updated_row_violations
    print("UPDATED_ROW_VIOLATION:\n{}".format(updated_row_violations))
    print("_"*100)

with open("./your_json_file_condensed.json","w") as fp:
    json.dump(violations,fp,indent=4) 



                




    


