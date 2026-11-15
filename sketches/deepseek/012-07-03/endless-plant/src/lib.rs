//! Endless plant — proposal sketch.
//!
//! A plant world that grows without a fixed depth, constrained by
//! energy rather than a depth cap. Optionally driven by a single
//! choice neuron.
//!
//! This is a sketch for review; it is not a course step. The
//! technical lead compiles and fits it.

pub mod rule;
pub mod monad;
pub mod world;
pub mod vectors;

pub use rule::{Template, Segment, Tip, Direction, DIRECTIONS};
pub use world::{World, Entry, EntryKind};
pub use monad::{Neuron, Action};
