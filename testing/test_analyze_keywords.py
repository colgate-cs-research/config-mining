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
        "green": [
            "green"
        ],
        "orange": [
            "orange"
        ],
        "red": [
            "red"
        ],
        "yellow": [
            "yellow"
        ]
    }
}

def test_get_common_keywords_once():
    common = analyze_keywords.get_common_keywords(keywords, "interfaces", 1)
    expected = ["red", "yellow", "blue"]
    assert sorted(common) == sorted(expected)

def test_get_common_keywords_thrice():
    common = analyze_keywords.get_common_keywords(keywords, "interfaces", 3)
    expected = ["red", "yellow"]
    assert sorted(common) == sorted(expected)

def test_keyword_interfaces():
    Keywords2IfaceNames = analyze_keywords.keyword_stanza(["red", "yellow", "blue"], keywords, "interfaces")
    expected = {
        "red" : ["GigabitEthernet0/2", "GigabitEthernet0/3", "GigabitEthernet0/5"],
        "yellow" : ["GigabitEthernet0/3", "GigabitEthernet0/4", "GigabitEthernet0/5", "GigabitEthernet0/6"],
        "blue" : ["GigabitEthernet0/1", "GigabitEthernet0/4"]
    }
    assert sorted(Keywords2IfaceNames.keys()) == sorted(expected.keys())
    for keyword in expected:
        assert sorted(Keywords2IfaceNames[keyword]) == sorted(expected[keyword])

def test_keyword_acls():
    Keywords2AclNames = analyze_keywords.keyword_stanza(["red", "yellow", "blue"], keywords, "acls")
    expected = {
        "red" : ["red"],
        "yellow" : ["yellow"],
        "blue" : []
    }
    assert sorted(Keywords2AclNames.keys()) == sorted(expected.keys())
    for keyword in expected:
        assert sorted(Keywords2AclNames[keyword]) == sorted(expected[keyword])