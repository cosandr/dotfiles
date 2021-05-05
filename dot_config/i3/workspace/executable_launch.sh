#!/bin/bash


declare -A ws_opts
ws_opts["1"]=""
ws_opts["2"]=""

# Example content
# ws_opts["1"]="work"
# ws_opts["2"]="work"
[[ -f ~/.i3_config ]] && source ~/.i3_config

for i in "${!ws_opts[@]}"; do
    name="$i"
    opt="${ws_opts[$i]}"
    file_name="$HOME/.config/i3/workspace/${name}.json"
    if [[ -n $opt ]]; then
        file_name_opt="$HOME/.config/i3/workspace/${name}-${opt}.json"
        if [[ -f $file_name_opt ]]; then
            file_name="$file_name_opt"
        else
            notify-send -a "Restore workspace ${name}" "File not found: ${file_name_opt}"
        fi
    fi
    i3-msg "workspace ${name}; append_layout ${file_name}"
    # Launch stuff if needed
    grep -q "spotify" "${file_name}" && gtk-launch spotify
    grep -q "self-monitoring" "${file_name}" && kitty --detach --title self-monitoring tmuxinator start hjn --suppress-tmux-version-warning=SUPPRESS-TMUX-VERSION-WARNING &
    grep -q "server-monitoring" "${file_name}" && "$HOME"/.config/i3/server-monitoring.sh &
    grep -q "workstation-monitoring" "${file_name}" && "$HOME"/.config/i3/workstation-monitoring.sh &
    grep -q "discord" "${file_name}" && gtk-launch discord
    grep -qiE 'name.*google\s+chrome' "${file_name}" && gtk-launch google-chrome
done
