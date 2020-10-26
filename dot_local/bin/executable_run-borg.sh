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
export BORG_REPO=root@DreSRV:/tank/backup/arch-desktop

# Setting this, so you won't be asked for your repository passphrase:
# export BORG_PASSPHRASE=''

# some helpers and error handling:
info() { printf "\n%s %s\n\n" "$( date )" "$*" >&2; }
trap 'echo $( date ) Backup interrupted >&2; exit 2' INT TERM

info "Starting backup"

# Backup the most important directories into an archive named after
# the machine this script is currently running on:

borg create                         \
    --stats                         \
    --show-rc                       \
    --compression auto,zstd         \
    --exclude-caches                \
    --exclude '/home/*/.cache/*'    \
    --exclude '/home/*/.local/share/baloo'      \
    --exclude '/home/*/.local/share/containers' \
    --exclude '/home/*/.snapshots'  \
    ::'{hostname}-{now}'            \
    /etc                            \
    /home                           \
    /root                           \

backup_exit=$?

info "Pruning repository"

# Use the `prune` subcommand to maintain 7 daily, 4 weekly and 6 monthly
# archives of THIS machine. The '{hostname}-' prefix is very important to
# limit prune's operation to this machine's archives and not apply to
# other machines' archives also:

borg prune                          \
    --list                          \
    --prefix '{hostname}-'          \
    --show-rc                       \
    --keep-daily    4               \
    --keep-weekly   2               \
    --keep-monthly  3               \

prune_exit=$?

# use highest exit code as global exit code
global_exit=$(( backup_exit > prune_exit ? backup_exit : prune_exit ))

if [ ${global_exit} -eq 0 ]; then
    info "Backup and Prune finished successfully"
elif [ ${global_exit} -eq 1 ]; then
    info "Backup and/or Prune finished with warnings"
else
    info "Backup and/or Prune finished with errors"
fi

unset BORG_REPO
exit ${global_exit}
