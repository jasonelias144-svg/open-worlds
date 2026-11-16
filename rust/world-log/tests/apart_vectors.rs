// rust/world-log/tests/apart_vectors.rs
//! A log whose fields are kept apart (`world_log::apart`), checked
//! against `vectors/log-apart.json`, which Python writes
//! (`python3 -m world.vectors`, from `world/apart.py`): the same
//! fingerprints, the same states, the same joined entries, and the same
//! reason for every log and contents that must be refused.

// Tests may unwrap, expect, panic and index: a failure here is a failed
// test, not a world that crashed.
#![allow(
    clippy::unwrap_used,
    clippy::expect_used,
    clippy::panic,
    clippy::indexing_slicing
)]

use serde_json::{Map, Value, json};
use std::collections::BTreeSet;
use world_log::apart::{
    self, EntryState, FORM, GROUNDS, KEPT, Log, MARK, MAX_NESTING, MAX_WHOLE, PUT_BACK, REMOVED,
    RESTORED, Refused, SHORT, State, TAKEN_BACK, check, fingerprint, fingerprint_text, incidents,
    join, short_ids, value_allowed,
};
use world_log::{LogError, sha256_hex, verify_log};

const VECTORS: &str = include_str!("../../../vectors/log-apart.json");

fn vectors() -> Value {
    serde_json::from_str(VECTORS).unwrap()
}

fn cases(v: &Value, key: &str) -> Vec<Value> {
    v[key].as_array().unwrap().clone()
}

/// The n-th trial salt, as `world/apart_vectors.py` makes it.
fn trial_salt(n: usize) -> String {
    sha256_hex(format!("open-worlds trial salt {n}").as_bytes())[..32].to_owned()
}

/// Trial salts in order, from the first.
fn trial_salts() -> impl FnMut() -> String {
    let mut n = 0;
    move || {
        n += 1;
        trial_salt(n - 1)
    }
}

fn states_json(states: &apart::States) -> Value {
    let mut out = Map::new();
    for (entry, fields) in states {
        let fields: Map<String, Value> = fields
            .iter()
            .map(|(name, state)| (name.clone(), json!(state.as_str())))
            .collect();
        out.insert(entry.clone(), Value::Object(fields));
    }
    Value::Object(out)
}

fn incidents_json(standing: &std::collections::BTreeMap<String, apart::Standing>) -> Value {
    let mut out = Map::new();
    for (entry, its) in standing {
        let list: Vec<Value> = its
            .incidents
            .iter()
            .map(|i| {
                json!({"id": i.id, "short": i.short, "kind": i.kind.as_str(),
                       "stands": i.stands})
            })
            .collect();
        out.insert(
            entry.clone(),
            json!({"state": its.state.as_str(), "incidents": list}),
        );
    }
    Value::Object(out)
}

fn map(value: &Value) -> Map<String, Value> {
    value.as_object().unwrap().clone()
}

/// Where a refusal points, as the vectors write it: nothing; an entry's
/// place in the log; or, in the contents, an entry's hash alone or with
/// a field's name.
fn place(error: &Refused) -> Value {
    match error {
        Refused::Chain(LogError::NotAList)
        | Refused::NoForm
        | Refused::Table
        | Refused::FirstGiven
        | Refused::Entry { index: None } => Value::Null,
        Refused::Chain(
            LogError::Malformed { index }
            | LogError::BrokenChain { index }
            | LogError::WrongHash { index }
            | LogError::Unwritable { index, .. },
        )
        | Refused::Entry { index: Some(index) }
        | Refused::Untabled { index }
        | Refused::Open { index }
        | Refused::Twice { index }
        | Refused::BadMark { index }
        | Refused::BadKept { index }
        | Refused::BadRemoval { index }
        | Refused::BadRestoring { index }
        | Refused::BadTakingBack { index }
        | Refused::BadPuttingBack { index } => json!(index),
        Refused::Contents(p)
        | Refused::Unknown(p)
        | Refused::Salt(p)
        | Refused::SaltTwice(p)
        | Refused::Value(p)
        | Refused::Fingerprint(p) => match (&p.entry, &p.field) {
            (Some(entry), Some(field)) => json!([entry, field]),
            (Some(entry), None) => json!([entry]),
            _ => Value::Null,
        },
    }
}

/// The trial room of the vectors, written again here.
fn room(v: &Value, salt: &mut dyn FnMut() -> String) -> Log {
    let mut log = Log::new(&v["table"], &map(&v["first"]), "world_created", salt).unwrap();
    for step in cases(v, "written") {
        log.append(
            step["tick"].as_u64().unwrap(),
            step["kind"].as_str().unwrap(),
            step["agent"].as_str(),
            &map(&step["data"]),
            &map(&step["apart"]),
            salt,
        )
        .unwrap();
    }
    log
}

#[test]
fn the_names_and_limits_are_pythons() {
    let v = vectors();
    assert_eq!(v["form"], FORM);
    assert_eq!(v["mark"], MARK);
    assert_eq!(v["kept"], KEPT);
    assert_eq!(v["max_whole"], MAX_WHOLE);
    assert_eq!(v["max_nesting"], MAX_NESTING);
    assert_eq!(v["removed"], REMOVED);
    assert_eq!(v["restored"], RESTORED);
    assert_eq!(v["taken_back"], TAKEN_BACK);
    assert_eq!(v["put_back"], PUT_BACK);
    assert_eq!(v["grounds"], json!(GROUNDS));
    assert_eq!(v["short"], SHORT);
    let entry_states: Vec<&str> = [
        EntryState::AsWritten,
        EntryState::Removed,
        EntryState::TakenBack,
        EntryState::Restored,
    ]
    .iter()
    .map(|s| s.as_str())
    .collect();
    assert_eq!(v["entry_states"], json!(entry_states));
    let states: Vec<&str> = [
        State::Present,
        State::Redacted,
        State::Unfinished,
        State::KeptPublic,
        State::Missing,
    ]
    .iter()
    .map(|s| s.as_str())
    .collect();
    assert_eq!(v["states"], json!(states));
}

#[test]
fn every_fingerprint_and_its_text_match_python() {
    let v = vectors();
    let prints = cases(&v, "fingerprints");
    assert!(prints.len() >= 18, "the vectors are all there");
    for (n, case) in prints.iter().enumerate() {
        let salt = case["salt"].as_str().unwrap();
        let name = case["name"].as_str().unwrap();
        assert_eq!(salt, trial_salt(n), "trial salt {n}");
        assert!(value_allowed(&case["value"]), "{}", case["text"]);
        assert_eq!(
            fingerprint_text(salt, name, &case["value"]).unwrap(),
            case["text"].as_str().unwrap()
        );
        assert_eq!(
            fingerprint(salt, name, &case["value"]).unwrap(),
            case["fingerprint"].as_str().unwrap()
        );
    }
}

#[test]
fn the_values_python_refuses_are_refused() {
    let v = vectors();
    let refused = cases(&v, "values_refused");
    assert!(refused.len() >= 9, "the vectors are all there");
    for case in refused {
        assert!(!value_allowed(&case["value"]), "{}", case["name"]);
        assert_eq!(
            fingerprint(&trial_salt(0), "thing", &case["value"]),
            Err(Refused::Value(apart::Place::default())),
            "{}",
            case["name"]
        );
    }
}

#[test]
fn nesting_stops_at_the_limit() {
    for wrap in [
        (|v: Value| json!([v])) as fn(Value) -> Value,
        |v: Value| json!({"k": v}),
    ] {
        let mut value = json!(0);
        for _ in 0..MAX_NESTING {
            value = wrap(value);
        }
        assert!(value_allowed(&value));
        assert!(!value_allowed(&wrap(value)));
    }
    assert!(value_allowed(&json!(MAX_WHOLE)));
    assert!(value_allowed(&json!(-MAX_WHOLE)));
    assert!(!value_allowed(&json!(MAX_WHOLE + 1)));
    assert!(!value_allowed(&json!(-MAX_WHOLE - 1)));
    assert!(!value_allowed(&json!(u64::MAX)));
    assert!(!value_allowed(&json!(0.0)));
    // The limit in the module's documentation, shown: Python reads -0 as
    // the whole number 0.
    let minus_zero: Value = serde_json::from_str("-0").unwrap();
    assert!(!value_allowed(&minus_zero));
}

#[test]
fn a_bad_salt_or_name_is_refused() {
    let good = trial_salt(0);
    for salt in ["", &good[..31], &format!("{good}0"), &good.to_uppercase()] {
        assert_eq!(
            fingerprint(salt, "text", &json!("v")).unwrap_err().reason(),
            "a salt is not 32 lowercase hex digits",
            "{salt:?}"
        );
    }
    let long = "k".repeat(65);
    for name in [
        "",
        "Text",
        "1st",
        "a-b",
        "a b",
        "text\n",
        "caf\u{e9}",
        &long,
    ] {
        assert_eq!(
            fingerprint(&good, name, &json!("v")).unwrap_err().reason(),
            "an entry is not in this form",
            "{name:?}"
        );
    }
    assert!(fingerprint(&good, &"k".repeat(64), &json!("v")).is_ok());
    assert!(fingerprint(&good, "a_1", &json!("v")).is_ok());
}

#[test]
fn the_trial_room_written_here_is_the_one_python_wrote() {
    let v = vectors();
    let (entries, contents) = room(&v, &mut trial_salts()).into_parts();
    let first = &v["holds"][0];
    assert_eq!(first["name"], "every field is there");
    assert_eq!(Value::Array(entries), first["log"]);
    assert_eq!(Value::Object(contents), first["contents"]);
}

#[test]
fn each_case_that_holds_gives_pythons_states_and_entries() {
    let v = vectors();
    let holds = cases(&v, "holds");
    assert_eq!(holds.len(), 6, "the vectors are all there");
    let mut seen = BTreeSet::new();
    let mut entry_states = BTreeSet::new();
    for case in holds {
        let name = &case["name"];
        assert!(verify_log(&case["log"]).is_ok(), "{name}");
        let states = check(&case["log"], &case["contents"]).unwrap();
        assert_eq!(states_json(&states), case["states"], "{name}");
        let standing = incidents(&case["log"]).unwrap();
        assert_eq!(incidents_json(&standing), case["incidents"], "{name}");
        entry_states.extend(standing.values().map(|s| s.state));
        let joined = join(&case["log"], &case["contents"]).unwrap();
        assert_eq!(Value::Array(joined), case["joined"], "{name}");
        seen.extend(states.values().flat_map(|fields| fields.values().copied()));
    }
    assert_eq!(seen.len(), 5, "every state is in the vectors");
    // Removed, taken back, and as written with an incident that no longer
    // stands; "restored" is in the writer's test below.
    assert_eq!(entry_states.len(), 3, "the entries' states are there");
}

#[test]
fn an_incidents_id_is_shown_as_short_as_is_still_its_own() {
    let v = vectors();
    let groups = cases(&v, "short_ids");
    assert_eq!(groups.len(), 5, "the vectors are all there");
    for group in groups {
        let ids: Vec<String> = group["ids"]
            .as_array()
            .unwrap()
            .iter()
            .map(|id| id.as_str().unwrap().to_owned())
            .collect();
        let short: Map<String, Value> = short_ids(&ids)
            .into_iter()
            .map(|(id, short)| (id, json!(short)))
            .collect();
        assert_eq!(Value::Object(short), group["short"]);
    }
}

#[test]
fn what_wins_among_removing_restoring_taking_back_and_putting_back() {
    // The table in docs/research/REDACTION.md, decision 9, through the
    // writer: each refused act leaves the log as it was.
    let v = vectors();
    let mut salt = trial_salts();
    let mut log = room(&v, &mut salt);
    let said = log.entries()[3]["hash"].as_str().unwrap().to_owned();
    let ground = json!({"kind": "law", "ref": "trial room law, part 3"});
    let decision = "ab".repeat(32);
    let office = |name: &str, key: &str, target: &str| {
        map(&json!({key: target, "office": name, "ground": ground, "decision": decision}))
    };
    let none = Map::new();
    let state = |log: &Log| {
        incidents(&Value::Array(log.entries().to_vec()))
            .unwrap()
            .get(&said)
            .map_or(EntryState::AsWritten, |s| s.state)
    };
    assert_eq!(state(&log), EntryState::AsWritten);
    // A restoring of what is not removed.
    let error = log
        .append(
            5,
            RESTORED,
            None,
            &office("keeper", "incident", &said),
            &none,
            &mut salt,
        )
        .unwrap_err();
    assert_eq!(error, Refused::BadRestoring { index: 7 });
    // Removed; a second removal is refused.
    let removal = log
        .append(
            5,
            REMOVED,
            None,
            &office("moderator", "entry", &said),
            &none,
            &mut salt,
        )
        .unwrap();
    assert_eq!(state(&log), EntryState::Removed);
    let error = log
        .append(
            5,
            REMOVED,
            None,
            &office("moderator", "entry", &said),
            &none,
            &mut salt,
        )
        .unwrap_err();
    assert_eq!(error, Refused::BadRemoval { index: 8 });
    // The author takes it back; the office can no longer restore it.
    let taking = log
        .append(
            6,
            TAKEN_BACK,
            None,
            &map(&json!({"entry": said})),
            &none,
            &mut salt,
        )
        .unwrap();
    assert_eq!(state(&log), EntryState::TakenBack);
    let error = log
        .append(
            6,
            RESTORED,
            None,
            &office("keeper", "incident", &removal),
            &none,
            &mut salt,
        )
        .unwrap_err();
    assert_eq!(error, Refused::BadRestoring { index: 9 });
    let error = log
        .append(
            6,
            TAKEN_BACK,
            None,
            &map(&json!({"entry": said})),
            &none,
            &mut salt,
        )
        .unwrap_err();
    assert_eq!(error, Refused::BadTakingBack { index: 9 });
    // Put back: the removal still stands. Then restored.
    log.append(
        7,
        PUT_BACK,
        None,
        &map(&json!({"taken_back": taking})),
        &none,
        &mut salt,
    )
    .unwrap();
    assert_eq!(state(&log), EntryState::Removed);
    let error = log
        .append(
            7,
            PUT_BACK,
            None,
            &map(&json!({"taken_back": taking})),
            &none,
            &mut salt,
        )
        .unwrap_err();
    assert_eq!(error, Refused::BadPuttingBack { index: 10 });
    log.append(
        8,
        RESTORED,
        None,
        &office("keeper", "incident", &removal),
        &none,
        &mut salt,
    )
    .unwrap();
    assert_eq!(state(&log), EntryState::Restored);
    // A removal after a restoring is a new incident, with a new id.
    let again = log
        .append(
            9,
            REMOVED,
            None,
            &office("moderator", "entry", &said),
            &none,
            &mut salt,
        )
        .unwrap();
    assert_ne!(again, removal);
    // The form's own entries can't be removed or taken back.
    for own in [&removal, &taking] {
        assert_eq!(
            log.append(
                9,
                REMOVED,
                None,
                &office("moderator", "entry", own),
                &none,
                &mut salt
            )
            .unwrap_err(),
            Refused::BadRemoval { index: 12 }
        );
        assert_eq!(
            log.append(
                9,
                TAKEN_BACK,
                None,
                &map(&json!({"entry": own})),
                &none,
                &mut salt
            )
            .unwrap_err(),
            Refused::BadTakingBack { index: 12 }
        );
    }
    assert_eq!(log.entries().len(), 12);
    // Nothing left the record: the entry is given whole, with its state.
    let (entries, contents) = log.into_parts();
    let joined = join(&Value::Array(entries), &Value::Object(contents)).unwrap();
    assert_eq!(joined[3]["data"]["text"], "hello, room");
    assert_eq!(joined[3]["state"], "removed");
    let its = joined[3]["incidents"].as_array().unwrap();
    assert_eq!(its.len(), 3);
    assert_eq!(its[0]["id"], json!(removal));
    assert_eq!(its[0]["stands"], false);
    assert_eq!(its[1]["kind"], "taken back");
    assert_eq!(its[2]["stands"], true);
    assert_eq!(joined[4]["state"], "as written");
    assert_eq!(joined[4]["incidents"], json!([]));
}

#[test]
fn each_case_that_is_refused_is_refused_for_pythons_reason() {
    let v = vectors();
    let refused = cases(&v, "refused");
    assert_eq!(refused.len(), 121, "the vectors are all there");
    let mut seen = BTreeSet::new();
    for case in refused {
        let name = &case["name"];
        let reason = case["reason"].as_str().unwrap();
        let error = check(&case["log"], &case["contents"]).expect_err(&name.to_string());
        assert_eq!(error.reason(), reason, "{name}");
        assert_eq!(
            join(&case["log"], &case["contents"]).unwrap_err(),
            error,
            "{name}"
        );
        assert_eq!(place(&error), case["where"], "{name}");
        // Only the chain's own cases break the chain: every other log is
        // refused for what it says, never for a hash. (The cases with two
        // faults are left out: some break the chain as their second.) A
        // log holding a number this crate can't write is one the kernel's
        // own check can't judge here; the form's check names its entry.
        if !name.as_str().unwrap().starts_with("two faults") {
            match verify_log(&case["log"]) {
                Err(LogError::Unwritable { index, .. }) => {
                    assert_eq!(error, Refused::Entry { index: Some(index) }, "{name}");
                }
                held => assert_eq!(held.is_ok(), !matches!(error, Refused::Chain(_)), "{name}"),
            }
        }
        assert!(error.to_string().starts_with(reason), "{name}");
        seen.insert(reason.to_owned());
    }
    let reasons: BTreeSet<String> = v["reasons"]
        .as_array()
        .unwrap()
        .iter()
        .map(|r| r.as_str().unwrap().to_owned())
        .collect();
    assert_eq!(seen, reasons, "every reason is in the vectors");
}

#[test]
fn the_log_is_the_same_whatever_is_taken_out() {
    let v = vectors();
    let (entries, contents) = room(&v, &mut trial_salts()).into_parts();
    let log = Value::Array(entries);
    let mut emptied = contents.clone();
    for fields in emptied.values_mut() {
        *fields = json!({});
    }
    assert!(verify_log(&log).is_ok());
    let states = check(&log, &Value::Object(emptied)).unwrap();
    assert!(
        states
            .values()
            .flat_map(|fields| fields.values())
            .all(|state| *state == State::Missing)
    );
    // No value kept apart, and no salt, is anywhere in the log itself.
    let text = log.to_string();
    for fields in contents.values() {
        for pair in fields.as_object().unwrap().values() {
            assert!(!text.contains(pair[0].as_str().unwrap()));
            if let Some(value) = pair[1].as_str() {
                assert!(!text.contains(&json!(value).to_string()), "{value}");
            }
        }
    }
}

#[test]
fn a_refused_entry_is_not_appended_and_the_log_goes_on() {
    let v = vectors();
    let mut salt = trial_salts();
    let mut log = room(&v, &mut salt);
    let before = (log.entries().to_vec(), log.contents().clone());
    let head = log.head().to_owned();
    let refusals: [(&str, Value, Value, &str); 7] = [
        (
            "said",
            json!({}),
            json!({"name": "ada"}),
            "a field is kept apart that the table does not name",
        ),
        (
            "said",
            json!({"text": "open"}),
            json!({}),
            "a field the table keeps apart is in the open",
        ),
        (
            "said",
            json!({}),
            json!({"text": 1.5}),
            "a value is not one a fingerprint allows",
        ),
        (
            "said",
            json!({}),
            json!({"Text": "x"}),
            "an entry is not in this form",
        ),
        (
            MARK,
            json!({"entry": head, "field": "nothing"}),
            json!({}),
            "a mark does not name an earlier entry and a field it keeps apart",
        ),
        (
            MARK,
            json!({"entry": head, "field": "nothing"}),
            json!({"reason": "kept apart, and still refused"}),
            "a mark does not name an earlier entry and a field it keeps apart",
        ),
        (
            KEPT,
            json!({"mark": head}),
            json!({}),
            "a decision to keep a field public does not name an earlier mark",
        ),
    ];
    for (kind, data, kept, reason) in refusals {
        let error = log
            .append(9, kind, None, &map(&data), &map(&kept), &mut salt)
            .unwrap_err();
        assert_eq!(error.reason(), reason);
        assert_eq!(log.entries(), before.0.as_slice(), "{reason}");
        assert_eq!(log.contents(), &before.1, "{reason}");
        assert_eq!(log.head(), head, "{reason}");
    }
    // The log still takes an entry, and still holds.
    let target = before.0[3]["hash"].as_str().unwrap();
    let mark = log
        .append(
            9,
            MARK,
            Some("trial office"),
            &map(&json!({"entry": target, "field": "text"})),
            &map(&json!({"reason": "asked"})),
            &mut salt,
        )
        .unwrap();
    assert_eq!(log.head(), mark);
    let (entries, contents) = log.into_parts();
    let states = check(
        &Value::Array(entries.clone()),
        &Value::Object(contents.clone()),
    )
    .unwrap();
    assert_eq!(states[target]["text"], State::Unfinished);
    assert_eq!(states[&mark]["reason"], State::Present);
    // A field under a standing mark is never shown, though it is still
    // in the contents.
    let joined = join(&Value::Array(entries), &Value::Object(contents.clone())).unwrap();
    assert!(contents[target].get("text").is_some());
    assert!(joined[3]["data"].get("text").is_none());
    assert_eq!(joined[3]["fields"]["text"], "unfinished");
}

#[test]
fn a_salt_source_that_repeats_or_is_wrong_is_refused() {
    let table = json!({"said": ["key", "text"]});
    let mut same = || "0".repeat(32);
    let mut log = Log::new(&table, &Map::new(), "world_created", &mut same).unwrap();
    let two = map(&json!({"key": "k", "text": "t"}));
    assert_eq!(
        log.append(1, "said", None, &Map::new(), &two, &mut same)
            .unwrap_err()
            .reason(),
        "a salt appears twice"
    );
    let one = map(&json!({"text": "t"}));
    log.append(1, "said", None, &Map::new(), &one, &mut same)
        .unwrap();
    assert_eq!(
        log.append(2, "said", None, &Map::new(), &one, &mut same)
            .unwrap_err()
            .reason(),
        "a salt appears twice"
    );
    assert_eq!(log.entries().len(), 2);
    for bad in ["0".repeat(31), "A".repeat(32), String::new()] {
        let mut wrong = || bad.clone();
        assert_eq!(
            log.append(3, "said", None, &Map::new(), &one, &mut wrong)
                .unwrap_err()
                .reason(),
            "a salt is not 32 lowercase hex digits"
        );
    }
}

#[test]
fn the_first_entry_is_written_not_given() {
    let table = json!({"said": ["text"]});
    let mut salt = trial_salts();
    for key in ["form", "kept_apart"] {
        let data = map(&json!({key: "mine"}));
        assert_eq!(
            Log::new(&table, &data, "world_created", &mut salt).unwrap_err(),
            Refused::FirstGiven
        );
    }
    // A table holding nothing or a fraction is refused as a table too, as
    // the check refuses it, not as an entry out of form.
    for table in [
        json!({"said": ["text", "key"]}),
        json!({"said": "text"}),
        json!([]),
        json!({"said": ["Text"]}),
        json!({"said": [null]}),
        json!({"said": [1.5]}),
        json!({"said": null}),
        json!(null),
        json!(1.5),
    ] {
        assert_eq!(
            Log::new(&table, &Map::new(), "world_created", &mut salt).unwrap_err(),
            Refused::Table
        );
    }
    // The first entry's own kind can keep fields apart, but never its
    // form or its table.
    let table = json!({"world_created": ["form"]});
    assert_eq!(
        Log::new(&table, &Map::new(), "world_created", &mut salt).unwrap_err(),
        Refused::Open { index: 0 }
    );
}

#[test]
fn the_open_part_is_held_to_the_rule_for_values() {
    // The kernel's own check can't judge a log holding a float here. The
    // form allows no such value, so its check refuses the entry by name,
    // as Python's does, and never has to hash it.
    let v = vectors();
    let mut log = v["holds"][0]["log"].clone();
    log[4]["data"]["height"] = json!(1.5);
    assert!(matches!(
        verify_log(&log),
        Err(LogError::Unwritable { index: 4, .. })
    ));
    assert_eq!(
        check(&log, &json!({})).unwrap_err(),
        Refused::Entry { index: Some(4) }
    );
    // The writer refuses the same, before a salt is drawn, and goes on.
    let drawn = std::cell::Cell::new(0);
    let mut salt = {
        let mut next = trial_salts();
        let drawn = &drawn;
        move || {
            drawn.set(drawn.get() + 1);
            next()
        }
    };
    let mut written = room(&v, &mut salt);
    let before = written.entries().len();
    let drawn_before = drawn.get();
    let kept = map(&json!({"text": "kept apart"}));
    for data in [
        json!({"height": 1.5}),
        json!({"where": null}),
        json!({"count": MAX_WHOLE + 1}),
        json!({"count": u64::MAX}),
        json!({"list": [{"deep": 0.5}]}),
    ] {
        let error = written
            .append(9, "said", None, &map(&data), &kept, &mut salt)
            .unwrap_err();
        assert_eq!(
            error,
            Refused::Entry {
                index: Some(before)
            },
            "{data}"
        );
    }
    let too_late = u64::try_from(MAX_WHOLE).unwrap() + 1;
    assert_eq!(
        written
            .append(too_late, "said", None, &Map::new(), &kept, &mut salt)
            .unwrap_err(),
        Refused::Entry {
            index: Some(before)
        }
    );
    assert_eq!(written.entries().len(), before);
    assert_eq!(drawn.get(), drawn_before, "no salt was drawn for them");
    let last = u64::try_from(MAX_WHOLE).unwrap();
    written
        .append(
            last,
            "said",
            Some("an office"),
            &Map::new(),
            &kept,
            &mut salt,
        )
        .unwrap();
    let (entries, contents) = written.into_parts();
    assert!(check(&Value::Array(entries), &Value::Object(contents)).is_ok());
}
