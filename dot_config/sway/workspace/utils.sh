#!/bin/bash

launch_app() {
    case $1 in
        alacritty) alacritty ;;
        chrome) gtk-launch google-chrome ;;
        discord) gtk-launch discord ;;
        firefox) gtk-launch firefox ;;
        firefox-work) gtk-launch firefox-work ;;
        self-mon) "$HOME"/.local/bin/self-mon ;;
        slack) gtk-launch slack ;;
        spotify) gtk-launch spotify ;;
        srv-mon) TITLE=server-monitoring "$HOME"/.local/bin/theia-mon ;;
        vscode) "$HOME"/.local/bin/code --new-window "$2" ;;
    esac
}

launch_app_silent() {
    launch_app "$1" &>/dev/null &
}

wtype_sway_cmd() {
    case $1 in
        set_v) wtype -M win -k v ;;
        set_h) wtype -M win -k h ;;
        set_tabbed) wtype -M win -k v -s 200 -M win -k w ;;
        move_left) wtype -M win -k left ;;
        move_right) wtype -M win -k right ;;
    esac
    sleep 0.2
}

num_app_ids() {
    swaymsg -t get_tree | jq -e -r "[..|try select(.app_id | ascii_downcase == \"$1\")] | length"
}

num_names() {
    swaymsg -t get_tree | jq -e -r "[..|try select(.name | ascii_downcase == \"$1\")] | length"
}

wait_app_id() {
    local prev_num="$(num_app_ids "$1")"
    local tries=0
    while [[ "$(num_app_ids "$1")" -le "$prev_num" ]]; do
        sleep 0.1
        tries=$(( tries + 1))
        if [[ $tries -gt 50 ]]; then
            notify-send -a "Restore workspace $0" "Timeout waiting for app_id: $1"
            return
        fi
    done
}

wait_name() {
    local prev_num="$(num_names "$1")"
    local tries=0
    while [[ "$(num_names "$1")" -le "$prev_num" ]]; do
        sleep 0.1
        tries=$(( tries + 1))
        if [[ $tries -gt 50 ]]; then
            notify-send -a "Restore workspace $0" "Timeout waiting for name: $1"
            return
        fi
    done
}
