#!/bin/sh
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_dir"
for vfs_kind in minimal several deep; do
    ./run.sh --vfs "examples/vfs/$vfs_kind" --prompt "$vfs_kind> " \
        --script examples/stage3.txt </dev/null && exit 1
done
./run.sh --vfs /nonexistent/vfs --prompt 'error> ' \
    --script examples/stage3.txt </dev/null && exit 1
./run.sh --vfs examples/vfs/minimal/hello.txt --prompt 'error> ' \
    --script examples/stage3.txt </dev/null && exit 1
exit 0
