#!/bin/bash

# Ensure bitwarden is OK
bw_test=$(bw get item chezmoi)
if [[ $? -ne 0 ]]; then
    echo "$bw_test"
    echo "Bitwarden failed."
    exit 1
fi
cfg_path="$HOME/.config/chezmoi/chezmoi.toml"
# Make config
mkdir -p ~/.config/chezmoi
chezmoi cat ~/make_chezmoi_cfg > "$cfg_path"

# Check for installed commands
check_cmds=("corefreq-cli" "pyenv" "go" "virsh" "virt-install" "go-motd" "dotnet" "cargo")
avail_cmds=""
for cmd in "${check_cmds[@]}"; do
    if command -v "$cmd" &> /dev/null; then
        if [[ -z $avail_cmds ]]; then
            avail_cmds+="$cmd"
        else
            avail_cmds+=" $cmd"
        fi
    fi
done

# Don't add empty string
if [[ -n $avail_cmds ]]; then
    avail_cmds="    avail_cmds = \"${avail_cmds}\""
    echo -e "\n$avail_cmds" >> "$cfg_path"
fi

src_list=""
# Check for files to source
source_files=("$HOME/.keychain/$(uname -n)-sh" "/usr/share/zsh/site-functions/_podman" "/usr/share/zsh/site-functions/fzf")
for src in "${source_files[@]}"; do
    if [[ -f $src ]]; then
        if [[ -z $src_list ]]; then
            src_list+="$src"
        else
            src_list+=" $src"
        fi
    fi
done
# Don't add empty string
if [[ -n $src_list ]]; then
    src_list="    src_list = \"${src_list}\""
    if [[ -n $avail_cmds ]]; then
        echo "$src_list" >> "$cfg_path"
    else
        echo -e "\n$src_list" >> "$cfg_path"
    fi
fi

echo -e "Config created\n$(<"$cfg_path")"
