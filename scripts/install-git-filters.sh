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
  # Git replaces %f with the path, so the filter backs up only the working file's text.
  FILTER_COMMAND="$SCRIPT_COMMAND $kind %f"
  git config --local "filter.agent-$kind.clean" "$FILTER_COMMAND"
  git config --local "filter.agent-$kind.smudge" cat
  git config --local "filter.agent-$kind.required" true
done
RESTORE_COMMAND="$SCRIPT_COMMAND restore"
HOOK_COMMAND="$RESTORE_COMMAND --if-wiped"
# Show status even if refresh reports a problem. A git alias runs from the top level;
# return to the caller's directory for its pathspecs.
git config --local alias.agent-status \
  "!f() { $SCRIPT_COMMAND refresh; cd \"\${GIT_PREFIX:-.}\" && git status \"\$@\"; }; f"
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
fi
realpath_of() { "$FILTER_PYTHON" -c 'import os, sys; print(os.path.realpath(sys.argv[1]))' "$1"; }
COMMON_DIR="$(realpath_of "$(git rev-parse --git-common-dir)")"
HOOKS_REAL="$(realpath_of "${HOOKS_DIR:-.}")"
if [ -n "${HOOKS_DIR:-}" ] && [[ "$HOOKS_REAL/" == "$(realpath_of .)/"* ]] \
  && [[ "$HOOKS_REAL/" != "$COMMON_DIR/"* ]]; then
  # fix(privacy): hooks embed this machine's Python path; never write them into the worktree,
  # where they could be committed.
  echo "warning: core.hooksPath points inside this worktree, so no restore hooks were" \
    "installed; call 'git agent-restore' from its post-checkout, post-merge, and" \
    "post-rewrite hooks by hand." >&2
elif [ -n "${HOOKS_DIR:-}" ]; then
  mkdir -p "$HOOKS_DIR" || echo "warning: could not create $HOOKS_DIR." >&2
  for hook in post-checkout post-merge post-rewrite; do
    hook_path="$HOOKS_DIR/$hook"
    if [ -e "$hook_path" ] && ! grep -qxF "$HOOK_MARKER" "$hook_path"; then
      echo "warning: kept existing $hook_path; call 'git agent-restore' from it by hand." >&2
      continue
    fi
    # fix(config): restore only files whose index copy changed from the commit Git left.
    case "$hook" in
      post-checkout)
        # During a rebase, a restore before the remaining picks would make them refuse to
        # touch the file; post-rewrite restores at the end instead. A rebase with nothing
        # left to pick (a fast-forward, or every commit already upstream) runs no
        # post-rewrite, so restore here. A file checkout ($3 = 0) names no commits.
        # The apply backend checks out onto before creating rebase-apply, so recognise it
        # by the rebase command that runs this hook, or by configuration.
        HOOK_BODY='git_dir="$(git rev-parse --git-dir)"
if [ -d "$git_dir/rebase-apply" ]; then exit 0; fi
case " $(ps -o command= -p "$PPID" 2>/dev/null) " in
  *"git rebase"*" --apply"*|*"git rebase"*" --whitespace"*|*"git rebase"*" -C"*) exit 0 ;;
  *"git rebase "*) [ "$(git config rebase.backend)" = apply ] && exit 0 ;;
esac
if grep -qv -e "^#" -e "^\$" "$git_dir/rebase-merge/git-rebase-todo" 2>/dev/null; then exit 0; fi
if [ "$3" = 1 ]; then set -- --changed "$1"; else set --; fi' ;;
      post-merge) HOOK_BODY='set -- --changed ORIG_HEAD' ;;
      # A rebase rewrites the file at its onto checkout and at each pick, so the final copy
      # may equal ORIG_HEAD's although the file was wiped; rely on the wiped check alone.
      post-rewrite) HOOK_BODY='[ "$1" = rebase ] || exit 0
set --' ;;
    esac
    # Write whole, then rename, so a failure never leaves a partial hook without the marker.
    if ! cat > "$hook_path.tmp" <<HOOK
#!/bin/sh
$HOOK_MARKER
cd "\$(git rev-parse --show-toplevel)" || exit 0
# An older checkout may predate restore; skip quietly rather than fail every checkout.
grep -qx 'HOOK_API = 1' scripts/clean-agent-config.py 2>/dev/null || exit 0
$HOOK_BODY
$HOOK_COMMAND "\$@"
# Restore reports its own problems; never fail the Git command that ran this hook.
exit 0
HOOK
    then
      echo "warning: could not write $hook_path; call 'git agent-restore' after rewrites." >&2
      rm -f "$hook_path.tmp"
      continue
    fi
    if ! { chmod +x "$hook_path.tmp" && mv "$hook_path.tmp" "$hook_path"; }; then
      echo "warning: could not install $hook_path; call 'git agent-restore' after rewrites." >&2
      rm -f "$hook_path.tmp"
    fi
  done
fi

# Seed the private backups now rather than waiting for the next edit.
if ! "${SCRIPT[@]}" seed; then
  echo "warning: could not back up the agent config files; check their syntax and the Git" \
    "directory's permissions, then rerun this installer." >&2
fi
