#!/usr/bin/env python3

import re
import signal
import subprocess

# Fix for inputs not switching
# Change in /etc/pulse/default.pa
# load-module module-stream-restore restore_device=false

# <sink>: <friendly-name>
# Should only be two entries that toggle when this script runs
dev_list = {
    0: {
        "alsa_output.usb-0b0e_Jabra_Link_370_70BF9276CB92-00.analog-stereo": "Jabra",
    },
    1: {
        "alsa_output.pci-0000_2d_00.4.analog-stereo": "MB",
        "alsa_output.pci-0000_01_00.1.hdmi-stereo-extra3": "Sony",
    }
}
# Get audio devices
s = subprocess.run(["pactl", "list", "short", "sinks"], text=True, capture_output=True, check=True)
_avail_devs = []
for t in s.stdout.splitlines():
    tmp = t.split()
    if len(tmp) > 2:
        _avail_devs.append(tmp[1])

SWAP = {}
# Determine which devices are available
for dev, name in dev_list[0].items():
    if dev in _avail_devs:
        SWAP[dev] = name
        break

for dev, name in dev_list[1].items():
    if dev in _avail_devs:
        SWAP[dev] = name
        break

# No defined devices found, pick first two or fail
if len(SWAP) == 0:
    # Not enough devices to swap
    if len(_avail_devs) <= 1:
        print("Dev 1")
        exit(0)
    # Pick first two
    SWAP = {
        _avail_devs[0]: "Dev 1",
        _avail_devs[1]: "Dev 2",
    }
elif len(SWAP) == 1:
    # Not enough devices to swap
    if len(_avail_devs) <= 1:
        print(SWAP.get(_avail_devs[0], "Dev 1"))
        exit(0)
    # Pick the other
    for dev in _avail_devs:
        if dev not in SWAP:
            SWAP[dev] = "Dev 2"


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
