import glob
import json
import os
from concurrent.futures import ThreadPoolExecutor

def process_configs(function, in_path, out_path, extra=None):
    print("INPUT: %s OUTPUT: %s" % (in_path, out_path))

    # Check if all arguments are files
    if isinstance(in_path, list):
        all_files = all([os.path.isfile(i) for i in in_path])
    else:
        all_files = os.path.isfile(in_path)

    # Check if all arguments are paths
    all_dirs = os.path.isdir(out_path)
    if isinstance(in_path, list):
        all_dirs = all_dirs and all([os.path.isdir(i) for i in in_path])
    else:
        all_dirs = all_dirs and os.path.isdir(in_path)

    if all_files:
        if (extra is None):
            function(in_path, out_path)
        else:
            function(in_path, out_path, extra)
    elif all_dirs:
        files = glob.glob((in_path[0] if isinstance(in_path, list) else in_path) + '/**/*.json', recursive=True)
        with ThreadPoolExecutor(max_workers=1) as executor:
            futures = []
            for file in sorted(files):
                # Compute paths for specific file
                filename = os.path.basename(file)
                in_filepath = file
                if isinstance(in_path, list):
                    in_filepath = []
                    for i in in_path:
                        in_filepath.append(os.path.join(i, filename))
                out_filepath = os.path.join(out_path, filename)

                # Call function
                if (extra is None):
                    future = executor.submit(function, in_filepath, out_filepath)
                else:
                    future = executor.submit(function, in_filepath, out_filepath, extra)
                futures.append(future)

            # Get results from functions to catch any exceptions
            for future in futures:
                result = future.result()
                if (result is not None):
                    print(result)

    else:
        print("ERROR: input path(s) and output path is a mix of files and directories")


def compute_confidence(numerator, denominator):
    if (denominator > 0):
        return round(numerator / denominator, 3)
    return None 

def create_rule(message, numerator, denominator):
    return {
        "msg" : message,
        "n" : numerator,
        "d" : denominator,
        "c": compute_confidence(numerator, denominator)
    }

'''Writes confidence/support for association rules to JSON file'''
def write_to_outfile(filename, rules):
    with open(filename, 'w') as outfile:         
        json.dump(rules, outfile, indent=4, sort_keys=True)
    return