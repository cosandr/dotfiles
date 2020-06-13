#!/bin/bash

# Wait for SSH agent
while [[ -z $SSH_AUTH_SOCK ]]; do sleep 1; done

# Start terminal
kitty --title server-monitoring ssh -t root@DreSRV 'tmux attach -t hjd' &
