#!/bin/bash

if [[ $EUID -ne 0 ]]; then
    echo "Must run as root"
    exit 1
fi

# Root requires SSH_AUTH_SOCK
# Run with sudo -E or set it manually (/run/user/1000/keyring/ssh)

if [[ -z $SSH_AUTH_SOCK ]]; then
    # Found socket
    if [[ -S /run/user/1000/keyring/ssh ]]; then
            export SSH_AUTH_SOCK=/run/user/1000/keyring/ssh
    else
        echo "Set SSH_AUTH_SOCK variable"
        exit 1
    fi
fi

# Setting this, so the repo does not need to be given on the commandline:
export BORG_REPO=root@DreSRV:/tank/backup/borg-windows

# Setting this, so you won't be asked for your repository passphrase:
# export BORG_PASSPHRASE=''

trap 'echo Backup interrupted >&2; exit 2' INT TERM

# Add bitlk_c to /etc/crypttab
# bitlk_c  PARTUUID=<uuid>    /etc/bitlk_c.key  noauto,bitlk
MOUNTED_WIN_C=0
if [[ ! -d /win_c/Users ]]; then
    echo "Mounting C:"
    set -e
    systemctl start systemd-cryptsetup@bitlk_c.service
    mount /win_c
    set +e
    MOUNTED_WIN_C=1
fi

function cleanup {
    if [[ $MOUNTED_WIN_C -eq 1 ]]; then
        echo "Unmounting C:"
        umount /win_c
        systemctl stop systemd-cryptsetup@bitlk_c.service
    fi
}

trap cleanup EXIT

echo "Starting backup"

# Backup the most important directories into an archive named after
# the machine this script is currently running on:

borg create                         \
    --stats                         \
    --show-rc                       \
    --compression auto,zstd         \
    --exclude-caches                \
    --exclude '/win_c/Users/Andrei/AppData/Local/Packages/Spotify*' \
    --exclude '/win_c/Users/Andrei/Downloads' \
    --exclude '/win_d/src/valve-leak' \
    ::'desktop-win-{now}'           \
    /win_c/Users/Andrei             \
    /win_d/Drivers                  \
    /win_d/Nvidia                   \
    /win_d/Other                    \
    /win_d/Programs                 \
    /win_d/src                      \

backup_exit=$?

echo "Pruning repository"

# Use the `prune` subcommand to maintain 7 daily, 4 weekly and 6 monthly
# archives of THIS machine. The '{hostname}-' prefix is very important to
# limit prune's operation to this machine's archives and not apply to
# other machines' archives also:

borg prune                          \
    --list                          \
    --prefix 'desktop-win-'         \
    --show-rc                       \
    --keep-daily    4               \
    --keep-weekly   2               \
    --keep-monthly  3               \

prune_exit=$?

# use highest exit code as global exit code
global_exit=$(( backup_exit > prune_exit ? backup_exit : prune_exit ))

if [ ${global_exit} -eq 0 ]; then
    echo "Backup and Prune finished successfully"
elif [ ${global_exit} -eq 1 ]; then
    echo "Backup and/or Prune finished with warnings"
else
    echo "Backup and/or Prune finished with errors"
fi

unset BORG_REPO

exit ${global_exit}
