import json
import pandas as pd
from stucco import ContrastSetLearner as csl
from iacl_match import intraconfig_refs, write_to_outfile
from itertools import chain



def get_first_octet(ip_address_string):
    return ip_address_string.split(".")[0]

def aggregate_first_octect_vals(AclName2IpsInRules):
    all_possible_values=[]
    from_iterable = chain.from_iterable(AclName2IpsInRules.values())
    #list(from_iterable)

    
    for ip_set in list(from_iterable):
        src_ip= ip_set[0]
        
        first_octet= get_first_octet(src_ip)
        

        if first_octet not in all_possible_values:
            all_possible_values.append(first_octet)
    #print(all_possible_values)
    return all_possible_values

'''
computes a data entry line from a single ACL reference
ip_refs_list=> AclName2IpsInRules[acl_name]
all_possible_vales=> list of all possibel first_octet values.
'''
def octet_dataline(ip_refs_list,all_possible_values):
    all_possible_values_dict=dict.fromkeys(all_possible_values,False)

    for ip_set in ip_refs_list:
        src_ip = ip_set[0]
        all_possible_values_dict[get_first_octet(src_ip)]=True
    

    return all_possible_values_dict


def octet_dataline_list_format(index,octet_dataline,all_possible_values):
    dataline_list_format=[index]
    for val in all_possible_values:
        dataline_list_format.append(octet_dataline[val])

    return dataline_list_format




'''
Generates a pandas database from AclName2IpsInRules
'''
def generate_dataframe(AclName2IpsInRules):
    acl_name_list= list(AclName2IpsInRules.keys()) #index of the dataframe
    all_possible_vals= ['name'] + aggregate_first_octect_vals(AclName2IpsInRules) #column names in the data frame

    print(all_possible_vals)
    print(acl_name_list)
    
    
    i=0;
    first_octect_dataframe = pd.DataFrame(columns=all_possible_vals)

    for acl_name in acl_name_list:
        current_acl_ref=AclName2IpsInRules[acl_name]
        acl_dataline= octet_dataline(current_acl_ref,all_possible_vals[1:])
        acl_dataline_list_format= octet_dataline_list_format(acl_name,acl_dataline,all_possible_vals[1:])
        print("ACL name: "+acl_name)
        print(acl_dataline_list_format)


        first_octect_dataframe.loc[i] = acl_dataline_list_format
        i+=1

        #generating val list from dataline

    first_octect_dataframe.set_index('name')
    return first_octect_dataframe
    
    
        
'''
Generate new data frame.
Groupss:  Private vs Public IP t
'''
def generate_private_public_df(input_df):
    pass





def main():

    cfile = "/shared/configs/northwestern/configs_json/edge18.json"
    IfaceName2AppliedAclNames, IfaceIp2AppliedAclNames, AclName2IpsInRules = intraconfig_refs(cfile)

    input_dataframe= generate_dataframe(AclName2IpsInRules)
    print(input_dataframe)


    #STARTING Contrast Set Learner
    learner = csl(input_dataframe, group_feature='10')
    #derive 3-length combinations of a rule and enumerate their abundance.
    learner.learn(max_length=3)
    output = learner.score(min_lift=0)
    print(output)









    return 0




if __name__ == "__main__":
    main()
