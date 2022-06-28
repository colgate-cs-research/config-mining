import json

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
      # one thing is the key
      # the other is the 
      for i in range (len(values)):
        for (attribute, others) in values[i][2].items():
          if (key == attribute and values[i][0] != 'System'):
            # this is where we go one level deeper
            for (a, details) in values[i][2].items():
              for (meat, b) in details.items():
                output_set.add((values[i][0],meat))
          else:
            # otherwise dont
            output_set.add((values[i][0], attribute))
  
  return output_set

def main (file_list):
  result_list = []
  for i in range (len(file_list)):
    with open(file_list[i]) as file:
      data = json.load(file)
      # Extract all the stanza type + attribute from the current config diffing result file
      result = process (data)
      result_list.append(result)

  # Clean up the "result"
  final = clean_up (result_list)
  print(final)
  return final

if __name__ == "__main__":
  file_list = ["2021-08-09vs2021-09-09.json",
               "2021-09-09vs2021-10-09.json",
               "2021-10-09vs2021-11-09.json",
               "2021-11-09vs2021-12-09.json"]

  # file_list = ["2021-10-09vs2021-11-09.json"]
  main(file_list)