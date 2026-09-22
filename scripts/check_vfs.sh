#!/bin/sh
. "$(dirname -- "$0")/common.sh"
for vfs_kind in minimal several deep; do
    expect_status 1 ./run.sh --vfs "examples/vfs/$vfs_kind" \
        --prompt "$vfs_kind> " --script examples/stage3.txt
done
