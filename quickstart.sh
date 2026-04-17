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

# 2. Install home-manager channel (nixpkgs is provided by Determinate)
log "Ensuring home-manager channel..."
nix-channel --add "$HM_CHANNEL" home-manager
nix-channel --update

# 3. Generate ed25519 SSH key (used for git commit signing) if missing
SSH_KEY="$HOME/.ssh/id_ed25519"
if [ ! -f "$SSH_KEY" ]; then
  log "Generating ed25519 SSH keypair at $SSH_KEY..."
  mkdir -p "$HOME/.ssh"
  chmod 700 "$HOME/.ssh"
  ssh-keygen -t ed25519 -f "$SSH_KEY" -C "cman101202@gmail.com" -N ""
fi

# Register key as a trusted signer so git can verify your own commits
ALLOWED_SIGNERS="$HOME/.ssh/allowed_signers"
SIGNER_LINE="cman101202@gmail.com $(cat "$SSH_KEY.pub")"
if [ ! -f "$ALLOWED_SIGNERS" ] || ! grep -qxF "$SIGNER_LINE" "$ALLOWED_SIGNERS"; then
  log "Adding signing key to $ALLOWED_SIGNERS..."
  printf '%s\n' "$SIGNER_LINE" >> "$ALLOWED_SIGNERS"
fi

# 4. Link this repo's home.nix into ~/.config/home-manager
log "Linking home.nix -> $REPO_ROOT/home.nix"
mkdir -p "$HOME/.config/home-manager"
ln -sfn "$REPO_ROOT/home.nix" "$HOME/.config/home-manager/home.nix"

# 5. Install home-manager, or just switch if already installed
if ! command -v home-manager >/dev/null 2>&1; then
  log "Installing home-manager..."
  nix-shell '<home-manager>' -A install
else
  log "Running home-manager switch..."
  home-manager switch -b backup
fi

# 6. Switch login shell to the nix-managed zsh
ZSH_PATH="$HOME/.nix-profile/bin/zsh"
if [ -x "$ZSH_PATH" ]; then
  if ! grep -qxF "$ZSH_PATH" /etc/shells 2>/dev/null; then
    log "Registering $ZSH_PATH in /etc/shells..."
    echo "$ZSH_PATH" | sudo tee -a /etc/shells >/dev/null
  fi
  if [ "$SHELL" != "$ZSH_PATH" ]; then
    log "Changing login shell to $ZSH_PATH..."
    sudo chsh -s "$ZSH_PATH" "$USER"
  fi
fi

log "Done. Log out and back in to pick up the new shell + environment."
log "Public key for git signing:"
cat "$SSH_KEY.pub"
