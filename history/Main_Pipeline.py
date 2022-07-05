import argparse
import logging
import os
import subprocess

def main():
  parser = argparse.ArgumentParser(description='Choose from different paths')
  parser.add_argument('paths', choices=['full', 'diffing', 'CSL'], action='store')
  arguments = parser.parse_args()

  if (arguments.paths == "diffing"):
    # Fix hard code here (monthly/daily)
    subprocess.run(["python3", "history/Config_Diffing_Pipeline.py", "input/colgate/daily/2021", "monthly", "output/colgate/", "-vv"])
  elif (arguments.paths == "CSL"):
    CSL_para = argparse.ArgumentParser(description='Choose a threshold')
    CSL_para.add_argument('threshold',type=str)
    threshold=CSL_para.parse_args()

    subprocess.run(["python3", "history/CSL_Pipeline.py", "threshold"])
  else:
    # Fix hard code here (monthly/daily)
    subprocess.run(["python3", "history/Config_Diffing_Pipeline.py", "input/colgate/daily/2021", "monthly", "output/colgate/", "-vv"])
    CSL_para = argparse.ArgumentParser(description='Choose a threshold')
    CSL_para.add_argument('threshold',type=str)
    threshold=CSL_para.parse_args()

    subprocess.run(["python3", "history/CSL_Pipeline.py", "threshold"])

if __name__ == "__main__":
    main()