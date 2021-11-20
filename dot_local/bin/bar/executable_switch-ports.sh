#!/bin/bash

PORT_OUT="analog-output-lineout"
PORT_HEAD="analog-output-headphones"

ACTIVE_PORT=$(pactl list sinks | grep -oP '^\s*Active Port: \K\S+')
[[ -z $ACTIVE_PORT ]] && notify-send -a 'Switch Port' "Cannot determine active port"

# Switch to headphones
if [[ "$ACTIVE_PORT" = "$PORT_OUT" ]]; then
    if pactl set-sink-port @DEFAULT_SINK@ "$PORT_HEAD"; then
        notify-send -a 'Switch Port' "Switched to headphones"
    else
        notify-send -a 'Switch Port' "Cannot switch to headphones"
    fi
# Switch to line out
else
    if pactl set-sink-port @DEFAULT_SINK@ "$PORT_OUT"; then
        notify-send -a 'Switch Port' "Switched to line out"
    else
        notify-send -a 'Switch Port' "Cannot switch to line out"
    fi
fi
