#!/bin/sh

# nerd-fonts

# `bluetoothctl info` version 5.60
# Battery Percentage: 0x46 (70)
ICON_OFF=${ICON_OFF:-""}
ICON_ON=${ICON_ON:-""}

if ! mac="$(bluetoothctl info | awk '/^Device/ {print $2}' | head -n1 | sed 's/:/_/g')"; then
    echo "$ICON_OFF"
    exit 0
fi

if [ -z "$mac" ]; then
    echo "$ICON_OFF"
    exit 0
fi

perc="$(dbus-send --print-reply=literal --system --dest=org.bluez \
    /org/bluez/hci0/dev_"$mac" org.freedesktop.DBus.Properties.Get \
    string:"org.bluez.Battery1" string:"Percentage" | grep -oP '\d+$')"

echo "${ICON_ON}${perc}%"
