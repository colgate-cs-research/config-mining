import glob
import json
import os
from concurrent.futures import ThreadPoolExecutor

def determine_path_types(in_path, out_path):
    # Check if all arguments are files
    if isinstance(in_path, list):
        all_files = all([os.path.isfile(i) for i in in_path])
    else:
        all_files = os.path.isfile(in_path)

    # Check if all arguments are paths
    all_dirs = os.path.isdir(out_path) or (not os.path.exists(out_path))
    if isinstance(in_path, list):
        all_dirs = all_dirs and all([os.path.isdir(i) or (not os.path.exists(out_path)) for i in in_path])
    else:
        all_dirs = all_dirs and (os.path.isdir(in_path) or (not os.path.exists(out_path)))

    return all_files, all_dirs

def determine_filepaths(in_path, out_path):
    in_filepaths = []
    out_filepaths = []

    all_files, all_dirs = determine_path_types(in_path, out_path)

    if all_files:
        in_filepaths = [in_path]
        out_filepaths = [out_path]
    elif all_dirs:
        files = glob.glob((in_path[0] if isinstance(in_path, list) else in_path) + '/**/*.json', recursive=True)
        for file in sorted(files):
            # Compute paths for specific file
            filename = os.path.basename(file)
            in_filepath = file
            if isinstance(in_path, list):
                in_filepath = []
                for i in in_path:
                    in_filepath.append(os.path.join(i, filename))
            in_filepaths.append(in_filepath)
            out_filepaths.append(os.path.join(out_path, filename))
    else:
        print("ERROR: input path(s) and output path is a mix of files and directories")

    return in_filepaths, out_filepaths

def process_configs(function, in_path, out_path, extra=None, generate_global=False):
    print("INPUT: %s OUTPUT: %s" % (in_path, out_path))
    in_filepaths, out_filepaths = determine_filepaths(in_path, out_path)

    with ThreadPoolExecutor(max_workers=1) as executor:
        futures = []
        #individual configs
        for i in range(len(in_filepaths)):
            in_filepath = in_filepaths[i]
            out_filepath = out_filepaths[i]

            # Call function
            if generate_global:
                in_filepath = [in_filepath]
            future = executor.submit(function, in_filepath, out_filepath, extra)
            futures.append(future)
        
        #aggregate
        if len(in_filepaths) > 1 and generate_global:
            out_filepath = os.path.join(out_path, "network.json") 
            future = executor.submit(function, in_filepaths, out_filepath, extra)

        # Get results from functions to catch any exceptions
        for future in futures:
            result = future.result()
            if (result is not None):
                print(result)

def compute_confidence(numerator, denominator):
    if (denominator > 0):
        return round(numerator / denominator, 3)
    return None 

def create_rule(message, numerator, denominator, exceptions=None):
    rule = {
        "msg" : message,
        "n" : numerator,
        "d" : denominator,
        "c": compute_confidence(numerator, denominator)
    }
    if exceptions is not None:
        rule["except"] = exceptions
    return rule

'''Writes confidence/support for association rules to JSON file'''
def write_to_outfile(filename, rules):
    dirpath = os.path.dirname(filename)
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    with open(filename, 'w') as outfile:         
        json.dump(rules, outfile, indent=4, sort_keys=True)
    return