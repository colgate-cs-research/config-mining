import os
import sys
import pandas as pd
import numpy as np
import re
import logging
from sklearn.metrics import f1_score

logging.basicConfig(level=logging.DEBUG)
logging.getLogger(__name__)

def extract_dataframe(dataframe):

    
    
    # converting rules to dict { 'attribute'<type: str> : 'value'<type: str> } 
    dataframe = dataframe.assign(rule= dataframe['rule'].map(lambda x: clean_rule(x)))
    # cleaning group
    dataframe = dataframe.assign(group= dataframe['group'].map(lambda x: clean_group(x)))

    # cleaning precision
    dataframe = dataframe.assign(precision= dataframe['precision'].map(lambda x: float(x)))
    # cleaning recall
    dataframe = dataframe.assign(recall= dataframe['recall'].map(lambda x: float(x)))

    # cleaning recall
    dataframe = dataframe.assign(frequency= dataframe['frequency'].map(lambda x: int(x)))
    
    # removing all rules with "filename" string 
    #dataframe = filter_rule_column(dataframe)

    #print(dataframe.head)
    return dataframe


def filter_rule_column(df):
    record_list = df.to_dict('records')
    new_record_list = []
    #print("Entering filter_rule_column")
    
    for record in record_list:
        rule_dict = record['rule']

        # FILTER 1 -----
        # filtering all records which contain   "filename" : 'some_value' 
        if "filename" not in list(rule_dict.keys()):
            #print(" entering record:" +str(rule_dict))
            new_record_list.append(record)
            

    

    df = pd.DataFrame.from_records(new_record_list)
    

    #print("\n\n Leaving filter_rule_column")
    return df


def clean_group(string):
    return int(string.strip()[-1])

def clean_rule(string):
    #print("executing: clean_rule", end=" ")
    # removing '(' and ')' from rule
    string=string[1:-1]
    # breaking rules at ','
    string =string.split(',')
    rules = {}
    for single_rule in string:
        # stripping whitespaces and excess commas
        single_rule=single_rule.strip()[1:-1]
        # converting string to rule
        a=single_rule.split("=>")
        if(len(a)==2):
            rules[a[0]]=a[1]

    #print(rules)
    #print('|'+string[0]+'|'+string[1]+'|')
    return rules



def order_dataframe(df,group):
    # selecting rules where GROUP = 1
    #df.to_csv("./ordered_df_INITIAL.csv",index=False)
    logging.info("\t\t\torder_dataframe->START")
    logging.info("group:{}| & type:{}|".format(group,type(group)))
    logging.info("INPUTS:\n group:{} \n df:{}".format(df.head,group))
    if(int(group)>=0): 
        logging.debug("Specific group selected")
        unique_elements= list(np.unique(df['group']))
        #print( str(i)+" type:"+str(type(i)) for i in unique_elements)
        unique_elements= list(map(int, unique_elements))
        #print(unique_elements[0],type(unique_elements[0]))
        #df = df.loc[ df['group']== int(group)]

        df['group'] = df['group'].astype("int")
        logging.debug("Group is:{}| type:{}\n current df:{}".format(group,type(group),df.head))
        df = df.query('group == '+str(int(group)))
        
        logging.debug("Group is:{}| type:{}\n current df:{}".format(group,type(group),df.head))
    
    #df.to_csv("./ordered_df_FINAL.csv",index=False)
    #sys.exit()
    # ordering metric
    df =df.sort_values(by=['precision','frequency'], ascending=False)

    #df=df[df['group'] == 1]
    return df

def additional_mertics(df):

    p = df['precision']
    r = df['recall']
    f = df['frequency']

    # adding f1 score
    df = df.assign(f1_score= 2*p*r/(p+r))

    f1 = df['f1_score']

    # adding weigthed rank
    precision_weight = 10
    recall_weight = 1
    frequency_weight = 1
    f1_score_weight = 2

    # frequency is normalied. divided by the biggest value
    df = df.assign(weighted_value= precision_weight*p+frequency_weight*f/max(f) + f1_score_weight*f1)


    return df


def top_attributes(df):
    # selecting the top attributes
    no_of_rules = 10 
    rules = df["rule"][0:no_of_rules-1]



    return rules


def main():
    depth = 2
    keyword = 'l3'
    group = -1  # 0 for not present | 1 for present | -1 for both

    # creating dataframe
    rule_df = pd.read_csv("./csl_output/rules/aggregate_df_depth_"+str(depth)+"keyword: "+keyword+"_pr.csv",header=0)

    # printing column names of the database
    #print(list(rule_df.columns.values))

    # read strings and convert into machine readable format
    new_df = extract_dataframe(rule_df)

    # adding metrics
    new_df = additional_mertics(new_df)
    
    
    # ranking rules
    new_df=order_dataframe(new_df,group)
    
    # geetng the best predictors for the GROUP
    top_network_attributes = top_attributes(new_df)

    new_df.to_csv('new_df.csv', index=False)
    #new_df.to_pickle('new_df.pkl')
    print(new_df.head)

    return new_df



if __name__ == "__main__":
    #doctest.testmod()
    main()