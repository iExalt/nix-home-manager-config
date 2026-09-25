#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

# fix(config): refresh stat data only when filtered content matches the index.
for config_file in dotfiles/.codex/config.toml dotfiles/.claude/settings.json; do
  [ -f "$config_file" ] || continue
  indexed_blob="$(git rev-parse --verify ":$config_file" 2>/dev/null)" || continue
  cleaned_blob="$(git hash-object --path="$config_file" "$config_file")"
  if [ "$indexed_blob" = "$cleaned_blob" ]; then
    git add --renormalize -- "$config_file"
  fi
done
git status "$@"
