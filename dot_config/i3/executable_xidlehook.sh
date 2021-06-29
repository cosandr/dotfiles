#!/usr/bin/env bash

idle_hook=${idle_hook:-"xidlehook"}

[[ -f ~/.config/override/lock ]] && source ~/.config/override/lock

case $idle_hook in
    xidlehook)
        xidlehook \
            --not-when-fullscreen \
            --not-when-audio \
            --timer 600 \
            'xset dpms force off' \
            ''
        ;;
    xidlehook_lock)
        xidlehook \
            --not-when-fullscreen \
            --not-when-audio \
            --timer 590 \
            'xset dpms force off' \
            '' \
            --timer 10 \
            '"$HOME"/.local/bin/my-screenlock' \
            ''
        ;;
    xidlehook_lock_screen_on)
        xidlehook \
            --not-when-fullscreen \
            --not-when-audio \
            --timer 600 \
            '"$HOME"/.local/bin/my-screenlock screen_on' \
            ''
        ;;
    xidlehook_suspend)
        export PRIMARY_DISPLAY="$(xrandr | awk '/ primary/{print $1}')"
        xidlehook \
            --not-when-fullscreen \
            --not-when-audio \
            `# Dim the screen after 4m50s, undim if user becomes active` \
            --timer 290 \
            'xrandr --output "$PRIMARY_DISPLAY" --brightness .1' \
            'xrandr --output "$PRIMARY_DISPLAY" --brightness 1' \
            `# Undim & lock after 10 more seconds` \
            --timer 10 \
            'xrandr --output "$PRIMARY_DISPLAY" --brightness 1; "$HOME/.local/bin/my-screenlock"' \
            '' \
            `# Finally, suspend 5 minutes after it locks` \
            --timer 300 \
            'systemctl suspend' \
            ''
        ;;
    xfce4_power_manager)
        xfce4-power-manager &
        ;;
esac
