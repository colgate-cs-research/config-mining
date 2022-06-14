#!/usr/bin/python3 

import argparse
import os
import pandas
import sys
import datetime
import time
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'libraries', 'contrast'))
#import stucco_parallel1 as stucco
import stucco_parallel2 as stucco
#import stucco as stucco
def update_time_measurement(file_name,depth,keyword,time_taken):
    '''
    Save time measurement to file
    '''
    now = datetime.datetime.now()
    d4 = now.strftime("%d/%m/%Y %H:%M:%S")

    file = open("./csl_runtime_dataset.txt", "a")

    date_entry = "date:"+str(d4)+" | "
    L = date_entry+"input:"+file_name.split("/")[-2] + "/" +file_name.split("/")[-1] +" | " +"depth:"+str(depth)+" | "+"keyword:"+ keyword + " | "+"time_taken:"+ str(time_taken)+"\n"
    file.writelines(L)
    file.close()

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Run Stucco on a dataset')
    parser.add_argument('db_path',type=str, help='Path for a CSV file containing the input data')
    parser.add_argument('rules_path',type=str, help='Path for a CSV file in which to store the rules')
    parser.add_argument('feature',type=str, help='Feature to group by')
    parser.add_argument('-d', '--depth', type=int, default=1, help="Maximum rule depth")
    arguments = parser.parse_args()

    data = pandas.read_csv(arguments.db_path, header=0)
    if arguments.feature not in data.columns:
        print("{} is not a valid feature choice".format(arguments.feature))
        print("You must choose one of the following features: {}".format(", ".join(list(data.columns))))
        sys.exit(1)

    if "filename" in data.columns:
        data.drop("filename", inplace=True, axis=1)

    csl = stucco.ContrastSetLearner(data, group_feature=arguments.feature, max_real_bias=1)
    
    # time measuring
    start_time = time.process_time()
    csl.learn(max_length=arguments.depth)
    # stopping time measurement
    execution_time = time.process_time()-start_time
    # updating time measurement in the 
    update_time_measurement(arguments.db_path,arguments.depth,arguments.feature,execution_time)
    
    results = csl.score(min_lift=0) 
    print(results)

    results.to_csv(arguments.rules_path,index=False)

if __name__ == "__main__":
    main()