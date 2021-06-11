#!/usr/bin/env python3

import os
import sys
import tempfile
import difflib

# Load code to test
testing_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.dirname(testing_dir))
import analyze_refs

configs_dir = os.path.join(testing_dir, "analysis", "configs_json")
expected_dir = os.path.join(testing_dir, "analysis", "expected")

def test_analyze_refs():
    config_file = os.path.join(configs_dir, "acls.json") 
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