// rust/ur-world/tests/door.rs
//! Minds that run as their own programs, through the doorway: what they
//! are told, and what happens when they answer well, badly, late, too
//! much, or not at all. The minds here are small Python programs (CI has
//! Python), run with `python3 -I`.

// Tests may unwrap, expect, panic and index: a failure here is a failed
// test, not a world that crashed.
#![allow(
    clippy::unwrap_used,
    clippy::expect_used,
    clippy::panic,
    clippy::indexing_slicing
)]

use std::process::{Command, Stdio};
use std::time::{Duration, Instant};

use serde_json::Value;
use ur_world::door::ProcessMind;
use ur_world::world::MAX_SAY;
use ur_world::{Cell, World};

const SEED: u64 = 7;
const A: Cell = Cell::new(4, 1, 5);

/// A Python mind: `code` reads the world's lines from standard input.
fn python(code: &str, limit: Duration) -> Box<ProcessMind> {
    let mut command = Command::new("python3");
    command.args(["-I", "-c", code]).stderr(Stdio::null());
    Box::new(ProcessMind::spawn(command, "ALICE", limit).expect("python3 runs"))
}

/// Run one mind for `ticks` ticks; the log's entries for it, as
/// `(tick, kind, data)`, leaving out what came into view.
fn run(code: &str, limit: Duration, ticks: u64) -> Vec<(u64, String, Value)> {
    let mut w = World::new(SEED);
    w.add("ALICE", python(code, limit), A).unwrap();
    w.run(ticks);
    let log = Value::Array(w.log().to_vec());
    assert!(world_log::verify_log(&log).is_ok());
    w.log()
        .iter()
        .filter(|e| e["agent"] == "ALICE" && e["kind"] != "explored" && e["kind"] != "entered")
        .map(|e| {
            (
                e["tick"].as_u64().unwrap(),
                e["kind"].as_str().unwrap().to_owned(),
                e["data"].clone(),
            )
        })
        .collect()
}

const ECHO: &str = r#"
import json, sys
first = None
for line in sys.stdin:
    m = json.loads(line)
    if "orientation" in m:
        first = m["orientation"].splitlines()[0]
        assert m["name"] == "ALICE" and m["law"]["rules"] == m["rules"]
        continue
    t = m["tick"]
    replies = {
        0: "say " + first,
        1: "say " + m["seen"].splitlines()[0],
        2: "Step East.",
        3: "go somewhere",
        4: "say " + json.dumps(m["observation"]["last"]),
    }
    print(json.dumps({"tick": t, "reply": replies.get(t, "wait")}), flush=True)
"#;

#[test]
fn a_mind_is_told_its_orientation_and_what_it_sees_and_its_replies_are_read() {
    let entries = run(ECHO, Duration::from_secs(20), 6);
    let said = |text: &str| serde_json::json!({ "text": text });
    assert_eq!(
        entries,
        [
            (0, "said".into(), said("You are ALICE, in the Ur-world.")),
            (1, "said".into(), said("Tick 1.")),
            (
                2,
                "moved".into(),
                serde_json::json!({ "from": [4, 1, 5], "to": [5, 1, 5] })
            ),
            (
                3,
                "unreadable".into(),
                serde_json::json!({ "reply": "go somewhere" })
            ),
            (4, "said".into(), said(r#"{"kind": "unreadable"}"#)),
        ]
    );
}

#[test]
fn a_mind_that_never_answers_is_recorded_as_unanswered() {
    let start = Instant::now();
    let entries = run(
        "import sys\nfor line in sys.stdin: pass",
        Duration::from_millis(200),
        3,
    );
    let kinds: Vec<&str> = entries.iter().map(|(_, k, _)| k.as_str()).collect();
    assert_eq!(kinds, ["unanswered"; 3]);
    assert!(start.elapsed() >= Duration::from_millis(600));
}

#[test]
fn a_mind_that_never_reads_doesnt_hold_up_the_world() {
    // Each tick's message is about 600 bytes, so 400 ticks of them are
    // several times what a pipe holds (64 KiB on Linux).
    let start = Instant::now();
    let entries = run("import time\ntime.sleep(60)", Duration::from_millis(5), 400);
    assert_eq!(entries.len(), 400);
    assert!(entries.iter().all(|(_, k, _)| k == "unanswered"));
    assert!(start.elapsed() < Duration::from_secs(20));
}

#[test]
fn a_mind_that_has_gone_is_not_waited_for() {
    let start = Instant::now();
    let entries = run("pass", Duration::from_secs(30), 3);
    let kinds: Vec<&str> = entries.iter().map(|(_, k, _)| k.as_str()).collect();
    assert_eq!(kinds, ["unanswered"; 3]);
    assert!(start.elapsed() < Duration::from_secs(20));
}

#[test]
fn a_late_reply_is_set_aside() {
    // Tick 0 is answered at once, so the program's start-up doesn't count.
    // Tick 1's reply comes half a second after its limit; tick 2's comes
    // as soon as the mind wakes, well within tick 2's limit.
    let late = r#"
import json, sys, time
for line in sys.stdin:
    m = json.loads(line)
    if "tick" not in m:
        continue
    if m["tick"] == 1:
        time.sleep(2.5)
        print(json.dumps({"tick": 1, "reply": "say late"}), flush=True)
    else:
        print(json.dumps({"tick": m["tick"], "reply": "say on time"}), flush=True)
"#;
    let entries = run(late, Duration::from_secs(2), 3);
    let on_time = serde_json::json!({ "text": "on time" });
    assert_eq!(
        entries,
        [
            (0, "said".into(), on_time.clone()),
            (1, "unanswered".into(), serde_json::json!({})),
            (2, "said".into(), on_time),
        ]
    );
}

#[test]
fn a_flood_is_cut_short_and_the_mind_goes_on() {
    let flood = r#"
import json, sys
for line in sys.stdin:
    m = json.loads(line)
    if "tick" not in m:
        continue
    if m["tick"] == 0:
        sys.stdout.write("x" * 200000 + "\n")
        sys.stdout.flush()
    elif m["tick"] == 1:
        print("not json", flush=True)
    else:
        print(json.dumps({"tick": m["tick"], "reply": "say still here"}), flush=True)
"#;
    let entries = run(flood, Duration::from_secs(20), 3);
    assert_eq!(entries.len(), 3);
    assert_eq!(entries[0].1, "unreadable");
    let cut = entries[0].2["reply"].as_str().unwrap();
    assert_eq!(cut, "x".repeat(MAX_SAY));
    assert_eq!(
        entries[1],
        (
            1,
            "unreadable".into(),
            serde_json::json!({ "reply": "not json" })
        )
    );
    assert_eq!(
        entries[2],
        (
            2,
            "said".into(),
            serde_json::json!({ "text": "still here" })
        )
    );
}

#[test]
fn a_mind_that_leaves_is_stopped() {
    let entries = run(
        "import json, sys\nfor line in sys.stdin:\n    m = json.loads(line)\n    if 'tick' in m: print(json.dumps({'tick': m['tick'], 'reply': 'exit'}), flush=True)",
        Duration::from_secs(20),
        3,
    );
    assert_eq!(
        entries,
        [(
            0,
            "exited".into(),
            serde_json::json!({ "reason": "chose to leave" })
        )]
    );
}

#[cfg(target_os = "linux")]
#[test]
fn a_minds_program_is_stopped_when_its_mind_is_dropped() {
    let mind = python(
        "import sys\nfor line in sys.stdin: pass",
        Duration::from_secs(1),
    );
    let proc = format!("/proc/{}", mind.id());
    assert!(std::path::Path::new(&proc).exists());
    drop(mind);
    assert!(!std::path::Path::new(&proc).exists());
}
