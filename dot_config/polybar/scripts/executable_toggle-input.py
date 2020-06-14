#!/usr/bin/env python3

import re
import signal
import subprocess

# <sink>: <friendly-name>
# Should only be two entries that toggle when this script runs
SWAP = {
    "alsa_output.usb-FiiO_FiiO_USB_DAC-E07K-01.analog-stereo": "DAC",
    "alsa_output.pci-0000_00_1f.3.analog-stereo": "MB",
}
SWAP_KEYS = list(SWAP.keys())
CURRENT_DEFAULT = ''


def update_default():
    global CURRENT_DEFAULT
    s = subprocess.run(["pactl", "info"], text=True, capture_output=True, check=True)
    for line in s.stdout.split('\n'):
        m = re.search(r'^Default Sink: (\S+)$', line)
        if m:
            CURRENT_DEFAULT = m.group(1)
            break


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


def swap_default():
    global CURRENT_DEFAULT
    # Default is DAC
    if CURRENT_DEFAULT == SWAP_KEYS[0]:
        move_to = SWAP_KEYS[1]
    # Default is motherboard
    else:
        move_to = SWAP_KEYS[0]
    s = subprocess.run(["pactl", "set-default-sink", move_to], capture_output=True, check=True)
    move_to_sink(move_to)
    subprocess.run(["notify-send", "-u", "low", f"Output device changed to {SWAP[move_to]}"])
    CURRENT_DEFAULT = move_to


def print_default():
    print(SWAP.get(CURRENT_DEFAULT, 'N/A'))


def handler_swap(signum, frame):
    update_default()
    swap_default()
    print_default()


if __name__ == "__main__":
    signal.signal(signal.SIGHUP, handler_swap)
    update_default()
    print_default()
    while True:
        signal.pause()
