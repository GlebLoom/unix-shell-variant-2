#!/bin/sh
. "$(dirname -- "$0")/common.sh"
expect_status 1 ./run.sh --vfs examples/vfs/minimal --prompt 'errors> ' \
    --script /nonexistent/start.txt
expect_status 2 ./run.sh --vfs examples/vfs/minimal --prompt 'errors> ' \
    --script examples/stage2.txt --unknown
expect_status 2 ./run.sh --vfs examples/vfs/minimal --prompt 'errors> ' \
    --script
