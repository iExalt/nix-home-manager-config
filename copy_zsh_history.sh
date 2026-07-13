#!/usr/bin/env bash
set -euo pipefail

old_history="$HOME/.zsh_history"
new_history="$HOME/.config/zsh/.zsh_history"

if [[ ! -f "$old_history" ]]; then
  printf 'error: old Zsh history does not exist: %s\n' "$old_history" >&2
  exit 1
fi

old_line_count="$(wc -l < "$old_history")"
new_line_count=0

if [[ -e "$new_history" ]]; then
  if [[ ! -f "$new_history" ]]; then
    printf 'error: new Zsh history is not a regular file: %s\n' "$new_history" >&2
    exit 1
  fi

  new_line_count="$(wc -l < "$new_history")"
fi

if (( new_line_count > old_line_count )); then
  printf 'error: refusing to overwrite %s (%d lines) with shorter history %s (%d lines)\n' \
    "$new_history" "$new_line_count" "$old_history" "$old_line_count" >&2
  exit 1
fi

mkdir -p "$(dirname "$new_history")"
cp -- "$old_history" "$new_history"
printf 'copied %d history lines from %s to %s\n' \
  "$old_line_count" "$old_history" "$new_history"
