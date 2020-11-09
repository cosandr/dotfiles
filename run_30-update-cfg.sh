#!/bin/bash

if [[ $EUID -eq 0 ]]; then
    UPDATE=1 "$(sudo -u andrei chezmoi source-path)"/update_config.py
else
    UPDATE=1 "$(chezmoi source-path)"/update_config.py
fi

