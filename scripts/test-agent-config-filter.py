#!/usr/bin/env python3
"""Exercise privacy projection, the clean filter, and three-way sync."""

import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest

SCRIPT = Path(__file__).with_name("clean-agent-config.py").resolve()
SPEC = importlib.util.spec_from_file_location("clean_filter", SCRIPT)
FILTER = importlib.util.module_from_spec(SPEC)
sys.dont_write_bytecode = True
SPEC.loader.exec_module(FILTER)


class CleanFilterTests(unittest.TestCase):
    def test_codex_privacy_and_idempotence(self):
        source = '''model = "example"
notify = ["/private/tool"]
unknown_future_key = "private value"
developer_instructions = "Read /private/instructions"
[projects."/private/project"]
trust_level = "trusted"
[mcp_servers.private]
url = "https://private.example"
[marketplaces.private]
source = "/private/marketplace"
[features]
goals = true
[tui]
status_line = ["model", "git-branch"]
screen_reader_detection_done = true
[tui.model_availability_nux]
example = 4
'''
        output = FILTER.clean(source, "codex")
        self.assertEqual(tomllib.loads(output), {
            "model": "example", "features": {"goals": True},
            "tui": {"status_line": ["model", "git-branch"]},
        })
        self.assertEqual(output, FILTER.clean(output, "codex"))

    def test_named_preferences_without_their_private_siblings(self):
        codex = FILTER.clean('''[desktop]
preventSleepWhileRunning = true
show-context-window-usage = true
conversationDetailMode = "STEPS_PROSE"
[desktop.daybreak-enabled]
accountId = "private"
''', "codex")
        self.assertEqual(tomllib.loads(codex), {"desktop": {
            "preventSleepWhileRunning": True, "show-context-window-usage": True,
            "conversationDetailMode": "STEPS_PROSE",
        }})
        claude = FILTER.clean(json.dumps({
            "autoCompactWindow": 500000,
            "env": {"CLAUDE_CODE_SILENT_TURN_REMINDER_TEXT": "Update me.", "API_TOKEN": "secret"},
        }), "claude")
        self.assertEqual(json.loads(claude), {
            "autoCompactWindow": 500000,
            "env": {"CLAUDE_CODE_SILENT_TURN_REMINDER_TEXT": "Update me."},
        })

    def test_claude_paths_and_unknown_state(self):
        source = json.dumps({
            "model": "example", "extraKnownMarketplaces": {"private": {"path": "/private"}},
            "statusLine": {"command": "run --config=~/private"},
            "permissions": {"defaultMode": "default", "additionalDirectories": ["/private"]},
            "enabledPlugins": {"safe@public": True, "C:\\private": True},
            "apiKey": "secret",
        })
        output = FILTER.clean(source, "claude")
        self.assertEqual(json.loads(output), {
            "model": "example", "permissions": {"defaultMode": "default"},
            "enabledPlugins": {"safe@public": True},
        })
        self.assertEqual(output, FILTER.clean(output, "claude"))

    def test_claude_instruction_files_excludes_other_plugin_state(self):
        source = json.dumps({"pluginConfigs": {
            "cc-plugin-agents-md@builtin": {
                "options": {
                    "instructionFiles": "claude-md-and-agents-md",
                    "unknownOption": "private value",
                },
                "privateState": "secret",
            },
            "other@plugin": {"options": {"instructionFiles": "private value"}},
        }})
        output = FILTER.clean(source, "claude")
        self.assertEqual(json.loads(output), {"pluginConfigs": {
            "cc-plugin-agents-md@builtin": {
                "options": {"instructionFiles": "claude-md-and-agents-md"},
            },
        }})
        self.assertEqual(output, FILTER.clean(output, "claude"))
        self.assertEqual(json.loads(FILTER.clean(
            source.replace("claude-md-and-agents-md", "/private/instructions"), "claude"
        )), {})

    def test_claude_keeps_shared_hooks_whole_or_not_at_all(self):
        shared = {"type": "command", "timeout": 10,
                  "command": 'python3 -I "$HOME/.config/agent-hooks/check.py"'}
        source = {"hooks": {
            "PreToolUse": [{"matcher": "AskUserQuestion", "hooks": [shared]}],
            "Stop": [{"matcher": "", "hooks": [dict(shared, command="/private/hook.sh")]}],
            "PostToolUse": [{"matcher": "Bash", "hooks": [dict(shared, privateKey="x")]}],
        }}
        output = FILTER.clean(json.dumps(source), "claude")
        self.assertEqual(json.loads(output), {"hooks": {"PreToolUse": source["hooks"]["PreToolUse"]}})
        self.assertEqual(output, FILTER.clean(output, "claude"))

    def test_filter_kinds_match_gitattributes(self):
        attributes = SCRIPT.parents[1].joinpath(".gitattributes").read_text()
        for kind, relative in FILTER.FILES.items():
            self.assertIn(f"/{relative} filter=agent-{kind}", attributes)

    def test_toml_escapes_round_trip(self):
        data = {"projects": {"/x/\U0001F600 proj": {"note": "del\x7f tab\t"}}}
        self.assertEqual(tomllib.loads(FILTER.dump(data, "codex")), data)

    def test_filter_warns_when_a_reviewed_key_stays_local(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "codex", FILTER.FILES["codex"]],
                                capture_output=True, text=True,
                                input='developer_instructions = "Report progress and/or blockers"\n'
                                      'model = {nested = 1}\n'
                                      '[projects."/private"]\nx = 1\n', cwd=tempfile.gettempdir())
        self.assertEqual(result.stdout, "\n")
        self.assertIn("kept developer_instructions local; its value contains a path-like", result.stderr)
        self.assertIn("kept model local; its value is not a reviewed type", result.stderr)
        self.assertNotIn("projects", result.stderr)

    def test_codex_private_sections_round_trip(self):
        dates = tomllib.loads('at = 1979-05-27T07:32:00Z\nday = 1979-05-27\nclock = 07:32:00.5\n'
                              'local = 1979-05-27T07:32:00\nbig = inf\nsmall = -inf\nodd = nan\n')
        restored = tomllib.loads(FILTER.dump({"notice": dates}, "codex"))["notice"]
        self.assertTrue(math.isnan(restored.pop("odd")))
        self.assertEqual(restored, {key: value for key, value in dates.items() if key != "odd"})
        data = {"mcp_servers": {"docs": {"command": "/bin/docs", "args": ["--port", "1"],
                                         "env": {"KEY": "value"}}},
                "projects": {"/private/a b": {"trust_level": "trusted"}},
                "hooks": {"tables": [{"name": "x", "nested": {"on": True}}]}}
        self.assertEqual(tomllib.loads(FILTER.dump(data, "codex")), data)



SHARED_HOOK = {"matcher": "Bash", "hooks": [
    {"type": "command", "command": '"$HOME/.config/agent-hooks/check.sh"'}]}
NEW_HOOK = {"matcher": "Edit", "hooks": [
    {"type": "command", "command": '"$HOME/.config/agent-hooks/lint.sh"'}]}
PRIVATE_HOOK = {"matcher": "Bash", "hooks": [{"type": "command", "command": "/opt/private"}]}


class MergeTests(unittest.TestCase):
    def merge(self, live, shared, base):
        return FILTER.merge(live, shared, base, FILTER.POLICY["claude"])

    def test_each_side_keeps_its_own_changes_and_private_keys_stay_put(self):
        live = {"model": "local", "theme": "dark", "effortLevel": "high", "env": {"TOKEN": "t"},
                "permissions": {"allow": ["Bash(/bin/x)"], "defaultMode": "plan"}}
        base = {"model": "old", "theme": "dark", "effortLevel": "high",
                "permissions": {"defaultMode": "plan"}}
        shared = {"model": "old", "theme": "light", "permissions": {"defaultMode": "plan"},
                  "switchModelsOnFlag": True}
        merged_live, merged_shared, report = self.merge(live, shared, base)
        self.assertEqual(merged_shared, {"model": "local", "theme": "light", "switchModelsOnFlag": True,
                                         "permissions": {"defaultMode": "plan"}})
        self.assertEqual(merged_live, {"model": "local", "theme": "light", "env": {"TOKEN": "t"},
                                       "permissions": {"allow": ["Bash(/bin/x)"], "defaultMode": "plan"},
                                       "switchModelsOnFlag": True})
        self.assertEqual(report["exported"], [("model",)])
        self.assertEqual(report["conflicts"], [])

    def test_both_sides_changed_keeps_local(self):
        merged_live, merged_shared, report = self.merge({"model": "a"}, {"model": "b"}, {"model": "c"})
        self.assertEqual((merged_live, merged_shared), ({"model": "a"}, {"model": "a"}))
        self.assertEqual(report["conflicts"], [("model",)])

    def test_without_a_base_nothing_is_deleted(self):
        live = {"model": "x", "env": {"TOKEN": "t"}}
        shared = {"model": "y", "theme": "dark"}
        merged_live, merged_shared, report = self.merge(live, shared, {})
        self.assertEqual(merged_live, {"model": "x", "env": {"TOKEN": "t"}, "theme": "dark"})
        self.assertEqual(merged_shared, {"model": "x", "theme": "dark"})
        self.assertEqual(report["conflicts"], [("model",)])

    def test_a_local_value_git_cannot_share_is_left_alone_both_ways(self):
        live = {"statusLine": {"command": "~/bin/status"}}
        for base in ({"statusLine": {"command": "show"}}, {}):
            merged_live, merged_shared, report = self.merge(live, {"statusLine": {"command": "show"}}, base)
            self.assertEqual(merged_live, live)
            self.assertEqual(merged_shared, {"statusLine": {"command": "show"}})
            self.assertEqual(report["kept"], [("statusLine", "command")])

    def test_hook_lists_take_repo_items_and_keep_private_ones(self):
        live = {"hooks": {"Stop": [PRIVATE_HOOK, SHARED_HOOK]}}
        unchanged, _, _ = self.merge(live, {"hooks": {"Stop": [SHARED_HOOK]}},
                                     {"hooks": {"Stop": [SHARED_HOOK]}})
        self.assertEqual(unchanged, live)
        merged_live, merged_shared, _ = self.merge(live, {"hooks": {"Stop": [SHARED_HOOK, NEW_HOOK]}},
                                                   {"hooks": {"Stop": [SHARED_HOOK]}})
        self.assertEqual(merged_live, {"hooks": {"Stop": [SHARED_HOOK, NEW_HOOK, PRIVATE_HOOK]}})
        self.assertEqual(merged_shared, {"hooks": {"Stop": [SHARED_HOOK, NEW_HOOK]}})
        emptied, _, _ = self.merge({"hooks": {"Stop": [SHARED_HOOK]}}, {},
                                   {"hooks": {"Stop": [SHARED_HOOK]}})
        self.assertEqual(emptied, {})


LIVE_CLAUDE = {"model": "opus", "theme": "dark", "permissions": {"allow": ["Bash(/bin/x)"]}}
LIVE_CODEX = 'model = "m"\n[projects."/work"]\ntrust_level = "trusted"\n'


class SyncCommandTests(unittest.TestCase):

    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="agent-sync-test-")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.repo, self.home, self.state = (self.root / name for name in ("repo", "home", "state"))
        for kind in FILTER.FILES:
            (self.repo / FILTER.FILES[kind]).parent.mkdir(parents=True, exist_ok=True)
            (self.home / FILTER.LIVE[kind]).parent.mkdir(parents=True, exist_ok=True)

    def path(self, kind, side):
        return (self.repo / FILTER.FILES[kind]) if side == "shared" else (self.home / FILTER.LIVE[kind])

    def sync(self, *arguments):
        return subprocess.run([sys.executable, str(SCRIPT), "sync", "--repo", str(self.repo),
                               "--home", str(self.home), "--state", str(self.state), *arguments],
                              capture_output=True, text=True)

    def test_migrates_retired_symlinks_once(self):
        full = {"claude": json.dumps(LIVE_CLAUDE), "codex": LIVE_CODEX}
        for kind, text in full.items():
            self.path(kind, "shared").write_text(text)
            self.path(kind, "live").symlink_to(self.path(kind, "shared"))
        result = self.sync()
        self.assertEqual(result.returncode, 0, result.stderr)
        for kind, text in full.items():
            live = self.path(kind, "live")
            self.assertFalse(live.is_symlink())
            self.assertEqual(os.stat(live).st_mode & 0o777, 0o600)
            self.assertEqual(FILTER.parse(live.read_text(), kind), FILTER.parse(text, kind))
            self.assertEqual(self.path(kind, "shared").read_text(), FILTER.clean(text, kind))
        before = {path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        again = self.sync()
        self.assertEqual((again.returncode, again.stdout), (0, ""), again.stderr)
        self.assertEqual({path: path.read_bytes() for path in self.root.rglob("*") if path.is_file()},
                         before)

    def test_seeds_from_the_newest_backup_when_a_pull_wiped_the_repo_copy(self):
        backups = self.repo / ".git" / "agent-config-private"
        backups.mkdir(parents=True)
        (backups / "claude.9").write_text(json.dumps(LIVE_CLAUDE | {"model": "stale"}))
        (backups / "claude.10").write_text(json.dumps(LIVE_CLAUDE))
        self.path("claude", "shared").write_text(json.dumps({"model": "pulled", "theme": "dark"}))
        result = self.sync("claude")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.path("claude", "live").read_text()),
                         LIVE_CLAUDE | {"model": "pulled"})

    def test_a_machine_without_a_base_gets_repo_keys_and_shares_its_own(self):
        self.path("claude", "shared").write_text(FILTER.clean('{"theme": "dark"}', "claude"))
        self.path("claude", "live").write_text('{"model": "opus", "env": {"TOKEN": "t"}}')
        result = self.sync("claude")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.path("claude", "live").read_text()),
                         {"model": "opus", "env": {"TOKEN": "t"}, "theme": "dark"})
        self.assertEqual(json.loads(self.path("claude", "shared").read_text()),
                         {"model": "opus", "theme": "dark"})

    def test_never_strips_private_keys_the_live_file_lacks(self):
        shared_text = json.dumps(LIVE_CLAUDE)
        self.path("claude", "shared").write_text(shared_text)
        self.path("claude", "live").write_text('{"model": "opus"}')
        result = self.sync("claude")
        self.assertEqual(result.returncode, 1)
        self.assertIn("still holds private keys", result.stderr)
        self.assertEqual(self.path("claude", "shared").read_text(), shared_text)

    def test_overlays_add_private_keys_only_and_worktrees_are_refused(self):
        shared_text = FILTER.clean('model = "m"\n', "codex")
        self.path("codex", "shared").write_text(shared_text)
        overlay = self.root / "overlay.toml"
        overlay.write_text('[mcp_servers.docs]\nurl = "https://docs.example"\n')
        result = self.sync("codex", "--overlay", f"codex={overlay}")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(tomllib.loads(self.path("codex", "live").read_text()),
                         {"model": "m", "mcp_servers": {"docs": {"url": "https://docs.example"}}})
        self.assertEqual(self.path("codex", "shared").read_text(), shared_text)
        overlay.write_text('model = "other"\n')
        self.assertIn("overlays may set private keys only",
                      self.sync("codex", "--overlay", f"codex={overlay}").stderr)
        (self.repo / ".git").write_text("gitdir: elsewhere\n")
        self.assertIn("linked worktree", self.sync().stderr)


if __name__ == "__main__":
    unittest.main()
