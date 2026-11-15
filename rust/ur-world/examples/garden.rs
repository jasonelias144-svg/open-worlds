// rust/ur-world/examples/garden.rs
//! Hello World for building worlds: run the garden, tell what happened, and
//! draw a map of what has come into view.
//!
//!     cargo run -p ur-world --example garden
//!     cargo run -p ur-world --example garden -- --vectors ../vectors
//!
//! With `--vectors DIR`, it also writes the shared test vectors
//! `ur-garden-log.json`, `ur-garden-head.json` (the log's head, signed by
//! the garden's trial world key), `ur-garden-hosted.json` (the plant
//! worlds the garden hosts: their logs, heads and birth records) and
//! `ur-chunks.json` into DIR. The folder must exist.

use std::process::ExitCode;

use serde_json::Value;
use ur_world::World;
use ur_world::arrival::head;
use ur_world::garden::{CREATED, hello_world, hosted_vectors, world_secret};
use ur_world::story::{map, tell};

fn main() -> ExitCode {
    let world = match hello_world() {
        Ok(world) => world,
        Err(e) => {
            eprintln!("the garden could not begin: {e}");
            return ExitCode::FAILURE;
        }
    };
    println!("{}\n\n{}", tell(&world), map(&world));
    let args: Vec<String> = std::env::args().collect();
    if let [_, flag, dir] = args.as_slice() {
        if flag != "--vectors" {
            eprintln!("usage: garden [--vectors DIR]");
            return ExitCode::from(2);
        }
        if let Err(e) = write_vectors(&world, dir) {
            eprintln!("cannot write the vectors: {e}");
            return ExitCode::FAILURE;
        }
    }
    ExitCode::SUCCESS
}

fn write_vectors(world: &World, dir: &str) -> std::io::Result<()> {
    let log = Value::Array(world.log().to_vec());
    std::fs::write(format!("{dir}/ur-garden-log.json"), pretty(&log))?;
    let head = head(world, &world_secret(), CREATED).map_err(std::io::Error::other)?;
    std::fs::write(format!("{dir}/ur-garden-head.json"), pretty(&head))?;
    let hosted = hosted_vectors(world).map_err(std::io::Error::other)?;
    std::fs::write(format!("{dir}/ur-garden-hosted.json"), pretty(&hosted))?;
    std::fs::write(
        format!("{dir}/ur-chunks.json"),
        pretty(&ur_world::generate::vectors()),
    )?;
    Ok(())
}

fn pretty(v: &Value) -> String {
    let mut s = serde_json::to_string_pretty(v).unwrap_or_default();
    s.push('\n');
    s
}
