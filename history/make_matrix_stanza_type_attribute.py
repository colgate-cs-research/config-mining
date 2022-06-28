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
        # if (out name matches inside name, then go one level deeper)
        # Capture multiple changes at same location
        for i in range(len(small_value)):
          stanza_type = small_value[i][0]
          for (attribute, details) in small_value[i][2].items():
            temp_tuple = (stanza_type, attribute)
            if (temp_tuple in stanza_type_dict):
              logging.debug(temp_tuple)
              temp_list[stanza_type_dict[temp_tuple]] = 1

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

stanza_type_dict = {('System', 'stp_mode'): 0,
                    ('Port', 'lag200'): 1,
                    ('Port', 'port_access_clients_limit'): 2,
                    ('Port', 'vlan_trunks'): 3,
                    ('Port', 'lag31'): 4,
                    ('Port', 'port_access_auth_configurations'): 5,
                    ('VLAN', '2008'): 6, 
                    ('Port', 'loop_protect_vlan'): 7,
                    ('Interface', 'user_config'): 8,
                    ('Port', 'admin'): 9,
                    ('System', 'mstp_config_revision'): 10,
                    ('Interface', 'description'): 11,
                    ('Port', 'vrf'): 12,
                    ('Port', '1/6/41'): 13,
                    ('Port', 'qos_config'): 14,
                    ('Interface', '1/1/31'): 15,
                    ('VRF', 'Tacacs_Server'): 16,
                    ('Port', 'vlan_mode'): 17,
                    ('Port', 'loop_protect_enable'): 18,
                    ('Port', 'stp_config'): 19,
                    ('Port', 'interfaces'): 20,
                    ('Port', '1/1/31'): 21,
                    ('VRF', 'Radius_Server'): 22,
                    ('Port', 'vlan_tag'): 23}

if __name__ == "__main__":
  main(stanza_type_dict)