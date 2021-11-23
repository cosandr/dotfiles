#!/usr/bin/env python3

import asyncio
import re
import sys
from asyncio.subprocess import DEVNULL, PIPE
from itertools import cycle

from dbus_next.aio.message_bus import MessageBus
from dbus_next.service import ServiceInterface, method


# Fix for inputs not switching
# Change in /etc/pulse/default.pa
# load-module module-stream-restore restore_device=false
class AudioInterface(ServiceInterface):
    def __init__(self, name):
        super().__init__(name)

    @method()
    async def swap(self):
        await self.cycle_output()
        await self.print_default()

    async def get_devs(self):
        # Get audio devices
        devs = {}
        s = await asyncio.create_subprocess_exec("pactl", "list", "sinks", stdout=PIPE, stderr=DEVNULL)
        stdout = (await s.communicate())[0].decode()
        sinks = re.split(r'Sink\s+\#\d+', stdout)
        for sink in sinks:
            desc = re.search(r'device\.description\s*=\s*\"(?P<desc>\S+).*\"', sink)
            name = re.search(r'node\.name\s*=\s*\"(?P<name>\S+)\"', sink)
            if desc and name:
                devs[name.group('name')] = desc.group('desc')
        return devs

    async def get_default(self):
        s = await asyncio.create_subprocess_exec("pactl", "info", stdout=PIPE, stderr=DEVNULL)
        stdout = (await s.communicate())[0].decode()
        for line in stdout.split('\n'):
            m = re.search(r'^Default Sink: (\S+)$', line)
            if m:
                return m.group(1)

    async def move_to_sink(self, sink: str):
        """Moves all current inputs to another sink"""
        # Get current sink inputs
        s = await asyncio.create_subprocess_exec("pactl", "list", "short", "sink-inputs", stdout=PIPE, stderr=DEVNULL)
        stdout = (await s.communicate())[0].decode()
        for m in re.finditer(r'(?P<input>\d+)\t(?P<sink>\d+)\t(?P<client>\d+)\t(?P<driver>\S+)\t(?P<spec>.*)', stdout):
            await asyncio.create_subprocess_exec("pactl", "move-sink-input", m.group('input'), sink, stdout=DEVNULL, stderr=DEVNULL)

    async def cycle_output(self):
        current = await self.get_default()
        devs = await self.get_devs()
        key_cycle = cycle(devs.keys())
        move_to = ""
        for _ in range(len(devs)):
            tmp = next(key_cycle)
            if tmp == current:
                move_to = next(key_cycle)
                break
        await asyncio.create_subprocess_exec("pactl", "set-default-sink", move_to, stdout=DEVNULL, stderr=DEVNULL)
        await self.move_to_sink(move_to)
        await asyncio.create_subprocess_exec("notify-send", "-u", "low", f"Output device changed to {devs[move_to]}", stdout=DEVNULL, stderr=DEVNULL)

    async def print_default(self):
        current = await self.get_default()
        devs = await self.get_devs()
        print(devs[current])


async def main():
    name = 'com.andrei.audio'
    path = '/'
    interface_name = 'input.toggle'

    bus = await MessageBus().connect()
    interface = AudioInterface(interface_name)
    bus.export(path, interface)
    await bus.request_name(name)
    print(f'dest: "{name}", path: "{path}", interface: "{interface_name}"', file=sys.stderr)
    await interface.print_default()
    await bus.wait_for_disconnect()


if __name__ == "__main__":
    asyncio.run(main())
