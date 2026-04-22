#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HM_FLAKE_REF="github:nix-community/home-manager"

log() { printf '\n==> %s\n' "$*"; }

# 1. Install Determinate Nix if missing (flakes enabled by default)
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

# 2. Generate ed25519 SSH key (used for git commit signing) if missing
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

# 3. Activate the home-manager flake
case "$(uname -s)-$(uname -m)" in
  Linux-x86_64)   SYSTEM="x86_64-linux" ;;
  Linux-aarch64)  SYSTEM="aarch64-linux" ;;
  Darwin-arm64)   SYSTEM="aarch64-darwin" ;;
  *)
    echo "Unsupported system: $(uname -s)-$(uname -m)" >&2
    exit 1
    ;;
esac

FLAKE_ATTR="$REPO_ROOT#$SYSTEM"
# --impure lets the flake read $USER / $HOME at eval time so it works
# for whichever user is actually running this (not just clliaw).
if ! command -v home-manager >/dev/null 2>&1; then
  log "Applying home-manager flake ($FLAKE_ATTR) via nix run..."
  nix run "$HM_FLAKE_REF" -- switch --flake "$FLAKE_ATTR" -b backup --impure
else
  log "Running home-manager switch ($FLAKE_ATTR)..."
  home-manager switch --flake "$FLAKE_ATTR" -b backup --impure
fi

# 4. Switch login shell to the nix-managed zsh
ZSH_PATH="$HOME/.nix-profile/bin/zsh"
if [ -x "$ZSH_PATH" ]; then
  if ! grep -qxF "$ZSH_PATH" /etc/shells 2>/dev/null; then
    log "Registering $ZSH_PATH in /etc/shells..."
    echo "$ZSH_PATH" | sudo tee -a /etc/shells >/dev/null
  fi
  if [ "$SHELL" = "$ZSH_PATH" ]; then
    :  # already the login shell
  elif ! grep -q "^$USER:" /etc/passwd 2>/dev/null; then
    # Some cloud VMs put the login user in LDAP/SSSD/DirectoryService
    # rather than /etc/passwd, which makes chsh refuse. Skip automatic
    # chsh and leave breadcrumbs for the user to do it manually later.
    log "User '$USER' is not in /etc/passwd — skipping automatic chsh."
    log "To change your login shell manually later, run:"
    log "  sudo chsh -s $ZSH_PATH $USER"
  else
    log "Changing login shell to $ZSH_PATH..."
    sudo chsh -s "$ZSH_PATH" "$USER"
    # Kick sshd so the new shell is picked up on the next login (without this,
    # connections that predated chsh — incl. SSH ControlMaster reuse — keep bash).
    if command -v systemctl >/dev/null 2>&1; then
      for svc in ssh sshd; do
        if systemctl list-unit-files "${svc}.service" >/dev/null 2>&1; then
          sudo systemctl restart "$svc" || true
          break
        fi
      done
    fi
  fi
fi

# 5. Install node + bun via mise, pinned to the current latest. Run through the
#    nix zsh with -i so mise activation and the `muse` function (from
#    dotfiles/.zsh_aliases) are loaded.
ZSH_BIN="$HOME/.nix-profile/bin/zsh"
if [ -x "$ZSH_BIN" ]; then
  log "Installing node + bun via mise (pinned to current latest)..."
  "$ZSH_BIN" -ic 'muse node && muse bun'
fi

log "Done. Log out and back in to pick up the new shell + environment."
log "Public key for git signing:"
cat "$SSH_KEY.pub"
