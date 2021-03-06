import argparse
import time

# stanza_type_dict = {('System', 'stp_mode'): 0,
#                     ('Port', 'lag200'): 1,
#                     ('Port', 'port_access_clients_limit'): 2,
#                     ('Port', 'vlan_trunks'): 3,
#                     ('Port', 'lag31'): 4,
#                     ('Port', 'port_access_auth_configurations'): 5,
#                     ('VLAN', '2008'): 6,
#                     ('Port', 'loop_protect_vlan'): 7,
#                     ('Interface', 'user_config'): 8,
#                     ('Port', 'admin'): 9,
#                     ('System', 'mstp_config_revision'): 10,
#                     ('Interface', 'description'): 11,
#                     ('Port', 'vrf'): 12,
#                     ('Port', '1/6/41'): 13,
#                     ('Port', 'qos_config'): 14,
#                     ('Interface', '1/1/31'): 15,
#                     ('VRF', 'Tacacs_Server'): 16,
#                     ('Port', 'vlan_mode'): 17,
#                     ('Port', 'loop_protect_enable'): 18,
#                     ('Port', 'stp_config'): 19,
#                     ('Port', 'interfaces'): 20,
#                     ('Port', '1/1/31'): 21,
#                     ('VRF', 'Radius_Server'): 22,
#                     ('Port', 'vlan_tag'): 23}

stanza_type_dict = {('System', 'stp_mode'): 0, ('Interface', 'user_config'): 1, ('DHCP_Relay', 'vrf'): 2, ('System', 'dlog_destination'): 3, ('VRF', 'ospf_routers'): 4, ('System', 'qos_config'): 5, ('System', '2'): 6, ('Port', 'aclv4_routed_out_cfg_version'): 7, ('Port', 'name'): 8, ('VLAN', 'id'): 9, ('VRF', 'aclv4_control_plane_cfg'): 10, ('Interface', 'description'): 11, ('Port', 'vlan_trunks'): 12, ('System', 'stp_enable'): 13, ('VRF', 'Radius_Server'): 14, ('Port', 'lacp'): 15, ('System', 'mirrors'): 16, ('System', '5.5.132.24'): 17, ('VLAN', 'description'): 18, ('ACL', 'cfg_aces'): 19, ('Port', 'port_access_clients_limit'): 20, ('System', 'ntp_config_vrf'): 21, ('Port', 'stp_config'): 22, ('System', 'mstp_config_revision'): 23, ('DHCP_Relay', 'ipv4_ucast_server'): 24, ('ACL', 'name'): 25, ('Port', 'loop_protect_enable'): 26, ('VRF', 'aclv4_control_plane_cfg_version'): 27, ('Port', 'interfaces'): 28, ('Port', 'description'): 29, ('Port', 'routing'): 30, ('Port', 'vlan_tag'): 31, ('VRF', 'Tacacs_Server'): 32, ('Port', 'loop_protect_vlan'): 33, ('Port', 'vrf'): 34, ('DHCP_Relay', 'port'): 35, ('Port', 'other_config'): 36, ('Port', 'port_access_auth_configurations'): 37, ('Port', 'vlan_mode'): 38, ('System', 'bpdu_guard_timeout'): 39, ('Port', 'admin'): 40, ('System', 'portaccess_local_accounting_enable'): 41, ('Interface', 'name'): 42, ('Port', 'aclv4_routed_out_cfg'): 43, ('ACL', 'vsx_sync'): 44, ('ACL', 'cfg_version'): 45, ('Port', 'l3_counters_enable'): 46, ('Port', 'qos_config'): 47, ('ACL', 'list_type'): 48, ('VLAN', 'name'): 49}

def make_csv(f):
    out = 'Stanza_type_tuples, '
    for key in stanza_type_dict:
        out += str(key) + (', ')
    out = out[:-2] + '\n'

    s = f.read()
    lst = s[1:-1].split('\n')

    row_num = 1

    for el in lst:
        out += "T" + str(row_num) + ", "
        el2 = el.strip()[1:-1]
        if el2[-1] == ']':
            el2 = el2[:-1]
        out += el2 + '\n'
        row_num += 1


    return out

    


def main():
    start = time.time()
    #parsing command-line arguments
    parser = argparse.ArgumentParser(description='Turn a matrix into a csv file, input must be one row per line and must start and end with square braces.')
    parser.add_argument('matrix_path', help='Path for a txt file containing matrix, one row per line, start with [ and end with ]')
    parser.add_argument('out_path', help='Name of csv file (or directory) to write the output to')

    arguments = parser.parse_args()

    f = open(arguments.matrix_path, 'r')
    out = make_csv(f)
    f.close()

    f = open(arguments.out_path, 'w')
    f.write(out)
    f.close()

    end = time.time()
    print()
    print("Time taken: " + str(end-start))
    print()

if __name__ == "__main__":
    main()