import argparse
import logging
import os
import subprocess
import pandas as pd
import glob
import csv

def write_output (data, out_filepath):

    with open(out_filepath, 'w') as csvfile: 
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
    parser = argparse.ArgumentParser("Aggregate a collection of CSL rules into a single file")
    parser.add_argument('csv_dir', type=str, 
        help='Path to directory containing CSV files produced by CSL')
    parser.add_argument('out_file', type=str,
        help='Path to a CSV file in which to store rules above treshold')
    parser.add_argument('threshold',type=str, help='Threshold')
    arguments=parser.parse_args()

    files = glob.glob(arguments.csv_dir+"/*.csv")
    all_data = []
    header = ["rule","group","precision","recall","frequency"] 
    all_data.append(header)
    for file in files:
        data = process_file (file, arguments.threshold)
        all_data.extend(data)
    write_output (all_data, arguments.out_file)

if __name__ == "__main__":
    main()