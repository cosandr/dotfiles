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

# Find and set amdgpu hwmon
for i in /sys/class/hwmon/hwmon*/device/vendor; do
    # Found amdgpu
    if [[ $(<"$i") -eq "0x1002" ]] && [[ -f $(dirname "$i")/gpu_busy_percent ]]; then
        export HWMON_AMDGPU="$(dirname "$(dirname "$i")")"
    fi
done

# Find and set default network adapter, try for 5 seconds
PRIMARY_INET=""
for i in {1..5}; do
    PRIMARY_INET=$(route | grep '^default' | grep -m 1 -o '[^ ]*$')
    [[ -n $PRIMARY_INET ]] && break
    sleep 1
done
export PRIMARY_INET

# Load specific config if present
[[ -f ~/.config/override/polybar ]] && source ~/.config/override/polybar
launched=""
if [[ -n ${!MONITOR_MAP[*]} ]]; then
    present_monitors=$(xrandr --listmonitors)
    for k in "${!MONITOR_MAP[@]}"; do
        [[ $present_monitors =~ $k ]] || continue
        MONITOR="$k" polybar "${MONITOR_MAP[$k]}" &
        launched+="$k "
    done
fi
# Auto launch bars
while IFS='=' read -r name value ; do
    # Skip if it was launched earlier
    [[ $launched =~ $value ]] && continue
    if [[ $name = "MONITOR_NAME_0" ]]; then
        MONITOR="$value" polybar main &
    elif [[ $name == 'MONITOR_NAME_'* ]]; then
        MONITOR="$value" polybar secondary &
    fi
done < <(env)
