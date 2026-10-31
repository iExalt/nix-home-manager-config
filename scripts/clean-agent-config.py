#!/usr/bin/env python3
"""Keep only reviewed, portable preferences in Git; never write the input file.

As a clean filter, also back up the raw file under the Git directory so that
`restore` can put back private keys that a checkout, pull, or stash removed.
"""

import argparse
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
    # feat(config): lists hold one item policy; each item is kept whole or dropped whole.
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
                # fix(config): keep the portable items, so a private item beside them
                # neither hides them from Git nor makes them look deleted after a restore.
                kept = [item for item in value
                        if isinstance(item, dict) and project(item, rule[0]) == item]
                if kept:
                    result[key] = kept
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
# Older backups that alone hold a private section survive rotation this long.
KEEP_UNIQUE_SECONDS = 30 * 24 * 60 * 60


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


def private_part(data, kind):
    return private(data, project(data, POLICY[kind]))


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
        elif isinstance(value, list) and isinstance(kept[key], list):
            dropped = [item for item in value if item not in kept[key]]
            if dropped:
                result[key] = dropped
    return result


def add_missing(live, extra, policy, path=()):
    """Add keys from extra that live lacks; live values always win."""
    added = []
    for key, value in extra.items():
        name = ".".join((*path, key))
        rule = policy.get(key, policy.get("*")) if isinstance(policy, dict) else None
        if key not in live:
            live[key] = value
            added.append(name)
        elif isinstance(live[key], dict) and isinstance(value, dict):
            added += add_missing(live[key], value, rule or {}, (*path, key))
        # fix(config): only lists with an item policy are tracked per item; appending to
        # any other list would make Git's whole copy of it look deleted.
        elif isinstance(rule, list) and isinstance(live[key], list) and isinstance(value, list):
            # Private items were never in Git; append the ones a pulled list lacks.
            missing = [item for item in value if item not in live[key]]
            if missing:
                live[key] = live[key] + missing
                added.append(name)
    return added


def absent(extra, live, path=()):
    """Name the sections of extra that live lacks."""
    names = []
    for key, value in extra.items():
        if key not in live:
            names.append(".".join((*path, key)))
        elif isinstance(value, dict) and isinstance(live[key], dict):
            names += absent(value, live[key], (*path, key))
    return names


def git(*args, cwd=None):
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True,
                          cwd=cwd).stdout.strip()


def backup_dir():
    # feat(config): per-worktree Git directory, so other checkouts never touch this backup.
    return Path(git("rev-parse", "--absolute-git-dir")) / "agent-config-private"


def backups(directory, kind):
    found = [item for item in directory.glob(f"{kind}.*") if item.suffix[1:].isdigit()]
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


def paths(data, prefix=()):
    """Name the sections of a nested dict, two levels deep, as restore reports them."""
    names = set()
    for key, value in data.items():
        if isinstance(value, dict) and value and len(prefix) < 1:
            names |= paths(value, (*prefix, key))
        else:
            names.add(".".join((*prefix, key)))
    return names


def rotate(directory, kind, now):
    # fix(config): keep the newest backups, plus older ones that alone still hold a private
    # section, so a run of small private sets after a wipe cannot evict the complete one.
    seen = set()
    for index, saved in enumerate(reversed(backups(directory, kind))):
        try:
            names = paths(private_part(parse(saved.read_text(), kind), kind))
        except ValueError:
            names = set()
        young = now - int(saved.suffix[1:]) < KEEP_UNIQUE_SECONDS * 10**9
        if index < KEEP_BACKUPS or (young and names - seen):
            seen |= names
        else:
            saved.unlink()


def back_up(text, kind, data, projected, directory=None):
    # fix(config): a file that already equals its projection holds nothing to protect,
    # so a wiped file never replaces a good backup.
    if data == projected:
        return
    directory = directory or backup_dir()
    directory.mkdir(mode=0o700, exist_ok=True)
    existing = backups(directory, kind)
    if existing and existing[-1].read_text() == text:
        return
    now = time.time_ns()
    write_private(directory / f"{kind}.{now}", text)
    rotate(directory, kind, now)


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


def refresh(root, relatives):
    # fix(config): refresh stat data only when the filtered content matches the index,
    # so Git stops reporting a byte-size change without staging a real one.
    for relative in relatives:
        if not (root / relative).is_file():
            continue
        indexed = subprocess.run(["git", "rev-parse", "--verify", "-q", f":{relative}"],
                                 cwd=root, capture_output=True, text=True).stdout.strip()
        if indexed and indexed == git("hash-object", f"--path={relative}", relative, cwd=root):
            git("add", "--renormalize", "--", relative, cwd=root)


def restore_file(target, saved, kind, if_wiped=False):
    """Merge private keys from saved into target; return the names added and the result.

    With if_wiped, leave a file alone unless it holds no private content, the state Git
    leaves after rewriting it; return None then.
    """
    extra = private_part(parse(saved.read_text(), kind), kind)
    for _ in range(3):
        before = target.stat()
        try:
            live = parse(target.read_text(), kind)
        except ValueError:  # tomllib and json errors; conflict markers, for example
            if if_wiped:  # Git never leaves an unparsable file, so it was not wiped.
                return None
            raise
        # fix(config): hooks also run when Git left the file alone; restoring then would
        # bring back a private key deleted since the latest backup.
        if if_wiped and live != project(live, POLICY[kind]):
            return None
        added = add_missing(live, extra, POLICY[kind])
        if not added:
            return [], live
        output = dump(live, kind)
        # fix(config): an agent may save the file meanwhile; start over rather than drop its write.
        now = target.stat()
        if (now.st_mtime_ns, now.st_size) == (before.st_mtime_ns, before.st_size):
            write_private(target, output, before.st_mode & 0o777)
            return added, live
    raise OSError("file kept changing")


def unrestored(older, live, kind):
    """Pair each older backup, newest first, with private sections live still lacks."""
    reported, result = set(), []
    for saved in reversed(older):
        names = [name for name in absent(private_part(parse(saved.read_text(), kind), kind), live)
                 if name not in reported]
        if names:
            reported.update(names)
            result.append((saved, names))
    return result


def restore_main(arguments, refresh_restored=True):
    parser = argparse.ArgumentParser(prog="git agent-restore")
    parser.add_argument("--from", dest="source", type=Path,
                        help="a backup file such as codex.<n> or claude.<n>")
    parser.add_argument("--if-wiped", action="store_true",
                        help="only restore files that hold no private content (used by hooks)")
    parser.add_argument("--forget", choices=FILES,
                        help="delete this file's backups, keeping only its current content")
    options = parser.parse_args(arguments)
    if options.forget:
        return forget(options.forget)
    source = options.source
    if source:
        # A git alias runs from the top level; resolve paths as typed by the user.
        source = Path(os.environ.get("GIT_PREFIX", "")) / source
        if not any(source.name.startswith(f"{kind}.") for kind in FILES) or not source.is_file():
            parser.error("--from expects an existing backup named codex.<n> or claude.<n>")
    root = Path(git("rev-parse", "--show-toplevel"))
    directory = backup_dir()
    failed = False
    for kind, relative in FILES.items():
        if source and not source.name.startswith(f"{kind}."):
            continue
        saved = backups(directory, kind)
        target = root / relative
        if not (source or saved) or not target.exists():
            continue
        try:
            result = restore_file(target, source or saved[-1], kind, options.if_wiped)
        except Exception:
            # fix(privacy): name the file, never its contents.
            print(f"agent-restore: skipped {relative}; it or its backup could not be parsed or written.",
                  file=sys.stderr)
            failed = True
            continue
        if result is None:
            continue
        added, live = result
        if added:
            print(f"agent-restore: restored {', '.join(added)} in {relative}; if you removed them on "
                  f"purpose, run: git agent-restore --forget {kind}", file=sys.stderr)
            try:
                if refresh_restored:
                    refresh(root, [relative])
            except subprocess.CalledProcessError:
                print(f"agent-restore: could not refresh {relative}; run git agent-status.",
                      file=sys.stderr)
                failed = True
        if source:
            continue
        try:
            # fix(config): a wipe followed by new private keys yields small latest backups;
            # name what older backups still hold instead of losing it silently.
            lost = unrestored(saved[:-1], live, kind)
        except Exception:
            print(f"agent-restore: could not check older backups of {relative}.", file=sys.stderr)
            failed = True
            continue
        for older, names in lost:
            print(f"agent-restore: {older} also has {', '.join(names)}; if you did not delete them "
                  f"on purpose, run: git agent-restore --from {older}", file=sys.stderr)
    return 1 if failed else 0


def forget(kind):
    """Purge a file's backups, so a deliberately removed private key (or secret) stays gone."""
    # fix(privacy): a removed secret may be revoked or rotated; keep no copies of it.
    root = Path(git("rev-parse", "--show-toplevel"))
    directory = backup_dir()
    old = backups(directory, kind)
    target = root / FILES[kind]
    if target.is_file():  # Save the new backup first, so a failed write keeps the old ones.
        directory.mkdir(mode=0o700, exist_ok=True)
        write_private(directory / f"{kind}.{time.time_ns()}", target.read_text())
    for saved in old:
        saved.unlink()
    print(f"agent-restore: kept only the current {FILES[kind]} as its backup.", file=sys.stderr)
    return 0


def seed():
    """Run the clean filter once per file, so its backup exists before any rewrite."""
    root = Path(git("rev-parse", "--show-toplevel"))
    failed = False
    for relative in FILES.values():
        if (root / relative).is_file():
            try:
                git("hash-object", f"--path={relative}", relative, cwd=root)
            except subprocess.CalledProcessError:
                print(f"agent-seed: could not back up {relative}.", file=sys.stderr)
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "restore":
        sys.exit(restore_main(sys.argv[2:]))
    if command == "refresh":
        # fix(config): also a catch-all for rewrites that fire no hook, such as cherry-pick.
        exit_code = restore_main(["--if-wiped"], refresh_restored=False)
        try:
            refresh(Path(git("rev-parse", "--show-toplevel")), FILES.values())
        except subprocess.CalledProcessError:
            print("agent-status: could not refresh the agent config files.", file=sys.stderr)
            exit_code = 1
        sys.exit(exit_code)
    if command == "seed":
        sys.exit(seed())
    if command == "kinds":
        print(" ".join(FILES))
        sys.exit(0)
    filter_main(command)
