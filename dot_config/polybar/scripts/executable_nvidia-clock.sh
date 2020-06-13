#!/bin/sh

nvidia-smi --query-gpu=clocks.gr --format=csv,noheader,nounits | awk '{ print ""$1"","MHz"}'
