#!/usr/bin/env python3

import argparse
import json
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
import re
import numpy
import time
import logging
#logging.basicConfig(filename="./TO_REMOVE/temp/graph_to_db.log",level=logging.DEBUG,filemode = 'w')

abbreviations = {
    "bldg" : "building",
    "mgmt" : "management",
    "pub" : "public"
}

# list of common keyword beginnings
common_starts = ["student", "ems", "bg", "voip"]

common_delims = ['_', '-', " "]


# function to find stuff like the common_starts elements
def longest_shared_sequence(keyword1,keyword2, shared_seq_dict):
    #shared_seq_dict  # dictionary containing common sequences found and how many times they were found
    longest_shared_seq = ""
    for i in range(len(keyword1)-1):
        for j in range(i+1,len(keyword1)):
            if keyword1[i:j] in keyword2:
                if keyword1[i:j] not in shared_seq_dict:
                    shared_seq_dict[keyword1[i:j]] = 0
                shared_seq_dict[keyword1[i:j]] += 1
                if len(keyword1[i:j])>len(longest_shared_seq):
                    longest_shared_seq = keyword1[i:j]

    #logging.debug("\t\t words:{} {}| seq:{}| ".format(keyword1,keyword2,longest_shared_seq)) #commented out 6/24 11:30am
    return longest_shared_seq
            
def reduce_similarity(word,similar_words, shared_seq_dict, min_len=3):
    to_return = []
    longest_list = []
    longest = ""
    #print(type(similar_words))
    for i in similar_words:
        longest = longest_shared_sequence(word,i,shared_seq_dict)
        if longest not in longest_list:
            longest_list.append(longest)
        if len(longest)>=min_len:
            to_return.append(i)
    to_pop = []
    for seq in shared_seq_dict:
        for lngst in longest_list:
            if (seq in lngst) and (seq != lngst) and (seq not in to_pop) :
                to_pop.append(seq)
    for seq in to_pop:
        shared_seq_dict.pop(seq)
    return to_return

"""Get keywords from a phrase"""
def get_keywords(phrase, delims=[" "]):
    words = re.split("|".join(delims), phrase)
    words = [word.lower() for word in words]

    # Skip stop words
    words = [word for word in words if not word in stopwords.words()]

    # Skip single-character words
    words = [word for word in words if len(word) > 1]

    # Replace abbreviations
    for i in range(len(words)):
        word = words[i]
        if word in abbreviations:
            words[i] = abbreviations[word]
    return words

"""Add keywords to a specific entry in a dictionary"""
def add_keywords(dictionary, key, words):
    if key not in dictionary:
        dictionary[key] = []
    for word in words:
        if word not in dictionary[key]:
            dictionary[key].append(word)




def infer_keywords(file, outf):
    #print("Current working FILE: " + file)
    # Load inverted_table
    with open(file, "r") as infile:
        inverted_table = json.load(infile)

    desc_lst = inverted_table['_description']

    # dictionary -  descriptions are keys and values are lists of keywords
    keyword_dict = {}
    unique_keywords  = []

    for desc in desc_lst:
        delims = []
        if desc!="":
            keywords = get_keywords(desc, common_delims)
            if len(keywords) > 0:
                keyword_dict[desc] = keywords
            else:
                #print("Could not get keywords for description: " + desc)
                keyword_dict[desc]= [desc] # use nltk to break these
            for keyword in keywords:
                if keyword not in unique_keywords:
                    unique_keywords.append(keyword)
        #else:
            #print("Empty description.")

    similarity_dict = {}
    #logging.debug("All he keywords:{}".format(keyword_dict.keys()))
    for word in unique_keywords:
        #logging.debug("\t\tkeywords:{}|\n\t\t\toccurences:{}".format(word,keyword_dict[word]))
        similarity_dict[word] = []
    for i in range(len(unique_keywords)):
        word1 = unique_keywords[i]
        list1 = list(set(word1))
        for j in range(i+1,len(unique_keywords)):
            similarity = 0
            word2 = unique_keywords[j]
            list2 = list(set(word2))
            for el in list1:
                if el in list2:
                    similarity += 1
                if similarity > 1:
                    similarity_dict[word1].append(word2)
                    similarity_dict[word2].append(word1)

    # Checking similarity dict
    new_dict={}
    new_dict2 = {}
    for key in similarity_dict:
        new_dict2[key] = {}
        #logging.debug("Key: " + key)
        #logging.debug("\tList of similar words: " + str(similarity_dict[key]))
        new_dict[key] = reduce_similarity(key,similarity_dict[key], new_dict2[key])
        #logging.debug("\told_list similar words: " + str(similarity_dict[key]))
        #logging.debug("\tUpdated_list similar words: " + str(new_dict[key])) #commented out 6/24 9:50am

    print(new_dict2)



    '''# extract keywords that are variations of a common term (hardcoded in list common_starts on line 17-18)
    common_keyword_dict = {}
    for word2 in common_starts:
        common_keyword_dict[word2] = []

    
    keys_to_remove = []
    for word in keyword_dict:
        for word2 in common_starts:
            if word2 in word:
                if word not in keys_to_remove:
                    keys_to_remove.append(word)
                for iface_or_vlan in keyword_dict[word]:
                    (common_keyword_dict[word2]).append(iface_or_vlan)

    for word in common_keyword_dict:
        keyword_dict[word] = common_keyword_dict[word]

    for word in keys_to_remove:
        keyword_dict.pop(word)

    # final list of keywords for Ifaces and Vlans
    for word in keyword_dict:
        for iName in keyword_dict[word]:
            add_keywords(iface_dict, iName, [word])'''

    with open(outf, 'w') as outfile:
        json.dump(keyword_dict, outfile, indent = 4)

    return keyword_dict

def main():
    start = time.time()
    #parsing command-line arguments
    parser = argparse.ArgumentParser(description='Extract keywords from _description in the inverted symbol table obtained from all the configurations.')
    parser.add_argument('inverted_table_path', help='Path for a file (or directory) containing a JSON representation the inverted symbol table')
    parser.add_argument('out_path', help='Name of file (or directory) to write JSON file(s) containing keywords associated with each description.')

    arguments = parser.parse_args()
    # call function to process description
    infer_keywords(arguments.inverted_table_path, arguments.out_path)

    end = time.time()
    print()
    print("Time taken: " + str(end-start))
    print()


if __name__ == "__main__":
    main()
