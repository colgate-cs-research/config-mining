import re
import json
import argparse
import analyze
import ipaddress
import random


def regenerate(cfile, percentage):
    with open(cfile, "r") as infile:
        config = json.load(infile)

    interfaces = list(config["interfaces"].values())
    length = len(interfaces)
    ratio = percentage/100 * length
    new_interfaces = []

    count = 0
    while count <= ratio:
        idx = random.randrange(length)
        new_interfaces.append(interfaces[idx])
        count += 1
    print(new_interfaces)

def main():
    regenerate("/shared/configs/uwmadison/2014-10-core/configs_json/r-432nm-b3a-1-core.json", 70)
if __name__ == "__main__":
    main()