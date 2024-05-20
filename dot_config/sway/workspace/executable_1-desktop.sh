#!/bin/bash

set -eo pipefail

swaymsg workspace 1

sleep 0.2

gtk-launch firefox

# Wait for firefox to launch
while ! swaymsg -t get_tree | jq -e -r '..|try select(.app_id | ascii_downcase == "firefox")'; do sleep 0.1; done

wtype -M win -k h

sleep 0.2

alacritty &

# Wait for alacritty
while ! swaymsg -t get_tree | jq -e -r '..|try select(.app_id | ascii_downcase == "alacritty")'; do sleep 0.1; done

# Set alacritty to tabbed
wtype -M win -k v -s 500 -M win -k w

sleep 0.2

# Set next window on Firefox to vertical
wtype -M win -k left -s 500 -M win -k v
