import json
import difflib
from difflib import *
import argparse
import os
import logging

def write_details (key, value, stanza_type, change_type, to_return, device):
  '''
  Write details of a specific change, including the stanza type, the change type, and the specific code changed
  '''
  # Details of change
  temp_dict = {}
  temp_dict[key] = value

  # Make details report
  temp_list = [stanza_type, change_type, temp_dict]

  # Update to_return dictionary
  if (device not in to_return.keys()):
    to_return[device] = [temp_list]
  else:
    retrieved_list = to_return[device]
    retrieved_list.append(temp_list)
    to_return[device] = retrieved_list

def diff_in_stanza_type (prior_logs, later_logs, stanza_type):
  '''
  Find all the differences between prior and later in the given stanza type
  Return a dictionary containing all the differences
  Key: Device, Value: list of list, where each nested list contains stanza type, change type, and the specific code changed
  '''

  logging.debug("Diffing {}".format(stanza_type))
  to_return = {}

  # Capture Deletion and Modification
  for (device, details) in prior_logs.items():

     # Deletion of key and corresponding details
    if (device not in later_logs.keys()):
        write_details (device, prior_logs[device], stanza_type, "Deletion", to_return, device)

    # Check for deletions or modification within details
    elif (type(details) == dict):
      for (details_key, details_value) in details.items():

        # Deletion
        if (details_key not in later_logs[device]):
          write_details(details_key, prior_logs[device][details_key], stanza_type, "Deletion", to_return, device)

        # Modification
        elif (details_key in later_logs[device] and later_logs[device][details_key] != details_value):
          temp_tuple = (details_value, later_logs[device][details_key])
          write_details(details_key, temp_tuple, stanza_type, "Modification", to_return, device)

    # Check for modification of single detail
    elif (later_logs[device] != details):
      temp_tuple = (prior_logs[device], later_logs[device])
      write_details (device, temp_tuple, stanza_type, "Modification", to_return, device)
  
  # Capture Addition and Newly Added device
  for (device, details) in later_logs.items():

    # Addition of key and details
    if (device not in prior_logs.keys()):
      write_details (device, later_logs[device], stanza_type, "Addition", to_return, device)
    
    # Check for additions within details
    elif (type(details) == dict):
      for (details_key, details_value) in details.items():
        if (details_key not in prior_logs[device]):
          write_details (details_key, later_logs[device][details_key], stanza_type, "Addition", to_return, device)

  return to_return

def find_diff_between (prior, later):
  '''
  Returns a output dictionary containing all changes between prior and later
  Key: Location, Value: Devices that experienced changes
  '''

  result_dict = {}

  for (stanza_type, logs) in prior.items():
    if (type(logs) == dict and not stanza_type.startswith("AAA")) and stanza_type in later.keys():
      prior_logs = prior[stanza_type]
      later_logs = later[stanza_type]

      temp_dict = diff_in_stanza_type(prior_logs, later_logs, stanza_type)
      result_dict.update(temp_dict)

  return result_dict

def compare (prior, later):
  logging.info("Compare {} to {}".format(prior, later))
  # Turn prior and later into dictionary format
  with open(prior) as prior, open(later) as later:
    try:
      prior = json.load(prior)
    except Exception as ex:
      print("Failed to load:", prior)
      return {}
    try:
      later = json.load(later)
    except Exception as ex:
      print("Failed to load:", later)
      return {}
      
  result_dict = find_diff_between(prior, later)

  # Print Dictionary
  '''for (key, value) in result_dict.items():
    print(key)
    for i in range (len(value)):
      print(value[i])
    print("")'''

  return result_dict

def helper (list1, list2, outfile=None):
  all_diffs = {}
  for i in range(len(list1)):
    output_dict = compare(list1[i], list2[i])
    if len(output_dict) > 0:
      device_name = os.path.basename(list1[i]).split(".")[0]
      all_diffs[device_name] = output_dict

  with open(outfile, 'w') as out:
    json.dump(all_diffs, out, indent=4)

def main():
  '''
  Ask user for two lists of configuration logs as input
  Call the helper function to compare each two configuration logs from the list
  '''
  # Parse command-line arguments
  # Ask user for which two files to process
  parser = argparse.ArgumentParser(description='Commandline arguments')
  parser.add_argument('baseline_path',type=str,
                      help='Path for a baseline directory containing JSON configs')
  parser.add_argument('comparison_path',type=str,
                      help='Path for a comparison directory containing JSON configs')
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

  filenames = sorted(os.listdir(arguments.baseline_path))

  baseline_filenames = [os.path.join(arguments.baseline_path, filename) for filename in filenames]
  baseline_date = os.path.basename(arguments.baseline_path)
  if baseline_date == "":
    baseline_date = os.path.basename(os.path.dirname(arguments.baseline_path))

  comparison_filenames = [os.path.join(arguments.comparison_path, filename) for filename in filenames]
  comparison_date = os.path.basename(arguments.comparison_path)
  if comparison_date == "":
    comparison_date = os.path.basename(os.path.dirname(arguments.comparison_path))

  outfile_name = os.path.join(arguments.output_dir, "{}vs{}.json".format(baseline_date, comparison_date))

  helper(baseline_filenames, comparison_filenames, outfile_name)

if __name__ == "__main__":
  main()