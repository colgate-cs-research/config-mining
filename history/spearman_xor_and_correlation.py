import argparse
import json
import logging
import pandas as pd

def printout (matrix):
  stanza_type = ["ACL           ",
                 "Interface     ",
                 "PKI_TA_Profile",
                 "Port          ",
                 "SNMP_Trap     ",
                 "System        ",
                 "User          ",
                 "User_Group    ",
                 "VLAN          ",
                 "VRF           "]

  for i in range(len(stanza_type)):
    print(stanza_type[i], matrix[i])
  print("")

def generate_XOR_matrix (matrix, output_matrix):
  for i in range (len(matrix)):
    line = matrix[i]
    for j in range (len(line) - 1):
      for k in range (j + 1, len(line)):
        if (line[j] != line[k]):
          output_matrix[j][k] += 1
          output_matrix[k][j] += 1
  
  return output_matrix

def generate_AND_matrix (matrix, output_matrix):
  for i in range (len(matrix)):
    line = matrix[i]
    for j in range (len(line) - 1):
      for k in range (j + 1, len(line)):
        
        if (line[j] == 1 and line[k] == 1):
          output_matrix[j][k] += 1
          output_matrix[k][j] += 1
  print(output_matrix)
  return output_matrix

def spearman_matrix(matrix, stanza_type):
  matrix_updated = pd.DataFrame (matrix, columns = stanza_type)
  output_matrix = matrix_updated.corr (method = "spearman")
  return output_matrix

def main():
  # Parse command-line arguments
  parser = argparse.ArgumentParser(description='Generate matrix of change types')
  parser.add_argument('matrix_file',type=str,
                      help='Path for a JSON file containing a matrix')
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

  with open(arguments.matrix_file, 'r') as infile:
    input_matrix = json.load(infile)
  
  output_matrix = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]

  stanza_type = ["ACL",
                "Interface",
                "PKI_TA_Profile",
                "Port",
                "SNMP_Trap",
                "System",
                "User",
                "User_Group",
                "VLAN",
                "VRF"]

  # spearman_matrix = spearman_matrix (matrix, stanza_type)
  # print(spearman_matrix)

  # XOR_matrix = XOR_matrix (matrix, output_matrix)
  # printout(XOR_matrix)

  AND_matrix = generate_AND_matrix (input_matrix, output_matrix)
  printout(AND_matrix)
  

if __name__ == "__main__":
  main()