#!/usr/bin/env python3

import subprocess
import json
import sys


SOCK_PATH   = "/run/go-check-updates.sock"
RUN_QUERY   = "http://localhost/api?updates"
SERVER_PATH = "/mnt/sshfs/tmp/go-check-updates.json"


def updates_str(data: dict) -> str:
    if not data.get('updates'):
        return 'No pending updates'
    ret_str = ''
    for u in data['updates']:
        ret_str += f'{u["pkg"]} -> {u["newVer"]}\n'
    return ret_str.strip()


def main():
    if '--server' in sys.argv:
        with open(SERVER_PATH, 'r') as f:
            data = json.load(f)
    else:
        s = subprocess.run(["curl", "--unix-socket", SOCK_PATH, RUN_QUERY], check=True, capture_output=True, text=True)
        tmp = json.loads(s.stdout)
        if not tmp.get('data'):
            raise Exception('Empty response')
        data = tmp['data']
    if '--show' in sys.argv:
        print(updates_str(data))
    elif '--notify' in sys.argv:
        subprocess.run(["notify-send", "-u", "critical", updates_str(data)])
    else:
        if not data.get('updates'):
            print('0')
        else:
            print(len(data['updates']))


if __name__ == '__main__':
    if '--refresh' in sys.argv:
        RUN_QUERY += '&refresh'
    try:
        main()
    except:
        print('N/A')
