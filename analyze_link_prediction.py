import glob
import json
import os

def separate_names():
    directory = '/shared/config-mining/output/northwestern'
    #want to make arguments that put in this directory

    link_prediction = os.path.join(directory, os.listdir(directory)[1])

    for folder in os.listdir(link_prediction):
        device = os.path.join(link_prediction, folder)

        for files in os.listdir(device):
            file = os.path.join(device, files)
            print(file)
            file1 = open(file, 'r')
            lines = file1.readlines()
            print(lines[-2])
            print(lines[-3])
            break
            

def main():
    separate_names()

if __name__ == "__main__":
    main()
