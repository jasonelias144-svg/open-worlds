// rust/ur-world/tests/person.rs
//! A person in the Ur-world (course step 3a, part three): the trial is
//! what the shared vectors record; a lesson goes from one world to another
//! only through the person; each presence is a key of its own, made from
//! the person's seed; a presence shows its own link, and the world takes
//! it, or refuses it and logs neither its records nor why, and a log check
//! finds every link the world would have refused.

// Tests may unwrap, expect, panic and index: a failure here is a failed
// test, not a world that crashed.
#![allow(
    clippy::unwrap_used,
    clippy::expect_used,
    clippy::panic,
    clippy::indexing_slicing
)]

use std::cell::RefCell;
use std::collections::VecDeque;
use std::rc::Rc;

use formats::persons::{link_problems, presence_key};
use formats::proof::public_key;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use ur_world::arrival::{arrival_problems, trial_secret};
use ur_world::door::{describe, observation};
use ur_world::garden::{FIRST_AT, SECOND_AT};
use ur_world::link::{Refusal, link_log_problems};
use ur_world::person::{
    CREATED, LESSON, PERSON, Person, SEED, TICKS, WORLDS, trial, trial_seed, vectors,
};
use ur_world::{Action, Cell, Mind, Observation, Outcome, World};

const VECTORS: &str = include_str!("../../../vectors/ur-person.json");

/// A mind that plays its actions, one a tick, then waits, and keeps what
/// it is told came of each.
struct Recorded {
    actions: VecDeque<Action>,
    told: Rc<RefCell<Vec<Outcome>>>,
}

impl Mind for Recorded {
    fn act(&mut self, seen: &Observation) -> Action {
        if let Some(last) = &seen.last {
            self.told.borrow_mut().push(last.clone());
        }
        self.actions.pop_front().unwrap_or(Action::Wait)
    }
}

fn person() -> Person {
    Person::trial(SEED, PERSON)
}

fn world(label: &str) -> World {
    World::new(SEED, &public_key(&trial_secret(SEED, label)))
}

/// The person's presence `counter` enters `world` as `name`, at `at`,
/// playing `actions`; what it is told comes back in the list returned.
fn enter(
    world: &mut World,
    person: &Person,
    counter: u32,
    name: &str,
    at: Cell,
    actions: Vec<Action>,
) -> Rc<RefCell<Vec<Outcome>>> {
    let told = Rc::new(RefCell::new(Vec::new()));
    let mind = Recorded {
        actions: actions.into(),
        told: Rc::clone(&told),
    };
    let arrival = person.arrival(world, counter, name, CREATED).unwrap();
    world.enter(&arrival, Box::new(mind), at).unwrap();
    told
}

fn show((holds, held_by): (Value, Value)) -> Action {
    Action::ShowLink { holds, held_by }
}

fn of_kind<'a>(log: &'a [Value], kind: &str) -> Vec<&'a Value> {
    log.iter().filter(|e| e["kind"] == kind).collect()
}

fn text(entries: &[Value]) -> String {
    Value::Array(entries.to_vec()).to_string()
}

#[test]
fn the_trial_is_what_the_vectors_record() {
    // Rewrite with: cargo run -p ur-world --example person -- --vectors ../vectors
    let recorded: Value = serde_json::from_str(VECTORS).unwrap();
    assert_eq!(vectors(&trial().unwrap()).unwrap(), recorded);
    // The seed in them is a trial key's: the hash of words that say so.
    let from = recorded["seed"]["from"].as_str().unwrap();
    assert!(from.contains("never for anything real"));
    let made: [u8; 32] = Sha256::digest(from).into();
    assert_eq!(made, trial_seed(SEED, PERSON));
}

#[test]
fn a_lesson_goes_through_the_person_and_no_world_sees_another() {
    let trial = trial().unwrap();
    assert_eq!(trial.notes.notes(), vec![LESSON.to_owned()]);
    let said = |w: usize| -> Vec<(u64, String, String)> {
        of_kind(trial.worlds[w].log(), "said")
            .iter()
            .map(|e| {
                (
                    e["tick"].as_u64().unwrap(),
                    e["agent"].as_str().unwrap().to_owned(),
                    e["data"]["text"].as_str().unwrap().to_owned(),
                )
            })
            .collect()
    };
    // Said in the first world at tick 0, heard there at tick 1, and said
    // in the second world at tick 1, since the first takes its tick first.
    assert_eq!(said(0), vec![(0, "TEACHER".into(), LESSON.into())]);
    assert_eq!(said(1), vec![(1, "BIRCH".into(), LESSON.into())]);
    assert!(said(2).is_empty());

    let person = trial.person.key();
    let keys: Vec<(String, String)> = trial
        .worlds
        .iter()
        .map(|w| {
            (
                w.key().to_owned(),
                trial.person.presence(w.key(), 0).unwrap(),
            )
        })
        .collect();
    for (i, w) in trial.worlds.iter().enumerate() {
        world_log::verify_log(&Value::Array(w.log().to_vec())).unwrap();
        let log = text(w.log());
        assert_eq!(arrival_problems(w.log()), Vec::<String>::new(), "world {i}");
        assert_eq!(
            link_log_problems(w.log()),
            Vec::<String>::new(),
            "world {i}"
        );
        // No world's log names another world, or another world's presence.
        for (j, (world_key, presence)) in keys.iter().enumerate() {
            if i != j {
                assert!(!log.contains(world_key.as_str()), "{i} names {j}");
                assert!(!log.contains(presence.as_str()), "{i} names {j}'s");
            }
        }
        // Only the third names the person, and only in the link shown.
        let unlinked: Vec<Value> = w
            .log()
            .iter()
            .filter(|e| e["kind"] != "linked")
            .cloned()
            .collect();
        assert!(!text(&unlinked).contains(person.as_str()), "world {i}");
        let linked = of_kind(w.log(), "linked");
        assert_eq!(linked.len(), usize::from(i == 2), "world {i}");
        assert_eq!(w.held_by(&keys[i].1), (i == 2).then_some(person.as_str()));
    }
    let linked = of_kind(trial.worlds[2].log(), "linked")[0];
    assert_eq!(linked["agent"], "CEDAR");
    assert_eq!(linked["tick"], 1);
    assert!(link_problems(&linked["data"]["holds"], &linked["data"]["held_by"]).is_empty());
    assert_eq!(trial.worlds[2].tick(), TICKS);
}

#[test]
fn each_presence_is_a_key_of_its_own_made_from_the_seed() {
    let trial = trial().unwrap();
    let seed = trial_seed(SEED, PERSON);
    let mut seen = vec![trial.person.key()];
    for ((_, name), w) in WORLDS.iter().zip(&trial.worlds) {
        let key = trial.person.presence(w.key(), 0).unwrap();
        assert_eq!(key, presence_key(&seed, w.key(), 0).unwrap());
        assert_eq!(w.name_of(&key), Some(*name));
        assert!(!seen.contains(&key));
        seen.push(key);
    }
    // Another counter in the same world is another key.
    let first = trial.worlds[0].key();
    assert_ne!(
        trial.person.presence(first, 0).unwrap(),
        trial.person.presence(first, 1).unwrap()
    );
    // The identity key isn't made from the seed, and the seed isn't it.
    assert_ne!(trial_secret(SEED, &format!("{PERSON}: identity")), seed);
}

#[test]
fn a_presence_shows_its_own_link_and_is_told() {
    let person = person();
    let mut w = world("a world for links");
    let link = person.link(w.key(), 0, CREATED).unwrap();
    let told = enter(
        &mut w,
        &person,
        0,
        "WREN",
        FIRST_AT,
        vec![show(link.clone())],
    );
    w.run(2);
    assert_eq!(
        *told.borrow(),
        vec![Outcome::Linked {
            person: person.key()
        }]
    );
    let linked = of_kind(w.log(), "linked");
    assert_eq!(linked.len(), 1);
    assert_eq!(linked[0]["agent"], "WREN");
    assert_eq!(
        linked[0]["data"],
        json!({ "holds": link.0, "held_by": link.1 })
    );
    let wren = person.presence(w.key(), 0).unwrap();
    assert_eq!(w.held_by(&wren), Some(person.key().as_str()));
    assert_eq!(link_log_problems(w.log()), Vec::<String>::new());
}

#[test]
fn several_presences_in_one_world_are_separate_until_one_shows_its_link() {
    let person = person();
    let mut w = world("a world for links");
    let finch_link = person.link(w.key(), 1, CREATED).unwrap();
    enter(&mut w, &person, 0, "WREN", FIRST_AT, vec![]);
    enter(
        &mut w,
        &person,
        1,
        "FINCH",
        SECOND_AT,
        vec![show(finch_link)],
    );
    w.run(1);
    let (wren, finch) = (
        person.presence(w.key(), 0).unwrap(),
        person.presence(w.key(), 1).unwrap(),
    );
    assert_ne!(wren, finch);
    assert_eq!(w.held_by(&wren), None);
    assert_eq!(w.held_by(&finch), Some(person.key().as_str()));
    assert_eq!(arrival_problems(w.log()), Vec::<String>::new());
    assert_eq!(link_log_problems(w.log()), Vec::<String>::new());
}

/// What WREN (the person's presence 0) is told after playing `actions`,
/// with FINCH (presence 1) in the world too, and the world's log.
fn shown(actions: impl Fn(&World) -> Vec<Action>) -> (Vec<Outcome>, World) {
    let person = person();
    let mut w = world("a world for links");
    let actions = actions(&w);
    let ticks = u64::try_from(actions.len()).unwrap() + 1;
    let told = enter(&mut w, &person, 0, "WREN", FIRST_AT, actions);
    enter(&mut w, &person, 1, "FINCH", SECOND_AT, vec![]);
    w.run(ticks);
    let told = told.borrow().clone();
    (told, w)
}

#[test]
fn a_refused_link_is_logged_with_neither_its_records_nor_why() {
    let person = person();
    let other = Person::new(
        trial_secret(SEED, "another trial person: identity"),
        trial_seed(SEED, PERSON),
    );
    let elsewhere = world("another world");
    let tampered = |w: &World| {
        let (mut holds, held_by) = person.link(w.key(), 0, CREATED).unwrap();
        holds["time"] = json!("2026-11-16T00:00:00Z");
        (holds, held_by)
    };
    let halves = |w: &World| {
        let (holds, _) = person.link(w.key(), 0, CREATED).unwrap();
        let (_, held_by) = person.link(w.key(), 1, CREATED).unwrap();
        (holds, held_by)
    };
    type Case<'a> = (&'a str, Box<dyn Fn(&World) -> (Value, Value) + 'a>, Refusal);
    let cases: Vec<Case> = vec![
        (
            "a link for another world",
            Box::new(|_| person.link(elsewhere.key(), 0, CREATED).unwrap()),
            Refusal::OtherWorld,
        ),
        (
            "another presence's link, here",
            Box::new(|w| person.link(w.key(), 1, CREATED).unwrap()),
            Refusal::NotYours,
        ),
        (
            "a link changed after signing",
            Box::new(tampered),
            Refusal::DoesntHold(vec![]),
        ),
        (
            "the halves of two links",
            Box::new(halves),
            Refusal::DoesntHold(vec![]),
        ),
    ];
    for (name, link, expected) in cases {
        let refused = link(&world("a world for links"));
        let (told, w) = shown(|w| vec![show(link(w))]);
        assert_eq!(told.len(), 1, "{name}");
        match (&told[0], &expected) {
            (Outcome::LinkRefused(Refusal::DoesntHold(why)), Refusal::DoesntHold(_)) => {
                assert!(!why.is_empty(), "{name}");
            }
            (Outcome::LinkRefused(got), _) => assert_eq!(got, &expected, "{name}"),
            other => panic!("{name}: {other:?}"),
        }
        let blocked = of_kind(w.log(), "blocked");
        assert_eq!(blocked.len(), 1, "{name}");
        // Only that a link was refused: why is told to WREN alone.
        assert_eq!(blocked[0]["data"], json!({ "action": "show" }), "{name}");
        assert!(!text(w.log()).contains(expected.reason()), "{name}");
        assert!(of_kind(w.log(), "linked").is_empty(), "{name}");
        // Neither record, nor either signature, is in the log.
        for record in [&refused.0, &refused.1] {
            let signature = record["proof"]["proofValue"].as_str().unwrap();
            assert!(!text(w.log()).contains(signature), "{name}");
        }
        assert_eq!(w.held_by(&person.presence(w.key(), 0).unwrap()), None);
        assert_eq!(link_log_problems(w.log()), Vec::<String>::new(), "{name}");
    }

    // A link shown twice, and a link to another person after one is shown.
    for (name, second, expected) in [
        ("the same link again", &person, Refusal::Shown),
        ("another person's link", &other, Refusal::HeldByAnother),
    ] {
        let (told, w) = shown(|w| {
            vec![
                show(person.link(w.key(), 0, CREATED).unwrap()),
                show(second.link(w.key(), 0, CREATED).unwrap()),
            ]
        });
        assert_eq!(
            told,
            vec![
                Outcome::Linked {
                    person: person.key()
                },
                Outcome::LinkRefused(expected.clone())
            ],
            "{name}"
        );
        assert_eq!(of_kind(w.log(), "linked").len(), 1, "{name}");
        assert_eq!(
            w.held_by(&person.presence(w.key(), 0).unwrap()),
            Some(person.key().as_str()),
            "{name}"
        );
        let blocked = of_kind(w.log(), "blocked");
        assert_eq!(blocked[0]["data"], json!({ "action": "show" }), "{name}");
        // The other person is named nowhere in the log.
        assert!(!text(w.log()).contains(other.key().as_str()), "{name}");
    }
}

#[test]
fn a_presence_that_leaves_and_comes_back_is_still_held_by_its_person() {
    let person = person();
    let other = Person::new(
        trial_secret(SEED, "another trial person: identity"),
        trial_seed(SEED, PERSON),
    );
    let mut w = world("a world for links");
    let link = person.link(w.key(), 0, CREATED).unwrap();
    let others = other.link(w.key(), 0, CREATED).unwrap();
    let first = enter(
        &mut w,
        &person,
        0,
        "WREN",
        FIRST_AT,
        vec![show(link.clone()), Action::Exit],
    );
    w.run(2);
    assert_eq!(w.position("WREN"), None);
    let again = enter(
        &mut w,
        &person,
        0,
        "WREN",
        FIRST_AT,
        vec![show(link), show(others)],
    );
    w.run(3);
    assert_eq!(
        *first.borrow(),
        vec![Outcome::Linked {
            person: person.key()
        }]
    );
    assert_eq!(
        *again.borrow(),
        vec![
            Outcome::LinkRefused(Refusal::Shown),
            Outcome::LinkRefused(Refusal::HeldByAnother)
        ]
    );
    assert_eq!(of_kind(w.log(), "linked").len(), 1);
    assert_eq!(of_kind(w.log(), "blocked").len(), 2);
    assert_eq!(of_kind(w.log(), "entered").len(), 2);
    assert_eq!(
        w.held_by(&person.presence(w.key(), 0).unwrap()),
        Some(person.key().as_str())
    );
    assert!(!text(w.log()).contains(other.key().as_str()));
    assert_eq!(arrival_problems(w.log()), Vec::<String>::new());
    assert_eq!(link_log_problems(w.log()), Vec::<String>::new());
}

#[test]
fn the_log_check_finds_every_link_the_world_would_refuse() {
    let person = person();
    let (_, w) = shown(|w| vec![show(person.link(w.key(), 0, CREATED).unwrap())]);
    let log = w.log().to_vec();
    assert_eq!(link_log_problems(&log), Vec::<String>::new());
    let at = log.iter().position(|e| e["kind"] == "linked").unwrap();
    let changed = |change: &dyn Fn(&mut Vec<Value>)| {
        let mut log = log.clone();
        change(&mut log);
        link_log_problems(&log)
    };
    let trial = trial().unwrap();
    let cedar = of_kind(trial.worlds[2].log(), "linked")[0].clone();
    type Change<'a> = Box<dyn Fn(&mut Vec<Value>) + 'a>;
    let cases: Vec<(&str, Change, String)> = vec![
        (
            "shown by one who isn't here",
            Box::new(|log| log[at]["agent"] = json!("NOBODY")),
            format!("[{at}]: a link shown by one who isn't here"),
        ),
        (
            "with half of it missing",
            Box::new(|log| {
                log[at]["data"].as_object_mut().unwrap().remove("held_by");
            }),
            format!("[{at}]: an entry with no link"),
        ),
        (
            "shown by another inhabitant",
            Box::new(|log| log[at]["agent"] = json!("FINCH")),
            format!("[{at}]: a link the world refuses: the link is another presence's"),
        ),
        (
            "shown twice",
            Box::new(|log| {
                let again = log[at].clone();
                log.push(again);
            }),
            format!(
                "[{}]: a link the world refuses: this presence's link is shown here already",
                log.len()
            ),
        ),
        (
            "brought from another world",
            Box::new(|log| {
                let mut moved = cedar.clone();
                moved["agent"] = json!("WREN");
                log[at] = moved;
            }),
            format!("[{at}]: a link the world refuses: the link names another world"),
        ),
    ];
    for (name, change, expected) in cases {
        assert_eq!(changed(&*change), vec![expected], "{name}");
    }
    // A link changed after signing no longer holds.
    let found = changed(&|log| log[at]["data"]["holds"]["time"] = json!("2026-11-16T00:00:00Z"));
    assert_eq!(found.len(), 1);
    assert!(
        found[0].starts_with(&format!(
            "[{at}]: a link the world refuses: the link doesn't hold: holds:"
        )),
        "{found:?}"
    );
    // After WREN leaves, the link can't be shown in its name.
    let found = changed(&|log| {
        let mut gone = log[at].clone();
        gone["kind"] = json!("exited");
        gone["data"] = json!({ "reason": "requested" });
        let again = log[at].clone();
        log.push(gone);
        log.push(again);
    });
    assert_eq!(
        found,
        vec![format!(
            "[{}]: a link shown by one who isn't here",
            log.len() + 1
        )]
    );
    assert_eq!(
        link_log_problems(&[]),
        vec!["[0]: not a world_created entry that names its world".to_owned()]
    );
}

#[test]
fn the_doorway_tells_what_came_of_a_link() {
    let person = person().key();
    let seen = |last: Outcome| Observation {
        tick: 1,
        me: "WREN".into(),
        position: FIRST_AT,
        heard: vec![],
        around: vec![],
        others: vec![],
        last: Some(last),
    };
    let linked = seen(Outcome::Linked {
        person: person.clone(),
    });
    assert!(describe(&linked).contains(&format!(
        "Your last action: you showed your link: you are held by {person}."
    )));
    assert_eq!(
        observation(&linked)["last"],
        json!({ "kind": "linked", "person": person })
    );
    let refused = seen(Outcome::LinkRefused(Refusal::DoesntHold(vec![
        "the two halves name another presence".into(),
    ])));
    assert!(describe(&refused).contains(
        "Your last action: your link wasn't shown: the link doesn't hold: the two halves name another presence."
    ));
    assert_eq!(
        observation(&refused)["last"],
        json!({
            "kind": "link_refused",
            "why": "the link doesn't hold: the two halves name another presence",
        })
    );
}
