#!/usr/bin/env python3

import os
import sys

# Load code to test
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import analyze_refs

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