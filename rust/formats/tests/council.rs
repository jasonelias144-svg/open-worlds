// rust/formats/tests/council.rs
//! A council's count, checked against `vectors/formats/council-v1.json`,
//! which the Python `formats/council_vectors.py` writes: the same counts,
//! the same outcome, the same votes counted, and the same problems, word
//! for word; and proposals that hold or are refused as stated.

// Tests may unwrap, expect, panic and index: a failure here is a failed
// test, which is what it should be.
#![allow(
    clippy::unwrap_used,
    clippy::expect_used,
    clippy::panic,
    clippy::indexing_slicing
)]

use formats::council::{Tally, tally};
use formats::records::check;
use serde_json::{Value, json};

fn vectors() -> Value {
    let path = concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../vectors/formats/council-v1.json"
    );
    serde_json::from_str(&std::fs::read_to_string(path).unwrap()).unwrap()
}

fn as_json(t: &Tally) -> Value {
    json!({
        "counts": t.counts,
        "persons": t.persons,
        "outcome": t.outcome,
        "counted": t.counted,
        "problems": t.problems,
    })
}

fn list(v: &Value) -> Vec<Value> {
    v.as_array().unwrap().clone()
}

#[test]
fn each_case_gives_the_same_count_as_pythons() {
    let v = vectors();
    let cases = v["cases"].as_array().unwrap();
    assert!(cases.len() >= 8);
    for case in cases {
        let proposal = case.get("proposal").unwrap_or(&v["proposal"]);
        let got = tally(proposal, &list(&case["votes"]), &list(&case["births"]));
        assert_eq!(as_json(&got), case["tally"], "{}", case["name"]);
    }
}

#[test]
fn each_proposal_holds_or_is_refused_as_stated() {
    let v = vectors();
    for case in v["proposals"].as_array().unwrap() {
        assert_eq!(
            check(&case["record"]).is_ok(),
            case["holds"].as_bool().unwrap(),
            "{}",
            case["name"]
        );
    }
}

#[test]
fn it_never_fails_on_what_it_is_given() {
    let v = vectors();
    let junk = vec![
        Value::Null,
        json!(5),
        json!("a vote"),
        json!([]),
        json!({}),
        json!({ "format": "open-worlds/vote/v1" }),
    ];
    for proposal in [Value::Null, json!({}), v["proposal"].clone()] {
        let t = tally(&proposal, &junk, &junk);
        assert_eq!(t.persons, 0);
        assert_eq!(t.outcome, None);
    }
}
