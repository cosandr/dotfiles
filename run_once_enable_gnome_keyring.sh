#!/bin/bash

# Only run on Linux, excluding WSL
[[ $(uname -s) != "Linux" || $(uname -a | grep -ic microsoft) -eq 1 ]] && exit 0

systemctl --user enable gnome-keyring-daemon.service gcr-ssh-agent.service
