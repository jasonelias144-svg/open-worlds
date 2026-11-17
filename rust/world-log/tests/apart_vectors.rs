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
    self, Decided, EntryState, FORM, GROUNDS, KEPT, Log, MARK, MAX_NESTING, MAX_REF, MAX_WHOLE,
    Office, PUT_BACK, REMOVED, RESTORED, RedactionState, Refused, SHORT, STAYS, State, TAKEN_BACK,
    check, fingerprint, fingerprint_text, incidents, join, redactions, short_ids, value_allowed,
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

fn redactions_json(found: &apart::Redactions) -> Value {
    let mut out = Map::new();
    for (entry, fields) in found {
        let mut of_fields = Map::new();
        for (name, list) in fields {
            let list: Vec<Value> = list
                .iter()
                .map(|r| json!({"id": r.id, "short": r.short, "state": r.state.as_str()}))
                .collect();
            of_fields.insert(name.clone(), Value::Array(list));
        }
        out.insert(entry.clone(), Value::Object(of_fields));
    }
    Value::Object(out)
}

fn map(value: &Value) -> Map<String, Value> {
    value.as_object().unwrap().clone()
}

/// The trial room's offices and grounds, as `world/apart_vectors.py`
/// names them.
const OFFICE: &str = "trial office";
const KEEPER: &str = "trial keeper";

fn private() -> Value {
    json!({"kind": "rule", "ref": "trial room law, private information"})
}

fn appeal() -> Value {
    json!({"kind": "rule", "ref": "trial appeal rule"})
}

/// A stand-in for a decision record's hash, as `world/apart_vectors.py`
/// makes it: 64 hex digits, public, and the hash of no record.
fn trial_decision(n: usize) -> String {
    sha256_hex(format!("open-worlds trial decision {n}").as_bytes())
}

fn why(text: &str) -> Map<String, Value> {
    map(&json!({"reason": text}))
}

/// A mark as the trial office writes one. The field stays in the
/// contents until it is taken out.
fn mark(
    log: &mut Log,
    tick: u64,
    entry: &str,
    field: &str,
    reason: &str,
    salt: &mut dyn FnMut() -> String,
) -> Result<String, Refused> {
    let by = Office {
        office: OFFICE,
        ground: &private(),
        agent: None,
    };
    log.mark(tick, entry, field, by, &why(reason), salt)
}

/// The entry and the field a mark names, read from the log.
fn marked(log: &Log, a_mark: &str) -> (String, String) {
    let entry = log
        .entries()
        .iter()
        .find(|e| e["hash"] == a_mark)
        .expect("the mark is in the log");
    let text = |key: &str| entry["data"][key].as_str().unwrap().to_owned();
    (text("entry"), text("field"))
}

/// The decision to keep public a field that is still in the contents.
fn keep(
    log: &mut Log,
    tick: u64,
    a_mark: &str,
    reason: &str,
    n: usize,
    salt: &mut dyn FnMut() -> String,
) -> Result<String, Refused> {
    let (entry, field) = marked(log, a_mark);
    let pair = log.contents()[&entry][&field].clone();
    let by = Decided {
        office: KEEPER,
        ground: &appeal(),
        decision: &trial_decision(n),
        agent: None,
    };
    log.keep_public(tick, a_mark, &pair, by, &why(reason), salt)
}

/// The decision that a field stays redacted.
fn stays(
    log: &mut Log,
    tick: u64,
    a_mark: &str,
    reason: &str,
    n: usize,
    salt: &mut dyn FnMut() -> String,
) -> Result<String, Refused> {
    let by = Decided {
        office: KEEPER,
        ground: &appeal(),
        decision: &trial_decision(n),
        agent: None,
    };
    log.stays_redacted(tick, a_mark, by, &why(reason), salt)
}

/// A log and its contents as one text: everything the writer keeps.
fn kept_text(log: &Log) -> String {
    format!(
        "{}{}",
        Value::Array(log.entries().to_vec()),
        Value::Object(log.contents().clone())
    )
}

fn field_state(log: &Log, entry: &str, field: &str) -> State {
    check(
        &Value::Array(log.entries().to_vec()),
        &Value::Object(log.contents().clone()),
    )
    .unwrap()[entry][field]
}

fn redactions_of(log: &Log, entry: &str, field: &str) -> Vec<apart::Redaction> {
    redactions(&Value::Array(log.entries().to_vec()))
        .unwrap()
        .get(entry)
        .and_then(|fields| fields.get(field))
        .cloned()
        .unwrap_or_default()
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
        | Refused::NotByAppend
        | Refused::NoSuchMark
        | Refused::NotThere
        | Refused::StillThere
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
        | Refused::BadStays { index }
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
    assert_eq!(v["stays"], STAYS);
    let redaction_states: Vec<&str> = [
        RedactionState::Open,
        RedactionState::Stands,
        RedactionState::KeptPublic,
    ]
    .iter()
    .map(|s| s.as_str())
    .collect();
    assert_eq!(v["redaction_states"], json!(redaction_states));
    assert_eq!(v["max_whole"], MAX_WHOLE);
    assert_eq!(v["max_nesting"], MAX_NESTING);
    assert_eq!(v["max_ref"], MAX_REF);
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
    assert_eq!(holds.len(), 7, "the vectors are all there");
    let mut seen = BTreeSet::new();
    let mut entry_states = BTreeSet::new();
    let mut redaction_states = std::collections::HashSet::new();
    for case in holds {
        let name = &case["name"];
        assert!(verify_log(&case["log"]).is_ok(), "{name}");
        let states = check(&case["log"], &case["contents"]).unwrap();
        assert_eq!(states_json(&states), case["states"], "{name}");
        let standing = incidents(&case["log"]).unwrap();
        assert_eq!(incidents_json(&standing), case["incidents"], "{name}");
        entry_states.extend(standing.values().map(|s| s.state.as_str()));
        let found = redactions(&case["log"]).unwrap();
        assert_eq!(redactions_json(&found), case["redactions"], "{name}");
        redaction_states.extend(
            found
                .values()
                .flat_map(|fields| fields.values().flatten().map(|r| r.state)),
        );
        let joined = join(&case["log"], &case["contents"]).unwrap();
        assert_eq!(Value::Array(joined), case["joined"], "{name}");
        seen.extend(states.values().flat_map(|fields| fields.values().copied()));
    }
    assert_eq!(seen.len(), 5, "every state is in the vectors");
    // Removed, taken back, restored, and as written with an incident
    // that no longer stands.
    assert_eq!(entry_states.len(), 4, "the entries' states are there");
    assert_eq!(
        redaction_states.len(),
        3,
        "the redactions' states are there"
    );
}

#[test]
fn the_five_states_written_here_are_the_ones_python_wrote() {
    // The same steps as `holds` in world/apart_vectors.py, through this
    // crate's writer: the same log, entry for entry, and the same
    // contents.
    let v = vectors();
    let mut salt = trial_salts();
    let mut room = room(&v, &mut salt);
    let h: Vec<String> = room
        .entries()
        .iter()
        .map(|e| e["hash"].as_str().unwrap().to_owned())
        .collect();
    // Redacted: a mark is open, and the field is gone.
    let first_mark = mark(
        &mut room,
        5,
        &h[5],
        "text",
        "private information",
        &mut salt,
    )
    .unwrap();
    room.take_out(&first_mark).unwrap();
    // Unfinished: a mark is open, and the field is still there.
    mark(
        &mut room,
        5,
        &h[4],
        "text",
        "asked by its author",
        &mut salt,
    )
    .unwrap();
    // Kept public: the mark was answered, and the field is there.
    let a_mark = mark(
        &mut room,
        6,
        &h[3],
        "time",
        "asked by its author",
        &mut salt,
    )
    .unwrap();
    keep(
        &mut room,
        7,
        &a_mark,
        "a time of day says nothing private here",
        1,
        &mut salt,
    )
    .unwrap();
    // Missing: the mark was answered, and the field is gone all the same.
    let a_mark = mark(
        &mut room,
        8,
        &h[2],
        "name",
        "asked by its author",
        &mut salt,
    )
    .unwrap();
    keep(
        &mut room,
        9,
        &a_mark,
        "the name is on the door",
        2,
        &mut salt,
    )
    .unwrap();
    // Redacted: marked, kept public, and marked again.
    let a_mark = mark(
        &mut room,
        10,
        &h[6],
        "thing",
        "asked by its author",
        &mut salt,
    )
    .unwrap();
    keep(
        &mut room,
        11,
        &a_mark,
        "nothing private in it",
        3,
        &mut salt,
    )
    .unwrap();
    let again = mark(
        &mut room,
        12,
        &h[6],
        "thing",
        "it names a third person",
        &mut salt,
    )
    .unwrap();
    room.take_out(&again).unwrap();
    // Redacted: a mark's own reason, which said what it should not.
    let on_reason = mark(
        &mut room,
        13,
        &first_mark,
        "reason",
        "the reason repeated it",
        &mut salt,
    )
    .unwrap();
    room.take_out(&on_reason).unwrap();
    // Redacted, and decided: the mark stands for good.
    let a_mark = mark(
        &mut room,
        14,
        &h[5],
        "time",
        "asked by its author",
        &mut salt,
    )
    .unwrap();
    room.take_out(&a_mark).unwrap();
    stays(
        &mut room,
        15,
        &a_mark,
        "with the text, the time says where",
        4,
        &mut salt,
    )
    .unwrap();
    // Unfinished, though decided: whoever published the log left the
    // field in the contents after the decision that it stays redacted.
    let a_mark = mark(
        &mut room,
        16,
        &h[3],
        "key",
        "asked by its author",
        &mut salt,
    )
    .unwrap();
    let left = room.take_out(&a_mark).unwrap();
    stays(
        &mut room,
        17,
        &a_mark,
        "a key that was never meant to be shown",
        5,
        &mut salt,
    )
    .unwrap();
    let (entries, mut contents) = room.into_parts();
    contents[&h[3]]["key"] = left;
    for (entry, field) in [(&h[1], "name"), (&h[2], "name")] {
        contents[entry].as_object_mut().unwrap().remove(field);
    }
    let case = &v["holds"][3];
    assert_eq!(case["name"], "the five states");
    assert_eq!(Value::Array(entries), case["log"]);
    assert_eq!(Value::Object(contents), case["contents"]);
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
    // The author takes it back: it stays hidden whatever the office does.
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
    // The office can still restore its removal, say after an appeal: the
    // removal stops standing, and the entry stays taken back.
    log.append(
        6,
        RESTORED,
        None,
        &office("keeper", "incident", &removal),
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
    assert_eq!(error, Refused::BadRestoring { index: 10 });
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
    assert_eq!(error, Refused::BadTakingBack { index: 10 });
    // Put back, it shows as restored: an office once removed it.
    log.append(
        7,
        PUT_BACK,
        None,
        &map(&json!({"taken_back": taking})),
        &none,
        &mut salt,
    )
    .unwrap();
    assert_eq!(state(&log), EntryState::Restored);
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
    assert_eq!(error, Refused::BadPuttingBack { index: 11 });
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
    assert_eq!(refused.len(), 161, "the vectors are all there");
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
    let refusals: [(&str, Value, Value, &str); 4] = [
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
    // A mark on a field the entry does not keep apart, with a reason
    // kept apart or without one; and answers to what is not a mark.
    let by = Office {
        office: OFFICE,
        ground: &private(),
        agent: None,
    };
    let decided = Decided {
        office: KEEPER,
        ground: &appeal(),
        decision: &trial_decision(1),
        agent: None,
    };
    let pair = before.1[before.0[3]["hash"].as_str().unwrap()]["text"].clone();
    let acts = [
        log.mark(9, &head, "nothing", by, &Map::new(), &mut salt),
        log.mark(9, &head, "nothing", by, &why("still refused"), &mut salt),
        log.keep_public(9, &head, &pair, decided, &Map::new(), &mut salt),
        log.stays_redacted(9, &head, decided, &Map::new(), &mut salt),
    ];
    let index = before.0.len();
    assert_eq!(
        acts,
        [
            Err(Refused::BadMark { index }),
            Err(Refused::BadMark { index }),
            Err(Refused::BadKept { index }),
            Err(Refused::BadStays { index }),
        ]
    );
    assert_eq!(log.entries(), before.0.as_slice());
    assert_eq!(log.contents(), &before.1);
    assert_eq!(log.head(), head);
    // The log still takes an entry, and still holds.
    let target = before.0[3]["hash"].as_str().unwrap();
    let by = Office {
        agent: Some("trial office"),
        ..by
    };
    let mark = log
        .mark(9, target, "text", by, &why("asked"), &mut salt)
        .unwrap();
    assert_eq!(log.entries().last().unwrap()["agent"], "trial office");
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

// Redacted first, decided after (docs/research/REDACTION.md, decisions 4
// and 5): a mark, and the one entry that answers it. The same tests as
// `TestRedacting` in tests/test_apart.py.

/// The trial room, its salts, and the hash of what ada said.
fn said_room() -> (Log, impl FnMut() -> String, String) {
    let v = vectors();
    let mut salt = trial_salts();
    let log = room(&v, &mut salt);
    let said = log.entries()[3]["hash"].as_str().unwrap().to_owned();
    (log, salt, said)
}

fn decided<'a>(ground: &'a Value, decision: &'a str) -> Decided<'a> {
    Decided {
        office: KEEPER,
        ground,
        decision,
        agent: None,
    }
}

#[test]
fn a_mark_says_its_office_and_its_ground_and_no_decision() {
    let (mut log, mut salt, said) = said_room();
    let made = mark(&mut log, 5, &said, "text", "asked", &mut salt).unwrap();
    assert_eq!(
        log.entries().last().unwrap()["data"],
        json!({"entry": said, "field": "text", "office": OFFICE, "ground": private()})
    );
    let found = redactions_of(&log, &said, "text");
    assert_eq!(found.len(), 1);
    assert_eq!(found[0].id, made);
    assert_eq!(found[0].short, made[..SHORT]);
    assert_eq!(found[0].state, RedactionState::Open);
}

#[test]
fn a_mark_without_its_office_or_ground_is_refused() {
    let (mut log, mut salt, said) = said_room();
    let index = log.entries().len();
    let good = private();
    for (office, ground) in [
        ("", good.clone()),
        (OFFICE, json!("private")),
        (OFFICE, json!({})),
        (OFFICE, json!({"kind": "whim", "ref": "x"})),
        (OFFICE, json!({"kind": "record", "ref": "x"})),
        (OFFICE, json!({"kind": "rule", "ref": ""})),
        (OFFICE, json!({"kind": "rule", "ref": "x", "more": "y"})),
    ] {
        let by = Office {
            office,
            ground: &ground,
            agent: None,
        };
        assert_eq!(
            log.mark(5, &said, "text", by, &Map::new(), &mut salt),
            Err(Refused::BadMark { index }),
            "{office:?} {ground}"
        );
    }
    // Nothing is not a value an open field can have, here as anywhere.
    let by = Office {
        office: OFFICE,
        ground: &Value::Null,
        agent: None,
    };
    assert_eq!(
        log.mark(5, &said, "text", by, &Map::new(), &mut salt),
        Err(Refused::Entry { index: Some(index) })
    );
    assert_eq!(log.entries().len(), index);
}

#[test]
fn a_field_has_one_mark_that_is_open_or_stands() {
    let (mut log, mut salt, said) = said_room();
    let first = mark(&mut log, 5, &said, "text", "asked", &mut salt).unwrap();
    let index = log.entries().len();
    assert_eq!(
        mark(&mut log, 5, &said, "text", "asked", &mut salt),
        Err(Refused::BadMark { index })
    );
    // Another field of the same entry is free.
    mark(&mut log, 5, &said, "time", "asked", &mut salt).unwrap();
    log.take_out(&first).unwrap();
    stays(&mut log, 6, &first, "decided", 1, &mut salt).unwrap();
    let index = log.entries().len();
    assert_eq!(
        mark(&mut log, 7, &said, "text", "asked", &mut salt),
        Err(Refused::BadMark { index })
    );
}

#[test]
fn kept_public_answers_a_mark_and_the_field_can_be_marked_again() {
    let (mut log, mut salt, said) = said_room();
    let first = mark(&mut log, 5, &said, "text", "asked", &mut salt).unwrap();
    keep(&mut log, 6, &first, "decided", 1, &mut salt).unwrap();
    assert_eq!(field_state(&log, &said, "text"), State::KeptPublic);
    let again = mark(&mut log, 7, &said, "text", "asked", &mut salt).unwrap();
    log.take_out(&again).unwrap();
    assert_eq!(field_state(&log, &said, "text"), State::Redacted);
    let found = redactions_of(&log, &said, "text");
    let states: Vec<RedactionState> = found.iter().map(|r| r.state).collect();
    assert_eq!(states, [RedactionState::KeptPublic, RedactionState::Open]);
    let ids: Vec<&str> = found.iter().map(|r| r.id.as_str()).collect();
    assert_eq!(ids, [first, again]);
}

#[test]
fn a_mark_is_answered_once() {
    type Answer =
        fn(&mut Log, u64, &str, &str, usize, &mut dyn FnMut() -> String) -> Result<String, Refused>;
    let cases: [(Answer, Answer, bool, bool); 3] = [
        (keep, keep, false, true),
        (keep, stays, false, false),
        (stays, stays, true, false),
    ];
    for (first, second, out_first, kept_second) in cases {
        let (mut log, mut salt, said) = said_room();
        let made = mark(&mut log, 5, &said, "text", "asked", &mut salt).unwrap();
        if out_first {
            log.take_out(&made).unwrap();
        }
        first(&mut log, 6, &made, "decided", 1, &mut salt).unwrap();
        let index = log.entries().len();
        let expected = if kept_second {
            Refused::BadKept { index }
        } else {
            Refused::BadStays { index }
        };
        // After a keeping, the field is still in the contents.
        assert_eq!(
            second(&mut log, 6, &made, "decided again", 2, &mut salt),
            Err(expected)
        );
        assert_eq!(log.entries().len(), index);
    }
}

#[test]
fn what_stands_is_never_made_public_again() {
    let (mut log, mut salt, said) = said_room();
    let made = mark(&mut log, 5, &said, "text", "asked", &mut salt).unwrap();
    let pair = log.take_out(&made).unwrap();
    stays(&mut log, 6, &made, "decided", 1, &mut salt).unwrap();
    let index = log.entries().len();
    let ground = appeal();
    let decision = trial_decision(2);
    assert_eq!(
        log.keep_public(
            9,
            &made,
            &pair,
            decided(&ground, &decision),
            &Map::new(),
            &mut salt
        ),
        Err(Refused::BadKept { index })
    );
    // Refused for the mark, before the salt and value are looked at.
    assert_eq!(
        log.keep_public(
            9,
            &made,
            &json!([pair[0], "something else"]),
            decided(&ground, &decision),
            &Map::new(),
            &mut salt
        ),
        Err(Refused::BadKept { index })
    );
    assert_eq!(field_state(&log, &said, "text"), State::Redacted);
    assert_eq!(
        redactions_of(&log, &said, "text")[0].state,
        RedactionState::Stands
    );
}

#[test]
fn an_answer_says_its_office_ground_and_decision() {
    let (mut log, mut salt, said) = said_room();
    let made = mark(&mut log, 5, &said, "text", "asked", &mut salt).unwrap();
    let pair = log.take_out(&made).unwrap();
    let index = log.entries().len();
    let before = log.contents().clone();
    let good_ground = appeal();
    let good_decision = trial_decision(1);
    let short = "f".repeat(63);
    let upper = "F".repeat(64);
    let bad: [(&str, Value, &str); 7] = [
        ("", good_ground.clone(), &good_decision),
        (KEEPER, json!({}), &good_decision),
        (KEEPER, json!("appeal"), &good_decision),
        (
            KEEPER,
            json!({"kind": "record", "ref": "not a hash"}),
            &good_decision,
        ),
        (KEEPER, good_ground.clone(), ""),
        (KEEPER, good_ground.clone(), &short),
        (KEEPER, good_ground.clone(), &upper),
    ];
    for (office, ground, decision) in bad {
        let by = Decided {
            office,
            ground: &ground,
            decision,
            agent: None,
        };
        assert_eq!(
            log.keep_public(6, &made, &pair, by, &Map::new(), &mut salt),
            Err(Refused::BadKept { index }),
            "{office:?} {ground} {decision:?}"
        );
        assert_eq!(
            log.stays_redacted(6, &made, by, &Map::new(), &mut salt),
            Err(Refused::BadStays { index }),
            "{office:?} {ground} {decision:?}"
        );
    }
    assert_eq!(log.entries().len(), index);
    assert_eq!(log.contents(), &before, "nothing was put back");
}

#[test]
fn neither_the_value_nor_its_salt_is_left_once_taken_out() {
    let (mut log, mut salt, said) = said_room();
    let pair = log.contents()[&said]["text"].clone();
    let its_salt = pair[0].as_str().unwrap().to_owned();
    let value = pair[1].as_str().unwrap().to_owned();
    let made = mark(&mut log, 5, &said, "text", "asked", &mut salt).unwrap();
    let before = log.entries().to_vec();
    assert!(kept_text(&log).contains(&its_salt));
    assert!(kept_text(&log).contains(&value));
    assert_eq!(log.take_out(&made).unwrap(), pair);
    let kept = kept_text(&log);
    assert!(!kept.contains(&its_salt));
    assert!(!kept.contains(&value));
    assert_eq!(log.entries(), before.as_slice(), "the log is not touched");
    assert_eq!(field_state(&log, &said, "text"), State::Redacted);
    // The other fields of the entry are still there.
    let left: Vec<&String> = log.contents()[&said].as_object().unwrap().keys().collect();
    assert_eq!(left, ["key", "time"]);
}

#[test]
fn an_entry_with_nothing_left_keeps_no_empty_map() {
    let (mut log, mut salt, _) = said_room();
    let entered = log.entries()[1]["hash"].as_str().unwrap().to_owned();
    for field in ["key", "name"] {
        let made = mark(&mut log, 5, &entered, field, "asked", &mut salt).unwrap();
        log.take_out(&made).unwrap();
    }
    assert!(!log.contents().contains_key(&entered));
    assert_eq!(field_state(&log, &entered, "key"), State::Redacted);
    assert_eq!(field_state(&log, &entered, "name"), State::Redacted);
}

#[test]
fn taking_out_needs_a_mark_that_stands_and_a_field_that_is_there() {
    let (mut log, mut salt, said) = said_room();
    assert_eq!(log.take_out(&said), Err(Refused::NoSuchMark)); // not a mark
    let made = mark(&mut log, 5, &said, "text", "asked", &mut salt).unwrap();
    log.take_out(&made).unwrap();
    assert_eq!(log.take_out(&made), Err(Refused::NotThere)); // already out
    let other = mark(&mut log, 5, &said, "time", "asked", &mut salt).unwrap();
    keep(&mut log, 6, &other, "decided", 1, &mut salt).unwrap();
    // Answered: it is public.
    assert_eq!(log.take_out(&other), Err(Refused::NoSuchMark));
    assert!(log.contents()[&said].get("time").is_some());
}

#[test]
fn keeping_public_puts_the_field_back_in_the_same_step() {
    let (mut log, mut salt, said) = said_room();
    let made = mark(&mut log, 5, &said, "text", "asked", &mut salt).unwrap();
    let pair = log.take_out(&made).unwrap();
    assert_eq!(field_state(&log, &said, "text"), State::Redacted);
    let ground = appeal();
    let decision = trial_decision(1);
    log.keep_public(
        6,
        &made,
        &pair,
        decided(&ground, &decision),
        &why("public"),
        &mut salt,
    )
    .unwrap();
    assert_eq!(field_state(&log, &said, "text"), State::KeptPublic);
    assert_eq!(log.contents()[&said]["text"], pair);
    assert_eq!(
        log.entries().last().unwrap()["data"],
        json!({"mark": made, "office": KEEPER, "ground": ground, "decision": decision})
    );
    let (entries, contents) = log.into_parts();
    let joined = join(&Value::Array(entries), &Value::Object(contents)).unwrap();
    assert_eq!(joined[3]["data"]["text"], pair[1]);
}

#[test]
fn keeping_public_refuses_what_the_log_does_not_commit_to() {
    let (mut log, mut salt, said) = said_room();
    let made = mark(&mut log, 5, &said, "text", "asked", &mut salt).unwrap();
    let pair = log.take_out(&made).unwrap();
    let entries = log.entries().to_vec();
    let contents = log.contents().clone();
    let its_salt = pair[0].as_str().unwrap();
    let value = pair[1].as_str().unwrap();
    let other_salt = contents[&said]["time"][0].clone();
    let place = apart::Place {
        entry: Some(said.clone()),
        field: Some("text".to_owned()),
    };
    let ground = appeal();
    let decision = trial_decision(1);
    for (bad, expected) in [
        (
            json!([its_salt, format!("{value}!")]),
            Refused::Fingerprint(place.clone()),
        ),
        (
            json!([other_salt, value]),
            Refused::Fingerprint(place.clone()),
        ),
        (
            json!([its_salt.to_uppercase(), value]),
            Refused::Salt(place.clone()),
        ),
        (json!([7, value]), Refused::Salt(place.clone())),
        (json!([its_salt, 1.5]), Refused::Value(place.clone())),
        // What is not a salt and a value at all.
        (json!([its_salt]), Refused::Contents(place.clone())),
        (
            json!([its_salt, value, value]),
            Refused::Contents(place.clone()),
        ),
        (json!({"salt": its_salt}), Refused::Contents(place.clone())),
        (Value::Null, Refused::Contents(place.clone())),
    ] {
        assert_eq!(
            log.keep_public(
                6,
                &made,
                &bad,
                decided(&ground, &decision),
                &Map::new(),
                &mut salt
            ),
            Err(expected),
            "{bad}"
        );
        assert_eq!(log.entries(), entries.as_slice(), "{bad}");
        assert_eq!(log.contents(), &contents, "{bad}");
    }
}

#[test]
fn it_stays_redacted_only_once_it_is_out_of_the_contents() {
    let (mut log, mut salt, said) = said_room();
    let made = mark(&mut log, 5, &said, "text", "asked", &mut salt).unwrap();
    let before = log.entries().len();
    assert_eq!(
        stays(&mut log, 6, &made, "decided", 1, &mut salt),
        Err(Refused::StillThere)
    );
    assert_eq!(log.entries().len(), before);
    assert_eq!(
        redactions_of(&log, &said, "text")[0].state,
        RedactionState::Open
    );
    log.take_out(&made).unwrap();
    stays(&mut log, 6, &made, "decided", 1, &mut salt).unwrap();
    assert_eq!(
        redactions_of(&log, &said, "text")[0].state,
        RedactionState::Stands
    );
}

#[test]
fn a_mark_and_its_answer_are_not_written_by_append() {
    let (mut log, mut salt, said) = said_room();
    let made = mark(&mut log, 5, &said, "text", "asked", &mut salt).unwrap();
    let entries = log.entries().to_vec();
    let answer = json!({"mark": made, "office": KEEPER, "ground": appeal(),
                        "decision": trial_decision(1)});
    for (kind, data) in [
        (
            MARK,
            json!({"entry": said, "field": "time", "office": OFFICE, "ground": private()}),
        ),
        (KEPT, answer.clone()),
        (STAYS, answer),
    ] {
        assert_eq!(
            log.append(6, kind, None, &map(&data), &Map::new(), &mut salt),
            Err(Refused::NotByAppend),
            "{kind}"
        );
        assert_eq!(log.entries(), entries.as_slice(), "{kind}");
    }
}

#[test]
fn a_decision_alone_never_makes_a_finished_redaction_missing() {
    // The fault carried from part two: one entry of kind
    // field_kept_public turned a redacted field into a missing one. The
    // writer now puts the field back with it, or writes nothing.
    let (mut log, mut salt, said) = said_room();
    let made = mark(&mut log, 5, &said, "text", "asked", &mut salt).unwrap();
    let pair = log.take_out(&made).unwrap();
    let ground = appeal();
    let decision = trial_decision(1);
    log.keep_public(
        6,
        &made,
        &pair,
        decided(&ground, &decision),
        &Map::new(),
        &mut salt,
    )
    .unwrap();
    let (entries, contents) = log.into_parts();
    let states = check(&Value::Array(entries), &Value::Object(contents)).unwrap();
    assert!(
        states
            .values()
            .flat_map(|fields| fields.values())
            .all(|state| *state != State::Missing)
    );
}

#[test]
fn a_published_log_can_still_be_at_fault() {
    // The check can't make a publisher honest: it says what it finds.
    let (mut log, mut salt, said) = said_room();
    let made = mark(&mut log, 5, &said, "text", "asked", &mut salt).unwrap();
    keep(&mut log, 6, &made, "decided", 1, &mut salt).unwrap();
    let mut contents = log.contents().clone();
    contents[&said].as_object_mut().unwrap().remove("text");
    let entries = Value::Array(log.entries().to_vec());
    assert_eq!(
        check(&entries, &Value::Object(contents)).unwrap()[&said]["text"],
        State::Missing
    );
    // And a field left in the contents after the decision that it stays
    // redacted is unfinished, and never shown.
    let other = mark(&mut log, 7, &said, "time", "asked", &mut salt).unwrap();
    let left = Value::Object(log.contents().clone());
    log.take_out(&other).unwrap();
    stays(&mut log, 8, &other, "decided", 2, &mut salt).unwrap();
    let entries = Value::Array(log.entries().to_vec());
    assert_eq!(
        check(&entries, &left).unwrap()[&said]["time"],
        State::Unfinished
    );
    let joined = join(&entries, &left).unwrap();
    assert!(joined[3]["data"].get("time").is_none());
}

#[test]
fn redactions_need_no_contents_and_join_gives_them() {
    let (mut log, mut salt, said) = said_room();
    let made = mark(&mut log, 5, &said, "text", "asked", &mut salt).unwrap();
    log.take_out(&made).unwrap();
    stays(&mut log, 6, &made, "decided", 1, &mut salt).unwrap();
    let (entries, contents) = log.into_parts();
    let entries = Value::Array(entries);
    let found = redactions_json(&redactions(&entries).unwrap());
    assert_eq!(
        found,
        json!({&said: {"text": [
            {"id": made, "short": made[..SHORT], "state": "stands"}]}})
    );
    let joined = join(&entries, &Value::Object(contents)).unwrap();
    assert_eq!(joined[3]["redactions"], found[&said]);
    assert_eq!(joined[1]["redactions"], json!({}));
}

#[test]
fn a_redactions_id_is_shown_with_the_incidents_ids() {
    // Short ids are worked out over incidents and redactions together,
    // so no two that a room shows begin alike.
    let (mut log, mut salt, said) = said_room();
    let made = mark(&mut log, 5, &said, "text", "asked", &mut salt).unwrap();
    let other = log.entries()[4]["hash"].as_str().unwrap().to_owned();
    let removal = log
        .append(
            9,
            REMOVED,
            None,
            &map(&json!({"entry": other, "office": "trial moderator",
                         "ground": {"kind": "law", "ref": "trial room law, part 3"},
                         "decision": trial_decision(1)})),
            &Map::new(),
            &mut salt,
        )
        .unwrap();
    let entries = Value::Array(log.entries().to_vec());
    let together = short_ids(&[removal.clone(), made.clone()]);
    assert_eq!(redactions_of(&log, &said, "text")[0].short, together[&made]);
    assert_eq!(
        incidents(&entries).unwrap()[&other].incidents[0].short,
        together[&removal]
    );
    // Two ids that begin alike are each shown one digit past where they
    // part.
    let alike = [
        format!("{}{}", &made[..20], "0".repeat(44)),
        format!("{}{}", &made[..20], "1".repeat(44)),
    ];
    assert!(short_ids(&alike).values().all(|short| short.len() == 21));
}
