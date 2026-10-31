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

    def test_refresh_skips_files_without_a_stage_zero_entry(self):
        with tempfile.TemporaryDirectory(prefix="agent-refresh-test-") as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", directory], check=True)
            config = root / FILTER.FILES["codex"]
            config.parent.mkdir(parents=True)
            config.write_text("<<<<<<< HEAD\nmodel = 1\n=======\nmodel = 2\n>>>>>>> other\n")
            self.assertEqual(FILTER.refresh(root, [FILTER.FILES["codex"]]), [])

    def test_filter_backs_up_only_the_working_files_text(self):
        with tempfile.TemporaryDirectory(prefix="agent-filter-path-test-") as directory:
            subprocess.run(["git", "init", "-q", directory], check=True)
            config = Path(directory, "config.toml")
            config.write_text('model = "a"\n[projects."/now"]\nx = 1\n')
            historical = 'model = "a"\n[projects."/old"]\nx = 1\n'

            def run(text):
                return subprocess.run([sys.executable, str(SCRIPT), "codex", "config.toml"], cwd=directory,
                                      input=text, capture_output=True, text=True, check=True).stdout

            self.assertEqual(run(historical), FILTER.clean(historical, "codex"))
            backup_dir = Path(directory, ".git", "agent-config-private")
            self.assertFalse(backup_dir.exists())  # A historical blob is cleaned, not backed up.
            run(config.read_text())
            self.assertEqual([item.read_text() for item in FILTER.backups(backup_dir, "codex")],
                             [config.read_text()])

    def test_filter_kinds_match_gitattributes(self):
        attributes = SCRIPT.parents[1].joinpath(".gitattributes").read_text()
        for kind, relative in FILTER.FILES.items():
            self.assertIn(f"/{relative} filter=agent-{kind}", attributes)

    def test_toml_escapes_round_trip(self):
        data = {"projects": {"/x/\U0001F600 proj": {"note": "del\x7f tab\t"}}}
        self.assertEqual(tomllib.loads(FILTER.dump(data, "codex")), data)

    def test_filter_warns_when_a_reviewed_key_stays_local(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "codex"], capture_output=True, text=True,
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
            # Edits to a portable hook beside a private one are not unique private sections.
            mine = {"matcher": "", "hooks": [{"type": "command", "command": "/private/x.sh"}]}
            for timeout in range(FILTER.KEEP_BACKUPS + 5):
                shared = {"matcher": "", "hooks": [{"type": "command", "timeout": timeout,
                                                    "command": 'python3 "$HOME/.config/agent-hooks/a.py"'}]}
                data = {"hooks": {"Stop": [mine, shared]}}
                FILTER.back_up(json.dumps(data), "claude", data, FILTER.project(data, FILTER.CLAUDE),
                               directory)
            self.assertEqual(len(FILTER.backups(directory, "claude")), FILTER.KEEP_BACKUPS)
            # A clock that steps back still names the next backup after the newest.
            newest = FILTER.backups(directory, "codex")[-1]
            future = directory / f"codex.{int(newest.suffix[1:]) + 10**18}"
            newest.rename(future)
            save('model = "late"\n[projects."/one"]\nx = 1\n')
            self.assertIn("late", FILTER.backups(directory, "codex")[-1].read_text())

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
        # The private hook returns to its place after its backup neighbour.
        self.assertEqual(live, {"hooks": {"Stop": [mine, local, theirs]}})
        # The filtered content still matches what Git holds: no phantom deletion.
        self.assertEqual(FILTER.project(live, FILTER.CLAUDE), {"hooks": {"Stop": [mine, theirs]}})
        # A list that still holds a private item was not wiped: an edited one wins, unduplicated.
        edited = hook("/private/hook.sh --edited")
        live = {"hooks": {"Stop": [mine, edited]}}
        self.assertEqual(FILTER.add_missing(live, FILTER.private(backup, kept), FILTER.CLAUDE), [])
        # Upstream deleted the event with its only shared hook: only the private one returns.
        live = {}
        self.assertEqual(FILTER.add_missing(live, FILTER.private(backup, kept), FILTER.CLAUDE), ["hooks"])
        self.assertEqual(live, {"hooks": {"Stop": [local]}})
        # Empty sections hold nothing private, so they never count as private content.
        self.assertEqual(FILTER.private({"env": {}, "notify": [], "permissions": {"allow": []}}, {}), {})
        # A named entry is private even with an empty table, like an MCP server with defaults.
        self.assertEqual(FILTER.private({"mcp_servers": {"x": {}}}, {}), {"mcp_servers": {"x": {}}})
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

    def test_hook_items_are_canonical_and_empty_sections_count_as_wiped(self):
        # Claude writes hook entries with its own key order; Git's copy sorts them.
        item = {"matcher": "", "hooks": [{"type": "command", "timeout": 5,
                                          "command": 'python3 "$HOME/.config/agent-hooks/a.py"'}]}
        output = FILTER.clean(json.dumps({"hooks": {"Stop": [item]}}), "claude")
        self.assertEqual(output, FILTER.clean(json.dumps({"hooks": {"Stop": [item]}}, sort_keys=True),
                                              "claude"))
        self.assertLess(output.index('"command"'), output.index('"type"'))
        with tempfile.TemporaryDirectory(prefix="agent-restore-test-") as directory:
            target, saved = Path(directory, "settings.json"), Path(directory, "claude.1")
            saved.write_text(json.dumps({"extraKnownMarketplaces": {"m": {}}}))
            target.write_text(json.dumps({"permissions": {"allow": []}}))  # Nothing private.
            added, _ = FILTER.restore_file(target, saved, "claude", lambda: b"{}\n")
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
            # A private hook item only an older backup holds is named; a plain private list
            # that restore cannot merge is not.
            mine = {"matcher": "", "hooks": [{"type": "command", "command": "/private/hook"}]}
            hooked = backup(3, {**full, "hooks": {"Stop": [mine]}})
            broken = Path(directory, "claude.4")
            broken.write_text("{")  # An unreadable backup is skipped, not fatal.
            live = {"permissions": {"allow": ["Bash(b)"]}, "hooks": {"Stop": []},
                    "extraKnownMarketplaces": {"m": {}}, "apiKeyHelper": "/private/helper"}
            self.assertEqual(FILTER.unrestored([hooked, broken], live, "claude"),
                             [(hooked, ["hooks.Stop"])])

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
            # Keys between model and service_tier let a local pick and a pulled change merge.
            portable = '\nsandbox_mode = "x"\nservice_tier = "t1"'
            (origin / config_path).write_text(FILTER.clean('model = "one"' + portable, "codex"))
            git(origin, "add", ".")
            git(origin, "commit", "-qm", "test: base")

            git(directory, "clone", "-q", str(origin), str(clone))
            install(clone)
            config = clone / config_path
            config.write_text(config.read_text() + private)
            self.assertEqual(git(clone, "agent-status", "--porcelain", "--", "dotfiles").stdout, "")

            def publish(model):
                (origin / config_path).write_text(FILTER.clean(f'model = "{model}"' + portable, "codex"))
                git(origin, "commit", "-qam", f"test: {model}")

            def assert_restored(model, projects=("/private/one", "/private/two")):
                data = tomllib.loads(config.read_text())
                self.assertEqual((data["model"], data.get("projects")),
                                 (model, {name: trusted for name in projects}))

            publish("two")
            git(clone, "pull", "-q", "--no-rebase")
            assert_restored("two")

            # The local commit touches the config, so a restore before its pick would make
            # the rebase refuse; post-rewrite restores once the pick is done.
            config.write_text(config.read_text().replace('"t1"', '"t2"'))
            git(clone, "commit", "-qam", "test: local tier")
            publish("three")
            git(clone, "pull", "-q", "--rebase")
            assert_restored("three")
            self.assertIn('"t2"', config.read_text())

            # When only the local commit touches the config, the rebase still rewrites the file
            # (onto checkout, then the pick), though the result matches ORIG_HEAD.
            git(clone, "agent-status", "--porcelain")
            config.write_text(config.read_text().replace('"t2"', '"t3"'))
            git(clone, "commit", "-qam", "test: local tier again")
            (origin / "other").write_text("upstream\n")
            git(origin, "add", "other")
            git(origin, "commit", "-qm", "test: unrelated")
            git(clone, "pull", "-q", "--rebase")
            assert_restored("three")
            self.assertIn('"t3"', config.read_text())

            # A rebase that rewrites no commits fires no post-rewrite; post-checkout restores.
            git(clone, "fetch", "-q", "origin")
            git(clone, "checkout", "-q", "-b", "fresh", "FETCH_HEAD")
            publish("four")
            git(clone, "fetch", "-q", "origin")
            git(clone, "rebase", "-q", "FETCH_HEAD")
            assert_restored("four")
            # Rebase rewrites the index after its hooks, so refresh before the next checkout.
            git(clone, "agent-status", "--porcelain")
            git(clone, "checkout", "-q", "-")
            assert_restored("three")

            # Hooks leave a file with private content alone, so a deletion sticks even when
            # no clean ran since the latest backup.
            # A staged change makes the index differ from HEAD although Git rewrote nothing;
            # the hook then only hints instead of merging the deleted key back.
            data = tomllib.loads(config.read_text())
            data["model"] = "staged"
            config.write_text(FILTER.dump(data, "codex"))
            git(clone, "add", config_path)
            del data["projects"]["/private/two"]
            config.write_text(FILTER.dump(data, "codex"))
            switched = git(clone, "checkout", "-q", "-b", "side")
            self.assertIn("already holds private keys", switched.stderr)
            git(clone, "reset", "-q", "--", config_path)
            data["model"] = "three"
            config.write_text(FILTER.dump(data, "codex"))
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

            # Deleting the last private key survives an amend and a branch switch, which
            # leave the file alone; only the agent-status catch-all brings it back.
            config.write_text(FILTER.clean(config.read_text(), "codex"))
            git(clone, "commit", "-q", "--amend", "--no-edit", "--allow-empty")
            git(clone, "checkout", "-q", "-b", "after-amend")
            self.assertNotIn("projects", config.read_text())

            # A squash merge rewrites the file without moving HEAD; the hook still restores.
            git(clone, "checkout", "-q", "-b", "squashed")
            config.write_text(FILTER.clean('model = "squashed"', "codex"))
            git(clone, "commit", "-qam", "test: squashed")
            git(clone, "checkout", "-q", "after-amend")
            config.write_text(FILTER.clean(config.read_text(), "codex"))
            git(clone, "agent-status", "--porcelain")  # Restores; a stale index blocks merges.
            git(clone, "merge", "-q", "--squash", "squashed")
            assert_restored("squashed", ["/private/one"])

            # Forget purges every backup of the removed key, so nothing brings it back.
            config.write_text(FILTER.clean(config.read_text(), "codex"))
            self.assertIn("--forget codex", git(clone, "agent-status", "--porcelain").stderr)
            config.write_text(FILTER.clean(config.read_text(), "codex"))
            # A linked worktree with its own private keys, wiped (mid-stash, say) when the
            # first forget runs, keeps its backups; once restored, it keeps one current backup.
            linked = Path(directory, "linked")
            git(clone, "worktree", "add", "-q", "-b", "linked", str(linked))
            # The scripts are untracked in this fixture, so the new worktree needs its own copy.
            shutil.copytree(clone / "scripts", linked / "scripts")
            linked_config = linked / config_path
            linked_private = '[projects."/linked"]\ntrust_level = "trusted"\n'
            linked_config.write_text(linked_config.read_text() + linked_private)
            git(linked, "agent-status", "--porcelain")
            linked_dir = Path(git(linked, "rev-parse", "--absolute-git-dir").stdout.strip(),
                              "agent-config-private")
            linked_config.write_text(FILTER.clean(linked_config.read_text(), "codex"))
            notice = git(clone, "agent-restore", "--forget", "codex").stderr
            self.assertRegex(notice, r"kept the backups of \S*linked,")
            linked_config.unlink()  # A missing file counts as wiped too.
            notice = git(clone, "agent-restore", "--forget", "codex").stderr
            self.assertRegex(notice, r"kept the backups of \S*linked,")
            git(linked, "checkout", "-q", "--", config_path)
            self.assertTrue(any("/linked" in item.read_text()
                                for item in FILTER.backups(linked_dir, "codex")))
            git(clone, "agent-status", "--porcelain")
            self.assertNotIn("projects", config.read_text())
            self.assertFalse(any("private" in item.read_text()
                                 for item in FILTER.backups(backup_dir, "codex")))
            self.assertIn("/linked", linked_config.read_text())  # Restored by the file checkout.
            leftover = linked_config.parent / f".{linked_config.name}.abc.agent-restore-tmp"
            leftover.write_text(linked_private)  # A killed restore's temp copy.
            git(clone, "agent-restore", "--forget", "codex")
            self.assertFalse(leftover.exists())
            self.assertEqual([item.read_text() for item in FILTER.backups(linked_dir, "codex")],
                             [linked_config.read_text()])

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
            # Nor a repository-local one inside the worktree, where the hooks could be committed.
            git(clone, "config", "core.hooksPath", ".githooks")
            skipped = subprocess.run(["bash", str(clone / "scripts/install-git-filters.sh")],
                                     capture_output=True, env={**isolated, "FILTER_PYTHON": sys.executable})
            self.assertIn(b"inside this worktree", skipped.stderr)
            self.assertFalse((clone / ".githooks").exists())

            config.write_text('model = "broken')
            self.assertNotEqual(git(clone, "add", config_path, check=False).returncode, 0)


if __name__ == "__main__":
    unittest.main()
