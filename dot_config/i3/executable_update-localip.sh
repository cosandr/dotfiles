#!/bin/bash

SRV_IP="dresrv.hm"

# Wait for SSH agent
while [[ -z $SSH_AUTH_SOCK ]]; do sleep 1; done

for i in {0..4}; do
    if ping -c 1 -W 1 "$SRV_IP"; then
        break
    fi
done

if [[ $i -ge 4 ]]; then
    notify-send -a "Update DreSRV hosts" "Could not connect to DreSRV at $SRV_IP"
    exit 1
fi

set -e -o pipefail

primary_inet=$(route | grep '^default' | grep -m 1 -o '[^ ]*$')
all_ips=$(ip -o addr show scope global "$primary_inet" | awk '{gsub(/\/.*/,"",$4); print $4}')
MY_IPV4=$(awk 'NR==1' <<< "$all_ips")

sed_cmd="sed -i \"s/.*desktop.hm$/$MY_IPV4 desktop.hm/g\" /etc/hosts"

ssh root@DreSRV "$sed_cmd"

notify-send -a "Update DreSRV hosts" "Updated desktop.hm to $MY_IPV4"
