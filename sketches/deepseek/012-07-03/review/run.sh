#!/bin/sh
# Ours, not DeepSeek's (see ../README.md). Builds a scratch copy of the
# endless-plant sketch with review/missing.rs added, and runs its own
# tests and review/review.rs. The sketch here is never changed. Run it
# from anywhere: sh sketches/deepseek/012-07-03/review/run.sh
#
# The sketch's own vector test fails (finding 2), so its result is
# printed, not required; the review's tests must all pass.
set -eu
here=$(cd "$(dirname "$0")/.." && pwd)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
cp -R "$here/endless-plant" "$scratch/"
cd "$scratch/endless-plant"
# The sketch names open-worlds' formats crate by a path that doesn't
# lead to it from this folder, and uses nothing from it.
grep -v '^formats = ' Cargo.toml > Cargo.toml.new && mv Cargo.toml.new Cargo.toml
cat "$here/review/missing.rs" >> src/rule.rs
mkdir -p tests && cp "$here/review/review.rs" tests/review.rs
echo "== the sketch's own tests (expected to fail: finding 2)"
cargo test --quiet --lib 2>&1 | tail -n 15 || true
echo "== the review's tests"
cargo test --quiet --test review
