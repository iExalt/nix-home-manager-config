#!/usr/bin/env python3
"""Keep only reviewed, portable preferences in Git; never write the input file.

As a clean filter, also back up the raw file under the Git directory so that
`restore` can put back private keys that a checkout, pull, or stash removed.
"""

import argparse
import copy
import datetime
import json
import math
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
                # neither hides them from Git nor makes them look deleted after a restore.
                # Keep the projected copy, whose keys are sorted, so Git's copy stays canonical.
                kept = [project(item, rule[0]) for item in value if portable_item(item, rule)]
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
            kept_local.append(f"{'.'.join((*path, key))} local; {reason}")
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
    # fix(config): restore rewrites private values too, which may use TOML-only types.
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
POLICY = {"codex": CODEX, "claude": CLAUDE}
KEEP_BACKUPS = 10
# Installed hooks probe for this exact line before passing restore their arguments.
HOOK_API = 1
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
            # Keep the whole list, so a restore can put private items back in their place.
            if any(item not in kept[key] for item in value):
                result[key] = value
    return result


def portable_item(item, rule):
    """Whether an item of a per-item tracked list survives projection unchanged."""
    return isinstance(item, dict) and project(item, rule[0]) == item


def restorable(value, rule):
    """Drop the portable items of per-item tracked lists from a backed-up section."""
    if isinstance(value, dict) and isinstance(rule, dict):
        result = {}
        for key, item in value.items():
            kept = restorable(item, rule.get(key, rule.get("*")))
            if kept != {} and kept != []:
                result[key] = kept
        return result
    if isinstance(value, list) and isinstance(rule, list):
        return [item for item in value if not portable_item(item, rule)]
    return value


def add_missing(live, extra, policy, path=()):
    """Add keys from extra that live lacks; live values always win."""
    added = []
    for key, value in extra.items():
        name = ".".join((*path, key))
        rule = policy.get(key, policy.get("*")) if isinstance(policy, dict) else None
        if key not in live:
            # fix(config): private() keeps whole lists for ordering; never bring back the
            # portable items Git deleted along with the list or its section.
            value = restorable(value, rule)
            if value != {} and value != []:
                live[key] = value
                added.append(name)
        elif isinstance(live[key], dict) and isinstance(value, dict):
            added += add_missing(live[key], value, rule or {}, (*path, key))
        # fix(config): only lists with an item policy are tracked per item; appending to
        # any other list would make Git's whole copy of it look deleted.
        elif isinstance(rule, list) and isinstance(live[key], list) and isinstance(value, list):
            # Private items were never in Git; restore the ones a pulled list lacks, each after
            # its nearest preceding neighbour from the backup, so hook order survives.
            # fix(config): Git never holds private items, so a list that still has one was not
            # wiped; it wins whole, and an edited private item is not duplicated.
            if not all(portable_item(item, rule) for item in live[key]):
                continue
            merged = list(live[key])
            for index, item in enumerate(value):
                if item in merged or portable_item(item, rule):
                    continue
                anchors = [merged.index(other) + 1 for other in value[:index] if other in merged]
                merged.insert(max(anchors, default=0), item)
            if merged != live[key]:
                live[key] = merged
                added.append(name)
    return added


def git(*args, cwd=None, check=True, text=True):
    """Run git; return its output, or None on failure when check is false."""
    result = subprocess.run(["git", *args], check=check, capture_output=True, text=text, cwd=cwd)
    if result.returncode:
        return None
    return result.stdout.strip() if text else result.stdout


def backup_dir_at(root):
    # feat(config): per-worktree Git directory, so other checkouts never touch this backup.
    return Path(git("rev-parse", "--absolute-git-dir", cwd=root)) / "agent-config-private"


def backup_dir():
    return backup_dir_at(None)


def backups(directory, kind):
    found = [item for item in directory.glob(f"{kind}.*") if item.suffix[1:].isdigit()]
    return sorted(found, key=lambda item: int(item.suffix[1:]))


def write_private(target, text, mode=0o600):
    # fix(privacy): .gitignore covers this suffix, so a temp copy left by a killed process
    # beside a tracked config is never staged unfiltered.
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


def paths(data, prefix=()):
    """Name every leaf of a nested dict, and every item of its lists."""
    names = set()
    for key, value in data.items():
        name = ".".join((*prefix, key))
        if isinstance(value, dict) and value:
            names |= paths(value, (*prefix, key))
        elif isinstance(value, list) and value:
            names |= {f"{name}[{json.dumps(item, sort_keys=True, default=str)}]" for item in value}
        else:
            names.add(name)
    return names


def read_or_none(path):
    try:
        return path.read_text()
    except FileNotFoundError:  # Another Git process rotated it away meanwhile.
        return None


def rotate(directory, kind, now):
    # fix(config): keep the newest backups, plus older ones that alone still hold a private
    # value or list item, so small private sets after a wipe cannot evict the complete one.
    seen = set()
    for index, saved in enumerate(reversed(backups(directory, kind))):
        try:
            data = parse(saved.read_text(), kind)
            # private() keeps whole lists for ordering; drop their portable items here.
            names = paths(private_part(data, kind)) - paths(project(data, POLICY[kind]))
        except (ValueError, FileNotFoundError):  # Unparsable, or rotated by another run.
            names = set()
        young = now - int(saved.suffix[1:]) < KEEP_UNIQUE_SECONDS * 10**9
        if index < KEEP_BACKUPS or (young and names - seen):
            seen |= names
        else:
            saved.unlink(missing_ok=True)


def back_up(text, kind, data, projected, directory=None):
    # fix(config): a file without private content holds nothing to protect, so a wiped
    # file never replaces a good backup. holds_private() uses the same test.
    if not private(data, projected):
        return
    directory = directory or backup_dir()
    directory.mkdir(mode=0o700, exist_ok=True)
    existing = backups(directory, kind)
    if existing and read_or_none(existing[-1]) == text:
        return
    now = time.time_ns()
    # fix(config): stay ordered even if the clock steps back.
    stamp = max(now, int(existing[-1].suffix[1:]) + 1) if existing else now
    write_private(directory / f"{kind}.{stamp}", text)
    rotate(directory, kind, now)


def clean_text(text, kind, directory=None):
    """Do what the clean filter does: back up the raw text and return Git's copy.

    Parse errors propagate; backup failures and reviewed keys kept local only warn.
    """
    data = parse(text, kind)
    kept_local = []
    projected = project(data, POLICY[kind], kept_local)
    output = dump(projected, kind)
    try:
        back_up(text, kind, data, projected, directory)
    except Exception:
        print(f"warning: agent config backup failed for {kind}; restore will not cover recent edits.",
              file=sys.stderr)
    for note in kept_local:
        # feat(config): a reviewed preference that silently stops syncing is easy to miss.
        print(f"warning: kept {note}.", file=sys.stderr)
    return output


def filter_main(kind):
    try:
        output = clean_text(sys.stdin.read(), kind)
    except Exception:
        # fix(privacy): do not echo configuration contents on parse failures.
        sys.exit("Agent config clean filter failed; check syntax and filter policy.")
    sys.stdout.write(output)


def refresh(root, relatives):
    """Refresh stat data per file; return the files that could not be refreshed."""
    # fix(config): refresh stat data only when the filtered content matches the index,
    # so Git stops reporting a byte-size change without staging a real one.
    failed = []
    for relative in relatives:
        if not (root / relative).is_file():
            continue
        kind = next(name for name, path in FILES.items() if path == relative)
        try:
            indexed = git("rev-parse", "-q", "--verify", f":{relative}", cwd=root, check=False)
            if not indexed:  # Unmerged or untracked: nothing to refresh, and no error.
                continue
            # fix(perf): clean in-process, as the filter would, rather than start it once more.
            # No eol or ident attribute applies to these paths, so Git's copy is exactly this.
            output = clean_text((root / relative).read_text(), kind, backup_dir_at(root))
            cleaned = subprocess.run(["git", "hash-object", "--no-filters", "--stdin"], cwd=root,
                                     input=output, capture_output=True, text=True, check=True)
            if indexed == cleaned.stdout.strip():
                git("add", "--renormalize", "--", relative, cwd=root)
        except (subprocess.CalledProcessError, ValueError, OSError):  # Skip only this file.
            failed.append(relative)
    return failed


def restore_file(target, saved, kind, indexed_bytes=None):
    """Merge private keys from saved into target; return the names added and the result.

    With indexed_bytes (a callable returning the index copy, used by hooks), leave a file
    alone unless Git wrote it: it holds no private content, or it equals the index copy.
    Return None then.
    """
    extra = private_part(parse(saved.read_text(), kind), kind)
    for _ in range(3):
        before = target.stat()
        raw = target.read_bytes()
        try:
            live = parse(raw.decode(), kind)
        except ValueError:  # tomllib and json errors; conflict markers, for example
            if indexed_bytes:  # Git never leaves an unparsable file, so it was not wiped.
                return None
            raise
        # fix(config): hooks also run when Git left the file alone; restoring then would
        # bring back a private key deleted since the latest backup. The index check covers
        # commits whose content another policy filtered.
        if (indexed_bytes and private(live, project(live, POLICY[kind]))
                and raw != indexed_bytes()):
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


def unchanged(root, old, relative):
    """Whether the index copy of a path matches commit old; any failure counts as changed."""
    before = git("rev-parse", "-q", "--verify", f"{old}:{relative}", cwd=root, check=False)
    return before is not None and before == git(
        "rev-parse", "-q", "--verify", f":{relative}", cwd=root, check=False)


def indexed(root, relative):
    """Return the stage-0 index bytes of a path, or None."""
    return git("cat-file", "blob", f":{relative}", cwd=root, check=False, text=False)


def unrestored(older, live, kind):
    """Pair each older backup, newest first, with private sections live still lacks."""
    reported, result = set(), []
    for saved in reversed(older):
        text = read_or_none(saved)
        if text is None:
            continue
        try:
            backup = private_part(parse(text, kind), kind)
        except ValueError:  # One unreadable backup must not hide the others.
            continue
        # The names add_missing would restore are exactly the ones live still lacks.
        names = [name for name in add_missing(copy.deepcopy(live), backup, POLICY[kind])
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
                        help="only restore files exactly as Git wrote them (used by hooks)")
    parser.add_argument("--changed", metavar="OLD",
                        help="with --if-wiped, skip files whose index copy matches commit OLD")
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
        # fix(config): an amend or a branch switch that leaves the file alone must not
        # restore a private key the user deleted. Compare with the index, not the new commit,
        # because a squash merge rewrites the file without moving HEAD.
        if options.changed and unchanged(root, options.changed, relative):
            continue
        try:
            index_copy = (lambda relative=relative: indexed(root, relative)) if options.if_wiped else None
            try:
                result = restore_file(target, source or saved[-1], kind, index_copy)
            except FileNotFoundError:
                if source or not target.exists():
                    raise
                # A concurrent clean rotated the newest backup away; use the one now newest.
                saved = backups(directory, kind)
                result = restore_file(target, saved[-1], kind, index_copy)
        except Exception:
            # fix(privacy): name the file, never its contents.
            print(f"agent-restore: skipped {relative}; it or its backup could not be parsed or written.",
                  file=sys.stderr)
            failed = True
            continue
        if result is None:
            if options.changed:
                # fix(config): Git changed the file, yet it already holds private keys (an agent
                # saved one meanwhile, or a staged change); merging could revive a deleted
                # key, so say so instead of staying silent.
                print(f"agent-restore: {relative} changed in Git but already holds private keys "
                      "or does not parse; run git agent-restore if any are missing.", file=sys.stderr)
            continue
        added, live = result
        if added:
            print(f"agent-restore: restored {', '.join(added)} in {relative}; if you removed them on "
                  f"purpose, run: git agent-restore --forget {kind}", file=sys.stderr)
            if refresh_restored and refresh(root, [relative]):
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


def temporaries(directory, kind):
    """Temp copies a killed backup write left behind; they may hold the same secrets."""
    return list(directory.glob(f".{kind}.*.agent-restore-tmp"))


def restore_temporaries(target):
    """Temp copies a killed restore left beside a config file."""
    return list(target.parent.glob(f".{target.name}.*.agent-restore-tmp"))


def holds_private(text, kind):
    try:
        return bool(private_part(parse(text, kind), kind))
    except ValueError:
        return False


def forget(kind):
    """Purge a file's backups, so a deliberately removed private key (or secret) stays gone."""
    # fix(privacy): a removed secret may be revoked or rotated; every worktree keeps its own
    # backups, so purge them all, including those of worktrees whose directory is gone.
    here = Path(git("rev-parse", "--show-toplevel")) / FILES[kind]
    if here.is_file():
        try:
            parse(here.read_text(), kind)
        except ValueError:  # Conflict markers, say; its backups are the only good copies.
            print(f"agent-restore: {FILES[kind]} does not parse; fix it before --forget.",
                  file=sys.stderr)
            return 1
    common = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir"))
    stale = {common, *(common / "worktrees").glob("*")}
    current = Path(git("rev-parse", "--absolute-git-dir"))
    for line in git("worktree", "list", "--porcelain").splitlines():
        worktree = Path(line.split(" ", 1)[1]) if line.startswith("worktree ") else None
        if worktree is None or not worktree.is_dir():
            continue
        git_dir = Path(git("rev-parse", "--absolute-git-dir", cwd=worktree))
        stale.discard(git_dir)
        directory = git_dir / "agent-config-private"
        old = backups(directory, kind)
        target = worktree / FILES[kind]
        text = read_or_none(target) if target.is_file() else None
        # fix(config): another worktree whose file was wiped (mid-stash, say) still needs
        # its backups to recover unrelated private keys; keep them and say so.
        # A missing file (a branch that predates it, say) counts as wiped too.
        if (git_dir != current and not holds_private(text or "", kind)
                and old and holds_private(read_or_none(old[-1]) or "", kind)):
            print(f"agent-restore: kept the backups of {worktree}, whose {FILES[kind]} is missing "
                  "or holds no private keys; restore it there, then run --forget there.",
                  file=sys.stderr)
            continue
        if text is not None:
            # fix(config): save the current file as the only backup, so this worktree keeps its
            # recovery. Write first, so a failed write keeps the old ones.
            directory.mkdir(mode=0o700, exist_ok=True)
            write_private(directory / f"{kind}.{time.time_ns()}", text)
        for saved in [*old, *temporaries(directory, kind), *restore_temporaries(target)]:
            saved.unlink(missing_ok=True)  # A concurrent rotation may have removed it already.
    for git_dir in stale:
        directory = git_dir / "agent-config-private"
        for saved in [*backups(directory, kind), *temporaries(directory, kind)]:
            saved.unlink(missing_ok=True)
    print(f"agent-restore: kept only each worktree's current {FILES[kind]} as its backup.",
          file=sys.stderr)
    return 0


def seed():
    """Run the clean filter once per file, so its backup exists before any rewrite."""
    root = Path(git("rev-parse", "--show-toplevel"))
    failed = False
    for kind, relative in FILES.items():
        if (root / relative).is_file():
            try:
                git("hash-object", f"--path={relative}", relative, cwd=root)
                text = (root / relative).read_text()
                # fix(config): the filter only warns when a backup fails, so check for it.
                saved = backups(backup_dir(), kind)
                if holds_private(text, kind) and not (saved and read_or_none(saved[-1]) == text):
                    raise OSError("no backup")
            except (subprocess.CalledProcessError, OSError):
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
        for relative in refresh(Path(git("rev-parse", "--show-toplevel")), FILES.values()):
            print(f"agent-status: could not refresh {relative}.", file=sys.stderr)
            exit_code = 1
        sys.exit(exit_code)
    if command == "seed":
        sys.exit(seed())
    if command == "kinds":
        print(" ".join(FILES))
        sys.exit(0)
    filter_main(command)
