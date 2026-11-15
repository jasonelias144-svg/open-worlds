// rust/ur-world/examples/person.rs
//! A person's Hello World (`ur_world::person`): one trial person with a
//! presence in each of three trial worlds at once. Tells what happened in
//! each world, what the person's client carried between them, and checks
//! each world's log: its chain, its arrivals, and the link shown in it.
//!
//!     cargo run -p ur-world --example person
//!     cargo run -p ur-world --example person -- --vectors ../vectors
//!
//! With `--vectors DIR`, it also writes the shared test vectors
//! `ur-person.json` into DIR, which must exist.

use std::process::ExitCode;

use serde_json::Value;
use ur_world::arrival::arrival_problems;
use ur_world::link::link_log_problems;
use ur_world::person::{WORLDS, trial, vectors};
use ur_world::story::tell;

fn main() -> ExitCode {
    let trial = match trial() {
        Ok(trial) => trial,
        Err(e) => {
            eprintln!("the trial could not begin: {e}");
            return ExitCode::FAILURE;
        }
    };
    let mut held = true;
    for ((label, name), world) in WORLDS.iter().zip(&trial.worlds) {
        println!("In {label}, where the person is {name}:\n{}", tell(world));
        let log = Value::Array(world.log().to_vec());
        let mut problems: Vec<String> = match world_log::verify_log(&log) {
            Ok(_) => Vec::new(),
            Err(e) => vec![format!("the log does not hold: {e}")],
        };
        problems.extend(arrival_problems(world.log()));
        problems.extend(link_log_problems(world.log()));
        if problems.is_empty() {
            println!("Its log, its arrivals and its links hold.\n");
        } else {
            held = false;
            for p in &problems {
                println!("{p}");
            }
            println!();
        }
    }
    println!("The person's client carried: {:?}", trial.notes.notes());
    let args: Vec<String> = std::env::args().collect();
    if let [_, flag, dir] = args.as_slice() {
        if flag != "--vectors" {
            eprintln!("usage: person [--vectors DIR]");
            return ExitCode::from(2);
        }
        let written = vectors(&trial).and_then(|v| {
            let mut text = serde_json::to_string_pretty(&v).map_err(|e| e.to_string())?;
            text.push('\n');
            std::fs::write(format!("{dir}/ur-person.json"), text).map_err(|e| e.to_string())
        });
        if let Err(e) = written {
            eprintln!("cannot write the vectors: {e}");
            return ExitCode::FAILURE;
        }
    }
    if held {
        ExitCode::SUCCESS
    } else {
        ExitCode::FAILURE
    }
}
