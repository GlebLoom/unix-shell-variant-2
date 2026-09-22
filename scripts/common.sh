#!/bin/sh
# Shared setup for the host verification scripts.
set -eu
project_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$project_dir"

expect_status() {
    expected_status=$1
    shift
    actual_status=0
    "$@" </dev/null || actual_status=$?
    if [ "$actual_status" -ne "$expected_status" ]; then
        echo "Expected exit $expected_status, got $actual_status: $*" >&2
        exit 1
    fi
}
