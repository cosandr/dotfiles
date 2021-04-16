#!/bin/sh

QUERY=${QUERY:-utilization.gpu}
UNIT=${UNIT:-"%"}

out=$(nvidia-smi --query-gpu="$QUERY" --format=csv,noheader,nounits)
if [ $? -ne 0 ]; then
    echo "N/A"
    sleep 5
    exit 1
fi
echo "${out%% *}$UNIT"
