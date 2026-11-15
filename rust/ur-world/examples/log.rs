// rust/ur-world/examples/log.rs
//! Checks an Ur-world log: that its chain of hashes holds (as `world-log`
//! checks it), that every arrival in it holds and keeps each name to one
//! individual (`ur_world::arrival::arrival_problems`), that every link
//! shown in it is one the world would take
//! (`ur_world::link::link_log_problems`), and how much of it the signed
//! heads given cover (`ur_world::arrival::head_coverage`).
//!
//!     cargo run -p ur-world --example log -- LOG [HEAD...]
//!
//! LOG is a JSON list of log entries; each HEAD a JSON file holding one
//! signed head (`open-worlds/log-head/v1`). Exits 0 if the log and every
//! head hold, 1 if not, and 2 if a file can't be read. Entries beyond the
//! longest head are the log's, but not yet signed by its world: a reader
//! who trusts only signed heads trusts only what they cover.

use std::process::ExitCode;

use serde_json::Value;
use ur_world::arrival::{arrival_problems, head_coverage};
use ur_world::link::link_log_problems;

fn read(path: &str) -> Result<Value, String> {
    let text = std::fs::read_to_string(path).map_err(|e| format!("cannot read {path}: {e}"))?;
    serde_json::from_str(&text).map_err(|e| format!("{path} is not JSON: {e}"))
}

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let Some((path, heads)) = args.split_first() else {
        eprintln!("usage: log LOG [HEAD...]");
        return ExitCode::from(2);
    };
    let read_all = || -> Result<(Value, Vec<Value>), String> {
        Ok((
            read(path)?,
            heads.iter().map(|h| read(h)).collect::<Result<_, _>>()?,
        ))
    };
    let (log, heads) = match read_all() {
        Ok(read) => read,
        Err(e) => {
            eprintln!("{e}");
            return ExitCode::from(2);
        }
    };
    if let Err(e) = world_log::verify_log(&log) {
        println!("the log does not hold: {e}");
        return ExitCode::FAILURE;
    }
    let entries = log.as_array().map(Vec::as_slice).unwrap_or_default();
    let mut problems = arrival_problems(entries);
    problems.extend(link_log_problems(entries));
    let (covered, head_problems) = head_coverage(entries, &heads);
    problems.extend(head_problems);
    let count = |kind: &str| entries.iter().filter(|e| e["kind"] == kind).count();
    let (arrivals, links) = (count("entered"), count("linked"));
    println!(
        "{} entries, {arrivals} arrivals, {links} links shown; signed heads cover {covered} of {} entries",
        entries.len(),
        entries.len()
    );
    if problems.is_empty() {
        println!("the log, its arrivals and its links hold");
        ExitCode::SUCCESS
    } else {
        for p in &problems {
            println!("{p}");
        }
        ExitCode::FAILURE
    }
}
