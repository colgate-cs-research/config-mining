import argparse
import time

stanza_type_dict = {('System', 'stp_mode'): 0,
                    ('Port', 'lag200'): 1,
                    ('Port', 'port_access_clients_limit'): 2,
                    ('Port', 'vlan_trunks'): 3,
                    ('Port', 'lag31'): 4,
                    ('Port', 'port_access_auth_configurations'): 5,
                    ('VLAN', '2008'): 6,
                    ('Port', 'loop_protect_vlan'): 7,
                    ('Interface', 'user_config'): 8,
                    ('Port', 'admin'): 9,
                    ('System', 'mstp_config_revision'): 10,
                    ('Interface', 'description'): 11,
                    ('Port', 'vrf'): 12,
                    ('Port', '1/6/41'): 13,
                    ('Port', 'qos_config'): 14,
                    ('Interface', '1/1/31'): 15,
                    ('VRF', 'Tacacs_Server'): 16,
                    ('Port', 'vlan_mode'): 17,
                    ('Port', 'loop_protect_enable'): 18,
                    ('Port', 'stp_config'): 19,
                    ('Port', 'interfaces'): 20,
                    ('Port', '1/1/31'): 21,
                    ('VRF', 'Radius_Server'): 22,
                    ('Port', 'vlan_tag'): 23}

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