// rust/ur-world/src/garden.rs
//! Hello World for building worlds: a garden, and two who enter it.
//!
//! The founder: "It's like Hello World for building worlds: you start it
//! with a garden of two individuals." ALICE and BOB will be the first two
//! inhabitants of the Ur-world, and of the whole multiverse, but they are
//! born at the course's step 9, with the minds chosen at step 8, and their
//! first arrival is their birth (docs/research/KEYS.md, decision 15). Until
//! then the Hello World runs with two scripted stand-ins, WALKER and
//! GARDENER, enough to show that the world works: they greet each other
//! (one speaks, the other listens, then they turn), GARDENER plants a
//! flower, and WALKER walks out of the garden into land no one has seen,
//! which comes into view as WALKER goes.
//!
//! The garden also hosts three plant worlds, each in a glasshouse
//! ([`crate::host`]): the founder's "microverse garden of hosted fractal
//! worlds". Each is a world of its own (`rust/plant-world`), with its own
//! trial key and log, grown from the plant vectors' trial template with
//! dials of its own; the garden gives each a step of its time every tick,
//! until it finishes.
//!
//! The Hello World is a trial world of its own, not the Ur-world: its key,
//! and its stand-ins' keys, are trial keys made from the seed
//! ([`crate::arrival::trial_secret`]), so its log is the same on every
//! run, and anyone can make the same keys.

use std::collections::VecDeque;

use formats::proof::public_key;
use formats::records::record_hash;
use plant_world::rule::Dials;
use plant_world::vectors::{TRIAL_CODE, TRIAL_TIME};
use plant_world::world::{PlantWorld, law, law_hash, template};
use serde_json::{Value, json};

use crate::arrival::{self, trial_secret};
use crate::space::{Cell, Dir};
use crate::world::{Action, EntryError, Mind, Observation, World};

/// The garden's seed: the day the Ur-world was decided, 2026-11-13.
pub const SEED: u64 = 20_261_113;

/// Where the first enters: west of the tree.
pub const FIRST_AT: Cell = Cell::new(-3, 1, 0);

/// Where the second enters: east of the tree.
pub const SECOND_AT: Cell = Cell::new(3, 1, 0);

/// How many ticks the Hello World runs.
pub const TICKS: u64 = 28;

/// When the Hello World's arrivals and head say they were signed: the day
/// the Ur-world was decided. A fixed time, so the log is the same on every
/// run; a proof's `created` is no evidence of when anything happened.
pub const CREATED: &str = "2026-11-13T00:00:00Z";

/// The Hello World's world key: a trial key, made from the seed.
pub fn world_secret() -> [u8; 32] {
    trial_secret(SEED, "the garden's world")
}

/// A mind that plays a fixed list of actions, one a tick, then waits.
#[derive(Debug, Clone, Default)]
pub struct Script {
    actions: VecDeque<Action>,
}

impl Script {
    /// A script of these actions.
    pub fn new(actions: impl IntoIterator<Item = Action>) -> Script {
        Script {
            actions: actions.into_iter().collect(),
        }
    }
}

impl Mind for Script {
    fn act(&mut self, _seen: &Observation) -> Action {
        self.actions.pop_front().unwrap_or(Action::Wait)
    }
}

/// WALKER's script: speak first, listen, then walk north around the
/// tree and east, out of the garden.
pub fn walker() -> Script {
    let mut actions = vec![
        Action::Say("Hello, world.".into()),
        Action::Wait,
        Action::Step(Dir::North),
        Action::Step(Dir::North),
    ];
    actions.extend(std::iter::repeat_n(Action::Step(Dir::East), 22));
    Script::new(actions)
}

/// GARDENER's script: listen, answer, and plant a flower close by.
pub fn gardener() -> Script {
    Script::new([
        Action::Wait,
        Action::Say("Hello, WALKER.".into()),
        Action::Plant(Dir::East),
    ])
}

/// The plant worlds the garden hosts: a name, where its glasshouse
/// stands, and its dials.
pub fn plants() -> Vec<(&'static str, Cell, Dials)> {
    let dials = |branch_length, max_depth, water, light| Dials {
        branch_length,
        max_depth,
        water,
        light,
    };
    vec![
        (
            "the template's own plant",
            Cell::new(-5, 1, -4),
            Dials::default(),
        ),
        ("a larger plant", Cell::new(0, 1, -6), dials(3, 8, 10, 10)),
        (
            "a plant in low light",
            Cell::new(5, 1, -4),
            dials(3, 7, 10, 2),
        ),
    ]
}

/// A hosted plant's trial key, made from the garden's seed and its name.
pub fn plant_secret(name: &str) -> [u8; 32] {
    trial_secret(SEED, &format!("plant world: {name}"))
}

/// The template the plants grow from: the plant vectors' own
/// (`plant_world::vectors`), signed by the same trial key.
pub fn plant_template() -> Result<Value, String> {
    let keeper = plant_world::world::trial_secret(0, "template keeper");
    template(&keeper, TRIAL_CODE.0, TRIAL_CODE.1, TRIAL_TIME)
}

/// The Hello World: the garden, its three glasshouses, WALKER and
/// GARDENER, `TICKS` ticks. Each plant is hosted before anyone enters;
/// each stand-in enters with an arrival signed by its own trial key.
pub fn hello_world() -> Result<World, String> {
    let mut world = World::new(SEED, &public_key(&world_secret()));
    let template_hash = record_hash(&plant_template()?)?;
    for (name, at, dials) in plants() {
        let key = plant_world::world::did(&plant_secret(name));
        let plant = PlantWorld::new(&key, &template_hash, dials, None)?;
        world.host(at, Box::new(plant)).map_err(|e| e.to_string())?;
    }
    for (name, script, at) in [
        ("WALKER", walker(), FIRST_AT),
        ("GARDENER", gardener(), SECOND_AT),
    ] {
        let arrival = arrival::sign(&world, &trial_secret(SEED, name), name, CREATED)?;
        world
            .enter(&arrival, Box::new(script), at)
            .map_err(|e: EntryError| e.to_string())?;
    }
    world.run(TICKS);
    Ok(world)
}

/// The hosted plants as shared vectors (`vectors/ur-garden-hosted.json`):
/// each one's name, glasshouse, log, signed head and birth record, with
/// the template and law they name.
pub fn hosted_vectors(world: &World) -> Result<Value, String> {
    let template = plant_template()?;
    let mut worlds = Vec::new();
    for (name, at, _) in plants() {
        let secret = plant_secret(name);
        let key = plant_world::world::did(&secret);
        let plant = world
            .glasshouses()
            .iter()
            .find(|g| g.world.key() == key)
            .and_then(|g| g.world.as_any().downcast_ref::<PlantWorld>())
            .ok_or_else(|| format!("{name} isn't hosted"))?;
        worlds.push(json!({
            "name": name,
            "at": at.json(),
            "birth": plant.birth(&secret, name, TRIAL_TIME)?,
            "log": plant.log(),
            "head": plant.head(&secret, TRIAL_TIME)?,
        }));
    }
    Ok(json!({
        "about": "The plant worlds the Ur-world's garden hosts (rust/ur-world, garden.rs), written by `cargo run -p ur-world --example garden -- --vectors ../vectors`. Each is a world of its own with a trial key made from the garden's seed and its name, public to everyone and never for anything real; the template is the plant vectors' own, signed by a trial key.",
        "template": template,
        "templateHash": record_hash(&template)?,
        "law": law(),
        "lawHash": law_hash()?,
        "worlds": worlds,
    }))
}
