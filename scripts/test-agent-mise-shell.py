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

import yaml

ROOT = Path(__file__).resolve().parents[1]
MISE = shutil.which("mise")


class ShellTests(unittest.TestCase):
    def test_validator_with_mise_absent_from_path_uses_bootstrap_and_project_python(self):
        with tempfile.TemporaryDirectory(prefix="agent-validator-bootstrap-") as tmp:
            base = Path(tmp)
            python = subprocess.check_output([MISE, "which", "python"], text=True).strip()
            (base / "mise.toml").write_text(
                '[tools]\npython = "path:' + str(base) + '"\n'
                '[env]\nPYTHONPATH = ' + json.dumps(str(Path(yaml.__file__).parent.parent)) + '\n')
            (base / "bin").mkdir()
            (base / "bin/python").symlink_to(python)
            validator = base / "validator.py"
            validator.write_text('import sys; print(sys.executable); print(sys.argv[1])\n')
            env = dict(os.environ, PATH="/usr/bin:/bin", AGENT_MISE_BIN=MISE,
                       MISE_TRUSTED_CONFIG_PATHS=tmp, MISE_AUTO_INSTALL="0")
            env.pop("VIRTUAL_ENV", None)
            result = subprocess.run(
                ["/bin/bash", str(ROOT / "scripts/validate-agent-skill"), tmp, str(validator)],
                cwd=tmp, env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout.splitlines(), [str(base / "bin/python"), tmp])

    def test_validator_distinguishes_missing_mise_from_missing_python(self):
        result = subprocess.run(
            ["/bin/bash", str(ROOT / "scripts/validate-agent-skill"), str(ROOT), __file__],
            env=dict(os.environ, AGENT_MISE_BIN="/nonexistent/agent-test-mise"),
            capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertIn("Mise is unavailable", result.stderr)
        self.assertNotIn("mise install python", result.stderr)

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
            fake_mise.write_text(
                '#!/bin/sh\ncase "$1" in\n'
                'which) printf "%s\\n" ' + shlex.quote(str(isolated)) + ' ;;\n'
                'exec) shift 4; exec ' + shlex.quote(str(isolated)) + ' "$@" ;;\n'
                '*) exit 2 ;;\nesac\n')
            fake_mise.chmod(0o755)
            validator = base / "validator.py"
            validator.write_text('raise RuntimeError("must not run")\n')
            result = subprocess.run([str(ROOT / "scripts/validate-agent-skill"), tmp, str(validator)],
                                    env=dict(os.environ, PATH=str(base) + ":/usr/bin:/bin"),
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 2)
            self.assertIn("PyYAML is missing", result.stderr)
            self.assertNotIn("must not run", result.stderr)

    def test_validator_uses_declared_venv_and_matching_active_environment(self):
        python = subprocess.check_output([MISE, "which", "python"], text=True).strip()
        with tempfile.TemporaryDirectory(prefix="agent-validator-env-") as tmp:
            base = Path(tmp)
            runtime = base / "runtime"
            subprocess.run([python, "-m", "venv", "--without-pip", str(runtime)], check=True, timeout=15)
            python = str(runtime / "bin/python")
            venv = base / "venv"
            subprocess.run([python, "-m", "venv", "--without-pip", str(venv)], check=True, timeout=15)
            site = subprocess.check_output(
                [str(venv / "bin/python"), "-c", "import sysconfig; print(sysconfig.get_path('purelib'))"],
                text=True).strip()
            shutil.copytree(Path(yaml.__file__).parent, Path(site) / "yaml")
            # The base runtime cannot import yaml; only the declared environment can.
            self.assertNotEqual(subprocess.run(
                [python, "-c", "import yaml"], env=dict(os.environ, PYTHONPATH=""),
                capture_output=True).returncode, 0)
            project = base / "project"
            project.mkdir()
            config = ('[tools]\npython = "path:' + str(Path(python).parent.parent) + '"\n'
                      'node = "0.0.999"\n')
            validator = base / "validator.py"
            validator.write_text('import sys, yaml; print(sys.executable); print(sys.argv[1])\n')
            env = dict(os.environ, AGENT_MISE_BIN=MISE, MISE_TRUSTED_CONFIG_PATHS=tmp,
                       MISE_AUTO_INSTALL="0", PYTHONPATH="", PATH="/usr/bin:/bin")
            for mode in ("declared", "active", "mismatched"):
                with self.subTest(mode=mode):
                    current = env.copy()
                    declaration = '[env]\n_.python.venv = ' + json.dumps(str(venv)) + '\n'
                    if mode == "active":
                        current["VIRTUAL_ENV"] = str(venv)
                        declaration = ""
                    elif mode == "mismatched":
                        other = base / "other" / "bin"
                        other.mkdir(parents=True)
                        fake = other / "python"
                        fake.write_text('#!/bin/sh\nprintf "/different/runtime\\n"\n')
                        fake.chmod(0o755)
                        current["VIRTUAL_ENV"] = str(other.parent)
                    else:
                        current.pop("VIRTUAL_ENV", None)
                    (project / "mise.toml").write_text(config + declaration)
                    result = subprocess.run(
                        ["/bin/bash", str(ROOT / "scripts/validate-agent-skill"), tmp, str(validator)],
                        cwd=project, env=current, capture_output=True, text=True, timeout=15)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout.splitlines(), [str(venv / "bin/python"), tmp])

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
