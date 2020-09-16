#!/usr/bin/env python3

"""
Requires the following udev rule in /etc/udev/rules.d/45-ddcutil-i2c.rules
KERNEL=="i2c-[0-9]*", GROUP="andrei", MODE="0660", PROGRAM="/usr/bin/ddcutil --bus=%n getvcp 0x10"
Requires i2c-dev kernel module
echo 'i2c-dev' > /etc/modules-load.d/i2c.conf
"""

import re
import signal
import subprocess
import time
from threading import Thread

from collections import namedtuple


Displays = namedtuple("Displays", ["main", "secondary"])
Preset = namedtuple("Preset", ["day", "night"])

DDC_GET = "ddcutil --bus={bus} --terse getvcp 10"
DDC_SET = "ddcutil --bus={bus} setvcp 10 {val}"
BUS_NUM = Displays(main=4, secondary=5)

PRESETS = Displays(
    main=Preset(day=35, night=0),
    secondary=Preset(day=25, night=5),
)

CURRENT = Displays(main=0, secondary=0)
NEXT = Displays(main=0, secondary=0)

# How many seconds to wait before changing brightness
DELAY = 5
COUNTER = 0
THREAD = None

def get_current():
    global CURRENT
    tmp = CURRENT._asdict()
    for name, bus in BUS_NUM._asdict().items():
        s = subprocess.run(DDC_GET.format(bus=bus).split(), text=True, capture_output=True)
        # Output for 5% brightness
        # VCP 10 C 5 100
        tmp[name] = int(s.stdout.split()[3])
    CURRENT = Displays(**tmp)

def print_brightness(vals=None):
    if not vals:
        vals = CURRENT
    # tmp = ["{}: {}%".format(k[0].upper(), v) for k, v in vals._asdict().items()]
    # print(", ".join(tmp))
    print(f'{vals.secondary}%, {vals.main}%')

def handler_up_down(signum, frame):
    global COUNTER, NEXT, THREAD
    COUNTER = 0
    if signum == signal.SIGUSR1:
        tmp = [v + 1 for v in NEXT]
    else:
        tmp = [v - 1 for v in NEXT]
    # Bounds check
    for i in range(len(tmp)):
        if tmp[i] < 0:
            tmp[i] = 0
        elif tmp[i] > 100:
            tmp[i] = 100
    NEXT = Displays(*tmp)
    print_brightness(NEXT)
    if THREAD is None or not THREAD.is_alive():
        THREAD = Thread(target=timer_thread, daemon=True)
        THREAD.start()

def handler_toggle(signum, frame):
    global CURRENT, NEXT
    new_curr = []
    curr_total = sum(CURRENT)
    night_total = sum([p.night for p in PRESETS])
    # We are in day mode
    if curr_total > night_total:
        for i, bus in enumerate(BUS_NUM):
            subprocess.run(DDC_SET.format(bus=bus, val=PRESETS[i].night).split(), check=True)
            new_curr.append(PRESETS[i].night)
    else:
        for i, bus in enumerate(BUS_NUM):
            subprocess.run(DDC_SET.format(bus=bus, val=PRESETS[i].day).split(), check=True)
            new_curr.append(PRESETS[i].day)
    CURRENT = Displays(*new_curr)
    NEXT = Displays(*new_curr)
    print_brightness()

def timer_thread():
    global CURRENT, COUNTER
    # print('Thread started')
    while COUNTER < DELAY:
        time.sleep(1)
        COUNTER += 1
        # print('Waiting... {}/{}'.format(COUNTER, DELAY))
    # print('Delay over')
    if CURRENT == NEXT:
        # print('No change')
        return

    new_curr = []
    for i, bus in enumerate(BUS_NUM):
        if CURRENT[i] == NEXT[i]:
            # print('No change for bus {}'.format(bus))
            continue
        subprocess.run(DDC_SET.format(bus=bus, val=NEXT[i]).split(), check=True)
        new_curr.append(NEXT[i])
    CURRENT = Displays(*new_curr)
    print_brightness()

if __name__ == "__main__":
    # # DEBUG
    # import os
    # print(os.getpid())
    # # DEBUG
    signal.signal(signal.SIGUSR1, handler_up_down)
    signal.signal(signal.SIGUSR2, handler_up_down)
    signal.signal(signal.SIGHUP, handler_toggle)
    get_current()
    NEXT = Displays(*CURRENT)
    print_brightness()
    while True:
        signal.pause()
