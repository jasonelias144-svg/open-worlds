#!/bin/sh
# Ours, not DeepSeek's (see ../README.md). Builds a scratch copy of the
# chat-world sketch as it stood at the end of DeepSeek's main reply (the
# files of its later reply are left out, since the crate as written
# doesn't name them), with the one line changed that stops it building,
# and runs its own tests and its demo. The sketch here is never changed.
# Run it from anywhere: sh sketches/deepseek/012-09-05/review/run.sh
#
# It needs Rust and the network: the sketch names ten packages from
# crates.io, and cargo fetches them. CI doesn't run it.
#
# Eight of the sketch's twelve tests fail (finding 2 in ../README.md), so
# those results are printed, not required. Then the same tests are run
# with a record's "type" left out of the bytes that are checked, as it
# is left out of the bytes that are signed: all twelve must pass, which
# shows the cause. That change is a test of the cause, not the repair.
set -eu
here=$(cd "$(dirname "$0")/.." && pwd)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
cp -R "$here/chat-world" "$scratch/"
cd "$scratch/chat-world"
find . -name '*@*' -delete
rm -f src/home.rs src/commons.rs src/transcript.rs src/bin/home-demo.rs
# Finding 1: Message has no hash(); the record it is in does.
sed -i 's/let hash = m\.hash()\.unwrap_or_default();/let hash = rec.hash().unwrap_or_default();/' src/room.rs
grep -q 'let hash = rec.hash()' src/room.rs
echo "== build"
cargo build --quiet
echo "== the sketch's own tests (eight are expected to fail: finding 2)"
cargo test --test integration 2>&1 | grep -E '^test |^test result' || true
echo "== the sketch's demo (its own check of the room fails: finding 2)"
cargo run --quiet --bin chat-demo | grep -E '^Verification|verifies offline'
echo "== the same tests, with the type left out of the checked bytes"
sed -i 's/^        map\.remove("proof");$/        map.remove("proof");\n        map.remove("type");/' src/hash.rs
test "$(grep -c 'map.remove("type");' src/hash.rs)" = 1
cargo test --quiet --test integration 2>&1 | grep -E '^test result'
cargo test --quiet --test integration 2>&1 | grep -q '^test result: ok. 12 passed; 0 failed'
