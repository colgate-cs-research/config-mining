import json
import glob
import sys
import logging

# module-wide logging
logging.basicConfig(level=logging.WARNING)
logging.getLogger(__name__)

########################
# DELETE aggreagte.json before compiling
########################
def directory_listing(directory_address):
    """
    Listing all the items in a given directory
    @returns: ['file1_Addr','file2_address'] 
    """
    if directory_address[-1] == '/':
        list = glob.glob(directory_address+"*.json")
    else:
        list = glob.glob(directory_address+"/*.json")
    return list

def glob_helper(directory):
    # helper for the presence/absebce of / at the end of the dirtcory list
    if directory[-1] == '/':
        directory = directory+"*.json"
    else:
        directory = directory+"/*.json"
    return directory

def join_all_files(directory_name=None,directory_list=None):
    logging.warning("#### join_all_files  ####  args: (directory_name=None, directory_list=None) ")
    # logging.debug("i={}; n(matrix)={:,}".format(i, len(self.counts)))
    #Checking mode of input
    if(directory_name!=None):
        logging.info("     directory_name is not empty")
        files_in_dir = glob.glob(glob_helper(directory_name))
    elif(directory_list!=None and directory_name==None):
        logging.info("     directory_list is not empty")
        files_in_dir = directory_list
    else:
        logging.info("Coding is a sacm")
    # CHECK
    # checking if the files are not empty
    logging.info("      n(files_in_dir)={}".format(len(files_in_dir)))
    

    all_file_dict ={'filenames':{}}
    for file in files_in_dir:
        file_name = file.split("/")[-1]
        logging.info("          Current working file:{}".format(file))
        json_file = open(file,'r')
        file_dict = json.load(json_file)['interfaces'] 
        
        logging.debug("the dictionary for the file:\n{}".format(file_dict))
        all_file_dict['filenames'][file_name] = file_dict

    logging.info("  Completed file aggregation; Now dumping file into:{}".format("/users/jchauhan/config-mining/csl_output/keywords/aggregate/aggregate_data.json"))
    logging.debug("all_file_dict:{}".format(all_file_dict))
    # Dumping the aggregate-files JSON file
    with open("/users/jchauhan/config-mining/csl_output/keywords/aggregate/"+'aggregate_data.json', 'w') as f:
        json.dump(all_file_dict,f, indent=4)

def main():
    join_all_files("/users/jchauhan/config-mining/csl_output/keywords/")


if __name__ == "__main__":
    #doctest.testmod()
    main()
    