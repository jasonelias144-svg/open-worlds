// rust/ur-world/src/architecture/octopus.rs
//! The octopus (DeepSeek's component 41): one brain, and an arm in each
//! of several worlds.
//!
//! - **The brain** is the person's client. It gives each arm an intent
//!   ([`Intent`]), and changes it only at the end of a tick, from what the
//!   arms reported: it never chooses an arm's steps.
//! - **Each arm** is a presence of the person's in a world of its own. It
//!   works out its own steps toward its intent, and has a reflex: when a
//!   step is blocked, it steps aside on its next tick, without asking the
//!   brain.
//! - **Every arm reports** what it stands on and what came of its last
//!   action, each tick ([`Report`]): the efference copy. Arms never hear
//!   each other; only the brain hears them all.
//!
//! The run ([`run`]): three arms start west of the tree, in three
//! worlds, the third further west, and the brain sends each to the cell
//! east of the tree. Each arm's way runs into the trunk, and its reflex
//! takes it round. When every arm has reported arriving, the brain tells
//! all three to plant a flower to the east; when every arm has reported
//! planting, it tells them to rest.

use std::cell::RefCell;
use std::rc::Rc;

use crate::architecture::{CREATED, SEED, toward, trial_world};
use crate::garden::{FIRST_AT, SECOND_AT};
use crate::person::Person;
use crate::space::{Cell, Dir};
use crate::world::{Action, Mind, Observation, Outcome, World};

/// The worlds of the run, the name of the arm in each (a name of its
/// own, since one name everywhere would link them: PERSONS.md, decision
/// 3), and where it enters. The third starts two cells further west, so
/// it arrives two ticks after the others, and the brain waits for it.
pub const ARMS: [(&str, &str, Cell); 3] = [
    ("the octopus's first world", "KELP", FIRST_AT),
    ("the octopus's second world", "CORAL", FIRST_AT),
    ("the octopus's third world", "TIDE", Cell::new(-5, 1, 0)),
];

/// How many ticks the run takes.
pub const TICKS: u64 = 15;

/// What the brain wants of an arm.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Intent {
    /// Go to the cell: the arm finds its own way.
    Go(Cell),
    /// Plant a flower that way, once.
    Plant(Dir),
    /// Wait.
    Rest,
}

/// What an arm tells the brain at the start of each of its ticks.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Report {
    /// Which arm, by its place in [`ARMS`].
    pub arm: usize,
    /// The tick.
    pub tick: u64,
    /// Where it stands.
    pub at: Cell,
    /// What came of its last action.
    pub last: Option<Outcome>,
    /// Whether it steps aside this tick, by its own reflex.
    pub reflex: bool,
}

#[derive(Debug, Default)]
struct State {
    intents: Vec<Intent>,
    reports: Vec<Report>,
    issued: Vec<(u64, usize, Intent)>,
}

/// The brain: the person's client, which every arm reports to.
#[derive(Debug, Clone, Default)]
pub struct Brain(Rc<RefCell<State>>);

impl Brain {
    /// Every report, in the order the arms made them.
    pub fn reports(&self) -> Vec<Report> {
        self.0.borrow().reports.clone()
    }

    /// Every intent the brain gave: the tick after which it gave it, the
    /// arm, and the intent.
    pub fn issued(&self) -> Vec<(u64, usize, Intent)> {
        self.0.borrow().issued.clone()
    }

    fn give(&self, tick: u64, arm: usize, intent: Intent) {
        let mut state = self.0.borrow_mut();
        if let Some(slot) = state.intents.get_mut(arm) {
            *slot = intent;
        } else {
            state.intents.push(intent);
        }
        state.issued.push((tick, arm, intent));
    }

    fn intent(&self, arm: usize) -> Intent {
        self.0
            .borrow()
            .intents
            .get(arm)
            .copied()
            .unwrap_or(Intent::Rest)
    }

    fn report(&self, report: Report) {
        self.0.borrow_mut().reports.push(report);
    }

    /// The end of a tick: from the latest report of each arm, the next
    /// intent for all of them, if every arm has done what it was given.
    fn decide(&self, tick: u64, arms: usize) {
        let latest: Vec<Option<Report>> = (0..arms)
            .map(|arm| {
                self.0
                    .borrow()
                    .reports
                    .iter()
                    .rev()
                    .find(|r| r.arm == arm)
                    .cloned()
            })
            .collect();
        let done = |arm: usize, r: &Option<Report>| match (self.intent(arm), r) {
            (Intent::Go(to), Some(r)) => r.at == to,
            (Intent::Plant(_), Some(r)) => matches!(
                r.last,
                Some(Outcome::Planted { .. } | Outcome::PlantBlocked(_))
            ),
            _ => false,
        };
        if !latest.iter().enumerate().all(|(arm, r)| done(arm, r)) {
            return;
        }
        for arm in 0..arms {
            let next = match self.intent(arm) {
                Intent::Go(_) => Intent::Plant(Dir::East),
                Intent::Plant(_) | Intent::Rest => Intent::Rest,
            };
            self.give(tick, arm, next);
        }
    }
}

/// An arm's mind: its own steps toward the brain's intent, its reflex,
/// and its report.
#[derive(Debug, Clone)]
pub struct Arm {
    arm: usize,
    brain: Brain,
}

impl Arm {
    /// The arm at `arm`'s place in [`ARMS`], reporting to `brain`.
    pub const fn new(arm: usize, brain: Brain) -> Arm {
        Arm { arm, brain }
    }
}

impl Mind for Arm {
    fn act(&mut self, seen: &Observation) -> Action {
        let intent = self.brain.intent(self.arm);
        let blocked = match seen.last {
            Some(Outcome::StepBlocked(dir)) => Some(dir),
            _ => None,
        };
        let reflex = blocked.is_some() && matches!(intent, Intent::Go(_));
        self.brain.report(Report {
            arm: self.arm,
            tick: seen.tick,
            at: seen.position,
            last: seen.last.clone(),
            reflex,
        });
        match (intent, blocked) {
            // The reflex: blocked, it steps aside, at right angles.
            (Intent::Go(_), Some(Dir::East | Dir::West)) => Action::Step(Dir::South),
            (Intent::Go(_), Some(Dir::North | Dir::South)) => Action::Step(Dir::East),
            (Intent::Go(to), None) => toward(seen.position, to).map_or(Action::Wait, Action::Step),
            (Intent::Plant(dir), _) => match seen.last {
                Some(Outcome::Planted { .. } | Outcome::PlantBlocked(_)) => Action::Wait,
                _ => Action::Plant(dir),
            },
            (Intent::Rest, _) => Action::Wait,
        }
    }
}

/// The octopus, as [`run`] leaves it.
pub struct Octopus {
    /// The person whose arms they are.
    pub person: Person,
    /// The worlds of [`ARMS`], in that order.
    pub worlds: Vec<World>,
    /// The brain, with every report and every intent it gave.
    pub brain: Brain,
}

/// The octopus's run ([`crate::architecture::octopus`]): the arms enter
/// west of the tree, each in its own world, where [`ARMS`] says, and the
/// brain sends each to [`SECOND_AT`], east of the tree; then the worlds take [`TICKS`] ticks in step, the
/// brain deciding at the end of each.
pub fn run() -> Result<Octopus, String> {
    let person = Person::trial(SEED, "the octopus");
    let brain = Brain::default();
    let mut worlds = Vec::new();
    for (i, (label, name, start)) in ARMS.iter().enumerate() {
        let index = u64::try_from(i).map_err(|e| e.to_string())?;
        let mut world = trial_world(label, SEED + index);
        brain.give(0, i, Intent::Go(SECOND_AT));
        let arrival = person.arrival(&world, 0, name, CREATED)?;
        world
            .enter(&arrival, Box::new(Arm::new(i, brain.clone())), *start)
            .map_err(|e| format!("{name} can't enter {label}: {e}"))?;
        worlds.push(world);
    }
    for tick in 0..TICKS {
        for world in &mut worlds {
            world.step();
        }
        brain.decide(tick, ARMS.len());
    }
    Ok(Octopus {
        person,
        worlds,
        brain,
    })
}
