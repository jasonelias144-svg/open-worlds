// rust/ur-world/src/host.rs
//! Hosting: the garden gives other worlds a place and time.
//!
//! The founder pictured the Ur-world as "a microverse garden of hosted
//! fractal worlds" (docs/URWORLD.md). A hosted world is a primary world of
//! its own, with its own key and its own log; the Ur-world gives it a place
//! in the garden, a glasshouse, and time: each tick, after its inhabitants
//! have acted, the Ur-world tends every world it hosts, one step of that
//! world's own time.
//!
//! Two logs record each step, as DeepSeek's microverse did (record
//! 012-06-02, piece 47: "two logs, one social act"): the hosted world
//! writes the step in its own log, and the Ur-world's `tended` entry names
//! the hash of that entry. So anyone holding both logs can check, with
//! [`hosting_problems`], that the Ur-world gave each world exactly the
//! steps its log shows, in order, and nothing more.
//!
//! Entries the Ur-world writes:
//! - `hosted`: `{world, kind, at, first, from}`: the hosted world's key,
//!   the rule it grows by, its glasshouse's cell, the hash of its log's
//!   first entry, and of its last entry when it came.
//! - `tended`: `{worlds: [[key, hash], ...]}`: in the order they were
//!   hosted, each world that took a step this tick, and the hash of the
//!   entry that step wrote.
//! - `untended`: `{world, reason}`: a world that couldn't take its step,
//!   and isn't tended again.

use std::collections::BTreeMap;

use plant_world::world::{PlantWorld, RULE};
use serde_json::Value;

use crate::generate::{GARDEN_RADIUS, SPRING, garden_piece};
use crate::space::Cell;

/// A world the Ur-world hosts: a primary world of its own.
pub trait Hosted {
    /// Its key, as a did:key: the `world` its first entry names.
    fn key(&self) -> &str;
    /// The rule it grows by.
    fn kind(&self) -> &str;
    /// Its log, in the common format (`world_log`).
    fn log(&self) -> &[Value];
    /// Whether it has finished: it takes no more steps.
    fn finished(&self) -> bool;
    /// One step of its own time. Refused, with the reason, if it can't.
    fn tend(&mut self) -> Result<(), String>;
    /// Itself, so its own kind can be read back (for a plant, its signed
    /// head and birth record).
    fn as_any(&self) -> &dyn std::any::Any;
}

impl Hosted for PlantWorld {
    fn key(&self) -> &str {
        PlantWorld::key(self)
    }
    fn kind(&self) -> &str {
        RULE
    }
    fn log(&self) -> &[Value] {
        PlantWorld::log(self)
    }
    fn finished(&self) -> bool {
        PlantWorld::finished(self)
    }
    fn tend(&mut self) -> Result<(), String> {
        self.grow().map(|_| ())
    }
    fn as_any(&self) -> &dyn std::any::Any {
        self
    }
}

/// Why a world can't be hosted where it was asked.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum HostError {
    /// The place isn't on the garden's ground: why.
    Place(&'static str),
    /// A glasshouse stands there already.
    Taken,
    /// That world is hosted here already.
    AlreadyHosted,
    /// The world's log is empty, or its first entry doesn't name its key.
    NoLog,
    /// The world's key is the Ur-world's own.
    OwnKey,
}

impl std::fmt::Display for HostError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            HostError::Place(why) => write!(f, "a glasshouse can't stand there: {why}"),
            HostError::Taken => write!(f, "a glasshouse stands there already"),
            HostError::AlreadyHosted => write!(f, "that world is hosted here already"),
            HostError::NoLog => write!(
                f,
                "that world's log is empty, or doesn't begin by naming its key"
            ),
            HostError::OwnKey => write!(f, "a world can't host itself"),
        }
    }
}

impl std::error::Error for HostError {}

/// Why a glasshouse can't stand at `at`, if it can't. It stands on the
/// garden's ground: one cell above it (`y` = 1), within the garden's
/// radius, and not in the tree's trunk or over the spring.
pub fn place_problem(at: Cell) -> Option<&'static str> {
    if at.y != 1 {
        return Some("it must stand on the garden's ground, at y = 1");
    }
    let (x, z) = (at.x.unsigned_abs(), at.z.unsigned_abs());
    let radius = GARDEN_RADIUS.unsigned_abs();
    // Compared before squaring, so nothing overflows.
    if x > radius || z > radius || (x * x + z * z).isqrt() > radius {
        return Some("it must be within the garden");
    }
    if garden_piece(at).is_some() {
        return Some("the tree stands there");
    }
    if at.x == SPRING.x && at.z == SPRING.z {
        return Some("the spring is there");
    }
    None
}

/// A world in a glasshouse.
pub struct Glasshouse {
    /// Where it stands.
    pub at: Cell,
    /// The world.
    pub world: Box<dyn Hosted>,
    /// Whether it couldn't take a step, and is no longer tended.
    pub untended: bool,
}

fn text<'a>(value: &'a Value, key: &str) -> Option<&'a str> {
    value.get(key).and_then(Value::as_str)
}

/// What is wrong with how a log of the Ur-world hosted the worlds whose
/// logs are given, if anything: each `hosted` entry names a world whose
/// log is given, by the hash of its first entry and of the entry it was at
/// when it came; each `tended` entry names, for each world, exactly the
/// next entry of that world's log; and each hosted log ends at the last
/// entry the Ur-world tended, and holds together as a log. A given log the
/// Ur-world never hosted is a problem too. Each problem names the entry of
/// the Ur-world's log (`[i]`) or the hosted world (by its key).
///
/// Whether each hosted log grows by its own rule is that world's check
/// (for a plant, `plant_world::world::log_problems`).
pub fn hosting_problems(log: &[Value], hosted: &[&[Value]]) -> Vec<String> {
    let mut problems = Vec::new();
    // Each given log, by the key its first entry names, and the index of
    // the last entry the Ur-world has accounted for (None until hosted).
    let mut logs: BTreeMap<String, (&[Value], Option<usize>, bool)> = BTreeMap::new();
    for given in hosted {
        let key = given
            .first()
            .and_then(|e| e.get("data"))
            .and_then(|d| text(d, "world"));
        match key {
            Some(key) if !logs.contains_key(key) => {
                if let Err(e) = world_log::verify_log(&Value::Array(given.to_vec())) {
                    problems.push(format!("{key}: its log doesn't hold together: {e}"));
                }
                logs.insert(key.to_owned(), (*given, None, false));
            }
            Some(key) => problems.push(format!("{key}: its log is given twice")),
            None => problems.push("a given log doesn't begin by naming its world".into()),
        }
    }
    for (i, entry) in log.iter().enumerate() {
        let data = entry.get("data").unwrap_or(&Value::Null);
        match entry.get("kind").and_then(Value::as_str) {
            Some("hosted") => {
                let Some(key) = text(data, "world") else {
                    problems.push(format!("[{i}]: hosts a world it doesn't name"));
                    continue;
                };
                let Some((given, at, _)) = logs.get_mut(key) else {
                    problems.push(format!("[{i}]: hosts {key}, whose log isn't given"));
                    continue;
                };
                if at.is_some() {
                    problems.push(format!("[{i}]: hosts {key} a second time"));
                    continue;
                }
                let hash_at = |j: usize| given.get(j).and_then(|e| text(e, "hash"));
                if text(data, "first") != hash_at(0) {
                    problems.push(format!("[{i}]: names another first entry for {key}"));
                }
                let from = text(data, "from");
                match (0..given.len()).find(|&j| hash_at(j) == from) {
                    Some(j) => *at = Some(j),
                    None => {
                        problems.push(format!("[{i}]: names an entry {key}'s log doesn't have"));
                        *at = Some(0);
                    }
                }
            }
            Some("tended") => {
                let Some(pairs) = data.get("worlds").and_then(Value::as_array) else {
                    problems.push(format!("[{i}]: tends, but names no worlds"));
                    continue;
                };
                for pair in pairs {
                    let (Some(key), Some(hash)) = (
                        pair.get(0).and_then(Value::as_str),
                        pair.get(1).and_then(Value::as_str),
                    ) else {
                        problems.push(format!("[{i}]: names a world it tended unreadably"));
                        continue;
                    };
                    match logs.get_mut(key) {
                        Some((given, Some(at), false)) => {
                            let next = *at + 1;
                            if given.get(next).and_then(|e| text(e, "hash")) == Some(hash) {
                                *at = next;
                            } else {
                                problems.push(format!(
                                    "[{i}]: tends {key} to an entry that isn't its next"
                                ));
                            }
                        }
                        Some((_, Some(_), true)) => {
                            problems.push(format!("[{i}]: tends {key} after it was untended"));
                        }
                        _ => problems.push(format!("[{i}]: tends {key}, which isn't hosted")),
                    }
                }
            }
            Some("untended") => match text(data, "world").and_then(|k| logs.get_mut(k)) {
                Some((_, Some(_), stopped)) => *stopped = true,
                _ => problems.push(format!("[{i}]: leaves untended a world it doesn't host")),
            },
            _ => {}
        }
    }
    for (key, (given, at, _)) in &logs {
        match at {
            None => problems.push(format!("{key}: not hosted in this log")),
            Some(at) if at + 1 != given.len() => problems.push(format!(
                "{key}: its log goes on past what the Ur-world tended"
            )),
            Some(_) => {}
        }
    }
    problems
}
