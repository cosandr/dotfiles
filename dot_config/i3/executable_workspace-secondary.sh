#!/bin/bash

if [[ -f $HOME/.config/i3/workspace-secondary-rotated ]]; then
i3-msg "workspace 2; append_layout $HOME/.config/i3/workspace-secondary-rotated.json"
elif [[ -f $HOME/.config/i3/workspace-secondary-no-discord ]]; then
i3-msg "workspace 2; append_layout $HOME/.config/i3/workspace-secondary-no-discord.json"
else
i3-msg "workspace 2; append_layout $HOME/.config/i3/workspace-secondary.json"
fi

spotify --force-device-scale-factor=1.5 &
kitty --detach --title self-monitoring tmuxinator start hjn --suppress-tmux-version-warning=SUPPRESS-TMUX-VERSION-WARNING &
"$HOME"/.config/i3/ssh-monitoring.sh &
[[ ! -f $HOME/.config/i3/workspace-secondary-no-discord ]] && discord
