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
def longest_shared_sequence(keyword1,keyword2, k1_shared_seq_dict, k2_shared_seq_dict, min_len):
    #shared_seq_dict  # dictionary containing common sequences found and how many times they were found
    longest_shared_seq = ""
    for i in range(len(keyword1)-1):
        for j in range(i+min_len,len(keyword1)):
            seq = keyword1[i:j+1]
            if seq in keyword2:
                if seq not in k1_shared_seq_dict:
                    k1_shared_seq_dict[seq] = 0
                if seq not in k2_shared_seq_dict:
                    k2_shared_seq_dict[seq] = 0
                k1_shared_seq_dict[seq] += 1
                k2_shared_seq_dict[seq] += 1
                if len(seq)>len(longest_shared_seq):
                    longest_shared_seq = seq
    return longest_shared_seq
            
def reduce_similarity(word,similar_words, all_shared_seq_dict, min_len=3):
    to_return = []
    longest = ""
    for similar_word in similar_words:
        longest = longest_shared_sequence(word, similar_word, all_shared_seq_dict[word], all_shared_seq_dict[similar_word], min_len)
        if longest not in to_return:
            to_return.append(longest)
    for word2 in to_return:
        if word2!="":
            other_words = word.split(word2)
            for word3 in other_words:
                if word3 not in all_shared_seq_dict[word]:
                    all_shared_seq_dict[word][word3] = 0
    return to_return

def de_num(d):
    to_change = []
    for key in d:
        new_key = ""
        num_count= 0
        for el in key:
            if (not el.isdigit()):
                new_key += el
            else:
                num_count+=1
        if (new_key!=key) and (num_count!=len(key)):
            to_change.append((key, new_key))
    for (key,new_key) in to_change:
        pass
        d[new_key] = d[key]
        d.pop(key)


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




def infer_keywords(file, outf, outf2):
    #print("Current working FILE: " + file)
    # Load inverted_table
    with open(file, "r") as infile:
        inverted_table = json.load(infile)

    desc_lst = inverted_table['_description']

    # dictionary -  descriptions are keys and values are lists of keywords
    desc_keyword_dict = {}
    unique_keywords  = []

    for desc in desc_lst:
        delims = []
        if desc!="":
            keywords = get_keywords(desc, common_delims)
            if len(keywords) > 0:
                desc_keyword_dict[desc] = keywords
            else:
                #print("Could not get keywords for description: " + desc)
                desc_keyword_dict[desc]= [desc] # use nltk to break these
            for keyword in keywords:
                if keyword not in unique_keywords:
                    unique_keywords.append(keyword)
        #else:
            #print("Empty description.")

    similarity_dict = {}
    for word in unique_keywords:
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

    # Check similarity dict
    new_dict={}
    all_shared_seq_dict = {} # keys are keywords and values are dictionaries { shared_sequences : count of how many other keywords this sequence is shared with}
    for key in similarity_dict:
        all_shared_seq_dict[key] = {}
    for key in similarity_dict:
        new_dict[key] = reduce_similarity(key,similarity_dict[key], all_shared_seq_dict)

    for word in all_shared_seq_dict:
        to_pop = []
        shared_seq_lst = list(all_shared_seq_dict[word].keys())
        for seq in shared_seq_lst:
            for seq2 in shared_seq_lst:
                if (seq!=seq2) and (seq in seq2) and (seq not in to_pop):
                    to_pop.append(seq)
        for seq in to_pop:
            all_shared_seq_dict[word].pop(seq)

    for key in all_shared_seq_dict:
        de_num(all_shared_seq_dict[key])

    keyword_dict2 = {}
    for key in all_shared_seq_dict:
        keyword_dict2[key] = list(all_shared_seq_dict[key].keys())
        print("Keyword: " + key)
        print("Shared sequences and their counts: ")
        print(all_shared_seq_dict[key])
        print("\n\n")



    

    with open(outf, 'w') as outfile:
        json.dump(keyword_dict2, outfile, indent = 4)

    with open(outf2, 'w') as outfile2:
        json.dump(desc_keyword_dict, outfile2, indent = 4)

    return keyword_dict2

def main():
    start = time.time()
    #parsing command-line arguments
    parser = argparse.ArgumentParser(description='Extract keywords from _description in the inverted symbol table obtained from all the configurations.')
    parser.add_argument('inverted_table_path', help='Path for a file (or directory) containing a JSON representation the inverted symbol table')
    parser.add_argument('out_path1', help='Name of file (or directory) to write JSON file(s) containing words associated with each keyword.')
    parser.add_argument('out_path2', help='Name of file (or directory) to write JSON file(s) containing keywords associated with each description.')

    arguments = parser.parse_args()
    # call function to process description
    infer_keywords(arguments.inverted_table_path, arguments.out_path1, arguments.out_path2)

    end = time.time()
    print()
    print("Time taken: " + str(end-start))
    print()


if __name__ == "__main__":
    main()
