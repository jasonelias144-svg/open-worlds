#!/bin/sh
# Ours, not DeepSeek's (see ../README.md). Builds each of the five
# deliveries that record 012-09-05 ends with, exactly as DeepSeek gave
# it, in a scratch folder, and runs its tests. Nothing here is changed.
# Run it from anywhere:
#   sh sketches/deepseek/012-09-05/review/steps.sh
#
# It runs DeepSeek's code as written, so run it where that is safe. It
# needs Rust and the network, as run.sh does, and CI doesn't run it.
# The sketch has no Cargo.lock, so a result can change with what
# crates.io serves that day.
#
# What it must find (2026-11-16):
#   delivery 1    22 tests pass
#   delivery 2    20 pass, 2 fail
#   delivery 3    27 pass, 2 fail
#   delivery 4    31 pass, 2 fail
#   delivery 5    does not compile
#   5-aside       39 pass, 2 fail (two faults set aside, not repaired)
# The two that fail are the same from delivery 2 on:
# home_port_verifies and home_bookmark_and_presence_verify.
set -eu
here=$(cd "$(dirname "$0")/.." && pwd)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
python3 "$here/review/steps.py" --aside "$scratch"
status=0
check() {
    # check DELIVERY WHAT-THE-TESTS-MUST-SAY
    echo "== delivery $1"
    ( cd "$scratch/$1/chat-world" && cargo test --test integration ) \
        > "$scratch/$1.out" 2>&1 || true
    # Each delivery is built on its own, and its build is not kept:
    # six of them side by side take a few gigabytes.
    rm -rf "$scratch/$1/chat-world/target"
    grep -E '^test result|FAILED$|could not compile' "$scratch/$1.out" || true
    if grep -q "$2" "$scratch/$1.out"; then
        echo "   as recorded"
    else
        echo "   NOT as recorded: wanted \"$2\""
        status=1
    fi
}
check 1 '^test result: ok. 22 passed; 0 failed'
check 2 '^test result: FAILED. 20 passed; 2 failed'
check 3 '^test result: FAILED. 27 passed; 2 failed'
check 4 '^test result: FAILED. 31 passed; 2 failed'
check 5 'could not compile `chat-world`'
check 5-aside '^test result: FAILED. 39 passed; 2 failed'
exit $status
