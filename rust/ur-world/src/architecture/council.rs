// rust/ur-world/src/architecture/council.rs
//! The council (DeepSeek's components 44 to 46; PERSONS.md, decision 8):
//! several persons, each counted once on a council's proposal, by their
//! identity keys, and only those whose birth a world the council trusts
//! signed.
//!
//! - **The council** signs a proposal: its choices, when votes count, its
//!   quorum, and the worlds whose births it trusts
//!   ([`formats::council`]).
//! - **Each person's client** signs their vote with their identity key
//!   ([`Person::vote`]). A vote is the person's, never a presence's.
//! - **Anyone counts again** from the records: the proposal, the votes and
//!   the births ([`formats::council::tally`]).
//! - **A world can't count persons** (decision 8). The council's world
//!   sees five inhabitants, presences of four persons (the first person
//!   has two there), and the council counts three: the fourth person's
//!   birth was signed by a world it doesn't trust.
//!
//! The run ([`run`]): four persons' presences enter the council's world,
//! the first person's twice. The council proposes planting the north bed;
//! the first two persons vote yes; the third votes no, then changes to yes
//! before the proposal closes; the fourth votes no, but was born in a far
//! world the council doesn't trust. Three persons are counted, all yes,
//! and the proposal passes.

use formats::council::{BIRTH, PROPOSAL, Tally, tally};
use formats::proof;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

use crate::architecture::{CREATED, SEED, trial_world, world_secret};
use crate::arrival::did;
use crate::garden::Script;
use crate::person::Person;
use crate::space::Cell;
use crate::world::World;

/// The council's world: it holds the council's key, and signs the births
/// the council trusts.
pub const COUNCIL_WORLD: &str = "the council's world";

/// A world whose births the council doesn't trust.
pub const FAR_WORLD: &str = "a far world";

/// A person: their label, the world of their birth, and their presences
/// in the council's world, each by its name there and where it enters.
pub type Member = (&'static str, &'static str, &'static [(&'static str, Cell)]);

/// The persons, in order: the first three born in the council's world,
/// the fourth in a far world.
pub const PERSONS: [Member; 4] = [
    (
        "a council member: one",
        COUNCIL_WORLD,
        &[
            ("WILLOW", Cell::new(-3, 1, 0)),
            ("ALDER", Cell::new(-3, 1, 2)),
        ],
    ),
    (
        "a council member: two",
        COUNCIL_WORLD,
        &[("ROWAN", Cell::new(3, 1, 0))],
    ),
    (
        "a council member: three",
        COUNCIL_WORLD,
        &[("HAZEL", Cell::new(0, 1, -3))],
    ),
    (
        "a council member: four",
        FAR_WORLD,
        &[("YEW", Cell::new(0, 1, 3))],
    ),
];

/// When the proposal opens, and closes.
pub const OPENS: &str = "2026-11-15T03:00:00Z";
/// When the proposal closes.
pub const CLOSES: &str = "2026-11-15T05:00:00Z";

/// The council, as [`run`] leaves it.
pub struct Council {
    /// The persons, in [`PERSONS`]' order.
    pub persons: Vec<Person>,
    /// The council's world, with the persons' presences in it.
    pub world: World,
    /// The council's proposal.
    pub proposal: Value,
    /// The votes, in the order they were cast.
    pub votes: Vec<Value>,
    /// The birth records the count was given.
    pub births: Vec<Value>,
    /// The count.
    pub tally: Tally,
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

/// The birth record of `person`, signed by the trial world `world`.
fn birth(world: &str, person: &Person, label: &str) -> Result<Value, String> {
    let secret = world_secret(world);
    let record = json!({
        "format": BIRTH,
        "world": did(&secret),
        "individual": person.key(),
        "name": label.rsplit(' ').next().unwrap_or(label).to_uppercase(),
        "tick": 0,
        "time": CREATED,
        "mind": hex(&Sha256::digest(format!("a trial mind record for {label}"))),
        "words": format!("You came into being in {world}. A trial, for the council."),
    });
    proof::sign(&record, &secret, CREATED, "assertionMethod")
}

/// The council's run ([`crate::architecture::council`]).
pub fn run() -> Result<Council, String> {
    let council = world_secret(COUNCIL_WORLD);
    let mut world = trial_world(COUNCIL_WORLD, SEED);
    let mut persons = Vec::new();
    let mut births = Vec::new();
    for (label, born_in, presences) in PERSONS {
        let person = Person::trial(SEED, label);
        births.push(birth(born_in, &person, label)?);
        for (counter, (name, at)) in (0_u32..).zip(presences.iter()) {
            let arrival = person.arrival(&world, counter, name, CREATED)?;
            world
                .enter(&arrival, Box::new(Script::new([])), *at)
                .map_err(|e| format!("{name} can't enter: {e}"))?;
        }
        persons.push(person);
    }
    let proposal = proof::sign(
        &json!({
            "format": PROPOSAL,
            "council": did(&council),
            "title": "The north bed",
            "text": "Plant the north bed with flowers this season.",
            "choices": ["yes", "no"],
            "trusts": [did(&council)],
            "quorum": 3,
            "opens": OPENS,
            "closes": CLOSES,
        }),
        &council,
        CREATED,
        "assertionMethod",
    )?;
    let (during, later) = ("2026-11-15T04:00:00Z", "2026-11-15T04:30:00Z");
    let cast = [
        (0, 0, during),
        (1, 0, during),
        (2, 1, during),
        (2, 0, later),
        (3, 1, during),
    ];
    let mut votes = Vec::new();
    for (who, choice, time) in cast {
        let person = persons.get(who).ok_or("no such person")?;
        votes.push(person.vote(&proposal, choice, time)?);
    }
    let tally = tally(&proposal, &votes, &births);
    world.run(1);
    Ok(Council {
        persons,
        world,
        proposal,
        votes,
        births,
        tally,
    })
}

/// The council's key, as a did:key: its world's.
pub fn council_key() -> String {
    did(&world_secret(COUNCIL_WORLD))
}
