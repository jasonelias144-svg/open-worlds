// rust/ur-world/src/lib.rs
//! The Ur-world: the first world of the multiverse, and its hub.
//!
//! A 3D world of cells, with ground and sky, that begins in a garden with
//! two individuals, ALICE and BOB, and comes into being as it is explored.
//! The design, and the founder's decisions behind it, are in
//! `docs/URWORLD.md`.
//!
//! - [`space`]: cells, chunks, directions and materials.
//! - [`generate`]: what is there before anyone changes it, worked out from
//!   the seed and the coordinates, in whole numbers, so every machine and
//!   language agrees.
//! - [`world`]: the kernel: inhabitants, the rules of movement, speech and
//!   planting, exploration, and the public log.
//! - [`garden`]: Hello World for building worlds.
//! - [`door`]: the doorway for minds: the orientation, what an inhabitant
//!   sees written out, replies read strictly, and minds that run as their
//!   own programs, in any language.
//! - [`story`]: the log told as a story, and a map of what has been seen.
//!
//! # Limits
//!
//! - Minds are scripts in the same process, or programs speaking the
//!   doorway's protocol ([`door`]). The world-crossing protocol (WCP) isn't
//!   in Rust yet; neither are keys, so ALICE and BOB are named here but
//!   don't yet sign.
//! - Everyone hears everyone, wherever they are.
//! - The only change an inhabitant can make is to plant a flower; the
//!   operator can shape any cell (`World::shape`).
//! - There is no viewer yet beyond the text map in the `garden` example.

#![forbid(unsafe_code)]

pub mod door;
pub mod garden;
pub mod generate;
pub mod space;
pub mod story;
pub mod world;

pub use space::{Cell, ChunkCoord, Dir, Material};
pub use world::{Action, EntryError, Mind, Observation, Outcome, World};
