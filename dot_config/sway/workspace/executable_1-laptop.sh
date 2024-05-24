#!/bin/bash

set -eo pipefail

# shellcheck source=$HOME/.local/share/chezmoi/dot_config/sway/workspace/utils.sh
source "$HOME/.config/sway/workspace/utils.sh"

swaymsg workspace 1

MONITOR_COUNT="$(swaymsg -t get_outputs -r | jq '. | length')"

# At office
if [[ $MONITOR_COUNT -eq 3 ]]; then
    launch_app_silent self-mon
    wait_name self-monitoring
    wtype_sway_cmd set_h

    launch_app_silent spotify
# At home
# Maybe TODO: Check models and handle 2 monitors at work too
elif [[ $MONITOR_COUNT -eq 2 ]]; then
    echo "Not implemented"
# Laptop screen alone
elif [[ $MONITOR_COUNT -eq 1 ]]; then
    launch_app_silent alacritty
    wait_app_id alacritty
    wtype_sway_cmd set_tabbed

    swaymsg workspace 2
    sleep 0.2

    launch_app_silent firefox-work
    wait_app_id firefox
    wtype_sway_cmd set_tabbed

    swaymsg workspace 3
    sleep 0.2

    launch_app_silent slack
    wait_app_id slack
fi
