// rust/ur-world/tests/arrivals.rs
//! Entering as one's key (docs/research/KEYS.md, decisions 11 to 17): an
//! arrival is admitted only signed by the one who enters, naming this
//! world, over its log's last entry as it is now; a name stays its
//! individual's; whoever comes back with the same key is the same
//! individual; and a log's arrivals and signed heads are checked whole.

// Tests may unwrap, expect, panic and index: a failure here is a failed
// test, not a world that crashed.
#![allow(
    clippy::unwrap_used,
    clippy::expect_used,
    clippy::panic,
    clippy::indexing_slicing
)]

use formats::proof::{self, public_key};
use serde_json::{Value, json};
use ur_world::arrival::{
    self, FORMAT, arrival_problems, did, head, head_coverage, log_world, trial_secret,
};
use ur_world::garden::Script;
use ur_world::story::tell;
use ur_world::{Action, Admission, Cell, EntryError, World};

const SEED: u64 = 11;
const CREATED: &str = "2026-11-14T00:00:00Z";
const A: Cell = Cell::new(4, 1, 5);
const B: Cell = Cell::new(5, 1, 5);

fn key(label: &str) -> [u8; 32] {
    trial_secret(SEED, label)
}

fn world() -> World {
    World::new(SEED, &public_key(&key("the world")))
}

fn still() -> Box<Script> {
    Box::new(Script::new([]))
}

/// `label`'s arrival under `name`, over the world as it is now.
fn arrival(w: &World, label: &str, name: &str) -> Value {
    arrival::sign(w, &key(label), name, CREATED).unwrap()
}

/// An arrival with its fields changed, then signed by `label`'s key.
fn resigned(record: &Value, label: &str, changes: &Value) -> Value {
    let mut fields = record.as_object().unwrap().clone();
    fields.remove("proof");
    for (k, v) in changes.as_object().unwrap() {
        fields.insert(k.clone(), v.clone());
    }
    proof::sign(
        &Value::Object(fields),
        &key(label),
        CREATED,
        "assertionMethod",
    )
    .unwrap()
}

#[test]
fn a_first_arrival_binds_the_name_to_the_key_that_signed_it() {
    let mut w = world();
    let a = arrival(&w, "one", "ONE");
    assert_eq!(a["format"], FORMAT);
    assert_eq!(a["world"], w.key());
    assert_eq!(a["individual"], did(&key("one")));
    assert_eq!(a["tick"], 0);
    assert_eq!(a["previous"], w.last_hash());
    // Admitting changes nothing; entering binds the name.
    assert_eq!(w.admit(&a), Ok(Admission::First));
    assert_eq!(w.log().len(), 1);
    assert_eq!(w.enter(&a, still(), A), Ok(Admission::First));
    assert_eq!(w.name_of(&did(&key("one"))), Some("ONE"));
    // The arrival is in the log, whole, signed over the entry before its own.
    let entered = w.log().iter().find(|e| e["kind"] == "entered").unwrap();
    assert_eq!(entered["data"]["arrival"], a);
    assert_eq!(entered["prev"], a["previous"]);
}

#[test]
fn an_arrival_is_refused_unless_its_own_key_signed_it_for_this_world_now() {
    let mut w = world();
    let a = arrival(&w, "one", "ONE");
    let refused = |w: &World, record: &Value| w.admit(record).unwrap_err();
    // Signed by another key than the one it names.
    let by_another = resigned(&a, "two", &json!({}));
    assert!(matches!(
        refused(&w, &by_another),
        EntryError::BadArrival(_)
    ));
    // Changed after signing.
    let mut changed = a.clone();
    changed["name"] = json!("TWO");
    assert!(matches!(refused(&w, &changed), EntryError::BadArrival(_)));
    // Not an arrival: a signed head of this world's log.
    let not_one = head(&w, &key("the world"), CREATED).unwrap();
    assert!(matches!(refused(&w, &not_one), EntryError::BadArrival(why) if why.contains("format")));
    // For another world, or a world with the same seed and another key.
    let elsewhere = World::new(SEED, &public_key(&key("another world")));
    assert_eq!(
        refused(&w, &arrival(&elsewhere, "one", "ONE")),
        EntryError::OtherWorld
    );
    // Over another tick or another last entry.
    let later = resigned(&a, "one", &json!({ "tick": 1 }));
    assert_eq!(refused(&w, &later), EntryError::Stale);
    let earlier = resigned(&a, "one", &json!({ "previous": world_log::GENESIS }));
    assert_eq!(refused(&w, &earlier), EntryError::Stale);
    // Signed, then the world moved on a tick before it was used.
    w.step();
    assert_eq!(refused(&w, &a), EntryError::Stale);
    assert!(w.admit(&arrival(&w, "one", "ONE")).is_ok());
}

#[test]
fn two_arrivals_in_one_tick_are_ordered() {
    let mut w = world();
    let one = arrival(&w, "one", "ONE");
    let two_early = arrival(&w, "two", "TWO");
    w.enter(&one, still(), A).unwrap();
    // Signed over the entry before ONE's: it is stale now.
    assert_eq!(w.enter(&two_early, still(), B), Err(EntryError::Stale));
    let two = arrival(&w, "two", "TWO");
    assert_eq!(w.enter(&two, still(), B), Ok(Admission::First));
    assert_eq!(one["tick"], two["tick"]);
    assert_ne!(one["previous"], two["previous"]);
    assert_eq!(arrival_problems(w.log()), Vec::<String>::new());
}

#[test]
fn a_name_stays_its_individuals_and_one_comes_back_as_the_same_individual() {
    let mut w = world();
    let first = arrival(&w, "one", "ONE");
    w.enter(&first, Box::new(Script::new([Action::Exit])), A)
        .unwrap();
    // Here already: the same key can't enter twice at once.
    assert_eq!(
        w.admit(&arrival(&w, "one", "ONE")),
        Err(EntryError::AlreadyHere)
    );
    w.step();
    assert_eq!(w.position("ONE"), None);
    // Another key can't take the name, even once its holder has gone.
    assert_eq!(
        w.admit(&arrival(&w, "two", "ONE")),
        Err(EntryError::NameBound)
    );
    // The same key has one name here.
    assert_eq!(
        w.admit(&arrival(&w, "one", "UNO")),
        Err(EntryError::KnownAs("ONE".into()))
    );
    // The first arrival can't be used again: it is stale.
    assert_eq!(w.enter(&first, still(), A), Err(EntryError::Stale));
    // Signed again, over the world as it is now, ONE comes back.
    let again = arrival(&w, "one", "ONE");
    assert_eq!(w.enter(&again, still(), A), Ok(Admission::Again));
    assert!(tell(&w).contains("ONE comes back, at [4,1,5]."));
    assert_eq!(arrival_problems(w.log()), Vec::<String>::new());
}

#[test]
fn the_refusals_say_why() {
    assert_eq!(
        EntryError::NameBound.to_string(),
        "that name is bound to another key: not this name's birth key (successions aren't checked yet)"
    );
    assert_eq!(
        EntryError::KnownAs("ONE".into()).to_string(),
        "this key has another name here: ONE"
    );
    assert!(EntryError::Stale.to_string().contains("sign it again"));
}

/// A log where ONE entered, left, and came back, and TWO entered.
fn a_log() -> Vec<Value> {
    let mut w = world();
    let a = arrival(&w, "one", "ONE");
    w.enter(&a, Box::new(Script::new([Action::Exit])), A)
        .unwrap();
    w.step();
    let a = arrival(&w, "one", "ONE");
    w.enter(&a, still(), A).unwrap();
    let b = arrival(&w, "two", "TWO");
    w.enter(&b, still(), B).unwrap();
    w.log().to_vec()
}

fn entered(log: &[Value]) -> Vec<usize> {
    (0..log.len())
        .filter(|&i| log[i]["kind"] == "entered")
        .collect()
}

#[test]
fn a_logs_arrivals_are_checked_whole() {
    let log = a_log();
    assert_eq!(arrival_problems(&log), Vec::<String>::new());
    assert_eq!(
        log_world(&log),
        Some(log[0]["data"]["world"].as_str().unwrap())
    );
    let at = entered(&log);
    assert_eq!(at.len(), 3);
    let (one, again, two) = (at[0], at[1], at[2]);

    // An arrival copied to another place in the log: it names the entry
    // before its first place, and another tick.
    let mut replayed = log.clone();
    replayed[again]["data"]["arrival"] = log[one]["data"]["arrival"].clone();
    assert_eq!(
        arrival_problems(&replayed),
        [
            format!("[{again}]: the arrival names another tick"),
            format!("[{again}]: the arrival names another entry before it"),
        ]
    );

    // TWO's entry under ONE's name, by TWO's key, signed for that place.
    let mut taken = log.clone();
    let mut a = taken[two]["data"]["arrival"].clone();
    a = resigned(&a, "two", &json!({ "name": "ONE" }));
    taken[two]["agent"] = json!("ONE");
    taken[two]["data"]["arrival"] = a;
    let found = arrival_problems(&taken);
    assert!(found.contains(&format!(
        "[{two}]: the arrival is under a name bound to another key"
    )));
    assert!(found.contains(&format!(
        "[{two}]: the arrival is by one who is here already"
    )));

    // ONE's key under a second name.
    let mut renamed = log.clone();
    let a = resigned(
        &renamed[again]["data"]["arrival"],
        "one",
        &json!({ "name": "UNO" }),
    );
    renamed[again]["agent"] = json!("UNO");
    renamed[again]["data"]["arrival"] = a;
    assert_eq!(
        arrival_problems(&renamed),
        [format!(
            "[{again}]: the arrival is signed by one who has another name here"
        )]
    );

    // An entry whose arrival is gone, or doesn't hold, or is for another
    // world, or under another name than the entry's.
    let mut bare = log.clone();
    bare[one]["data"].as_object_mut().unwrap().remove("arrival");
    assert_eq!(
        arrival_problems(&bare)[0],
        format!("[{one}]: an entry with no arrival")
    );
    let mut forged = log.clone();
    forged[one]["data"]["arrival"]["name"] = json!("TWO");
    assert!(
        arrival_problems(&forged)[0].starts_with(&format!("[{one}]: the arrival doesn't hold"))
    );
    let mut moved = log.clone();
    moved[0]["data"]["world"] = json!(did(&key("another world")));
    let found = arrival_problems(&moved);
    assert_eq!(found.len(), 3);
    assert!(found.iter().all(|p| p.ends_with("names another world")));
    let mut misnamed = log.clone();
    misnamed[two]["agent"] = json!("THREE");
    assert_eq!(
        arrival_problems(&misnamed),
        [format!("[{two}]: the arrival names another name")]
    );
    let mut headless = log.clone();
    headless.remove(0);
    assert_eq!(
        arrival_problems(&headless),
        ["[0]: not a world_created entry that names its world"]
    );
}

#[test]
fn a_signed_head_covers_what_its_world_signed() {
    let mut w = world();
    let early = head(&w, &key("the world"), CREATED).unwrap();
    let a = arrival(&w, "one", "ONE");
    let speaks = Script::new([Action::Wait, Action::Say("Here.".into())]);
    w.enter(&a, Box::new(speaks), A).unwrap();
    w.run(2);
    let late = head(&w, &key("the world"), CREATED).unwrap();
    let log = w.log().to_vec();
    assert_eq!(late["length"], log.len());
    assert_eq!(late["last"], w.last_hash());
    assert_eq!(
        head_coverage(&log, std::slice::from_ref(&early)),
        (1, vec![])
    );
    assert_eq!(
        head_coverage(&log, &[early.clone(), late.clone()]),
        (log.len(), vec![])
    );
    assert_eq!(head_coverage(&log, &[]), (0, vec![]));
    // Only the world's own key signs its head.
    assert_eq!(
        head(&w, &key("one"), CREATED),
        Err("only the world's own key signs its log's head".to_owned())
    );
    // A head by another key, though it names the world, doesn't hold.
    let mut fields = late.as_object().unwrap().clone();
    fields.remove("proof");
    let by_another = proof::sign(
        &Value::Object(fields.clone()),
        &key("one"),
        CREATED,
        "assertionMethod",
    )
    .unwrap();
    let (covered, found) = head_coverage(&log, &[by_another]);
    assert_eq!(covered, 0);
    assert!(found[0].starts_with("head 0: doesn't hold"));
    // A log cut short, or shown another way, against the late head.
    let (covered, found) = head_coverage(&log[..log.len() - 1], std::slice::from_ref(&late));
    assert_eq!(
        (covered, found),
        (0, vec!["head 0: longer than the log".to_owned()])
    );
    let mut other = log.clone();
    let n = other.len();
    other[n - 1]["hash"] = json!("0".repeat(64));
    assert_eq!(
        head_coverage(&other, std::slice::from_ref(&late)),
        (0, vec!["head 0: its last hash isn't the log's".to_owned()])
    );
    // Another world's head.
    let elsewhere = World::new(SEED, &public_key(&key("another world")));
    let theirs = head(&elsewhere, &key("another world"), CREATED).unwrap();
    assert_eq!(
        head_coverage(&log, &[theirs]),
        (0, vec!["head 0: signed by another world".to_owned()])
    );
    // A head whose tick doesn't fit where it says the log stood.
    fields.insert("tick".into(), json!(0));
    let wrong_tick = proof::sign(
        &Value::Object(fields),
        &key("the world"),
        CREATED,
        "assertionMethod",
    )
    .unwrap();
    assert_eq!(
        head_coverage(&log, &[wrong_tick]),
        (0, vec!["head 0: its tick doesn't fit the log".to_owned()])
    );
    // A head over the first entry alone, at a tick later than the entries
    // after it: they can't come before it.
    let mut fields = early.as_object().unwrap().clone();
    fields.remove("proof");
    fields.insert("tick".into(), json!(1));
    let too_late = proof::sign(
        &Value::Object(fields.clone()),
        &key("the world"),
        CREATED,
        "assertionMethod",
    )
    .unwrap();
    assert_eq!(
        head_coverage(&log, &[too_late]),
        (0, vec!["head 0: its tick doesn't fit the log".to_owned()])
    );
    // A head of the empty log, before the world was created, covers nothing.
    fields.insert("length".into(), json!(0));
    fields.insert("last".into(), json!(world_log::GENESIS));
    fields.insert("tick".into(), json!(0));
    let empty = proof::sign(
        &Value::Object(fields.clone()),
        &key("the world"),
        CREATED,
        "assertionMethod",
    )
    .unwrap();
    assert_eq!(head_coverage(&log, &[empty]), (0, vec![]));
    // ... and can't be at a tick after the log's first entry.
    fields.insert("tick".into(), json!(1));
    let empty_late = proof::sign(
        &Value::Object(fields),
        &key("the world"),
        CREATED,
        "assertionMethod",
    )
    .unwrap();
    assert_eq!(
        head_coverage(&log, &[empty_late]),
        (0, vec!["head 0: its tick doesn't fit the log".to_owned()])
    );
}
