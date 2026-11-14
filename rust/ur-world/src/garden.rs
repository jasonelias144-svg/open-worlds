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
//! The Hello World is a trial world of its own, not the Ur-world: its key,
//! and its stand-ins' keys, are trial keys made from the seed
//! ([`crate::arrival::trial_secret`]), so its log is the same on every
//! run, and anyone can make the same keys.

use std::collections::VecDeque;

use formats::proof::public_key;

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

/// The Hello World: the garden, WALKER and GARDENER, `TICKS` ticks. Each
/// enters with an arrival signed by its own trial key.
pub fn hello_world() -> Result<World, EntryError> {
    let mut world = World::new(SEED, &public_key(&world_secret()));
    for (name, script, at) in [
        ("WALKER", walker(), FIRST_AT),
        ("GARDENER", gardener(), SECOND_AT),
    ] {
        let arrival = arrival::sign(&world, &trial_secret(SEED, name), name, CREATED)
            .map_err(EntryError::BadArrival)?;
        world.enter(&arrival, Box::new(script), at)?;
    }
    world.run(TICKS);
    Ok(world)
}
