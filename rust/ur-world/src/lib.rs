// rust/ur-world/src/lib.rs
//! The Ur-world: the first world of the multiverse, and its hub.
//!
//! A 3D world of cells, with ground and sky, that begins in a garden with
//! two individuals, ALICE and BOB, and is made from its seed as it is explored.
//! ALICE and BOB are born at the course's step 9; until then the garden's
//! Hello World runs with two scripted stand-ins, WALKER and GARDENER.
//! The design, and the founder's decisions behind it, are in
//! `docs/URWORLD.md`.
//!
//! - [`space`]: cells, chunks, directions and materials.
//! - [`generate`]: what is there before anyone changes it, worked out from
//!   the seed and the coordinates, in whole numbers, so every machine and
//!   language agrees.
//! - [`world`]: the kernel: inhabitants, the rules of movement, speech and
//!   planting, exploration, and the public log.
//! - [`arrival`]: entering as one's key: signed arrivals, names bound to
//!   keys, a world's signed log heads, and the checks of both in a log.
//! - [`host`]: the garden gives other worlds a place and time: each hosted
//!   world, with its own key and log, takes a step each tick, and both logs
//!   record it.
//! - [`garden`]: Hello World for building worlds, hosting three plant
//!   worlds in its glasshouses.
//! - [`door`]: the doorway for minds: the orientation, what an inhabitant
//!   sees written out, replies read strictly, and minds that run as their
//!   own programs, in any language.
//! - [`story`]: the log told as a story, and a map of what has been seen.
//!
//! # Limits
//!
//! - Minds are scripts in the same process, or programs speaking the
//!   doorway's protocol ([`door`]). The world-crossing protocol (WCP) isn't
//!   in Rust yet. Arrivals are signed, but by the doorway, with keys made
//!   for the run: no holder's key is read yet (docs/research/KEYS.md,
//!   "As built, part four").
//! - Everyone hears everyone, wherever they are.
//! - The only change an inhabitant can make is to plant a flower; the
//!   operator can shape any cell (`World::shape`).
//! - There is no viewer yet beyond the text map in the `garden` example.
//! - A glasshouse is a place the log names, not a cell: inhabitants don't
//!   see it, or the world inside it, yet. What a hosted world shows is
//!   read from its own log, as Plant Watch reads a plant's.
//! - A hosted world takes one step each tick, at one pace for all; hosting
//!   has no end but a world's finishing, and no world leaves.

#![forbid(unsafe_code)]

pub mod arrival;
pub mod door;
pub mod garden;
pub mod generate;
pub mod host;
pub mod space;
pub mod story;
pub mod world;

pub use space::{Cell, ChunkCoord, Dir, Material};
pub use world::{Action, Admission, EntryError, Mind, Observation, Outcome, World};
