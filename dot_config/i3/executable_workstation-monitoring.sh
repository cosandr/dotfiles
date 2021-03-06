#!/bin/bash

# Wait for SSH agent
while [[ -z $SSH_AUTH_SOCK ]]; do sleep 1; done

# Wait for ws
while ! ssh -q -o "BatchMode=yes" ws exit &>/dev/null; do sleep 1; done

# Start terminal
kitty --detach --title workstation-monitoring ssh -t ws 'tmux new -s mon "htop -d10" \; split-window "journalctl -f" \; select-layout even-vertical || tmux attach -t mon'
