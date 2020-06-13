#!/usr/bin/env python3

import subprocess
import re
import sys


# <sink>: <friendly-name>
# Should only be two entries that toggle when this script runs
swap_between = {
    "alsa_output.usb-FiiO_FiiO_USB_DAC-E07K-01.analog-stereo": "DAC",
    "alsa_output.pci-0000_00_1f.3.analog-stereo": "MB",
}


def move_to_sink(sink: str):
    """Moves all current inputs to another sink"""
    # Get current sink inputs
    s = subprocess.run(["pactl", "list", "short", "sink-inputs"], text=True, capture_output=True, check=True)
    inputs = []
    for line in s.stdout.split('\n'):
        tmp = line.split()
        if len(tmp) == 7:
            inputs.append(tmp[0])
    for s_in in inputs:
        s = subprocess.run(["pactl", "move-sink-input", s_in, sink], capture_output=True, check=True)


if __name__ == "__main__":
    try:
        # Get current default
        s = subprocess.run(["pactl", "info"], text=True, capture_output=True, check=True)
        curr_default = ''
        for line in s.stdout.split('\n'):
            m = re.search(r'^Default Sink: (\S+)$', line)
            if m:
                curr_default = m.group(1)
                break
        if not curr_default:
            raise Exception('Cannot find current default')
        # Change defaults and current inputs
        keys = list(swap_between.keys())
        # Default is DAC
        if curr_default == keys[0]:
            move_to = keys[1]
            curr_name = swap_between[keys[0]]
        # Default is motherboard
        else:
            move_to = keys[0]
            curr_name = swap_between[keys[1]]
        if len(sys.argv) > 1 and sys.argv[1] == '--switch':
            s = subprocess.run(["pactl", "set-default-sink", move_to], capture_output=True, check=True)
            move_to_sink(move_to)
            curr_name = swap_between[move_to]
            s = subprocess.run(["notify-send", "-u", "low", f"Output device changed to {curr_name}"])
        print(curr_name)
    except:
        raise
        # Do nothing
        pass

# active_sink=$(pactl list short sinks | grep RUNNING | awk '{ print $2 }')

# if [ "$active_sink" = "$out_one" ]; then
#     pactl set-default-sink "$out_two"
#     echo "Changed default and moved inputs to $out_two"
# else
#     pactl set-default-sink "$out_one"
#     echo "Changed default and moved inputs to $out_one"
# fi
