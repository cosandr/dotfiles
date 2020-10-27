#!/bin/bash

caddy_path="$HOME/.local/bin/caddy"

if [[ ! -f "$caddy_path" ]]; then
    curl -L -o "$caddy_path" 'https://caddyserver.com/api/download?os=linux&arch=amd64'
    chmod 755 "$caddy_path"
fi
