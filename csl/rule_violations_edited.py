import csv
import json
import pandas as pd
import sys
import logging
logging.basicConfig(level=logging.WARNING)# ,filemode='w',filename="./TO_REMOVE/temp/spanning_rules.log")
logging.getLogger(__name__)
sys.path.append("/users/jchauhan/config-mining/")
import get_rule_coverage

violations = {}
db_path = "/users/jchauhan/config-mining/TO_REMOVE/graph_to_database/dataframes/pruned/network.csv"
rule_df_path = "/users/jchauhan/config-mining/csl_output/colgate/network_rules_d2_vlan_Vlan164.csv"
grp_feature = "vlan_Vlan164"
group = -1
precision = 0.05
db_csv = pd.read_csv(db_path)
# Getting coverage
#rules_df = get_rule_coverage.main(db_path,rule_df_path,grp_feature,group)
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

with open("your_json_file.json","r") as fp:
    violations = json.load(fp)

for row_num in violations.keys():
    # for each row/row_number
    print("\t\ROW_NUM:{}".format(row_num))
    rules_violated = violations[row_num]

    single_length_rules =[]
    for rule in rules_violated:
        if len(rule)==1:
            print("Found single-length rules for row:{}".format(row_num))
            single_length_rules.append(rule)
        else:
            pass
    if len(single_length_rules) ==0:
        
        print("No single length rules")
        continue
    
    new_rules_violated =[]
    for idv_rule in single_length_rules:
        new_rules_violated.append(idv_rule)
        rules_violated.remove(idv_rule)

        key = list(idv_rule.keys())[0]
        print(key)
        for remaining_rule in rules_violated:
            print("Curent_remaing_rule:{}".format(remaining_rule),end=" ")
            if key in remaining_rule.keys():
                print(" \t\tDELETE")
                rules_violated.remove(remaining_rule)
            else:
                new_rules_violated.append(remaining_rule)
                print("")
    
    #print("rules_violated:{}".format(rules_violated))
    violations[row_num] = new_rules_violated
    #sys.exit()

with open("your_json_file_cleaned.json", "w") as fp:
    json.dump(violations,fp,indent=4) 

# # Running rule condensation;
# with open("your_json_file_condensed.json","w") as fp
#     violations


