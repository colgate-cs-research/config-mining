import sys

from pandas.io.formats.format import return_docstring
sys.path.append("./libraries/contrast")
import json
import ipaddress
from os import initgroups, writev
import pandas as pd
from stucco import ContrastSetLearner as csl
from analyze_refs import intraconfig_refs
from analyze import write_to_outfile
from itertools import chain
import analyze


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



def read_dict_from_json(file_name,keywords=False):
    '''
    Input: JSON file
    Returns a dict of format: {"IfaceName":"IPaddress"/"Keywords"}
    '''
    json_file = open(file_name,'r')
    file_dict=json.load(json_file)['interfaces']
    to_return={}
    if(keywords):
        for IfaceName in file_dict.keys():
            to_return[IfaceName]=file_dict[IfaceName]    #  ADD  ['address'] to he end to select normal config file,   
    else:
        for IfaceName in file_dict.keys():
            to_return[IfaceName]=file_dict[IfaceName]['address']
    return to_return


def iterative_cumulative_bin_ip_list_gen(bin_ip_list):
    '''
    Name say it all. nuff said
    Input:['0','0','1','0']
    Output:['0','00','001','0010']
    '''
    if 'n' not in bin_ip_list:
        a=bin_ip_list[:1]
        #print(a)
        for digit in bin_ip_list:
            a.append(a[-1]+digit)
        return a
    else:
        return bin_ip_list



def get_binary(octet):
    '''
    INPUT: single octet (<255, str)
    Convert input string into 8 digit binary output (str)
    '''
    #print(octet)
    if octet != 'none':
        binary_num=bin(int(octet))[2:]
        return '0'*(8-len(binary_num))+binary_num
    else:
        return 'n'*8


def col_octet(ip):
    '''
    Generates a list of ip address octets broken down into binary form
    eg:-  the value for columns 'first octet', s'second octet' and 16 -> 1  
    column_list=['in_acl','out_acl','first_octet','second_octet','16','15','14','13','12','11','10','9','8','7','6','5','4','3','2','1']
    '''
    
    first_octet=list(get_binary(get_octet(ip,1)))
    second_octet=list(get_binary(get_octet(ip,2)))
    third_octet=list(get_binary(get_octet(ip,3)))
    forth_octet=list(get_binary(get_octet(ip,4)))

    partial_prefix = "".join(first_octet+second_octet+third_octet[:4])
    remaining_octet_list=third_octet[:4] + forth_octet

    # breaking down octets strings into individual chars
    binarized_remaining_octect_list=iterative_cumulative_bin_ip_list_gen(remaining_octet_list)  
    
    # to return item.
    current_selection=binarized_remaining_octect_list#first_octet+second_octet+
    return(current_selection)



def get_common_keywords(file):
    '''
    input: filename
    Output: IfaceName2Keywords,keyword_count_orginal,common_keywords
    '''
    file_name = file.split("/")[-1].split(".")[0]
    IfaceName2Keywords=read_dict_from_json("./csl_output/keywords/uw_"+file_name+"_keywords.json",True)
    #print("---curr IfaceName 2 Keyword ----")
    #print(IfaceName2Keywords)
    keyword_count = {}
    
    for IfaceName in IfaceName2Keywords.keys():
        keywords= IfaceName2Keywords[IfaceName]
        for keyword in keywords:
            if keyword not in keyword_count.keys():
                keyword_count[keyword]=1
            else:
                keyword_count[keyword]+=1

    keyword_count_orginal=keyword_count.copy()
    common_keywords=[]
    for i in range(0,9):
        count=max(keyword_count.values())
        keyword=list(keyword_count.keys())[list(keyword_count.values()).index(count)]
        #print(keyword+" Count: "+str(count))
        common_keywords.append(keyword)
        keyword_count.pop(keyword)

    print(common_keywords)
    return IfaceName2Keywords,keyword_count_orginal,common_keywords
        



def col_keywords(interface_keywords,common_keywords):
    '''
    return the list of one-hot encoded 1s and 0s
    Checks whether common_keywords are present in the list of interface_keywords
        1 if present
        O if absent
    '''
    col_ouput=[]
    for word in common_keywords:
        if word in interface_keywords:
            col_ouput.append('1')
        else:
            col_ouput.append('0')
    return col_ouput







def extended_df(IfaceName2AppliedAclNames,IfaceName2IfaceIp,IfaceName2Keywords=None,common_keywords=None):
    '''
    Creates extended dataframe using colums
        column_list=['in_acl','out_acl','first_octet','second_octet','16','15','14','13','12','11','10','9','8','7','6','5','4','3','2','1']
    '''
    
    input_dict={}
    
    for IfaceName in IfaceName2AppliedAclNames.keys():

        # adding in_acl and out_acl
        try: #why am I suing a try and except? 
            in_acl=IfaceName2AppliedAclNames[IfaceName]["in"] if IfaceName2AppliedAclNames[IfaceName]["in"] != '' else 'none'
        except KeyError:
            in_acl='none'
        try:
            out_acl=IfaceName2AppliedAclNames[IfaceName]["out"] if IfaceName2AppliedAclNames[IfaceName]["out"] != '' else 'none'
        except KeyError:
            out_acl='none'

        # Adding keywords- keyword_dataline
        if(IfaceName in IfaceName2Keywords.keys()):
            keyword_dataline=col_keywords(IfaceName2Keywords[IfaceName],common_keywords)
        else:
            keyword_dataline=list("0"*len(common_keywords))
        #if(IfaceName2Keywords[IfaceName]!=None):

        ip=IfaceName2IfaceIp[IfaceName]

        prefixlen = get_prefixlen(ip)
        has_in_acl = (in_acl != 'none')
        has_out_acl = (out_acl != 'none')
        has_both_acl = (has_in_acl & has_out_acl)

        
        #input_dict[IfaceName]=[in_acl,partial_prefix]+col_octet(ip)

        #cuurently using,
        # octet numbers     using   col_octet
        # in_acl names
        # Want to add keywords
        input_dict[IfaceName]=[in_acl]+col_octet(ip)+keyword_dataline#

        
        


    return input_dict


        

def run_csl(input_df,feature,len,lift):
    '''
    Runs ContrastSetLearner according to specifications
    input_df: Input Dataframe
    feature: Group Feature
    len: Max Length/depth of rule search
    lift: Minimum Lift require din the output

    OUPUT: learner.score 
    '''

    learner = csl(input_df, group_feature=feature)
    #derive 3-length combinations of a rule and enumerate their abundance.
    learner.learn(max_length=len)

    return learner.score(min_lift=lift)


def compile_dict(file_list):

    for cfile in file_list:
        IfaceName2AppliedAclNames, IfaceIp2AppliedAclNames, AclName2IpsInRules = intraconfig_refs(cfile)
        #write_to_outfile("AclName2IpsInRules.json",AclName2IpsInRules)
        #write_to_outfile("IfaceIp2AppliedAclNames.json",IfaceIp2AppliedAclNames)
        #write_to_outfile("IfaceName2AppliedAclNames.json",IfaceName2AppliedAclNames)

        #ge
        IfaceName2IfaceIp=read_dict_from_json(cfile)  #
        #IfaceName2Keywords=read_dict_from_json(cfile,True)
        IfaceName2Keywords,keyword_count,common_keywords=get_common_keywords(cfile)

    input_dict=extended_df(IfaceName2AppliedAclNames,IfaceName2IfaceIp,IfaceName2Keywords,common_keywords)
    return input_dict,common_keywords
    


def main():

    cfile_org = "/shared/configs/northwestern/configs_json/core3.json"
    cfile = "/shared/configs/uwmadison/2014-10-core/configs_json/r-432nm-b3a-10-core.json"
    #execute_file(cfile,3)

    column_list_old=['in_acl','has_in_acl','out_acl','prefixlen', 'first_octet','second_octet','16','15','14','13','12','11','10','9','8','7','6','5','4','3','2','1']
    column_list=['','has_in_acl','has_out_acl','has_both_acl','prefixlen', 'partial_prefix','21','22','23','24','25','26','27','28','29','30']
    column_list=['in_acl','has_in_acl','partial_prefix','21','22','23','24','25','26','27','28','29','30']
    column_list=['in_acl','20','21','22','23','24','25','26','27','28','29','30','31','32']
    #compte precision and recall.


    # compiling the entries in dictionary form
    input_dict,common_keywords=compile_dict([cfile])
    # creating a dataframe from the input dictionary
    print(common_keywords)
    dataframe=create_DataFrame(column_list+common_keywords,input_dict)

    
    print(dataframe.to_string())
    depth =2    
    #generates ACL, first octet DataFrame
    #input_dataframe= first_octet_df(AclName2IpsInRules)
    #print(input_dataframe)
    #print(get_binary('253'))


    
    # Saving the Database:
    dataframe.to_csv("/users/jchauhan/config-mining/csl_output/workingDB/"+cfile_org[-10:-5]+"_workDB.csv",index=False)

    #STARTING Contrast Set Learner
    run_csl(dataframe,'32',depth,0).to_csv("/users/jchauhan/config-mining/csl_output/rules/"+cfile_org[-10:-5]+"_depth_"+str(depth)+"_pr.csv",index=False)

    return 0




if __name__ == "__main__":
    main()
