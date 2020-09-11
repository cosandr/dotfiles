#!/usr/bin/env python3

import asyncio
import json
import os
import signal
from contextlib import suppress

import websockets
from aiohttp import ClientSession, UnixConnector


class UpdatesClient:
    def __init__(self, loop, server):
        self.loop: asyncio.AbstractEventLoop = loop
        self.server: str = server
        self.sess: ClientSession = None
        self.ws: websockets.Connect = None
        self.api_uri: str = 'http://{}/api'
        self.ws_uri: str = 'ws://{}/ws'
        self.data = {}
        self.loop.add_signal_handler(signal.SIGUSR1, self.handler_notify)
        self.loop.add_signal_handler(signal.SIGUSR2, self.handler_refresh)
        self.loop.add_signal_handler(signal.SIGTERM, self.handler_close)

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
        t = self.loop.create_task(self.ws_task())
        async with self.sess.get(url=self.api_uri, params=dict(updates='true')) as resp:
            data = await resp.json()
            self.data = data.get('data', {})
        print(self.get_numupdates())
        await t

    async def reconnect(self):
        if self.ws:
            await self.ws.close()
        if self.server.startswith('/'):
            self.ws = await websockets.unix_connect(self.server, uri=self.ws_uri)
        else:
            self.ws = await websockets.connect(self.ws_uri)

    async def close(self):
        if self.sess:
            await self.sess.close()
        if self.ws:
            await self.ws.close()

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

    def handler_notify(self):
        self.loop.create_task(self.send_notification(
            f'{self.get_numupdates()} pending',
            self.updates_str()
        ))

    def handler_refresh(self):
        self.loop.create_task(self.refresh())

    def handler_close(self):
        exit(0)

    def get_numupdates(self) -> int:
        if not self.data.get('updates'):
            return 0
        return len(self.data['updates'])

    async def ws_task(self):
        while True:
            try:
                async for msg in self.ws:
                    with suppress(Exception):
                        self.data = json.loads(msg)
                        print(self.get_numupdates())
            except Exception:
                print('N/A')
                with suppress(Exception):
                    await self.reconnect()

    async def refresh(self):
        await self.send_notification("Refreshing", level='normal')
        try:
            async with self.sess.get(url=self.api_uri, params=dict(refresh='true')) as resp:
                data = await resp.json()
                if data.get('error'):
                    await self.send_notification("Refresh failed", content=data['error'], level='critical')
        except Exception as e:
            await self.send_notification("Refresh failed", content=str(e), level='critical')


def main():
    loop = asyncio.get_event_loop()
    client = UpdatesClient(loop, server=os.getenv("SERVER", "localhost:8100"))
    try:
        loop.run_until_complete(client.run())
    except Exception:
        print('N/A')


if __name__ == "__main__":
    main()
