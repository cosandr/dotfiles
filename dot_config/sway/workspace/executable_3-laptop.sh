#!/bin/bash

set -eo pipefail

# shellcheck source=$HOME/.local/share/chezmoi/dot_config/sway/workspace/utils.sh
source "$HOME/.config/sway/workspace/utils.sh"

swaymsg workspace 3

launch_app_silent slack
wait_app_id slack
sleep 2
wtype_sway_cmd set_v

launch_app_silent firefox-work
wait_app_id firefox
wtype_sway_cmd set_tabbed

swaymsg resize set height 70 ppt
