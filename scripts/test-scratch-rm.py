#!/usr/bin/env python3
"""Prove containment, all-operand validation, and Git's dirty-worktree protection."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

SCRIPT = Path(__file__).with_name('scratch-rm.py')
spec = importlib.util.spec_from_file_location('scratch_rm', SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PermissionActivation(unittest.TestCase):
    def test_only_reviewed_rule_is_appended_and_private_rules_survive(self):
        specification = importlib.util.spec_from_file_location('allow_scratch', SCRIPT.with_name('allow-scratch-rm.py'))
        activation = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(activation)
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / 'settings.json'
            for rules in (None, [], ['Bash(scratch-rm *)'], ['Bash(ssh private-host)']):
                data = {'other': True}
                if rules is not None:
                    data['permissions'] = {'allow': rules.copy()}
                target.write_text(json.dumps(data))
                target.chmod(0o600)
                activation.install(target)
                result = json.loads(target.read_text())
                self.assertEqual(result['permissions']['allow'], list(dict.fromkeys((rules or []) + ['Bash(scratch-rm *)'])))
                self.assertTrue(result['other'])
                self.assertEqual(target.stat().st_mode & 0o777, 0o600)
                before = target.read_bytes()
                activation.install(target)
                self.assertEqual(target.read_bytes(), before)
            for invalid in ('bad', 12, {}):
                target.write_text(json.dumps({'permissions': {'allow': invalid}}))
                before = target.read_bytes()
                with self.assertRaises(ValueError):
                    activation.install(target)
                self.assertEqual(target.read_bytes(), before)


class ScratchRemoval(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name).resolve()
        self.roots = [self.home / '.paseo/worktrees', self.home / '.virtualenvs']
        for root in self.roots:
            root.mkdir(parents=True)
        self.outside = self.home / 'outside'
        self.outside.mkdir()

    def run_helper(self, *arguments):
        with patch.object(module.pwd, 'getpwuid', return_value=SimpleNamespace(pw_dir=str(self.home))):
            return module.main([str(arg) for arg in arguments])

    def test_allowed_nested_and_batched_targets(self):
        targets = [root / 'task' / 'nested' for root in self.roots]
        for target in targets:
            target.mkdir(parents=True)
            (target / 'receipt').touch()
        self.assertEqual(self.run_helper(*targets), 0)
        self.assertTrue(all(not target.exists() for target in targets))
        self.assertTrue(all(root.is_dir() for root in self.roots))

    def test_invalid_targets_never_partially_delete(self):
        good = self.roots[0] / 'keep'
        good.mkdir()
        link = self.roots[0] / 'link'
        link.symlink_to(self.outside, target_is_directory=True)
        inside_link = self.roots[0] / 'inside-link'
        inside_link.symlink_to(good, target_is_directory=True)
        sibling = self.home / '.paseo/worktrees-other'
        sibling.mkdir()
        cases = [*self.roots, self.outside, sibling, link, inside_link,
                 link / 'nested', self.roots[0] / '..' / 'worktrees', good,
                 good.parent, '', 'relative', good / 'missing']
        for bad in cases:
            with self.subTest(target=bad):
                self.assertNotEqual(self.run_helper(good, bad), 0)
                self.assertTrue(good.is_dir())
                self.assertTrue(self.outside.is_dir())
        (good / 'file').touch()
        self.assertNotEqual(self.run_helper(good / 'file'), 0)
        self.assertNotEqual(self.run_helper(), 0)

    def git(self, *arguments):
        return subprocess.run(['git', *arguments], check=True, capture_output=True,
                              env={k: v for k, v in os.environ.items() if not k.startswith('GIT_')},
                              timeout=10)

    def test_home_environment_cannot_change_approved_roots(self):
        fake = self.outside / '.virtualenvs' / 'keep'
        fake.mkdir(parents=True)
        with patch.dict(os.environ, HOME=str(self.outside)):
            self.assertNotEqual(self.run_helper(fake), 0)
            self.assertTrue(fake.exists())

    def test_registered_clean_and_dirty_worktrees(self):
        repository = self.home / 'repo'
        self.git('init', str(repository))
        self.git('-C', str(repository), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                 '-c', 'commit.gpgsign=false', 'commit', '--allow-empty', '-m', 'test')
        clean, dirty = [self.roots[0] / name for name in ('clean', 'dirty')]
        for target in (clean, dirty):
            self.git('-C', str(repository), 'worktree', 'add', '-b', target.name, str(target))
        (dirty / 'untracked').touch()
        self.assertNotEqual(self.run_helper(dirty), 0)
        self.assertTrue((dirty / 'untracked').exists())
        self.assertEqual(self.run_helper(clean), 0)
        self.assertFalse(clean.exists())
        listed = self.git('-C', str(repository), 'worktree', 'list', '--porcelain').stdout.decode()
        self.assertNotIn(str(clean), listed)
        self.assertIn(str(dirty), listed)
        self.assertIn('clean', self.git('-C', str(repository), 'branch', '--list').stdout.decode())
        self.assertNotEqual(self.run_helper(self.roots[0]), 0)
        container = self.roots[1] / 'container'
        container.mkdir()
        nested = container / 'nested'
        self.git('-C', str(repository), 'worktree', 'add', '-b', 'nested', str(nested))
        (nested / 'untracked').touch()
        self.assertNotEqual(self.run_helper(container), 0)
        self.assertTrue((nested / 'untracked').exists())
        main = self.roots[1] / 'main'
        self.git('init', str(main))
        self.git('-C', str(main), '-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                 '-c', 'commit.gpgsign=false', 'commit', '--allow-empty', '-m', 'test')
        self.assertNotEqual(self.run_helper(main), 0)
        self.assertTrue((main / '.git').is_dir())



if __name__ == '__main__':
    unittest.main()
