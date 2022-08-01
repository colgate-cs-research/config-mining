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
    elif kind == "pair":
        key = value[0] + " NAME"
    elif kind == "mixed":
        if len(value) == 1:
            key = value[0]
        elif len(value) == 2 and value[1] == "*":
            key = value[0] + " NAME"
        else:
            logging.error("!Unexpected mixed: {}".format(breadcrumb[0]))
    else:
        logging.error("!Breadcrumb has type {}: {}".format(kind, breadcrumb))
        return

    if key not in subtemplate:
        subtemplate[key] = {}
    elif isinstance(subtemplate[key], list):
        subtemplate[key] = {}

    if len(breadcrumb) > 2:
        add_breadcrumb(breadcrumb[1:], subtemplate[key])
    else:
        subtemplate[key] = [breadcrumb[1]]

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
    for breadcrumb, kind in keykinds.items():
        logging.debug("Adding {}".format(breadcrumb))
        add_breadcrumb(breadcrumb + (kind,), template)
        logging.debug("Updated template:\n{}".format(pprint.pformat(template)))
        
    logging.debug("Updated template:\n{}".format(pprint.pformat(template)))

    # Store template
    with open(os.path.join(arguments.infer_dir, "syntax_template.json"), 'w') as out_file:
        json.dump(template, out_file, indent=4, sort_keys=True)

if __name__ == "__main__":
    main()
