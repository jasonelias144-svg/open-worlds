//! The RNN-driven resident. Wraps `TinyRnn` as a `Mind`.

use std::collections::HashSet;

use crate::garden::{
    Cell, Direction, GardenAction, PlantKind,
};
use crate::garden::rnn::{
    SamplingMode, TinyRnn, XorShift64,
};
use crate::world::Mind;

// ────────────────────────────────────────────────────────────
// Observation
// ────────────────────────────────────────────────────────────

/// What a resident sees at its turn. Richer than the previous
/// `Observation` — includes plant positions and nearby agents
/// so the Mind can pick a direction.
#[derive(Debug, Clone)]
pub struct Observation {
    pub position: Cell,
    pub last_action: u8,
    pub last_reward_micros: u64,
    pub plants: Vec<(String, Cell)>,
    pub nearby_agents: Vec<String>,
    pub garden_size: [i64; 3],
}

#[derive(Debug, Clone)]
pub struct Outcome {
    pub accepted: bool,
    pub reward_micros: u64,
}

// ────────────────────────────────────────────────────────────
// The Mind
// ────────────────────────────────────────────────────────────

pub struct TinyRnnMind {
    rnn: TinyRnn,
    rng: XorShift64,
    mode: SamplingMode,
    visited: HashSet<(i64, i64, i64)>,
    last_action: u8,
    last_reward_micros: u64,
    step: u64,
}

const PHRASES: &[&str] = &[
    "the fern is growing",
    "the tree unfolds",
    "the vine is quiet today",
    "come look at this",
    "the garden is alive",
    "I wonder what it becomes",
    "each cycle changes everything",
];

impl TinyRnnMind {
    pub fn new(
        rnn: TinyRnn,
        seed: u64,
        mode: SamplingMode,
    ) -> Self {
        Self {
            rnn,
            rng: XorShift64::new(seed),
            mode,
            visited: HashSet::new(),
            last_action: 0,
            last_reward_micros: 0,
            step: 0,
        }
    }

    /// The 7-dimensional input to the RNN:
    /// [one_hot(last_action, 3); last_reward; x_norm; y_norm].
    fn build_state(&self, obs: &Observation) -> Vec<f64> {
        let mut s = vec![0.0; 7];
        if (self.last_action as usize) < 3 {
            s[self.last_action as usize] = 1.0;
        }
        s[3] = self.last_reward_micros as f64 / 1e6;
        s[4] = obs.position.x as f64
            / (obs.garden_size[0].max(2) - 1) as f64;
        s[5] = obs.position.y as f64
            / (obs.garden_size[1].max(2) - 1) as f64;
        s[6] = 0.0;
        s
    }

    /// Direction heuristic — matches Python's
    /// `garden_adapter._choose_direction` closely enough for
    /// behavioral parity. Prefers unvisited cells toward the
    /// nearest plant; falls back to any unvisited; then any
    /// in-bounds.
    fn choose_direction(
        &self,
        pos: Cell,
        plants: &[(String, Cell)],
        size: [i64; 3],
    ) -> Direction {
        let target = plants.iter()
            .min_by_key(|(_, p)| p.distance(&pos))
            .map(|(_, p)| *p);

        let step = |d: Direction| -> Option<Cell> {
            let (dx, dy, dz) = d.delta();
            let c = Cell {
                x: pos.x + dx,
                y: pos.y + dy,
                z: pos.z + dz,
            };
            if c.x < 0 || c.x >= size[0]
                || c.y < 0 || c.y >= size[1]
                || c.z < 0 || c.z >= size[2]
            {
                return None;
            }
            if plants.iter().any(|(_, p)| *p == c) {
                return None;
            }
            Some(c)
        };

        if let Some(t) = target {
            if t.distance(&pos) > 1 {
                let dx = t.x - pos.x;
                let dy = t.y - pos.y;
                let primary = if dx != 0 {
                    if dx > 0 { Direction::East } else { Direction::West }
                } else {
                    if dy > 0 { Direction::South } else { Direction::North }
                };
                let secondary = if dy != 0 {
                    if dy > 0 { Direction::South } else { Direction::North }
                } else {
                    if dx > 0 { Direction::East } else { Direction::West }
                };
                for d in [primary, secondary] {
                    if let Some(c) = step(d) {
                        if !self.visited.contains(&(c.x, c.y, c.z)) {
                            return d;
                        }
                    }
                }
            }
        }

        for d in [Direction::North, Direction::East,
                   Direction::South, Direction::West] {
            if let Some(c) = step(d) {
                if !self.visited.contains(&(c.x, c.y, c.z)) {
                    return d;
                }
            }
        }
        for d in [Direction::North, Direction::East,
                   Direction::South, Direction::West] {
            if step(d).is_some() {
                return d;
            }
        }
        Direction::North
    }
}

impl Mind for TinyRnnMind {
    type Observation = Observation;
    type Action = GardenAction;
    type Outcome = Outcome;

    fn observe(&mut self, obs: Self::Observation) -> Self::Action {
        self.visited.insert((obs.position.x, obs.position.y, obs.position.z));
        let state = self.build_state(&obs);
        let (action_idx, _probs) = self.rnn.act(
            &state, self.mode, &mut self.rng);
        self.last_action = action_idx as u8;
        self.step += 1;

        match action_idx {
            0 => {
                let dir = self.choose_direction(
                    obs.position, &obs.plants, obs.garden_size);
                GardenAction::Walk { direction: dir }
            }
            1 => GardenAction::Observe,
            _ => {
                let idx = (self.step as usize) % PHRASES.len();
                GardenAction::Speak {
                    text: PHRASES[idx].to_string(),
                }
            }
        }
    }

    fn receive(&mut self, outcome: Self::Outcome) {
        let reward = outcome.reward_micros as f64 / 1e6;
        self.rnn.learn(self.last_action as usize, reward);
        self.last_reward_micros = outcome.reward_micros;
    }
}

// Direction delta lives on Direction, but we needed it here.
impl Direction {
    pub fn delta(self) -> (i64, i64, i64) {
        match self {
            Direction::North => (0, -1, 0),
            Direction::South => (0, 1, 0),
            Direction::East => (1, 0, 0),
            Direction::West => (-1, 0, 0),
        }
    }
}

// Cell distance helper.
impl Cell {
    pub fn distance(&self, other: &Cell) -> i64 {
        (self.x - other.x).abs()
            + (self.y - other.y).abs()
            + (self.z - other.z).abs()
    }
}
