#!/bin/bash

# Wait for SSH agent
while [[ -z $SSH_AUTH_SOCK ]]; do sleep 1; done


mountpoint="/mnt/sshfs"

if grep -q "$mountpoint" /proc/mounts
then
    notify-send "$mountpoint already mounted"
else
    sshfs andrei@DreSRV:/ "$mountpoint"
    notify-send "$mountpoint mounted"
fi
