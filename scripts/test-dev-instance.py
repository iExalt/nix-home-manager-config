#!/usr/bin/env python3
"""Exercise dispatch and reject invalid private configuration before executing Mise."""
import json
import os
from pathlib import Path
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
            env = dict(os.environ, HOME=str(home), DEV_INSTANCE_MISE=str(shim),
                       DEV_INSTANCE_JQ=shutil.which('jq'))

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
            self.assertEqual(result.stdout.split(b'\0')[:-1],
                             [os.fsencode(x) for x in ['-C', str(checkout), 'run', 'dev-instance', '--',
                                                      'create', 'a b', '$(false)', '--dry-run']])
            self.assertEqual(result.stderr, b'diagnostic\n')


if __name__ == '__main__':
    unittest.main()
