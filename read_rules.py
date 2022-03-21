import pandas as pd
import numpy as np
import re

from sklearn.metrics import f1_score

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

    # 





    #print(dataframe.head)
    return dataframe

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

def weigthed_rank(df):

    return 

def order_dataframe(df):
    # selecting rules where GROUP = 1
    df = df.loc[ df['group']== 1]

    # ordering metric
    df =df.sort_values(by=['weighted_value','f1_score','frequency','precision'], ascending=False)

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
    precision_weight = 1
    recall_weight = 1
    frequency_weight = 1
    f1_score_weight = 2

    # frequency is normalied. divided by the biggest value
    df = df.assign(weighted_value= frequency_weight*f/max(f) + f1_score_weight*f1)


    return df


def top_attributes(df):
    # selecting the top attributes
    no_of_rules = 10 
    rules = df["rule"][0:no_of_rules-1]



    return rules


def main():
    depth = 2
    keyword = 'l3'

    # creating dataframe
    rule_df = pd.read_csv("./csl_output/rules/aggregate_df_depth_"+str(depth)+"keyword: "+keyword+"_pr.csv",header=0)

    # printing column names of the database
    #print(list(rule_df.columns.values))

    # read strings and convert into machine readable format
    new_df = extract_dataframe(rule_df)

    # adding metrics
    new_df = additional_mertics(new_df)
    
    
    # ranking rules
    new_df=order_dataframe(new_df)
    
    # geetng the best predictors for the GROUP
    top_network_attributes = top_attributes(new_df)

    new_df.to_csv('new_df.csv', index=False)
    #print(new_df.head)

    return 0



if __name__ == "__main__":
    #doctest.testmod()
    main()