import json
import argparse
import logging
import os

def make_matrix (all_diffs, device_dict):
    output_matrix = []

    for (date, date_diffs) in all_diffs.items():
        temp_list = [0] * len(device_dict.keys())
        for (device_name, device_diffs) in date_diffs.items():
            if (device_name in device_dict):
                temp_list[device_dict[device_name]] = 1
        output_matrix.append(temp_list)

    return output_matrix

def make_device_dict (input):
    device_dict = {}
    index = 0
    
    for value in input:
        device_dict[value] = index
        index += 1
    
    return device_dict

def clean_up_device_list (input):
    device_list = set()
    for i in range (len(input)):
        for device in input[i]:
            device_list.add(device)
    
    return device_list


def get_device_list (data):
    device_list = set()
    for (device, details) in data.items():
        device_list.add(device)
    
    return device_list

def main ():
    parser = argparse.ArgumentParser(description='Make Device Diffing Matrix')
    parser.add_argument('diffs_dir',type=str, help='Path for a directory containing config diffs')
    parser.add_argument('matrix_file',type=str, help='Path for a JSON file in which to store the matrix')
    parser.add_argument('-v', '--verbose', action='count', help="Display verbose output", default=0)
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
    device_list = []
    device_list_cleaned = []

    for current in dates:
        with open(os.path.join(arguments.diffs_dir, current), 'r') as file:
            data = json.load(file)

            current = get_device_list (data)
            device_list.append(current)
            
            device_list_cleaned = clean_up_device_list(device_list)

    device_dict = make_device_dict(device_list_cleaned)

    all_diffs = {}
    for current in dates:
        with open(os.path.join(arguments.diffs_dir, current), 'r') as infile:
            date_diffs = json.load(infile)
        all_diffs[current.split('.')[0]] = date_diffs
    
    matrix = make_matrix(all_diffs, device_dict)

    with open(arguments.matrix_file, 'w') as outfile:
        json.dump(matrix, outfile, indent=4)

if __name__ == "__main__":
  main()