#!/usr/bin/env python3

import subprocess
import json
import sys


SOCK_PATH = "/run/go-check-updates.sock"
RUN_QUERY = "http://localhost/api?updates"


def main():
    s = subprocess.run(["curl", "--unix-socket", SOCK_PATH, RUN_QUERY], check=True, capture_output=True, text=True)
    data = json.loads(s.stdout)
    if not data.get('data'):
        raise Exception('Empty response')
    if '--show' in sys.argv:
        for u in data['data'].get('updates', []):
            print(f'{u["pkg"]} -> {u["newVer"]}')
    elif '--notify' in sys.argv:
        if not data['data'].get('updates'):
            subprocess.run(["notify-send", "-u", "critical", "No pending updates"])
            sys.exit(0)
        send_str = ''
        for u in data['data']['updates']:
            send_str += f'{u["pkg"]} -> {u["newVer"]}\n'
        subprocess.run(["notify-send", "-u", "critical", send_str.strip()])
    else:
        if not data['data'].get('updates'):
            print('0')
        else:
            print(len(data['data']['updates']))

if __name__ == '__main__':
    if '--refresh' in sys.argv:
        RUN_QUERY += '&refresh'
    try:
        main()
    except:
        print('N/A')
