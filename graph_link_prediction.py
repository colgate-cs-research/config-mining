import csv
import pandas as pd
from matplotlib import pyplot as plt

def get_columns_csv(txt, title, variation=None):
    with open(txt) as csv_file:
        reader = csv.reader(csv_file, delimiter=',')
        rows = list(reader)
        col_list = rows[0]

        df = pd.read_csv(txt, usecols=col_list)
        title_list = df[title]
        
        #TRYING TO GRAB JUST THE THRESHOLDS etc
        '''
        if variation != None:
            variation_list = []
            for word in title_list:
                if 
        '''
    return title_list

def graph_data(x_values, y_values):
    #grabbing titles of names list.name
    plt.plot(x_values, y_values)
    plt.xlabel(x_values.name)
    plt.ylabel(y_values.name)

    plt.savefig("graph.png")

def main():
    precision_list = get_columns_csv("data_link_prediction.csv", "Precision")
    recall_list = get_columns_csv("data_link_prediction.csv", "Recall")
    hyperparam_name = get_columns_csv("data_link_prediction.csv", "Hyperparam name")

    #graph_data(precision_list, recall_list)

if __name__ == "__main__":
    main()







#These methods return as a list
'''
def read_csv(txt, title):
    with open(txt) as csv_file:
        reader = csv.reader(csv_file, delimiter=',')
        index = find_index(txt, title)
        title_list = []
        for row in reader:
            title_list.append(row[index])
    return title_list

def find_index(txt, title):
    with open(txt) as csv_file:
        reader = csv.reader(csv_file, delimiter=',')
        rows = list(reader)
        for word in rows[0]:
            if word == title:
                return rows[0].index(title)
    return -1
'''