#!/bin/bash

set -eo pipefail

# shellcheck source=$HOME/.local/share/chezmoi/dot_config/sway/workspace/utils.sh
source "$HOME/.config/sway/workspace/utils.sh"

swaymsg workspace 2

MONITOR_COUNT="$(swaymsg -t get_outputs -r | jq '. | length')"

# At office
if [[ $MONITOR_COUNT -eq 3 ]]; then
    launch_app_silent alacritty
    wait_app_id alacritty

    wtype_sway_cmd set_h

    launch_app_silent alacritty
    wait_app_id alacritty

    wtype_sway_cmd set_tabbed

    # Crashes instantly for some reason
    # launch_app_silent vscode ~/work/devops
    # wait_app_id code-url-handler

    # launch_app_silent vscode ~/work/customer_configuration
    # wait_app_id code-url-handler

    wtype_sway_cmd move_left
    wtype_sway_cmd set_tabbed
# At home
# Maybe TODO: Check models and handle 2 monitors at work too
elif [[ $MONITOR_COUNT -eq 2 ]]; then
    launch_app_silent alacritty
    wait_app_id alacritty

    wtype_sway_cmd set_h

    launch_app_silent alacritty
    wait_app_id alacritty

    wtype_sway_cmd set_tabbed

    wtype_sway_cmd move_left
    wtype_sway_cmd set_tabbed
fi
