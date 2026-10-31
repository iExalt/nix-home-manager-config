#!/usr/bin/env python3
"""Share reviewed, portable agent preferences through Git; keep everything else local.

The live configs (~/.claude/settings.json, ~/.codex/config.toml) are untracked files. `sync`
merges their portable keys three ways with the tracked copies under dotfiles/, using the
copy from the last sync as the base. As a Git clean filter, the script also keeps anything
private out of the tracked copies.
"""

import argparse
import copy
import datetime
import json
import math
import os
from pathlib import Path
import sys
import tempfile
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


def project(data, policy, kept_local=None, path=()):
    """Select the allowlisted, portable parts of data; name reviewed keys kept local."""
    result = {}
    for key in sorted(data):
        if not portable(key) or (key not in policy and "*" not in policy):
            continue
        rule = policy.get(key, policy.get("*"))
        value = data[key]
        if isinstance(rule, dict):
            if isinstance(value, dict):
                selected = project(value, rule, kept_local, (*path, key))
                if selected:
                    result[key] = selected
        elif isinstance(rule, list):
            if isinstance(value, list) and value:
                # fix(config): keep the portable items, so a private item beside them
                # neither hides them from Git nor makes them look deleted to sync.
                # Keep the projected copy, whose keys are sorted, so Git's copy stays canonical.
                kept = [projected for item in value if isinstance(item, dict)
                        and (projected := project(item, rule[0])) == item]
                if kept:
                    result[key] = kept
        elif portable(value):
            result[key] = value
        elif kept_local is not None and key in policy:
            # Wildcard entries are expected to hold private names; a reviewed key is not.
            textual = isinstance(value, str) or (
                isinstance(value, list) and all(isinstance(item, str) for item in value))
            reason = ("its value contains a path-like character (/, \\, ~, or $HOME)" if textual
                      else "its value is not a reviewed type")
            kept_local.append(((*path, key), reason))
    return result


def toml_string(text):
    # fix(config): JSON escapes are TOML escapes, except that TOML needs DEL escaped and
    # rejects the surrogate pairs json.dumps writes for non-BMP characters by default.
    return json.dumps(text, ensure_ascii=False).replace("\x7f", "\\u007f")


def toml_value(value):
    if isinstance(value, dict):
        return "{" + ", ".join(f"{toml_string(k)} = {toml_value(v)}" for k, v in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    # fix(config): sync rewrites private values too, which may use TOML-only types.
    if isinstance(value, (datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return "nan" if math.isnan(value) else ("inf" if value > 0 else "-inf")
    if isinstance(value, str):
        return toml_string(value)
    return json.dumps(value, allow_nan=False)


def toml_dump(data, prefix=()):
    lines = []
    if prefix:
        lines.append("[" + ".".join(toml_string(key) for key in prefix) + "]")
    for key, value in data.items():
        if not isinstance(value, dict):
            lines.append(f"{toml_string(key)} = {toml_value(value)}")
    for key, value in data.items():
        if isinstance(value, dict):
            lines.extend(["", toml_dump(value, (*prefix, key))])
    return "\n".join(lines)



FILES = {"codex": "dotfiles/.codex/config.toml", "claude": "dotfiles/.claude/settings.json"}
LIVE = {"codex": ".codex/config.toml", "claude": ".claude/settings.json"}
POLICY = {"codex": CODEX, "claude": CLAUDE}
MISSING = object()


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


def warn_kept_local(kept_local):
    for path, reason in kept_local:
        # feat(config): a reviewed preference that silently stops syncing is easy to miss.
        print(f"warning: kept {'.'.join(path)} local; {reason}.", file=sys.stderr)


def clean(text, kind, kept_local=None):
    return dump(project(parse(text, kind), POLICY[kind], kept_local), kind)


def holds_values(value):
    """Whether a section holds anything: a named entry counts even when its table is empty."""
    if isinstance(value, dict):
        return any(isinstance(item, dict) or holds_values(item) for item in value.values())
    return value != []


def private(data, kept):
    """Return the parts of data that the projection dropped."""
    result = {}
    for key, value in data.items():
        if key not in kept:
            if holds_values(value):  # Empty sections, however nested, hold nothing to protect.
                result[key] = value
        elif isinstance(value, dict) and isinstance(kept[key], dict):
            dropped = private(value, kept[key])
            if dropped:
                result[key] = dropped
        elif isinstance(value, list) and isinstance(kept[key], list):
            if any(item not in kept[key] for item in value):
                result[key] = value
    return result


def holds_private(data, kind):
    return bool(private(data, project(data, POLICY[kind])))


def portable_item(item, rule):
    """Whether an item of a per-item tracked list survives projection unchanged."""
    return isinstance(item, dict) and project(item, rule[0]) == item


def rule_at(policy, path):
    rule = policy
    for key in path:
        if not isinstance(rule, dict) or (key not in rule and "*" not in rule):
            return MISSING
        rule = rule.get(key, rule.get("*"))
    return rule


def leaves(data, policy, prefix=()):
    """Map each tracked leaf path of projected data to its value; lists are leaves."""
    result = {}
    for key, value in data.items():
        path = (*prefix, key)
        if isinstance(value, dict) and isinstance(rule_at(policy, path), dict):
            result.update(leaves(value, policy, path))
        else:
            result[path] = value
    return result


def get_path(data, path):
    for key in path:
        if not isinstance(data, dict) or key not in data:
            return MISSING
        data = data[key]
    return data


def set_path(data, path, value):
    for key in path[:-1]:
        if not isinstance(data.get(key), dict):
            data[key] = {}
        data = data[key]
    data[path[-1]] = value


def delete_path(data, path):
    parents = [data]
    for key in path[:-1]:
        parents.append(parents[-1][key])
    del parents[-1][path[-1]]
    # Drop only the tables this deletion emptied, innermost first.
    for depth in range(len(path) - 1, 0, -1):
        if parents[depth]:
            break
        del parents[depth - 1][path[depth - 1]]


def build(values):
    result = {}
    for path, value in values.items():
        set_path(result, path, value)
    return result


def apply(live, path, value, rule):
    """Set a tracked leaf in live data, keeping private items of a per-item list."""
    if isinstance(rule, list):
        current = get_path(live, path)
        kept = [item for item in (current if isinstance(current, list) else [])
                if not portable_item(item, rule)]
        value = (value if value is not MISSING else []) + kept
        value = value or MISSING
    if value is MISSING:
        if get_path(live, path) is not MISSING:
            delete_path(live, path)
    else:
        set_path(live, path, value)


def merge(live, shared, base, policy):
    """Merge the portable keys of live with shared, the projected repo copy, from base.

    A key changed on one side takes that side's value; a key changed on both keeps the
    live value. Without a base, nothing is deleted. Return the new live and shared data and
    the paths applied to live, exported to shared, in conflict, and kept local because
    live holds a value Git cannot share.
    """
    mine = leaves(project(live, policy), policy)
    theirs = leaves(shared, policy)
    common = leaves(base, policy)
    merged_live = copy.deepcopy(live)
    result = {}
    report = {"applied": [], "exported": [], "conflicts": [], "kept": []}
    for path in sorted(set(mine) | set(theirs) | set(common)):
        local, repo, old = (side.get(path, MISSING) for side in (mine, theirs, common))
        rule = rule_at(policy, path)
        if local is MISSING and not isinstance(rule, list) and get_path(live, path) is not MISSING:
            # fix(config): live holds a value Git cannot share; leave both sides alone.
            report["kept"].append(path)
            if repo is not MISSING:
                result[path] = repo
            continue
        if local == repo or local == old:
            value = repo
        else:
            value = local
            if repo != old:
                report["conflicts"].append(path)
        if value is not MISSING:
            result[path] = value
        if value != local:
            apply(merged_live, path, value, rule)
            report["applied"].append(path)
        if value != repo:
            report["exported"].append(path)
    merged_shared = project(build(result), policy)
    shared_paths = {path: value for path, value in result.items() if path not in report["kept"]}
    if leaves(project(merged_live, policy), policy) != shared_paths:
        raise RuntimeError("merge produced live and repo copies that disagree")
    return merged_live, merged_shared, report


def deep_merge(target, extra):
    for key, value in extra.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            deep_merge(target[key], value)
        else:
            target[key] = copy.deepcopy(value)


def write_atomic(target, text, mode):
    descriptor, temporary = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.",
                                             suffix=".agent-restore-tmp")
    try:
        with os.fdopen(descriptor, "w") as handle:
            handle.write(text)
        os.chmod(temporary, mode)
        os.replace(temporary, target)
    except BaseException:
        os.unlink(temporary)
        raise


def read_or_none(target):
    try:
        return target.read_text()
    except FileNotFoundError:
        return None


def newest_backup(repo, kind):
    """The newest raw copy the retired backup hooks saved, which may hold private keys."""
    directory = repo / ".git" / "agent-config-private"
    found = [item for item in directory.glob(f"{kind}.*") if item.suffix[1:].isdigit()]
    return max(found, key=lambda item: int(item.suffix[1:]), default=None)


def names(paths):
    return ", ".join(".".join(path) for path in paths)


class SyncError(Exception):
    pass


def load(path, kind):
    try:
        return parse(path.read_text(), kind)
    except ValueError:
        # fix(privacy): name the file without echoing its contents.
        raise SyncError(f"could not parse {path}") from None


def seed(kind, repo, live_path, shared_text, use_backup):
    """Return text to create a missing live file from, its base, and whether it is shared's.

    A retired Home Manager symlink points at the repo copy, which then still holds this
    machine's private keys. If a pull already wiped them there before this machine first
    synced, the retired backup hooks saved them.
    """
    if live_path.is_symlink():
        target = live_path.resolve()
        if target.is_file() and target != (repo / FILES[kind]).resolve():
            return target.read_text(), {}, False
    if use_backup and not holds_private(parse(shared_text, kind), kind):
        backup = newest_backup(repo, kind)
        if backup is not None:
            text = backup.read_text()
            # fix(config): base on the backup, so pulled portable changes still arrive.
            return text, project(load(backup, kind), POLICY[kind]), False
    return shared_text, {}, True


def sync_kind(kind, repo, home, state, overlay=None):
    policy = POLICY[kind]
    live_path = home / LIVE[kind]
    shared_path = repo / FILES[kind]
    base_path = state / f"{kind}.base"
    shared_text = shared_path.read_text()
    shared_raw = load(shared_path, kind)
    shared = project(shared_raw, policy)
    base_text = read_or_none(base_path)
    base = load(base_path, kind) if base_text is not None else {}
    seeded, from_shared = None, False
    if live_path.is_symlink() or not live_path.exists():
        seeded, seed_base, from_shared = seed(kind, repo, live_path, shared_text,
                                              use_backup=base_text is None)
        if base_text is None:
            base = seed_base
    if holds_private(shared_raw, kind) and not from_shared:
        # fix(privacy): never cut the only copy of private keys down to its projection.
        raise SyncError(f"{shared_path} still holds private keys that {live_path} lacks; "
                        f"copy them into {live_path}, then rerun sync")
    overlay_data = load(overlay, kind) if overlay else {}
    if project(overlay_data, policy):
        raise SyncError(f"the {kind} overlay sets shared keys; overlays may set private keys only")
    for _ in range(2):
        before = seeded if seeded is not None else live_path.read_text()
        try:
            live = parse(before, kind)
        except ValueError:
            raise SyncError(f"could not parse {live_path}") from None
        kept_local = []
        project(live, policy, kept_local)
        merged_live, merged_shared, report = merge(live, shared, base, policy)
        shareable = project(merged_live, policy)
        deep_merge(merged_live, overlay_data)
        if project(merged_live, policy) != shareable:
            raise SyncError(f"the {kind} overlay replaces a shared table")
        if seeded is None and merged_live == live:
            break
        # fix(config): an app may save while this runs; merge again rather than drop its edit.
        if seeded is None and live_path.read_text() != before:
            continue
        mode = 0o600 if seeded is not None else live_path.stat().st_mode & 0o777
        live_path.parent.mkdir(parents=True, exist_ok=True)
        write_atomic(live_path, dump(merged_live, kind), mode)
        break
    else:
        raise SyncError(f"{live_path} kept changing; rerun sync")
    warn_kept_local(kept_local)
    if seeded is not None:
        print(f"agent-config: created {live_path}.")
    if report["applied"]:
        print(f"agent-config: applied repo changes to {live_path}: {names(report['applied'])}.")
    for path in report["conflicts"]:
        print(f"warning: kept the local {'.'.join(path)}; the repo changed it too.",
              file=sys.stderr)
    shared_out = dump(merged_shared, kind)
    if shared_out != shared_text:
        write_atomic(shared_path, shared_out, shared_path.stat().st_mode & 0o777)
        if report["exported"]:
            print(f"agent-config: copied local changes to {FILES[kind]}; commit or revert "
                  f"them: {names(report['exported'])}.")
    if base_text != shared_out:
        state.mkdir(parents=True, exist_ok=True, mode=0o700)
        write_atomic(base_path, shared_out, 0o600)


def sync_main(arguments):
    parser = argparse.ArgumentParser(prog="clean-agent-config.py sync")
    parser.add_argument("kinds", nargs="*", metavar="KIND", help=" or ".join(FILES))
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--home", type=Path, default=Path.home())
    state_home = os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state"
    parser.add_argument("--state", type=Path, default=Path(state_home) / "agent-config")
    parser.add_argument("--overlay", action="append", default=[], metavar="KIND=FILE")
    options = parser.parse_args(arguments)
    overlays = dict(item.split("=", 1) for item in options.overlay)
    unknown = sorted(set(options.kinds) - set(FILES))
    if unknown:
        parser.error(f"unknown kind {', '.join(unknown)}; expected {' or '.join(FILES)}")
    if (options.repo / ".git").is_file():
        # fix(config): every checkout shares one base; a linked worktree's copy may be stale.
        print("agent-config: run sync from the main checkout, not a linked worktree.",
              file=sys.stderr)
        return 1
    exit_code = 0
    for kind in options.kinds or list(FILES):
        overlay = overlays.get(kind)
        try:
            sync_kind(kind, options.repo, options.home, options.state,
                      Path(overlay) if overlay else None)
        except (SyncError, RuntimeError, OSError) as error:
            print(f"agent-config: skipped {kind}: {error}", file=sys.stderr)
            exit_code = 1
    return exit_code


def filter_main(kind):
    try:
        kept_local = []
        output = clean(sys.stdin.read(), kind, kept_local)
    except Exception:
        # fix(privacy): do not echo configuration contents on parse failures.
        sys.exit("Agent config clean filter failed; check syntax and filter policy.")
    warn_kept_local(kept_local)
    sys.stdout.write(output)


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "sync":
        sys.exit(sync_main(sys.argv[2:]))
    if command == "kinds":
        print(" ".join(FILES))
        sys.exit(0)
    # Git runs `<kind> <path>`; the path is accepted for older filter configurations.
    filter_main(command)
