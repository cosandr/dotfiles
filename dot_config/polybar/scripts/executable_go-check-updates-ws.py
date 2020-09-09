#!/usr/bin/env python3

import asyncio
import json
import os
import signal
from contextlib import suppress

import websockets
from aiohttp import ClientSession, UnixConnector
import subprocess


class UpdatesClient:
    def __init__(self, loop, server):
        self.loop: asyncio.AbstractEventLoop = loop
        self.server: str = server
        self.sess: ClientSession = None
        self.ws: websockets.Connect = None
        self.api_uri: str = 'http://{}/api'
        self.ws_uri: str = 'ws://{}/ws'
        self.print_en = asyncio.Event()
        self.refresh_en = asyncio.Event()
        self.data = {}
        self.tasks = []
        signal.signal(signal.SIGUSR1, self.handler_notify)
        signal.signal(signal.SIGHUP, self.handler_refresh)

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
        self.tasks.append(self.loop.create_task(self.ws_task()))
        self.tasks.append(self.loop.create_task(self.print_task()))
        self.tasks.append(self.loop.create_task(self.refresh_task()))
        async with self.sess.get(url=self.api_uri, params=dict(updates='true')) as resp:
            if resp.status == 200:
                data = await resp.json()
                self.data = data.get('data', {})
        self.print_en.set()
        await asyncio.wait(self.tasks)

    async def close(self):
        await self.sess.close()
        await self.ws.close()

    def updates_str(self) -> str:
        if not self.data.get('updates'):
            return 'No pending updates'
        ret_str = ''
        for u in self.data['updates']:
            ret_str += f'{u["pkg"]} -> {u["newVer"]}\n'
        return ret_str.strip()

    def handler_notify(self, signum, frame):
        subprocess.run(["notify-send", "-u", "critical", "-a", "go-check-updates",
                       f'{self.get_numupdates()} pending updates', self.updates_str()])

    def handler_refresh(self, signum, frame):
        self.refresh_en.set()

    def get_numupdates(self) -> int:
        if not self.data.get('updates'):
            return 0
        return len(self.data['updates'])

    async def ws_task(self):
        async for msg in self.ws:
            with suppress(Exception):
                self.data = json.loads(msg)
                self.print_en.set()

    async def refresh_task(self):
        while True:
            await self.refresh_en.wait()
            async with self.sess.get(url=self.api_uri, params=dict(refresh='true')):
                pass
            self.refresh_en.clear()

    async def print_task(self):
        while True:
            await self.print_en.wait()
            print(self.get_numupdates())
            self.print_en.clear()


def main():
    loop = asyncio.get_event_loop()
    client = UpdatesClient(loop, server=os.getenv("SERVER", "localhost:8100"))
    try:
        loop.run_until_complete(client.run())
    finally:
        loop.run_until_complete(client.close())


if __name__ == "__main__":
    main()
