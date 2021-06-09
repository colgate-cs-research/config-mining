import json

#returns a list of keywords
def load_keywords(file):
    # Load config
    with open(file, "r") as infile:
        keywords = json.load(infile)

    #print((keywords)) # keys: 'interfaces', 'acls'
    #print((keywords["interfaces"])) #keys: Vlan18, Vlan...
    #print((keywords["interfaces"]["Vlan18"])) # list of words
    #print(len(keywords["interfaces"]))
    return keywords

def get_common_keywords(keywords, stanza, threshold=10): #stanza="interfaces"
    all_words = {}
    for iface_name in keywords[stanza]:
        iface_words = keywords[stanza][iface_name]
        for word in iface_words:
            if word not in all_words:
                all_words[word] = 1
            else:
                all_words[word] += 1

    common_words = []
    for word, count in all_words.items():
        if count > threshold: #FIXME: take threshold as argument
            common_words.append(word)

    return sorted(common_words)


    #1) interfaces have keywords keywords JSON file
    #2) ACLs have keywords keywords JSON file
    #3) interfaces have ACLs config JSON file
    #config JSON -> keywords.py -> keywords JSON
    #configs JSON & keywords JSON -> analyze_keywords.py -> confidence JSON
    #interface i has keyword k => interface i has ACL a
    #interface i has keyword k and ACL a has keyword k => interface i has ACL a

# For each common keyword, find all interfaces that have that keyword CREATE DICTIONARY, list of interface names
# TEST TO SEE IF THIS WORKS BY MAKING OWN DICTIONARY WITH WORDS ETC...
def keyword_interfaces(words, keywords):
    keyword_interface_dict = {}
    for word in words:
        interface_list = []
        for interface in keywords["interfaces"]:
            for keyword in keywords["interfaces"][interface]:
                if keyword == word and interface not in interface_list:
                    interface_list.append(interface)
        keyword_interface_dict[word] = interface_list
    
    return keyword_interface_dict

# For each common keyword, find all ACLs that have that keyword CREATE DICTIONARY 
def keyword_ACLs(words, keywords):
    keyword_ACL_dict = {}
    for keyword in words:
        acl_list = []
        for ACL in (keywords["acls"]):
            for words in keywords["acls"][ACL]:
                if keyword == words and ACL not in acl_list:
                    acl_list.append(ACL)
        keyword_ACL_dict[keyword] = acl_list

    return keyword_ACL_dict


def data_computation(keyword_interfaces):
    a={}
    a["message"]="C(Keyword ---> interface)"

    b={}
    b["message"]="C(Keyword ---> ACL)"

def write_to_outfile(filename, keyword_interfaces):
    with open(filename, 'w') as outfile:
        a = data_computation(keyword_interfaces)
        to_dump= [a,keyword_interfaces]
        json.dump(to_dump, outfile, indent=4, sort_keys=True)
    return 


def main():
    keywords = load_keywords("output/keywords.json") # FIXME: Take command-line arguments
    common_iface_words = get_common_keywords(keywords, "interfaces", 10)
    keyword_interface_dictionary = keyword_interfaces(common_iface_words, keywords)
    keyword_ACL_dictionary = keyword_ACLs(common_iface_words, keywords)

    #print(keyword_ACL_dictionary)

    #with open("output/analyze_keywords", 'w') as outfile:
        #keyword_ACL_dictionary

    write_to_outfile("output/analyze_keywords", keyword_interface_dictionary)

    # call iacl_match.intraconfig_refs to get mapping from interface names to applied ACLs

    # For each common keyword, for each interface, check if interface's ACL exists in list of ACLs with that keyword

if __name__ == "__main__":
    main()