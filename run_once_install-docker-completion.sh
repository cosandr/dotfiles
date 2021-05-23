#!/bin/bash

docker_version=$(docker version -f 'v{{ .Client.Version }}')
if [[ $? -eq 0 ]]; then
    echo "Downloading Docker ${docker_version} ZSH completion"
    mkdir -p ~/.zsh/completion
    curl -sS \
        -L "https://raw.githubusercontent.com/docker/cli/${docker_version}/contrib/completion/zsh/_docker" \
        -o ~/.zsh/completion/_docker
fi

compose_version=$(docker-compose version --short)
if [[ $? -eq 0 ]]; then
    echo "Downloading docker-compose ${compose_version} ZSH completion"
    mkdir -p ~/.zsh/completion
    curl -sS \
        -L "https://raw.githubusercontent.com/docker/compose/${compose_version}/contrib/completion/zsh/_docker-compose" \
        -o ~/.zsh/completion/_docker-compose
fi
