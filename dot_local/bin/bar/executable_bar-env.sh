#!/usr/bin/env bash

# Find and set CPU package
# https://github.com/polybar/polybar/issues/2078
for i in /sys/class/hwmon/hwmon*/temp*_input; do
    name="$(<"$(dirname "$i")"/name): $(cat "${i%_*}"_label 2>/dev/null || basename "${i%_*}")"
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
    if [[ $(<"$i") == "0x1002" ]] && [[ -f $(dirname "$i")/gpu_busy_percent ]]; then
        # shellcheck disable=SC2155
        export HWMON_AMDGPU="$(dirname "$(dirname "$i")")"
        break
    fi
done

# Find and set brightness device
for i in /sys/class/backlight/*/brightness; do
    # shellcheck disable=SC2155
    export BACKLIGHT_DEV="$(basename "$(dirname "$i")")"
    break
done

# Find and set default ethernet adapter
if ! PRIMARY_ETH=$(route | grep '^default' | awk '{print $NF}' | grep -m 1 '^e'); then
    PRIMARY_ETH=""
fi
export PRIMARY_ETH

# Find and set default wifi adapter
if ! PRIMARY_WLAN=$(route | grep '^default' | awk '{print $NF}' | grep -m 1 '^w'); then
    PRIMARY_WLAN=""
fi
export PRIMARY_WLAN

# shellcheck source=/dev/null
[[ -f ~/.config/override/bar-env ]] && source ~/.config/override/bar-env
