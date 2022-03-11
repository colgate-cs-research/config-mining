#!/usr/bin/env python3

import argparse
import os

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Commandline arguments')
    parser.add_argument('config_filepath',type=str, help='Path for a Juniper configuration file')
    parser.add_argument('output_path',type=str, help='Path in which to store the parts of the configuration')
    arguments = parser.parse_args()

    # Create output directory
    os.makedirs(arguments.output_path, exist_ok=True)

    # Open configuration file
    with open(arguments.config_filepath, 'r') as cfg_file:
        # TODO: iterate over configuration file and find sections

        # Sample code for writing to file
        section_name = "interfaces"
        section_contents = "interfaces {\n    testing\n}"
        with open(os.path.join(arguments.output_path, section_name+".cfg"), 'w') as out_file:
            out_file.write(section_contents)

if __name__ == "__main__":
    main()