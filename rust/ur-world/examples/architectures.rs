// rust/ur-world/examples/architectures.rs
//! The architectures (`ur_world::architecture`): the octopus, the relay
//! and the swarm, each a small run over trial worlds. Tells what happened
//! in each world, and checks each world's log: its chain, its arrivals,
//! and any link shown in it.
//!
//!     cargo run -p ur-world --example architectures

use std::process::ExitCode;

use serde_json::Value;
use ur_world::World;
use ur_world::architecture::{octopus, relay, swarm};
use ur_world::arrival::arrival_problems;
use ur_world::link::link_log_problems;
use ur_world::story::tell;

/// Tells `world`'s story under `title`, and whether its log holds.
fn show(title: &str, world: &World) -> bool {
    println!("{title}:\n{}", tell(world));
    let mut problems: Vec<String> = match world_log::verify_log(&Value::Array(world.log().to_vec()))
    {
        Ok(_) => Vec::new(),
        Err(e) => vec![format!("the log does not hold: {e}")],
    };
    problems.extend(arrival_problems(world.log()));
    problems.extend(link_log_problems(world.log()));
    for p in &problems {
        println!("{p}");
    }
    if problems.is_empty() {
        println!("Its log and its arrivals hold.\n");
    }
    problems.is_empty()
}

fn main() -> ExitCode {
    let mut held = true;
    match octopus::run() {
        Ok(o) => {
            println!("THE OCTOPUS: one brain, an arm in each of three worlds.\n");
            for ((label, name, _), world) in octopus::ARMS.iter().zip(&o.worlds) {
                held &= show(&format!("In {label}, the arm {name}"), world);
            }
            let reflexes = o.brain.reports().iter().filter(|r| r.reflex).count();
            println!(
                "The brain gave {} intents; the arms reported {} times, and stepped aside by reflex {reflexes} times.\n",
                o.brain.issued().len(),
                o.brain.reports().len()
            );
        }
        Err(e) => {
            eprintln!("the octopus could not run: {e}");
            held = false;
        }
    }
    match relay::run() {
        Ok(r) => {
            println!("THE RELAY: two senses and a leader, in three worlds.\n");
            for ((label, name), world) in relay::PRESENCES.iter().zip(&r.worlds) {
                held &= show(&format!("In {label}, {name}"), world);
            }
            println!("The senses fired (tick, sense): {:?}\n", r.board.fired());
        }
        Err(e) => {
            eprintln!("the relay could not run: {e}");
            held = false;
        }
    }
    match swarm::run() {
        Ok(s) => {
            println!("THE SWARM: five units in one world, one rule, no brain.\n");
            held &= show(&format!("In {}", swarm::WORLD), &s.world);
            let flowers = s
                .world
                .changes()
                .values()
                .filter(|m| **m == ur_world::Material::Flower)
                .count();
            println!("Flowers in the garden: {flowers}.\n");
        }
        Err(e) => {
            eprintln!("the swarm could not run: {e}");
            held = false;
        }
    }
    if held {
        ExitCode::SUCCESS
    } else {
        ExitCode::FAILURE
    }
}
