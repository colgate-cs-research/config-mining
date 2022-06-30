import argparse
import logging
import os
import subprocess

def main():
    # Takes in argument
    parser = argparse.ArgumentParser()
    parser.add_argument('file', type=argparse.FileType('r'))
    args = parser.parse_args()

    # Clean up the SandA list
    SandA_list = str(args.file.readlines())
    SandA_list = SandA_list.split(",")
    SandA_list[len(SandA_list) - 1] = SandA_list[len(SandA_list) - 1][0:-2]
    
    # Call run_stucco.py with each of the tuple
    for i in range (1, len(SandA_list)):
        subprocess.run(["python3", 
                        "csl/run_stucco.py", 
                        "config_history_stats/144_SandA_Updated.csv",
                        "output/run_stucco_result",
                        SandA_list[i]])

if __name__ == "__main__":
    main()