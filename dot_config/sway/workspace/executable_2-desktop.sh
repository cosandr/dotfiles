#!/bin/bash

swaymsg workspace 2

sleep 0.2

self-mon &

while ! swaymsg -t get_tree | jq -e -r '..|try select(.name == "self-monitoring")'; do sleep 0.1; done

wtype -M win -k h

TITLE=server-monitoring theia-mon &

while ! swaymsg -t get_tree | jq -e -r '..|try select(.name == "server-monitoring")'; do sleep 0.1; done

# Back to self-mon and set vertical mode
wtype -M win -k left -s 500 -M win -k v

sleep 0.2

gtk-launch spotify
