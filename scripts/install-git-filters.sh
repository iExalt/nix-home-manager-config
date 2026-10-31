#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
# feat(config): resolve Mise's Python once so Git does not invoke Mise per file.
FILTER_PYTHON="${FILTER_PYTHON:-$(mise which python)}"
"$FILTER_PYTHON" -c 'import tomllib'
quote() {
  "$FILTER_PYTHON" -c 'import shlex, sys; print(shlex.join(sys.argv[1:]))' "$@"
}
for kind in codex claude; do
  FILTER_COMMAND="$(quote "$FILTER_PYTHON" scripts/clean-agent-config.py "$kind")"
  git config --local "filter.agent-$kind.clean" "$FILTER_COMMAND"
  git config --local "filter.agent-$kind.smudge" cat
  git config --local "filter.agent-$kind.required" true
done
SCRIPT_COMMAND="$(quote "$FILTER_PYTHON" scripts/clean-agent-config.py)"
RESTORE_COMMAND="$SCRIPT_COMMAND restore"
# A git alias runs from the top level; return to the caller's directory for its pathspecs.
git config --local alias.agent-status \
  "!f() { $SCRIPT_COMMAND refresh && cd \"\${GIT_PREFIX:-.}\" && git status \"\$@\"; }; f"
git config --local alias.agent-restore "!$RESTORE_COMMAND"

# fix(config): put back private keys after Git rewrites the config files. Hook problems
# only warn, so quickstart still installs the filters, which guard privacy.
HOOK_MARKER="# agent-config-restore: written by scripts/install-git-filters.sh"
HOOKS_SCOPE="$(git config --show-scope --get core.hooksPath | cut -f1 || true)"
if [ -n "$HOOKS_SCOPE" ] && [ "$HOOKS_SCOPE" != local ] && [ "$HOOKS_SCOPE" != worktree ]; then
  # Never write repo-specific hooks into a directory that other repositories share.
  echo "warning: core.hooksPath is set in $HOOKS_SCOPE config, so no restore hooks were" \
    "installed; call 'git agent-restore' from its post-checkout, post-merge, and" \
    "post-rewrite hooks by hand." >&2
else
  HOOKS_DIR="$(git rev-parse --git-path hooks)"
  mkdir -p "$HOOKS_DIR"
  for hook in post-checkout post-merge post-rewrite; do
    hook_path="$HOOKS_DIR/$hook"
    if [ -e "$hook_path" ] && ! grep -qxF "$HOOK_MARKER" "$hook_path"; then
      echo "warning: kept existing $hook_path; call 'git agent-restore' from it by hand." >&2
      continue
    fi
    REBASE_GUARD=""
    if [ "$hook" = post-checkout ]; then
      # A rebase checks out commits one by one; post-rewrite restores once at the end.
      REBASE_GUARD='git_dir="$(git rev-parse --git-dir)"
if [ -d "$git_dir/rebase-merge" ] || [ -d "$git_dir/rebase-apply" ]; then exit 0; fi
'
    fi
    # Write whole, then rename, so a failure never leaves a partial hook without the marker.
    cat > "$hook_path.tmp" <<HOOK
#!/bin/sh
$HOOK_MARKER
cd "\$(git rev-parse --show-toplevel)" || exit 0
# An older checkout may predate restore; skip quietly rather than fail every checkout.
grep -q restore_main scripts/clean-agent-config.py 2>/dev/null || exit 0
${REBASE_GUARD}$RESTORE_COMMAND
# Restore reports its own problems; never fail the Git command that ran this hook.
exit 0
HOOK
    chmod +x "$hook_path.tmp"
    mv "$hook_path.tmp" "$hook_path"
  done
fi

# Seed the private backups now rather than waiting for the next edit.
for config_file in dotfiles/.codex/config.toml dotfiles/.claude/settings.json; do
  if [ -f "$config_file" ]; then
    git hash-object --path="$config_file" "$config_file" > /dev/null
  fi
done
