#!/bin/bash

if [[ ! -d "${HOME}/.zprezto" ]]; then
    git clone --recursive https://github.com/sorin-ionescu/prezto.git "${HOME}/.zprezto"
else
    cd "${HOME}/.zprezto" || exit 1
    git pull --recurse-submodules
fi 
