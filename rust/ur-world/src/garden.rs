// rust/ur-world/src/garden.rs
//! Hello World for building worlds: a garden, and two individuals.
//!
//! The founder: "It's like Hello World for building worlds: you start it
//! with a garden of two individuals." ALICE and BOB are the first two
//! inhabitants of the Ur-world, and of the whole multiverse. Here they are
//! driven by short scripts, enough to show that the world works: they greet
//! each other (one speaks, the other listens, then they turn), BOB plants a
//! flower, and ALICE walks out of the garden into land no one has seen,
//! which comes into being as ALICE goes. They gain minds of their own at the
//! course's language-model step (docs/URWORLD.md).

use std::collections::VecDeque;

use crate::space::{Cell, Dir};
use crate::world::{Action, EntryError, Mind, Observation, World};

/// The garden's seed: the day the Ur-world was decided, 2026-11-13.
pub const SEED: u64 = 20_261_113;

/// Where ALICE enters: west of the tree.
pub const ALICE_AT: Cell = Cell::new(-3, 1, 0);

/// Where BOB enters: east of the tree.
pub const BOB_AT: Cell = Cell::new(3, 1, 0);

/// How many ticks the Hello World runs.
pub const TICKS: u64 = 28;

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

/// ALICE's script: speak first, listen, then walk north around the
/// tree and east, out of the garden.
pub fn alice() -> Script {
    let mut actions = vec![
        Action::Say("Hello, world.".into()),
        Action::Wait,
        Action::Step(Dir::North),
        Action::Step(Dir::North),
    ];
    actions.extend(std::iter::repeat_n(Action::Step(Dir::East), 22));
    Script::new(actions)
}

/// BOB's script: listen, answer, and plant a flower close by.
pub fn bob() -> Script {
    Script::new([
        Action::Wait,
        Action::Say("Hello, ALICE.".into()),
        Action::Plant(Dir::East),
    ])
}

/// The Hello World: the garden, ALICE and BOB, `TICKS` ticks.
pub fn hello_world() -> Result<World, EntryError> {
    let mut world = World::new(SEED);
    world.add("ALICE", Box::new(alice()), ALICE_AT)?;
    world.add("BOB", Box::new(bob()), BOB_AT)?;
    world.run(TICKS);
    Ok(world)
}
