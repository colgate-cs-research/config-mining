import pandas as pd
import time
import numpy as np
import re
from sklearn.preprocessing import LabelEncoder as le
import get_rule_coverage 
from sklearn.metrics import f1_score


def gen_rule_column(rules_df,total_rows,rule_no):
    rule_series = np.zeros(total_rows, dtype=int)[np.newaxis]
    rule_coverage = rules_df.loc[rule_no]['coverage']
    for i in rule_coverage:
        print(i,end=" ")
        rule_series[0][i]=1
    print(rule_series)

    return rule_series
    


def gen_rule_matrix(rules_df,total_rows,resuse=0):


    print("Starting Matrix generation:")
    rule_matrix = np.empty([total_rows, len(rules_df)], dtype=int)
    for i in range(len(rules_df)):
        if i%100 ==0: print(i,end=" ")
        curr_rule = gen_rule_column(rules_df,total_rows,i)
        rule_matrix[:,i] = curr_rule
        print(rule_matrix[:,i])


    #print(type(a))
    print(rule_matrix[:,1])
    #print(np.where(rule_matrix[:,1]==1))
    print("MATRIX SHAPE:"+str(rule_matrix.shape))
    #print(rule_matrix)


    return rule_matrix

def stopping_condition(for_sum,option = 0):
    # for_sum <ndarray>
    untouched_rows = len(np.where(for_sum == 1.0)[0])
    total_rows = len(for_sum)
    val = False
    if option==0:

        threshold = 0.70
        
        ratio = untouched_rows/total_rows
        
        val =  True if (ratio)<threshold else False
        #print("Untouched_rows:"+str(untouched_rows))

    print(" Untouched percentage:"+str(round(untouched_rows/total_rows*100)) + '%',end =' ')
    
    return val
    pass

def get_rule_set(rule_matrix,total_rows,initial_weight,weight_reduction):
    print("Starting rule_set generation:")
    for_sum = np.full((total_rows), initial_weight,dtype=float)
    for_reduction = np.full((total_rows), weight_reduction,dtype=float)[np.newaxis]
    

    rule_set =[]
    old_sum=np.Inf
    while not stopping_condition(for_sum):
    
        
        # print("Current sum(for_sum):"+str(np.sum(for_sum)))
        # print("Current rule set state:"+str(rule_set))
        a = np.matmul(for_sum, rule_matrix)
        # print("TYPE of a:"+str(type(a))+" SHAPE:"+str(a.shape))
        best_rule_val = np.amax(a)
        # print("     value of np.amax(a):"+str(best_rule_val))
        
        #best_rule_loc = int(np.where(a == np.amax(a))[0])
        best_rule_loc = np.argmax(a)

        #print(best_rule_loc,end=" <- best_rule_loc   ")
        best_rule_matrix = np.copy(rule_matrix[:,best_rule_loc])

        # removing selected rule from the existing pool
        #print(" BEFORE: rule_matrix[best_rule_loc]:" + str(len(np.where(rule_matrix[:,best_rule_loc] == 1)[0])),end="   ")
        
        #print(" AFTER: rule_matrix[best_rule_loc]:" + str(len(np.where(rule_matrix[:,best_rule_loc] == 1)[0])))
        print(float(best_rule_val), end=" <- best_rule_val \r")
        # adding best rule_no. to rule_set
        if(int(best_rule_loc) not in rule_set):
            rule_set.append(int(best_rule_loc))    # +2 for off-setting python + header line
        else:
            print("\n\n\nREPETitions detected")
            break

        # if rule ={ 0 0 1 0 }
        # then for_reduction = { 1 1 0.5 1}
        
        for_reduction = best_rule_matrix *0.5
        #print(for_reduction,end=" - for reduction\n")
        #print(len(np.where(best_rule_matrix==1)[0]))
        #for_reduction[for_reduction==0.0] = 1.0
        #print(for_reduction,end=" - for reduction\n")
        full1 = np.full((total_rows), 1.0,dtype=float)
        for_reduction = full1 - for_reduction
        #print(best_rule_matrix)
        #print(len(np.where(for_reduction==0.1)[0]))
        #print(np.where(rule_matrix[:,5180]==1))

        # if for_reduction = { 1 1 0.5 1} & for_sum = { 1 1 1 1 }
        # then for_sum = { 1 1 0.5 1} <- new rule_selection matrix

        for_sum = np.multiply(for_reduction, for_sum)
        # print(for_sum,end=" - for_sum - \n\n")
        #print((for_sum==for_sum).all(),end=" \n\n")
        

        #print(for_sum)
        #print(len(np.where(for_reduction==1.0)[0]))
        rule_matrix[:,best_rule_loc] = rule_matrix[:,best_rule_loc] * int(0)
        #break
    
    untouched_rows = len(np.where(for_sum == 1.0)[0])
    time.sleep(1) 
    print("\nUntouched_rows:"+str(untouched_rows))
    
    #print("REPETitions detected")
    return rule_set


def main():
    keyword = 'staff'
    depth = 2
    group = '-1'  # 0 for not present | 1 for present | -1 for both

    rules_df = get_rule_coverage.main()


    # selecting rules with precision:1
    rules_df = rules_df.loc[rules_df['precision'] > 0.950]

    aggregate_df = pd.read_csv("./csl_output/workingDB/colgate_workDB.csv")
    rules_df.reset_index(drop=True, inplace=True)
    # testing import
    print(rules_df.head)
    #print(len(aggregate_df))

    total_rows = len(aggregate_df)

    rule_matrix=gen_rule_matrix(rules_df,total_rows)

    print(len(np.where(np.sum(rule_matrix,axis=1) == 0.0)[0]))
    print("DONE HERE")

    rule_list= get_rule_set(rule_matrix,total_rows,1.0,0.5)
    
    rules_df.drop(["coverage"], axis=1, inplace=True)
    selected_rules = rules_df.loc[rule_list]
    #selected_rules.to_csv("./csl_output/rules/spanning_rules/span_aggregate_df_depth_"+str(depth)+"keyword: "+keyword+"_pr",index=False)
    selected_rules.to_csv("./tmep_df.csv",index=False)
    return rules_df



if __name__ == "__main__":
    #doctest.testmod()
    main()