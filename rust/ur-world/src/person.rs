// rust/ur-world/src/person.rs
//! A person's client (docs/research/PERSONS.md; course step 3a, part
//! three). It holds a person's identity key and presence seed, makes the
//! key of each presence from the seed and its world
//! ([`formats::persons::presence_secret`]), signs each presence's
//! arrivals, and signs both halves of a link when the person chooses to
//! show one ([`crate::link`]).
//!
//! Information flows through the person (decision 7): the client runs
//! every presence's mind, so a note taken by a presence in one world is
//! the person's, and reaches another world only through what a presence
//! of theirs says there. No world hears another behind the person's back.
//!
//! [`trial`] is a person's Hello World: one trial person, with a presence
//! in each of three trial worlds at once. In the first, a local says
//! something, and the presence there writes it down; the person's
//! presence in the second says it in its own world on the same tick; the
//! presence in the third shows its link. The first two worlds never see
//! the person's key, and the third sees it only in the link its presence
//! showed.
//!
//! # Limits
//!
//! - **Trial persons only.** Their identity keys and seeds are made from
//!   labels ([`Person::trial`]), so anyone can make them. Where a real
//!   seed is kept waits for the founder (decision 13).
//! - **No person's list yet.** The client knows each presence by its world
//!   and counter; the list (`open-worlds/person-list/v1`) is checked in
//!   `formats`, but not kept here.
//! - **One presence per world, each with counter 0**, in the trial.
//!   Several in one world (decision 9) are allowed by the world, and
//!   tested, but not shown in the trial.

use std::cell::RefCell;
use std::rc::Rc;

use formats::persons::{HELD_BY, HOLDS, presence_key, presence_secret};
use formats::proof::{self, public_key};
use serde_json::{Value, json};

use crate::arrival::{self, did, trial_secret};
use crate::garden::{FIRST_AT, SECOND_AT, Script};
use crate::world::{Action, Mind, Observation, World};

/// The trial's seed: the day part three was built, 2026-11-15.
pub const SEED: u64 = 20_261_115;

/// The trial person's label, from which their trial keys are made.
pub const PERSON: &str = "a trial person";

/// When the trial's arrivals, links and heads say they were signed: a
/// fixed time, so the trial is the same on every run. A proof's `created`
/// is no evidence of when anything happened.
pub const CREATED: &str = "2026-11-15T00:00:00Z";

/// How many ticks each of the trial's worlds runs.
pub const TICKS: u64 = 3;

/// The trial's worlds, with the name of the person's presence in each:
/// each a name of its own, since one name everywhere would link them
/// (decision 3).
pub const WORLDS: [(&str, &str); 3] = [
    ("the first trial world", "ASH"),
    ("the second trial world", "BIRCH"),
    ("the third trial world", "CEDAR"),
];

/// What the local in the first trial world says.
pub const LESSON: &str = "The spring is south-east of the tree.";

/// A person, as their client holds them: their identity key, which never
/// enters a world (decision 1), and their presence seed, from which every
/// presence's key is made. Neither is ever shown.
pub struct Person {
    identity: [u8; 32],
    seed: [u8; 32],
}

impl Person {
    /// A person with this identity key's secret and this presence seed.
    pub const fn new(identity: [u8; 32], seed: [u8; 32]) -> Person {
        Person { identity, seed }
    }

    /// A trial person: an identity key and a presence seed made from
    /// `seed` and `label`, as trial keys are ([`trial_secret`]). Anyone
    /// who knows them can make the same: for trial worlds, tests and the
    /// shared vectors only, never for an individual.
    pub fn trial(seed: u64, label: &str) -> Person {
        Person {
            identity: trial_secret(seed, &format!("{label}: identity")),
            seed: trial_seed(seed, label),
        }
    }

    /// The person's identity key, as a did:key.
    pub fn key(&self) -> String {
        did(&self.identity)
    }

    /// The key of the presence `counter` in `world` (a did:key).
    pub fn presence(&self, world: &str, counter: u32) -> Result<String, String> {
        presence_key(&self.seed, world, counter)
    }

    /// The arrival of the presence `counter` into `world` as it is now,
    /// under `name`, signed by the presence ([`arrival::sign`]).
    pub fn arrival(
        &self,
        world: &World,
        counter: u32,
        name: &str,
        created: &str,
    ) -> Result<Value, String> {
        let secret = presence_secret(&self.seed, world.key(), counter)?;
        arrival::sign(world, &secret, name, created)
    }

    /// Both halves of the link between the person and their presence
    /// `counter` in `world` (a did:key), each signed at `time`: the
    /// person's `holds`, signed by their identity key, and the presence's
    /// `held-by`, signed by the presence. Only the presence can show it,
    /// by its own act in its world ([`Action::ShowLink`]).
    pub fn link(&self, world: &str, counter: u32, time: &str) -> Result<(Value, Value), String> {
        let secret = presence_secret(&self.seed, world, counter)?;
        let (person, presence) = (self.key(), did(&secret));
        let holds = json!({
            "format": HOLDS,
            "person": person,
            "presence": presence,
            "world": world,
            "time": time,
        });
        let held_by = json!({
            "format": HELD_BY,
            "presence": presence,
            "person": person,
            "world": world,
            "time": time,
        });
        Ok((
            proof::sign(&holds, &self.identity, time, "assertionMethod")?,
            proof::sign(&held_by, &secret, time, "assertionMethod")?,
        ))
    }
}

/// The presence seed of the trial person made from `seed` and `label`
/// ([`Person::trial`]): public, as every trial key is.
pub fn trial_seed(seed: u64, label: &str) -> [u8; 32] {
    trial_secret(seed, &format!("{label}: presence seed"))
}

/// The notes a person's client carries between their presences: the
/// person's own, never a world's (decision 7). Shared by the minds it
/// runs; a clone is the same notebook.
#[derive(Debug, Clone, Default)]
pub struct Notebook(Rc<RefCell<Vec<String>>>);

impl Notebook {
    /// Write a note.
    pub fn write(&self, note: &str) {
        self.0.borrow_mut().push(note.to_owned());
    }

    /// Every note, in the order written.
    pub fn notes(&self) -> Vec<String> {
        self.0.borrow().clone()
    }
}

/// A presence's mind that writes down, in the person's notebook,
/// whatever others say in its world, and otherwise waits.
#[derive(Debug, Clone)]
pub struct Listens {
    notes: Notebook,
}

impl Listens {
    /// A mind that writes into `notes`.
    pub const fn new(notes: Notebook) -> Listens {
        Listens { notes }
    }
}

impl Mind for Listens {
    fn act(&mut self, seen: &Observation) -> Action {
        for (who, said) in &seen.heard {
            if *who != seen.me {
                self.notes.write(said);
            }
        }
        Action::Wait
    }
}

/// A presence's mind that says, one a tick, each note in the person's
/// notebook it hasn't said yet, and otherwise waits: what a presence of
/// theirs learned in another world, said in this one.
#[derive(Debug, Clone)]
pub struct Tells {
    notes: Notebook,
    told: usize,
}

impl Tells {
    /// A mind that tells what is in `notes`.
    pub const fn new(notes: Notebook) -> Tells {
        Tells { notes, told: 0 }
    }
}

impl Mind for Tells {
    fn act(&mut self, _seen: &Observation) -> Action {
        match self.notes.notes().get(self.told) {
            Some(note) => {
                self.told += 1;
                Action::Say(note.clone())
            }
            None => Action::Wait,
        }
    }
}

/// The person's Hello World, as [`trial`] leaves it.
pub struct Trial {
    /// The trial person.
    pub person: Person,
    /// The three trial worlds of [`WORLDS`], in that order, each with
    /// one of the person's presences.
    pub worlds: Vec<World>,
    /// What the person's client carried between them.
    pub notes: Notebook,
}

/// The trial key of the trial world `name`.
pub fn world_secret(name: &str) -> [u8; 32] {
    trial_secret(SEED, name)
}

/// The person's Hello World ([`crate::person`]): a trial person with a
/// presence in each of three trial worlds at once, run tick by tick in
/// step. In the first, a local, TEACHER, says [`LESSON`], and the
/// presence there writes it down; the presence in the second world says
/// it there on the same tick, since the first world takes its tick first;
/// the presence in the third shows its link on the second tick.
pub fn trial() -> Result<Trial, String> {
    let person = Person::trial(SEED, PERSON);
    let notes = Notebook::default();
    let mut worlds = Vec::new();
    for (i, (label, name)) in WORLDS.iter().enumerate() {
        let index = u64::try_from(i).map_err(|e| e.to_string())?;
        let mut world = World::new(SEED + index, &public_key(&world_secret(label)));
        let mind: Box<dyn Mind> = match i {
            0 => Box::new(Listens::new(notes.clone())),
            1 => Box::new(Tells::new(notes.clone())),
            _ => {
                let (holds, held_by) = person.link(world.key(), 0, CREATED)?;
                Box::new(Script::new([
                    Action::Wait,
                    Action::ShowLink { holds, held_by },
                ]))
            }
        };
        let arrival = person.arrival(&world, 0, name, CREATED)?;
        world
            .enter(&arrival, mind, FIRST_AT)
            .map_err(|e| format!("{name} can't enter {label}: {e}"))?;
        if i == 0 {
            let local = trial_secret(SEED, "TEACHER");
            let arrival = arrival::sign(&world, &local, "TEACHER", CREATED)?;
            let script = Script::new([Action::Say(LESSON.to_owned())]);
            world
                .enter(&arrival, Box::new(script), SECOND_AT)
                .map_err(|e| format!("TEACHER can't enter {label}: {e}"))?;
        }
        worlds.push(world);
    }
    for _ in 0..TICKS {
        for world in &mut worlds {
            world.step();
        }
    }
    Ok(Trial {
        person,
        worlds,
        notes,
    })
}

/// The trial as shared vectors (`vectors/ur-person.json`): the trial
/// person's key; their presence seed (public, as every trial key is),
/// with the words it is the SHA-256 of; and for each world its log, the
/// head its world signed, and the person's presence there, by name,
/// counter and key.
pub fn vectors(trial: &Trial) -> Result<Value, String> {
    let seed: String = trial_seed(SEED, PERSON)
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect();
    let mut worlds = Vec::new();
    for ((label, name), world) in WORLDS.iter().zip(&trial.worlds) {
        worlds.push(json!({
            "name": label,
            "log": world.log(),
            "head": arrival::head(world, &world_secret(label), CREATED)?,
            "presence": {
                "name": name,
                "counter": 0,
                "key": trial.person.presence(world.key(), 0)?,
            },
        }));
    }
    Ok(json!({
        "description": "A person's Hello World (rust/ur-world/src/person.rs): one trial person with a presence in each of three trial worlds at once. A local in the first says something, which the presence there writes down; the presence in the second says it in its world; the presence in the third shows its link. Written by `cargo run -p ur-world --example person -- --vectors ../vectors`. The person's keys and seed are trial keys made from labels, never anyone's.",
        "person": trial.person.key(),
        "seed": {
            "label": PERSON,
            "from": format!("open-worlds trial key, never for anything real: {SEED}: {PERSON}: presence seed"),
            "hex": seed,
        },
        "lesson": LESSON,
        "worlds": worlds,
    }))
}
