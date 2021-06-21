#!/usr/bin/env python3

import json
import os
import subprocess
import sys
import shutil
from getpass import getpass
from difflib import unified_diff

CHEZMOI_HOME = os.getenv('CHEZMOI_HOME') or subprocess.run(["chezmoi", "source-path"], universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.strip()
SECRETS_FILE = os.getenv('SECRETS_FILE') or os.path.join(CHEZMOI_HOME, '.chezmoidata.json')
SECRETS_ENCRYPTED = os.getenv('SECRETS_ENCRYPTED') or os.path.join(CHEZMOI_HOME, '.secrets.json.gpg')
SECRETS_PASS = os.getenv('SECRETS_PASS') or os.path.join(CHEZMOI_HOME, '.secrets.pass')
DRY_RUN = '-n' in sys.argv
VERBOSE = '-v' in sys.argv


def update_secrets_pass():
    with open(SECRETS_PASS, 'w') as f:
        f.write(getpass('Enter secrets password: '))


def ask_confirm(action):
    return 'y' in input("{}? [yN] ".format(action)).lower()


def write_file(path, content):
    with open(path, 'w', encoding='utf-8') as fw:
        fw.write(content)


def decrypt_secrets():
    """Decrypts secrets file using gpg"""
    if not os.path.exists(SECRETS_PASS):
        update_secrets_pass()
    try:
        return subprocess.run(['gpg', '--batch', '--yes', '--passphrase-file', SECRETS_PASS,
                               '-d', SECRETS_ENCRYPTED], universal_newlines=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
    except Exception:
        os.unlink(SECRETS_PASS)
        exit(1)


def encrypt_secrets():
    """Encrypts secrets file using gpg"""
    if not os.path.exists(SECRETS_PASS):
        update_secrets_pass()
    if DRY_RUN:
        return
    try:
        subprocess.run(['gpg', '--armor', '--symmetric', '--cipher-algo', 'AES256',
                        '--batch', '--yes', '--passphrase-file', SECRETS_PASS,
                        '-o', SECRETS_ENCRYPTED, SECRETS_FILE], check=True)
    except Exception:
        os.unlink(SECRETS_PASS)
        exit(1)


def read_secrets():
    secrets = None
    with open(SECRETS_FILE, 'r', encoding='utf-8') as fr:
        secrets = fr.read()
    return secrets


def show_diff(old):
    # Print entire file if we have no old version
    if not old:
        print('no old')
        return
    if not os.path.exists(SECRETS_FILE):
        print('no secrets')
        return
    if not shutil.which('diff'):
        new = read_secrets()
        d = unified_diff([x + "\n" for x in old.splitlines()], [x + "\n" for x in new.splitlines()],
                         fromfile='before', tofile='after')
        sys.stdout.writelines(d)
        return
    try:
        s = subprocess.run(['diff', '--unified', '--color=always', '--', '-', SECRETS_FILE], universal_newlines=True, input=old, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Exit status is 0 if inputs are the same, 1 if different, 2 if trouble.
        if s.returncode == 2:
            raise RuntimeError
        print(s.stdout)
    except RuntimeError:
        subprocess.run(['diff', '--unified', '--', '-', SECRETS_FILE], universal_newlines=True, input=old)


def main():
    if not os.path.exists(SECRETS_ENCRYPTED) and not os.path.exists(SECRETS_FILE):
        print("Cannot find encrypted [{}] nor decrypted [{}] file, nothing to do.".format(
            SECRETS_ENCRYPTED, SECRETS_FILE))
        exit(0)
    # No decrpyted secrets found
    if not os.path.exists(SECRETS_FILE):
        print('Decrypting secrets')
        new = decrypt_secrets()
        if not DRY_RUN:
            write_file(SECRETS_FILE, new)
        if VERBOSE:
            print(json.dumps(json.loads(new), indent=2))
        exit(0)
    # No encrypted file found
    if not os.path.exists(SECRETS_ENCRYPTED):
        print('Encrypting secrets')
        encrypt_secrets()
        if VERBOSE:
            new = json.loads(read_secrets())
            print(json.dumps(new, indent=2))
        exit(0)
    dec = read_secrets()
    enc = decrypt_secrets()
    if dec == enc:
        print('Secrets up to date')
        return
    # Update if encrypted file is newer
    if os.path.getmtime(SECRETS_ENCRYPTED) > os.path.getmtime(SECRETS_FILE):
        show_diff(dec)
        if ask_confirm("Replace decrypted secrets"):
            print('Updating decrypted secrets')
            if not DRY_RUN:
                write_file(SECRETS_FILE, enc)
        else:
            print('Updating encrypted secrets')
            encrypt_secrets()
    elif os.path.getmtime(SECRETS_FILE) > os.path.getmtime(SECRETS_ENCRYPTED):
        show_diff(enc)
        if ask_confirm("Replace encrypted secrets"):
            print('Updating encrypted secrets')
            encrypt_secrets()
        else:
            print('Updating decrypted secrets')
            if not DRY_RUN:
                write_file(SECRETS_FILE, enc)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print('\n\nCancelled')
