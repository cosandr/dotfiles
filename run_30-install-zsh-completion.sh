#!/bin/bash

if [[ ! -d ~/.zsh/completion ]]; then
    mkdir -p ~/.zsh/completion
fi

# Remove old compose completions
if [[ -f ~/.zsh/completion/_docker-compose ]]; then
    echo "Removing old docker-compose completions"
    rm -f ~/.zsh/completion/_docker-compose
fi

cmds=(docker kubectl minikube k9s flux argocd talosctl cilium chezmoi helm)

for cmd in "${cmds[@]}"; do
    if command -v "$cmd" &>/dev/null && [[ ! -f ~/.zsh/completion/_"$cmd" ]]; then
        echo "Generating completions for $cmd"
        "$cmd" completion zsh > ~/.zsh/completion/_"$cmd"
    fi
done
