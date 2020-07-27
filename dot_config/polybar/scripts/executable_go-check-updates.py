#!/usr/bin/env python3

import argparse
import json
import subprocess
import signal
import time


SOCK_PATH   = "/run/go-check-updates.sock"
RUN_QUERY   = "http://localhost/api?updates&refresh"
SERVER_PATH = "/mnt/sshfs/tmp/go-check-updates.json"
DATA        = {}



parser = argparse.ArgumentParser()
parser.add_argument('--server', action='store_true', help=f'Read updates from server file at {SERVER_PATH}')
parser.add_argument('--minutes', type=int, required=False, help='Only refresh if enough minutes have passed')
args = parser.parse_args()


def update_data():
    global DATA
    if args.server:
        with open(SERVER_PATH, 'r') as f:
            DATA = json.load(f)
    else:
        s = subprocess.run(["curl", "--unix-socket", SOCK_PATH, RUN_QUERY], check=True, capture_output=True, text=True)
        tmp = json.loads(s.stdout)
        if not tmp.get('data'):
            raise Exception('Empty response')
        DATA = tmp['data']


def get_numupdates() -> int:
    if not DATA.get('updates'):
        return 0
    else:
        return len(DATA['updates'])


def handler_notify(signum, frame):
    subprocess.run(["notify-send", "-u", "critical", "-a", "go-check-updates",
                    f'{get_numupdates()} pending updates', updates_str(DATA)])


def handler_refresh(signum, frame):
    update_data()
    print(get_numupdates())


def updates_str(data: dict) -> str:
    if not data.get('updates'):
        return 'No pending updates'
    ret_str = ''
    for u in data['updates']:
        ret_str += f'{u["pkg"]} -> {u["newVer"]}\n'
    return ret_str.strip()


if __name__ == '__main__':
    signal.signal(signal.SIGUSR1, handler_notify)
    signal.signal(signal.SIGHUP, handler_refresh)
    last_update = 0
    wait_time = 0
    while True:
        # print(f'Seconds passed: {time.time() - last_update}')
        if args.minutes and time.time() - last_update >= args.minutes * 60:
            # print('updating data')
            try:
                update_data()
                last_update = time.time()
                print(get_numupdates())
            except:
                print('N/A')
        time.sleep(60)
