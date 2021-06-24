import json
import ipaddress
from os import initgroups, writev
import pandas as pd
from stucco import ContrastSetLearner as csl
from analyze_refs import intraconfig_refs
from analyze import write_to_outfile
from itertools import chain


'''
Get octet from IP address string
eg: IPaddr=> 121.23.45.678
position=1 : 121
postion=2 : 23
...
'''
def get_octet(ip_address_string,position):
    
    if ip_address_string is not None:
        ip_address_string = str(ipaddress.IPv4Interface(ip_address_string).network. network_address)
        return ip_address_string.split(".")[position-1]
    else:
        return 'none'

def get_prefixlen(ip_address_string):
    
    if ip_address_string is not None:
        return ip_address_string.split("/")[1]
    else:
        return 'none'

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
        all_possible_values_dict[get_octet(src_ip,1)]=True
    

    return all_possible_values_dict


def octet_dataline_list_format(index,octet_dataline,all_possible_values):
    dataline_list_format=[index]
    for val in all_possible_values:
        dataline_list_format.append(octet_dataline[val])

    return dataline_list_format


'''
Generates a pandas database from AclName2IpsInRules
Columns: first octet values
Rows: True,False
'''
def first_octet_df(AclName2IpsInRules):
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
Generates dataframe according to below specification
       A  B  C  D      <- column list
row_1  3  2  1  0      <- input_dict["row_1"] = [3,2,1,0]
row_2  a  b  c  d
'''
def create_DataFrame(column_list,input_dict):
    df=pd.DataFrame.from_dict(input_dict,orient='index',columns=column_list)
    return df


'''
Input: JSON file
Returns a dict of format: {"IfaceName":"IPaddress"}
'''
def get_IfaceName2IfaceIp(file_name):
    json_file = open(file_name,'r')
    file_dict=json.load(json_file)['interfaces']
    to_return={}

    for IfaceName in file_dict.keys():
        to_return[IfaceName]=file_dict[IfaceName]['address']
    
    return to_return


'''
INPUT: single octet (<255, str)
Convert input string into 8 digit binary output (str)
'''
def get_binary(octet):
    #print(octet)
    if octet != 'none':
        binary_num=bin(int(octet))[2:]
        return '0'*(8-len(binary_num))+binary_num
    else:
        return 'n'*8

'''
Creates extended dataframe using colums
    column_list=['in_acl','out_acl','first_octet','second_octet','16','15','14','13','12','11','10','9','8','7','6','5','4','3','2','1']
'''
def extended_df(IfaceName2AppliedAclNames,IfaceName2IfaceIp):
    
    
    input_dict={}

    for IfaceName in IfaceName2AppliedAclNames.keys():

        try:
            in_acl=IfaceName2AppliedAclNames[IfaceName]["in"] if IfaceName2AppliedAclNames[IfaceName]["in"] != '' else 'none'
        except KeyError:
            in_acl='none'
        try:
            out_acl=IfaceName2AppliedAclNames[IfaceName]["out"] if IfaceName2AppliedAclNames[IfaceName]["out"] != '' else 'none'
        except KeyError:
            out_acl='none'

        
        ip=IfaceName2IfaceIp[IfaceName]
        first_octet=list(get_binary(get_octet(ip,1)))
        second_octet=list(get_binary(get_octet(ip,2)))
        third_octet=list(get_binary(get_octet(ip,3)))
        forth_octet=list(get_binary(get_octet(ip,4)))
        prefixlen = get_prefixlen(ip)
        partial_prefix = "".join(first_octet+second_octet+third_octet[:4])
        has_in_acl = (in_acl != 'none')


        input_dict[IfaceName]=[in_acl,has_in_acl,out_acl,prefixlen,partial_prefix]+third_octet[4:]+forth_octet[:6]


        
        


    return input_dict


        
'''
Runs ContrastSetLearner according to specifications
input_df: Input Dataframe
feature: Group Feature
len: Max Length/depth of rule search
lift: Minimum Lift require din the output

OUPUT: learner.score 
'''
def run_csl(input_df,feature,len,lift):
    learner = csl(input_df, group_feature=feature)
    #derive 3-length combinations of a rule and enumerate their abundance.
    learner.learn(max_length=len)

    return learner.score(min_lift=lift)



    
    


def main():

    cfile = "/shared/configs/northwestern/configs_json/core1.json"
    IfaceName2AppliedAclNames, IfaceIp2AppliedAclNames, AclName2IpsInRules = intraconfig_refs(cfile)
    #write_to_outfile("AclName2IpsInRules.json",AclName2IpsInRules)
    #write_to_outfile("IfaceIp2AppliedAclNames.json",IfaceIp2AppliedAclNames)
    #write_to_outfile("IfaceName2AppliedAclNames.json",IfaceName2AppliedAclNames)

    IfaceName2IfaceIp=get_IfaceName2IfaceIp(cfile)

    input_dict=extended_df(IfaceName2AppliedAclNames,IfaceName2IfaceIp)
    column_list_old=['in_acl','has_in_acl','out_acl','prefixlen', 'first_octet','second_octet','16','15','14','13','12','11','10','9','8','7','6','5','4','3','2','1']
    column_list=['','has_in_acl','','', 'partial_prefix','21','22','23','24','25','26','27','28','29','30']
    #compte precision and recall.

    dataframe=create_DataFrame(column_list,input_dict)
    #print(dataframe.to_string())
    #generates ACL, first octet DataFrame
    #input_dataframe= first_octet_df(AclName2IpsInRules)
    #print(input_dataframe)
    #print(get_binary('253'))

    #STARTING Contrast Set Learner
    run_csl(dataframe,'has_in_acl',3,0).to_csv("core1_depth_3.csv",index=False)
    
    return 0




if __name__ == "__main__":
    main()
