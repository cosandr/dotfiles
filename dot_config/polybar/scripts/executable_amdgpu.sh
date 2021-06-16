#!/bin/bash

# https://github.com/Shaped/amdpwrman/blob/master/amdpwrman

if [[ -z $HWMON_AMDGPU ]]; then
    echo "N/A"
    exit 0
fi

QUERY=${QUERY:-gpu_usage}
UNIT=${UNIT:-"%"}

case $QUERY in
    gpu_usage)
        echo "$(<"$HWMON_AMDGPU"/device/gpu_busy_percent)${UNIT}"
        ;;
    mem_usage)
        echo "$(<"$HWMON_AMDGPU"/device/mem_busy_percent)${UNIT}"
        ;;
    gpu_clk)
        val="$(<"$HWMON_AMDGPU"/freq1_input)"
        echo "$(( val / 1000000 ))${UNIT}"
        ;;
    mem_clk)
        val="$(<"$HWMON_AMDGPU"/freq2_input)"
        echo "$(( val / 1000000 ))${UNIT}"
        ;;
    gpu_temp)
        val="$(<"$HWMON_AMDGPU"/temp1_input)"
        echo "$(( val / 1000 ))${UNIT}"
        ;;
    power)
        val="$(<"$HWMON_AMDGPU"/power1_average)"
        echo "$(( val / 1000000 ))${UNIT}"
        ;;
    *)
        echo "!Q!"
        exit 1
esac

exit 0
