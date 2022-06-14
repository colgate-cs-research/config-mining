import pandas as pd
import numpy as np
import logging as log
import argparse

# module-wide logging
log.basicConfig(level=log.INFO)
log.getLogger(__name__)

''' Does a column need to be removed?'''
def prune_column(col,threshold):

    (unique_items, counts) = np.unique(col, return_counts=True)
    frequencies = np.asarray((unique_items, counts)).T

    log.debug(" Series->{} ".format(col))
    log.debug(" frequency->\n{} ".format(frequencies))
    
    # one_hot encoded columns
    if len(unique_items)==2 and ('1' and '0' in unique_items):
        log.debug("     ---ONE_HOT_ENCODED--")
        ratio = frequencies[0][1]/frequencies[1][1]
        log.debug("     Ratio->{}".format(ratio))
        if ratio<threshold or ratio>1/threshold:
            return True
    
    return False

''' Remove columns which have ratio belo the threshold'''
def prune_df(df,col_list,threshold=0.001):
    log.info(" prune_df() ->")
    drop_cols=[]
    for col in col_list:
        log.debug(" Col->{} ".format(col))
        log.debug(" df shape->{}".format(df.shape))
        col_array = df[col].astype(str).to_numpy()
        
        if prune_column(col_array,threshold):
            
            log.info("      Dropping column-> {}".format(col))
            drop_cols.append(col)
            
            #df = df.drop(col,axis=1,inplace=True)
    df.drop(drop_cols, axis=1, inplace=True)

    return df

''' Get the file name out of a path'''
def get_filename(path):
    file_plus_ext = path.split("/")[-1] if path.split("/")[-1] is not "" else path.split("/")[-2]
    filename = file_plus_ext.split(".")[0]
    return filename

def main():
    #Parse command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('df_path',type=str, 
            help='Path for a file containing a CSV representation of dataframe')
    parser.add_argument('out_path',type=str, 
            help='Path for a out_file: CSV representation of pruned dataframe')
    arguments=parser.parse_args()

    df = pd.read_csv(arguments.df_path)
    df.fillna("NaN")
    column_list = list(df.columns.values)
    #log.debug("Column list:\n{}\n".format(column_list))

    new_df = prune_df(df,column_list)

    new_df.to_csv(arguments.out_path+get_filename(arguments.df_path)+".csv",index=False)

    

if __name__ == "__main__":
    main()





