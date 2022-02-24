import json
import glob
import sys
from contrast_set_prog import directory_listing



########################
# DELETE aggreagte.json before compiling
########################

def join_all_files(directory_name):
    
    #looking for JSON files"
    files_in_dir = glob.glob(directory_name+"*.json")
    print(files_in_dir)
    all_file_dict ={'filenames':{}}
    for file in files_in_dir:
        print("Current working file:"+file)
        json_file = open(file,'r')
        file_dict = json.load(json_file)['interfaces'] 
        print("going here too")
        print(file_dict)
        print("\n\n\n\n\n")
        all_file_dict['filenames'][file] = file_dict


    # Dumping the aggregate-files JSON file
    with open("/users/jchauhan/config-mining/csl_output/keywords/aggregate/"+'aggregate_data.json', 'w') as f:
        json.dump(all_file_dict,f, indent=4)

def main():
    join_all_files("/users/jchauhan/config-mining/csl_output/keywords/")


if __name__ == "__main__":
    #doctest.testmod()
    main()
    