// rust/world-log/tests/cli.rs
//! The `world-log` command, run on the Python kernel's log and on changed
//! copies of it.

// Tests may unwrap, expect, panic and index: a failure here is a failed
// test, not a world that crashed.
#![allow(
    clippy::unwrap_used,
    clippy::expect_used,
    clippy::panic,
    clippy::indexing_slicing
)]

use std::path::{Path, PathBuf};
use std::process::Command;

const LOG: &str = concat!(env!("CARGO_MANIFEST_DIR"), "/../../vectors/world-log.json");

fn run(path: &Path) -> (Option<i32>, String) {
    let out = Command::new(env!("CARGO_BIN_EXE_world-log"))
        .arg(path)
        .output()
        .unwrap();
    (
        out.status.code(),
        String::from_utf8_lossy(&out.stdout).into_owned(),
    )
}

/// A file of our own in the system's temporary folder, removed when dropped.
struct Scratch(PathBuf);

impl Scratch {
    fn new(name: &str, contents: &str) -> Scratch {
        let path = std::env::temp_dir().join(format!("world-log-{}-{name}", std::process::id()));
        std::fs::write(&path, contents).unwrap();
        Scratch(path)
    }
}

impl Drop for Scratch {
    fn drop(&mut self) {
        let _ = std::fs::remove_file(&self.0);
    }
}

#[test]
fn the_python_log_holds() {
    let (code, out) = run(Path::new(LOG));
    assert_eq!(code, Some(0), "{out}");
    assert!(out.starts_with("the log holds: 19 entries, head "), "{out}");
}

#[test]
fn a_changed_log_does_not_hold() {
    let text = std::fs::read_to_string(LOG).unwrap();
    let changed = text.replacen("hello, world", "hello, world!", 1);
    assert_ne!(changed, text);
    let file = Scratch::new("changed.json", &changed);
    let (code, out) = run(&file.0);
    assert_eq!(code, Some(1), "{out}");
    assert!(out.starts_with("the log does not hold: entry "), "{out}");
}

#[test]
fn a_log_it_cannot_write_exactly_is_reported_as_unchecked() {
    // A float, as in the chemistry soup's log: Python can check it, this
    // crate can't, and it says so rather than calling the log broken.
    let text = std::fs::read_to_string(LOG).unwrap();
    let changed = text.replacen("\"pos\": [", "\"pos\": [0.5, ", 1);
    assert_ne!(changed, text);
    let file = Scratch::new("float.json", &changed);
    let (code, out) = run(&file.0);
    assert_eq!(code, Some(2), "{out}");
    assert!(
        out.starts_with("the log can't be checked here: entry "),
        "{out}"
    );
}

#[test]
fn a_file_that_is_not_json_is_reported() {
    let file = Scratch::new("broken.json", "[{");
    assert_eq!(run(&file.0).0, Some(2));
    let missing = std::env::temp_dir().join("world-log-no-such-file.json");
    assert_eq!(run(&missing).0, Some(2));
}

// -- a log whose fields are kept apart, with its contents --

const APART: &str = include_str!("../../../vectors/log-apart.json");

fn run_with(log: &Path, contents: &Path) -> (Option<i32>, String) {
    let out = Command::new(env!("CARGO_BIN_EXE_world-log"))
        .arg(log)
        .arg(contents)
        .output()
        .unwrap();
    (
        out.status.code(),
        String::from_utf8_lossy(&out.stdout).into_owned(),
    )
}

/// One case of the shared vectors, as a log file and a contents file.
/// `test` names the files, so that tests running at once, each removing
/// its own, never share one.
fn case(test: &str, group: &str, name: &str) -> (Scratch, Scratch) {
    let vectors: serde_json::Value = serde_json::from_str(APART).unwrap();
    let case = vectors[group]
        .as_array()
        .unwrap()
        .iter()
        .find(|c| c["name"] == name)
        .unwrap_or_else(|| panic!("no case named {name}"));
    (
        Scratch::new(&format!("{test}-log.json"), &case["log"].to_string()),
        Scratch::new(
            &format!("{test}-contents.json"),
            &case["contents"].to_string(),
        ),
    )
}

#[test]
fn a_whole_log_and_its_contents_hold() {
    let (log, contents) = case("whole", "holds", "every field is there");
    let (code, out) = run_with(&log.0, &contents.0);
    assert_eq!(code, Some(0), "{out}");
    assert!(out.starts_with("the log holds: 7 entries, head "), "{out}");
    assert!(
        out.contains(
            "the fields kept apart: 15 present, 0 redacted, 0 unfinished, 0 kept public, 0 missing"
        ),
        "{out}"
    );
}

#[test]
fn the_log_alone_holds_and_asks_for_its_contents() {
    let (log, _contents) = case("alone", "holds", "every field is there");
    let (code, out) = run(&log.0);
    assert_eq!(code, Some(0), "{out}");
    assert!(out.starts_with("the log holds: 7 entries, head "), "{out}");
    assert!(out.contains("give the contents file too"), "{out}");
    // The kernel's own form is not asked for any.
    let (_, out) = run(Path::new(LOG));
    assert!(!out.contains("contents"), "{out}");
}

#[test]
fn missing_fields_are_counted_and_fail() {
    let (log, contents) = case("states", "holds", "the five states");
    let (code, out) = run_with(&log.0, &contents.0);
    assert_eq!(code, Some(1), "{out}");
    assert!(
        out.contains(
            "the fields kept apart: 18 present, 3 redacted, 1 unfinished, 1 kept public, 2 missing"
        ),
        "{out}"
    );
    assert!(
        out.contains("the contents are not whole: 2 missing"),
        "{out}"
    );
}

#[test]
fn contents_that_do_not_match_fail() {
    let (log, contents) = case("changed", "refused", "the value was changed");
    let (code, out) = run_with(&log.0, &contents.0);
    assert_eq!(code, Some(1), "{out}");
    assert!(out.starts_with("the log holds: 2 entries, head "), "{out}");
    assert!(
        out.contains(
            "the log and its contents do not hold together: \
             the contents do not match the fingerprint: entry "
        ),
        "{out}"
    );
    // The kernel's own log has no contents to hold.
    let (code, out) = run_with(Path::new(LOG), &contents.0);
    assert_eq!(code, Some(1), "{out}");
    assert!(
        out.contains("the first entry does not name this form"),
        "{out}"
    );
}

#[test]
fn contents_that_cannot_be_read_are_reported() {
    let (log, _contents) = case("unread", "holds", "every field is there");
    let broken = Scratch::new("broken-contents.json", "{");
    assert_eq!(run_with(&log.0, &broken.0).0, Some(2));
    let three = Command::new(env!("CARGO_BIN_EXE_world-log"))
        .args(["a", "b", "c"])
        .output()
        .unwrap();
    assert_eq!(three.status.code(), Some(2));
}
