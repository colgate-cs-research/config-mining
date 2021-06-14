import glob
import os
from concurrent.futures import ThreadPoolExecutor

def process_configs(config_path,out_path, analyze_configuration):
    print("INPUT: "+config_path+" OUTPUT: "+out_path)
    if os.path.isfile(config_path):
        print("Input is a file")
        analyze_configuration(config_path, out_path)
    else:
        if os.path.isdir(out_path):
            files = glob.glob(config_path + '/**/*.json', recursive=True)
            with ThreadPoolExecutor(max_workers=4) as executor:
                for file in sorted(files):
                    executor.submit(analyze_configuration, file, os.path.join(out_path, os.path.basename(file)))
        else:
            print("ERROR: input path is a directory; output path is not a directory")