import json
import glob
import os
from analyze_refs import ACL_Interface, data_computation, is_regex_match


def compile_all_dicts(dict_list):
    merged_dicts={}
    for i in dict_list:
        merged_dicts.update(i)
    return merged_dicts


def rebuild_dict(input_file):
    with open(input_file, 'r') as f:
        return json.load(f)

    
def extract_data(pattern,path):
    IToACl_dict_list=[]
    interfaceIP_dict_list=[]
    ACLtoI_dict_list=[]
    total_interfaces=0;
    total_out_acl_refs=0;

    all_files = glob.glob(path + '/**/*.json', recursive=True)
    for file in all_files:
        if is_regex_match(pattern,file):

            extract=rebuild_dict(file)

            IToACl_dict_list.append(extract[3])
            interfaceIP_dict_list.append(extract[4])
            ACLtoI_dict_list.append(extract[5])
            #print(extract[6])
            total_interfaces+=extract[6]
            total_out_acl_refs+=extract[7]


    return IToACl_dict_list,interfaceIP_dict_list,ACLtoI_dict_list,total_interfaces,total_out_acl_refs






def main():
    pattern1="edge" # edge devices
    pattern2="core" # core devices
    pattern3="*+" #   all devices

    #working on pattern1
    IToACl_dict_list,interfaceIP_dict_list,ACLtoI_dict_list,total_num_interfaces,total_out_acl_refs= extract_data(pattern2,"./output/")

    IToACL= compile_all_dicts(IToACl_dict_list)
    interfaceIP= compile_all_dicts(interfaceIP_dict_list)
    ACLtoI= compile_all_dicts(ACLtoI_dict_list)

    two_way_references, total_ACL_IP_refs= ACL_Interface(ACLtoI, interfaceIP)


    a,b,c=data_computation(IToACL, total_num_interfaces, total_out_acl_refs, two_way_references, total_ACL_IP_refs)

    for i in [a,b,c]:
        print(i["message"])
        print(i["n"])
        print(i["d"])
        print(i["c"]+"\n")






if __name__ == "__main__":
    main()
