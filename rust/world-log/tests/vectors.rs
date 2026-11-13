// rust/world-log/tests/vectors.rs
//! The crate checked against the shared test vectors in `vectors/`, which
//! the Python kernel writes (`python3 -m world.vectors`): the same text and
//! the same hashes, and a log that holds here exactly when it holds there.

// Tests may unwrap, expect, panic and index: a failure here is a failed
// test, not a world that crashed.
#![allow(
    clippy::unwrap_used,
    clippy::expect_used,
    clippy::panic,
    clippy::indexing_slicing
)]

use serde_json::{Value, json};
use world_log::{Error, GENESIS, LogError, digest, python_json, verify_log};

const DIGESTS: &str = include_str!("../../../vectors/digests.json");
const LOG: &str = include_str!("../../../vectors/world-log.json");

fn log() -> Vec<Value> {
    serde_json::from_str(LOG).unwrap()
}

fn verify(entries: &[Value]) -> Result<String, LogError> {
    verify_log(&Value::Array(entries.to_vec())).map(str::to_owned)
}

#[test]
fn every_text_and_hash_matches_python() {
    let vectors: Vec<Value> = serde_json::from_str(DIGESTS).unwrap();
    assert!(vectors.len() >= 18, "the vectors are all there");
    for v in &vectors {
        let body = &v["body"];
        assert_eq!(python_json(body).unwrap(), v["text"].as_str().unwrap());
        assert_eq!(digest(body).unwrap(), v["hash"].as_str().unwrap());
    }
}

#[test]
fn a_log_the_python_kernel_wrote_holds() {
    let entries = log();
    let head = entries.last().unwrap()["hash"].as_str().unwrap();
    assert_eq!(verify(&entries).unwrap(), head);
    // The run writes every kind of entry the kernel has.
    let kinds: Vec<&str> = entries
        .iter()
        .map(|e| e["kind"].as_str().unwrap())
        .collect();
    for kind in [
        "world_created",
        "entered",
        "moved",
        "blocked",
        "said",
        "invalid_action",
        "agent_error",
        "exited",
    ] {
        assert!(kinds.contains(&kind), "{kind} is in the run");
    }
}

#[test]
fn each_entry_hashes_its_body() {
    for entry in log() {
        let mut body = entry.as_object().unwrap().clone();
        let hash = body.remove("hash").unwrap();
        assert_eq!(
            digest(&Value::Object(body)).unwrap(),
            hash.as_str().unwrap()
        );
    }
}

#[test]
fn any_change_to_any_field_of_any_entry_is_caught() {
    let entries = log();
    for index in 0..entries.len() {
        let changes: [(&str, Value); 7] = [
            ("tick", json!(entries[index]["tick"].as_u64().unwrap() + 1)),
            ("kind", json!("rewritten")),
            ("agent", json!("someone else")),
            ("data", json!({"changed": true})),
            ("prev", json!(entries[entries.len() - 1 - index]["hash"])),
            ("hash", json!(GENESIS)),
            ("extra", json!("a field the kernel never wrote")),
        ];
        for (field, value) in changes {
            let mut changed = entries.clone();
            if changed[index].get(field) == Some(&value) {
                continue; // not a change for this entry
            }
            changed[index][field] = value;
            assert!(verify(&changed).is_err(), "entry {index}, field {field}");
        }
        for field in ["tick", "kind", "agent", "data", "prev", "hash"] {
            let mut changed = entries.clone();
            changed[index].as_object_mut().unwrap().remove(field);
            assert!(verify(&changed).is_err(), "entry {index}, {field} removed");
        }
    }
}

#[test]
fn removed_moved_or_repeated_entries_are_caught() {
    let entries = log();
    for index in 0..entries.len() - 1 {
        let mut removed = entries.clone();
        removed.remove(index);
        assert_eq!(
            verify(&removed),
            Err(LogError::BrokenChain { index }),
            "entry {index} removed"
        );
        let mut swapped = entries.clone();
        swapped.swap(index, index + 1);
        assert!(
            verify(&swapped).is_err(),
            "entries {index} and next swapped"
        );
        let mut repeated = entries.clone();
        repeated.insert(index, entries[index].clone());
        assert!(verify(&repeated).is_err(), "entry {index} repeated");
    }
}

#[test]
fn a_log_cut_short_still_holds_so_compare_its_head() {
    // The limit in the crate's documentation, shown: only the head says
    // whether a log is whole.
    let entries = log();
    let cut = &entries[..entries.len() - 3];
    let head = verify(cut).unwrap();
    assert_eq!(head, cut.last().unwrap()["hash"].as_str().unwrap());
    assert_ne!(head, entries.last().unwrap()["hash"].as_str().unwrap());
}

#[test]
fn the_shape_of_a_log_is_checked() {
    assert_eq!(verify(&[]), Ok(GENESIS.to_owned()));
    assert_eq!(
        verify_log(&json!({"not": "a list"})),
        Err(LogError::NotAList)
    );
    let mut entries = log();
    entries[2] = json!("not an object");
    assert_eq!(verify(&entries), Err(LogError::Malformed { index: 2 }));
    let mut entries = log();
    entries[0]["hash"] = json!(12);
    assert_eq!(verify(&entries), Err(LogError::Malformed { index: 0 }));
}

#[test]
fn a_float_is_refused_not_guessed() {
    let mut entries = log();
    entries[1]["data"] = json!({"pos": [0.5, 0]});
    assert_eq!(
        verify(&entries),
        Err(LogError::Unwritable {
            index: 1,
            error: Error::Number("0.5".into())
        })
    );
}

#[test]
fn text_with_a_lone_surrogate_cannot_be_read() {
    // Python can write this, and Rust can't hold it: the kernel now keeps
    // such text out of its log (world/core.py, _is_unicode).
    assert!(serde_json::from_str::<Value>(r#""\ud800""#).is_err());
    assert!(serde_json::from_str::<Value>(r#""\ud83d\ude42""#).is_ok());
}
