#!/bin/bash

# Only run if we have systemctl
command -v systemctl &>/dev/null || exit 0

# Check if we have config dir
[[ -d ~/.config/systemd/user ]] || exit 0

# Check for stuff in there
[[ $(find ~/.config/systemd/user -type f | wc -l) -gt 0 ]] || exit 0

systemctl --user daemon-reload

# Ensure services are enabled
services=(
    "dresrv-gpg" "dresrv-tunnel" "dresrv-wait-online" "ws-gpg" "ws-proxy" "ws-wait-online"
    "dunst" "nextcloud"
    "kanshi" "swayidle" "waybar" "clipman"
    "auto-lock" "picom" "polybar" "redshift-gtk"
)

for srv in "${services[@]}"; do
    if [[ -f ~/.config/systemd/user/"$srv".service ]]; then
        systemctl --user enable "$srv".service
    fi
done
