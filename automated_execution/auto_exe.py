import subprocess
import doctest
import os
from tokenize import group
import glob


def run_stucco_initiator(db_path,rules_path,group_feature,depth):
    #if BYPASS_Keyword_FILE_CREATION_PROCESS ==1:
     #   return 0
    #generating keyword list for the directories listed
    python_bash_cmd = "/usr/bin/python3"
    script_path_cmd = "/users/jchauhan/config-mining/csl/run_stucco.py"
    
    

    print("Group feature:{} depth:{}".format(group_feature,depth))

    final_cmd = [python_bash_cmd,script_path_cmd,db_path,rules_path,group_feature,"-d "+str(depth)]
    print("final command:{}\n\n\n".format(" ".join(final_cmd)))
    try:
        with open(os.devnull, 'wb') as devnull:
            subprocess.check_call(final_cmd, stdout=devnull,stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as err:
        #DEBUG:
        print("error: {0}".format(err.output))
        pass

def get_spanning_rules_initiator(org_df_path,rules_path,out_path,feature,group,depth=None,precision=None):
    #if BYPASS_Keyword_FILE_CREATION_PROCESS ==1:
     #   return 0
    #generating keyword list for the directories listed

    python_bash_cmd = "/usr/bin/python3"
    script_path_cmd = "/users/jchauhan/config-mining/get_spanning_rules.py"
    
    

    #print("Inputs->{} depth:{}".format(group_feature,depth))

    final_cmd = [python_bash_cmd,script_path_cmd,org_df_path,rules_path,out_path,feature,"-g "+str(group)]
    print("final command:\n{}\n\n\n".format(" ".join(final_cmd)))
    try:
        with open(os.devnull, 'wb') as devnull:
            subprocess.check_call(final_cmd, stdout=devnull,stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as err:
        #DEBUG:
        print("error: {0}".format(err.output))
        pass
    print("")


def main():
    # group_features = [56, 60, 164, 474, 2008]
    # group_features = ["vlan_Vlan"+str(grp) for grp in group_features ]
    # depth = 2
    # out_file_list = ["./csl_output/colgate/network_rules_"+"d"+str(depth)+"_"+grp_ftr+".csv" for grp_ftr in group_features]
    # db_path = "./TO_REMOVE/graph_to_database/dataframes/pruned/network.csv"

    # for i,j in zip(group_features,out_file_list):
    #     run_stucco_initiator(db_path,j,i,depth)
    # print(out_file_list)

    # for spanning rule finding
    rule_directory = './csl_output/colgate/network_rules_d2_*.csv'
    rule_files = glob.glob(rule_directory)
    
    print(rule_files)

    group_features = [56, 60, 164, 474, 2008]
    group_features = ["vlan_Vlan"+str(grp) for grp in group_features ]

    depth = 2
    
    db_path = "./TO_REMOVE/graph_to_database/dataframes/pruned/network.csv"
    rule_files = ['./csl_output/colgate/network_rules_d2_'+grp_ftr+".csv" for grp_ftr in group_features]
    for ftr_val in ["1","0"]:
        out_file_list = ["./csl_output/colgate/spanning_rules/network_rules_"+"d"+str(depth)+"_"+grp_ftr+"_"+ftr_val for grp_ftr in group_features]
        for rule_path,grp_ftr,out_file in zip(rule_files,group_features,out_file_list):
            #ARGUMENTS: org_df_path,rules_path,out_path,feature,group,depth=None,precision=None):
            print("\nRule_path:{}\n grp_ftr:{}\n out_file:{}".format(rule_path,grp_ftr,out_file))
            get_spanning_rules_initiator(db_path,rule_path,out_file,grp_ftr,ftr_val)
        #print(out_file_list)

    

    



if __name__ == "__main__":
    doctest.testmod()
    main()
