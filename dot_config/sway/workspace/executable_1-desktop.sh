#!/bin/bash

set -eo pipefail

swaymsg workspace 1
sleep 0.2

launch_app_silent firefox
wait_app_id firefox
wtype_sway_cmd set_h

launch_app_silent alacritty
wait_app_id alacritty
wtype_sway_cmd set_tabbed

# Set next window on Firefox to vertical
wtype_sway_cmd move_left
wtype_sway_cmd set_v
