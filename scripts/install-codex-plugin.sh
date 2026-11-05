#!/usr/bin/env bash
# feat(skills): Codex installs plugins as copies, so rerun this after editing a
# skill under dotfiles/plugins/iExalt to refresh what Codex sessions load.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
marketplace_root="$repo_root/dotfiles/plugins"
codex_bin="${CODEX_BIN:-$(command -v codex || true)}"
if [[ -z "$codex_bin" && -x "$HOME/.local/share/mise/shims/codex" ]]; then
  codex_bin="$HOME/.local/share/mise/shims/codex"
fi
if [[ -z "$codex_bin" ]]; then
  echo "install-codex-plugin: codex not found; skipping the iExalt plugin" >&2
  exit 0
fi

# Activation runs with a minimal PATH, so parse the listing in pure Bash.
marketplace_listed=false
while read -r name _; do
  [[ "$name" == iexalt ]] && marketplace_listed=true
done < <("$codex_bin" plugin marketplace list)
if [[ "$marketplace_listed" == false ]]; then
  "$codex_bin" plugin marketplace add "$marketplace_root"
fi
"$codex_bin" plugin add iExalt@iexalt
