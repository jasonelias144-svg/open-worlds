// rust/plant-wasi/tests/respond.rs
//! The command grows the same logs as the shared vectors, and refuses what
//! isn't a request, with the reason.

// Tests may unwrap, expect, panic and index: a failure here is a failed
// test, which is what it should be.
#![allow(
    clippy::unwrap_used,
    clippy::expect_used,
    clippy::panic,
    clippy::indexing_slicing
)]

use plant_wasi::{MAX_TICKS, respond};
use serde_json::{Value, json};

fn vectors() -> Value {
    let path = concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../vectors/plant-world.json"
    );
    serde_json::from_str(&std::fs::read_to_string(path).unwrap()).unwrap()
}

/// The request that grows `world` from its first entry.
fn request(world: &Value, ticks: u64) -> Value {
    let first = &world["log"][0]["data"];
    json!({
        "key": first["world"], "template": first["template"],
        "dials": first["dials"], "pot": first["pot"], "ticks": ticks,
    })
}

#[test]
fn every_world_in_the_vectors_grows_the_same_log() {
    let v = vectors();
    for world in v["worlds"].as_array().unwrap() {
        let log: Value =
            serde_json::from_str(&respond(&request(world, 100).to_string()).unwrap()).unwrap();
        assert_eq!(log, world["log"], "{}", world["name"]);
    }
}

#[test]
fn ticks_bound_the_steps() {
    let v = vectors();
    let world = &v["worlds"][1];
    for ticks in [0, 1, 3] {
        let log: Value =
            serde_json::from_str(&respond(&request(world, ticks).to_string()).unwrap()).unwrap();
        let want: Vec<Value> = world["log"].as_array().unwrap()[..=ticks as usize].to_vec();
        assert_eq!(log, Value::Array(want), "{ticks} ticks");
    }
}

#[test]
fn a_field_written_twice_counts_by_its_last_value() {
    let v = vectors();
    let good = request(&v["worlds"][1], 3).to_string();
    let twice = good.replacen('{', "{\"ticks\":-1,", 1);
    assert!(twice.contains("\"ticks\":-1") && twice.contains("\"ticks\":3"));
    assert_eq!(respond(&twice).unwrap(), respond(&good).unwrap());
}

#[test]
fn what_isnt_a_request_is_refused_with_the_reason() {
    let v = vectors();
    let good = request(&v["worlds"][1], 5);
    let with = |path: &[&str], value: Value| {
        let mut r = good.clone();
        let mut at = &mut r;
        for key in &path[..path.len() - 1] {
            at = &mut at[*key];
        }
        at[path[path.len() - 1]] = value;
        r.to_string()
    };
    let without = |key: &str| {
        let mut r = good.clone();
        r.as_object_mut().unwrap().remove(key);
        r.to_string()
    };
    let cases: Vec<(String, &str)> = vec![
        ("not json".into(), "isn't JSON"),
        ("[1, 2]".into(), "isn't a JSON object"),
        (with(&["extra"], json!(1)), "exactly the fields"),
        (without("ticks"), "exactly the fields"),
        (with(&["key"], json!("did:key:nope")), "key"),
        (with(&["key"], json!(7)), "its key isn't text"),
        (with(&["template"], json!("abc")), "hash"),
        (
            with(&["dials", "water"], json!(1.5)),
            "its dial water isn't a whole number",
        ),
        (
            with(&["dials", "colour"], json!(1)),
            "its dials must be exactly",
        ),
        (with(&["dials", "maxDepth"], json!(13)), "maxDepth"),
        (with(&["dials"], json!([1, 2])), "aren't a JSON object"),
        (with(&["pot"], json!([0, 0, 10])), "four whole numbers"),
        (with(&["pot"], json!("big")), "or null"),
        (with(&["ticks"], json!(-1)), "from 0 to"),
        (with(&["ticks"], json!(MAX_TICKS + 1)), "from 0 to"),
    ];
    for (input, why) in cases {
        let refused = respond(&input).expect_err(&input);
        assert!(refused.contains(why), "{input}: {refused}");
    }
}
