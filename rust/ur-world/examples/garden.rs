// rust/ur-world/examples/garden.rs
//! Hello World for building worlds: run the garden, tell what happened, and
//! draw a map of what has come into view.
//!
//!     cargo run -p ur-world --example garden
//!     cargo run -p ur-world --example garden -- --vectors ../vectors
//!
//! With `--vectors DIR`, it also writes the shared test vectors
//! `ur-garden-log.json` and `ur-chunks.json` into DIR.

use std::process::ExitCode;

use serde_json::Value;
use ur_world::garden::hello_world;
use ur_world::space::CHUNK;
use ur_world::{Material, World};

fn main() -> ExitCode {
    let world = match hello_world() {
        Ok(world) => world,
        Err(e) => {
            eprintln!("the garden could not begin: {e:?}");
            return ExitCode::FAILURE;
        }
    };
    tell(&world);
    println!();
    draw(&world);
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

fn text(v: Option<&Value>) -> String {
    match v {
        Some(Value::String(s)) => s.clone(),
        Some(other) => other.to_string(),
        None => String::new(),
    }
}

/// The log, told as a story: one line for each event, with the chunks that
/// came into view counted rather than listed.
fn tell(world: &World) {
    let mut explored = 0;
    let mut last_tick = None;
    for entry in world.log() {
        let kind = text(entry.get("kind"));
        let who = text(entry.get("agent"));
        let data = entry.get("data");
        let tick = text(entry.get("tick"));
        if kind == "explored" {
            explored += 1;
            continue;
        }
        if explored > 0 {
            println!("        ({explored} chunks came into view)");
            explored = 0;
        }
        let what = match kind.as_str() {
            "world_created" => format!(
                "The world is created from seed {}: {}.",
                text(data.and_then(|d| d.get("seed"))),
                text(data.and_then(|d| d.get("begins")))
            ),
            "entered" => format!(
                "{who} enters, at {}.",
                text(data.and_then(|d| d.get("pos")))
            ),
            "said" => format!("{who} says: \"{}\"", text(data.and_then(|d| d.get("text")))),
            "planted" => format!(
                "{who} plants a {} at {}.",
                text(data.and_then(|d| d.get("what"))),
                text(data.and_then(|d| d.get("at")))
            ),
            "moved" => format!("{who} moves to {}.", text(data.and_then(|d| d.get("to")))),
            "fell" => format!("{who} falls to {}.", text(data.and_then(|d| d.get("to")))),
            "blocked" => format!(
                "{who} can't {} {}.",
                text(data.and_then(|d| d.get("action"))),
                text(data.and_then(|d| d.get("dir")))
            ),
            "exited" => format!(
                "{who} leaves ({}).",
                text(data.and_then(|d| d.get("reason")))
            ),
            other => format!("{other} {who}"),
        };
        let stamp = if last_tick.as_ref() == Some(&tick) {
            String::new()
        } else {
            format!("[{tick}]")
        };
        last_tick = Some(tick);
        println!("{stamp:>7} {what}");
    }
    if explored > 0 {
        println!("        ({explored} chunks came into view)");
    }
    println!(
        "\n{} log entries; head {}.\n{} chunks explored; {} cell(s) changed and stored.",
        world.log().len(),
        world
            .log()
            .last()
            .and_then(|e| e.get("hash"))
            .and_then(Value::as_str)
            .unwrap_or(""),
        world.explored().len(),
        world.changes().len()
    );
}

/// A map seen from above, one character a cell: what lies on top in each
/// explored column, the two of them, and blank where no one has looked.
fn draw(world: &World) {
    let explored = world.explored();
    let (Some(west), Some(east)) = (
        explored.iter().map(|c| c.x).min(),
        explored.iter().map(|c| c.x).max(),
    ) else {
        return;
    };
    let (Some(north), Some(south)) = (
        explored.iter().map(|c| c.z).min(),
        explored.iter().map(|c| c.z).max(),
    ) else {
        return;
    };
    let people = world.inhabitants();
    println!("North is up. A = ALICE, B = BOB, T = the tree (its crown), ~ water,");
    println!("* flower; the land by height: . 0 or below, : 1 to 3, = 4 to 7, ^ 8 and up;");
    println!("blank: not yet explored.");
    for z in north * CHUNK..(south + 1) * CHUNK {
        let mut row = String::new();
        for x in west * CHUNK..(east + 1) * CHUNK {
            let here = people
                .iter()
                .find(|(_, c)| c.x == x && c.z == z)
                .map(|(n, _)| n.as_str());
            let ch = match (here, world.surface(x, z)) {
                (Some("ALICE"), _) => 'A',
                (Some("BOB"), _) => 'B',
                (Some(_), _) => '@',
                (None, None) => ' ',
                (None, Some((y, m))) => match m {
                    Material::Grass | Material::Soil if y <= 0 => '.',
                    Material::Grass | Material::Soil if y <= 3 => ':',
                    Material::Grass | Material::Soil if y <= 7 => '=',
                    Material::Grass | Material::Soil | Material::Rock => '^',
                    Material::Water => '~',
                    Material::Wood | Material::Leaves => 'T',
                    Material::Flower => '*',
                    Material::Air => ' ',
                },
            };
            row.push(ch);
        }
        println!("{}", row.trim_end());
    }
}

fn write_vectors(world: &World, dir: &str) -> std::io::Result<()> {
    let log = Value::Array(world.log().to_vec());
    std::fs::write(format!("{dir}/ur-garden-log.json"), pretty(&log))?;
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
