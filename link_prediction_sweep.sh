#!/bin/bash

GRAPH="output/northwestern/graphs/core1.json"
OUTPUT_DIR="output/northwestern/link_prediction"

for walks in 10 25 50 75 100 200 300 400 500; do
    echo "***** $walks WALKS *****"
    date
    python3 -u link_prediction.py $GRAPH -n "{\"num_walks\" : $walks}" | tee $OUTPUT_DIR/walks_$walks.log
done

for dims in 16 32 64 128 256; do
    echo "***** $dims DIMENSIONS *****"
    date
    python3 -u link_prediction.py $GRAPH -n "{\"dimensions\" : $dims}" | tee $OUTPUT_DIR/dims_$dims.log
done

for len in 2 5 10 20 30 40 50; do
    echo "***** $len LENGTH *****"
    date
    python3 -u link_prediction.py $GRAPH -n "{\"walk_length\" : $len}" | tee $OUTPUT_DIR/len_$len.log
done