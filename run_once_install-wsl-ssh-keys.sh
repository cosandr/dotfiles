#!/bin/bash

# Only run on WSL
[[ $(uname -a | grep -ic microsoft) -eq 1 ]] || exit 0

cp -f /mnt/c/Users/Andrei/.ssh/*.pub ~/.ssh/
chmod 644 ~/.ssh/*.pub
