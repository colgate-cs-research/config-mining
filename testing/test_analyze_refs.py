#!/usr/bin/env python3

import difflib
import os
import sys
import tempfile

# Load code to test
testing_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.dirname(testing_dir))
import analyze_refs

def test_intraconfig_refs_acls_IfaceName2AppliedAclNames():
    configs_dir = os.path.join(testing_dir, "analysis", "configs_json")
    actual, _, _ = analyze_refs.intraconfig_refs(os.path.join(configs_dir, "acls.json"))
    expected = {
        'GigabitEthernet0/1': {}, 
        'GigabitEthernet0/2': {'in': 'aclA'}, 
        'GigabitEthernet0/3': {'out': 'aclB'}, 
        'GigabitEthernet0/4': {'in': 'aclC', 'out': 'aclD'}, 
        'GigabitEthernet0/5': {'in': 'aclC', 'out': 'aclB'}, 
        'GigabitEthernet0/6': {'out': 'aclB'}, 
        'GigabitEthernet0/7': {}, 
        'GigabitEthernet0/8': {}
    }
    assert actual == expected

def test_intraconfig_refs_acls_IfaceIp2AppliedAclNames():
    configs_dir = os.path.join(testing_dir, "analysis", "configs_json")
    _, actual, _ = analyze_refs.intraconfig_refs(os.path.join(configs_dir, "acls.json"))
    expected = {
        '10.0.1.1': {}, 
        '10.0.2.1': {'in': 'aclA'}, 
        '10.0.3.1': {'out': 'aclB'}, 
        '10.0.4.1': {'in': 'aclC', 'out': 'aclD'}, 
        '10.0.5.1': {'in': 'aclC', 'out': 'aclB'}, 
        '20.0.2.1': {'out': 'aclB'}, 
        '20.0.3.1': {}, 
        '20.0.4.1': {}
    }
    assert actual == expected

def test_intraconfig_refs_acls_AclName2IpsInRules():
    configs_dir = os.path.join(testing_dir, "analysis", "configs_json")
    _, _, actual = analyze_refs.intraconfig_refs(os.path.join(configs_dir, "acls.json"))
    expected = {
        'aclA': [
            ['20.0.1.128', '0.0.0.127'], 
            ['20.0.1.0', '0.0.0.255']
        ], 
        'aclB': [
            ['20.0.2.1', '0.0.0.0']
        ], 
        'aclC': [
            ['20.0.3.0', '0.0.0.255'], 
            ['20.0.4.1', '0.0.0.0'], 
            ['20.0.5.0', '0.0.0.255'], 
            ['20.0.6.1', '0.0.0.0'], 
            ['20.0.7.0', '0.0.0.255'], 
            ['20.0.8.0', '0.0.0.255'], 
            ['20.0.9.1', '0.0.0.0'], 
            ['20.0.10.1', '0.0.0.0'], 
            ['20.0.11.0', '0.0.0.255'], 
            ['20.0.12.1', '0.0.0.0'], 
            ['20.0.13.1', '0.0.0.0'], 
            ['20.0.14.0', '0.0.0.255']
        ], 
        'aclD': [
            ['20.0.16.0', '0.0.0.255'], 
            ['20.0.17.0', '0.0.0.255']
        ]
    }
    assert actual == expected


"""is interface => interface has ACL reference(s)"""
def test_rule1():
    IfaceName2AppliedAclNames = { 
        "Vlan1" : {"in" : "aclA"}, 
        "Vlan2" : {"out" : "aclB"}, 
        "Vlan3" : {"in" : "aclC", "out" : "aclD"},
        "Vlan4" : {"out" : "aclE"},
        "Vlan5" : {}
    }
    assert analyze_refs.assoc_iface_has_acl(IfaceName2AppliedAclNames) == (5, 4)

"""interface has 'in' access list => interface has 'out' access list"""
def test_rule2_in():
    IfaceName2AppliedAclNames = { 
        "Vlan1" : {"in" : "aclA"}, 
        "Vlan2" : {"out" : "aclB"}, 
        "Vlan3" : {"in" : "aclC", "out" : "aclD"},
        "Vlan4" : {"out" : "aclE"},
        "Vlan5" : {}
    }
    assert analyze_refs.assoc_acl_directions("in", IfaceName2AppliedAclNames) == (2, 1)

"""interface has 'out' access list => interface has 'in' access list"""
def test_rule2_out():
    IfaceName2AppliedAclNames = { 
        "Vlan1" : {"in" : "aclA"},
        "Vlan2" : {"out" : "aclB"}, 
        "Vlan3" : {"in" : "aclC", "out" : "aclD"},
        "Vlan4" : {"out" : "aclE"},
        "Vlan5" : {}
    }
    assert analyze_refs.assoc_acl_directions("out", IfaceName2AppliedAclNames) == (3, 1)

"""ACL covers the IP address of at least one interface => ACL is applied to all interfaces whose IP addresses are covered"""
def test_rule3_general():
    interfaceIP = {
        "149.224.15.65": {"in": "naArSbuXSGZ", "out": "ZL5LSHxVaqsG"}, 
        "164.77.128.65": {"in": "WG8frRhR", "out": "Ejbiau4T3"}
        }
    ACLtoI = {
        "naArSbuXSGZ": [["149.224.15.64", "0.0.0.31"]],
        "ZL5LSHxVaqsG": [["164.77.33.0", "0.0.0.255"], ["149.224.129.0", "0.0.0.255"], ["149.224.20.0", "0.0.0.255"], ["164.77.21.0", "0.0.0.255"]], 
        "WG8frRhR": [ ["164.77.128.64", "0.0.0.63"] ], 
        "Ejbiau4T3": [ ["164.77.21.0", "0.0.0.255"], ["149.224.20.0", "0.0.0.255"], ["149.224.44.0", "0.0.0.15"], ["149.224.44.32", "0.0.0.15"]]
        }
    assert analyze_refs.ACL_Interface(ACLtoI, interfaceIP) == (2, 2)

"""ACL covers the IP address of at least one interface => ACL is applied to all interfaces whose IP addresses are covered"""
def test_rule3_host():
    interfaceIP = {
        "10.0.1.1": {"in" : "aclA"}, 
        "10.0.2.1": {"in" : "aclA"}
        }
    ACLtoI = {
        "aclA": [["10.0.1.1", "0.0.0.0"]],
        }
    assert analyze_refs.ACL_Interface(ACLtoI, interfaceIP) == (1, 1)

"""interface's IP address falls within range => specific ACL applied to the interface"""
def test_rule4_gap():
    interfaceIP = {"10.0.0.1": {"in" : "aclA"}, "10.0.1.1" : {"in" : "aclB"}, "10.0.2.1": {"in" : "aclA"}} 
    assert analyze_refs.fourth_association("aclA", interfaceIP) == (2, 3, ["10.0.0.1", "10.0.2.1"])

"""interface's IP address falls within range => specific ACL applied to the interface"""
def test_rule4_continuous():
    interfaceIP = {"10.0.0.1": {"in" : "aclA"}, "10.0.1.1" : {"in" : "aclA"}, "10.0.2.1": {"in" : "aclB"}} 
    assert analyze_refs.fourth_association("aclA", interfaceIP) == (2, 2, ["10.0.0.1", "10.0.1.1"])

"""interface's IP address falls within range => specific ACL applied to the interface"""
def test_rule4_single():
    interfaceIP = {"10.0.0.1": {"in" : "aclA"}, "10.0.1.1" : {"in" : "aclB"}, "10.0.2.1": {"in" : "aclC"}} 
    assert analyze_refs.fourth_association("aclA", interfaceIP) == (1, 1, ["10.0.0.1", "10.0.0.1"])

def test_analyze_configuration():
    configs_dir = os.path.join(testing_dir, "analysis", "configs_json")
    config_file = os.path.join(configs_dir, "acls.json") 
    expected_dir = os.path.join(testing_dir, "analysis", "expected")
    expected_file = os.path.join(expected_dir, "analyze_refs", "acls.json") 
    out_dir = tempfile.mkdtemp()
    out_file = os.path.join(out_dir, "acls.json")
    analyze_refs.analyze_configuration(config_file, out_file)

    with open(out_file, 'r') as out:
        out_lines = out.readlines()

    with open(expected_file, 'r') as expected:
        expected_lines = expected.readlines()

    diff = list(difflib.unified_diff(expected_lines, out_lines))
    print(''.join(diff))
    assert len(diff) == 0