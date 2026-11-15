// rust/ur-world/src/architecture/mod.rs
//! The architectures (course step 3a, part four; docs/research/PERSONS.md,
//! decision 11): ways a mind can be spread over presences, each a small
//! run over trial worlds, on the unchanged core. The ideas come from
//! DeepSeek's sketches (record 012-04-00, components 41 to 46); their
//! code is not brought in.
//!
//! - [`octopus`]: one brain, arms in several worlds. The brain gives each
//!   arm an intent; each arm works out its own steps, has a reflex of its
//!   own, and reports back.
//! - [`relay`]: senses in some worlds, a leader in another. Each sense
//!   fires on what it sees; the leader acts only when enough fire at once.
//! - [`swarm`]: no brain. Several presences in one world follow one
//!   simple rule, and talk only through what they leave in the world.
//! - [`council`]: several persons, each counted once by their identity
//!   key on a council's proposal, and only those whose birth a world the
//!   council trusts signed (decision 8), from DeepSeek's components 44 to
//!   46.
//!
//! In the first three, one person's client runs every presence (decision
//! 7): what goes between worlds goes through it, and no world hears
//! another. In the council, each person's client signs their own vote.
//!
//! # Limits
//!
//! - **Scripted minds.** Every mind here is a short rule, not a model:
//!   the point is the shape of each architecture, not what its minds
//!   choose.
//! - **One thread.** The worlds take their ticks one after another, in a
//!   fixed order, so each run is the same every time; the architectures
//!   don't depend on that order beyond what each module says.

pub mod council;
pub mod octopus;
pub mod relay;
pub mod swarm;

use formats::proof::public_key;

use crate::arrival::trial_secret;
use crate::space::{Cell, Dir};
use crate::world::World;

/// The seed of the architectures' trial worlds and persons: the day they
/// were built, 2026-11-15.
pub const SEED: u64 = 20_261_115;

/// When their arrivals say they were signed: a fixed time, so each run is
/// the same every time.
pub const CREATED: &str = "2026-11-15T00:00:00Z";

/// The trial key of the trial world `label`.
pub fn world_secret(label: &str) -> [u8; 32] {
    trial_secret(SEED, &format!("an architecture's trial world: {label}"))
}

/// A fresh trial world: `label`'s trial key, and a seed of its own.
pub fn trial_world(label: &str, seed: u64) -> World {
    World::new(seed, &public_key(&world_secret(label)))
}

/// The way to step from `from` toward `to`, along the axis with further
/// to go (east or west first, on a tie), or `None` if `from` is above or
/// below `to`.
pub const fn toward(from: Cell, to: Cell) -> Option<Dir> {
    let (dx, dz) = (to.x - from.x, to.z - from.z);
    if dx == 0 && dz == 0 {
        None
    } else if dx.abs() >= dz.abs() {
        Some(if dx > 0 { Dir::East } else { Dir::West })
    } else {
        Some(if dz > 0 { Dir::South } else { Dir::North })
    }
}
