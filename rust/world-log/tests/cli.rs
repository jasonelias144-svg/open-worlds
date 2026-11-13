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
fn a_file_that_is_not_json_is_reported() {
    let file = Scratch::new("broken.json", "[{");
    assert_eq!(run(&file.0).0, Some(2));
    let missing = std::env::temp_dir().join("world-log-no-such-file.json");
    assert_eq!(run(&missing).0, Some(2));
}
