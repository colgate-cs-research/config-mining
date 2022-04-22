from cgi import print_directory
import time
import datetime
#from join_all_files_json import join_all_files
from pickle import TRUE
import sys
import glob
from pandas.io.formats.format import return_docstring
sys.path.append("./libraries/contrast")
import json
import ipaddress
from os import initgroups, writev, system
import pandas as pd
from stucco import ContrastSetLearner as csl
from analyze_refs import intraconfig_refs
from analyze import write_to_outfile
from itertools import chain
import analyze
import doctest


def get_octet(ip_address_string,position):
    """
    Get octet from IP address string (one-based indexing)

    >>> get_octet("121.23.45.67", 1)
    '121'
    >>> get_octet("121.23.45.67", 2)
    '23'
    >>> get_octet("121.23.45.67", 4)
    '67'
    >>> get_octet(None, 1)
    'none'
    """
    if ip_address_string is not None:
        ip_address_string = str(ipaddress.IPv4Interface(ip_address_string).network. network_address)
        return ip_address_string.split(".")[position-1]
    else:
        return 'none'

def get_prefixlen(ip_address_string):
    """
    >>> get_prefixlen("0.0.0.0/0")
    '0'
    >>> get_prefixlen("121.23.45.67/32")
    '32'
    >>> get_prefixlen("121.23.0.0/16")
    '16'
    >>> get_prefixlen(None)
    'none'
    """ 
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

    >>> iterative_cumulative_bin_ip_list_gen(list('00000000'))
    ['0', '00', '000', '0000', '00000', '000000', '0000000', '00000000']
    >>> iterative_cumulative_bin_ip_list_gen(list('10101010'))
    ['1', '10', '101', '1010', '10101', '101010', '1010101', '10101010']
    >>> iterative_cumulative_bin_ip_list_gen(list('11011011'))
    ['1', '11', '110', '1101', '11011', '110110', '1101101', '11011011']
    '''
    if 'n' not in bin_ip_list:
        a = []
        accum = ""
        for digit in bin_ip_list:
            accum += digit
            a.append(accum)
        return a
    else:
        return bin_ip_list

def get_binary(octet):
    '''
    Convert a single octet (< 255, str) into 8 digit binary output (str)

    >>> get_binary('0')
    '00000000'
    >>> get_binary('1')
    '00000001'
    >>> get_binary('13')
    '00001101'
    >>> get_binary('42')
    '00101010'
    >>> get_binary('254')
    '11111110'
    >>> get_binary('255')
    '11111111'
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

    >>> col_octet("85.36.219.170")
    ['1', '10', '101', '1011', '10111', '101110', '1011101', '10111010', '101110101', '1011101010', '10111010101', '101110101010']
    '''
    
    first_octet=list(get_binary(get_octet(ip,1)))
    second_octet=list(get_binary(get_octet(ip,2)))
    third_octet=list(get_binary(get_octet(ip,3)))
    forth_octet=list(get_binary(get_octet(ip,4)))

    partial_prefix = "".join(first_octet+second_octet+third_octet[:4])
    remaining_octet_list=third_octet[4:] + forth_octet

    # breaking down octets strings into individual chars
    binarized_remaining_octect_list=iterative_cumulative_bin_ip_list_gen(remaining_octet_list)  
    
    # to return item.
    current_selection=binarized_remaining_octect_list#first_octet+second_octet+
    
    return(current_selection)

def col_prefixes(ip, startlen=20, endlen=32):
    """
    Generates prefixes of varying length from an IP address.
    #>>> col_prefixes("85.36.219.170", 20, 31)
    ['85.36.208.0/20', '85.36.216.0/21', '85.36.216.0/22', '85.36.218.0/23', '85.36.219.0/24', '85.36.219.128/25', '85.36.219.128/26', '85.36.219.160/27', '85.36.219.160/28', '85.36.219.168/29', '85.36.219.168/30', '85.36.219.170/31']
    """
    if(ip!=None and "/" in ip):
        
        ip_original,subnet =ip.split("/")[0] ,ip.split("/")[1]
        
               

        #####################
        # starting the tendril search
        ###################
             
        
        powers_of_two =[128,64,32,16,8,4,2,1]

        # Figuring ou the starting point
        # Step1: find the maximun below-min value.
        remainder=int(ip_original.split(".")[3 -1]) # "3"rd is the octet we want to examine.
        for two in powers_of_two:
            if two ==8: # since we only examine the secnd part of the octet.
                break
            if two>remainder:
                pass
            else:
                remainder-=two
        
        start = int(ip_original.split(".")[3 -1]) - remainder

        #print("Start:"+str(start)+" Remainder:"+str(remainder)+"  original_IP: "+str(ip_original.split(".")[3 -1]))

        # We got the starting point, now we need to generate the list of subnets.
        # Step2: WE start the largets subnet;  from the middle of the third octet.

        prefixes = []       # the list of prefixes to be added to the one of the greater lists in the parent function
        #for two in powers_of_two[4:]:


        ########################
        #' IPv4Network nodeul Code (start)
        # #######################'    


        for prefixlen in range(startlen, endlen):
            prefix = ipaddress.IPv4Network(ip_original + "/" + str(prefixlen), strict=False) # generates subnet list
            prefixes.append(str(prefix))  # collection of generated subnet lists.

        # Now prefixes have all the subnets relavant for the current IP's situation.
        # print(prefixes)

        ##################"
        # Code (end)
        # ################"


        


        return prefixes
    else:
        # print("Goes here")
        return list("n"*12)

def get_common_keywords(file="",multifile=0):
    '''
    input: filename
    Output: IfaceName2Keywords,keyword_count_orginal,common_keywords
    '''

    if (multifile==1): # we are dealing witha directory
        # Running the join_all_files_json to produce input
        # join_all_files_json.join_all_files(file)  # ecnourting circular import

        # loading aggreagted json data

        files = json.load(open("./csl_output/keywords/aggregate/aggregate_data.json",'r'))["filenames"]
        keyword_count={}

        # Keyword frequency calculator
        for single_file in files.keys():
            single_file_dict = files[single_file]
            for interface in single_file_dict.keys():
                keywords = single_file_dict[interface]
                for keyword in keywords:
                    if keyword in keyword_count.keys():
                        keyword_count[keyword]+=1
                    else:
                        keyword_count[keyword]=1
        
        json.dump(keyword_count,open("./tempfile.json","w"),indent=4)



    else:
        file_name = file.split("/")[-1].split(".")[0]
        IfaceName2Keywords=read_dict_from_json("./csl_output/keywords/"+file_name+".json",True)
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
    for i in range(0,14):
        count=max(keyword_count.values())
        keyword=list(keyword_count.keys())[list(keyword_count.values()).index(count)]
        #print(keyword+" Count: "+str(count))
        common_keywords.append(keyword)
        keyword_count.pop(keyword)

    #print("################ Common keywords ###############")
    #print(common_keywords)

    # different return statements for multifile vs local file.
    if(multifile==1):
        return common_keywords
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

        #print("Current Word:"+word)
        if word in interface_keywords:
            col_ouput.append('1')
        else:
            col_ouput.append('0')
    return col_ouput







def extended_df(IfaceName2AppliedAclNames,IfaceName2IfaceIp,IfaceName2Keywords=None,common_keywords=None,subnet_list=None):
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

        

        #curently using,
        # octet numbers     using   col_octet
        # in_acl names
        # Want to add keywords
        # print(IfaceName2IfaceIp)
        # print("######## IP: ##########")
        # print(ip)
        # print("####### END #########")
        

        # print("######################")
        # col_prefixes(ip)
        # print("####### END #########")
        # Generating dataline about subnets(YES/NO |  1/0) using subnet_list
        # subnet_values = []
        # for supernet in subnet_list:
        #     if ip_network(supernet).supernet_of(ip):
        #         subnet_values.append(1)
        #         continue
        #     subnet_values.append(0)



        input_dict[IfaceName]=[in_acl,ip,IfaceName]+col_prefixes(ip)+keyword_dataline #+subnet_values#

        
        


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



def directory_listing(directory_address):
    """
    Listing all the items in a given directory
    @returns: ['file1_Addr','file2_address'] 
    """
    list = glob.glob("/shared/configs/uwmadison/2014-10-core/configs_json/*.json")
    return list


def compile_dict(cfile,custom_keywords=[]):

    IfaceName2AppliedAclNames, IfaceIp2AppliedAclNames, AclName2IpsInRules = intraconfig_refs(cfile)
        #write_to_outfile("AclName2IpsInRules.json",AclName2IpsInRules)
        #write_to_outfile("IfaceIp2AppliedAclNames.json",IfaceIp2AppliedAclNames)
        #write_to_outfile("IfaceName2AppliedAclNames.json",IfaceName2AppliedAclNames)

    IfaceName2IfaceIp=read_dict_from_json(cfile)  # 
    #IfaceName2Keywords=read_dict_from_json(cfile,True)
    IfaceName2Keywords,keyword_count,common_keywords=get_common_keywords(cfile)

    # Collecting common Keywords for columns

    # generating the input dictionary and the data.
    
    if custom_keywords == []:
        input_dict=extended_df(IfaceName2AppliedAclNames,IfaceName2IfaceIp,IfaceName2Keywords,common_keywords)
    else:
        input_dict=extended_df(IfaceName2AppliedAclNames,IfaceName2IfaceIp,IfaceName2Keywords,custom_keywords)

    # For multi-file processing, adding file name to every line in input dict
    for key in input_dict.keys():
        input_dict[key] = [cfile]+input_dict[key]
        # print(input_dict[key])

    return input_dict,common_keywords
    
def update_time_measurement(file_name,depth,keyword,time_taken):
    '''
    Save time measurement to file
    '''
    now = datetime.datetime.now()
    d4 = now.strftime("%d/%m/%Y %H:%M:%S")

    file = open("csl_runtime_dataset.txt", "a")

    date_entry = "date:"+str(d4)+" | "
    L = date_entry+"input:"+file_name.split("/")[-2] + "/" +file_name.split("/")[-1] +" | " +"depth:"+str(depth)+" | "+"keyword:"+ keyword + " | "+"time_taken:"+ str(time_taken)+"\n"
    file.writelines(L)
    file.close()



def main():

    

    # 1 - directories, 0 - file name
    multiple_files = 1

    cfile_org = "/shared/configs/northwestern/configs_json/core3.json"
    cfile = "/shared/configs/uwmadison/2014-10-core/configs_json/r-432nm-b3a-2-core.json"
    cdir = "/shared/configs/uwmadison/2014-10-core/configs_json/"
    #execute_file(cfile,3)

    column_list_old=['in_acl','has_in_acl','out_acl','prefixlen', 'first_octet','second_octet','16','15','14','13','12','11','10','9','8','7','6','5','4','3','2','1']
    column_list=['','has_in_acl','has_out_acl','has_both_acl','prefixlen', 'partial_prefix','21','22','23','24','25','26','27','28','29','30']
    column_list=['in_acl','has_in_acl','partial_prefix','/21','/22','/23','/24','/25','/26','/27','/28','/29','/30']
    column_list=['in_acl','/20','/21','/22','/23','/24','/25','/26','/27','/28','/29','/30','/31']
    column_list=['filename','in_acl','IfaceName','ip','/20','/21','/22','/23','/24','/25','/26','/27','/28','/29','/30','/31']

    #compte precision and recall.   s

    agg_common_keywords,aggregated_input_dict = [],{}
    
    if multiple_files == 1:     # multiple files

        # getting the file list
        directory_list = directory_listing(cdir)

        #aggregated_input_dict = {}

        #generating keyword list for the directories listed
        python_bash_cmd = "/usr/bin/python3"
        script_path_cmd = "/users/jchauhan/config-mining/extract_keywords.py"
        output_path_cmd = "/users/jchauhan/config-mining/csl_output/keywords/"
        print("Reached till here")
        for json_file in directory_list:
            # Generates Iface2Keywords files
            final_cmd = python_bash_cmd +" "+script_path_cmd+" "+ json_file +" "+ output_path_cmd+json_file.split("/")[-1]
            system(final_cmd)


        # Compile aggregated keyword list using join_all_files_json.py
        # system(python_bas_cmd +" "+"/users/jchauhan/config-mining/jsoin_all_files_json.py")

        # Finding most common keywords when aggreagted
        agg_common_keywords = get_common_keywords("",1)

        print("######## COMMON KEYWORDS ###########")
        print(agg_common_keywords)
        print("####################################")


        # generating aggregated input dict
        for json_file in directory_list:
            current_input_dict,current_common_keywords=compile_dict(json_file,agg_common_keywords)

            # changing primary key in aggregate_input_dict
            for interface in current_input_dict.keys():
                dataline =current_input_dict[interface]
                aggregate_key = dataline[0] + " "+ interface
                aggregated_input_dict[aggregate_key] = dataline

        # json.dump(aggregated_input_dict,open("aggregted_input_dict.json",'w'),indent = 4)
        # creating a dataframe from the input dictionary
        print("Almost done")
        #dataframe=create_DataFrame(column_list+agg_common_keywords,aggregated_input_dict)
        #print(dataframe.head)

        
    else:                       # single file
        # compiling the entries in dictionary form
        input_dict,common_keywords=compile_dict(cfile)
        
        ## PRINT statements
        # print(common_keywords)
        # print(input_dict)

        # creating a dataframe from the input dictionary
        dataframe=create_DataFrame(column_list+common_keywords,input_dict)

    # IF DOESN"T RUN, the uncomment
    # compiling the entries in dictionary form
    #       input_dict,common_keywords=compile_dict(cfile)
        
        ## PRINT statements
        # print(common_keywords)
        # print(input_dict)

        # creating a dataframe from the input dictionary
    #       dataframe=create_DataFrame(column_list+common_keywords,input_dict)

    dataframe=create_DataFrame(column_list+agg_common_keywords,aggregated_input_dict)

    print("Till here.......")
    print(dataframe.head)
    print("And here")
     
    #generates ACL, first octet DataFrame
    #input_dataframe= first_octet_df(AclName2IpsInRules)
    #print(input_dataframe)
    #print(get_binary('253'))


    
    # Saving the Database:
    dataframe.to_csv("/users/jchauhan/config-mining/csl_output/workingDB/"+"aggregate_df"+"_workDB.csv",index=False)

    #STARTING Contrast Set Learner
    depth = 2    
    keyword = 'management'


    # time measuring
    start_time = time.process_time()

    run_csl(dataframe,keyword,depth,0).to_csv("/users/jchauhan/config-mining/csl_output/rules/"+"aggregate_df"+"_depth_"+str(depth)+"keyword: "+keyword+"_pr.csv",index=False)

    # time Measuring 
    execution_time = time.process_time()-start_time
    update_time_measurement(cdir,depth,keyword,execution_time)

    return 0



if __name__ == "__main__":
    doctest.testmod()
    main()
