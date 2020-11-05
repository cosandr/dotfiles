#!/usr/bin/env python3

import json
import os
import platform
import shutil
import subprocess
from getpass import getpass
from socket import gethostname

if os.getenv('USER'):
    USER_HOME = os.path.expanduser("~{}".format(os.environ['USER']))
else:
    USER_HOME = os.path.expanduser("~")
if os.getenv('CHEZMOI_HOME'):
    CHEZMOI_HOME = os.environ['CHEZMOI_HOME']
else:
    CHEZMOI_HOME = os.path.join(USER_HOME, '.local/share/chezmoi')
CHEZMOI_CONFIG = os.path.join(USER_HOME, '.config/chezmoi/chezmoi.json')
CHEZMOI_CONFIG_TMPL = os.path.join(CHEZMOI_HOME, '.chezmoi.json.tmpl')
CHEZMOI_CONFIG_OLD = CHEZMOI_CONFIG + '.old'
HOSTNAME = gethostname()
SECRETS_FILE = os.path.join(CHEZMOI_HOME, '.secrets.json')
SECRETS_ENCRYPTED = os.path.join(CHEZMOI_HOME, 'secrets.json.gpg')
SECRETS_PASS = os.path.join(CHEZMOI_HOME, '.secrets_pass')
OS_NAME = platform.system()
if os.getenv('UPDATE') == '1':
    UPDATE = True
else:
    UPDATE = False

CONFIG = dict(
    data=dict(
        romsto=dict(
            domain="",
            ssh_port="",
        ),
        dresrv=dict(
            domain="",
            local_ip="",
            ssh_port="",
            use_domain=False,
        ),
        git=dict(
            private_email="",
            private_name="",
            public_email="",
            public_name="",
        ),
        check=dict(
            exec=[],
            source=[],
            files={},
            ignore_config={},
        ),
    ),
)


def check_cmds(cfg):
    """Check if commands are in PATH"""
    check = [
        "cargo",
        "corefreq-cli",
        "docker",
        "dotnet",
        "go-motd",
        "go",
        "podman",
        "pyenv",
        "virsh",
        "virt-install",
    ]
    cfg["data"]["check"]["exec"] = []
    for c in check:
        if shutil.which(c):
            cfg["data"]["check"]["exec"].append(c)
    return cfg


def check_src(cfg):
    """Check if files exist"""
    check = [
        "{}/.zprezto/init.zsh".format(USER_HOME),
        "/usr/share/zsh/site-functions/_podman",
        "/usr/share/zsh/site-functions/fzf",
        "/usr/share/fzf/shell/key-bindings.zsh",
        "/usr/share/fzf/completion.zsh",
        "/usr/share/fzf/key-bindings.zsh",
    ]
    cfg["data"]["check"]["source"] = []
    for c in check:
        if os.path.exists(c):
            cfg["data"]["check"]["source"].append(c)
    return cfg


def check_files(cfg):
    """Check if files exist"""
    check = dict(
        mrbot="srv/containers/containers/mrbot/src/mrbot.log",
        twitch_rec="srv/containers/containers/twitch/src/log/recorder.log",
        twitch_enc="srv/containers/containers/twitch/src/log/encoder.log",
    )
    path_prefix = ""
    if OS_NAME == "Linux":
        if HOSTNAME == 'DreSRV':
            path_prefix = '/'
        else:
            path_prefix = '/dresrv/'
    elif OS_NAME == "Windows":
        path_prefix = '//dresrv.local/'
    # join takes care of paths which were already absolute
    check = {k: os.path.join(path_prefix, v) for k, v in check.items()}
    cfg["data"]["check"]["files"] = {}
    for k, v in check.items():
        if os.path.exists(v):
            cfg["data"]["check"]["files"][k] = v
    return cfg


def check_ignore_config(cfg):
    check = {
        "alacritty": ".config/alacritty",
        "caddy": ".config/caddy",
        "chromium": ".config/chromium-flags.conf",
        "code": ".config/Code",
        "dunst": ".config/dunst",
        "feh": ".config/feh",
        "i3": ".config/i3",
        "kitty": ".config/kitty",
        "nvim": ".config/nvim",
        "picom": ".config/picom.conf",
        "polybar": ".config/polybar",
        "redshift": ".config/redshift",
        "rofi": ".config/rofi",
        "sublime_text": ".config/sublime-text-3",
        "tmuxinator": ".config/tmuxinator",
    }
    cfg["data"]["check"]["ignore_config"] = {}
    for k, v in check.items():
        cfg["data"]["check"]["ignore_config"][k] = {"cfg": v, "ok": bool(shutil.which(k))}
    return cfg


def json_str(cfg):
    return json.dumps(cfg, indent=2)


def write_json_file(obj, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, indent=1)


def read_json_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def update_secrets_pass():
    with open(SECRETS_PASS, 'w') as f:
        f.write(getpass('Enter secrets password: '))


def decrypt_secrets():
    """Decrypts secrets file using gpg"""
    if not os.path.exists(SECRETS_PASS):
        update_secrets_pass()
    try:
        subprocess.run(['gpg', '--batch', '--yes', '--passphrase-file', SECRETS_PASS,
                        '-o', SECRETS_FILE, '-d', SECRETS_ENCRYPTED], check=True)
    except Exception:
        os.unlink(SECRETS_PASS)
        exit(1)


def read_secrets():
    def _decrypt():
        if os.path.exists(SECRETS_ENCRYPTED):
            print('Decrypting secrets file: {} -> {}'.format(
                SECRETS_ENCRYPTED, SECRETS_FILE))
            decrypt_secrets()
        else:
            print('Secrets file [{}] not found, encrypted file missing [{}]'.format(
                SECRETS_FILE, SECRETS_ENCRYPTED))
    secrets = {}
    if not os.path.exists(SECRETS_FILE):
        _decrypt()
    if os.path.exists(SECRETS_FILE):
        # Update if encrypted file is newer
        if os.path.getmtime(SECRETS_ENCRYPTED) > os.path.getmtime(SECRETS_FILE):
            _decrypt()
        secrets = read_json_file(SECRETS_FILE)
    return secrets


def show_diff():
    # Print entire config if we have no old version
    if not os.path.exists(CHEZMOI_CONFIG_OLD):
        print(json_str(read_json_file(CHEZMOI_CONFIG)))
        return
    s = subprocess.run(['diff', '--unified', '--color=always', CHEZMOI_CONFIG_OLD, CHEZMOI_CONFIG])
    if s.returncode == 2:
        # --color=always fails on Windows and Alpine (maybe more)
        subprocess.run(['diff', '--unified', CHEZMOI_CONFIG_OLD, CHEZMOI_CONFIG])


def main():
    # Might not exist if we are using chezmoi --source
    if os.path.exists(CHEZMOI_HOME):
        # Update config template
        write_json_file(CONFIG, CHEZMOI_CONFIG_TMPL)

    cfg = CONFIG.copy()
    old_config = {}

    if os.path.exists(CHEZMOI_CONFIG):
        old_config = read_json_file(CHEZMOI_CONFIG)
        if UPDATE:
            cfg = old_config.copy()
    # Read secrets if not updating or if config is default
    if not UPDATE or cfg == CONFIG:
        secrets = read_secrets()
        cfg['data'] = {**cfg['data'], **secrets.get('data', {})}
        cfg["data"]["dresrv"]["use_domain"] = HOSTNAME not in ('desktop', 'DreSRV')

    cfg = check_cmds(cfg)
    cfg = check_files(cfg)
    cfg = check_src(cfg)
    cfg = check_ignore_config(cfg)

    if cfg == old_config:
        print('No config changes')
        return
    elif os.path.exists(CHEZMOI_CONFIG):
        shutil.move(CHEZMOI_CONFIG, CHEZMOI_CONFIG_OLD)

    # Write file
    write_json_file(cfg, CHEZMOI_CONFIG)

    # Display diff
    show_diff()


if __name__ == "__main__":
    main()
    if os.path.exists(CHEZMOI_CONFIG_OLD):
        os.unlink(CHEZMOI_CONFIG_OLD)
