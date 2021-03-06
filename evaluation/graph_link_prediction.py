import csv
import pandas as pd
from matplotlib import pyplot as plt
import argparse

# Grabs specific columns to analyze
def get_columns_csv(txt, title, variation=None):
    with open(txt) as csv_file:
        reader = csv.reader(csv_file, delimiter=',')
        rows = list(reader)
        col_list = rows[0]

        df = pd.read_csv(txt, usecols=col_list)
        title_list = df[title]

        filtered = df.loc[df["Hyperparam name"] == "thresh", ["Hyperparam value", "Precision"]]
        
    return title_list

# Graphs the x and y coordinates as given
def graph_data(csv_file, network):
    df = pd.read_csv(csv_file)

    #grab unique pairs of Hyperparam name and Similarity
    variants = df.loc[:,["Hyperparam name", "Similarity"]].drop_duplicates()

    # Iterate over each unique hyperparam, similarity pair
    for _, row in variants.iterrows():
        hyperparam = row["Hyperparam name"]
        similarity = row["Similarity"]

        #isolating data for specific hyperparam and similarity
        filtered = df.loc[
            (df["Hyperparam name"] == hyperparam) & (df["Similarity"] == similarity),
            ["Hyperparam value", "Precision", "Recall", "Device"]]
        filtered = filtered.sort_values("Hyperparam value")

        # New graph
        plt.clf()

        # Add line for each device
        devices = filtered["Device"].unique()
        for device in devices:
            device_filtered = filtered.loc[filtered["Device"] == device,:]
            param_values = list(device_filtered["Hyperparam value"])
            bar_locs = list(range(len(param_values)))
            plt.bar([x - .15 for x in bar_locs], device_filtered["Precision"], width=0.3, color='r', label=device + " precision")
            plt.bar([x + .15 for x in bar_locs], device_filtered["Recall"], width=0.3, color='b', label=device + " recall")

        # Add labels to graph
        plt.xticks(bar_locs, param_values)
        plt.xlabel(hyperparam)
        plt.ylabel("Precision/Recall")
        plt.legend()

        # Save graph
        # filename = "output/graphs/graph_" + hyperparam + "_" + similarity + ".png"
        filename = "output/" + network + "/analysis/graph_" + hyperparam + "_" + similarity + ".png"
        plt.savefig(filename)

def main():
    parser = argparse.ArgumentParser(description='graph link prediction analysis')
    parser.add_argument('network', help="Network like Northwestern or UW Madison")
    arguments = parser.parse_args()
    csv_file = "data_link_prediction_" + arguments.network + ".csv"
    graph_data(csv_file, arguments.network)
    
    #print(devices)
    #plt.plot(filtered["Hyperparam value"], filtered["Precision"], label="Precision")
    
if __name__ == "__main__":
    main()