import re
import json
import argparse
import analyze
import ipaddress
import random


def regenerate(cfile, percentage, factor):
    with open(cfile, "r") as infile:
        config = json.load(infile)

    items = list(config[factor].values())
    length = len(items)
    ratio = percentage/100 * length
    new_items = []

    count = 0
    while count <= ratio:
        idx = random.randrange(length)
        new_items.append(items[idx])
        count += 1
    return new_items

#how to layout the json file

def main():
    lists = regenerate("/shared/configs/uwmadison/2014-10-core/configs_json/r-432nm-b3a-1-core.json", 1, "interfaces")
    print(lists)
if __name__ == "__main__":
    main()