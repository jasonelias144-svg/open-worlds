//! Residents as `Mind` implementations.
//!
//! ALICE and BOB are `Mind`s. The trait signature follows
//! `ur-world`'s `Mind: Observation → Action → Outcome`.
//!
//! Two implementations ship here:
//!   - `ScriptedMind`: deterministic, picks moves by a seeded
//!     pseudo-random policy. Proves the loop.
//!   - `TinyRnnMind`: placeholder for the tiny-RNN policy from
//!     Python. Deferred until the RNN weights are ported; the
//!     ScriptedMind is the reference until then.

use crate::garden::{Cell, Direction, GardenAction, Garden};
use crate::world::Mind;

/// What a resident sees at its turn.
#[derive(Debug, Clone)]
pub struct Observation {
    pub position: Cell,
    pub last_action: u8,
    pub last_reward_micros: u64,
    pub garden_width: i64,
    pub garden_height: i64,
    pub garden_depth: i64,
}

/// The outcome of a resident's previous action.
#[derive(Debug, Clone)]
pub struct Outcome {
    pub accepted: bool,
    pub reward_micros: u64,
}

/// Deterministic resident. Proof of the `Mind` loop; not the
/// eventual model-based resident.
pub struct ScriptedMind {
    seed: u64,
    step: u64,
    last_action: u8,
    last_reward_micros: u64,
    position: Cell,
}

impl ScriptedMind {
    pub fn new(seed: u64, start: Cell) -> Self {
        Self { seed, step: 0, last_action: 0, last_reward_micros: 0, position: start }
    }

    fn next(&mut self) -> u64 {
        self.step += 1;
        let mut x = self.seed.wrapping_add(self.step);
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        x.wrapping_mul(0x2545F4914F6CDD1D)
    }

    fn pick_direction(&mut self) -> Direction {
        match self.next() % 4 {
            0 => Direction::North,
            1 => Direction::South,
            2 => Direction::East,
            _ => Direction::West,
        }
    }
}

impl Mind for ScriptedMind {
    type Observation = Observation;
    type Action = GardenAction;
    type Outcome = Outcome;

    fn observe(&mut self, obs: Self::Observation) -> Self::Action {
        self.position = obs.position;
        self.last_action = obs.last_action;
        self.last_reward_micros = obs.last_reward_micros;

        // 0 = wander, 1 = attend, 2 = speak
        match self.next() % 3 {
            0 => GardenAction::Walk {
                direction: self.pick_direction(),
            },
            1 => GardenAction::Observe,
            _ => GardenAction::Speak {
                text: format!("I see the garden at step {}", self.step),
            },
        }
    }

    fn receive(&mut self, outcome: Self::Outcome) {
        // Learning: nothing in the scripted mind. The reward is
        // recorded for logging; the policy doesn't change.
        self.last_reward_micros = outcome.reward_micros;
    }
}
