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

drives=('c' 'd')
declare -a unlocked
declare -a mounted
# Add bitlk_c to /etc/crypttab
# bitlk_c  PARTUUID=<uuid>    /etc/bitlk_c.key  noauto,bitlk
for d in "${drives[@]}"; do
    if ! grep -q "win_$d" /proc/mounts ; then
        if grep -qE "^bitlk_$d" /etc/crypttab && [[ ! -b "/dev/mapper/bitlk_$d" ]] ; then
            echo "Unlocking $d"
            set -e
            systemctl start "systemd-cryptsetup@bitlk_$d.service"
            set +e
            unlocked+=("$d")
        fi
        echo "Mounting $d"
        set -e
        mount -o ro "/win_$d"
        set +e
        mounted+=("$d")
    fi
done

function cleanup {
    for d in "${mounted[@]}"; do
        echo "Unmounting $d"
        umount "/win_$d"
    done
    for d in "${unlocked[@]}"; do
        echo "Locking $d"
        systemctl start "systemd-cryptsetup@bitlk_$d.service"
    done
}

trap cleanup EXIT

# Check paths
declare -a backup_paths=()
declare -a check_paths=(
    "/win_c/Users/Andrei"
    "/win_d/Drivers"
    "/win_d/Other"
    "/win_d/Programs"
    "/win_d/src"
)
for p in "${check_paths[@]}"; do
    if [[ -d "$p" ]]; then
        backup_paths+=("$p")
    else
        echo "WARN: cannot backup $p: not found"
    fi
done
if [[ ${#backup_paths[@]} -eq 0 ]]; then
    echo "No backup paths found"
    exit 1
fi
echo "Backing up ${backup_paths[*]}"

echo "Starting backup"
export BORG_RELOCATED_REPO_ACCESS_IS_OK=yes

# Backup the most important directories into an archive named after
# the machine this script is currently running on:
# shellcheck disable=SC2086

borg create                         \
    --stats                         \
    --show-rc                       \
    --compression auto,zstd         \
    --noatime                       \
    --nobsdflags                    \
    --exclude-caches                \
    --exclude '/win_c/Users/Andrei/AppData/Local/Packages/Spotify*' \
    --exclude '/win_c/Users/Andrei/Downloads' \
    --exclude '/win_d/src/valve-leak' \
    ::'desktop_win-{now}'           \
    ${backup_paths[*]}

backup_exit=$?

echo "Pruning repository"

# Use the `prune` subcommand to maintain 7 daily, 4 weekly and 6 monthly
# archives of THIS machine. The '{hostname}-' prefix is very important to
# limit prune's operation to this machine's archives and not apply to
# other machines' archives also:

borg prune                          \
    --list                          \
    --prefix 'desktop_win-'         \
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
