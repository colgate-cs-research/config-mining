import pandas as pd
import numpy as np
import re
import itertools as itools
from sklearn.preprocessing import LabelEncoder as le
from read_rules import extract_dataframe,order_dataframe
from sklearn.metrics import f1_score

def column_hash(pd_series):
    # converting pandas series to numoy series
    numpy_series = pd_series.to_numpy()
    
    # compiling unique values in has_keys
    hash_keys = np.unique(numpy_series)


    # key: str(hash_key-value) | value: np.array(occurence1,occurence2....)
    hash_dict = {}
    for singular_key_object in zip(hash_keys) :
        singular_key=singular_key_object[0]
        #print("     current_key:"+singular_key+"|")
        #print(type(singular_key))
        if singular_key != None:
            hash_dict[singular_key] = np.where(numpy_series == singular_key)[0]
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
        #print("     key:"+key+"| values:"+value )
        #print(table_hash_dict[key].keys())
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

    rule_cover = get_common_rows(get_rule_rows(singular_rule,table_hash_dict),get_group_rows(group_val,column_hash_dict))

    return rule_cover


def all_rules_coverage(df,table_hash_dict,column_hash_dict):
    
    all_rules_coverage_list =[]
    for index, record in df.iterrows():
        coverage = rule_coverage(record,table_hash_dict,column_hash_dict)
        all_rules_coverage_list.append(coverage)

    df['coverage']=all_rules_coverage_list

    
    return df


    

def get_rules(keyword,depth,group,raw=0):
    '''
    for future more complex implementationg of importing rules
    '''
    # reading rule csv file
    rules_df = pd.read_csv("./csl_output/rules/aggregate_df_colgate_depth_"+str(depth)+"keyword: "+keyword+"_pr.csv",header=0)
    if raw==1: return rules_df
    # extracting the rules from strings
    # print(rules_df.head)
    rules_df = extract_dataframe(rules_df)
    rules_df = order_dataframe(rules_df,group)
    
    return rules_df

def main():
    keyword = 'staff'
    depth = 2
    group = '-1'  # 0 for not present | 1 for present | -1 for both


    # networkwide dataframe
    #aggregate_df = pd.read_csv("./csl_output/workingDB/aggregate_df_workDB.csv")
    aggregate_df = pd.read_csv("./csl_output/workingDB/colgate_workDB.csv")
    table_hash_dict = table_hash(aggregate_df)

    print("Columns:")
    #print(table_hash_dict.keys())
    column_hash_dict = table_hash_dict[keyword]
    #print(column_hash_dict)

    
    
    # loading rule dataframe
    print("Rules:")
    rules_df = get_rules(keyword,depth,group)
    print(rules_df)
    

    # adding rule coverage to rules_df
    print("Testing Coverage")
    rules_df = all_rules_coverage(rules_df,table_hash_dict,column_hash_dict)

    #print(rules_df.loc[0,'coverage'])
    return rules_df



if __name__ == "__main__":
    #doctest.testmod()
    main()