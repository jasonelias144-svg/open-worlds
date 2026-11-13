// rust/ur-world/tests/garden.rs
//! The garden's Hello World, checked: its log holds by the same check as
//! the Python kernel's, it is exactly what the shared vectors record, and
//! every chunk it explored is what the generator makes.

// Tests may unwrap, expect, panic and index: a failure here is a failed
// test, not a world that crashed.
#![allow(
    clippy::unwrap_used,
    clippy::expect_used,
    clippy::panic,
    clippy::indexing_slicing
)]

use std::collections::BTreeSet;

use serde_json::{Value, json};
use ur_world::garden::{ALICE_AT, BOB_AT, SEED, TICKS, hello_world};
use ur_world::generate::{self, GENERATOR};
use ur_world::{Cell, ChunkCoord, Material};

const LOG: &str = include_str!("../../../vectors/ur-garden-log.json");
const CHUNKS: &str = include_str!("../../../vectors/ur-chunks.json");

fn of_kind<'a>(log: &'a [Value], kind: &str) -> Vec<&'a Value> {
    log.iter().filter(|e| e["kind"] == kind).collect()
}

fn coord(v: &Value) -> ChunkCoord {
    ChunkCoord::new(
        v[0].as_i64().unwrap(),
        v[1].as_i64().unwrap(),
        v[2].as_i64().unwrap(),
    )
}

#[test]
fn the_log_holds_by_the_same_check_as_pythons() {
    let world = hello_world().unwrap();
    let log = Value::Array(world.log().to_vec());
    let head = world.log().last().unwrap()["hash"].as_str().unwrap();
    assert_eq!(world_log::verify_log(&log), Ok(head));
}

#[test]
fn the_garden_is_what_the_vectors_record() {
    // Rewrite with: cargo run -p ur-world --example garden -- --vectors ../vectors
    let recorded: Value = serde_json::from_str(LOG).unwrap();
    assert_eq!(
        Value::Array(hello_world().unwrap().log().to_vec()),
        recorded
    );
}

#[test]
fn the_generator_is_what_the_vectors_record() {
    let recorded: Value = serde_json::from_str(CHUNKS).unwrap();
    assert_eq!(generate::vectors(), recorded);
}

#[test]
fn the_same_seed_gives_the_same_world() {
    assert_eq!(hello_world().unwrap().log(), hello_world().unwrap().log());
}

#[test]
fn the_story_begins_as_decided() {
    let world = hello_world().unwrap();
    let log = world.log();
    assert_eq!(log[0]["kind"], "world_created");
    assert_eq!(log[0]["data"]["seed"], SEED);
    assert_eq!(log[0]["data"]["generator"], GENERATOR);
    let entered: Vec<(&Value, &Value)> = of_kind(log, "entered")
        .iter()
        .map(|e| (&e["agent"], &e["data"]["pos"]))
        .collect();
    assert_eq!(
        entered,
        [
            (&json!("ALICE"), &ALICE_AT.json()),
            (&json!("BOB"), &BOB_AT.json())
        ]
    );
    // One speaks, the other listens; then they turn.
    let said: Vec<(&Value, &Value, &Value)> = of_kind(log, "said")
        .iter()
        .map(|e| (&e["tick"], &e["agent"], &e["data"]["text"]))
        .collect();
    assert_eq!(
        said,
        [
            (&json!(0), &json!("ALICE"), &json!("Hello, world.")),
            (&json!(1), &json!("BOB"), &json!("Hello, ALICE.")),
        ]
    );
    let planted = of_kind(log, "planted");
    assert_eq!(planted.len(), 1);
    assert_eq!(planted[0]["agent"], "BOB");
    assert_eq!(planted[0]["data"]["at"], json!([4, 1, 0]));
    assert_eq!(world.tick(), TICKS);
}

#[test]
fn every_explored_chunk_is_what_the_generator_makes() {
    let world = hello_world().unwrap();
    let explored = of_kind(world.log(), "explored");
    let mut seen = BTreeSet::new();
    for e in &explored {
        let c = coord(&e["data"]["chunk"]);
        assert!(seen.insert(c), "{c:?} explored twice");
        assert_eq!(e["data"]["generator"], GENERATOR);
        // Each was explored before anything in it changed.
        assert_eq!(e["data"]["hash"], generate::generate(SEED, c).hash());
    }
    assert_eq!(&seen, world.explored());
    // The land beyond what they saw holds no data at all.
    assert!(!world.explored().contains(&ChunkCoord::new(10, 0, 0)));
}

#[test]
fn the_world_stores_only_what_changed() {
    let world = hello_world().unwrap();
    let changed: Vec<(Cell, Material)> = world.changes().iter().map(|(c, m)| (*c, *m)).collect();
    assert_eq!(changed, [(Cell::new(4, 1, 0), Material::Flower)]);
    // The chunk as it is now differs from the generated one by that cell.
    let home = ChunkCoord::new(0, 0, 0);
    let mut expected = generate::generate(SEED, home);
    assert_ne!(world.chunk(home), expected);
    expected.set(Cell::new(4, 1, 0), Material::Flower);
    assert_eq!(world.chunk(home), expected);
}

#[test]
fn alice_walked_out_of_the_garden_and_climbed_the_hills() {
    let world = hello_world().unwrap();
    let moves: Vec<&Value> = of_kind(world.log(), "moved")
        .into_iter()
        .filter(|e| e["agent"] == "ALICE")
        .collect();
    assert_eq!(moves.len(), 24);
    for m in &moves {
        let (from, to) = (&m["data"]["from"], &m["data"]["to"]);
        // A step goes one cell across, and up or down by at most one here.
        let dy = to[1].as_i64().unwrap() - from[1].as_i64().unwrap();
        assert!(dy.abs() <= 1, "{m}");
    }
    let end = world.position("ALICE").unwrap();
    assert_eq!((end.x, end.z), (19, -2));
    assert!(end.y > 1, "ALICE has climbed: {end:?}");
    assert_eq!(world.position("BOB"), Some(BOB_AT));
}
