// rust/formats/src/persons.rs
//! Persons: one individual across worlds (`docs/research/PERSONS.md`),
//! course step 3a, part two: the formats. The same as the Python
//! `formats/persons.py`, checked against it through
//! `vectors/formats/persons-v1.json`.
//!
//! - **Presence keys** ([`presence_secret`]): HKDF-SHA256 (RFC 5869) with
//!   the person's presence seed (32 random bytes) as the input key
//!   material and no salt; `info` is the label `open-worlds/presence/v1`,
//!   a zero byte, the world's did:key in ASCII, a zero byte, and the
//!   counter as four bytes, big-endian ([`presence_info`]). Its 32 bytes
//!   out are the presence's Ed25519 secret key: RFC 8032 takes any 32
//!   bytes.
//! - **A link holds only both ways** ([`link_problems`]):
//!   `open-worlds/holds/v1`, signed by the person, and
//!   `open-worlds/held-by/v1`, signed by the presence, naming the same
//!   person, presence and world.
//! - **The person's list** ([`person_list_chain_problems`]): versions
//!   that each name the one before by hash, signed by the person's
//!   identity key, with no presence twice.
//!
//! # Limits
//!
//! - A dropped presence is shown by comparing two versions of a list, not
//!   refused: whether a person may drop one is theirs to decide.
//! - Whether a world has admitted a presence, and has seen it linked to
//!   no one else, is the world's to check when a link is shown there
//!   (part three: `rust/ur-world/src/link.rs`).

use hkdf::Hkdf;
use serde_json::Value;
use sha2::Sha256;

use crate::multikey::{did_key, public_from_multikey};
use crate::proof::public_key;
use crate::records::{check, record_hash};

/// The label at the start of every presence key's `info`.
pub const LABEL: &[u8] = b"open-worlds/presence/v1";
/// A person's half of a link.
pub const HOLDS: &str = "open-worlds/holds/v1";
/// A presence's half of a link.
pub const HELD_BY: &str = "open-worlds/held-by/v1";
/// A person's list of their presences.
pub const PERSON_LIST: &str = "open-worlds/person-list/v1";

/// HKDF's `info` for the presence `counter` in `world` (a did:key).
/// Refused if the world isn't an Ed25519 did:key.
pub fn presence_info(world: &str, counter: u32) -> Result<Vec<u8>, String> {
    let multikey = world
        .strip_prefix("did:key:")
        .ok_or("the world isn't a did:key")?;
    public_from_multikey(multikey)
        .map_err(|e| format!("the world isn't an Ed25519 did:key: {e}"))?;
    let mut info = Vec::with_capacity(LABEL.len() + world.len() + 6);
    info.extend_from_slice(LABEL);
    info.push(0);
    info.extend_from_slice(world.as_bytes());
    info.push(0);
    info.extend_from_slice(&counter.to_be_bytes());
    Ok(info)
}

/// The Ed25519 secret key of the presence `counter` in `world`, made from
/// the person's presence `seed`.
pub fn presence_secret(seed: &[u8; 32], world: &str, counter: u32) -> Result<[u8; 32], String> {
    let info = presence_info(world, counter)?;
    let mut secret = [0_u8; 32];
    Hkdf::<Sha256>::new(None, seed)
        .expand(&info, &mut secret)
        .map_err(|e| format!("HKDF refused: {e}"))?;
    Ok(secret)
}

/// The did:key of the presence `counter` in `world`.
pub fn presence_key(seed: &[u8; 32], world: &str, counter: u32) -> Result<String, String> {
    Ok(did_key(&public_key(&presence_secret(
        seed, world, counter,
    )?)))
}

fn text<'a>(record: &'a Value, field: &str) -> Option<&'a str> {
    record.get(field).and_then(Value::as_str)
}

/// Why the two halves don't make a link, or an empty list: each must hold,
/// as its kind, signed by the one it must be (the person, the presence),
/// and both must name the same person, presence and world; a person's
/// identity key is never one of their presences.
pub fn link_problems(holds: &Value, held_by: &Value) -> Vec<String> {
    let mut found = Vec::new();
    for (name, record, format) in [("holds", holds, HOLDS), ("held-by", held_by, HELD_BY)] {
        if text(record, "format") != Some(format) {
            found.push(format!("{name}: not a record of the format {format}"));
            continue;
        }
        if let Err(e) = check(record) {
            found.push(format!("{name}: {e}"));
        }
    }
    if !found.is_empty() {
        return found;
    }
    for field in ["person", "presence", "world"] {
        if text(holds, field) != text(held_by, field) {
            found.push(format!("the two halves name another {field}"));
        }
    }
    if text(holds, "person") == text(holds, "presence") {
        found.push("the presence is the person's own identity key".into());
    }
    found
}

fn person_list(record: &Value) -> Result<(), String> {
    if text(record, "format") != Some(PERSON_LIST) {
        return Err(format!("not a record of the format {PERSON_LIST}"));
    }
    check(record).map(|_| ())
}

fn presences(record: &Value) -> &[Value] {
    record
        .get("presences")
        .and_then(Value::as_array)
        .map_or(&[], Vec::as_slice)
}

/// Where a person's list repeats itself, or lists the person, or an empty
/// list: no two presences with the same world and counter, or the same
/// key, and no presence whose key is the person's own identity key, which
/// never enters a world (`docs/research/PERSONS.md`, decision 1).
pub fn entries_problems(person_list: &Value) -> Vec<String> {
    let mut found = Vec::new();
    let mut places = std::collections::BTreeSet::new();
    let mut keys = std::collections::BTreeSet::new();
    for (i, entry) in presences(person_list).iter().enumerate() {
        if text(entry, "key").is_some() && text(entry, "key") == text(person_list, "person") {
            found.push(format!("$.presences.{i}: the person's own identity key"));
        }
        let place = (
            text(entry, "world"),
            entry.get("counter").and_then(Value::as_u64),
        );
        if !places.insert(place) {
            found.push(format!(
                "$.presences.{i}: a second presence with this world and counter"
            ));
        }
        if !keys.insert(text(entry, "key")) {
            found.push(format!("$.presences.{i}: a second presence with this key"));
        }
    }
    found
}

/// Where a version of a person's list fails to follow the one before, or
/// an empty list: both must hold; it must name that version by hash, be
/// the next number, be the same person's, and be no earlier; and it must
/// not repeat itself. A presence dropped or added between the two is shown
/// by comparing them, not refused.
pub fn person_list_problems(new: &Value, previous: &Value) -> Vec<String> {
    let mut found = Vec::new();
    for (name, record) in [("new", new), ("previous", previous)] {
        if let Err(e) = person_list(record) {
            found.push(format!("{name}: {e}"));
        }
    }
    if !found.is_empty() {
        return found;
    }
    match record_hash(previous) {
        Ok(hash) if text(new, "previous") == Some(hash.as_str()) => {}
        _ => found.push("$.previous: names another version".into()),
    }
    let version = |r: &Value| r.get("version").and_then(Value::as_u64);
    if version(new) != version(previous).and_then(|v| v.checked_add(1)) {
        found.push("$.version: not the next version".into());
    }
    if text(new, "person") != text(previous, "person") {
        found.push("$.person: another person's list".into());
    }
    if text(new, "time") < text(previous, "time") {
        found.push("$.time: earlier than the version before".into());
    }
    found.extend(entries_problems(new));
    found
}

/// Where a person's list's history fails, or an empty list: from version
/// 1, each version following the one before. Each problem names the
/// version's place in `versions`.
pub fn person_list_chain_problems(versions: &[Value]) -> Vec<String> {
    let Some(first) = versions.first() else {
        return vec!["[]: no versions".into()];
    };
    let mut found: Vec<String> = versions
        .iter()
        .enumerate()
        .filter_map(|(i, r)| person_list(r).err().map(|e| format!("[{i}] {e}")))
        .collect();
    if !found.is_empty() {
        return found;
    }
    if first.get("version").and_then(Value::as_u64) != Some(1) {
        found.push("[0] $.version: the history doesn't start at 1".into());
    }
    found.extend(
        entries_problems(first)
            .into_iter()
            .map(|p| format!("[0] {p}")),
    );
    for (i, pair) in versions.windows(2).enumerate() {
        if let [previous, new] = pair {
            found.extend(
                person_list_problems(new, previous)
                    .into_iter()
                    .map(|p| format!("[{}] {p}", i + 1)),
            );
        }
    }
    found
}

/// Which presences in a person's list weren't made from `seed` with their
/// world and counter, or an empty list: what the person's own client
/// checks. The list must hold ([`person_list_chain_problems`]); given one
/// that doesn't, an entry whose world and counter make no key (one
/// missing, or not a key's) is reported as not made from the seed if it
/// has a key, and passed over if it has none.
pub fn seed_problems(person_list: &Value, seed: &[u8; 32]) -> Vec<String> {
    presences(person_list)
        .iter()
        .enumerate()
        .filter(|(_, e)| {
            let counter = e
                .get("counter")
                .and_then(Value::as_u64)
                .and_then(|c| u32::try_from(c).ok());
            let made = match (text(e, "world"), counter) {
                (Some(world), Some(counter)) => presence_key(seed, world, counter).ok(),
                _ => None,
            };
            made.as_deref() != text(e, "key")
        })
        .map(|(i, _)| format!("$.presences.{i}: its key isn't the one its world and counter give"))
        .collect()
}
