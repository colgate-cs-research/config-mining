#!/bin/bash

if [ $# -ne 2 ]; then
    echo "Usage: inference_pipeline.sh CONFIGS_DIR OUTPUT_DIR"
    exit 1
fi

CONFIGS_DIR=$1
OUTPUT_DIR=$2

python3 parsing/infer_symbols.py $CONFIGS_DIR $OUTPUT_DIR
python3 evaluation/keykinds2syntax.py $OUTPUT_DIR
exit 2
python3 parsing/cleanup_symbols.py $OUTPUT_DIR
python3 parsing/infer_keywords.py $OUTPUT_DIR
python3 parsing/infer_relationships.py $CONFIGS_DIR $OUTPUT_DIR
python3 parsing/infer_graph.py -v -p $OUTPUT_DIR $OUTPUT_DIR