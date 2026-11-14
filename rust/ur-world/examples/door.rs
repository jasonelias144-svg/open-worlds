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
//! - `--head FILE`: write the log's head there, signed by the run's world
//!   key, as JSON (`open-worlds/log-head/v1`).
//!
//! Each `--mind NAME=PROGRAM ARGS...` runs until the next `--mind`. The
//! program is run directly, not through a shell. The first mind enters
//! west of the tree, where WALKER does in the Hello World, the second east
//! of it. A mind's standard error is passed through, so its own messages
//! show.
//!
//! A run is a trial world of its own (docs/research/KEYS.md, decision
//! 14): the doorway makes a fresh key for the world and one for each mind,
//! signs each mind's arrival with its key, and throws the keys away at the
//! end. No key is passed to a mind's program, and no holder's key is read.

use std::process::{Command, ExitCode};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use formats::proof::public_key;
use serde_json::Value;
use ur_world::arrival::{self, utc};
use ur_world::door::ProcessMind;
use ur_world::garden::{FIRST_AT, SECOND_AT, SEED, TICKS};
use ur_world::story::{map, tell};
use ur_world::{Cell, World};

const USAGE: &str = "usage: door [--seed N] [--ticks N] [--limit SECONDS] [--log FILE] \
                     [--head FILE] --mind NAME=PROGRAM [ARGS...] [--mind NAME=PROGRAM [ARGS...]]";

struct Options {
    seed: u64,
    ticks: u64,
    limit: Duration,
    log: Option<String>,
    head: Option<String>,
    minds: Vec<(String, Vec<String>)>,
}

fn options(args: &[String]) -> Result<Options, String> {
    let mut o = Options {
        seed: SEED,
        ticks: TICKS,
        limit: Duration::from_secs(60),
        log: None,
        head: None,
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
            "--head" => o.head = Some(value()?),
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

/// A fresh key, from the operating system's randomness.
fn fresh_key() -> Result<[u8; 32], String> {
    let mut secret = [0; 32];
    getrandom::fill(&mut secret).map_err(|e| format!("no randomness for a key: {e}"))?;
    Ok(secret)
}

/// The signer's clock, as a proof writes it.
fn now() -> String {
    utc(SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_or(0, |d| d.as_secs()))
}

fn write_json(path: &str, value: &Value) -> Result<(), String> {
    let mut text = serde_json::to_string_pretty(value).unwrap_or_default();
    text.push('\n');
    std::fs::write(path, text).map_err(|e| format!("cannot write {path}: {e}"))
}

fn run(o: &Options) -> Result<(), String> {
    let world_secret = fresh_key()?;
    let mut world = World::new(o.seed, &public_key(&world_secret));
    eprintln!("This run is a trial world of its own: {}", world.key());
    let places: [Cell; 2] = [FIRST_AT, SECOND_AT];
    for ((name, words), at) in o.minds.iter().zip(places) {
        let Some((program, args)) = words.split_first() else {
            continue;
        };
        let secret = fresh_key()?;
        let arrival = arrival::sign(&world, &secret, name, &now())?;
        let admission = world
            .admit(&arrival)
            .map_err(|e| format!("{name} could not enter: {e}"))?;
        let mut command = Command::new(program);
        command.args(args);
        let mind = ProcessMind::spawn(command, name, admission, o.limit)
            .map_err(|e| format!("{name}'s mind could not start: {e}"))?;
        world
            .enter(&arrival, Box::new(mind), at)
            .map_err(|e| format!("{name} could not enter: {e}"))?;
        eprintln!("{name} entered as {}", arrival::did(&secret));
    }
    world.run(o.ticks);
    println!("{}\n\n{}", tell(&world), map(&world));
    if let Some(path) = &o.log {
        write_json(path, &Value::Array(world.log().to_vec()))?;
    }
    if let Some(path) = &o.head {
        write_json(path, &arrival::head(&world, &world_secret, &now())?)?;
    }
    Ok(())
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
    match run(&o) {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("{e}");
            ExitCode::FAILURE
        }
    }
}
