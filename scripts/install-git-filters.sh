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
# fix(privacy): stop if kinds fails or prints nothing; a for list would ignore both.
SCRIPT=("$FILTER_PYTHON" scripts/clean-agent-config.py)
read -ra KINDS <<< "$("${SCRIPT[@]}" kinds)"
[ "${#KINDS[@]}" -gt 0 ]
# Git and sh re-parse these strings, so they are shell-quoted once here.
# fix(config): name the fix when Mise prunes this Python, instead of Git's "cannot run".
GUARD='python=$1; shift; [ -x "$python" ] || { echo "agent config: $python is missing;" \
  "rerun scripts/install-git-filters.sh" >&2; exit 1; }; exec "$python" scripts/clean-agent-config.py "$@"'
SCRIPT_COMMAND="$(quote sh -c "$GUARD" agent-config "$FILTER_PYTHON")"
for kind in "${KINDS[@]}"; do
  git config --local "filter.agent-$kind.clean" "$SCRIPT_COMMAND $kind"
  git config --local "filter.agent-$kind.smudge" cat
  git config --local "filter.agent-$kind.required" true
done

# fix(config): retire the restore hooks and aliases; the live configs now live outside Git.
# Remove only hooks that carry the marker the previous installer wrote.
HOOK_MARKER="# agent-config-restore: written by scripts/install-git-filters.sh"
HOOKS_DIR="$(git rev-parse --git-path hooks)"
for hook in post-checkout post-merge post-rewrite; do
  if [ -f "$HOOKS_DIR/$hook" ] && grep -qxF "$HOOK_MARKER" "$HOOKS_DIR/$hook"; then
    rm -f "$HOOKS_DIR/$hook"
  fi
done
for alias in agent-status agent-restore; do
  git config --local --unset "alias.$alias" || true
done
