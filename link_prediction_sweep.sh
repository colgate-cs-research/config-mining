#!/bin/bash

# Example command: $ bash link_prediction_sweep.sh northwestern core1

if [[ $# -eq 2 ]]; then
    NETWORK=$1
    DEVICE=$2
else
    NETWORK="northwestern"
    DEVICE="core1"
    #NETWORK="uwmadison"
    #DEVICE="r-432nm-b3a-1-core"
fi
echo $NETWORK $DEVICE

GRAPH="/shared/config-mining/output/$NETWORK/graphs/$DEVICE.json"
OUTPUT_DIR="/shared/config-mining/output/$NETWORK/link_prediction/$DEVICE"
mkdir -p $OUTPUT_DIR

# Consider various types of nodes when computing fraction of common neighbors
for factor in "none" "vlan" "acl" "keyword"; do
    echo "***** COMMON $factor *****"
    date
    python3 -u link_prediction.py $GRAPH -c "{\"$factor\" : 1}" | tee $OUTPUT_DIR/common_factor_$factor.log
done
exit
# Consider various thresholds for declaring two nodes as similar
for thresh in 0.5 0.6 0.7 0.8 0.9; do
    echo "***** THRESH $thresh (COMMON) *****"
    date
    python3 -u link_prediction.py $GRAPH -t $thresh -c | tee $OUTPUT_DIR/common_thresh_$thresh.log
    echo "***** THRESH $thresh (NODE2VEC) *****"
    date
    python3 -u link_prediction.py $GRAPH -t $thresh -n | tee $OUTPUT_DIR/node2vec_thresh_$thresh.log
done

# Consider various number of random graph traversals for node2vec
for walks in 10 25 50 75 100 200 300 400 500; do
    echo "***** $walks WALKS *****"
    date
    python3 -u link_prediction.py $GRAPH -n "{\"num_walks\" : $walks}" | tee $OUTPUT_DIR/node2vec_walks_`printf %03d $walks`.log
done

# Consider various number of features for node2vec
for dims in 16 32 64 128 256; do
    echo "***** $dims DIMENSIONS *****"
    date
    python3 -u link_prediction.py $GRAPH -n "{\"dimensions\" : $dims}" | tee $OUTPUT_DIR/node2vec_dims_`printf %03d $dims`.log
done

# Consider various lengths of graph traversals for node2vec
for len in 2 5 10 20 30 40 50; do
    echo "***** $len LENGTH *****"
    date
    python3 -u link_prediction.py $GRAPH -n "{\"walk_length\" : $len}" | tee $OUTPUT_DIR/node2vec_len_`printf %02d $len`.log
done