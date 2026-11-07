#!/usr/bin/env python3
"""Fresh noninteractive zsh, real Mise and temporary project/venv fixtures; no installs."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MISE = shutil.which("mise")


class ShellTests(unittest.TestCase):
    def test_missing_selected_runtime_cannot_fall_back_to_system_python(self):
        with tempfile.TemporaryDirectory(prefix="agent-mise-missing-") as tmp:
            (Path(tmp) / "mise.toml").write_text('[tools]\npython = "3.1.999"\n')
            env = dict(os.environ, MISE_TRUSTED_CONFIG_PATHS=tmp, MISE_AUTO_INSTALL="0")
            payload = {"cwd": tmp, "tool_input": {"cmd": "/usr/bin/python3 --version"}}
            result = subprocess.run([sys.executable, str(ROOT / "dotfiles/hooks/mise-tool-guard.py")],
                                    input=json.dumps(payload), capture_output=True, text=True,
                                    env=env, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            decision = json.loads(result.stdout)["hookSpecificOutput"]
            self.assertEqual(decision["permissionDecision"], "deny")
            self.assertIn("not installed", decision["permissionDecisionReason"])

    def test_validator_reports_missing_dependency_without_running_validator(self):
        import shlex
        python = subprocess.check_output([MISE, "which", "python"], text=True).strip()
        with tempfile.TemporaryDirectory(prefix="agent-validator-") as tmp:
            base = Path(tmp)
            isolated = base / "python"
            isolated.write_text('#!/bin/sh\nexec ' + shlex.quote(python) + ' -S "$@"\n')
            isolated.chmod(0o755)
            fake_mise = base / "mise"
            fake_mise.write_text('#!/bin/sh\nprintf "%s\\n" ' + shlex.quote(str(isolated)) + '\n')
            fake_mise.chmod(0o755)
            validator = base / "validator.py"
            validator.write_text('raise RuntimeError("must not run")\n')
            result = subprocess.run([str(ROOT / "scripts/validate-agent-skill"), tmp, str(validator)],
                                    env=dict(os.environ, PATH=str(base) + ":/usr/bin:/bin"),
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 2)
            self.assertIn("PyYAML is missing", result.stderr)
            self.assertNotIn("must not run", result.stderr)

    def test_startup_directory_change_and_external_venv(self):
        python = subprocess.check_output([MISE, "which", "python"], text=True).strip()
        with tempfile.TemporaryDirectory(prefix="agent-mise-shell-") as tmp:
            base = Path(tmp)
            startup, project, venv = (base / name for name in ("startup", "project", "venv"))
            startup.mkdir()
            project.mkdir()
            subprocess.run([python, "-m", "venv", "--without-pip", str(venv)], check=True, timeout=15)
            (project / "mise.toml").write_text('[env]\n_.python.venv = ' + json.dumps(str(venv)) + '\n')
            (startup / ".zshenv").write_text(
                'source "' + str(ROOT / "dotfiles/shell/agent-mise.zsh") + '" "' + MISE + '"\n')
            env = dict(os.environ, ZDOTDIR=str(startup), MISE_TRUSTED_CONFIG_PATHS=str(base),
                       PATH="/usr/bin:/bin:" + str(Path(MISE).parent))
            env.pop("VIRTUAL_ENV", None)
            # Fresh root and child shells; cd must update project selection without a prompt.
            command = '''python -c 'import sys; print(sys.executable)'
cd "$1"
python -c 'import sys; print(sys.executable)'
zsh -c "python -c 'import sys; print(sys.executable)'"
cd "$2"
python -c 'import sys; print(sys.executable)'
'''
            result = subprocess.run(["/bin/zsh", "-c", command, "test", str(project), str(base)],
                                    cwd=base, env=env, capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            paths = result.stdout.splitlines()
            self.assertEqual(len(paths), 4, result.stdout)
            self.assertEqual(Path(paths[0]).resolve(), Path(python).resolve())
            self.assertEqual(paths[1:3], [str(venv / "bin/python")] * 2)
            self.assertEqual(Path(paths[3]).resolve(), Path(python).resolve())
            env.update(VIRTUAL_ENV=str(venv), PATH=str(venv / "bin") + ":" + env["PATH"])
            result = subprocess.run(["/bin/zsh", "-c", "command -v python"], cwd=base, env=env,
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.strip(), str(venv / "bin/python"))


if __name__ == "__main__":
    unittest.main()
