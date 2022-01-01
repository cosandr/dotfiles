#!/usr/bin/env python3

import asyncio
import json
import os
import sys

import websockets
from aiohttp import ClientSession, UnixConnector
from dbus_next.aio.message_bus import MessageBus
from dbus_next.service import ServiceInterface, method


class UpdatesClient(ServiceInterface):
    def __init__(self, name, server):
        super().__init__(name)
        self.server: str = server
        self.sess: ClientSession = None
        self.ws: websockets.Connect = None
        self.api_uri: str = 'http://{}/api'
        self.ws_uri: str = 'ws://{}/ws'
        self.data = {}

    @method()
    async def notify(self):
        await self.get_updates_api()
        print(self.get_numupdates())
        await self.send_notification(f'{self.get_numupdates()} pending', self.updates_str())

    @method()
    async def refresh(self):
        await self.send_notification("Refreshing", level='normal')
        try:
            async with self.sess.get(url=self.api_uri, params=dict(updates='true', refresh='true')) as resp:
                data = await resp.json()
                if data.get('error'):
                    return await self.send_notification("Refresh failed", content=data['error'], level='critical')
                self.data = data.get('data', {})
        except Exception as e:
            await self.send_notification("Refresh failed", content=str(e), level='critical')

    @method()
    async def close(self):
        if self.sess:
            await self.sess.close()
        if self.ws:
            await self.ws.close()

    @method()
    async def reconnect(self):
        if self.ws:
            await self.ws.close()
        if self.server.startswith('/'):
            self.ws = await websockets.unix_connect(self.server, uri=self.ws_uri)
        else:
            self.ws = await websockets.connect(self.ws_uri)

    async def run(self):
        if self.server.startswith('/'):
            self.api_uri = self.api_uri.format('localhost')
            self.ws_uri = self.ws_uri.format('localhost')
            self.sess = ClientSession(connector=UnixConnector(path=self.server))
            self.ws = await websockets.unix_connect(self.server, uri=self.ws_uri)
        else:
            self.api_uri = self.api_uri.format(self.server)
            self.ws_uri = self.ws_uri.format(self.server)
            self.sess = ClientSession()
            self.ws = await websockets.connect(self.ws_uri)
        await self.get_updates_api()
        print(self.get_numupdates())
        while True:
            try:
                await self.ws_task()
            except Exception:
                print('WS ERR')
                await self.reconnect()

    def updates_str(self) -> str:
        if not self.data.get('updates'):
            return 'No pending updates'
        ret_str = ''
        for u in self.data['updates']:
            ret_str += f'{u["pkg"]} -> {u["newVer"]}\n'
        return ret_str.strip()

    async def send_notification(self, title, content='', level='critical'):
        args = ["-u", level, "-a", f"Updates [{self.server}]", title]
        if content:
            args.append(content)
        p = await asyncio.create_subprocess_exec('notify-send', *args)
        await p.wait()

    def get_numupdates(self) -> int:
        if not self.data.get('updates'):
            return 0
        return len(self.data['updates'])

    async def ws_task(self):
        async for msg in self.ws:
            self.data = json.loads(msg)
            print(self.get_numupdates())

    async def get_updates_api(self):
        async with self.sess.get(url=self.api_uri, params=dict(updates='true')) as resp:
            data = await resp.json()
            self.data = data.get('data', {})


async def main():
    name = 'com.andrei.go-check-updates'
    path = os.getenv("BUS_PATH", "/")
    interface_name = 'gcu.control'

    bus = await MessageBus().connect()
    interface = UpdatesClient(interface_name, server=os.getenv("SERVER", "localhost:8100"))
    bus.export(path, interface)
    await bus.request_name(name)
    print(f'dest: "{name}", path: "{path}", interface: "{interface_name}"', file=sys.stderr)
    await interface.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print('N/A')
        print(e, file=sys.stderr)
        exit(1)
