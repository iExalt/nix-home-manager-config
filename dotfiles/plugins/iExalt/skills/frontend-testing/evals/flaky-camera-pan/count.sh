#!/bin/zsh
# count.sh DIR N [DETAILS_DELAY_MS] -> fail=k/N. Keeps each failing run's output in DIR/.runs/.
dir=$1; n=$2; [[ -n $3 ]] && export DETAILS_DELAY_MS=$3
mkdir -p $dir/.runs; f=0
for i in $(seq $n); do
  if ! (cd $dir && mise exec -- uv run -q --with playwright --with pytest pytest -q -x -p no:cacheprovider test_select.py > .runs/run-$i.log 2>&1); then
    f=$((f+1))
  else
    rm -f $dir/.runs/run-$i.log
  fi
done
echo "fail=$f/$n delay=${DETAILS_DELAY_MS:-default}"
