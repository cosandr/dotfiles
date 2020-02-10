#!/bin/bash


if [[ $EUID -ne 0 ]]; then
    echo "Run as root"
    exit 1
fi
run_as="/home/andrei"
cfg_file="/root/.config/chezmoi/chezmoi.toml"
mkdir -p /root/.config/chezmoi
cp "${run_as}/.config/chezmoi/chezmoi.toml" "$cfg_file"
./make_config.sh

chezmoi --source "${run_as}/.local/share/chezmoi" apply -v
