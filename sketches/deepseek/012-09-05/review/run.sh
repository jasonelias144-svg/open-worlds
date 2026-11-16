#!/bin/sh
# Ours, not DeepSeek's (see ../README.md). Builds a scratch copy of the
# chat-world sketch as it stands here, after the changes ../README.md
# lists, and runs its own tests and its two demos. The sketch here is
# never changed. Run it from anywhere:
#   sh sketches/deepseek/012-09-05/review/run.sh
#
# It needs Rust and the network: the sketch names ten packages from
# crates.io, and cargo fetches them. CI doesn't run it. The sketch has
# no Cargo.lock, so cargo takes the newest versions that fit, and a
# result can change with what crates.io serves that day.
#
# All eighteen of the sketch's tests must pass, and both demos must say
# their logs verify. Then one more test, ours, shows a finding that is
# not fixed: after a redaction, the visible log still shows the text.
set -eu
here=$(cd "$(dirname "$0")/.." && pwd)
scratch=$(mktemp -d)
trap 'rm -rf "$scratch"' EXIT
cp -R "$here/chat-world" "$scratch/"
cd "$scratch/chat-world"
# The files named file@LINE are the record's additions, kept beside the
# files they were merged into; cargo must not see them.
find . -name '*@*' -delete
echo "== build"
cargo build --quiet
echo "== the sketch's own tests"
cargo test --test integration > tests.out 2>&1 || true
grep -E '^test |^test result' tests.out
grep -q '^test result: ok. 18 passed; 0 failed' tests.out
echo "== the sketch's demos"
cargo run --quiet --bin chat-demo > chat-demo.out
grep -E '^Verification' chat-demo.out
grep -q '^Verification: room verifies offline' chat-demo.out
cargo run --quiet --bin home-demo > home-demo.out
grep -E '^  (home|bob.s|commons): ' home-demo.out
test "$(grep -cE '^  (home|bob.s|commons): +verifies' home-demo.out)" = 3
echo "== a finding, not fixed: a redacted message's text in the visible log"
cat > tests/redaction_probe.rs <<'PROBE'
use chat_world::{Keypair, Room, RoomTemplate};

#[test]
fn a_redacted_message_still_shows_its_text() {
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "test"), alice).unwrap();
    room.join(&bob, "communicate", false).unwrap();
    let msg = room.post(&bob, "words I take back", "normal").unwrap();
    let hash = msg.hash().unwrap();
    room.redact(&bob, &hash, "regret").unwrap();
    assert!(room.is_redacted(&hash));
    let shown: Vec<String> = room
        .visible_log()
        .iter()
        .filter(|e| e["type"] == "message")
        .map(|e| format!("redacted={} text={}", e["redacted"], e["text"]))
        .collect();
    println!("visible log: {}", shown.join("; "));
    // The finding: this is what the sketch does, not what it should do.
    assert_eq!(shown, vec!["redacted=false text=\"words I take back\""]);
}
PROBE
cargo test --quiet --test redaction_probe -- --nocapture > probe.out 2>&1 || true
grep -E '^visible log|^test result' probe.out
grep -q '^test result: ok. 1 passed' probe.out
