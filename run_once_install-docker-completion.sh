#!/bin/bash

if command -v docker &>/dev/null; then
    docker_version=$(docker version -f 'v{{ .Client.Version }}')
    if [[ -n $docker_version ]]; then
        echo "Downloading Docker ${docker_version} ZSH completion"
        mkdir -p ~/.zsh/completion
        curl -sS \
            -L "https://raw.githubusercontent.com/docker/cli/${docker_version}/contrib/completion/zsh/_docker" \
            -o ~/.zsh/completion/_docker
    fi
fi

if command -v docker-compose &>/dev/null; then
    compose_version=$(docker-compose version --short)
    if [[ -n $compose_version ]]; then
        echo "Downloading docker-compose ${compose_version} ZSH completion"
        mkdir -p ~/.zsh/completion
        curl -sS \
            -L "https://raw.githubusercontent.com/docker/compose/${compose_version}/contrib/completion/zsh/_docker-compose" \
            -o ~/.zsh/completion/_docker-compose
    fi
fi
