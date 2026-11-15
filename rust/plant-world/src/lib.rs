//! A fractal plant world: the fractal track's first part
//! (`docs/FRACTALS.md`, "The plan").
//!
//! A primary world, with a key and a log of its own, made from a template
//! whose dials are the rule's numbers. It grows by its rule and dials
//! alone, in whole numbers, so the same template and dials give the same
//! log on any machine. The rule is DeepSeek's plant, from record 012-06-02
//! ([`rule`]); the world around it is ours ([`world`]).
//!
//! `examples/plant.rs` grows a plant and prints it, and writes the shared
//! vectors (`vectors/plant-world.json`), which Python checks against
//! DeepSeek's own `advance`, step by step.
//!
//! # Limits
//!
//! - One rule, DeepSeek's: plants that look more like plants (rewriting
//!   rules, L-systems) come later (`docs/FRACTALS.md`, part 1).
//! - A plant world takes no change from outside. How a world may change,
//!   by branching or otherwise, is left open, and comes one world at a
//!   time.
//! - The template it is made from is signed by a trial key in the vectors.
//!   A template signed by the project's own key, naming the merged commit
//!   that runs it, is for when plant worlds are hosted in the Ur-world's
//!   garden (part 3).
//! - A pot is set by the world, not by the template.
//! - Nothing draws it but the example's text: the web page is part 2.

pub mod rule;
pub mod vectors;
pub mod world;
