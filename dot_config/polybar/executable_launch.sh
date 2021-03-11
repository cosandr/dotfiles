#!/usr/bin/env bash

## Add this to your wm startup file.

# Terminate already running bar instances
killall -q polybar

# Wait until the processes have been shut down
while pgrep -u $UID -x polybar >/dev/null; do sleep 1; done

# Find and set CPU package
# https://github.com/polybar/polybar/issues/2078
for i in /sys/class/hwmon/hwmon*/temp*_input; do
    name="$(<$(dirname $i)/name): $(cat ${i%_*}_label 2>/dev/null || echo $(basename ${i%_*}))"
    if [ "$name" = "k10temp: Tctl" ]; then
        export HWMON_PATH="$i"
        break
    elif [ "$name" = "coretemp: Package id 0" ]; then
        export HWMON_PATH="$i"
        break
    fi
done

# Find and set default network adapter
PRIMARY_INET=""
while [[ -z $PRIMARY_INET ]]; do
    PRIMARY_INET=$(route | grep '^default' | grep -m 1 -o '[^ ]*$')
    sleep 1
done
export PRIMARY_INET

# Launch bars
while IFS='=' read -r name value ; do
    if [[ $name = "MONITOR_NAME_0" ]]; then
        MONITOR="$value" polybar main &
    elif [[ $name == 'MONITOR_NAME_'* ]]; then
        MONITOR="$value" polybar secondary &
    fi
done < <(env)
