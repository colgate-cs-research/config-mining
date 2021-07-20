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
    writer.writerow(["Network", "Device", "Similarity", "Hyperparam name", "Hyperparam value", "Precision", "Recall"])

    for folder in os.listdir(link_prediction):
        device = os.path.join(link_prediction, folder)
        directory = folder


        for files in os.listdi
        r(device):
            items = files.split('_')
            similarity = items[0]
            hyperparam_name = items[1]
            hyperparam_value = items[2].split('.')[0]


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
            
            writer.writerow([network, directory, similarity, hyperparam_name, hyperparam_value, precision, recall])
    
def main():
    parser = argparse.ArgumentParser(description='Perform link prediction analysis')
    parser.add_argument('directory', help="Directory to iterate over")
    parser.add_argument('network', help="Network like Northwestern or UW Madison")

    arguments = parser.parse_args()

    separate_names(arguments.directory, arguments.network)

    #printing data
    '''
    print(network)
    print(directory)
    print(similarity)
    print(hyperparam_name)
    print(hyperparam_value)
    print(precision)
    print(recall)
    '''

if __name__ == "__main__":
    main()
