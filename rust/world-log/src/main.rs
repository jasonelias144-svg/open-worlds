// rust/world-log/src/main.rs
//! `world-log LOG [CONTENTS]`: checks a world's public record, a JSON
//! list of log entries as the agent kernel keeps them (`World.log` in
//! `world/core.py`, or the Ur-world's), and says whether it holds.
//!
//! With `CONTENTS`, for a log whose fields are kept apart
//! (`open-worlds/log-apart/v1`, [`world_log::apart`]): also holds the
//! contents kept beside the log to the fingerprints in it, and counts
//! the fields in each state.
//!
//! Exits 0 if everything given holds, and 1 if it doesn't: the chain is
//! broken, the contents hold something the log doesn't commit to, or a
//! field is missing (gone, with no mark standing). Exits 2 if it can't be
//! checked here: a file can't be read as JSON, or the log holds a value
//! this crate can't write exactly as Python does, such as a float. The
//! chemistry soup's log holds floats: check it with Python's
//! `World.verify_log`.

use serde_json::Value;
use std::process::ExitCode;
use world_log::apart::{self, State};

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

fn check_contents(log: &Value, contents: &Value) -> ExitCode {
    let states = match apart::check(log, contents) {
        Ok(states) => states,
        Err(e) => {
            println!("the log and its contents do not hold together: {e}");
            return ExitCode::FAILURE;
        }
    };
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
    match contents_path {
        Some(contents_path) => match read(contents_path) {
            Ok(contents) => check_contents(&log, &contents),
            Err(code) => code,
        },
        None => {
            if names_the_form(&log) {
                println!(
                    "its fields are kept apart ({}): give the contents file too, to check them",
                    apart::FORM
                );
            }
            ExitCode::SUCCESS
        }
    }
}
