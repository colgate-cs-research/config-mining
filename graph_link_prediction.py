import csv
import pandas as pd
from matplotlib import pyplot as plt

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
def graph_data(x_values, y_values):
    # grabbing titles of names list.name
    plt.plot(x_values, y_values)
    plt.xlabel(x_values.name)
    plt.ylabel(y_values.name)

    plt.savefig("graph.png")

def main():
    csv_file = "data_link_prediction.csv"
    df = pd.read_csv(csv_file)
    #print(df.head())

    #grab unique pairs of Hyperparam name and Similarity
    variants = df.loc[:,["Hyperparam name", "Similarity"]].drop_duplicates()

    # Iterate over each unique hyperparam, similarity pair
    for _, row in variants.iterrows():
        hyperparam = row["Hyperparam name"]
        similarity = row["Similarity"]
        print(hyperparam, similarity)

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
            plt.plot(device_filtered["Hyperparam value"], device_filtered["Precision"], label=device + " precision", linestyle='solid')
            plt.plot(device_filtered["Hyperparam value"], device_filtered["Recall"], label=device + " recall", linestyle='dashed')

        # Add labels to graph
        plt.xlabel(row["Hyperparam name"])
        plt.ylabel("Precision/Recall")
        plt.legend()

        # Save graph
        filename = "output/graphs/graph_" + hyperparam + "_" + similarity + ".png"
        plt.savefig(filename)
    #print(devices)
    #plt.plot(filtered["Hyperparam value"], filtered["Precision"], label="Precision")

if __name__ == "__main__":
    main()

        #precision_list = get_columns_csv("data_link_prediction.csv", "Precision")
        #recall_list = get_columns_csv("data_link_prediction.csv", "Recall")
        #hyperparam_name = get_columns_csv("data_link_prediction.csv", "Hyperparam name")

  