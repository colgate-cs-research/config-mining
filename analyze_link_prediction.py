import glob
import argparse
import json
import os
import csv

def separate_names(directories, network):
    #RUNLINE = python3 analyze_link_prediction.py /shared/config-mining/output/ northwestern
    directory = os.path.join(directories, network)
    link_prediction = os.path.join(directory, os.listdir(directory)[1])

    f = open("data_link_prediction.csv", 'w')
    writer = csv.writer(f)
    # Make title for columns in csv file
    writer.writerow(["Network", "Device", "Similarity", "Hyperparam name", "Hyperparam value", "Precision", "Recall"])

    for folder in os.listdir(link_prediction):
        device = os.path.join(link_prediction, folder)
        directory = folder

        for files in os.listdir(device):
            items = files.split('_')
            similarity = items[0]
            hyperparam_name = items[1]
            hyperparam_value = items[2][:-4]

            # Opening csv files to read and grab precision and recall values
            file = os.path.join(device, files)
            file1 = open(file, 'r')
            lines = file1.readlines()

            precision_values = lines[-3][0:-1].split(' ')
            recall_values = lines[-2][0:-1].split(' ')
            recall = recall_values[1]

            if precision_values[0] == '':
                precision = 0.00
            else:
                precision = precision_values[1]         
            
            # Writes row with each attribute of the device
            writer.writerow([network, directory, similarity, hyperparam_name, hyperparam_value, precision, recall])
    
def main():
    parser = argparse.ArgumentParser(description='Perform link prediction analysis')
    parser.add_argument('directory', help="Directory to iterate over")
    parser.add_argument('network', help="Network like Northwestern or UW Madison")

    arguments = parser.parse_args()

    separate_names(arguments.directory, arguments.network)

if __name__ == "__main__":
    main()
