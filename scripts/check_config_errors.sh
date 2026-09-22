#!/bin/sh
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_dir"
./run.sh --vfs . --prompt 'errors> ' \
    --script /nonexistent/start.txt </dev/null && exit 1
./run.sh --vfs . --prompt 'errors> ' \
    --script examples/stage2.txt --unknown </dev/null && exit 1
./run.sh --vfs . --prompt 'errors> ' \
    --script </dev/null && exit 1
exit 0
