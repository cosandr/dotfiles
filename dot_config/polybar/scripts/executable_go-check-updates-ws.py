#!/usr/bin/env python3

import asyncio
import json
import os
import signal
import sys

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

    def handler_notify(self):
        self.loop.create_task(self.handler_notify_async())

    async def handler_notify_async(self):
        await self.get_updates_api()
        print(self.get_numupdates())
        await self.send_notification(f'{self.get_numupdates()} pending', self.updates_str())

    def handler_refresh(self):
        self.loop.create_task(self.refresh())

    def handler_close(self):
        # takes too long to run
        # self.loop.create_task(self.handler_close_async())
        exit(0)

    async def handler_close_async(self):
        await self.close()
        exit(0)

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


def main():
    loop = asyncio.get_event_loop()
    if os.getenv('DEBUG', '0') == '1':
        print(f'PID: {os.getpid()}')
    client = UpdatesClient(loop, server=os.getenv("SERVER", "localhost:8100"))
    loop.run_until_complete(client.run())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print('N/A')
        print(e, file=sys.stderr)
        exit(1)
