// rust/acts/tests/vectors.rs
//! Who may act on a log (`acts`), checked against `vectors/acts.json`,
//! which Python writes (`python3 -m world.acts_vectors`, from
//! `world/acts.py`): the same state for every act in each room that
//! holds, the same reason and the same place for every room that is
//! refused, and the same answer for each record held to its office's
//! grant on its own.

// Tests may unwrap, expect, panic and index: a failure here is a failed
// test, not a world that crashed.
#![allow(
    clippy::unwrap_used,
    clippy::expect_used,
    clippy::panic,
    clippy::indexing_slicing
)]

use acts::{
    ACTS, MAX_CHAIN, OWN_ACTS, REASONS, RECORD, RULED, Reason, Refused, STATES, State, check,
    kinds_of_act, office_may, rules_ok,
};
use serde_json::{Map, Value, json};
use std::collections::BTreeSet;
use world_log::apart;

const VECTORS: &str = include_str!("../../../vectors/acts.json");

fn vectors() -> Value {
    serde_json::from_str(VECTORS).unwrap()
}

/// What a case is held to: its own grants or rules, or the file's.
fn given<'a>(all: &'a Value, case: &'a Value, key: &str) -> &'a Value {
    case.get(key).unwrap_or(&all[key])
}

fn words(list: &Value) -> Vec<&str> {
    list.as_array()
        .unwrap()
        .iter()
        .map(|v| v.as_str().unwrap())
        .collect()
}

fn pairs(map: &Value) -> Vec<(&str, &str)> {
    map.as_object()
        .unwrap()
        .iter()
        .map(|(k, v)| (k.as_str(), v.as_str().unwrap()))
        .collect()
}

#[test]
fn the_names_and_reasons_are_the_vectors() {
    let all = vectors();
    assert_eq!(all["record"], RECORD);
    // A map is read in the order of its keys, whatever order it was
    // written in.
    let mut acts = ACTS.to_vec();
    acts.sort_unstable();
    assert_eq!(pairs(&all["acts"]), acts);
    let mut own_acts = OWN_ACTS.to_vec();
    own_acts.sort_unstable();
    assert_eq!(pairs(&all["own_acts"]), own_acts);
    assert_eq!(words(&all["ruled"]), RULED.to_vec());
    assert_eq!(all["max_chain"], MAX_CHAIN);
    let states: Vec<&str> = STATES.iter().map(|s| s.as_str()).collect();
    assert_eq!(words(&all["states"]), states);
    let reasons: Vec<&str> = REASONS.iter().map(|r| r.as_str()).collect();
    assert_eq!(words(&all["reasons"]), reasons);
    let distinct: BTreeSet<&str> = reasons.iter().copied().collect();
    assert_eq!(distinct.len(), 24);
    assert_eq!(
        kinds_of_act(),
        [
            "keep-field-public",
            "keep-field-redacted",
            "redact-field",
            "remove-comment",
            "restore-comment"
        ]
    );
}

#[test]
fn every_one_of_the_forms_own_kinds_is_an_offices_or_an_authors() {
    let mut kinds: Vec<&str> = ACTS
        .iter()
        .chain(OWN_ACTS.iter())
        .map(|(kind, _)| *kind)
        .collect();
    kinds.sort_unstable();
    let mut own = apart::OWN.to_vec();
    own.sort_unstable();
    assert_eq!(kinds, own);
}

#[test]
fn every_room_that_holds_gives_its_states() {
    let all = vectors();
    let mut seen = BTreeSet::new();
    for case in all["holds"].as_array().unwrap() {
        let name = case["name"].as_str().unwrap();
        let got = check(
            &case["log"],
            &case["contents"],
            given(&all, case, "grants"),
            given(&all, case, "rules"),
        )
        .unwrap_or_else(|e| panic!("{name}: {e}"));
        let mut as_map = Map::new();
        for (entry, state) in &got {
            as_map.insert(entry.clone(), json!(state.as_str()));
            seen.insert(*state);
        }
        assert_eq!(Value::Object(as_map), case["states"], "{name}");
    }
    assert_eq!(seen.into_iter().collect::<Vec<State>>(), STATES.to_vec());
}

#[test]
fn every_refused_room_is_refused_for_its_reason() {
    let all = vectors();
    let mut seen = BTreeSet::new();
    for case in all["refused"].as_array().unwrap() {
        let name = case["name"].as_str().unwrap();
        let refused = check(
            &case["log"],
            &case["contents"],
            given(&all, case, "grants"),
            given(&all, case, "rules"),
        )
        .expect_err(name);
        assert!(matches!(refused, Refused::Act { .. }), "{name}: {refused}");
        assert_eq!(refused.reason(), case["reason"].as_str().unwrap(), "{name}");
        assert_eq!(
            refused.at().map(|at| at as u64),
            case["where"].as_u64(),
            "{name}"
        );
        // The form itself has nothing against the log: only who acted
        // is at fault.
        apart::check(&case["log"], &case["contents"]).expect(name);
        seen.insert(refused.reason());
    }
    let all_reasons: BTreeSet<&str> = REASONS.iter().map(|r| r.as_str()).collect();
    assert_eq!(seen, all_reasons);
}

#[test]
fn an_office_is_held_to_its_grant_on_its_own() {
    let all = vectors();
    for case in all["offices"].as_array().unwrap() {
        let name = case["name"].as_str().unwrap();
        let got = office_may(
            &case["record"],
            case["act"].as_str().unwrap(),
            &all["grants"],
            &all["rules"],
        );
        match case["reason"].as_str() {
            None => got.unwrap_or_else(|e| panic!("{name}: {e}")),
            Some(reason) => {
                let refused = got.expect_err(name);
                assert_eq!(refused.reason(), reason, "{name}");
                assert_eq!(refused.at(), None, "{name}");
            }
        }
    }
}

#[test]
fn a_log_that_does_not_hold_is_the_forms_to_refuse() {
    let all = vectors();
    let case = &all["holds"][1];
    let mut log = case["log"].clone();
    log[3]["tick"] = json!(9);
    let refused = check(&log, &case["contents"], &all["grants"], &all["rules"]).unwrap_err();
    assert!(matches!(refused, Refused::Log(_)), "{refused}");
    assert_eq!(refused.reason(), "the chain does not hold");
    assert_eq!(refused.at(), None);
}

#[test]
fn what_is_given_must_be_rules_and_a_list_of_grants() {
    let all = vectors();
    let case = &all["holds"][0];
    let rules = &all["rules"];
    assert!(rules_ok(rules));
    for odd in [json!(null), json!({}), json!("grants"), json!(5)] {
        let refused = check(&case["log"], &case["contents"], &odd, rules).unwrap_err();
        assert_eq!(
            refused,
            Refused::Act {
                reason: Reason::Rules,
                at: None
            }
        );
    }
    let mut no_room = rules.clone();
    no_room["room"] = json!(null);
    let mut own = rules.clone();
    own["authors"][apart::REMOVED] = json!("key");
    let mut capital = rules.clone();
    capital["authors"]["said"] = json!("Key");
    for odd in [
        json!(null),
        json!([]),
        json!("rules"),
        json!({}),
        no_room,
        own,
        capital,
    ] {
        assert!(!rules_ok(&odd), "{odd}");
        let refused = check(&case["log"], &case["contents"], &all["grants"], &odd).unwrap_err();
        assert_eq!(refused.reason(), Reason::Rules.as_str(), "{odd}");
    }
    for kind in RULED {
        let mut on_own = rules.clone();
        on_own["on"][kind] = json!([apart::MARK]);
        assert!(!rules_ok(&on_own), "{kind}");
    }
}

#[test]
fn what_can_not_be_a_record_among_the_grants_is_passed_over() {
    let all = vectors();
    let case = &all["holds"][1];
    let mut more = all["grants"].as_array().unwrap().clone();
    more.extend([
        json!(null),
        json!(5),
        json!("a grant"),
        json!([]),
        json!({"format": 1}),
        json!({"a": 1.5}),
    ]);
    let with = check(
        &case["log"],
        &case["contents"],
        &Value::Array(more),
        &all["rules"],
    )
    .unwrap();
    let without = check(
        &case["log"],
        &case["contents"],
        &all["grants"],
        &all["rules"],
    )
    .unwrap();
    assert_eq!(with, without);
}

#[test]
fn a_record_changed_in_the_contents_is_no_longer_held() {
    // The contents are held to the log by the fingerprint, so a changed
    // record is the form's to refuse, before any act is looked at.
    let all = vectors();
    let case = &all["holds"][4];
    let log = case["log"].as_array().unwrap();
    let removal = log.last().unwrap()["hash"].as_str().unwrap();
    let mut contents = case["contents"].clone();
    contents[removal][RECORD][1]["reasons"] = json!("Changed.");
    let refused = check(
        &case["log"],
        &contents,
        given(&all, case, "grants"),
        &all["rules"],
    )
    .unwrap_err();
    assert!(matches!(refused, Refused::Log(_)), "{refused}");
}
