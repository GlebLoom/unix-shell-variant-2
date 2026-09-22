#!/bin/sh
. "$(dirname -- "$0")/common.sh"
for vfs_kind in minimal several deep; do
    expect_status 1 ./run.sh --vfs "examples/vfs/$vfs_kind" \
        --prompt "$vfs_kind> " --script examples/stage3.txt
done
expect_status 1 ./run.sh --vfs /nonexistent/vfs --prompt 'error> ' \
    --script examples/stage3.txt
expect_status 1 ./run.sh --vfs examples/vfs/minimal/hello.txt \
    --prompt 'error> ' --script examples/stage3.txt
