#!/bin/sh
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_dir"
for vfs_kind in minimal several deep; do
    ./run.sh --vfs "examples/vfs/$vfs_kind" --prompt "$vfs_kind> " \
        --script examples/stage3.txt </dev/null && exit 1
done
exit 0
