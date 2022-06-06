import json
import filecmp
import difflib
from difflib import *

def make_matrix (all_diffs, stanza_type_dict):
  # Make a dictionary of the stanza types in configuration logs
  # Key: Stanza types, Value: Integers

  '''
  # To change: place holder for 0...
  with open(file1) as f1, open(file2) as f2:
    data1 = json.load(f1)
    data2 = json.load(f2)
  
  # Find the file with more stanza types and construct stanza type dict based on it
  stanza_type_dict = {}
  index = 0

  if (len(data1.keys()) >= len(data2.keys())):
    for (key, value) in data1.items():
      stanza_type_dict[key] = index
      index += 1
  else:
    for (key, value) in data2.items():
      stanza_type_dict[key] = index
      index += 1
  '''

  # Construct the matrix
  output_matrix = []

#  for i in range(len(dict_list)):
  for date, date_diffs in all_diffs.items():
    #input_dict = dict_list[i]
    temp_list = [0] * len(stanza_type_dict.keys())

    for (device_name, device_diffs) in date_diffs.items():
      for (element_name, small_value) in device_diffs.items():

        # Capture multiple changes at same location
        if (len(small_value) < 3): # Not general enough, change later
          for i in range(len(small_value)):
            if (small_value[i][0] in stanza_type_dict):
              temp_list[stanza_type_dict[small_value[i][0]]] = 1
        else:
          if (small_value[0] in stanza_type_dict):
            temp_list[stanza_type_dict[small_value[0]]] = 1

    output_matrix.append(temp_list)

  return output_matrix

def make_dict(input, location):
  output_dict = {}
  temp_dict = {}

  for i in range(len(input)):
    current = input[i]
    key = current[0]

    if (key in temp_dict.keys()):
      current_list = temp_dict[key]
      new_list = [current_list, [current[1], current[2], current[3]]]
      temp_dict[key] = new_list
      output_dict[location] = temp_dict
      
    else:
      value = [current[1], current[2], current[3]]
      temp_dict[key] = value
      output_dict[location] = temp_dict
    
  return output_dict

def extract_change(input):
  for i in range(len(input)):
    current = input[i]
    if (len(current) == 4):
      # Newly Added
      v1 = current[3]
      current.pop(3)
      current.append(v1)
    else:
      v1 = current[3]
      v2 = current[4]

      if (current[2] == "Addition"):
        diff_dict = {}
        for (key, value) in v2.items():
          if (key not in v1.keys()):
            diff_dict[key] = value
      elif (current[2] == "Modification"):
        diff_dict = {}
        for (key, value) in v2.items():
          if (v2[key] != v1[key]):
            temp_list = [v1[key], v2[key]]
            diff_dict[key] = temp_list
      else:
        diff_dict = {}
        for (key, value) in v1.items():
          if (key not in v2.keys()):
            diff_dict[key] = value
      
      current.pop(3)
      current.pop(3)
      current.append(diff_dict)

def classify_difference(input):
  for i in range(len(input)):
    current = input[i]
    if (len(current) == 3):
      current.insert(2, "Newly Added")
    else:
      if (len(current[2].keys()) < len(current[3].keys())):
        # Addition
        current.insert(2, "Addition")
      elif (len(current[2].keys()) == len(current[3].keys())):
        current.insert(2, "Modification")
      else:
        current.insert(2, "Deletion")

def diff_detector (dict1, dict2, section):
  # Do a comparison between dict1 and dict2 for the specific section
  to_return = []

  # Detect Addition, Modification, or Deletion
  for (key, value) in dict1.items():
    if (key in dict2.keys()):
      diff = difflib.Differ().compare(json.dumps(dict1[key]).splitlines(), json.dumps(dict2[key]).splitlines())

      if (len('\n'.join(diff).splitlines()) > 1):
        temp_list = [key, section, dict1[key], dict2[key]]
        to_return.append(temp_list)

  # Detect Newly Added
  for (key, value) in dict2.items():
    if (key not in dict1.keys()):
      temp_list = [key, section, value]
      to_return.append(temp_list)
  
  return to_return

def find_difference_between (file1, file2):
  # The main processor
  # Return a dictionary consisting of all the differences between these two dates
  # Key: Specific Location
  # Value: List of List [[Specific Information of change 1, type, section], [Specific Information of change 2, type, section]]

  with open(file1) as f1, open(file2) as f2:
    data1 = json.load(f1)
    data2 = json.load(f2)

  # Itereate over all the sections (Port, ACL, ...), and get differences in each section
  diff_list = []
  for (key, value) in data1.items():
    if (type(value) == dict and not key.startswith("AAA")):
      dict1 = data1[key]
      dict2 = data2[key]

      temp = diff_detector(dict1, dict2, key)
      diff_list.append(temp)
  
  # Reorganize diff_list
  diff_list_v2 = []
  for i in range(len(diff_list)):
    for j in range(len(diff_list[i])):
      diff_list_v2.append(diff_list[i][j])
  
  # Classify the differences
  classify_difference(diff_list_v2)

  # Get specific information of the change
  extract_change(diff_list_v2)

  # Arrange information into a dictionary
  output_dict = make_dict(diff_list_v2, file1.split(" ")[0])

  return output_dict

def helper (dates, stanza_type_dict):
  # Find difference between configuration logs
  #dict_list = []
  #for i in range(len(list1)):
  #  output_dict = find_difference_between(list1[i], list2[i])
  #  dict_list.append(output_dict)

  all_diffs = {}
  for date in dates:
    with open(date, 'r') as infile:
      date_diffs = json.load(infile)
    all_diffs[date.split('.')[0]] = date_diffs
  
  # Record differences in matrix
  matrix = make_matrix(all_diffs, stanza_type_dict)
  dates = list(all_diffs.keys())
  for i in range(len(dates)):
    print(dates[i],matrix[i])

stanza_type_dict = { "Interface" : 0, "ACL" : 1, "Port" : 2, "System": 3, "VRF": 4 }
dates = ['2021-08-09vs2021-09-09.json', '2021-09-09vs2021-10-09.json', '2021-10-09vs2021-11-09.json', '2021-11-09vs2021-12-09.json']
helper(dates, stanza_type_dict)