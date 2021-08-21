#!/bin/bash

if ! command -v selinuxenabled &>/dev/null; then
    exit 0
fi

if selinuxenabled; then
    restorecon -r ~/.ssh
fi
