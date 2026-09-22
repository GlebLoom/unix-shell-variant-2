#!/bin/sh
. "$(dirname -- "$0")/common.sh"
expect_status 0 ./run.sh --help
expect_status 0 ./run.sh
expect_status 1 ./run.sh --vfs examples/vfs/minimal --prompt 'stage2> ' \
    --script examples/stage2.txt
expect_status 1 ./run.sh --vfs examples/vfs/several --prompt '' \
    --script examples/stage2.txt
