#!/bin/sh
. "$(dirname -- "$0")/common.sh"
"${PYTHON:-python3}" -m unittest discover -s tests -v
./scripts/check_config.sh
./scripts/check_config_errors.sh
./scripts/check_vfs.sh
./scripts/check_vfs_errors.sh
for stage in 4 5; do
    expect_status 1 ./run.sh --vfs examples/vfs/deep --prompt 'check> ' \
        --script "examples/stage$stage.txt"
done
expect_status 0 ./run.sh --vfs examples/vfs/deep --prompt 'demo> ' \
    --script examples/demo.txt
echo 'All checks passed.'
