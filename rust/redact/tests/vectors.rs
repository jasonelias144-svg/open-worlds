// rust/redact/tests/vectors.rs
//! The act of redacting (`redact`), checked against
//! `vectors/redaction.json`, which Python writes
//! (`python3 -m world.redact_vectors`, from `world/redact.py`), on the
//! trial room of `vectors/log-apart.json`: the same log and contents
//! after the act, the same records inside the copies, the same log after
//! each decision, and the same reason for every record that must be
//! refused, among them the records of a log written by hand whose entries
//! commit to texts that are not a field as a log writes one.

// Tests may unwrap, expect, panic and index: a failure here is a failed
// test, not a world that crashed.
#![allow(
    clippy::unwrap_used,
    clippy::expect_used,
    clippy::panic,
    clippy::indexing_slicing
)]

use formats::canonical::canonical;
use formats::multikey::{
    sealing_from_multikey, sealing_secret_from_multikey, secret_from_multikey,
};
use formats::{records, sealed};
use redact::{
    Act, Answer, FORMAT, LABEL, Office, Opener, PADDED, REASONS, Recipient, Redaction, Refused,
    finish, held_to, keep_public, open_copy, redact, stays_redacted, what_was_there,
};
use serde_json::{Map, Value, json};
use world_log::apart::{self, Decided, Log, RedactionState, State};
use world_log::sha256_hex;

const VECTORS: &str = include_str!("../../../vectors/redaction.json");
const ROOM: &str = include_str!("../../../vectors/log-apart.json");

const ABOUT: [&str; 2] = ["ALICE", "BOB"];
const DECIDES: &str = "the Ur-world's Keeper";
const VALUE: &str = "hello, room";

fn vectors() -> Value {
    serde_json::from_str(VECTORS).unwrap()
}

fn map(value: &Value) -> Map<String, Value> {
    value.as_object().unwrap().clone()
}

/// Trial salts in order, from the first, as `world/apart_vectors.py`
/// makes them.
fn trial_salts() -> impl FnMut() -> String {
    let mut n = 0;
    move || {
        n += 1;
        sha256_hex(format!("open-worlds trial salt {}", n - 1).as_bytes())[..32].to_owned()
    }
}

/// Trial salts that go on where a log's writer stopped: it drew one for
/// each field it kept apart.
fn trial_salts_after(log: &Value) -> impl FnMut() -> String {
    let mut n: usize = log
        .as_array()
        .unwrap()
        .iter()
        .map(|e| e["apart"].as_object().unwrap().len())
        .sum();
    move || {
        n += 1;
        sha256_hex(format!("open-worlds trial salt {}", n - 1).as_bytes())[..32].to_owned()
    }
}

/// The trial room of `vectors/log-apart.json`, written again here.
fn room(salt: &mut dyn FnMut() -> String) -> Log {
    let v: Value = serde_json::from_str(ROOM).unwrap();
    let mut log = Log::new(&v["table"], &map(&v["first"]), "world_created", salt).unwrap();
    for step in v["written"].as_array().unwrap() {
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

/// A party's keys, as the vectors give them.
struct Party {
    id: String,
    secret: [u8; 32],
    sealing: [u8; 32],
    sealing_secret: [u8; 32],
}

fn party(v: &Value, name: &str) -> Party {
    let p = &v["parties"][name];
    let text = |key: &str| p[key].as_str().unwrap();
    Party {
        id: text("id").to_owned(),
        secret: secret_from_multikey(text("secretKeyMultibase")).unwrap(),
        sealing: sealing_from_multikey(text("sealingKeyMultibase")).unwrap(),
        sealing_secret: sealing_secret_from_multikey(text("sealingSecretMultibase")).unwrap(),
    }
}

impl Party {
    fn recipient(&self) -> Recipient<'_> {
        Recipient {
            key: &self.id,
            sealing: &self.sealing,
        }
    }

    fn opener(&self) -> Opener<'_> {
        Opener {
            key: &self.id,
            sealing_secret: &self.sealing_secret,
        }
    }
}

/// Everything a test needs: the vectors, the parties, and the room.
struct Trial {
    v: Value,
    alice: Party,
    bob: Party,
    redacts: Party,
    decides: Party,
}

impl Trial {
    fn new() -> Trial {
        let v = vectors();
        Trial {
            alice: party(&v, "ALICE"),
            bob: party(&v, "BOB"),
            redacts: party(&v, v["act"]["by"].as_str().unwrap()),
            decides: party(&v, DECIDES),
            v,
        }
    }

    fn office(&self) -> Office<'_> {
        Office {
            name: self.v["act"]["office"].as_str().unwrap(),
            secret: &self.redacts.secret,
            grant: self.v["act"]["grant"].as_str().unwrap(),
        }
    }

    fn entry(&self) -> &str {
        self.v["act"]["entry"].as_str().unwrap()
    }

    /// The act of the vectors, done here on a room written here.
    fn redacted(&self) -> (Log, Redaction, impl FnMut() -> String) {
        let mut salt = trial_salts();
        let mut log = room(&mut salt);
        let act = &self.v["act"];
        let about = [self.alice.recipient(), self.bob.recipient()];
        let made = redact(
            &mut log,
            &Act {
                tick: act["tick"].as_u64().unwrap(),
                entry: self.entry(),
                field: act["field"].as_str().unwrap(),
                ground: &act["ground"],
                created: self.v["created"].as_str().unwrap(),
                about: &about,
                decider: self.decides.recipient(),
                agent: None,
                apart: &map(&act["apart"]),
            },
            &self.office(),
            None,
            &mut salt,
        )
        .unwrap();
        (log, made, salt)
    }

    /// A decision as the vectors' case `name` has it.
    fn decide<R>(&self, name: &str, mark: &str, then: impl FnOnce(&Answer<'_>) -> R) -> R {
        let case = &self.v[name];
        then(&Answer {
            tick: case["tick"].as_u64().unwrap(),
            mark,
            by: Decided {
                office: case["office"].as_str().unwrap(),
                ground: &case["ground"],
                decision: case["decision"].as_str().unwrap(),
                agent: None,
            },
            apart: &map(&case["apart"]),
        })
    }
}

fn entries(log: &Log) -> Value {
    Value::Array(log.entries().to_vec())
}

fn contents(log: &Log) -> Value {
    Value::Object(log.contents().clone())
}

fn state(log: &Log, entry: &str, field: &str) -> State {
    apart::check(&entries(log), &contents(log)).unwrap()[entry][field]
}

#[test]
fn the_names_and_reasons_are_pythons() {
    let v = vectors();
    assert_eq!(v["format"], FORMAT);
    assert_eq!(v["label"], LABEL);
    assert_eq!(v["padded"], json!(PADDED));
    let reasons: Vec<&str> = REASONS.iter().map(Refused::reason).collect();
    assert_eq!(v["reasons"], json!(reasons));
}

#[test]
fn each_copy_in_the_file_opens_for_the_one_it_names_and_holds() {
    let t = Trial::new();
    let log = &t.v["redacted"]["log"];
    let copies = t.v["copies"].as_array().unwrap();
    let to: Vec<&str> = copies.iter().map(|c| c["to"].as_str().unwrap()).collect();
    assert_eq!(to, [ABOUT[0], ABOUT[1], DECIDES]);
    for case in copies {
        let who = party(&t.v, case["to"].as_str().unwrap());
        let inside = open_copy(&case["envelope"], who.opener(), log).unwrap();
        assert_eq!(inside, case["inside"]);
        assert_eq!(records::record_hash(&inside).unwrap(), case["record"]);
        assert_eq!(
            sealed::fingerprint(&case["envelope"]).unwrap(),
            case["fingerprint"]
        );
    }
}

#[test]
fn each_refused_record_holds_as_a_record_and_not_to_the_log() {
    let v = vectors();
    let log = &v["redacted"]["log"];
    let refused = v["refused"].as_array().unwrap();
    assert_eq!(refused.len(), 9, "the vectors are all there");
    for case in refused {
        let name = &case["name"];
        assert!(records::check(&case["record"]).is_ok(), "{name}");
        let Err(error) = held_to(&case["record"], log) else {
            panic!("{name}: held");
        };
        assert_eq!(error.reason(), case["reason"], "{name}");
        assert_eq!(
            error.to_string(),
            case["reason"].as_str().unwrap(),
            "{name}"
        );
    }
}

#[test]
fn a_text_that_is_not_a_field_is_refused_though_it_hashes() {
    // A log written by hand commits to texts that are not a field as a
    // log writes one. Each record carries exactly the text its entry's
    // fingerprint is the hash of, and is refused all the same: what is
    // put back must be what a log would write.
    let v = vectors();
    let case = &v["odd"];
    let log = &case["log"];
    assert_eq!(case["reason"], Refused::NotHeld.reason());
    assert_eq!(held_to(&case["holds"], log), Ok(()));
    assert_eq!(what_was_there(&case["holds"]).unwrap().1, VALUE);
    let refused = case["refused"].as_array().unwrap();
    assert_eq!(refused.len(), 21, "the vectors are all there");
    for one in refused {
        let name = &one["name"];
        let record = &one["record"];
        assert!(records::check(record).is_ok(), "{name}");
        let entry = log
            .as_array()
            .unwrap()
            .iter()
            .find(|e| e["hash"] == record["entry"])
            .unwrap();
        assert_eq!(
            json!(sha256_hex(record["hashed"].as_str().unwrap().as_bytes())),
            entry["apart"]["text"],
            "{name}"
        );
        assert_eq!(what_was_there(record), None, "{name}");
        assert_eq!(held_to(record, log), Err(Refused::NotHeld), "{name}");
    }
}

#[test]
fn the_act_done_here_gives_pythons_log_and_pythons_records() {
    let t = Trial::new();
    let (log, made, _) = t.redacted();
    let after = &t.v["redacted"];
    assert_eq!(made.mark, after["mark"].as_str().unwrap());
    assert_eq!(entries(&log), after["log"]);
    assert_eq!(contents(&log), after["contents"]);
    assert_eq!(state(&log, t.entry(), "text"), State::Redacted);
    // The boxes differ, since sealing is random; what is inside is the
    // same record, signature and all.
    let ours: Vec<&Value> = made
        .copies
        .iter()
        .chain(std::iter::once(&made.office_copy))
        .collect();
    let theirs = t.v["copies"].as_array().unwrap();
    assert_eq!(ours.len(), theirs.len());
    for (envelope, case) in ours.iter().zip(theirs) {
        let who = party(&t.v, case["to"].as_str().unwrap());
        assert_eq!(envelope["to"], json!(who.id));
        assert_ne!(envelope["box"], case["envelope"]["box"]);
        let inside = open_copy(envelope, who.opener(), &entries(&log)).unwrap();
        assert_eq!(inside, case["inside"]);
    }
}

#[test]
fn neither_the_value_nor_its_salt_is_left_anywhere() {
    let t = Trial::new();
    let mut salt = trial_salts();
    let before = room(&mut salt);
    let pair = before.contents()[t.entry()]["text"].clone();
    let its_salt = pair[0].as_str().unwrap();
    assert_eq!(pair[1], VALUE);
    let all = |log: &Log, more: &[&Value]| {
        let more: Vec<String> = more.iter().map(|v| v.to_string()).collect();
        format!("{}{}{}", entries(log), contents(log), more.join(""))
    };
    assert!(all(&before, &[]).contains(its_salt));
    assert!(all(&before, &[]).contains(VALUE));
    let (log, made, _) = t.redacted();
    let everything = all(&log, &[&made.copies[0], &made.copies[1], &made.office_copy]);
    assert!(!everything.contains(its_salt));
    assert!(!everything.contains(VALUE));
    // Nor anywhere else in what the writer holds, or in what the act
    // gave back.
    let held = format!("{log:?}{made:?}");
    assert!(format!("{before:?}").contains(its_salt));
    assert!(!held.contains(its_salt));
    assert!(!held.contains(VALUE));
    // The entry's other fields are untouched.
    let left: Vec<&String> = log.contents()[t.entry()]
        .as_object()
        .unwrap()
        .keys()
        .collect();
    assert_eq!(left, ["key", "time"]);
}

#[test]
fn each_copy_is_for_one_alone() {
    let t = Trial::new();
    let (log, made, _) = t.redacted();
    let log = entries(&log);
    for (envelope, who, other) in [
        (&made.copies[0], &t.alice, &t.bob),
        (&made.copies[1], &t.bob, &t.decides),
        (&made.office_copy, &t.decides, &t.alice),
    ] {
        open_copy(envelope, who.opener(), &log).unwrap();
        assert!(matches!(
            open_copy(envelope, other.opener(), &log),
            Err(Refused::Sealed(_))
        ));
        // With the right key under another's name, too.
        let wrong = Opener {
            key: &other.id,
            sealing_secret: &who.sealing_secret,
        };
        assert!(matches!(
            open_copy(envelope, wrong, &log),
            Err(Refused::Sealed(_))
        ));
    }
}

#[test]
fn a_redaction_that_cannot_be_made_changes_nothing() {
    let t = Trial::new();
    let mut salt = trial_salts();
    let mut log = room(&mut salt);
    let before = (log.entries().to_vec(), log.contents().clone());
    let act = &t.v["act"];
    let none = Map::new();
    let good = Act {
        tick: 5,
        entry: t.entry(),
        field: "text",
        ground: &act["ground"],
        created: t.v["created"].as_str().unwrap(),
        about: &[t.alice.recipient()],
        decider: t.decides.recipient(),
        agent: None,
        apart: &none,
    };
    let office = t.office();
    let zeros = "0".repeat(64);
    let twice = [t.alice.recipient(), t.alice.recipient()];
    let also_decides = [t.decides.recipient()];
    let small = [0u8; 32];
    let to_small = [Recipient {
        key: &t.alice.id,
        sealing: &small,
    }];
    let whim = json!({"kind": "whim", "ref": "x"});
    type Expected = fn(&Refused) -> bool;
    let cases: Vec<(&str, Act<'_>, Office<'_>, Expected)> = vec![
        (
            "no such entry",
            Act {
                entry: &zeros,
                ..good
            },
            office,
            |e| *e == Refused::NotThere,
        ),
        (
            "no such field",
            Act {
                field: "name",
                ..good
            },
            office,
            |e| *e == Refused::NotThere,
        ),
        (
            "the same one twice",
            Act {
                about: &twice,
                ..good
            },
            office,
            |e| *e == Refused::Twice,
        ),
        (
            "the deciding office is also asked as a person",
            Act {
                about: &also_decides,
                ..good
            },
            office,
            |e| *e == Refused::Twice,
        ),
        (
            "a sealing key no one should seal to",
            Act {
                about: &to_small,
                ..good
            },
            office,
            |e| matches!(e, Refused::Sealed(_)),
        ),
        (
            "a time that is not a time",
            Act {
                created: "yesterday",
                ..good
            },
            office,
            |e| matches!(e, Refused::Sealed(_)),
        ),
        (
            "a grant that is not a hash",
            good,
            Office {
                grant: "mine",
                ..office
            },
            |e| matches!(e, Refused::Sealed(_)),
        ),
        (
            "a ground the log does not take",
            Act {
                ground: &whim,
                ..good
            },
            office,
            |e| matches!(e, Refused::Log(apart::Refused::BadMark { .. })),
        ),
        (
            "an office with no name",
            good,
            Office { name: "", ..office },
            |e| matches!(e, Refused::Log(apart::Refused::BadMark { .. })),
        ),
    ];
    for (name, act, by, expected) in cases {
        let error = redact(&mut log, &act, &by, None, &mut salt).expect_err(name);
        assert!(expected(&error), "{name}: {error}");
        assert_eq!(log.entries(), before.0.as_slice(), "{name}");
        assert_eq!(log.contents(), &before.1, "{name}");
    }
    // And the room still takes the act.
    let made = redact(&mut log, &good, &office, None, &mut salt).unwrap();
    assert_eq!(made.copies.len(), 1);
    // A field is redacted once: it is gone, and its mark is open.
    assert_eq!(
        redact(&mut log, &good, &office, None, &mut salt),
        Err(Refused::NotThere)
    );
}

#[test]
fn no_copy_is_kept_for_someone_with_no_key() {
    let t = Trial::new();
    let mut salt = trial_salts();
    let mut log = room(&mut salt);
    let none = Map::new();
    let made = redact(
        &mut log,
        &Act {
            tick: 5,
            entry: t.entry(),
            field: "text",
            ground: &t.v["act"]["ground"],
            created: t.v["created"].as_str().unwrap(),
            about: &[],
            decider: t.decides.recipient(),
            agent: Some("trial office"),
            apart: &none,
        },
        &t.office(),
        None,
        &mut salt,
    )
    .unwrap();
    assert!(made.copies.is_empty());
    assert_eq!(made.office_copy["to"], json!(t.decides.id));
    assert_eq!(log.entries().last().unwrap()["agent"], "trial office");
    assert_eq!(state(&log, t.entry(), "text"), State::Redacted);
}

#[test]
fn a_redaction_that_stopped_after_its_mark_is_finished() {
    let t = Trial::new();
    let mut salt = trial_salts();
    let mut log = room(&mut salt);
    let by = apart::Office {
        office: "trial office",
        ground: &t.v["act"]["ground"],
        agent: None,
    };
    let created = t.v["created"].as_str().unwrap();
    // What is not a mark is not finished.
    for odd in [t.entry(), &"0".repeat(64)] {
        assert_eq!(
            finish(
                &mut log,
                odd,
                &t.office(),
                created,
                &[],
                t.decides.recipient(),
                None
            ),
            Err(Refused::NoMark)
        );
    }
    let mark = log
        .mark(5, t.entry(), "text", by, &Map::new(), &mut salt)
        .unwrap();
    assert_eq!(state(&log, t.entry(), "text"), State::Unfinished);
    let before = log.entries().to_vec();
    // A copy that can't be made takes nothing out.
    let small = [0u8; 32];
    let to_small = [Recipient {
        key: &t.alice.id,
        sealing: &small,
    }];
    assert!(matches!(
        finish(
            &mut log,
            &mark,
            &t.office(),
            created,
            &to_small,
            t.decides.recipient(),
            None
        ),
        Err(Refused::Sealed(_))
    ));
    assert_eq!(state(&log, t.entry(), "text"), State::Unfinished);
    let made = finish(
        &mut log,
        &mark,
        &t.office(),
        created,
        &[t.alice.recipient()],
        t.decides.recipient(),
        None,
    )
    .unwrap();
    assert_eq!(made.mark, mark);
    assert_eq!(log.entries(), before.as_slice(), "the log is not touched");
    assert_eq!(state(&log, t.entry(), "text"), State::Redacted);
    let inside = open_copy(&made.copies[0], t.alice.opener(), &entries(&log)).unwrap();
    assert_eq!(what_was_there(&inside).unwrap().1, VALUE);
    // Already out.
    assert_eq!(
        finish(
            &mut log,
            &mark,
            &t.office(),
            created,
            &[],
            t.decides.recipient(),
            None
        ),
        Err(Refused::NotThere)
    );
    // The office's copy then decides, as after any redaction; and what
    // is public again is not finished.
    t.decide("kept", &mark, |answer| {
        keep_public(
            &mut log,
            answer,
            &made.office_copy,
            t.decides.opener(),
            &mut salt,
        )
    })
    .unwrap();
    assert_eq!(state(&log, t.entry(), "text"), State::KeptPublic);
    assert_eq!(
        finish(
            &mut log,
            &mark,
            &t.office(),
            created,
            &[],
            t.decides.recipient(),
            None
        ),
        Err(Refused::NoMark)
    );
    assert_eq!(state(&log, t.entry(), "text"), State::KeptPublic);
}

#[test]
fn the_office_keeps_it_public_from_its_copy() {
    let t = Trial::new();
    // From the copy made here, and from the box kept in the file.
    let kept_in_file = t.v["copies"][2]["envelope"].clone();
    for from_file in [false, true] {
        let (mut log, made, mut salt) = t.redacted();
        let envelope = if from_file {
            &kept_in_file
        } else {
            &made.office_copy
        };
        let decision = t
            .decide("kept", &made.mark, |answer| {
                keep_public(&mut log, answer, envelope, t.decides.opener(), &mut salt)
            })
            .unwrap();
        assert_eq!(log.entries().last().unwrap()["hash"], json!(decision));
        assert_eq!(entries(&log), t.v["kept"]["log"]);
        assert_eq!(contents(&log), t.v["kept"]["contents"]);
        assert_eq!(state(&log, t.entry(), "text"), State::KeptPublic);
        let joined = apart::join(&entries(&log), &contents(&log)).unwrap();
        assert_eq!(joined[3]["data"]["text"], VALUE);
    }
}

#[test]
fn it_stays_redacted_and_is_never_made_public_again() {
    let t = Trial::new();
    let (mut log, made, mut salt) = t.redacted();
    t.decide("stays", &made.mark, |answer| {
        stays_redacted(&mut log, answer, &mut salt)
    })
    .unwrap();
    assert_eq!(entries(&log), t.v["stays"]["log"]);
    assert_eq!(contents(&log), t.v["stays"]["contents"]);
    assert_eq!(state(&log, t.entry(), "text"), State::Redacted);
    let found = apart::redactions(&entries(&log)).unwrap();
    assert_eq!(found[t.entry()]["text"][0].state, RedactionState::Stands);
    // Even with the copy in hand.
    let before = (log.entries().to_vec(), log.contents().clone());
    let error = t
        .decide("kept", &made.mark, |answer| {
            keep_public(
                &mut log,
                answer,
                &made.office_copy,
                t.decides.opener(),
                &mut salt,
            )
        })
        .unwrap_err();
    assert_eq!(
        error,
        Refused::Log(apart::Refused::BadKept {
            index: before.0.len()
        })
    );
    assert_eq!(log.entries(), before.0.as_slice());
    assert_eq!(log.contents(), &before.1);
}

#[test]
fn only_the_deciding_offices_own_copy_of_that_field_decides() {
    let t = Trial::new();
    let (mut log, made, mut salt) = t.redacted();
    let before = log.entries().len();
    let untouched = (log.entries().to_vec(), log.contents().clone());
    // A person's copy, in the office's hands: it does not open.
    let error = t
        .decide("kept", &made.mark, |answer| {
            keep_public(
                &mut log,
                answer,
                &made.copies[0],
                t.decides.opener(),
                &mut salt,
            )
        })
        .unwrap_err();
    assert!(matches!(error, Refused::Sealed(_)), "{error}");
    // A person's own copy, opened by that person: it opens, it is what
    // the log held, and it names another as the deciding office.
    let error = t
        .decide("kept", &made.mark, |answer| {
            keep_public(
                &mut log,
                answer,
                &made.copies[0],
                t.alice.opener(),
                &mut salt,
            )
        })
        .unwrap_err();
    assert_eq!(error, Refused::NotDeciders);
    assert_eq!(log.entries(), untouched.0.as_slice());
    assert_eq!(log.contents(), &untouched.1);
    // Every copy names the same deciding office.
    for (envelope, who) in [
        (&made.copies[0], &t.alice),
        (&made.copies[1], &t.bob),
        (&made.office_copy, &t.decides),
    ] {
        let inside = open_copy(envelope, who.opener(), &entries(&log)).unwrap();
        assert_eq!(inside["decider"], json!(t.decides.id));
    }
    // What is not a mark is refused as the log refuses it.
    for odd in [t.entry(), &"0".repeat(64)] {
        let error = t
            .decide("kept", odd, |answer| {
                keep_public(
                    &mut log,
                    answer,
                    &made.office_copy,
                    t.decides.opener(),
                    &mut salt,
                )
            })
            .unwrap_err();
        assert_eq!(
            error,
            Refused::Log(apart::Refused::BadKept { index: before })
        );
    }
    // The office's copy of another field, redacted by another mark.
    let none = Map::new();
    let other = redact(
        &mut log,
        &Act {
            tick: 6,
            entry: t.entry(),
            field: "time",
            ground: &t.v["act"]["ground"],
            created: t.v["created"].as_str().unwrap(),
            about: &[],
            decider: t.decides.recipient(),
            agent: None,
            apart: &none,
        },
        &t.office(),
        None,
        &mut salt,
    )
    .unwrap();
    let kept = (log.entries().to_vec(), log.contents().clone());
    let error = t
        .decide("kept", &made.mark, |answer| {
            keep_public(
                &mut log,
                answer,
                &other.office_copy,
                t.decides.opener(),
                &mut salt,
            )
        })
        .unwrap_err();
    assert_eq!(error, Refused::OtherField);
    // A decision the log refuses puts nothing back.
    let bad = Answer {
        tick: 7,
        mark: &made.mark,
        by: Decided {
            office: "trial keeper",
            ground: &t.v["kept"]["ground"],
            decision: "not a hash",
            agent: None,
        },
        apart: &none,
    };
    assert_eq!(
        keep_public(
            &mut log,
            &bad,
            &made.office_copy,
            t.decides.opener(),
            &mut salt
        ),
        Err(Refused::Log(apart::Refused::BadKept {
            index: kept.0.len()
        }))
    );
    assert_eq!(log.entries(), kept.0.as_slice());
    assert_eq!(log.contents(), &kept.1);
    assert_eq!(state(&log, t.entry(), "text"), State::Redacted);
}

#[test]
fn a_copy_is_held_to_the_log_it_is_opened_against() {
    let t = Trial::new();
    let (log, made, _) = t.redacted();
    // Another room, begun the same way, has other salts: the same first
    // entry, and so the same name, but no entry in common after it that
    // keeps a field apart.
    let mut n = 1000;
    let mut other_salts = move || {
        n += 1;
        sha256_hex(format!("another room's salt {n}").as_bytes())[..32].to_owned()
    };
    let other = room(&mut other_salts);
    assert_eq!(other.entries()[0]["hash"], log.entries()[0]["hash"]);
    assert_eq!(
        open_copy(&made.office_copy, t.decides.opener(), &entries(&other)),
        Err(Refused::NoEntry)
    );
    // A log that does not hold is refused as a log.
    let mut broken = entries(&log);
    broken[2]["tick"] = json!(99);
    assert!(matches!(
        open_copy(&made.office_copy, t.decides.opener(), &broken),
        Err(Refused::Log(_))
    ));
    let inside = &t.v["copies"][0]["inside"];
    for odd in [json!(null), json!({}), json!("log"), json!([])] {
        assert!(
            matches!(held_to(inside, &odd), Err(Refused::Log(_))),
            "{odd}"
        );
    }
}

#[test]
fn what_is_held_to_a_log_need_not_be_a_record_at_all() {
    let t = Trial::new();
    let log = &t.v["redacted"]["log"];
    for odd in [
        json!(null),
        json!([]),
        json!("copy"),
        json!({}),
        json!({"format": "open-worlds/x/v1"}),
    ] {
        assert_eq!(held_to(&odd, log), Err(Refused::NotACopy), "{odd}");
    }
    let mut good = t.v["copies"][0]["inside"].clone();
    good.as_object_mut().unwrap().remove("proof");
    assert_eq!(held_to(&good, log), Ok(()));
    let changed = |key: &str, value: Value| {
        let mut record = good.clone();
        record[key] = value;
        record
    };
    for (record, expected) in [
        (changed("log", json!(7)), Refused::OtherLog),
        (changed("entry", json!(["x"])), Refused::NoEntry),
        (changed("field", json!(7)), Refused::NoField),
        (changed("field", json!(["text"])), Refused::NoField),
        (changed("hashed", json!(7)), Refused::NotHeld),
        (
            changed("hashed", json!(["salt", "text", "value"])),
            Refused::NotHeld,
        ),
        (changed("hashed", json!("")), Refused::NotHeld),
        (
            changed(
                "hashed",
                json!(format!("{} ", good["hashed"].as_str().unwrap())),
            ),
            Refused::NotHeld,
        ),
    ] {
        assert_eq!(held_to(&record, log), Err(expected), "{record}");
    }
    for (missing, expected) in [
        ("log", Refused::OtherLog),
        ("entry", Refused::NoEntry),
        ("field", Refused::NoField),
        ("hashed", Refused::NotHeld),
    ] {
        let mut record = good.clone();
        record.as_object_mut().unwrap().remove(missing);
        assert_eq!(held_to(&record, log), Err(expected), "{missing}");
    }
}

#[test]
fn a_copy_says_what_was_there_and_where() {
    let t = Trial::new();
    let mut salt = trial_salts();
    let before = room(&mut salt);
    let pair = before.contents()[t.entry()]["text"].clone();
    let (log, made, _) = t.redacted();
    let mut inside = open_copy(&made.copies[0], t.alice.opener(), &entries(&log)).unwrap();
    assert_eq!(
        what_was_there(&inside),
        Some((pair[0].as_str().unwrap().to_owned(), pair[1].clone()))
    );
    // Signed by the office that redacted it.
    assert!(records::check(&inside).is_ok());
    let pad = inside["pad"].clone();
    inside.as_object_mut().unwrap().remove("proof");
    assert_eq!(
        inside,
        json!({
            "format": FORMAT,
            "office": {"key": t.redacts.id, "grant": t.v["act"]["grant"]},
            "to": t.alice.id,
            "decider": t.decides.id,
            "log": log.entries()[0]["hash"],
            "entry": t.entry(),
            "field": "text",
            "hashed": apart::fingerprint_text(pair[0].as_str().unwrap(), "text", &pair[1])
                .unwrap(),
            "pad": pad,
        })
    );
}

/// A room of one entry that keeps `value` apart as its text, and that
/// entry's hash.
fn one_said(value: &Value, salt: &mut dyn FnMut() -> String) -> (Log, String) {
    let table = json!({"said": ["text"]});
    let mut log = Log::new(&table, &Map::new(), "world_created", salt).unwrap();
    let mut kept = Map::new();
    kept.insert("text".to_owned(), value.clone());
    let said = log
        .append(1, "said", None, &Map::new(), &kept, salt)
        .unwrap();
    (log, said)
}

#[test]
fn whatever_a_log_can_keep_apart_can_be_redacted() {
    // Among them a map with a key that is not ASCII, which no signed
    // record could hold as a key of its own: a copy carries what was
    // hashed, as text.
    let t = Trial::new();
    let room: Value = serde_json::from_str(ROOM).unwrap();
    let values: Vec<&Value> = room["fingerprints"]
        .as_array()
        .unwrap()
        .iter()
        .map(|f| &f["value"])
        .collect();
    assert_eq!(values.len(), 18, "the vectors are all there");
    assert!(values.iter().any(|v| {
        v.as_object()
            .is_some_and(|m| m.keys().any(|k| !k.is_ascii()))
    }));
    let none = Map::new();
    for value in values {
        let mut salt = trial_salts();
        let (mut log, said) = one_said(value, &mut salt);
        let its_salt = log.contents()[&said]["text"][0]
            .as_str()
            .unwrap()
            .to_owned();
        let made = redact(
            &mut log,
            &Act {
                tick: 2,
                entry: &said,
                field: "text",
                ground: &t.v["act"]["ground"],
                created: t.v["created"].as_str().unwrap(),
                about: &[t.alice.recipient()],
                decider: t.decides.recipient(),
                agent: None,
                apart: &none,
            },
            &t.office(),
            None,
            &mut salt,
        )
        .unwrap();
        assert_eq!(state(&log, &said, "text"), State::Redacted, "{value}");
        let inside = open_copy(&made.copies[0], t.alice.opener(), &entries(&log)).unwrap();
        assert_eq!(
            what_was_there(&inside),
            Some((its_salt.clone(), value.clone())),
            "{value}"
        );
        // This room's table keeps nothing of a decision apart.
        let answer = Answer {
            tick: 3,
            mark: &made.mark,
            by: Decided {
                office: t.v["kept"]["office"].as_str().unwrap(),
                ground: &t.v["kept"]["ground"],
                decision: t.v["kept"]["decision"].as_str().unwrap(),
                agent: None,
            },
            apart: &none,
        };
        keep_public(
            &mut log,
            &answer,
            &made.office_copy,
            t.decides.opener(),
            &mut salt,
        )
        .unwrap();
        assert_eq!(log.contents()[&said]["text"], json!([its_salt, value]));
        let joined = apart::join(&entries(&log), &contents(&log)).unwrap();
        assert_eq!(&joined[1]["data"]["text"], value);
    }
}

#[test]
fn a_copys_length_says_little_of_what_was_there() {
    // Before it is signed, a record is 1024 bytes or the next power of
    // two. A signature's text is 87 or 88 characters, whatever was
    // signed, so two boxes of one size differ by a byte at most.
    let t = Trial::new();
    let none = Map::new();
    let mut sizes: std::collections::BTreeMap<usize, Vec<usize>> = Default::default();
    for length in [0, 1, 11, 200, 400, 600, 1500, 5000] {
        let mut salt = trial_salts();
        let (mut log, said) = one_said(&json!("x".repeat(length)), &mut salt);
        let made = redact(
            &mut log,
            &Act {
                tick: 2,
                entry: &said,
                field: "text",
                ground: &t.v["act"]["ground"],
                created: t.v["created"].as_str().unwrap(),
                about: &[t.alice.recipient()],
                decider: t.decides.recipient(),
                agent: None,
                apart: &none,
            },
            &t.office(),
            None,
            &mut salt,
        )
        .unwrap();
        let mut inside = open_copy(&made.office_copy, t.decides.opener(), &entries(&log)).unwrap();
        inside.as_object_mut().unwrap().remove("proof");
        let size = canonical(&inside).unwrap().len();
        assert!(size.is_power_of_two(), "{length}: {size}");
        assert!(size >= PADDED, "{length}: {size}");
        assert!(inside["pad"].as_str().unwrap().bytes().all(|b| b == b'0'));
        for envelope in [&made.copies[0], &made.office_copy] {
            sizes
                .entry(size)
                .or_default()
                .push(envelope["box"].as_str().unwrap().len() / 2);
        }
    }
    // Five short values share the smallest size.
    let all: Vec<&usize> = sizes.keys().collect();
    assert_eq!(all, [&1024, &2048, &4096, &8192]);
    assert_eq!(sizes[&1024].len(), 10);
    for (size, boxes) in &sizes {
        let (least, most) = (boxes.iter().min().unwrap(), boxes.iter().max().unwrap());
        assert!(most - least <= 1, "{size}: {boxes:?}");
    }
}

#[test]
fn the_copies_are_handed_over_before_anything_is_written() {
    let t = Trial::new();
    let mut salt = trial_salts();
    let mut log = room(&mut salt);
    let before = (log.entries().to_vec(), log.contents().clone());
    let none = Map::new();
    let act = Act {
        tick: 5,
        entry: t.entry(),
        field: "text",
        ground: &t.v["act"]["ground"],
        created: t.v["created"].as_str().unwrap(),
        about: &[t.alice.recipient()],
        decider: t.decides.recipient(),
        agent: None,
        apart: &none,
    };
    // If they can't be kept, nothing is marked and nothing taken out.
    let mut full = |_: &[Value], _: &Value| Err("no room for them".to_owned());
    assert_eq!(
        redact(&mut log, &act, &t.office(), Some(&mut full), &mut salt),
        Err(Refused::Store("no room for them".to_owned()))
    );
    assert_eq!(log.entries(), before.0.as_slice());
    assert_eq!(log.contents(), &before.1);
    // They are handed over once, as the act gives them back.
    let mut seen: Vec<(Vec<Value>, Value)> = Vec::new();
    let mut keep = |copies: &[Value], office_copy: &Value| {
        seen.push((copies.to_vec(), office_copy.clone()));
        Ok(())
    };
    let made = redact(&mut log, &act, &t.office(), Some(&mut keep), &mut salt).unwrap();
    assert_eq!(seen, [(made.copies.clone(), made.office_copy.clone())]);
    assert_eq!(state(&log, t.entry(), "text"), State::Redacted);

    // The same for a redaction finished after its mark.
    let mut salt = trial_salts();
    let mut log = room(&mut salt);
    let by = apart::Office {
        office: "trial office",
        ground: &t.v["act"]["ground"],
        agent: None,
    };
    let mark = log
        .mark(5, t.entry(), "text", by, &Map::new(), &mut salt)
        .unwrap();
    let created = t.v["created"].as_str().unwrap();
    assert_eq!(
        finish(
            &mut log,
            &mark,
            &t.office(),
            created,
            &[],
            t.decides.recipient(),
            Some(&mut full)
        ),
        Err(Refused::Store("no room for them".to_owned()))
    );
    assert_eq!(state(&log, t.entry(), "text"), State::Unfinished);
    let mut seen: Vec<(Vec<Value>, Value)> = Vec::new();
    let mut keep = |copies: &[Value], office_copy: &Value| {
        seen.push((copies.to_vec(), office_copy.clone()));
        Ok(())
    };
    let made = finish(
        &mut log,
        &mark,
        &t.office(),
        created,
        &[],
        t.decides.recipient(),
        Some(&mut keep),
    )
    .unwrap();
    assert_eq!(seen, [(Vec::new(), made.office_copy.clone())]);
    assert_eq!(state(&log, t.entry(), "text"), State::Redacted);
}

// The office that decides need not be the writer that redacted. It opens
// the log and the contents as they were published (`Log::open`) and goes
// on from the log's head.

#[test]
fn the_office_decides_on_a_log_it_opens() {
    let t = Trial::new();
    let case = &t.v["redacted"];
    let mut log = Log::open(&case["log"], &case["contents"]).unwrap();
    let mut salt = trial_salts_after(&case["log"]);
    let mark = case["mark"].as_str().unwrap();
    let envelope = &t.v["copies"][2]["envelope"];
    t.decide("kept", mark, |answer| {
        keep_public(&mut log, answer, envelope, t.decides.opener(), &mut salt)
    })
    .unwrap();
    assert_eq!(entries(&log), t.v["kept"]["log"]);
    assert_eq!(contents(&log), t.v["kept"]["contents"]);
}

#[test]
fn that_it_stays_redacted_is_decided_on_a_log_it_opens() {
    let t = Trial::new();
    let case = &t.v["redacted"];
    let mut log = Log::open(&case["log"], &case["contents"]).unwrap();
    let mut salt = trial_salts_after(&case["log"]);
    t.decide("stays", case["mark"].as_str().unwrap(), |answer| {
        stays_redacted(&mut log, answer, &mut salt)
    })
    .unwrap();
    assert_eq!(entries(&log), t.v["stays"]["log"]);
    assert_eq!(contents(&log), t.v["stays"]["contents"]);
}

#[test]
fn a_field_is_redacted_on_a_log_opened_again() {
    let t = Trial::new();
    let mut first = trial_salts();
    let before = room(&mut first);
    let its_salt = before.contents()[t.entry()]["text"][0]
        .as_str()
        .unwrap()
        .to_owned();
    let written = entries(&before);
    let mut log = Log::open(&written, &contents(&before)).unwrap();
    let mut salt = trial_salts_after(&written);
    let act = &t.v["act"];
    let about = [t.alice.recipient(), t.bob.recipient()];
    let made = redact(
        &mut log,
        &Act {
            tick: act["tick"].as_u64().unwrap(),
            entry: t.entry(),
            field: "text",
            ground: &act["ground"],
            created: t.v["created"].as_str().unwrap(),
            about: &about,
            decider: t.decides.recipient(),
            agent: None,
            apart: &map(&act["apart"]),
        },
        &t.office(),
        None,
        &mut salt,
    )
    .unwrap();
    assert_eq!(made.mark, t.v["redacted"]["mark"].as_str().unwrap());
    assert_eq!(entries(&log), t.v["redacted"]["log"]);
    assert_eq!(contents(&log), t.v["redacted"]["contents"]);
    // The writer that was opened holds neither the value nor its salt
    // after the act, as the one that wrote the log does not.
    let held = format!("{log:?}{made:?}");
    assert!(format!("{before:?}").contains(&its_salt));
    assert!(!held.contains(&its_salt));
    assert!(!held.contains(VALUE));
}

#[test]
fn a_redaction_that_stands_with_its_field_left_in_is_finished() {
    // A log whose redaction stands, published with the field still in
    // its contents: no writer here leaves that, but a published log can
    // show it, and the check calls the field unfinished.
    let t = Trial::new();
    let stays = &t.v["stays"];
    let mut first = trial_salts();
    let before = room(&mut first);
    let mut left_in = stays["contents"].clone();
    left_in[t.entry()]["text"] = before.contents()[t.entry()]["text"].clone();
    assert_eq!(
        apart::check(&stays["log"], &left_in).unwrap()[t.entry()]["text"],
        State::Unfinished
    );
    let mut log = Log::open(&stays["log"], &left_in).unwrap();
    let mut salt = trial_salts_after(&stays["log"]);
    let mark = t.v["redacted"]["mark"].as_str().unwrap();
    let made = finish(
        &mut log,
        mark,
        &t.office(),
        t.v["created"].as_str().unwrap(),
        &[],
        t.decides.recipient(),
        None,
    )
    .unwrap();
    assert_eq!(entries(&log), stays["log"], "the log is not touched");
    assert_eq!(contents(&log), stays["contents"]);
    assert_eq!(state(&log, t.entry(), "text"), State::Redacted);
    // The copy made is the field, though no decision can use it: the
    // redaction stands.
    let inside = open_copy(&made.office_copy, t.decides.opener(), &entries(&log)).unwrap();
    assert_eq!(what_was_there(&inside).unwrap().1, VALUE);
    let error = t
        .decide("kept", mark, |answer| {
            keep_public(
                &mut log,
                answer,
                &made.office_copy,
                t.decides.opener(),
                &mut salt,
            )
        })
        .unwrap_err();
    assert!(matches!(
        error,
        Refused::Log(apart::Refused::BadKept { .. })
    ));
}
