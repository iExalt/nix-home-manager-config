#!/usr/bin/env python3
"""Remove inspected, task-owned scratch directories inside the two approved roots."""
import os
import pwd
from pathlib import Path
import shutil
import subprocess
import sys


def validate(arguments, home):
    roots = [(home / suffix).resolve() for suffix in ('.paseo/worktrees', '.virtualenvs')]
    targets = []
    for argument in arguments:
        raw = Path(argument).expanduser()
        if not argument or not raw.is_absolute() or '..' in raw.parts:
            raise ValueError(f'expected an absolute path without ..: {argument!r}')
        target = raw.resolve(strict=True)
        root = next((root for root in roots if root in target.parents), None)
        if root is None:
            raise ValueError(f'not a child of an approved scratch root: {argument}')
        # Reject even in-root symlinks, so the inspected name is the deleted directory.
        if any(part.is_symlink() for part in (raw, *raw.parents)):
            raise ValueError(f'symlink in target path: {argument}')
        if not target.is_dir():
            raise ValueError(f'not a directory: {argument}')
        if any(target == old or target in old.parents or old in target.parents for old in targets):
            raise ValueError(f'duplicate or overlapping target: {argument}')
        targets.append(target)
    return targets


def git(arguments):
    # Caller Git overrides must not redirect discovery or removal to another repository.
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    return subprocess.run([os.environ.get('SCRATCH_RM_GIT', 'git'), *arguments], env=env, capture_output=True, check=True,
                          timeout=30)


def worktree_repository(target):
    def scan_error(error):
        raise error

    for directory, children, files in os.walk(target, followlinks=False, onerror=scan_error):
        if '.git' in children or '.git' in files:
            if Path(directory) != target:
                raise ValueError(f'nested repository must be removed separately: {directory}')
            if '.git' in children:
                children.remove('.git')
    if not (target / '.git').exists():
        return None
    common = os.fsdecode(git(['-C', str(target), 'rev-parse', '--path-format=absolute',
                             '--git-common-dir']).stdout).strip()
    entries = git(['--git-dir', common, 'worktree', 'list', '--porcelain', '-z']).stdout
    worktrees = [Path(os.fsdecode(field[len(b'worktree '):])).resolve()
                 for field in entries.split(b'\0') if field.startswith(b'worktree ')]
    if target not in worktrees:
        raise ValueError(f'Git metadata does not list the target worktree: {target}')
    return common


def main(arguments):
    if not arguments:
        print('Usage: scratch-rm ABSOLUTE_DIRECTORY [...]', file=sys.stderr)
        return 2
    try:
        targets = validate(arguments, Path(pwd.getpwuid(os.getuid()).pw_dir))
        # Complete Git discovery before deleting any operand as well.
        repositories = [worktree_repository(target) for target in targets]
        for target, repository in zip(targets, repositories):
            if repository is not None:
                # Never fall back after a Git refusal: dirty or locked worktrees stay intact.
                git(['--git-dir', repository, 'worktree', 'remove', str(target)])
            else:
                shutil.rmtree(target)
            print(f'Removed {target}')
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'scratch-rm: {error}', file=sys.stderr)
        if isinstance(error, subprocess.CalledProcessError):
            print(os.fsdecode(error.stderr).strip(), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
