import argparse
import logging
import os
import subprocess

def main():
  # Parse command-line arguments
  # Ask user for which two files to process
  parser = argparse.ArgumentParser(description='Run full config history pipeline')
  parser.add_argument('year_dir',type=str,
                      help='Path for a directory containing a year of daily snapshots')
  parser.add_argument('frequency', choices=['daily', 'weekly', 'monthly'], action='store')
  parser.add_argument('output_dir',type=str,
                      help='Path for a directory in which to store file of differences')
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

  # Identify dates to diff
  all_dates = []
  if (arguments.frequency == "daily"):
    months = sorted(os.listdir(arguments.year_dir))
    for month in months:
        dates_in_month = sorted(os.listdir(os.path.join(arguments.year_dir, month)))
        all_dates.extend(dates_in_month)
  elif(arguments.frequency == "monthly"):
    months = sorted(os.listdir(arguments.year_dir))
    dates_in_first_month = sorted(os.listdir(os.path.join(arguments.year_dir, months[0])))
    first_date = dates_in_first_month[0]
    year = first_date.split("-")[0]
    day = first_date.split("-")[2]
    for month in months:
        all_dates.append("{}-{}-{}".format(year, month, day))
  logging.info(all_dates)

  # Prepare output directory
  diffs_dir = os.path.join(arguments.output_dir, arguments.frequency)
  os.makedirs(diffs_dir, exist_ok=True)

  # Diff sequential dates
  for i in range(len(all_dates)-1):
    baseline = all_dates[i]
    baseline_dir = os.path.join(arguments.year_dir, baseline.split("-")[1], baseline)
    comparison = all_dates[i+1]
    comparison_dir = os.path.join(arguments.year_dir, comparison.split("-")[1], comparison)
    logging.debug("Compare {} to {}".format(baseline_dir, comparison_dir))
    subprocess.run(["python3", "history/configs_diff_v2.py", baseline_dir, comparison_dir, diffs_dir])

  # Generate matrix
  logging.debug("Generate matrix")
  matrix_file = os.path.join(arguments.output_dir, arguments.frequency + ".json")
  # subprocess.run(["python3", "history/make_matrix.py", diffs_dir, matrix_file])
  subprocess.run(["python3", "history/make_matrix_stanza_type_attribute.py", diffs_dir, matrix_file])
  

  # Run correlation
  logging.debug("Run correlation")
  subprocess.run(["python3", "history/spearman_xor_and_correlation.py", matrix_file])



if __name__ == "__main__":
    main()