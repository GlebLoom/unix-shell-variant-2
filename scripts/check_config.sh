#!/bin/sh
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_dir"
./run.sh --help
./run.sh --vfs . --prompt 'stage2> ' \
    --script examples/stage2.txt </dev/null && exit 1
./run.sh --vfs . --prompt '' \
    --script examples/stage2.txt </dev/null && exit 1
exit 0
