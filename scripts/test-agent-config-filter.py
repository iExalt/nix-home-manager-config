#!/usr/bin/env python3
"""Exercise privacy projection and Git's actual clean-filter behavior."""

import importlib.util
import json
from pathlib import Path
import shlex
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

    def test_git_clean_status_private_edits_and_required_failure(self):
        with tempfile.TemporaryDirectory(prefix="agent-filter-test-") as directory:
            root = Path(directory)

            def git(*args, check=True):
                return subprocess.run(["git", "-C", directory, *args], check=check,
                                      capture_output=True, text=True)

            git("init", "-q")
            git("config", "filter.test.clean", shlex.join([sys.executable, str(SCRIPT), "codex"]))
            git("config", "filter.test.required", "true")
            (root / ".gitattributes").write_text("dotfiles/.codex/config.toml filter=test\n")
            config = root / "dotfiles/.codex/config.toml"
            config.parent.mkdir(parents=True)
            helper = SCRIPT.with_name("agent-status.sh")
            git("config", "alias.agent-status", "!" + shlex.join(["bash", str(helper)]))
            original = 'model = "example"\n[projects."/private/one"]\ntrust_level = "trusted"\n'
            config.write_text(original)
            git("add", ".")
            git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                "-c", "commit.gpgsign=false", "commit", "-qm", "test: filter")
            self.assertEqual(config.read_text(), original)
            config.write_text(original.replace("/private/one", "/private/two-longer"))
            self.assertEqual(git("diff", "--no-ext-diff").stdout, "")
            self.assertEqual(git("agent-status", "--porcelain").stdout, "")
            self.assertEqual(git("status", "--porcelain").stdout, "")
            self.assertNotIn("private", git("show", "HEAD:dotfiles/.codex/config.toml").stdout)
            config.write_text(original.replace('"example"', '"different"'))
            self.assertIn("dotfiles/.codex/config.toml", git("agent-status", "--porcelain").stdout)
            self.assertEqual(git("diff", "--cached", "--no-ext-diff").stdout, "")
            config.write_text('model = "broken')
            self.assertNotEqual(git("add", "dotfiles/.codex/config.toml", check=False).returncode, 0)


if __name__ == "__main__":
    unittest.main()
