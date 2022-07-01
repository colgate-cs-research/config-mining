import argparse
import logging
import os
import subprocess
import pandas as pd
import glob
import csv

def write_output (data):

    with open("output/colgate/CSL_cleaned.csv", 'w') as csvfile: 
        # creating a csv writer object 
        csvwriter = csv.writer(csvfile) 

        # writing the data rows 
        csvwriter.writerows(data)
        

def process_file (file, threshold):
    # Open and read the csv file
    csvreader = csv.reader(open(file))

    rows = []
    for row in csvreader:
        if (row[2] >= threshold and row[1][-1] == '1'):
            rows.append(row)
    
    return rows

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('threshold',type=str, help='Threshold')
    arguments=parser.parse_args()

    files = glob.glob("output/colgate/run_stucco_result/*.csv")
    all_data = []
    for file in files:
        data = process_file (file, arguments.threshold)
        all_data.extend(data)
    
    write_output (all_data)

if __name__ == "__main__":
    main()