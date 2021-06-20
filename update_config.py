#!/usr/bin/env python3

import json
import os
import subprocess
import sys
import shutil
from difflib import unified_diff

if os.getenv('USER'):
    USER_HOME = os.path.expanduser("~{}".format(os.environ['USER']))
else:
    USER_HOME = os.path.expanduser("~")


CHEZMOI_HOME = os.getenv('CHEZMOI_HOME') or subprocess.run(["chezmoi", "source-path"], universal_newlines=True, capture_output=True).stdout.strip()
CHEZMOI_CONFIG = os.getenv('CHEZMOI_CONFIG') or os.path.join(USER_HOME, '.config/chezmoi/chezmoi.json')
CHEZMOI_CONFIG_TMPL = os.getenv('CHEZMOI_CONFIG_TMPL') or os.path.join(CHEZMOI_HOME, '.chezmoi.json.tmpl')


def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as fw:
        fw.write(content)


def read_config():
    config = None
    with open(CHEZMOI_CONFIG, 'r', encoding='utf-8') as fr:
        config = fr.read()
    return config


def read_config_template():
    config = None
    with open(CHEZMOI_CONFIG_TMPL, 'r', encoding='utf-8') as fr:
        config = fr.read()
    s = subprocess.run(["chezmoi", "execute-template"], universal_newlines=True, input=config, capture_output=True)
    return s.stdout


def show_diff(new):
    if not new:
        return
    if not os.path.exists(CHEZMOI_CONFIG):
        return
    if not shutil.which('diff'):
        old = read_config()
        d = unified_diff([x + "\n" for x in old.splitlines()], [x + "\n" for x in new.splitlines()],
                         fromfile='before', tofile='after')
        sys.stdout.writelines(d)
        return
    try:
        subprocess.run(['diff', '--unified', '--color=always', '--', CHEZMOI_CONFIG, '-'], universal_newlines=True, input=new, check=True, capture_output=True).stdout
    except:
        subprocess.run(['diff', '--unified', '--', CHEZMOI_CONFIG, '-'], universal_newlines=True, input=new)


def main():
    # It's not possible for an existing config not to exist
    # if it doesn't somehow, just run chezmoi init
    old = read_config()
    new = read_config_template()
    if old == new:
        print('Config up to date')
        return
    # Show diff and ask if we update

    show_diff(new)
    print('\n')
    while True:
        action = input("[merge,overwrite,skip] ").lower()
        if action.startswith('m'):
            old_json = json.loads(old)
            new_json = json.loads(new)
            new_json['data'] = {**new_json['data'], **old_json['data']}
            new_str = json.dumps(new_json, indent=2)
            show_diff(new_str)
            if 'y' in input('Merge? [yN] ').lower():
                write_file(CHEZMOI_CONFIG, new_str)
                print('merged {}'.format(CHEZMOI_CONFIG))
            return
        elif action.startswith('o'):
            write_file(CHEZMOI_CONFIG, new)
            print('overwrote {}'.format(CHEZMOI_CONFIG))
            return
        elif action.startswith('s'):
            return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('\n\nCancelled')
