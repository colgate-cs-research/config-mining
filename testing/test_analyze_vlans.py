#!/usr/bin/env python3

import difflib
import os
import sys
import tempfile

# Load code to test
testing_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.dirname(testing_dir))
import analyze_vlans

def test_generate_vlan_pairs_one():
    vlan_list = [10]
    vlan_pair_freq = {}
    single_vlan_freq = {}
    analyze_vlans.generate_vlan_pairs(vlan_list, vlan_pair_freq, single_vlan_freq)
    assert len(vlan_pair_freq) == 0
    assert len(single_vlan_freq) == 1
    assert 10 in single_vlan_freq
    assert single_vlan_freq[10] == 1

def test_generate_vlan_pairs_two():
    vlan_list = [20, 21]
    vlan_pair_freq = {}
    single_vlan_freq = {}
    analyze_vlans.generate_vlan_pairs(vlan_list, vlan_pair_freq, single_vlan_freq)
    assert len(vlan_pair_freq) == 1
    assert (20, 21) in vlan_pair_freq
    assert vlan_pair_freq[(20, 21)] == 1
    assert len(single_vlan_freq) == 2
    assert 20 in single_vlan_freq
    assert single_vlan_freq[20] == 1
    assert 21 in single_vlan_freq
    assert single_vlan_freq[21] == 1

def test_generate_vlan_pairs_three():
    vlan_list = [30, 31, 32]
    vlan_pair_freq = {}
    single_vlan_freq = {}
    analyze_vlans.generate_vlan_pairs(vlan_list, vlan_pair_freq, single_vlan_freq)
    assert len(vlan_pair_freq) == 3
    assert (30, 31) in vlan_pair_freq
    assert vlan_pair_freq[(30, 31)] == 1
    assert (30, 32) in vlan_pair_freq
    assert vlan_pair_freq[(30, 32)] == 1
    assert (31, 32) in vlan_pair_freq
    assert vlan_pair_freq[(31, 32)] == 1
    assert len(single_vlan_freq) == 3
    assert 30 in single_vlan_freq
    assert single_vlan_freq[30] == 1
    assert 31 in single_vlan_freq
    assert single_vlan_freq[31] == 1
    assert 32 in single_vlan_freq
    assert single_vlan_freq[32] == 1

def test_generate_vlan_pairs_update():
    vlan_list = [10, 20, 21]
    vlan_pair_freq = { (20, 21) : 1 }
    single_vlan_freq = { 10: 1, 20: 1, 21: 1}
    analyze_vlans.generate_vlan_pairs(vlan_list, vlan_pair_freq, single_vlan_freq)
    assert len(vlan_pair_freq) == 3
    assert (10, 20) in vlan_pair_freq
    assert vlan_pair_freq[(10, 20)] == 1
    assert (10, 21) in vlan_pair_freq
    assert vlan_pair_freq[(10, 21)] == 1
    assert (20, 21) in vlan_pair_freq
    assert vlan_pair_freq[(20, 21)] == 2
    assert len(single_vlan_freq) == 3
    assert 10 in single_vlan_freq
    assert single_vlan_freq[10] == 2
    assert 20 in single_vlan_freq
    assert single_vlan_freq[20] == 2
    assert 21 in single_vlan_freq
    assert single_vlan_freq[21] == 2

def test_get_iface_accepted_vlans():
    configs_dir = os.path.join(testing_dir, "analysis", "configs_json")
    config_file = os.path.join(configs_dir, "vlans.json") 
    expected_dir = os.path.join(testing_dir, "analysis", "expected")
    expected_file = os.path.join(expected_dir, "analyze_vlans", "vlans.json") 
    out_dir = tempfile.mkdtemp()
    out_file = os.path.join(out_dir, "vlans.json")
    analyze_vlans.analyze_configuration(config_file, out_file)

    with open(out_file, 'r') as out:
        out_lines = out.readlines()

    with open(expected_file, 'r') as expected:
        expected_lines = expected.readlines()

    diff = list(difflib.unified_diff(expected_lines, out_lines))
    print(''.join(diff))
    assert len(diff) == 0