#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
# feat(config): resolve Mise's Python once so Git does not invoke Mise per file.
FILTER_PYTHON="$(mise which python)"
"$FILTER_PYTHON" -c 'import tomllib'
for kind in codex claude; do
  FILTER_COMMAND="$("$FILTER_PYTHON" -c 'import shlex, sys; print(shlex.join(sys.argv[1:]))' \
    "$FILTER_PYTHON" scripts/clean-agent-config.py "$kind")"
  git config --local "filter.agent-$kind.clean" "$FILTER_COMMAND"
  git config --local "filter.agent-$kind.smudge" cat
  git config --local "filter.agent-$kind.required" true
done
git config --local alias.agent-status '!bash scripts/agent-status.sh'
