import json
import argparse
import logging
import os

def make_matrix (all_diffs, stanza_type_dict):
  # Construct the matrix
  output_matrix = []

  for (date, date_diffs) in all_diffs.items():
    logging.info("Processing {}...".format(date))
    temp_list = [0] * len(stanza_type_dict.keys())

    for (device_name, device_diffs) in date_diffs.items():
      logging.debug("Processing diffs for {}...".format(device_name))
      for (element_name, small_value) in device_diffs.items():
        # Capture multiple changes at same location
        for i in range(len(small_value)):
          if (small_value[i][0] in stanza_type_dict):
            temp_list[stanza_type_dict[small_value[i][0]]] = 1

    output_matrix.append(temp_list)

  return output_matrix

def main (stanza_type_dict):
  # Parse command-line arguments
  parser = argparse.ArgumentParser(description='Generate matrix of change types')
  parser.add_argument('diffs_dir',type=str,
                      help='Path for a directory containing config diffs')
  parser.add_argument('matrix_file',type=str,
                      help='Path for a JSON file in which to store the matrix')
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

  dates = sorted(os.listdir(arguments.diffs_dir))

  all_diffs = {}
  for date in dates:
    with open(os.path.join(arguments.diffs_dir, date), 'r') as infile:
      date_diffs = json.load(infile)
    all_diffs[date.split('.')[0]] = date_diffs
  
  # Record differences in matrix
  matrix = make_matrix(all_diffs, stanza_type_dict)

  with open(arguments.matrix_file, 'w') as outfile:
    json.dump(matrix, outfile, indent=4)
  
# Hard code stanza type dictionary for now
stanza_type_dict = {"ACL": 0,
                    "Interface": 1,
                    "PKI_TA_Profile": 2,
                    "Port": 3,
                    "SNMP_Trap": 4,
                    "System": 5,
                    "User": 6,
                    "User_Group": 7,
                    "VLAN": 8,
                    "VRF": 9}

if __name__ == "__main__":
  main(stanza_type_dict)