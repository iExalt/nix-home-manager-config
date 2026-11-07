#!/usr/bin/env python3
"""Cheap ownership/parser regressions; executable fixtures never run submitted commands."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "dotfiles/hooks/mise-tool-guard.py"
SPEC = importlib.util.spec_from_file_location("guard", SCRIPT)
GUARD = importlib.util.module_from_spec(SPEC)
sys.dont_write_bytecode = True
SPEC.loader.exec_module(GUARD)


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="mise-guard-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.managed, self.other = self.base / "managed", self.base / "other"
        for directory in (self.managed, self.other):
            directory.mkdir()
            for name in ("python3", "npm", "cargo", "gh", "new-tool"):
                binary = directory / name
                binary.write_text("#!/bin/sh\nexit 99\n")
                binary.chmod(0o755)
        self.owned = {p.name: {str(p.resolve())} for p in self.managed.iterdir()}

    def check(self, command):
        return GUARD.violation(command, str(self.base), lambda cwd: self.owned)

    def test_configuration_drives_aliases_and_new_tools(self):
        for name in self.owned:
            with self.subTest(name=name):
                self.assertIsNotNone(self.check(str(self.other / name)))
                self.assertIsNone(self.check(str(self.managed / name)))
                self.assertIsNotNone(self.check(f"env PATH={self.other} {name} --version"))
                self.assertIsNone(self.check(f"PATH={self.managed} {name} --version"))
        self.assertIsNone(self.check("/usr/bin/git status"))
        for command in (f"PATH={self.other} env python3 -V", f"exec env PATH={self.other} python3 -V",
                        f"command exec {self.other}/python3 -V", f"PATH={self.other} \\\npython3 -V",
                        str(self.other) + "/py\\\nthon3 -V"):
            self.assertIsNotNone(self.check(command))

    def test_sequences_use_new_directory_and_tool_workdir(self):
        visited = []
        result = GUARD.violation(f"cd {self.other} && ./python3 -V", str(self.base),
                                 lambda cwd: visited.append(cwd) or self.owned)
        self.assertIsNotNone(result)
        self.assertEqual(visited, [str(self.other)])
        self.assertIsNotNone(self.check(f"echo ready\n{self.other}/python3 -V"))
        for comment in ("# comment", "# don't", "foo#bar"):
            self.assertIsNotNone(self.check(f"echo {comment}\n{self.other}/python3 -V"))
        self.assertIsNotNone(self.check(f"echo foo#bar; {self.other}/python3 -V"))

    def test_declared_environments_and_pinned_bootstrap(self):
        venv = self.base / "venv"
        (venv / "bin").mkdir(parents=True)
        (venv / "pyvenv.cfg").write_text("home = /example\n")
        (venv / "bin/python3").symlink_to(self.other / "python3")
        local = self.base / "node_modules/.bin"
        local.mkdir(parents=True)
        (local / "npm").symlink_to(self.other / "npm")
        for command in (str(venv / "bin/python3"), str(local / "npm"),
                        "/nix/store/" + "a" * 32 + "-python/bin/python3"):
            self.assertIsNone(self.check(command))
        child = self.base / "src"
        child.mkdir()
        self.assertIsNone(GUARD.violation("../node_modules/.bin/npm --version", str(child), lambda cwd: self.owned))

    def test_inspection_and_unknown_contexts_do_not_execute_or_deny(self):
        for command in ("python3 -V", "command -v /usr/bin/python3", "echo '/usr/bin/python3'",
                        "mise exec python -- /usr/bin/python3", "ssh example /usr/bin/python3",
                        "bash -c '/usr/bin/python3 -V'", "PATH=$PATH python3 -V",
                        "source .venv/bin/activate; /usr/bin/python3 -V",
                        "cat <<'EOF'\n/usr/bin/python3\nEOF", "$(touch should-not-exist)",
                        "printf '%s\\n' ';' /usr/bin/python3", "echo '&&' /usr/bin/python3",
                        "echo '\n' /usr/bin/python3", "echo \\; /usr/bin/python3"):
            self.assertIsNone(self.check(command), command)
        self.assertIsNotNone(self.check(f"'{self.other}/python3' -c 'print(1)'"))
        self.assertFalse((self.base / "should-not-exist").exists())

    def test_missing_selected_version_retains_alias_ownership(self):
        data = [[], {"python": [{"active": False, "installed": False, "version": "missing", "requested_version": "missing"},
                                 {"installed": True, "version": "old"}]},
                [{"name": "python3", "path": str(self.managed / "python3")}]]
        with patch.object(GUARD.subprocess, "run", side_effect=[
                subprocess.CompletedProcess([], 0, json.dumps(value)) for value in data]):
            owned = GUARD.owned_executables(str(self.base))
        self.assertEqual(owned, {"python3": set()})
        self.assertIn("not installed", GUARD.violation(str(self.other / "python3"), str(self.base), lambda cwd: owned))

    def test_hook_json_contract_and_metadata_failure(self):
        import io
        payload = {"cwd": "/ignored", "tool_input": {"workdir": str(self.base), "cmd": str(self.other / "python3")}}
        with patch.object(GUARD, "owned_executables", return_value=self.owned):
            # Default parameters bind functions at definition time; inject through metadata instead.
            with patch.object(GUARD.subprocess, "run", side_effect=OSError("metadata unavailable")):
                output = io.StringIO()
                with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))), patch.object(sys, "stdout", output):
                    GUARD.main()
                self.assertIn("could not check", json.loads(output.getvalue())["hookSpecificOutput"]["additionalContext"])


if __name__ == "__main__":
    unittest.main()
