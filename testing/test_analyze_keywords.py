#!/usr/bin/env python3

import os
import sys

# Load code to test
sys.path.insert(1, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import analyze_keywords

keywords = {
    "interfaces": {
        "GigabitEthernet0/1": [
            "blue"
        ],
        "GigabitEthernet0/2": [
            "red"
        ],
        "GigabitEthernet0/3": [
            "red",
            "yellow"
        ],
        "GigabitEthernet0/4": [
            "yellow",
            "blue"
        ],
        "GigabitEthernet0/5": [
            "red",
            "yellow"
        ],
        "GigabitEthernet0/6": [
            "yellow"
        ]
    },
    "acls": {
        "G": [
            "green"
        ],
        "O": [
            "orange"
        ],
        "R": [
            "red"
        ],
        "Y": [
            "yellow"
        ]
    }
}

IfaceName2AppliedAclNames = {
    "GigabitEthernet0/1": {},
    "GigabitEthernet0/2": {"in": "R"},
    "GigabitEthernet0/3": {"out": "O"},
    "GigabitEthernet0/4": {"in": "Y", "out": "G"},
    "GigabitEthernet0/5": {"in": "O", "out": "Y"},
    "GigabitEthernet0/6": {"out": "Y"}
}

def test_get_common_keywords_once():
    counts = {}
    analyze_keywords.count_keywords(keywords, "interfaces", counts)
    common = analyze_keywords.get_common_keywords(counts, 1)
    expected = ["red", "yellow", "blue"]
    assert sorted(common) == sorted(expected)

def test_get_common_keywords_thrice():
    counts = {}
    analyze_keywords.count_keywords(keywords, "interfaces", counts)
    common = analyze_keywords.get_common_keywords(counts, 3)
    expected = ["red", "yellow"]
    assert sorted(common) == sorted(expected)

def test_keyword_stanza_interfaces():
    Keywords2IfaceNames = analyze_keywords.keyword_stanza(["red", "yellow", "blue"], keywords, "interfaces")
    expected = {
        "red" : ["GigabitEthernet0/2", "GigabitEthernet0/3", "GigabitEthernet0/5"],
        "yellow" : ["GigabitEthernet0/3", "GigabitEthernet0/4", "GigabitEthernet0/5", "GigabitEthernet0/6"],
        "blue" : ["GigabitEthernet0/1", "GigabitEthernet0/4"]
    }
    assert sorted(Keywords2IfaceNames.keys()) == sorted(expected.keys())
    for keyword in expected:
        assert sorted(Keywords2IfaceNames[keyword]) == sorted(expected[keyword])

def test_keyword_stanza_acls():
    Keywords2AclNames = analyze_keywords.keyword_stanza(["red", "yellow", "blue"], keywords, "acls")
    expected = {
        "red" : ["R"],
        "yellow" : ["Y"],
        "blue" : []
    }
    assert sorted(Keywords2AclNames.keys()) == sorted(expected.keys())
    for keyword in expected:
        assert sorted(Keywords2AclNames[keyword]) == sorted(expected[keyword])

def test_keyword_association():
    Keywords2IfaceNames = { "device" : {
        "red" : ["GigabitEthernet0/2", "GigabitEthernet0/3", "GigabitEthernet0/5"],
        "yellow" : ["GigabitEthernet0/3", "GigabitEthernet0/4", "GigabitEthernet0/5", "GigabitEthernet0/6"],
        "blue" : ["GigabitEthernet0/1", "GigabitEthernet0/4"]
    }}
    used_acls = ["R", "O", "Y", "G"]
    associations = analyze_keywords.keyword_association(["blue", "red", "yellow"], used_acls, {"device":IfaceName2AppliedAclNames}, Keywords2IfaceNames)
    expected = {
        ("blue", "G"): (1, 2, ["GigabitEthernet0/1"]),
        ("blue", "O"): (0, 2, ["GigabitEthernet0/1", "GigabitEthernet0/4"]),
        ("blue", "R"): (0, 2, ["GigabitEthernet0/1", "GigabitEthernet0/4"]),
        ("blue", "Y"): (1, 2, ["GigabitEthernet0/1"]),
        ("red", "G"): (0, 3, ["GigabitEthernet0/2", "GigabitEthernet0/3", "GigabitEthernet0/5"]),
        ("red", "O"): (2, 3, ["GigabitEthernet0/2"]),
        ("red", "R"): (1, 3, ["GigabitEthernet0/3", "GigabitEthernet0/5"]),
        ("red", "Y"): (1, 3, ["GigabitEthernet0/2", "GigabitEthernet0/3"]),
        ("yellow", "G"): (1, 4, ["GigabitEthernet0/3", "GigabitEthernet0/5", "GigabitEthernet0/6"]),
        ("yellow", "O"): (2, 4, ["GigabitEthernet0/4", "GigabitEthernet0/6"]),
        ("yellow", "R"): (0, 4, ["GigabitEthernet0/3", "GigabitEthernet0/4", "GigabitEthernet0/5", "GigabitEthernet0/6"]),
        ("yellow", "Y"): (3, 4, ["GigabitEthernet0/3"])
    }
    assert associations == expected

def test_keyword_ipaddress_range():
    Keywords2IfaceNames = {
        "red" : ["GigabitEthernet0/2", "GigabitEthernet0/3", "GigabitEthernet0/5"],
        "yellow" : ["GigabitEthernet0/3", "GigabitEthernet0/4", "GigabitEthernet0/5", "GigabitEthernet0/6"],
        "blue" : ["GigabitEthernet0/1", "GigabitEthernet0/4"]
    } 
    IfaceNames2Ips = {
        "GigabitEthernet0/1": "10.0.1.1",
        "GigabitEthernet0/2": "10.0.2.1",
        "GigabitEthernet0/3": "10.0.3.1",
        "GigabitEthernet0/4": "10.0.4.1",
        "GigabitEthernet0/5": "10.0.5.1",
        "GigabitEthernet0/6": "10.0.6.1",
    }
    expected_ranges = {
        "red": ["10.0.2.1", "10.0.5.1"],
        "yellow": ["10.0.3.1", "10.0.6.1"],
        "blue": ["10.0.1.1", "10.0.4.1"]
    }
    expected_ips = {
        "red": ["10.0.2.1", "10.0.3.1", "10.0.5.1"],
        "yellow": ["10.0.3.1", "10.0.4.1", "10.0.5.1", "10.0.6.1"],
        "blue": ["10.0.1.1", "10.0.4.1"]
    }
    Keywords2IpRanges, Keywords2Ips = analyze_keywords.keyword_ipaddress_range(Keywords2IfaceNames, IfaceNames2Ips)
    assert Keywords2IpRanges == expected_ranges
    assert Keywords2Ips == expected_ips

def test_keyword_range_confidence():
    IfaceNames2Ips = {
        "GigabitEthernet0/1": "10.0.1.1",
        "GigabitEthernet0/2": "10.0.2.1",
        "GigabitEthernet0/3": "10.0.3.1",
        "GigabitEthernet0/4": "10.0.4.1",
        "GigabitEthernet0/5": "10.0.5.1",
        "GigabitEthernet0/6": "10.0.6.1",
    }
    Keywords2IpRanges = {
        "red": ["10.0.2.1", "10.0.5.1"],
        "yellow": ["10.0.3.1", "10.0.6.1"],
        "blue": ["10.0.1.1", "10.0.4.1"]
    }
    Keywords2Ips = {
        "red": ["10.0.2.1", "10.0.3.1", "10.0.5.1"],
        "yellow": ["10.0.3.1", "10.0.4.1", "10.0.5.1", "10.0.6.1"],
        "blue": ["10.0.1.1", "10.0.4.1"]
    }
    associations = analyze_keywords.keyword_range_confidence(IfaceNames2Ips.values(), Keywords2IpRanges, Keywords2Ips)
    expected = {
        "red": [3, 4],
        "yellow": [4, 4],
        "blue": [2, 4]
    }
    assert associations == expected