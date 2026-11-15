// rust/ur-world/src/link.rs
//! Links shown in a world: a presence shows, by its own act, that a person
//! holds it (docs/research/PERSONS.md, decision 4; course step 3a, part
//! three).
//!
//! A link is two records, which [`formats::persons::link_problems`]
//! checks: the person's `open-worlds/holds/v1`, signed by their identity
//! key, and the presence's `open-worlds/held-by/v1`, signed by the
//! presence. An inhabitant shows one on its turn, as an action
//! ([`crate::Action::ShowLink`]), and the world takes it only if:
//! - both records hold, as one link;
//! - it names this world;
//! - its presence is the key that the one who shows it entered under:
//!   so showing is the presence's own act, and the presence is one the
//!   world has admitted;
//! - this presence has shown no link here before: a presence is held by
//!   one person, and a link, once shown, is shown for good.
//!
//! The world writes a link it takes into its log whole, as `linked`, so
//! anyone can check it ([`link_log_problems`]). A link it refuses is
//! written as `blocked`, with a fixed reason, and without the records:
//! shown in the wrong world, a link that holds in its own would otherwise
//! be published here, linking that world's presence to its person in
//! public. The reason's details are told only to the one who showed it.
//!
//! # Limits
//!
//! - **The person is a key, not a born identity.** No check here, nor in
//!   `link_problems`, asks whether a world signed the person's birth
//!   (births come at the course's step 9). A link shows which key holds a
//!   presence; it shows neither who the person is nor that they are one
//!   (PERSONS.md, decision 8).
//! - **A person's identity key never enters a world** (decision 1), but a
//!   world doesn't check that: it is the person's to keep.
//! - **Minds through the doorway can't show a link yet:** the doorway
//!   reads a reply as a line of text ([`crate::door::read_reply`]), and a
//!   link is two signed records.

use std::collections::{BTreeMap, BTreeSet};
use std::fmt;

use formats::persons::link_problems;
use serde_json::Value;

use crate::arrival::log_world;

/// Why a world refuses a link.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Refusal {
    /// The two records don't make a link: why, as
    /// [`formats::persons::link_problems`] says.
    DoesntHold(Vec<String>),
    /// The link names another world.
    OtherWorld,
    /// The link is another presence's: not the key the one who shows it
    /// entered under.
    NotYours,
    /// This presence has shown this person's link here already.
    Shown,
    /// This presence has shown a link to another person here.
    HeldByAnother,
}

impl Refusal {
    /// The reason as the log writes it: fixed words, with no detail from
    /// the records, which the log never holds for a link it refused.
    pub const fn reason(&self) -> &'static str {
        match self {
            Refusal::DoesntHold(_) => "the link doesn't hold",
            Refusal::OtherWorld => "the link names another world",
            Refusal::NotYours => "the link is another presence's",
            Refusal::Shown => "this presence's link is shown here already",
            Refusal::HeldByAnother => "this presence is held by another person here",
        }
    }
}

impl fmt::Display for Refusal {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Refusal::DoesntHold(why) => write!(f, "{}: {}", self.reason(), why.join("; ")),
            other => write!(f, "{}", other.reason()),
        }
    }
}

impl std::error::Error for Refusal {}

fn text<'a>(v: &'a Value, key: &str) -> &'a str {
    v.get(key).and_then(Value::as_str).unwrap_or("")
}

/// Why `world` (a did:key) refuses the link `holds` and `held_by`, shown
/// by the one who entered with the key `presence`, given the links shown
/// there before (each presence's key, and the person who holds it); or
/// `None` if it takes it.
pub(crate) fn refusal(
    world: &str,
    presence: &str,
    holds: &Value,
    held_by: &Value,
    links: &BTreeMap<String, String>,
) -> Option<Refusal> {
    let problems = link_problems(holds, held_by);
    if !problems.is_empty() {
        return Some(Refusal::DoesntHold(problems));
    }
    // The two halves name the same person, presence and world, so either
    // can be read.
    if text(holds, "world") != world {
        return Some(Refusal::OtherWorld);
    }
    if text(holds, "presence") != presence {
        return Some(Refusal::NotYours);
    }
    match links.get(presence) {
        Some(person) if person == text(holds, "person") => Some(Refusal::Shown),
        Some(_) => Some(Refusal::HeldByAnother),
        None => None,
    }
}

/// Where the links shown in an Ur-world log fail, or an empty list: each
/// `linked` entry must be by one who is here, carry both records, and be
/// a link the world would take ([`Refusal`]), with the presence's key
/// read from the arrival its name first entered with. The arrivals
/// themselves are [`crate::arrival::arrival_problems`]'s to check, and the
/// chain `world_log::verify_log`'s. Each problem names the entry's place
/// in the log, counting from 0.
pub fn link_log_problems(log: &[Value]) -> Vec<String> {
    let Some(world) = log_world(log) else {
        return vec!["[0]: not a world_created entry that names its world".into()];
    };
    let mut found = Vec::new();
    let mut keys: BTreeMap<&str, &str> = BTreeMap::new();
    let mut here: BTreeSet<&str> = BTreeSet::new();
    let mut links: BTreeMap<String, String> = BTreeMap::new();
    for (i, entry) in log.iter().enumerate() {
        let who = text(entry, "agent");
        let data = entry.get("data");
        match text(entry, "kind") {
            "entered" => {
                let key = data
                    .and_then(|d| d.get("arrival"))
                    .map_or("", |a| text(a, "individual"));
                keys.entry(who).or_insert(key);
                here.insert(who);
            }
            "exited" => {
                here.remove(who);
            }
            "linked" => {
                if !here.contains(who) {
                    found.push(format!("[{i}]: a link shown by one who isn't here"));
                    continue;
                }
                let (Some(holds), Some(held_by)) = (
                    data.and_then(|d| d.get("holds")),
                    data.and_then(|d| d.get("held_by")),
                ) else {
                    found.push(format!("[{i}]: an entry with no link"));
                    continue;
                };
                let presence = keys.get(who).copied().unwrap_or("");
                match refusal(world, presence, holds, held_by, &links) {
                    Some(why) => found.push(format!("[{i}]: a link the world refuses: {why}")),
                    None => {
                        links.insert(presence.to_owned(), text(holds, "person").to_owned());
                    }
                }
            }
            _ => {}
        }
    }
    found
}
