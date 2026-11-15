// rust/ur-world/src/architecture/relay.rs
//! The relay (DeepSeek's component 42): senses in some worlds, and a
//! leader in another, joined through the person.
//!
//! - **Each sense** is a presence that only watches: on each tick it fires
//!   if anyone stands within [`REACH`] cells of it, and the person's client
//!   writes the firing on its board ([`Board`]). It never acts.
//! - **The leader** is a presence in a world of its own, which no sense
//!   can see. On each tick it reads how many senses fired that tick, and
//!   acts only when [`THRESHOLD`] of them did: one alone isn't enough.
//!
//! Where the octopus's brain pushes intents to its arms, the leader here
//! pulls what the senses fired. The leader's world takes its tick after
//! the senses' worlds, so it reads what they fired on the same tick.
//!
//! The run ([`run`]): in each sense's world a stranger walks toward the
//! sense, the second setting out five ticks after the first. The first
//! sense fires from tick 4, the second from tick 9; on tick 9, with both
//! firing, the leader plants a flower, once.

use std::cell::RefCell;
use std::rc::Rc;

use crate::architecture::{CREATED, SEED, trial_world};
use crate::arrival::{self, trial_secret};
use crate::garden::{FIRST_AT, Script};
use crate::person::Person;
use crate::space::{Cell, Dir};
use crate::world::{Action, Mind, Observation, World};

/// The senses' worlds, with each sense's name, then the leader's.
pub const PRESENCES: [(&str, &str); 3] = [
    ("the relay's first world", "HERON"),
    ("the relay's second world", "OWL"),
    ("the relay's third world", "FOX"),
];

/// How near, in cells east-west and north-south, someone must stand for
/// a sense to fire.
pub const REACH: i64 = 2;

/// How many senses must fire on one tick for the leader to act.
pub const THRESHOLD: usize = 2;

/// How many ticks the run takes.
pub const TICKS: u64 = 12;

/// Where each stranger enters: east of the tree, a row south of the
/// trunk, so that walking west goes past it.
pub const STRANGER_AT: Cell = Cell::new(3, 1, 1);

/// The person's board of what fired: each sense, by its place in
/// [`PRESENCES`], and the tick it fired on.
#[derive(Debug, Clone, Default)]
pub struct Board(Rc<RefCell<Vec<(u64, usize)>>>);

impl Board {
    /// Every firing, in order.
    pub fn fired(&self) -> Vec<(u64, usize)> {
        self.0.borrow().clone()
    }

    /// How many senses fired on `tick`.
    pub fn count(&self, tick: u64) -> usize {
        self.0.borrow().iter().filter(|(t, _)| *t == tick).count()
    }

    fn fire(&self, tick: u64, sense: usize) {
        self.0.borrow_mut().push((tick, sense));
    }
}

/// A sense's mind: it fires when anyone stands within [`REACH`], and
/// otherwise only waits.
#[derive(Debug, Clone)]
pub struct Senses {
    sense: usize,
    board: Board,
}

impl Senses {
    /// The sense at `sense`'s place in [`PRESENCES`], writing on `board`.
    pub const fn new(sense: usize, board: Board) -> Senses {
        Senses { sense, board }
    }
}

impl Mind for Senses {
    fn act(&mut self, seen: &Observation) -> Action {
        let near = seen.others.iter().any(|(_, at)| {
            (at.x - seen.position.x).abs() <= REACH && (at.z - seen.position.z).abs() <= REACH
        });
        if near {
            self.board.fire(seen.tick, self.sense);
        }
        Action::Wait
    }
}

/// The leader's mind: it plants a flower to the east, once, on the first
/// tick that [`THRESHOLD`] senses fire.
#[derive(Debug, Clone)]
pub struct Leads {
    board: Board,
    acted: Option<u64>,
}

impl Leads {
    /// A leader that reads `board`.
    pub const fn new(board: Board) -> Leads {
        Leads { board, acted: None }
    }
}

impl Mind for Leads {
    fn act(&mut self, seen: &Observation) -> Action {
        if self.acted.is_none() && self.board.count(seen.tick) >= THRESHOLD {
            self.acted = Some(seen.tick);
            return Action::Plant(Dir::East);
        }
        Action::Wait
    }
}

/// The relay, as [`run`] leaves it.
pub struct Relay {
    /// The person whose senses and leader they are.
    pub person: Person,
    /// The worlds of [`PRESENCES`], in that order.
    pub worlds: Vec<World>,
    /// What the senses fired.
    pub board: Board,
}

/// The relay's run ([`crate::architecture::relay`]): a sense in each of
/// two worlds and the leader in a third, all west of the tree; a stranger
/// in each sense's world, walking west from [`STRANGER_AT`], the second
/// five ticks after the first; then [`TICKS`] ticks, the worlds in
/// [`PRESENCES`]'s order.
pub fn run() -> Result<Relay, String> {
    let person = Person::trial(SEED, "the relay");
    let board = Board::default();
    let mut worlds = Vec::new();
    for (i, (label, name)) in PRESENCES.iter().enumerate() {
        let index = u64::try_from(i).map_err(|e| e.to_string())?;
        let mut world = trial_world(label, SEED + index);
        let mind: Box<dyn Mind> = if i < 2 {
            Box::new(Senses::new(i, board.clone()))
        } else {
            Box::new(Leads::new(board.clone()))
        };
        let arrival = person.arrival(&world, 0, name, CREATED)?;
        world
            .enter(&arrival, mind, FIRST_AT)
            .map_err(|e| format!("{name} can't enter {label}: {e}"))?;
        if i < 2 {
            let delay = if i == 0 { 0 } else { 5 };
            let walk = std::iter::repeat_n(Action::Wait, delay)
                .chain(std::iter::repeat_n(Action::Step(Dir::West), 5));
            let secret = trial_secret(SEED, &format!("a stranger in {label}"));
            let arrival = arrival::sign(&world, &secret, "STRANGER", CREATED)?;
            world
                .enter(&arrival, Box::new(Script::new(walk)), STRANGER_AT)
                .map_err(|e| format!("the stranger can't enter {label}: {e}"))?;
        }
        worlds.push(world);
    }
    for _ in 0..TICKS {
        for world in &mut worlds {
            world.step();
        }
    }
    Ok(Relay {
        person,
        worlds,
        board,
    })
}
