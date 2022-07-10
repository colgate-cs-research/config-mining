import json
import argparse
import logging
import os
# import csv
import pprint

def write_file (input_dict, option, path):
    file_name = ""
    if (option == '1'):
        file_name = "Count_Frequency_Stanza_Only.txt"
    else:
        file_name = "Count_Frequency_SandA.txt"
    
    with open(path, "w") as outfile:
        for (key, value) in input_dict.items():
            outfile.write('%s:%s\n' % (key, value))
    
    outfile.close()

def sort_dict (raw_dict):
    sorted_values = sorted(raw_dict.values(), reverse = True) # Sort the values
    sorted_dict = {}
    
    for i in sorted_values:
        for k in raw_dict.keys():
            if raw_dict[k] == i:
                sorted_dict[k] = raw_dict[k]
                break
    
    return sorted_dict

def count_frequency (list):
    SandA_dict = {}
    
    for i in range (len(list)):
        current_set = list[i]
        for value in current_set:
            if (value in SandA_dict.keys()):
                count = SandA_dict[value]
                count += 1
                SandA_dict[value] = count
            else:
                SandA_dict[value] = 1

    return SandA_dict

def process_stanza_only (data):
    output_set = set()

    # Iterate over each device
    for (location, device) in data.items():

        # Iterate over each stanza
        for (stanza_name, changes) in device.items():
            
            # Iterate over each change
            for i in range (len(changes)):
                stanza_type = changes[i][0]
                output_set.add(stanza_type)

    return output_set

def process_SandA (data):
    output_set = set()

    # Iterate over each device
    for (location, device) in data.items():
        
        # Iterate over each stanza
        for (stanza_name, changes) in device.items():
            
            # Iterate over each change
            for i in range (len(changes)):
                stanza_type = changes[i][0]
                
                # Iterate over each attribute
                for (attribute, details) in changes[i][2].items():
                    if (stanza_name == attribute and stanza_type != 'System'):
                        logging.debug("Special case: {} > {} > {} {}".format(location, stanza_name, stanza_type, attribute))
                        for inner_attribute in details:
                            output_set.add((stanza_type, inner_attribute))
                    else:
                        output_set.add((stanza_type, attribute))
    return output_set
  
def main ():
    parser = argparse.ArgumentParser(description='Count frequency of stanza types in config diffs dataset')
    parser.add_argument('diffs_dir',type=str,help='Path for a directory containing config diffs')
    parser.add_argument('output_path',type=str,help='Path for a JSON file in which to store the result')
    parser.add_argument('option',type=str,help='Option 1: stanza type only, Option 2: SandA')
    parser.add_argument ('-v', '--verbose', action='count', help="Display verbose output", default=0)
    arguments=parser.parse_args()
    
    # Configure logging
    if (arguments.verbose == 0):
        logging.basicConfig(level=logging.WARNING)
    elif (arguments.verbose == 1):
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)
    logging.getLogger(__name__)
    
    dates = sorted(os.listdir(arguments.diffs_dir))
    result_list = []
    
    for current in dates:
        with open(os.path.join(arguments.diffs_dir, current), 'r') as file:
            data = json.load(file)
            # Extract all the stanza type + attribute from the current config diffing result file
            if (arguments.option == '1'):
                # stanza type only
                result = process_stanza_only (data)
                logging.debug(current)
                logging.debug(pprint.pformat(result))
                result_list.append(result)
            else:
                # SandA
                result = process_SandA (data)
                logging.debug(current)
                logging.debug(pprint.pformat(result))
                result_list.append(result)
    
    raw_dict = count_frequency (result_list)
    sorted_dict = sort_dict (raw_dict)
    write_file (sorted_dict, arguments.option, arguments.output_path)

if __name__ == "__main__":
    main()