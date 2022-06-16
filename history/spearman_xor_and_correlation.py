# -*- coding: utf-8 -*-
"""Spearman XOR AND correlation.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1qboZnyCj0-w1NWH83Ov2m1DBy0qybti6
"""

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

def XOR_matrix (matrix, output_matrix):
  for i in range (len(matrix)):
    line = matrix[i]
    for j in range (len(line) - 1):
      for k in range (j + 1, len(line)):
        if (line[j] != line[k]):
          output_matrix[j][k] += 1
          output_matrix[k][j] += 1
  
  return output_matrix

def AND_matrix (matrix, output_matrix):
  for i in range (len(matrix)):
    line = matrix[i]
    for j in range (len(line) - 1):
      for k in range (j + 1, len(line)):
        
        if (line[j] == 1 and line[k] == 1):
          output_matrix[j][k] += 1
          output_matrix[k][j] += 1
  
  return output_matrix

def spearman_matrix(matrix, stanza_type):
  matrix_updated = pd.DataFrame (matrix, columns = stanza_type)
  output_matrix = matrix_updated.corr (method = "spearman")
  return output_matrix

matrix = [[0, 1, 0, 1, 0, 1, 0, 0, 1, 1],
          [0, 1, 0, 1, 0, 1, 0, 0, 1, 1],
          [1, 1, 0, 1, 0, 1, 0, 0, 0, 1],
          [0, 1, 0, 1, 0, 0, 0, 0, 1, 0]]

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

AND_matrix = AND_matrix (matrix, output_matrix)
printout(AND_matrix)