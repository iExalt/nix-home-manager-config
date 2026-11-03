#!/usr/bin/env python3
"""Exercise the process-probe guard's decisions and its hook I/O contract.

Commands are synthetic; they mirror the shapes that broke agent waits, not real sessions.
"""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "dotfiles/hooks/process-probe-guard.py"
SPEC = importlib.util.spec_from_file_location("guard", SCRIPT)
GUARD = importlib.util.module_from_spec(SPEC)
sys.dont_write_bytecode = True
SPEC.loader.exec_module(GUARD)


def decision(command, linux=False):
    with mock.patch.object(GUARD, "LINUX", linux):
        result = GUARD.decide(command)
    if not result:
        return "allow"
    out = result["hookSpecificOutput"]
    return out.get("permissionDecision") or ("warn" if out.get("additionalContext") else "allow")


class DecisionTests(unittest.TestCase):
    def check(self, cases, expected, linux=False):
        for command in cases:
            with self.subTest(command=command, linux=linux):
                self.assertEqual(decision(command, linux), expected)

    def test_wrong_results_are_denied(self):
        self.check((
            "until ssh host 'test -f out.apk && ! pgrep -f \"npm run build\"'; do sleep 30; done",
            "ssh host 'while pgrep -f build.sh >/dev/null; do sleep 20; done; tail log'",
            "ssh host 'pkill -f build.sh; sleep 2; echo done'",
            "ssh host \"pgrep -f build.sh | wc -l\"",
            "kubectl exec pod -- bash -c 'pkill -f \"node proxy.mjs\"; node proxy.mjs &'",
            "docker exec box sh -c 'kill $(pgrep -f worker.py)'",
            "while pgrep -af build.sh >/dev/null; do sleep 5; done",  # -a includes ancestors
            "ssh host 'pgrep -f build.sh || echo done; tail log'",
            "ssh host 'pgrep -f worker.py | xargs kill; echo ok'",
            "bash -c 'while pgrep -af build.sh >/dev/null; do sleep 1; done'",
            "/tmp/run-remote.sh 'pkill -f build.sh; sleep 1; echo ok'",  # forwarding wrapper
        ), "deny")

    def test_linux_local_wrapper_is_denied(self):
        self.check(("while pgrep -f build.sh >/dev/null; do sleep 5; done",
                    "pkill -f build.sh; echo stopped"), "deny", linux=True)

    def test_listings_warn(self):
        self.check(("ps -eo pid,args | grep build.sh",
                    "pgrep -af build.sh",
                    "ssh host 'cd /srv && pgrep -fl build.sh'",
                    "ssh host 'tail -3 build.log; pgrep -af build.sh | head -3'",
                    "ssh host 'for p in $(pgrep -f build.sh); do readlink /proc/$p/cwd; done'",
                    "pgrep -fal 'npm ci|npm install' || true"), "warn")
        note = GUARD.decide("ps aux | grep gradle")["hookSpecificOutput"]["additionalContext"]
        self.assertIn("[g]radle", note)

    def test_correct_commands_are_allowed(self):
        self.check((
            "while pgrep -f build.sh >/dev/null; do sleep 5; done",  # macOS excludes ancestors
            "pkill -f build.sh; echo stopped",
            "ssh host 'pgrep -f build.sh'",                          # lone remote command is exec'd
            "ssh host 'pkill -f build.sh' || true",
            "ssh host 'pgrep -f \"[b]uild.sh\" && echo running'",    # bracket trick
            "ssh host 'pgrep -x gradle && echo up'",                 # name match, no -f
            "kubectl exec pod -- pgrep -f worker.py",                # argv, no remote shell
            "ssh host 'kill -0 \"$(cat /tmp/build.pid)\" && echo up'",
            "ssh host 'bash -s' <<'EOF'\nwhile pgrep -f build.sh; do sleep 5; done\nEOF",
            "cat > /tmp/wait.sh <<'EOF'\npkill -f build.sh; until ! pgrep -f build.sh; do sleep 1; done\nEOF",
            "ps aux | grep '[g]radle'",
            "ps aux | grep gradle | grep -v grep",
            "git log --oneline | grep fix",
            "rg -n pgrep scripts/",
            "codex exec \"Run: pgrep -af marker >/dev/null && echo matched || echo none\"",
            "git commit -m 'avoid `while pgrep -af build.sh; do sleep 1; done`'",
            "ssh host 'uptime; pgrep -af \"gradle|vitest\" | grep -v pgrep | wc -l'",  # filtered
        ), "allow")

    def test_deny_reason_names_the_fix(self):
        out = GUARD.decide("ssh h 'pkill -f build.sh; true'")["hookSpecificOutput"]
        for phrase in ("[b]uild.sh", "pidfile", "done-marker"):
            self.assertIn(phrase, out["permissionDecisionReason"])


class HookContractTests(unittest.TestCase):
    def run_hook(self, payload):
        stdin = payload if isinstance(payload, str) else json.dumps(payload)
        return subprocess.run([sys.executable, "-I", "-S", str(SCRIPT)], input=stdin,
                              capture_output=True, text=True, check=True)

    def test_claude_and_codex_inputs(self):
        loop = "ssh h 'while pgrep -f build.sh; do sleep 5; done'"
        for tool_input in ({"command": loop},                          # Claude Bash, Codex Bash
                           {"cmd": loop},                              # exec_command arguments
                           {"command": ["bash", "-lc", loop]},         # argv form
                           'await tools.exec_command({cmd:%s, yield_time_ms:1000})' % json.dumps(loop)):
            with self.subTest(tool_input=tool_input):
                out = json.loads(self.run_hook({"tool_name": "Bash", "tool_input": tool_input}).stdout)
                self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_fails_open_and_stays_silent(self):
        for payload in ("", "not json", {"tool_input": None}, {"tool_input": {"command": "ls"}},
                        {"tool_input": {"command": 42}}):
            with self.subTest(payload=payload):
                self.assertEqual(self.run_hook(payload).stdout, "")


if __name__ == "__main__":
    unittest.main()
