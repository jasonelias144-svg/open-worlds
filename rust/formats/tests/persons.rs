// rust/formats/tests/persons.rs
//! Persons, checked against `vectors/formats/persons-v1.json`, which the
//! Python `formats/persons_vectors.py` writes: the same presence keys from
//! the same seed, the same links holding or not, and the same problems in
//! the histories of a person's list.

// Tests may unwrap, expect, panic and index: a failure here is a failed
// test, which is what it should be.
#![allow(
    clippy::unwrap_used,
    clippy::expect_used,
    clippy::panic,
    clippy::indexing_slicing
)]

use formats::persons::{
    link_problems, person_list_chain_problems, presence_info, presence_key, presence_secret,
    seed_problems,
};
use hkdf::Hkdf;
use serde_json::Value;
use sha2::Sha256;

fn vectors() -> Value {
    let path = concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../vectors/formats/persons-v1.json"
    );
    serde_json::from_str(&std::fs::read_to_string(path).unwrap()).unwrap()
}

fn hex(text: &str) -> Vec<u8> {
    (0..text.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&text[i..i + 2], 16).unwrap())
        .collect()
}

fn to_hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

fn seed(v: &Value) -> [u8; 32] {
    hex(v["seed"]["hex"].as_str().unwrap()).try_into().unwrap()
}

fn strings(v: &Value) -> Vec<String> {
    v.as_array()
        .unwrap()
        .iter()
        .map(|s| s.as_str().unwrap().to_owned())
        .collect()
}

#[test]
fn hkdf_gives_rfc_5869s_first_test_case() {
    let v = vectors();
    let case = &v["hkdf"];
    let mut okm = vec![0_u8; usize::try_from(case["length"].as_u64().unwrap()).unwrap()];
    Hkdf::<Sha256>::new(
        Some(&hex(case["salt"].as_str().unwrap())),
        &hex(case["ikm"].as_str().unwrap()),
    )
    .expand(&hex(case["info"].as_str().unwrap()), &mut okm)
    .unwrap();
    assert_eq!(to_hex(&okm), case["okm"].as_str().unwrap());
}

#[test]
fn each_presence_has_its_info_and_its_key() {
    let v = vectors();
    let seed = seed(&v);
    let presences = v["presences"].as_array().unwrap();
    assert!(!presences.is_empty());
    for p in presences {
        let world = p["world"].as_str().unwrap();
        let counter = u32::try_from(p["counter"].as_u64().unwrap()).unwrap();
        assert_eq!(
            to_hex(&presence_info(world, counter).unwrap()),
            p["info"].as_str().unwrap()
        );
        assert_eq!(
            presence_key(&seed, world, counter).unwrap(),
            p["key"].as_str().unwrap()
        );
    }
}

#[test]
fn what_cant_be_a_presence_is_refused() {
    let v = vectors();
    let cases = v["refusedDerivations"].as_array().unwrap();
    assert!(!cases.is_empty());
    for case in cases {
        let name = case["name"].as_str().unwrap();
        // A seed that isn't 32 bytes, or a counter that isn't four bytes,
        // can't even be given: the types refuse them.
        let seed: Option<[u8; 32]> = hex(case["seed"].as_str().unwrap()).try_into().ok();
        let counter = case["counter"].as_i64().and_then(|c| u32::try_from(c).ok());
        let refused = match (seed, counter) {
            (Some(seed), Some(counter)) => {
                presence_secret(&seed, case["world"].as_str().unwrap(), counter).is_err()
            }
            _ => true,
        };
        assert!(refused, "not refused: {name}");
    }
}

#[test]
fn each_link_holds_or_not_as_stated() {
    let v = vectors();
    let links = v["links"].as_array().unwrap();
    assert!(links.iter().any(|l| l["linked"] == true));
    assert!(links.iter().any(|l| l["linked"] == false));
    for link in links {
        let name = link["name"].as_str().unwrap();
        let found = link_problems(&link["holds"], &link["heldBy"]);
        assert_eq!(
            found.is_empty(),
            link["linked"].as_bool().unwrap(),
            "{name}: {found:?}"
        );
        // Where both halves hold as records, the reasons are Python's,
        // word for word; a record's own refusal is worded by each language.
        let python = strings(&link["problems"]);
        if !python
            .iter()
            .any(|p| p.starts_with("holds:") || p.starts_with("held-by:"))
        {
            assert_eq!(found, python, "{name}");
        }
    }
}

#[test]
fn each_history_of_a_person_list_has_the_same_problems() {
    let v = vectors();
    let lists = &v["personLists"];
    let by = |name: &Value| {
        lists["versions"]
            .as_array()
            .unwrap()
            .iter()
            .find(|r| r["name"] == *name)
            .map(|r| r["record"].clone())
            .unwrap()
    };
    let histories = lists["histories"].as_array().unwrap();
    assert!(!histories.is_empty());
    for case in histories {
        let versions: Vec<Value> = case["versions"]
            .as_array()
            .unwrap()
            .iter()
            .map(by)
            .collect();
        assert_eq!(
            person_list_chain_problems(&versions),
            strings(&case["problems"]),
            "{}",
            case["name"]
        );
    }
    for case in lists["seedChecks"].as_array().unwrap() {
        let record = match case.get("record") {
            Some(record) => record.clone(),
            None => by(&case["version"]),
        };
        assert_eq!(
            seed_problems(&record, &seed(&v)),
            strings(&case["problems"]),
            "{}",
            case["name"]
        );
    }
}
