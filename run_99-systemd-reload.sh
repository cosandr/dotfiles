#!/bin/bash

# Only run if we have systemctl
command -v systemctl &>/dev/null || exit 0

systemctl --user daemon-reload
