#!/bin/bash

GRAPH_PATH="output/colgate/infer/graph.json"
OUTPUT_DIR="output/colgate/cycles_jun27"

for DEGREE in "2" "3"; do
    for START in "interface" "vlan" "keyword"; do
        python3 graphs/cycle_finding.py -d $DEGREE -s $START -t 90 \
            $GRAPH_PATH $OUTPUT_DIR/d-${DEGREE}_s-${START}_t-90.csv
        for NAMES in "interface" "vlan" "keyword" "group" "unit" "keyword-vlan"; do
            ARGS=`echo $NAMES | sed -e 's/-/ -n /'`
            python3 graphs/cycle_finding.py -d $DEGREE -s $START -n $ARGS -t 90 \
                $GRAPH_PATH $OUTPUT_DIR/d-${DEGREE}_s-${START}_t-90_n-${NAMES}.csv
        done
    done
done

