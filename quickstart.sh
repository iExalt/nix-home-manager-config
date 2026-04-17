#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HM_CHANNEL="https://github.com/nix-community/home-manager/archive/release-25.11.tar.gz"

log() { printf '\n==> %s\n' "$*"; }

# 1. Install Determinate Nix if missing
if ! command -v nix >/dev/null 2>&1; then
  log "Installing Determinate Nix..."
  curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix \
    | sh -s -- install --determinate
fi

# Make nix available in this (non-login) shell
if [ -f /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh ]; then
  # shellcheck disable=SC1091
  . /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
fi

# 2. Add home-manager channel if missing
if ! nix-channel --list | grep -q '^home-manager '; then
  log "Adding home-manager channel..."
  nix-channel --add "$HM_CHANNEL" home-manager
  nix-channel --update
fi

# 3. Link this repo's home.nix into ~/.config/home-manager
log "Linking home.nix -> $REPO_ROOT/home.nix"
mkdir -p "$HOME/.config/home-manager"
ln -sfn "$REPO_ROOT/home.nix" "$HOME/.config/home-manager/home.nix"

# 4. Install home-manager, or just switch if already installed
if ! command -v home-manager >/dev/null 2>&1; then
  log "Installing home-manager..."
  nix-shell '<home-manager>' -A install
else
  log "Running home-manager switch..."
  home-manager switch -b backup
fi

log "Done. Start a new shell to pick up the environment."
