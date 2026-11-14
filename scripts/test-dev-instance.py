#!/usr/bin/env python3
"""Exercise dispatch and reject invalid private configuration before executing Mise."""
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('dev-instance')


class Dispatch(unittest.TestCase):
    def test_dispatch_and_configuration_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / 'home'
            config = home / '.config/dev-instance/config.json'
            config.parent.mkdir(parents=True)
            checkout = root / 'checkout with spaces; $(false)'
            (checkout / 'scripts').mkdir(parents=True)
            (checkout / 'mise.toml').touch()
            (checkout / 'scripts/dev_instance_cli.py').touch()
            shim = root / 'mise'
            shim.write_text('#!/usr/bin/env bash\nprintf "%s\\0" "$@"\nprintf "diagnostic\\n" >&2\nexit 17\n')
            shim.chmod(0o700)
            jq = shutil.which('jq')
            self.assertIsNotNone(jq)
            jq_shim = root / 'jq'
            jq_log = root / 'jq.log'
            jq_shim.write_text(f'#!/usr/bin/env bash\nprintf called >> {shlex.quote(str(jq_log))}\n'
                               f'exec {shlex.quote(jq)} "$@"\n')
            jq_shim.chmod(0o700)
            env = dict(os.environ, HOME=str(home), DEV_INSTANCE_MISE=str(shim),
                       PATH=f'{root}:{os.environ["PATH"]}')
            env.pop('DEV_INSTANCE_JQ', None)

            def run():
                return subprocess.run(['bash', str(SCRIPT), 'create', 'a b', '$(false)', '--dry-run'],
                                      cwd=root, env=env, capture_output=True, timeout=5)

            invalid = [None, '{', '[]', '{}', '{"checkout":false}', '{"checkout":42}',
                       '{"checkout":"relative"}', '{"checkout":"/nonexistent"}',
                       json.dumps({'checkout': str(root)}),
                       json.dumps({'checkout': str(checkout)}) + '\n{}']
            for contents in invalid:
                with self.subTest(contents=contents):
                    if contents is not None:
                        config.write_text(contents)
                    result = run()
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(result.stdout, b'')
                    self.assertIn(b'dev-instance:', result.stderr)
            config.write_text(json.dumps({'checkout': str(checkout)}))
            result = run()
            self.assertEqual(result.returncode, 17)
            self.assertTrue(jq_log.exists())
            self.assertEqual(result.stdout.split(b'\0')[:-1],
                             [os.fsencode(x) for x in ['-C', str(checkout), 'run', 'dev-instance', '--',
                                                      'create', 'a b', '$(false)', '--dry-run']])
            self.assertIn(b'checkout revision unavailable', result.stderr)
            self.assertTrue(result.stderr.endswith(b'diagnostic\n'))

    def test_checkout_freshness_at_real_entry_point(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            home = root / 'home'
            config = home / '.config/dev-instance/config.json'
            config.parent.mkdir(parents=True)

            (home / '.gitconfig').write_text('[user]\nname = Test\nemail = test@example.invalid\n')

            def git(*args, cwd=root):
                return subprocess.check_output(
                    ['git', '-c', 'commit.gpgsign=false', '-c', 'user.name=Test',
                     '-c', 'user.email=test@example.invalid', *args],
                    cwd=cwd, stderr=subprocess.DEVNULL, timeout=5).decode().strip()

            origin = root / 'origin'
            git('init', '-b', 'main', str(origin))
            (origin / 'scripts').mkdir()
            (origin / 'mise.toml').touch()
            (origin / 'scripts/dev_instance_cli.py').touch()
            git('add', '.', cwd=origin)
            git('commit', '-m', 'test: initial fixture', cwd=origin)
            checkout = root / 'checkout'
            git('clone', str(origin), str(checkout))
            revision = git('rev-parse', 'HEAD', cwd=checkout)
            config.write_text(json.dumps({'checkout': str(checkout)}))
            shim = root / 'mise'
            shim.write_text('#!/usr/bin/env bash\nprintf \'{"ready":true}\\n\'\n')
            shim.chmod(0o700)
            env = dict(os.environ, HOME=str(home), DEV_INSTANCE_MISE=str(shim))
            env.pop('DEV_INSTANCE_JQ', None)

            def run(command='create'):
                result = subprocess.run(['bash', str(SCRIPT), command, 'fixture'],
                                        env=env, capture_output=True, timeout=5)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stdout, b'{"ready":true}\n')
                self.assertIn(revision.encode(), result.stderr)
                self.assertEqual(git('rev-parse', 'HEAD', cwd=checkout), revision)
                self.assertEqual(git('status', '--porcelain', cwd=checkout), '')
                return result.stderr

            self.assertNotIn(b'warning:', run())
            git('commit', '--allow-empty', '-m', 'test: upstream update', cwd=origin)
            self.assertNotIn(b'missing', run('destroy'))  # Cached ref is still current.
            self.assertIn(b'missing 1 commit(s)', run())
            self.assertIn(b'(cached)', run('list'))
            git('merge', '--ff-only', 'origin/main', cwd=checkout)
            revision = git('rev-parse', 'HEAD', cwd=checkout)
            self.assertNotIn(b'warning:', run())
            git('commit', '--allow-empty', '-m', 'test: local update', cwd=checkout)
            revision = git('rev-parse', 'HEAD', cwd=checkout)
            self.assertNotIn(b'warning:', run())  # Ahead is not stale.
            git('commit', '--allow-empty', '-m', 'test: divergent update', cwd=origin)
            self.assertIn(b'missing 1 commit(s)', run())

            timeout_shim = root / 'timeout'
            timeout_shim.write_text('#!/usr/bin/env bash\n'
                                    '[[ "$1" == --kill-after=0.2s && "$2" == 1.8s ]] || exit 99\n'
                                    'exit "${FIXTURE_TIMEOUT_EXIT:-124}"\n')
            timeout_shim.chmod(0o700)
            env['DEV_INSTANCE_TIMEOUT'] = str(timeout_shim)
            for code in ('124', '128'):
                env['FIXTURE_TIMEOUT_EXIT'] = code
                self.assertIn(b'freshness unverified (using cached ref)', run())
            git('remote', 'remove', 'origin', cwd=checkout)
            self.assertIn(b'origin/main unavailable', run())


if __name__ == '__main__':
    unittest.main()
