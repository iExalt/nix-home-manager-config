#!/bin/bash

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEM="$(nix eval --impure --raw --expr 'builtins.currentSystem')"

home-manager switch --flake "path:$REPO_ROOT#$SYSTEM" --impure
