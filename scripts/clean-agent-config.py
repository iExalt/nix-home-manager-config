#!/usr/bin/env python3
"""Keep only reviewed, portable preferences in Git; never write the input file.

As a clean filter, also back up the raw file under the Git directory so that
`restore` can put back private keys that a checkout, pull, or stash removed.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import tomllib


# feat(config): unknown keys stay local until explicitly reviewed here.
CODEX = {
    key: None for key in (
        "approval_policy", "approvals_reviewer", "developer_instructions",
        "model", "model_reasoning_effort", "model_reasoning_summary",
        "sandbox_mode", "service_tier",
    )
}
CODEX.update({
    "desktop": {
        key: None for key in (
            "conversationDetailMode", "dock-icon-preference", "followUpQueueMode",
            "preventSleepWhileRunning", "show-context-window-usage",
        )
    },
    "features": {"goals": None, "memories": None},
    "memories": {"generate_memories": None, "use_memories": None},
    "plugins": {"*": {"enabled": None}},
    "tui": {"status_line": None, "status_line_use_colors": None},
})
CLAUDE = {
    key: None for key in (
        "model", "effortLevel", "tui", "skipDangerousModePermissionPrompt",
        "theme", "switchModelsOnFlag", "autoCompactWindow",
    )
}
CLAUDE.update({
    "attribution": {"commit": None, "pr": None},
    # fix(privacy): name each variable; env commonly holds secrets.
    "env": {"CLAUDE_CODE_SILENT_TURN_REMINDER_TEXT": None},
    "permissions": {"defaultMode": None},
    "statusLine": {"type": None, "command": None, "padding": None},
    "enabledPlugins": {"*": None},
    "pluginConfigs": {
        "cc-plugin-agents-md@builtin": {"options": {"instructionFiles": None}},
    },
    "sandbox": {"enabled": None},
    "modelSettings": {"*": {"effortLevel": None}},
    # feat(config): lists hold one item policy; an item is kept whole or not at all.
    "hooks": {"*": [{"matcher": None, "hooks": [{"type": None, "command": None, "timeout": None}]}]},
})
# Shared hook scripts live at this fixed path, which identifies nothing.
SHARED_HOOKS = '"$HOME/.config/agent-hooks/'


def portable(value):
    # fix(privacy): conservatively omit strings containing any path separator.
    if isinstance(value, str):
        value = value.replace(SHARED_HOOKS, '"')
        return not any(part in value for part in ("/", "\\", "$HOME", "${HOME}", "~"))
    if isinstance(value, list):
        return all(portable(item) for item in value)
    return isinstance(value, (bool, int, float)) or value is None


def project(data, policy):
    result = {}
    for key in sorted(data):
        if not portable(key) or (key not in policy and "*" not in policy):
            continue
        rule = policy.get(key, policy.get("*"))
        value = data[key]
        if isinstance(rule, dict):
            if isinstance(value, dict):
                selected = project(value, rule)
                if selected:
                    result[key] = selected
        elif isinstance(rule, list):
            if isinstance(value, list) and value:
                items = [project(item, rule[0]) if isinstance(item, dict) else {} for item in value]
                if all(items[i] == value[i] for i in range(len(value))):
                    result[key] = items
        elif portable(value):
            result[key] = value
    return result


def toml_value(value):
    if isinstance(value, dict):
        return "{" + ", ".join(f"{json.dumps(k)} = {toml_value(v)}" for k, v in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def toml_dump(data, prefix=()):
    lines = []
    if prefix:
        lines.append("[" + ".".join(json.dumps(key) for key in prefix) + "]")
    for key, value in data.items():
        if not isinstance(value, dict):
            lines.append(f"{json.dumps(key)} = {toml_value(value)}")
    for key, value in data.items():
        if isinstance(value, dict):
            lines.extend(["", toml_dump(value, (*prefix, key))])
    return "\n".join(lines)


FILES = {"codex": "dotfiles/.codex/config.toml", "claude": "dotfiles/.claude/settings.json"}
POLICY = {"codex": CODEX, "claude": CLAUDE}
KEEP_BACKUPS = 10


def parse(text, kind):
    if kind == "codex":
        return tomllib.loads(text)
    if kind == "claude":
        return json.loads(text)
    raise ValueError("expected codex or claude")


def dump(data, kind):
    if kind == "codex":
        return toml_dump(data) + "\n"
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def clean(text, kind):
    return dump(project(parse(text, kind), POLICY[kind]), kind)


def private(data, kept):
    """Return the parts of data that the projection dropped."""
    result = {}
    for key, value in data.items():
        if key not in kept:
            result[key] = value
        elif isinstance(value, dict) and isinstance(kept[key], dict):
            dropped = private(value, kept[key])
            if dropped:
                result[key] = dropped
    return result


def add_missing(live, extra, path=()):
    """Add keys from extra that live lacks; live values always win."""
    added = []
    for key, value in extra.items():
        if key not in live:
            live[key] = value
            added.append(".".join((*path, key)))
        elif isinstance(live[key], dict) and isinstance(value, dict):
            added += add_missing(live[key], value, (*path, key))
    return added


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout.strip()


def backup_dir():
    # feat(config): per-worktree Git directory, so other checkouts never touch this backup.
    return Path(git("rev-parse", "--absolute-git-dir")) / "agent-config-private"


def backups(kind):
    found = [item for item in backup_dir().glob(f"{kind}.*") if item.suffix[1:].isdigit()]
    return sorted(found, key=lambda item: int(item.suffix[1:]))


def write_private(target, text, mode=0o600):
    descriptor, temporary = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.")
    try:
        with os.fdopen(descriptor, "w") as handle:
            handle.write(text)
        os.chmod(temporary, mode)
        os.replace(temporary, target)
    except BaseException:
        os.unlink(temporary)
        raise


def back_up(text, kind, data, projected):
    # fix(config): a file that already equals its projection holds nothing to protect,
    # so a wiped file never replaces a good backup.
    if data == projected:
        return
    directory = backup_dir()
    directory.mkdir(mode=0o700, exist_ok=True)
    existing = backups(kind)
    if existing and existing[-1].read_text() == text:
        return
    write_private(directory / f"{kind}.{time.time_ns()}", text)
    # fix(config): rotate rather than overwrite, so a smaller private set stays recoverable.
    for old in backups(kind)[:-KEEP_BACKUPS]:
        old.unlink()


def filter_main(kind):
    text = sys.stdin.read()
    try:
        data = parse(text, kind)
        projected = project(data, POLICY[kind])
        output = dump(projected, kind)
    except Exception:
        # fix(privacy): do not echo configuration contents on parse failures.
        sys.exit("Agent config clean filter failed; check syntax and filter policy.")
    try:
        back_up(text, kind, data, projected)
    except Exception:
        print(f"warning: agent config backup failed for {kind}; restore will not cover recent edits.",
              file=sys.stderr)
    sys.stdout.write(output)


def restore_main(arguments):
    source = Path(arguments[arguments.index("--from") + 1]) if "--from" in arguments else None
    if source and not any(source.name.startswith(f"{kind}.") for kind in FILES):
        print("agent-restore: --from expects a backup named codex.<n> or claude.<n>.", file=sys.stderr)
        return 1
    root = Path(git("rev-parse", "--show-toplevel"))
    failed = False
    for kind, relative in FILES.items():
        if source and not source.name.startswith(f"{kind}."):
            continue
        saved = source or (backups(kind) or [None])[-1]
        target = root / relative
        if saved is None or not target.exists():
            continue
        try:
            live = parse(target.read_text(), kind)
            backup = parse(saved.read_text(), kind)
            added = add_missing(live, private(backup, project(backup, POLICY[kind])))
            if added:
                write_private(target, dump(live, kind), target.stat().st_mode & 0o777)
        except Exception:
            # fix(privacy): name the file, never its contents.
            print(f"agent-restore: skipped {relative}; it or its backup could not be parsed or written.",
                  file=sys.stderr)
            failed = True
            continue
        if added:
            print(f"agent-restore: restored {', '.join(added)} in {relative}", file=sys.stderr)
            # fix(config): like agent-status, refresh stat data only when the filtered
            # content still matches the index, so Git does not report a phantom change.
            indexed = subprocess.run(["git", "rev-parse", "--verify", "-q", f":{relative}"],
                                     cwd=root, capture_output=True, text=True).stdout.strip()
            if indexed and indexed == git("-C", str(root), "hash-object", f"--path={relative}", relative):
                git("-C", str(root), "add", "--renormalize", "--", relative)
    return 1 if failed else 0


if __name__ == "__main__":
    if sys.argv[1:2] == ["restore"]:
        sys.exit(restore_main(sys.argv[2:]))
    filter_main(sys.argv[1] if len(sys.argv) > 1 else "")
