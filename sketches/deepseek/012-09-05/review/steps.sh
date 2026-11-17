#!/bin/sh
# Ours, not DeepSeek's (see ../README.md). Builds each of the five
# deliveries that record 012-09-05 ends with, exactly as DeepSeek gave
# it, then each of Gemini's three that followed and its three on the
# Commons, in a scratch folder, and runs its tests. Nothing here is
# changed.
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
#   5-repaired    41 pass (three faults repaired): what Gemini was given
# The two that fail are the same from delivery 2 on:
# home_port_verifies and home_bookmark_and_presence_verify.
# Then Gemini's, every test file of the crate, counted together:
#   g1            42 pass, 2 fail
#   g2            61 pass, 5 fail
#   g3            64 pass, 2 fail
#   g3-repaired   66 pass (fixes 22 and 23): what Gemini was given the
#                 second time
# The two that fail in g1 to g3 are rate_limit_enforced and
# inter_ai_pace_fires; the other three in g2 are the attacks Gemini
# said would get through.
# Then Gemini's three on the Commons (2026-11-17):
#   c1            69 pass
#   c2            82 pass, 3 fail: the three attacks Gemini said would
#                 get through
#   now           92 pass, and the four demos run. This is c3, which
#                 is the crate as it stands.
set -eu
here=$(cd "$(dirname "$0")/.." && pwd)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
python3 "$here/review/steps.py" --aside "$scratch"
python3 "$here/review/steps.py" --check
python3 "$here/review/steps.py" --now "$scratch/more"
for name in 5-repaired g1 g2 g3 g3-repaired c1 c2; do mv "$scratch/more/$name" "$scratch/$name"; done
mkdir "$scratch/now"
cp -R "$here/chat-world-now" "$scratch/now/chat-world"
status=0
check() {
    # check DELIVERY WHAT-THE-TESTS-MUST-SAY
    echo "== delivery $1"
    ( cd "$scratch/$1/chat-world" && cargo test --test integration ) \
        > "$scratch/$1.out" 2>&1 || true
    grep -E '^test result|FAILED$|could not compile' "$scratch/$1.out" || true
    if grep -q "$2" "$scratch/$1.out"; then
        echo "   as recorded"
    else
        echo "   NOT as recorded: wanted \"$2\""
        status=1
    fi
    # Each delivery is built on its own, and its build is not kept:
    # side by side they take a few gigabytes.
    rm -rf "$scratch/$1/chat-world/target"
}
check_all() {
    # check_all DELIVERY PASSED FAILED: every test file, counted together
    echo "== delivery $1"
    ( cd "$scratch/$1/chat-world" && cargo test --no-fail-fast ) \
        > "$scratch/$1.out" 2>&1 || true
    grep -E 'FAILED$|could not compile' "$scratch/$1.out" || true
    got=$(awk '/^test result/ {p += $4; f += $6} END {print p+0 " passed, " f+0 " failed"}' "$scratch/$1.out")
    echo "   $got"
    if [ "$got" = "$2 passed, $3 failed" ]; then
        echo "   as recorded"
    else
        echo "   NOT as recorded: wanted \"$2 passed, $3 failed\""
        status=1
    fi
    if [ "$1" = now ]; then
        for demo in chat-demo home-demo head-demo succession-demo; do
            if ( cd "$scratch/now/chat-world" && cargo run --quiet --bin "$demo" ) \
                > "$scratch/$demo.out" 2>&1; then
                echo "   $demo runs"
            else
                echo "   $demo DOES NOT RUN"
                status=1
            fi
        done
    fi
    rm -rf "$scratch/$1/chat-world/target"
}
check 1 '^test result: ok. 22 passed; 0 failed'
check 2 '^test result: FAILED. 20 passed; 2 failed'
check 3 '^test result: FAILED. 27 passed; 2 failed'
check 4 '^test result: FAILED. 31 passed; 2 failed'
check 5 'could not compile `chat-world`'
check 5-aside '^test result: FAILED. 39 passed; 2 failed'
check 5-repaired '^test result: ok. 41 passed; 0 failed'
check_all g1 42 2
check_all g2 61 5
check_all g3 64 2
check_all g3-repaired 66 0
check_all c1 69 0
check_all c2 82 3
check_all now 92 0
exit $status
