#!/bin/bash

set -uo pipefail

# nerd-fonts

# `bluetoothctl info` version 5.60
# Battery Percentage: 0x46 (70)

# https://github.com/TheWeirdDev/Bluetooth_Headset_Battery_Level
# dnf install -y bluez-libs-devel python3-bluez
# pip3 install --user bluetooth_battery
ICON_OFF=${ICON_OFF:-""}
ICON_ON=${ICON_ON:-""}

if ! mac="$(bluetoothctl info | awk '/^Device/ {print $2}' | head -n1)"; then
    echo "$ICON_OFF"
    exit 0
fi

if [ -z "$mac" ]; then
    echo "$ICON_OFF"
    exit 0
fi

if command -v bluetooth_battery &> /dev/null; then
    # Battery level for F4:7D:EF:0C:BE:02 is 65%
    perc="$(bluetooth_battery "$mac" | grep -oP '\d+%$')"
else
    perc="$(dbus-send --print-reply=literal --system --dest=org.bluez \
    /org/bluez/hci0/dev_"${mac//:/_}" org.freedesktop.DBus.Properties.Get \
    string:"org.bluez.Battery1" string:"Percentage" 2>/dev/null | grep -oP '\d+$')"
fi

if [[ -n $perc ]]; then
    echo "${ICON_ON}${perc}%"
    exit 0
else
    echo "${ICON_ON}?%"
    exit 0
fi
