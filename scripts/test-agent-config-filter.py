#!/usr/bin/env python3
"""Exercise privacy projection and Git's actual clean-filter behavior."""

import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
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

    def test_restore_adds_only_missing_private_keys(self):
        backup = {"model": "old", "switchModelsOnFlag": True,
                  "permissions": {"defaultMode": "default", "allow": ["Bash(/private:*)"]},
                  "extraKnownMarketplaces": {"private": {"path": "/private"}}}
        live = {"model": "new", "permissions": {"defaultMode": "plan"}}
        extra = FILTER.private(backup, FILTER.project(backup, FILTER.CLAUDE))
        self.assertEqual(sorted(FILTER.add_missing(live, extra, FILTER.CLAUDE)),
                         ["extraKnownMarketplaces", "permissions.allow"])
        # A portable key removed on purpose stays removed; live values win.
        self.assertEqual(live["model"], "new")
        self.assertNotIn("switchModelsOnFlag", live)
        self.assertEqual(live["permissions"]["defaultMode"], "plan")

    def test_filter_kinds_match_gitattributes(self):
        attributes = SCRIPT.parents[1].joinpath(".gitattributes").read_text()
        for kind, relative in FILTER.FILES.items():
            self.assertIn(f"/{relative} filter=agent-{kind}", attributes)

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

    def test_backup_skips_wiped_input_and_rotates(self):
        with tempfile.TemporaryDirectory(prefix="agent-backup-test-") as directory:
            directory = Path(directory)

            def save(text):
                data = tomllib.loads(text)
                FILTER.back_up(text, "codex", data, FILTER.project(data, FILTER.CODEX), directory)

            full = 'model = "a"\n[projects."/one"]\nx = 1\n[projects."/two"]\nx = 2\n'
            save(full)
            save('model = "a"\n')  # A wiped file never replaces the backup.
            save(full)  # Unchanged content adds no version.
            self.assertEqual([item.read_text() for item in FILTER.backups(directory, "codex")], [full])
            for index in range(FILTER.KEEP_BACKUPS + 2):
                save(f'model = "{index}"\n[projects."/one"]\nx = 1\n'
                     f'[tui.model_availability_nux]\nsome-model = {index}\n')
            kept = [item.read_text() for item in FILTER.backups(directory, "codex")]
            # The only backup holding /two survives rotation while it is young.
            self.assertEqual(kept[0], full)
            self.assertEqual(len(kept), FILTER.KEEP_BACKUPS + 1)
            FILTER.rotate(directory, "codex", time.time_ns() + FILTER.KEEP_UNIQUE_SECONDS * 10**9)
            self.assertNotIn(full, [item.read_text() for item in FILTER.backups(directory, "codex")])

    def test_lists_keep_portable_items_and_restore_private_ones(self):
        def hook(command):
            return {"matcher": "", "hooks": [{"type": "command", "command": command}]}

        mine = hook('python3 "$HOME/.config/agent-hooks/a.py"')
        theirs = hook('python3 "$HOME/.config/agent-hooks/b.py"')
        local = hook("/private/hook.sh")
        backup = {"hooks": {"Stop": [mine, local]}}
        kept = FILTER.project(backup, FILTER.CLAUDE)
        self.assertEqual(kept, {"hooks": {"Stop": [mine]}})
        # A pull adds another shared hook and drops the private one from the file.
        live = {"hooks": {"Stop": [mine, theirs]}}
        self.assertEqual(FILTER.add_missing(live, FILTER.private(backup, kept), FILTER.CLAUDE), ["hooks.Stop"])
        self.assertEqual(live, {"hooks": {"Stop": [mine, theirs, local]}})
        # The filtered content still matches what Git holds: no phantom deletion.
        self.assertEqual(FILTER.project(live, FILTER.CLAUDE), {"hooks": {"Stop": [mine, theirs]}})
        # A plain list is tracked whole, so the pulled copy wins over a local one.
        backup = {"tui": {"status_line": ["model", "~/bin/x"]}}
        live = {"tui": {"status_line": ["model", "git-branch"]}}
        extra = FILTER.private(backup, FILTER.project(backup, FILTER.CODEX))
        self.assertEqual(FILTER.add_missing(live, extra, FILTER.CODEX), [])
        self.assertEqual(live, {"tui": {"status_line": ["model", "git-branch"]}})

    def test_hook_restore_leaves_unparsable_files_alone(self):
        with tempfile.TemporaryDirectory(prefix="agent-restore-test-") as directory:
            target, saved = Path(directory, "settings.json"), Path(directory, "claude.1")
            saved.write_text(json.dumps({"extraKnownMarketplaces": {"m": {}}}))
            target.write_text("<<<<<<< HEAD\n{}\n=======\n{}\n>>>>>>> other\n")
            self.assertIsNone(FILTER.restore_file(target, saved, "claude", lambda: b"{}\n"))
            with self.assertRaises(ValueError):
                FILTER.restore_file(target, saved, "claude")
            # Exactly what Git wrote is restored, even when today's policy would filter it
            # differently; a file with private content Git did not write is left alone.
            target.write_text('{"retiredKey": 1}\n')
            self.assertIsNone(FILTER.restore_file(target, saved, "claude", lambda: b"{}\n"))
            added, _ = FILTER.restore_file(target, saved, "claude", lambda: b'{"retiredKey": 1}\n')
            self.assertEqual(added, ["extraKnownMarketplaces"])

    def test_restore_names_private_sections_left_in_older_backups(self):
        with tempfile.TemporaryDirectory(prefix="agent-restore-test-") as directory:
            def backup(index, data):
                path = Path(directory, f"claude.{index}")
                path.write_text(json.dumps(data))
                return path

            nux = {"permissions": {"allow": ["Bash(a)"]}}
            full = {"permissions": {"allow": ["Bash(a)"]}, "extraKnownMarketplaces": {"m": {}},
                    "apiKeyHelper": "/private/helper"}
            older = [backup(1, full), backup(2, {**nux, "apiKeyHelper": "/private/helper"})]
            self.assertEqual(FILTER.unrestored(older, dict(nux), "claude"),
                             [(older[1], ["apiKeyHelper"]), (older[0], ["extraKnownMarketplaces"])])
            # A private list item only an older backup holds is named too.
            live = {"permissions": {"allow": ["Bash(b)"]}}
            self.assertEqual(FILTER.unrestored(older[:1], live, "claude"),
                             [(older[0], ["permissions.allow", "extraKnownMarketplaces", "apiKeyHelper"])])

    def test_restore_retries_when_the_file_changes_meanwhile(self):
        with tempfile.TemporaryDirectory(prefix="agent-restore-test-") as directory:
            target, saved = Path(directory, "settings.json"), Path(directory, "claude.1")
            saved.write_text(json.dumps({"extraKnownMarketplaces": {"m": {"path": "/m"}}}))
            target.write_text(json.dumps({"model": "a"}))
            original, calls = FILTER.dump, []

            def racing_dump(data, kind):
                if not calls:  # An agent saves a new key between the read and the write.
                    target.write_text(json.dumps({"model": "a", "theme": "agent-write"}))
                calls.append(kind)
                return original(data, kind)

            FILTER.dump = racing_dump
            try:
                added, _ = FILTER.restore_file(target, saved, "claude")
            finally:
                FILTER.dump = original
            self.assertEqual(added, ["extraKnownMarketplaces"])
            self.assertEqual(json.loads(target.read_text()), {
                "model": "a", "theme": "agent-write", "extraKnownMarketplaces": {"m": {"path": "/m"}}})

    def test_git_filter_backup_hooks_and_restore(self):
        with tempfile.TemporaryDirectory(prefix="agent-filter-test-") as directory:
            origin, clone = Path(directory, "origin"), Path(directory, "clone")
            # Keep the user's global hooks, signing, and aliases out of the test.
            isolated = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}

            def git(root, *args, check=True):
                result = subprocess.run(
                    ["git", "-C", str(root), "-c", "user.name=Test",
                     "-c", "user.email=test@example.invalid", *args],
                    check=False, capture_output=True, text=True, env=isolated)
                if check and result.returncode:
                    self.fail(f"git {' '.join(args)} failed: {result.stderr.strip()}")
                return result

            def install(root):
                (root / "scripts").mkdir(exist_ok=True)
                for name in ("clean-agent-config.py", "install-git-filters.sh"):
                    shutil.copy(SCRIPT.with_name(name), root / "scripts" / name)
                subprocess.run(["bash", str(root / "scripts/install-git-filters.sh")], check=True,
                               capture_output=True, env={**isolated, "FILTER_PYTHON": sys.executable})

            config_path = "dotfiles/.codex/config.toml"
            private = ('[projects."/private/one"]\ntrust_level = "trusted"\n'
                       '[projects."/private/two"]\ntrust_level = "trusted"\n')
            trusted = {"trust_level": "trusted"}
            # The origin only publishes filtered commits, so it needs no filter.
            git(directory, "init", "-q", str(origin))
            (origin / ".gitattributes").write_text(f"/{config_path} filter=agent-codex\n")
            (origin / config_path).parent.mkdir(parents=True)
            (origin / config_path).write_text(FILTER.clean('model = "one"', "codex"))
            git(origin, "add", ".")
            git(origin, "commit", "-qm", "test: base")

            git(directory, "clone", "-q", str(origin), str(clone))
            install(clone)
            config = clone / config_path
            config.write_text(config.read_text() + private)
            self.assertEqual(git(clone, "agent-status", "--porcelain", "--", "dotfiles").stdout, "")

            def publish(model):
                (origin / config_path).write_text(FILTER.clean(f'model = "{model}"', "codex"))
                git(origin, "commit", "-qam", f"test: {model}")

            def assert_restored(model, projects=("/private/one", "/private/two")):
                self.assertEqual(tomllib.loads(config.read_text()), {
                    "model": model, "projects": {name: trusted for name in projects}})

            publish("two")
            git(clone, "pull", "-q", "--no-rebase")
            assert_restored("two")

            (clone / "note").write_text("local\n")
            git(clone, "add", "note")
            git(clone, "commit", "-qm", "test: local")
            publish("three")
            git(clone, "pull", "-q", "--rebase")
            assert_restored("three")

            # Hooks leave a file with private content alone, so a deletion sticks even when
            # no clean ran since the latest backup.
            data = tomllib.loads(config.read_text())
            del data["projects"]["/private/two"]
            config.write_text(FILTER.dump(data, "codex"))
            git(clone, "checkout", "-q", "-b", "side")
            assert_restored("three", ["/private/one"])
            # Once agent-status has backed up the deletion, a forced rewrite restores without it.
            git(clone, "agent-status", "--porcelain")
            git(clone, "reset", "-q", "--hard")
            git(clone, "agent-status", "--porcelain")
            assert_restored("three", ["/private/one"])

            # Cherry-pick rewrites the file without a hook; agent-status restores it.
            config.write_text(config.read_text().replace('"three"', '"picked"'))
            git(clone, "commit", "-qam", "test: picked")
            git(clone, "checkout", "-q", "-")
            assert_restored("three", ["/private/one"])
            git(clone, "cherry-pick", "side")
            self.assertNotIn("projects", config.read_text())
            git(clone, "agent-status", "--porcelain")
            assert_restored("picked", ["/private/one"])

            # Stash fires no hook; agent-restore recovers, and the wiped file never
            # replaced the backup.
            config.write_text(config.read_text().replace('"picked"', '"local"'))
            git(clone, "stash", "-q")
            git(clone, "status", "--porcelain")
            self.assertNotIn("projects", config.read_text())
            git(clone, "stash", "pop", "-q")
            # The popped file holds a portable change, so it differs from the index, but it
            # holds no private content either; agent-status restores it.
            git(clone, "agent-status", "--porcelain")
            assert_restored("local", ["/private/one"])
            # --from resolves against the directory the user ran it from.
            backup_dir = Path(git(clone, "rev-parse", "--absolute-git-dir").stdout.strip(),
                              "agent-config-private")
            self.assertNotEqual(git(clone, "agent-restore", "--from", check=False).returncode, 0)
            relative = os.path.relpath(FILTER.backups(backup_dir, "codex")[-1],
                                       (clone / "dotfiles").resolve())
            subprocess.run(["git", "agent-restore", "--from", relative], cwd=clone / "dotfiles",
                           check=True, capture_output=True, env=isolated)
            assert_restored("local", ["/private/one"])
            git(clone, "add", config_path)
            self.assertNotIn("private", git(clone, "show", f":{config_path}").stdout)

            # Forget purges every backup of the removed key, so nothing brings it back.
            config.write_text(FILTER.clean(config.read_text(), "codex"))
            self.assertIn("--forget codex", git(clone, "agent-status", "--porcelain").stderr)
            config.write_text(FILTER.clean(config.read_text(), "codex"))
            git(clone, "agent-restore", "--forget", "codex")
            git(clone, "agent-status", "--porcelain")
            self.assertNotIn("projects", config.read_text())
            self.assertFalse(any("private" in item.read_text()
                                 for item in FILTER.backups(backup_dir, "codex")))

            backups = list(Path(git(clone, "rev-parse", "--absolute-git-dir").stdout.strip(),
                                "agent-config-private").iterdir())
            self.assertTrue(backups)
            self.assertTrue(all(item.stat().st_mode & 0o777 == 0o600 for item in backups))

            # A hooks directory shared through global config is never written.
            shared = Path(directory, "shared-hooks")
            global_config = Path(directory, "gitconfig")
            global_config.write_text(f"[core]\n\thooksPath = {shared}\n")
            skipped = subprocess.run(
                ["bash", str(clone / "scripts/install-git-filters.sh")], capture_output=True,
                env={**isolated, "GIT_CONFIG_GLOBAL": str(global_config), "FILTER_PYTHON": sys.executable})
            self.assertEqual(skipped.returncode, 0)
            self.assertIn(b"core.hooksPath", skipped.stderr)
            self.assertFalse(shared.exists())

            config.write_text('model = "broken')
            self.assertNotEqual(git(clone, "add", config_path, check=False).returncode, 0)


if __name__ == "__main__":
    unittest.main()
