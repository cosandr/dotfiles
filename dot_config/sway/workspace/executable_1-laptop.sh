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
    launch_app_silent alacritty
    wait_app_id alacritty
    wtype_sway_cmd set_tabbed

    launch_app_silent firefox-work
    wait_app_id firefox

    launch_app_silent awsvpnclient
    wait_app_id "aws vpn client"
    sleep 0.2
    wtype -k down
    sleep 0.2
    wtype -k down
    sleep 0.2
    wtype -k return
    sleep 0.5
    swaymsg move scratchpad

    # swaymsg workspace 3

    # TODO: Launches in the wrong workspace for some reason
    # launch_app_silent spotify
    # # https://github.com/electron/electron/issues/33578
    # wait_name "spotify premium"
    # wtype_sway_cmd set_tabbed

    # Crashes
    # launch_app_silent slack
    # wait_app_id slack

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
