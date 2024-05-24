#!/bin/bash

swaymsg workspace 2
sleep 0.2

launch_app_silent self-mon
wait_name self-monitoring
wtype_sway_cmd set_h

launch_app_silent srv-mon
wait_name server-monitoring

wtype_sway_cmd move_left
wtype_sway_cmd set_v

launch_app_silent spotify
