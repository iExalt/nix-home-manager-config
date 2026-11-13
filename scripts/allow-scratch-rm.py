#!/usr/bin/env python3
"""Install the reviewed allow rule without exporting other local permissions."""
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile


def install(target):
    settings = json.loads(target.read_text())
    permissions = settings.setdefault('permissions', {})
    rules = permissions.setdefault('allow', [])
    if not isinstance(rules, list) or not all(isinstance(rule, str) for rule in rules):
        raise ValueError('permissions.allow must be a list of strings')
    rule = 'Bash(scratch-rm *)'
    if rule in rules:
        return
    rules.append(rule)
    descriptor, temporary = tempfile.mkstemp(dir=target.parent, prefix='.scratch-rm-settings-')
    try:
        with os.fdopen(descriptor, 'w') as handle:
            json.dump(settings, handle, indent=2)
            handle.write('\n')
        shutil.copymode(target, temporary)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


if __name__ == '__main__':
    install(Path(sys.argv[1]))
