import sys
import pandas as pd
import numpy as np
import re
import itertools as itools
from sklearn.preprocessing import LabelEncoder as le
from read_rules import extract_dataframe,order_dataframe
from sklearn.metrics import f1_score
import logging

logging.basicConfig(level=logging.INFO)# ,filemode='w',filename="./TO_REMOVE/temp/spanning_rules.log")
logging.getLogger(__name__)

def column_hash(pd_series):
    # converting pandas series to numoy series
    #logging.debug("pd_series_index:{}".format(pd_series.index))
    #sys.exit()
    #numpy_series = pd_series.to_numpy()
    
    # compiling unique values in has_keys
    hash_keys = pd.unique(pd_series)


    # key: str(hash_key-value) | value: np.array(occurence1,occurence2....)
    hash_dict = {}
    for singular_key_object in zip(hash_keys) :
        singular_key=singular_key_object[0]
        #print("     current_key:"+singular_key+"|")
        #print(type(singular_key))
        if singular_key != None:
            hash_dict[singular_key] = pd_series[pd_series == singular_key].index#pd_series.where(pd_series == singular_key)
            #print(hash_dict[singular_key])
            #sys.exit()
        #print(len(hash_dict[str(singular_key)]))

    
    return hash_dict
        
def table_hash(df):
    # list of all columsn in dataframe
    column_list = list(df)
    # to return object
    table_hash_dict = {}

    for column in column_list:
        df[column] = df[column].astype(str)
        # hash of column values for each column
        #print("        Current Col:"+str(column)+"|")
        table_hash_dict[column] = column_hash(df[column])
    
    return table_hash_dict

def get_common_rows(np_arr1,np_arr2):
    return np.intersect1d(np_arr1,np_arr2)

def get_rule_rows(rule,table_hash_dict):
    '''
    get common rows among all the groups listed in the row.
    rule => {'backup': '1', 'to': '0'}
    common_rows => row which are in BOTH - backup:1 & to:0
    '''
    common_rows_list = []
    rule_keys = rule.keys()

    for key in rule_keys:
        value = str(rule[key]) if str(rule[key]) != 'None' else 'nan'
        key = str(key)
        logging.info("{}:{}".format(key, value))
        print("     key:"+key+"| values:"+value )
        print(table_hash_dict[key].keys())
        common_rows_list.append(table_hash_dict[key][value])

    # getting common rows in numpy arrays
    common_rows = common_rows_list[0]
    for i in range(1,len(common_rows_list)):
        common_rows = get_common_rows(common_rows,common_rows_list[i])
    
    return common_rows
        

def get_group_rows(group,column_hash_dict):
    '''
    here the group aka group_feature is 'ls
    group => '0' i.e 'l3'= 0
    TO RETURN=> rows which satisfy 'l3'=0   <type> = np array
    
    '''
    #print("Inside get_grp_rows")
    #print(type(group))
    return column_hash_dict[group]

def rule_coverage(rule_df_record,table_hash_dict,column_hash_dict):
    singular_rule = rule_df_record['rule']
    group_val = str(rule_df_record['group'])

    rule_rows = get_rule_rows(singular_rule,table_hash_dict)
    if column_hash_dict is not None:
        group_rows = get_group_rows(group_val,column_hash_dict)
    else:
        group_rows = get_rule_rows(rule_df_record['consequent'], table_hash_dict)
    rule_cover = get_common_rows(rule_rows,group_rows)
    
    rows_not_covered = np.setdiff1d(rule_rows,rule_cover)#[i for i in rule_rows if i not in rule_cover]

    
    return rule_cover,rule_rows,rows_not_covered



def all_rules_coverage(df,table_hash_dict,column_hash_dict):
    
    all_rules_coverage_list =[]
    rule_rows_list = []
    rows_not_covered_list =[]
    for index, record in df.iterrows():
        coverage,rule_rows,rows_not_covered = rule_coverage(record,table_hash_dict,column_hash_dict)
        all_rules_coverage_list.append(coverage)
        rule_rows_list.append(rule_rows)
        rows_not_covered_list.append(",".join(map(str,rows_not_covered)))

    df['coverage']=all_rules_coverage_list
    df['rule_coverage']=rule_rows_list
    df['rows_not_covered']=rows_not_covered_list

    
    return df
def find_subset_df(df,group_feature,group_val,rows_to_keep):
    '''
    find the subset of the INPUT df according to group and rows_to_keep

    '''
    if str(group_val)=="-1":
        pass
    else:
        try:
            df = df.query(group_feature+' == '+str(int(group_val)))
            
        except:
            print("ERROR: cannot make group selection")
            print("Group:{}| and Type:{}|".format(group_val,type(group_val)))
            sys.exit()
    df.reset_index()
    print(np.array(rows_to_keep))
    return df.loc[rows_to_keep]
    
    
    


def find_rule_violations(rule_df,aggreagate_df):
    '''
    find the rows which are violated by a particula rule
    Ensure that df contains 'coverage' and 'rule_coverage'
    '''
    pass
    

    

def get_rules(path,group,raw=0):
    '''
    for future more complex implementationg of importing rules
    '''
    logging.debug("\t\t\t<<START>> get_rules")
    # reading rule csv file
    rules_df = pd.read_csv(path,header=0)
    if raw==1: return rules_df
    # extracting the rules from strings
    # print(rules_df.head)

    rules_df = extract_dataframe(rules_df)
    rules_df = order_dataframe(rules_df,group)
    logging.debug("\t\t\t<<END>> get rules")
    return rules_df

def main(org_df_path,rules_path,grp_feature=None,feature_val=-1,precision=0):
    logging.debug("\t\tget_rule_coverage \t\tMAIN:-")
    logging.debug("\t\tGroup Feature:{}\t feature_val:{}".format(grp_feature,int(feature_val)))
    feature_val = feature_val  # 0 for not present | 1 for present | -1 for both


    # networkwide dataframe
    #aggregate_df = pd.read_csv("./csl_output/workingDB/aggregate_df_workDB.csv")
    aggregate_df = pd.read_csv(org_df_path)
    #aggregate_df[grp_feature] = aggregate_df[grp_feature].astype("int")
    #aggregate_df['index1'] = aggregate_df.index

    #logging.debug("grp_col_unique_items:{} \ntype:{}\n\n".format(aggregate_df[grp_feature],type(aggregate_df[grp_feature])))
    
    
    # This version of the column selection works
    #aggregate_df = aggregate_df.query(str(grp_feature)+' == '+str(int(feature_val)))
    aggregate_df.to_csv("Tmepp.csv")



    
    #logging.debug("Unique grp feature:{} vals:{}".format(grp_feature,np.unique(aggregate_df[grp_feature])))
    table_hash_dict = table_hash(aggregate_df)

    grp_feature_hash = None
    if (grp_feature is not None):
        logging.debug("Columns:\n\t\t{}".format(table_hash_dict.keys()))
        grp_feature_hash = table_hash_dict[grp_feature]
        logging.debug("ColumnHashDict:\n\t\t{}".format(grp_feature_hash))
    #sys.exit()


    
    
    # loading rule dataframe
    rules_df = get_rules(rules_path,feature_val)
    #logging.debug("Selecting rules with precision:{}".format(arguments.precision))
    # selecting rules with precision:1
    rules_df = rules_df.loc[rules_df['precision'] > precision]
    logging.debug("Rules:\n\t\t{}".format(rules_df))
        

    

    # adding rule coverage to rules_df
    
    rules_df = all_rules_coverage(rules_df,table_hash_dict,grp_feature_hash)
    #logging.debug("Testing Coverage:{}".format(rules_df.loc[0,'coverage']))

    logging.debug("\tget_rule_coverage->END")
    return rules_df



if __name__ == "__main__":
    #doctest.testmod()
    main()