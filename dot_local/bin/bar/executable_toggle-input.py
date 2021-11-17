#!/usr/bin/env python3

import re
import signal
import subprocess
from itertools import cycle

# Fix for inputs not switching
# Change in /etc/pulse/default.pa
# load-module module-stream-restore restore_device=false

def get_devs():
    # Get audio devices
    devs = {}
    s = subprocess.run(["pactl", "list", "sinks"], text=True, capture_output=True, check=True)
    sinks = re.split(r'Sink\s+\#\d+', s.stdout)
    for sink in sinks:
        desc = re.search(r'device\.description\s*=\s*\"(?P<desc>\S+).*\"', sink)
        name = re.search(r'node\.name\s*=\s*\"(?P<name>\S+)\"', sink)
        if desc and name:
            devs[name.group('name')] = desc.group('desc')
    return devs


def get_default():
    s = subprocess.run(["pactl", "info"], text=True, capture_output=True, check=True)
    for line in s.stdout.split('\n'):
        m = re.search(r'^Default Sink: (\S+)$', line)
        if m:
            return m.group(1)


def move_to_sink(sink: str):
    """Moves all current inputs to another sink"""
    # Get current sink inputs
    s = subprocess.run(["pactl", "list", "short", "sink-inputs"], text=True, capture_output=True, check=True)
    for m in re.finditer(r'(?P<input>\d+)\t(?P<sink>\d+)\t(?P<client>\d+)\t(?P<driver>\S+)\t(?P<spec>.*)', s.stdout):
        subprocess.run(["pactl", "move-sink-input", m.group('input'), sink], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def cycle_output():
    current = get_default()
    devs = get_devs()
    key_cycle = cycle(devs.keys())
    move_to = ""
    for _ in range(len(devs)):
        tmp = next(key_cycle)
        if tmp == current:
            move_to = next(key_cycle)
            break
    subprocess.run(["pactl", "set-default-sink", move_to], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    move_to_sink(move_to)
    subprocess.run(["notify-send", "-u", "low", f"Output device changed to {devs[move_to]}"])


def print_default():
    current = get_default()
    devs = get_devs()
    print(devs[current])


def handler_swap(signum, frame):
    cycle_output()
    print_default()


if __name__ == "__main__":
    signal.signal(signal.SIGHUP, handler_swap)
    print_default()
    while True:
        signal.pause()
