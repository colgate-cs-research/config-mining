import argparse
import json
import ast
import logging
import pprint
import os

def add_breadcrumb(breadcrumb, subtemplate):
    kind, value = breadcrumb[0]
    if kind == "type":
        key = value
    elif kind == "name":
        key = "NAME"
    elif kind == "pair" or kind == "mixed":
        key = value[0] + " NAME"
    else:
        logging.error("!Breadcrumb has type {}: {}".format(kind, breadcrumb))
        return
    if key not in subtemplate:
        subtemplate[key] = {}
    if len(breadcrumb) > 1:
        add_breadcrumb(breadcrumb[1:], subtemplate[key])

def main():
    #Parse command-line arguments
    parser = argparse.ArgumentParser(description='Generate a configuration syntax template from inferred keykinds')
    parser.add_argument('infer_dir', help='Path to directory containing inference output')
    parser.add_argument('-v', '--verbose', action='count', help="Display verbose output", default=0)
    arguments=parser.parse_args()
    
    # module-wide logging
    if (arguments.verbose == 0):
        logging.basicConfig(level=logging.WARNING)
    elif (arguments.verbose == 1):
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.DEBUG)
    logging.getLogger(__name__)

    # Load inference results
    with open(os.path.join(arguments.infer_dir, "keykinds.json"), 'r') as in_file:
        pickle_keykinds = json.load(in_file) 
    keykinds = {ast.literal_eval(k) : v for k, v in pickle_keykinds.items()} 

    template = {}
    for breadcrumb in keykinds.keys():
        logging.debug("Adding {}".format(breadcrumb))
        add_breadcrumb(breadcrumb, template)
        logging.debug("Updated template:\n{}".format(pprint.pformat(template)))
        
    logging.debug("Updated template:\n{}".format(pprint.pformat(template)))

    # Store template
    with open(os.path.join(arguments.infer_dir, "syntax_template.json"), 'w') as out_file:
        json.dump(template, out_file, indent=4, sort_keys=True)

if __name__ == "__main__":
    main()
