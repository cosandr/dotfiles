#!/usr/bin/env python3

"""
Requires the following udev rule in /etc/udev/rules.d/45-ddcutil-i2c.rules
KERNEL=="i2c-[0-9]*", GROUP="andrei", MODE="0660", PROGRAM="/usr/bin/ddcutil --bus=%n getvcp 0x10"
Requires i2c-dev kernel module
echo 'i2c-dev' | sudo tee /etc/modules-load.d/i2c.conf
"""

import os
import re
import signal
import sys
import asyncio
import time
from typing import List, NamedTuple


class Preset(NamedTuple):
    day: int
    night: int


class Display:
    def __init__(self, name, bus, preset=None, selected=False, min_brightness=0, max_brigtness=100):
        self.name: str = name
        self.bus: int = bus
        self.preset: Preset = preset or Preset(day=40, night=0)
        self.brightness: int = None
        self.selected: bool = selected
        self.min_brightness: int = min_brightness
        self.max_brigtness: int = max_brigtness
        self._next_brightness: int = None

    @property
    def next_brightness(self):
        return self._next_brightness

    @next_brightness.setter
    def next_brightness(self, val: int):
        if val is not None:
            if val < self.min_brightness:
                val = self.min_brightness
            elif val > self.max_brigtness:
                val = self.max_brigtness
        self._next_brightness = val

    async def read_brightness(self):
        s = await asyncio.create_subprocess_exec(
            'ddcutil', '--bus', str(self.bus), '--terse', 'getvcp', '10',
            stdout=asyncio.subprocess.PIPE,
        )
        stdout, _ = await s.communicate()
        # Output for 5% brightness
        # VCP 10 C 5 100
        self.brightness = int(stdout.split()[3])
        self.next_brightness = self.brightness

    async def set_brightness(self, val: int = None):
        if val is None:
            val = self.next_brightness
        if self.brightness == val:
            return
        if val < 0:
            val = 0
        elif val > 100:
            val = 100
        s = await asyncio.create_subprocess_exec('ddcutil', '--bus', str(self.bus), 'setvcp', '10', str(val))
        await s.wait()
        self.brightness = val
        self.next_brightness = val

    async def toggle_preset(self):
        # Default to day
        if self.brightness is None:
            await self.set_brightness(self.preset.day)
        elif self.brightness > self.preset.night:
            await self.set_brightness(self.preset.night)
        else:
            await self.set_brightness(self.preset.day)


class MyDisplays:
    def __init__(self, delay=5, increment=10):
        self.displays: List[Display] = [
            Display(name='Acer', bus=4, preset=Preset(day=35, night=0), selected=True),
            Display(name='Samsung', bus=3, preset=Preset(day=25, night=5), selected=True,
                    min_brightness=5, max_brigtness=70),
        ]
        self.delay: int = delay
        self.increment: int = increment
        self._counter = 0
        self.selected_event = asyncio.Event()
        self.selected_task: asyncio.Task = None
        self.delay_event = asyncio.Event()
        asyncio.create_task(self.async_init())
        asyncio.create_task(self.delay_worker())
        loop = asyncio.get_running_loop()
        loop.add_signal_handler(signal.SIGUSR1, self.handler_up)
        loop.add_signal_handler(signal.SIGUSR2, self.handler_down)
        loop.add_signal_handler(signal.SIGHUP, lambda: asyncio.create_task(self.handler_toggle()))
        loop.add_signal_handler(signal.SIGALRM, lambda: asyncio.create_task(self.handler_cycle_selected()))

    async def async_init(self):
        try:
            await self.read_all()
        except Exception as e:
            print(e, file=sys.stderr)
            self.displays = await self.detect_displays()
            while not self.displays:
                print('N/A')
                await asyncio.sleep(30)
                self.displays = await self.detect_displays()
            self.read_all()

    @staticmethod
    async def detect_displays() -> List[Display]:
        displays = []
        s = await asyncio.create_subprocess_exec('ddcutil', 'detect', '--terse', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, _ = await s.communicate()
        for m in re.finditer(r"I2C bus:\s+\/dev\/i2c-(\d)\s+Monitor:\s+\w+:(\w+):?", stdout, re.S):
            bus = int(m.group(1))
            name = m.group(2)
            print(f'Found {name} on bus {bus}', file=sys.stderr)
            displays.append(Display(name=name, bus=bus, selected=True))
        return displays

    def handler_up(self):
        self._counter = 0
        for d in self.displays:
            if not d.selected:
                continue
            if d.next_brightness is None:
                d.next_brightness = 0
            else:
                d.next_brightness += self.increment
        self.delay_event.set()
        self.print(show_next=True)

    def handler_down(self):
        self._counter = 0
        for d in self.displays:
            if not d.selected:
                continue
            if d.next_brightness is None:
                d.next_brightness = 100
            else:
                d.next_brightness -= self.increment
        self.delay_event.set()
        self.print(show_next=True)

    async def handler_toggle(self):
        await self.toggle_preset()

    async def handler_cycle_selected(self):
        # Select first if all or no displays are selected
        sel_all = False
        sel_list = [d.selected for d in self.displays]
        if all(sel_list) or not any(sel_list):
            next_sel = 0
        else:
            # Get currently selected
            curr_sel = 0
            for i, sel in enumerate(sel_list):
                if sel:
                    curr_sel = i
                    break
            # Select all
            if curr_sel >= len(sel_list) - 1:
                sel_all = True
            else:
                next_sel = curr_sel + 1
        for i, d in enumerate(self.displays):
            if sel_all or i == next_sel:
                d.selected = True
            else:
                d.selected = False

        async def show_selected():
            self.print_selected(show_next=self.delay_event.is_set())
            await asyncio.sleep(1)
            if self.selected_event.is_set():
                self.selected_event.clear()
                return
            self.print(show_next=self.delay_event.is_set())

        if self.selected_task is not None and self.selected_task.done():
            self.selected_event.set()

        self.selected_task = asyncio.create_task(show_selected())

    async def toggle_preset(self):
        for d in self.displays:
            await d.toggle_preset()
        self.print()

    async def read_all(self):
        for d in self.displays:
            await d.read_brightness()
        self.print()

    async def set_all(self):
        for d in self.displays:
            if not d.selected:
                continue
            # Run in tasks?
            await d.set_brightness()
        self.print()

    def print(self, show_next=False):
        attr = 'next_brightness' if show_next else 'brightness'
        print(', '.join(
            [f'{getattr(d, attr)}%' if getattr(d, attr) is not None else 'N/A' for d in self.displays]
        ))

    def print_selected(self, show_next=False):
        attr = 'next_brightness' if show_next else 'brightness'
        tmp = []
        for d in self.displays:
            if d.selected:
                tmp.append(f'[{getattr(d, attr)}%]')
            else:
                tmp.append(f'{getattr(d, attr)}%')
        print(', '.join(tmp))

    async def delay_worker(self):
        """Waits for event and then sets all displays' brightness"""
        while True:
            await self.delay_event.wait()
            while self._counter < self.delay:
                await asyncio.sleep(1)
                self._counter += 1
            await self.set_all()
            self._counter = 0
            # Do stuff
            self.delay_event.clear()


async def main():
    md = MyDisplays(delay=2, increment=5)
    md.print()


if __name__ == "__main__":
    _f = None
    if os.getenv("DEBUG", "0") == "0":
        _f = open(os.devnull, 'w')
        sys.stderr = _f
    print(os.getpid(), file=sys.stderr)
    delay = int(os.getenv("DELAY", "0"))
    if delay != 0:
        time.sleep(delay)
    loop = asyncio.get_event_loop()
    try:
        loop.create_task(main())
        loop.run_forever()
    except Exception as e:
        print('N/A')
        print(e, file=sys.stderr)
        exit(1)
    if _f:
        _f.close()
