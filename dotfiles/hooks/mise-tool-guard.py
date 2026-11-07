#!/usr/bin/env python3
"""Catch explicit bypasses of Mise-selected tools; never evaluate submitted shell code.

Ownership comes from `mise bin-paths --json`, including companion executables.
Checks literal paths and literal inline PATH assignments in simple local commands,
including sequences with literal cd. Bare commands inherit shell activation; a hook's
PATH is not proof of the tool shell's PATH. Nested shells/scripts, dynamic expressions,
remote execution and compound shell control flow are outside this guard's coverage.
This is a workflow check, not a sandbox. Unknown syntax fails open.
"""
import json
import os
from pathlib import Path
import re
import bashlex
import shutil
import subprocess
import sys

PINNED = re.compile(r"^/nix/store/[a-z0-9]{32}-[^/]+/")
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z_0-9]*=")
DYNAMIC = re.compile(r"[$`*?\[~]")
def literal_commands(source):
    """Use shell grammar for boundaries; inspect only literal local command sequences."""
    def words(node):
        if node.kind == "list":
            for part in node.parts:
                if part.kind == "operator":
                    if part.op not in (";", "&&", "\n"):
                        raise ValueError("unsupported shell operator")
                else:
                    yield from words(part)
        elif node.kind == "command":
            if any(part.kind not in ("word", "assignment") or part.parts for part in node.parts):
                raise ValueError("nonliteral shell command")
            yield [part.word for part in node.parts]
        else:
            raise ValueError("unsupported shell construct")

    return [command for node in bashlex.parse(source) for command in words(node)]


def owned_executables(cwd):
    def metadata(*args):
        result = subprocess.run([os.environ.get("AGENT_MISE_BIN", "mise"), *args],
                                cwd=cwd, capture_output=True, text=True, timeout=3, check=True)
        return json.loads(result.stdout)

    owned = {}
    for entry in metadata("bin-paths", "--json"):
        owned.setdefault(entry["name"], set()).add(os.path.realpath(entry["path"]))
    # A missing selected version must not turn a known executable into an unmanaged one.
    # Recover names from an installed version, but never authorize that other version.
    for tool, versions in metadata("ls", "--json").items():
        if any(v.get("requested_version") and not v.get("installed") for v in versions):
            installed = next((v for v in versions if v.get("installed")), None)
            if installed is None:
                raise ValueError("selected tool has no installed executable metadata")
            for entry in metadata("bin-paths", "--json", tool + "@" + installed["version"]):
                owned.setdefault(entry["name"], set())
    return owned


def project_executable(filename, cwd):
    """Allow explicit venv interpreters and project-local executable directories."""
    candidate = Path(os.path.abspath(filename))
    # Check lexical location before resolving Python's symlink to its base interpreter.
    if candidate.parent.name in ("bin", "Scripts") and (candidate.parent.parent / "pyvenv.cfg").is_file():
        return True
    # Node package scripts are selected by the project's dependency installation.
    if candidate.parent.name == ".bin" and candidate.parent.parent.name == "node_modules":
        project = candidate.parent.parent.parent
        directory = Path(os.path.abspath(cwd))
        return candidate.is_file() and (directory == project or project in directory.parents or directory in project.parents)
    return False


def violation(command, cwd, lookup=owned_executables):
    try:
        segments = literal_commands(command)
    except (ValueError, NotImplementedError, bashlex.errors.ParsingError):
        return None
    cache = {}
    for args in segments:
        if not args:
            continue
        if args[0] in ("if", "for", "while", "until", "case", "function", "source", ".", "eval", "export", "unset"):
            return None
        search_path = None
        # Prefixes can compose in any order: PATH=... env, exec env PATH=..., etc.
        while args:
            if ASSIGNMENT.match(args[0]):
                key, value = args[0].split("=", 1)
                if key == "PATH":
                    if DYNAMIC.search(value):
                        return None
                    search_path = value
                elif key.startswith("MISE_") or key in ("HOME", "XDG_CONFIG_HOME", "VIRTUAL_ENV"):
                    return None
                args = args[1:]
            elif args[0] in ("env", "command", "exec"):
                args = args[1:]
                if args and args[0] == "--":
                    args = args[1:]
                if args and args[0].startswith("-"):
                    return None  # inspection and environment-changing flags aren't executed here
            else:
                break
        if not args:
            return None  # standalone assignments change later resolution
        executable = args[0]
        if DYNAMIC.search(executable):
            return None
        if executable == "cd":
            if len(args) != 2 or DYNAMIC.search(args[1]):
                return None
            destination = os.path.abspath(os.path.join(cwd, args[1]))
            if not os.path.isdir(destination):
                return None
            cwd = destination
            continue
        if "/" not in executable and search_path is None:
            continue  # actual shell activation, not the hook's inherited PATH, owns this
        name = os.path.basename(executable)
        if cwd not in cache:
            cache[cwd] = lookup(cwd)
        if name not in cache[cwd]:
            continue
        allowed = cache[cwd][name]
        if "/" in executable:
            actual = os.path.abspath(os.path.join(cwd, executable))
        else:
            directories = [os.path.abspath(os.path.join(cwd, part)) for part in search_path.split(os.pathsep)]
            actual = shutil.which(executable, path=os.pathsep.join(directories))
        if not actual:
            continue  # a missing executable is the shell's error, not a competing installation
        if os.path.realpath(actual) in allowed or PINNED.match(actual) or project_executable(actual, cwd):
            continue
        shims = Path(os.environ.get("MISE_DATA_DIR", str(Path.home() / ".local/share/mise"))) / "shims"
        if Path(actual).parent == shims and Path(actual).is_file():
            continue
        return ("mise-tool-guard: `%s` bypasses the selected Mise/project executable for `%s`. "
                "Use `%s` without the PATH override, or run it with `mise exec <owning-tool> -- %s ...` "
                "using the project's configured version. Selected path: %s"
                % (executable, name, name, name,
                   sorted(allowed)[0] if allowed else "selected version is not installed"))
    return None


def main():
    payload = json.load(sys.stdin)
    tool_input = payload.get("tool_input", {})
    if not isinstance(tool_input, dict):
        return
    command = tool_input.get("command", tool_input.get("cmd"))
    if not isinstance(command, str):
        return
    cwd = tool_input.get("workdir") or tool_input.get("cwd") or payload.get("cwd") or os.getcwd()
    try:
        reason = violation(command, cwd)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        # Fail visibly open when local metadata is unavailable; never imply enforcement ran.
        json.dump({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext":
                   "mise-tool-guard could not check tool ownership (%s); use explicit Mise execution."
                   % type(error).__name__}}, sys.stdout)
        return
    if reason:
        json.dump({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                         "permissionDecisionReason": reason}}, sys.stdout)


if __name__ == "__main__":
    main()
