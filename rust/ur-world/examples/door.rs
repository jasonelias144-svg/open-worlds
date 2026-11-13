// rust/ur-world/examples/door.rs
//! The garden, with minds that run as their own programs: each speaks the
//! doorway's protocol (`ur_world::door`), in any language.
//!
//!     cargo run -p ur-world --example door -- \
//!         --mind TRIAL-1=python3 -I ../minds/wanderer.py \
//!         --mind TRIAL-2=python3 -I ../minds/wanderer.py
//!
//! Options, all before the minds:
//!
//! - `--seed N`: the world's seed (the garden's by default).
//! - `--ticks N`: how many ticks to run (28 by default).
//! - `--limit SECONDS`: how long each mind has to reply each tick (60 by
//!   default).
//! - `--log FILE`: write the world's log there, as JSON.
//!
//! Each `--mind NAME=PROGRAM ARGS...` runs until the next `--mind`. The
//! program is run directly, not through a shell. The first mind enters
//! where ALICE does in the Hello World, the second where BOB does. A
//! mind's standard error is passed through, so its own messages show.

use std::process::{Command, ExitCode};
use std::time::Duration;

use serde_json::Value;
use ur_world::door::ProcessMind;
use ur_world::garden::{ALICE_AT, BOB_AT, SEED, TICKS};
use ur_world::story::{map, tell};
use ur_world::{Cell, World};

const USAGE: &str = "usage: door [--seed N] [--ticks N] [--limit SECONDS] [--log FILE] \
                     --mind NAME=PROGRAM [ARGS...] [--mind NAME=PROGRAM [ARGS...]]";

struct Options {
    seed: u64,
    ticks: u64,
    limit: Duration,
    log: Option<String>,
    minds: Vec<(String, Vec<String>)>,
}

fn options(args: &[String]) -> Result<Options, String> {
    let mut o = Options {
        seed: SEED,
        ticks: TICKS,
        limit: Duration::from_secs(60),
        log: None,
        minds: Vec::new(),
    };
    let mut rest = args.iter();
    while let Some(arg) = rest.next() {
        if let Some((_, words)) = o.minds.last_mut()
            && arg != "--mind"
        {
            words.push(arg.clone());
            continue;
        }
        let mut value = || rest.next().cloned().ok_or(format!("{arg} needs a value"));
        let number = |v: String| v.parse::<u64>().map_err(|e| format!("{arg} {v}: {e}"));
        match arg.as_str() {
            "--seed" => o.seed = number(value()?)?,
            "--ticks" => o.ticks = number(value()?)?,
            "--limit" => o.limit = Duration::from_secs(number(value()?)?),
            "--log" => o.log = Some(value()?),
            "--mind" => {
                let given = value()?;
                let Some((name, program)) = given.split_once('=') else {
                    return Err(format!("--mind {given}: expected NAME=PROGRAM"));
                };
                o.minds.push((name.to_owned(), vec![program.to_owned()]));
            }
            other => return Err(format!("unknown option {other}")),
        }
    }
    if o.minds.is_empty() || o.minds.len() > 2 {
        return Err("give one or two minds".into());
    }
    Ok(o)
}

fn main() -> ExitCode {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let o = match options(&args) {
        Ok(o) => o,
        Err(e) => {
            eprintln!("{e}\n{USAGE}");
            return ExitCode::from(2);
        }
    };
    let mut world = World::new(o.seed);
    let places: [Cell; 2] = [ALICE_AT, BOB_AT];
    for ((name, words), at) in o.minds.iter().zip(places) {
        let Some((program, args)) = words.split_first() else {
            continue;
        };
        let mut command = Command::new(program);
        command.args(args);
        let mind = match ProcessMind::spawn(command, name, o.limit) {
            Ok(mind) => mind,
            Err(e) => {
                eprintln!("{name}'s mind could not start: {e}");
                return ExitCode::FAILURE;
            }
        };
        if let Err(e) = world.add(name, Box::new(mind), at) {
            eprintln!("{name} could not enter: {e:?}");
            return ExitCode::FAILURE;
        }
    }
    world.run(o.ticks);
    println!("{}\n\n{}", tell(&world), map(&world));
    if let Some(path) = o.log {
        let mut text =
            serde_json::to_string_pretty(&Value::Array(world.log().to_vec())).unwrap_or_default();
        text.push('\n');
        if let Err(e) = std::fs::write(&path, text) {
            eprintln!("cannot write the log to {path}: {e}");
            return ExitCode::FAILURE;
        }
    }
    ExitCode::SUCCESS
}
