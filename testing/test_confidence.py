#!/usr/bin/env python3

import os
import sys

# Load code to test
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import iacl_match

"""ACL covers the IP address of at least one interface => ACL is applied to all interfaces whose IP addresses are covered"""
def test_rule3():
    interfaceIP = {"149.224.15.65": ["naArSbuXSGZ","ZL5LSHxVaqsG"], "164.77.128.65": ["WG8frRhR","Ejbiau4T3"]}
    ACLtoI= {"naArSbuXSGZ": [["149.224.15.64", "0.0.0.31"]],"ZL5LSHxVaqsG": [["164.77.33.0", "0.0.0.255"], ["149.224.129.0", "0.0.0.255"], ["149.224.20.0", "0.0.0.255"], ["164.77.21.0", "0.0.0.255"]], "WG8frRhR": [ ["164.77.128.64", "0.0.0.63"] ], "Ejbiau4T3": [ ["164.77.21.0", "0.0.0.255"], ["149.224.20.0", "0.0.0.255"], ["149.224.44.0", "0.0.0.15"], ["149.224.44.32", "0.0.0.15"]]}
    assert iacl_match.ACL_Interface(ACLtoI, interfaceIP) == (2, 2)


"""Specific ACL applied to an interface => interface's IP address falls within range"""
def test_rule4():
    interfaceIP = {"10.0.0.1": ["aclA"], "10.0.1.1" : [], "10.0.2.1": ["aclA"]} 
    assert iacl_match.fourth_association("aclA", interfaceIP) == (2, 3)