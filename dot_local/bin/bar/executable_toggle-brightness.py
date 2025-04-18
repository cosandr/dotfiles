#!/usr/bin/env python3

"""
Requires the following udev rule in /etc/udev/rules.d/45-ddcutil-i2c.rules
KERNEL=="i2c-[0-9]*", GROUP="andrei", MODE="0660", PROGRAM="/usr/bin/ddcutil --bus=%n getvcp 0x10"
Requires i2c-dev kernel module
echo 'i2c-dev' | sudo tee /etc/modules-load.d/i2c.conf
"""

import asyncio
import os
import re
import sys
from typing import List, NamedTuple

from dbus_next.aio.message_bus import MessageBus
from dbus_next.service import ServiceInterface, method


class Preset(NamedTuple):
    day: int
    night: int


class MissingMonitorException(Exception):
    pass


KNOWN_MONITORS = {
    "U24E850": dict(preset=Preset(day=25, night=5), selected=True,
                    min_brightness=5, max_brigtness=70),
    "Gigabyte M32U": dict(preset=Preset(day=35, night=0), selected=True),
    "MPG321UX": dict(preset=Preset(day=40, night=0), selected=True),
}


DETECT_REGEX = [
    r"Display \d+\s+I2C bus:\s+\/dev\/i2c-(\d+)\s+DRM connector:\s+\S+\s+(?:\s+drm_connector_id:\s+\S+\s+)?Monitor:\s+\w+:([^:]+):",
    r"I2C bus:\s+\/dev\/i2c-(\d+)\s+Monitor:\s+\w+:([^:]+):",
]


DDCUTIL_SLEEP_MULTIPLIER = os.getenv("DDCUTIL_SLEEP_MULTIPLIER", "1")


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
            'ddcutil', '--sleep-multiplier', DDCUTIL_SLEEP_MULTIPLIER, '--bus', str(self.bus), '--terse', 'getvcp', '10',
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
        )
        stdout = (await s.communicate())[0].decode()
        print(f'read_brightness: {stdout}', file=sys.stderr)
        # Output for 5% brightness
        # VCP 10 C 5 100
        m = re.match(r'^VCP 10 C (\d+) \d+\s?$', stdout)
        if not m:
            raise MissingMonitorException(f'No monitor detected on bus {self.bus}')
        self.brightness = int(m.group(1))
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
        s = await asyncio.create_subprocess_exec('ddcutil', '--sleep-multiplier', DDCUTIL_SLEEP_MULTIPLIER, '--bus', str(self.bus), 'setvcp', '10', str(val))
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


class DisplayInterface(ServiceInterface):
    def __init__(self, name, delay=5, increment=10):
        super().__init__(name)
        self.displays: List[Display] = []
        self.delay: int = delay
        self.increment: int = increment
        self._counter = 0
        self.selected_event = asyncio.Event()
        self.selected_task: asyncio.Task = None
        self.delay_event = asyncio.Event()
        asyncio.create_task(self.async_init())
        asyncio.create_task(self.delay_worker())

    async def async_init(self):
        while not self.displays:
            self.displays = await self.detect_displays()
            try:
                await self.read_all()
                continue
            except Exception as e:
                print(e, file=sys.stderr)
            print('N/A')
            await asyncio.sleep(30)

    @staticmethod
    def get_known(name: str) -> dict:
        name_lower = name.lower()
        for k, v in KNOWN_MONITORS.items():
            k_lower = k.lower()
            if name_lower in k_lower or k_lower in name_lower:
                print(f'Matched "{name}" to "{k}"', file=sys.stderr)
                return dict(name=k, **v)
        return dict(name=name, selected=True)

    @staticmethod
    async def detect_displays() -> List[Display]:
        displays = []
        s = await asyncio.create_subprocess_exec('ddcutil', '--sleep-multiplier', DDCUTIL_SLEEP_MULTIPLIER, 'detect', '--terse', stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
        stdout = (await s.communicate())[0].decode()
        print(f'detect_displays:\n{stdout}', file=sys.stderr)
        re_matched = False
        for det_re in DETECT_REGEX:
            for m in re.finditer(det_re, stdout, re.S):
                re_matched = True
                bus = int(m.group(1))
                name = m.group(2)
                print(f'Found {name} on bus {bus}', file=sys.stderr)
                kwargs = DisplayInterface.get_known(name)
                displays.append(Display(bus=bus, **kwargs))
            if re_matched:
                break
        if not re_matched:
            print(f'No regex matched ddcutil output', file=sys.stderr)
        return displays

    @method()
    def up(self):
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

    @method()
    def down(self):
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

    @method()
    async def toggle(self):
        await self.toggle_preset()

    @method()
    async def cycle_selected(self):
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
            try:
                await d.read_brightness()
            except MissingMonitorException:
                pass
        if all([d.brightness is None for d in self.displays]):
            raise Exception('No monitors detected')
        # Remove invalid monitors
        self.displays = [d for d in self.displays if d.brightness is not None]
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
    delay = int(os.getenv("DELAY", "0"))
    if delay != 0:
        await asyncio.sleep(delay)

    name = 'com.andrei.brightness'
    path = os.getenv("BUS_PATH", "/")
    interface_name = 'ddcci.control'

    bus = await MessageBus().connect()
    interface = DisplayInterface(interface_name, delay=2, increment=5)
    bus.export(path, interface)
    await bus.request_name(name)
    print(f'dest: "{name}", path: "{path}", interface: "{interface_name}"', file=sys.stderr)
    interface.print()
    await bus.wait_for_disconnect()


if __name__ == "__main__":
    _f = None
    if os.getenv("DEBUG", "0") == "0":
        _f = open(os.devnull, 'w')
        sys.stderr = _f
    print(os.getpid(), file=sys.stderr)
    try:
        asyncio.run(main())
    except Exception as e:
        print('N/A')
        print(e, file=sys.stderr)
        exit(1)
    if _f:
        _f.close()
