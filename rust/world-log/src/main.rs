// rust/world-log/src/main.rs
//! `world-log LOG [CONTENTS]`: checks a world's public record, a JSON
//! list of log entries as the agent kernel keeps them (`World.log` in
//! `world/core.py`, or the Ur-world's), and says whether it holds.
//!
//! With `CONTENTS`, for a log whose fields are kept apart
//! (`open-worlds/log-apart/v1`, [`world_log::apart`]): also holds the
//! contents kept beside the log to the fingerprints in it, and counts
//! the fields in each state, the redactions (open, standing, or
//! answered by a decision to keep the field public) and the entries a
//! room no longer shows as written.
//!
//! Exits 0 if everything given holds, and 1 if it doesn't: the chain is
//! broken, the log is not in the form, the contents hold something the
//! log doesn't commit to, or a field is missing (gone, with no mark
//! standing). Exits 2 if it can't be checked here: a file can't be read
//! as JSON, or, with no `CONTENTS`, the log holds a value this crate
//! can't write exactly as Python does, such as a float. The chemistry
//! soup's log holds floats: check it with Python's `World.verify_log`.
//! With `CONTENTS`, the log is checked as the form whose fields are kept
//! apart, and by that check alone: it takes the chain with it, an entry
//! at a time, so the first fault in the log's order is the one named. A
//! value this crate can't write is then refused, not left unchecked,
//! since the form allows none.

use serde_json::Value;
use std::process::ExitCode;
use world_log::apart::{self, EntryState, RedactionState, State};

fn read(path: &str) -> Result<Value, ExitCode> {
    let text = std::fs::read_to_string(path).map_err(|e| {
        eprintln!("cannot read {path}: {e}");
        ExitCode::from(2)
    })?;
    serde_json::from_str(&text).map_err(|e| {
        eprintln!("{path} is not JSON: {e}");
        ExitCode::from(2)
    })
}

/// True if the log's first entry names the form whose fields are kept
/// apart.
fn names_the_form(log: &Value) -> bool {
    log.get(0)
        .and_then(|first| first.get("data"))
        .and_then(|data| data.get("form"))
        .and_then(Value::as_str)
        == Some(apart::FORM)
}

/// Says that the log holds: how many entries, and its head.
fn says_the_log_holds(log: &Value) {
    let entries = log.as_array().map_or(&[][..], Vec::as_slice);
    let head = entries
        .last()
        .and_then(|last| last.get("hash"))
        .and_then(Value::as_str)
        .unwrap_or(world_log::GENESIS);
    println!("the log holds: {} entries, head {head}", entries.len());
}

fn check_contents(log: &Value, contents: &Value) -> ExitCode {
    let states = match apart::check(log, contents) {
        Ok(states) => states,
        Err(apart::Refused::Chain(e)) => {
            println!("the log does not hold: {e}");
            return ExitCode::FAILURE;
        }
        Err(e) => {
            // A fault in the contents is found only once the whole log
            // has held.
            if matches!(
                e,
                apart::Refused::Contents(_)
                    | apart::Refused::Unknown(_)
                    | apart::Refused::Salt(_)
                    | apart::Refused::SaltTwice(_)
                    | apart::Refused::Value(_)
                    | apart::Refused::Fingerprint(_)
            ) {
                says_the_log_holds(log);
            }
            println!("the log and its contents do not hold together: {e}");
            return ExitCode::FAILURE;
        }
    };
    says_the_log_holds(log);
    let count = |state: State| {
        states
            .values()
            .flat_map(|fields| fields.values())
            .filter(|s| **s == state)
            .count()
    };
    let missing = count(State::Missing);
    println!(
        "the fields kept apart: {} present, {} redacted, {} unfinished, {} kept public, {} missing",
        count(State::Present),
        count(State::Redacted),
        count(State::Unfinished),
        count(State::KeptPublic),
        missing
    );
    // Every redaction, from the open fields alone: a mark, and what was
    // decided of it. The log has held by now, so this can't be refused.
    let redactions = apart::redactions(log).unwrap_or_default();
    let decided = |state: RedactionState| {
        redactions
            .values()
            .flat_map(|fields| fields.values().flatten())
            .filter(|r| r.state == state)
            .count()
    };
    println!(
        "the redactions: {} open, {} stand, {} kept public",
        decided(RedactionState::Open),
        decided(RedactionState::Stands),
        decided(RedactionState::KeptPublic)
    );
    // What a room shows of each entry, from the open fields alone.
    let standing = apart::incidents(log).unwrap_or_default();
    let shown = |state: EntryState| standing.values().filter(|s| s.state == state).count();
    println!(
        "the entries: {} removed, {} taken back, {} restored, the rest as written",
        shown(EntryState::Removed),
        shown(EntryState::TakenBack),
        shown(EntryState::Restored)
    );
    if missing > 0 {
        println!("the contents are not whole: {missing} missing, gone with no mark standing");
        return ExitCode::FAILURE;
    }
    ExitCode::SUCCESS
}

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().collect();
    let (path, contents_path) = match args.as_slice() {
        [_, path] => (path, None),
        [_, path, contents] => (path, Some(contents)),
        _ => {
            eprintln!("usage: world-log LOG [CONTENTS]");
            return ExitCode::from(2);
        }
    };
    let log = match read(path) {
        Ok(log) => log,
        Err(code) => return code,
    };
    if let Some(contents_path) = contents_path {
        return match read(contents_path) {
            Ok(contents) => check_contents(&log, &contents),
            Err(code) => code,
        };
    }
    match world_log::verify_log(&log) {
        Ok(head) => {
            let count = log.as_array().map_or(0, Vec::len);
            println!("the log holds: {count} entries, head {head}");
        }
        Err(world_log::LogError::Unwritable { index, error }) => {
            println!("the log can't be checked here: entry {index}: {error}");
            return ExitCode::from(2);
        }
        Err(e) => {
            println!("the log does not hold: {e}");
            return ExitCode::FAILURE;
        }
    }
    if names_the_form(&log) {
        println!(
            "its fields are kept apart ({}): give the contents file too, to check them",
            apart::FORM
        );
    }
    ExitCode::SUCCESS
}
