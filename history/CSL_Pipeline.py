import argparse
import logging
import os
import subprocess

def main():
  # Run CSL
  parser = argparse.ArgumentParser(description='Run full CSL pipeline')
  parser.add_argument('threshold',type=str)
  arguments=parser.parse_args()

  logging.debug("Run CSL Generate Files relying on run_stuccco.py")
  subprocess.run(["python3", "history/CSL_generate_files.py", "shared/colgate/diffs/daily_SandA.csv", "shared/colgate/diffs/SandA_csl"])

  logging.debug("Run CSL Threshold")
  subprocess.run(["python3", "history/CSL_Threshold.py", "shared/colgate/diffs/SandA_csl", "shared/colgate/diffs/SandA_csl.csv", arguments.threshold])
  
  logging.debug("Run CSL Anomalies")
  subprocess.run(["python3", "history/CSL_anomalies.py", "shared/colgate/diffs/daily_SandA.csv", "shared/colgate/diffs/SandA_csl.csv", "shared/colgate/diffs/SandA_csl_anomalies.csv"])

if __name__ == "__main__":
    main()

# Try to understand the anomolies
# On which devices is there a chnage
# What triggered the anamolies
