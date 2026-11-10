#!/bin/zsh
# setup.sh DIR -> creates the fixture checkout, a Git repository with one commit, at DIR.
set -e
dir=${1:?usage: setup.sh DIR}
[[ -e $dir ]] && { echo "$dir already exists" >&2; exit 2; }
mkdir -p $dir
cp -R ${0:A:h}/fixture/. $dir/
git -C $dir init -q
git -C $dir add -A
git -C $dir -c user.name=eval -c user.email=eval@example.invalid commit -qm "chore: add fixture"
