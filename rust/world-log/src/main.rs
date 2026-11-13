// rust/world-log/src/main.rs
//! `world-log FILE`: checks a world's public record, a JSON list of log
//! entries as the agent kernel keeps them (`World.log` in `world/core.py`,
//! or the Ur-world's), and says whether it holds. Exits 0 if it does, 1 if
//! it doesn't, and 2 if it can't be checked here: the file can't be read as
//! JSON, or it holds a value this crate can't write exactly as Python does,
//! such as a float. The chemistry soup's log holds floats: check it with
//! Python's `World.verify_log`.

use std::process::ExitCode;

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().collect();
    let [_, path] = args.as_slice() else {
        eprintln!("usage: world-log FILE");
        return ExitCode::from(2);
    };
    let text = match std::fs::read_to_string(path) {
        Ok(text) => text,
        Err(e) => {
            eprintln!("cannot read {path}: {e}");
            return ExitCode::from(2);
        }
    };
    let log: serde_json::Value = match serde_json::from_str(&text) {
        Ok(log) => log,
        Err(e) => {
            eprintln!("{path} is not JSON: {e}");
            return ExitCode::from(2);
        }
    };
    match world_log::verify_log(&log) {
        Ok(head) => {
            let count = log.as_array().map_or(0, Vec::len);
            println!("the log holds: {count} entries, head {head}");
            ExitCode::SUCCESS
        }
        Err(world_log::LogError::Unwritable { index, error }) => {
            println!("the log can't be checked here: entry {index}: {error}");
            ExitCode::from(2)
        }
        Err(e) => {
            println!("the log does not hold: {e}");
            ExitCode::FAILURE
        }
    }
}
