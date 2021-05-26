#!/usr/bin/env python3

import json
import os
import platform
import shutil
import subprocess
from copy import deepcopy
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

DEFAULT_CONFIG = dict(
    data=dict(
        romsto=dict(
            domain="",
            ssh_port="",
        ),
        romrt=dict(
            domain="",
            ssh_user="",
            ssh_port="",
        ),
        dresrv=dict(
            domain="",
            local_ip="",
            ssh_port="",
            use_domain=False,
        ),
        git=dict(
            main_email="",
            main_name="",
            main_key="",
            alt_email="",
            alt_name=""
        ),
        check=dict(
            exec=[],
            files={},
            ignore_config=[],
            source=[],
        ),
        work=dict(
            git_name="",
            git_email="",
            git_key="",
            git_url="",
            ws_name="",
        )
    ),
)


def check_cmds(cfg):
    """Check if commands are in PATH"""
    check = [
        "docker",
        "dotnet",
        "kdeconnect-cli",
        "podman",
        "virsh",
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
        "/usr/local/opt/fzf/shell/completion.zsh",
        "/usr/local/opt/fzf/shell/key-bindings.zsh",
        "/opt/homebrew/opt/fzf/shell/completion.zsh",
        "/opt/homebrew/opt/fzf/shell/key-bindings.zsh",
    ]
    cfg["data"]["check"]["source"] = []
    for c in check:
        if os.path.exists(c):
            cfg["data"]["check"]["source"].append(c)
    return cfg


def check_files(cfg):
    """Check if files exist"""
    check = dict(
        mrbot="srv/containers/mrbot/src/mrbot.log",
        twitch="srv/containers/twitch/src/log/twitch.log",
    )
    path_prefix = ""
    if OS_NAME == "Linux":
        if HOSTNAME == 'DreSRV':
            path_prefix = '/'
        else:
            path_prefix = '/dresrv/'
    elif OS_NAME == "Windows":
        path_prefix = '//dresrv.hm/'
    if OS_NAME != "Windows":
        # join takes care of paths which were already absolute
        check = {k: os.path.join(path_prefix, v) for k, v in check.items()}
    else:
        # Join strings, ignore absolute paths
        check = {k: "{}{}".format(path_prefix, v) for k, v in check.items() if not k.startswith('/')}
    cfg["data"]["check"]["files"] = {}
    for k, v in check.items():
        cfg["data"]["check"]["files"][k] = v if os.path.exists(v) else ""
    return cfg


def check_ignore_config(cfg):
    check = {
        "alacritty": dict(path=".config/alacritty"),
        "caddy": dict(path=".config/caddy"),
        "chromium": dict(path=".config/chromium-flags.conf"),
        "google-chrome-stable": dict(path=".config/chrome-flags.conf"),
        "dunst": dict(path=".config/dunst"),
        "feh": dict(path=".config/feh"),
        "htop": dict(path=".config/htop", skip_root=False),
        "i3": dict(path=".config/i3"),
        "kitty": dict(path=".config/kitty"),
        "nvim": dict(path=".config/nvim", skip_root=False),
        "picom": dict(path=".config/picom.conf"),
        "polybar": dict(path=".config/polybar"),
        "redshift": dict(path=".config/redshift"),
        "rofi": dict(path=".config/rofi"),
        "sublime_text": dict(path=".config/sublime-text-3"),
        "sway": dict(path=".config/sway"),
        "tmuxinator": dict(path=".config/tmuxinator", skip_root=False),
        "waybar": dict(path=".config/waybar"),
    }
    cfg["data"]["check"]["ignore_config"] = []
    for k, v in check.items():
        cfg["data"]["check"]["ignore_config"].append(
            dict(
                path=v['path'],
                missing=not bool(shutil.which(k)),
                skip_root=v.get('skip_root', True),
            )
        )
    return cfg


def json_str(cfg):
    return json.dumps(cfg, indent=2)


def write_json_file(obj, path):
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
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
    subprocess.run(['git', 'diff', '--unified', '--color=always', CHEZMOI_CONFIG_OLD, CHEZMOI_CONFIG])


def main():
    # Might not exist if we are using chezmoi --source
    if os.path.exists(CHEZMOI_HOME):
        # Update config template
        write_json_file(DEFAULT_CONFIG, CHEZMOI_CONFIG_TMPL)

    cfg = deepcopy(DEFAULT_CONFIG)
    old_config = {}

    if os.path.exists(CHEZMOI_CONFIG):
        old_config = read_json_file(CHEZMOI_CONFIG)
        if UPDATE:
            cfg = deepcopy(old_config)
    # Read secrets if not updating or if config is default
    if not UPDATE or cfg == DEFAULT_CONFIG:
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
