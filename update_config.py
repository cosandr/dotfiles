#!/usr/bin/env python3

import json
import os
import subprocess
from shutil import which
from socket import gethostname

if os.getenv('USER'):
    USER_HOME = os.path.expanduser("~{}".format(os.environ['USER']))
else:
    USER_HOME = os.path.expanduser("~")
if os.getenv('CHEZMOI_HOME'):
    CHEZMOI_HOME = os.environ['CHEZMOI_HOME']
else:
    CHEZMOI_HOME = os.path.join(USER_HOME, '.local/share/chezmoi')
CHEZMOI_CONFIG = os.path.join(USER_HOME, '.config/chezmoi/chezmoi.toml')
CHEZMOI_CONFIG_TMPL = os.path.join(CHEZMOI_HOME, '.chezmoi.toml.tmpl')
HOSTNAME = gethostname()
INDENT_CHAR = '  '
SECRETS_FILE = os.path.join(CHEZMOI_HOME, '.secrets.json')
SECRETS_ENCRYPTED = os.path.join(CHEZMOI_HOME, 'secrets.json.gpg')
SECRETS_PASS = os.path.join(CHEZMOI_HOME, '.secrets_pass')


CONFIG = dict(
    data=dict(
        log_files=dict(
            discord="",
            twitch_rec="",
            twitch_enc="",
        ),
        dresrv=dict(
            domain="",
            local_ip="",
            ssh_port="",
            ssh_use_domain=False,
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
        ),
    ),
)

CHECK_CMDS = [
    "corefreq-cli",
    "pyenv",
    "go",
    "virsh",
    "virt-install",
    "go-motd",
    "dotnet",
    "cargo",
    "docker",
    "podman",
]

CHECK_SRC = [
    "{}/.zprezto/init.zsh".format(USER_HOME),
    "{}/.keychain/{}-sh".format(USER_HOME, HOSTNAME),
    "/usr/share/zsh/site-functions/_podman",
    "/usr/share/zsh/site-functions/fzf",
    "/usr/share/fzf/shell/key-bindings.zsh",
    "/usr/share/fzf/completion.zsh",
    "/usr/share/fzf/key-bindings.zsh",
]


def to_toml(cfg, depth=0, parent=''):
    toml_str = ''
    for k, v in cfg.items():
        if isinstance(v, dict):
            if parent:
                toml_str += "\n{}[{}.{}]\n".format(INDENT_CHAR * depth, parent, k)
            else:
                toml_str += "{}[{}]\n".format(INDENT_CHAR * depth, k)
            toml_str += to_toml(v, depth+1, parent=k)
            continue
        toml_str += "{}{} = ".format(INDENT_CHAR * depth, k)
        if isinstance(v, list):
            toml_str += "["
            v = ['"{}"'.format(el) for el in v]
            toml_str += ", ".join(v)
            toml_str += "]"
        elif isinstance(v, bool):
            toml_str += '{}'.format(str(v).lower())
        elif isinstance(v, (int, float)):
            toml_str += '{}'.format(str(v))
        else:
            toml_str += '"{}"'.format(str(v))
        toml_str += "\n"
    return toml_str


def to_json(cfg):
    return json.dumps(cfg, indent=2)

def update_secrets_pass():
    with open(SECRETS_PASS, 'w') as f:
        f.write(input('Enter secrets password: '))

def decrypt_secrets():
    """Decrypts secrets file using gpg"""
    if not os.path.exists(SECRETS_PASS):
        update_secrets_pass()
    try:
        subprocess.run(['gpg', '--batch', '--yes', '--passphrase-file', SECRETS_PASS,
                        '-o', SECRETS_FILE, '-d', SECRETS_ENCRYPTED], check=True)
    except:
        os.unlink(SECRETS_PASS)
        exit(1)

def read_secrets():
    secrets = {}
    if not os.path.exists(SECRETS_FILE):
        if os.path.exists(SECRETS_ENCRYPTED):
            print('Decrypting secrets file: {} -> {}'.format(
                SECRETS_ENCRYPTED, SECRETS_FILE))
            decrypt_secrets()
        else:
            print('Secrets file [{}] not found, encrypted file missing [{}]'.format(
                SECRETS_FILE, SECRETS_ENCRYPTED))
    if os.path.exists(SECRETS_FILE):
        with open(SECRETS_FILE, 'r') as f:
            secrets = json.load(f)
    return secrets

if __name__ == "__main__":
    # Might not exist if we are using chezmoi --source
    if os.path.exists(CHEZMOI_HOME):
        # Update config template
        with open(CHEZMOI_CONFIG_TMPL, 'w') as f:
            f.write(to_toml(CONFIG))
    cfg = CONFIG.copy()
    secrets = read_secrets()
    cfg['data'] = {**cfg['data'], **secrets.get('data', {})}

    log_files = dict(
        discord="/srv/containers/discord/src/discord.log",
        twitch_rec="/srv/containers/twitch/src/log/recorder.log",
        twitch_enc="/srv/containers/twitch/src/log/encoder.log",
    )
    if HOSTNAME != 'DreSRV':
        log_files = {k: '/mnt/sshfs{}'.format(v) for k, v in log_files.items()}
    for k in log_files.keys():
        if not os.path.exists(log_files[k]):
            log_files[k] = ""
    cfg["data"]['log_files'].update(log_files)

    cfg["data"]["dresrv"]["ssh_use_domain"] = HOSTNAME != 'desktop'

    for c in CHECK_CMDS:
        if which(c):
            cfg["data"]["check"]["exec"].append(c)

    for c in CHECK_SRC:
        if os.path.exists(c):
            cfg["data"]["check"]["source"].append(c)

    new_config = to_toml(cfg)
    old_config = ''
    # Backup old file
    if os.path.exists(CHEZMOI_CONFIG):
        # Read old file
        with open(CHEZMOI_CONFIG, 'r') as f:
            old_config = f.read()
        if new_config != old_config:
            os.rename(CHEZMOI_CONFIG, CHEZMOI_CONFIG + '.old')

    if new_config == old_config:
        exit(0)

    # Write file
    with open(CHEZMOI_CONFIG, 'w') as f:
        f.write(to_toml(cfg))
    
    # Display diff
    subprocess.run(['diff', '--unified', '--color=always', CHEZMOI_CONFIG + '.old', CHEZMOI_CONFIG])
