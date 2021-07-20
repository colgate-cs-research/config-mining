import glob
import argparse
import json
import os

def separate_names(directories, network):
    #RUNLINE = python3 analyze_link_prediction.py /shared/config-mining/output/ northwestern
    directory = os.path.join(directories, network)

    link_prediction = os.path.join(directory, os.listdir(directory)[1])

    for folder in os.listdir(link_prediction):
        device = os.path.join(link_prediction, folder)
        directory = folder

        for files in os.listdir(device):
            items = files.split('_')
            similarity = items[0]
            hyperparam_name = items[1]
            hyperparam_value = items[2].split('.')[0]
            #print(similarity)
            #print(hyperparam_name)
            #print(hyperparam_value)

            file = os.path.join(device, files)
            file1 = open(file, 'r')
            lines = file1.readlines()
            recall = lines[-2]
            precision = lines[-3]
                
            #print(recall)
            #print(precision)

            

def main():
    parser = argparse.ArgumentParser(description='Perform link prediction analysis')
    parser.add_argument('directory', help="Directory to iterate over")
    parser.add_argument('network', help="Network like Northwestern or UW Madison")

    arguments = parser.parse_args()

    separate_names(arguments.directory, arguments.network)

if __name__ == "__main__":
    main()
