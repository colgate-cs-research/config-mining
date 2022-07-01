import json
import argparse
import logging
import os
import csv

def make_SandA_dict(SandA):
  SandA_dict = {}
  index = 0
  for value in SandA:
    SandA_dict[value] = index
    index += 1
  return SandA_dict

'''
Extract SandA
'''
def clean_up (input_list):
  output_set = set()
  for i in range (len(input_list)):
    for value in input_list[i]:
      output_set.add(value)
  
  return output_set

def process (data):
  output_set = set()
  for (location, device) in data.items():
    for (key, values) in device.items():
      for i in range (len(values)):
        for (attribute, others) in values[i][2].items():
          if (key == attribute and values[i][0] != 'System'):
            for (a, details) in values[i][2].items():
              for (meat, b) in details.items():
                output_set.add((values[i][0],meat))
          else:
            output_set.add((values[i][0], attribute))
  
  return output_set

'''
Make Matrix
'''
def make_matrix (all_diffs, stanza_type_dict):
# Construct the matrix
  output_matrix = []

  header = [''] * len(stanza_type_dict.keys())
  for stanza_type, index in stanza_type_dict.items():
    header[index] = ":".join(stanza_type)
  header = ['date'] + header
  output_matrix.append(header)

  for (date, date_diffs) in all_diffs.items():
    logging.info("Processing {}...".format(date))
    temp_list = [0] * len(stanza_type_dict.keys())

    for (device_name, device_diffs) in date_diffs.items():
      logging.debug("Processing diffs for {}...".format(device_name))
      for (element_name, small_value) in device_diffs.items():
        for i in range(len(small_value)):
          stanza_type = small_value[i][0]
          for (attribute, details) in small_value[i][2].items():
            temp_tuple = (stanza_type, attribute)
            if (temp_tuple in stanza_type_dict):
              logging.debug(temp_tuple)
              temp_list[stanza_type_dict[temp_tuple]] = 1

    output_matrix.append([date] + temp_list)

  return output_matrix

def main ():
  parser = argparse.ArgumentParser(description='Extract SandA from config diffs')
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

  result_list = []
  for current in dates:
    with open(os.path.join(arguments.diffs_dir, current), 'r') as file:
      data = json.load(file)
      # Extract all the stanza type + attribute from the current config diffing result file
      result = process (data)
      result_list.append(result)

  # Clean up the "result"
  SandA = clean_up (result_list)
  SandA_dict = make_SandA_dict(SandA)
  print(SandA_dict)

  parser = argparse.ArgumentParser(description='Generate matrix of change types')

  all_diffs = {}
  for date in dates:
    with open(os.path.join(arguments.diffs_dir, date), 'r') as infile:
      date_diffs = json.load(infile)
    all_diffs[date.split('.')[0]] = date_diffs
  
  # Record differences in matrix
  matrix = make_matrix(all_diffs, SandA_dict)

  with open(arguments.matrix_file, 'w') as outfile:
    writer = csv.writer(outfile)
    writer.writerows(matrix)
#    json.dump(matrix, outfile, indent=4)

if __name__ == "__main__":
  main()