// rust/ur-world/src/architecture/swarm.rs
//! The swarm (DeepSeek's component 43): no brain, and several presences
//! of one person in one world, all following the same rule.
//!
//! - **No unit leads,** and none is told anything by the person's client:
//!   each is a key and a name of its own in the world (PERSONS.md,
//!   decision 9), with the same mind ([`Unit`]).
//! - **They talk only through the world** (stigmergy): what one leaves,
//!   a flower, is what another finds.
//! - **The rule.** A unit standing on a flower plants another on a free
//!   side of it, where the ground will take one. A unit with a flower
//!   beside it, that no one stands on, steps onto it (a flower isn't
//!   solid). Any other unit wanders: a step a tick, the way given by its
//!   own number and the tick, and back toward the tree when it nears the
//!   garden's edge.
//!
//! No unit decides that the garden has a patch of flowers: the patch is
//! what their one rule, followed apart, adds up to. Every flower they
//! plant is beside the one its planter stands on, so the flowers stay one
//! patch, each joined to another on a side.
//!
//! The run ([`run`]): the operator plants one flower north of the tree,
//! as a gardener would ([`World::shape`]); five units enter around the
//! garden, and the world takes [`TICKS`] ticks.

use crate::architecture::{CREATED, SEED, trial_world};
use crate::person::Person;
use crate::space::{Cell, Dir, Material};
use crate::world::{Action, Mind, Observation, World};

/// The units' names, and where each enters.
pub const UNITS: [(&str, Cell); 5] = [
    ("BEE-1", Cell::new(-3, 1, 0)),
    ("BEE-2", Cell::new(3, 1, 0)),
    ("BEE-3", Cell::new(0, 1, -3)),
    ("BEE-4", Cell::new(-3, 1, 3)),
    ("BEE-5", Cell::new(4, 1, -4)),
];

/// Where the operator plants the first flower.
pub const FIRST_FLOWER: Cell = Cell::new(1, 1, -4);

/// How far from the tree, east-west or north-south, a unit wanders
/// before it turns back.
pub const RANGE: i64 = 6;

/// How many ticks the run takes.
pub const TICKS: u64 = 60;

/// The trial world of the run.
pub const WORLD: &str = "the swarm's world";

/// A unit's mind: the one rule every unit follows.
#[derive(Debug, Clone)]
pub struct Unit {
    number: u64,
}

impl Unit {
    /// The unit with this number, which sets its wandering.
    pub const fn new(number: u64) -> Unit {
        Unit { number }
    }

    /// The way it wanders on `tick`, from where it stands.
    fn wander(&self, tick: u64, at: Cell) -> Dir {
        if at.x > RANGE {
            return Dir::West;
        }
        if at.x < -RANGE {
            return Dir::East;
        }
        if at.z > RANGE {
            return Dir::North;
        }
        if at.z < -RANGE {
            return Dir::South;
        }
        // A fixed scramble of the unit's number and the tick (SplitMix64's
        // last steps), so each run is the same.
        let mut h = self
            .number
            .wrapping_mul(0x9e37_79b9_7f4a_7c15)
            .wrapping_add(tick.wrapping_mul(0xbf58_476d_1ce4_e5b9));
        h = (h ^ (h >> 30)).wrapping_mul(0x94d0_49bb_1331_11eb);
        h ^= h >> 31;
        let way = usize::try_from(h % 4).unwrap_or(0);
        Dir::ALL.get(way).copied().unwrap_or(Dir::North)
    }
}

/// The cell beside, `dir` from where it stands, at `dy` up or down.
fn beside(seen: &Observation, dir: Dir, dy: i64) -> Option<Material> {
    let (dx, dz) = dir.step();
    seen.at(dx, dy, dz)
}

impl Mind for Unit {
    fn act(&mut self, seen: &Observation) -> Action {
        let someone_at = |dir: Dir| {
            let (dx, dz) = dir.step();
            let cell = seen.position.offset(dx, 0, dz);
            seen.others.iter().any(|(_, at)| *at == cell)
        };
        if seen.at(0, 0, 0) == Some(Material::Flower) {
            let free = Dir::ALL.iter().copied().find(|d| {
                beside(seen, *d, 0) == Some(Material::Air)
                    && matches!(beside(seen, *d, -1), Some(Material::Grass | Material::Soil))
                    && !someone_at(*d)
            });
            if let Some(dir) = free {
                return Action::Plant(dir);
            }
        } else if let Some(dir) = Dir::ALL
            .iter()
            .copied()
            .find(|d| beside(seen, *d, 0) == Some(Material::Flower) && !someone_at(*d))
        {
            return Action::Step(dir);
        }
        Action::Step(self.wander(seen.tick, seen.position))
    }
}

/// The swarm, as [`run`] leaves it.
pub struct Swarm {
    /// The person whose units they are.
    pub person: Person,
    /// The world they are in.
    pub world: World,
}

/// The swarm's run ([`crate::architecture::swarm`]): the operator plants
/// [`FIRST_FLOWER`]; the person's presences 0 to 4 enter as [`UNITS`];
/// then [`TICKS`] ticks.
pub fn run() -> Result<Swarm, String> {
    let person = Person::trial(SEED, "the swarm");
    let mut world = trial_world(WORLD, SEED);
    if !world.shape(FIRST_FLOWER, Material::Flower) {
        return Err("the first flower can't be planted".into());
    }
    for (counter, (name, at)) in (0_u32..).zip(UNITS) {
        let arrival = person.arrival(&world, counter, name, CREATED)?;
        world
            .enter(&arrival, Box::new(Unit::new(u64::from(counter))), at)
            .map_err(|e| format!("{name} can't enter: {e}"))?;
    }
    world.run(TICKS);
    Ok(Swarm { person, world })
}
