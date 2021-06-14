import glob
import os
from concurrent.futures import ThreadPoolExecutor

def process_configs(config_path,out_path, function, extra=None):
    print("INPUT: "+config_path+" OUTPUT: "+out_path)
    if os.path.isfile(config_path):
        print("Input is a file")
        if (extra is None):
            function(config_path, out_path)
        else:
            function(config_path, out_path, extra)
    else:
        if os.path.isdir(out_path):
            files = glob.glob(config_path + '/**/*.json', recursive=True)
            with ThreadPoolExecutor(max_workers=4) as executor:
                for file in sorted(files):
                    if (extra is None):
                        executor.submit(function, file, os.path.join(out_path, os.path.basename(file)))
                    else:
                        executor.submit(function, file, os.path.join(out_path, os.path.basename(file)), extra)
        else:
            print("ERROR: input path is a directory; output path is not a directory")