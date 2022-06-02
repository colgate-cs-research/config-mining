!pip install jsondiff
import json
import filecmp
import difflib
from difflib import *
import jsondiff as jd
from jsondiff import diff

def write_report(input_dict, file1, file2):
  # Initialize the report
  outfile = open("Change between " + file1.split(" ")[1].split(".")[0] + " and " + file2.split(" ")[1].split(".")[0] + " at " + file1.split(" ")[0], "w")

  # Record changes in file
  for (key, value) in input_dict.items():
    for (specific_location, current_list) in value.items():
      if (len(current_list) < 3):
        for i in range (len(current_list)):
          outfile.write(current_list[i][1] + " at " + specific_location + " in " + current_list[i][0] + "\n")
          outfile.write("Details: " + json.dumps(current_list[i][2]) + "\n\n")
      else:
        outfile.write(current_list[1] + " at " + specific_location + " in " + current_list[0] + "\n")
        outfile.write("Details: " + json.dumps(current_list[2]) + "\n\n")

  outfile.close()

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

  # Write Report
  write_report(output_dict, file1, file2)

def helper (list1, list2):
  for i in range(len(list1)):
    find_difference_between(list1[i], list2[i])

date_8_9 = ['49broad 8_9.json', 'case-247 8_9.json', 'townhouse1 8_9.json']
date_12_4 = ['49broad 12_4.json', 'case-247 12_4.json', 'townhouse1 12_4.json']
helper(date_8_9, date_12_4)