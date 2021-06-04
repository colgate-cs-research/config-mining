#!/usr/bin/env python3

import os
import sys
import tempfile
import difflib

# Load code to test
testing_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.dirname(testing_dir))
import iacl_match

def test_acls():
    configs_dir = os.path.join(testing_dir, "parsing", "configs")
    config_file = os.path.join(configs_dir, "acls.conf") 
    expected_dir = os.path.join(testing_dir, "parsing", "expected")
    expected_file = os.path.join(expected_dir, "acls.out") 
    out_dir = tempfile.mkdtemp()
    out_file = os.path.join(out_dir, "acls.out")
    iacl_match.intraconfig_refs(config_file, out_file)

    with open(out_file, 'r') as out:
        out_lines = out.readlines()

    with open(expected_file, 'r') as expected:
        expected_lines = expected.readlines()

    diff = list(difflib.unified_diff(expected_lines, out_lines))
    print(''.join(diff))
    assert len(diff) == 0