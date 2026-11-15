//! The shared vectors are still what this crate writes. Tests may unwrap.
#![allow(clippy::unwrap_used, clippy::indexing_slicing)]

use plant_world::vectors::shared_vectors;
use plant_world::world::log_problems;
use serde_json::Value;

#[test]
fn the_vectors_file_is_what_the_crate_writes() {
    let path = concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../vectors/plant-world.json"
    );
    let file: Value = serde_json::from_str(&std::fs::read_to_string(path).unwrap()).unwrap();
    assert_eq!(
        file,
        shared_vectors().unwrap(),
        "rewrite it: cargo run -p plant-world --example plant -- --vectors ../vectors"
    );
}

#[test]
fn every_log_in_the_vectors_holds_by_its_rule() {
    let vectors = shared_vectors().unwrap();
    for world in vectors["worlds"].as_array().unwrap() {
        let log = world["log"].as_array().unwrap();
        assert!(log_problems(log).is_empty(), "{}", world["name"]);
    }
}
