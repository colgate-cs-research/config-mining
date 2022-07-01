import argparse
import logging
import os
import subprocess
import csv

def main():
    # Takes in argument
    parser = argparse.ArgumentParser()
    parser.add_argument('matrix_csv_file')
    parser.add_argument('out_dir')
    args = parser.parse_args()

    # Clean up the SandA list
    #SandA_list = str(args.file.readlines())
    #SandA_list = SandA_list.split(",")
    #SandA_list[len(SandA_list) - 1] = SandA_list[len(SandA_list) - 1][0:-2]
    with open(args.matrix_csv_file, 'r') as csv_file:
        header = csv_file.readline().strip()
        SandA_list = header.split(',')
    
    # Call run_stucco.py with each of the tuple
    for i in range (1, len(SandA_list)):
        subprocess.run(["python3", 
                        "csl/run_stucco.py", 
                        args.matrix_csv_file,
                        
                        os.path.join(args.out_dir, SandA_list[i] + '.csv'),
                        SandA_list[i]])
    
    
if __name__ == "__main__":
    main()