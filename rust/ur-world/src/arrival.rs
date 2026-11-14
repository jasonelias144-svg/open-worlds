// rust/ur-world/src/arrival.rs
//! Arrivals: how an individual enters a world as their key, so that
//! whoever comes back with the same key is known as the same individual
//! (docs/research/KEYS.md, decisions 11 to 17).
//!
//! On entering, the individual's key signs an arrival,
//! `open-worlds/arrival/v1` in records-v1: the world's did:key, their own,
//! the name they enter under, the tick, and `previous`, the hash of the
//! world's log entry just before the arrival's own. The world holds an
//! arrival only over its log's last entry as it is now ([`World::admit`]),
//! so one arrival can't be used twice in one history, and two arrivals in
//! one tick are ordered, each signed over the one before. Once a name is
//! bound, it is its individual's: an arrival under it signed by another
//! key is refused, and one signed by the same key is the individual
//! coming back. Leaving needs no signature: `exit` always works.
//!
//! A world has a key of its own, which every arrival names, and which
//! signs the heads of its log (`open-worlds/log-head/v1`, [`head`]). A
//! reader who holds a head the world signed knows that much of the log
//! is the world's own: [`head_coverage`] says how much of a log the heads
//! given cover, and [`arrival_problems`] checks every arrival in it.
//!
//! # Limits
//!
//! - An arrival proves the key, not the program (KEYS.md, "Honest
//!   limits"): while the doorway signs, whoever runs it can enter as
//!   anyone whose key it holds.
//! - Only the birth key is checked: a name is bound to the key that
//!   signed its first arrival. Successions aren't a records-v1 record yet,
//!   so a key signed over from it can't come back under the name.
//! - Trial keys ([`trial_secret`]) are made from the seed, so anyone can
//!   make them: they are for trial worlds, tests and the shared vectors,
//!   never for the Ur-world or an individual.

use formats::multikey::did_key;
use formats::proof::{self, public_key};
use formats::records;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};

use crate::world::World;

/// The arrival's format, in records-v1.
pub const FORMAT: &str = "open-worlds/arrival/v1";

/// The signed head's format, in records-v1.
pub const HEAD: &str = "open-worlds/log-head/v1";

/// The did:key of the holder of `secret`.
pub fn did(secret: &[u8; 32]) -> String {
    did_key(&public_key(secret))
}

/// A key made from a seed and a label, for trial worlds, tests and the
/// shared vectors only. Anyone who knows the seed can make it, so it
/// protects nothing: never the Ur-world's or an individual's key.
pub fn trial_secret(seed: u64, label: &str) -> [u8; 32] {
    Sha256::digest(format!(
        "open-worlds trial key, never for anything real: {seed}: {label}"
    ))
    .into()
}

/// The arrival of the holder of `secret` into `world` as it is now, under
/// `name`: over the world's tick and its log's last entry. `created` is
/// the signer's clock, `YYYY-MM-DDTHH:MM:SSZ`, and no evidence of when the
/// arrival happened: the log's order is. Whether the world admits it is
/// the world's to say ([`World::admit`]).
pub fn sign(world: &World, secret: &[u8; 32], name: &str, created: &str) -> Result<Value, String> {
    let record = json!({
        "format": FORMAT,
        "world": world.key(),
        "individual": did(secret),
        "name": name,
        "tick": world.tick(),
        "previous": world.last_hash(),
    });
    proof::sign(&record, secret, created, "assertionMethod")
}

/// The world's signed head of its log as it is now: its length, the hash
/// of its last entry, and the tick, signed with `secret`, which must be
/// the world's own key.
pub fn head(world: &World, secret: &[u8; 32], created: &str) -> Result<Value, String> {
    if did(secret) != world.key() {
        return Err("only the world's own key signs its log's head".into());
    }
    let record = json!({
        "format": HEAD,
        "world": world.key(),
        "length": world.log().len(),
        "last": world.last_hash(),
        "tick": world.tick(),
    });
    let signed = proof::sign(&record, secret, created, "assertionMethod")?;
    records::check(&signed)?;
    Ok(signed)
}

/// A signed record's checked fields, if it holds and is of `format`.
pub(crate) fn checked(record: &Value, format: &str) -> Result<Value, String> {
    let unsecured = records::check(record)?;
    if unsecured.get("format").and_then(Value::as_str) != Some(format) {
        return Err(format!("$.format: not {format}"));
    }
    Ok(unsecured)
}

fn text<'a>(v: &'a Value, key: &str) -> &'a str {
    v.get(key).and_then(Value::as_str).unwrap_or("")
}

/// The world a log names in its first entry, `world_created`.
pub fn log_world(log: &[Value]) -> Option<&str> {
    let first = log.first()?;
    if first.get("kind").and_then(Value::as_str) != Some("world_created") {
        return None;
    }
    first.get("data")?.get("world")?.as_str()
}

/// Where the arrivals in an Ur-world log fail, or an empty list. The
/// log's chain of hashes is `world_log::verify_log`'s to check; this
/// checks that the first entry names the world, and that each `entered`
/// entry carries an arrival that holds, signed by the one who entered,
/// naming this world, the entry's tick, the entry just before it, and
/// the entry's name; that a name stays its individual's and an
/// individual keeps one name; and that no one enters while here. Each
/// problem names the entry's place in the log, counting from 0.
pub fn arrival_problems(log: &[Value]) -> Vec<String> {
    let Some(world) = log_world(log) else {
        return vec!["[0]: not a world_created entry that names its world".into()];
    };
    let mut found = Vec::new();
    let mut names: std::collections::BTreeMap<&str, String> = std::collections::BTreeMap::new();
    let mut known: std::collections::BTreeMap<String, &str> = std::collections::BTreeMap::new();
    let mut here: std::collections::BTreeSet<&str> = std::collections::BTreeSet::new();
    for (i, entry) in log.iter().enumerate() {
        let kind = text(entry, "kind");
        let who = text(entry, "agent");
        if kind == "exited" {
            here.remove(who);
            continue;
        }
        if kind != "entered" {
            continue;
        }
        let Some(arrival) = entry.get("data").and_then(|d| d.get("arrival")) else {
            found.push(format!("[{i}]: an entry with no arrival"));
            continue;
        };
        let a = match checked(arrival, FORMAT) {
            Ok(a) => a,
            Err(e) => {
                found.push(format!("[{i}]: the arrival doesn't hold: {e}"));
                continue;
            }
        };
        let individual = text(&a, "individual").to_owned();
        let mut wrong = Vec::new();
        if text(&a, "world") != world {
            wrong.push("names another world");
        }
        if a.get("tick") != entry.get("tick") {
            wrong.push("names another tick");
        }
        if a.get("previous") != entry.get("prev") {
            wrong.push("names another entry before it");
        }
        if text(&a, "name") != who {
            wrong.push("names another name");
        }
        if names.get(who).is_some_and(|bound| *bound != individual) {
            wrong.push("is under a name bound to another key");
        }
        if known.get(&individual).is_some_and(|name| *name != who) {
            wrong.push("is signed by one who has another name here");
        }
        if here.contains(who) {
            wrong.push("is by one who is here already");
        }
        for w in wrong {
            found.push(format!("[{i}]: the arrival {w}"));
        }
        names.entry(who).or_insert_with(|| individual.clone());
        known.entry(individual).or_insert(who);
        here.insert(who);
    }
    found
}

/// How much of `log` the signed `heads` cover: the longest length of a
/// head that holds for it, with a problem for each head that doesn't. A
/// head holds for a log when it is a log head that holds, signed by the
/// world the log names, and its length, last hash and tick agree with the
/// log: so a log cut short, or shown two ways, is caught.
pub fn head_coverage(log: &[Value], heads: &[Value]) -> (usize, Vec<String>) {
    let mut covered = 0;
    let mut found = Vec::new();
    let world = log_world(log);
    for (i, signed) in heads.iter().enumerate() {
        let h = match checked(signed, HEAD) {
            Ok(h) => h,
            Err(e) => {
                found.push(format!("head {i}: doesn't hold: {e}"));
                continue;
            }
        };
        if world != Some(text(&h, "world")) {
            found.push(format!("head {i}: signed by another world"));
            continue;
        }
        let length = h
            .get("length")
            .and_then(Value::as_u64)
            .and_then(|n| usize::try_from(n).ok())
            .unwrap_or(usize::MAX);
        let tick = h.get("tick").and_then(Value::as_u64).unwrap_or(0);
        let (last, before, after) = match length.checked_sub(1) {
            None => (world_log::GENESIS, None, log.first()),
            Some(at) => match log.get(at) {
                Some(e) => (text(e, "hash"), Some(e), log.get(length)),
                None => {
                    found.push(format!("head {i}: longer than the log"));
                    continue;
                }
            },
        };
        let entry_tick = |e: Option<&Value>| e.and_then(|e| e.get("tick")).and_then(Value::as_u64);
        if text(&h, "last") != last {
            found.push(format!("head {i}: its last hash isn't the log's"));
        } else if entry_tick(before).is_some_and(|t| t > tick)
            || entry_tick(after).is_some_and(|t| t < tick)
        {
            found.push(format!("head {i}: its tick doesn't fit the log"));
        } else {
            covered = covered.max(length);
        }
    }
    (covered, found)
}

/// A UTC time to the second, `YYYY-MM-DDTHH:MM:SSZ`, from seconds since
/// 1970-01-01T00:00:00Z: a signer's clock, as a proof's `created` writes
/// it. Days are turned into dates as in Howard Hinnant's
/// `civil_from_days`.
pub fn utc(seconds: u64) -> String {
    let days = seconds / 86_400;
    let rest = seconds % 86_400;
    let z = days + 719_468;
    let era = z / 146_097;
    let doe = z % 146_097;
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let day = doy - (153 * mp + 2) / 5 + 1;
    let month = if mp < 10 { mp + 3 } else { mp - 9 };
    let year = yoe + era * 400 + u64::from(month <= 2);
    format!(
        "{year:04}-{month:02}-{day:02}T{:02}:{:02}:{:02}Z",
        rest / 3600,
        rest % 3600 / 60,
        rest % 60
    )
}

#[cfg(test)]
// Tests may unwrap: a failure here is a failed test.
#[allow(clippy::unwrap_used)]
mod tests {
    use super::*;

    #[test]
    fn times_are_written_as_a_proof_writes_them() {
        assert_eq!(utc(0), "1970-01-01T00:00:00Z");
        assert_eq!(utc(951_782_400), "2000-02-29T00:00:00Z");
        assert_eq!(utc(1_709_251_199), "2024-02-29T23:59:59Z");
        // The day the Ur-world was decided, and the turn of a century that
        // isn't a leap year.
        assert_eq!(utc(1_794_528_000), "2026-11-13T00:00:00Z");
        assert_eq!(utc(4_107_542_400), "2100-03-01T00:00:00Z");
        for s in [0, 951_782_400, 1_794_528_000, 4_107_542_399] {
            assert!(proof::check_time(Some(&json!(utc(s)))).is_ok());
        }
    }

    #[test]
    fn trial_keys_differ_by_seed_and_label() {
        let a = trial_secret(1, "A");
        assert_eq!(a, trial_secret(1, "A"));
        assert_ne!(a, trial_secret(2, "A"));
        assert_ne!(a, trial_secret(1, "B"));
        assert!(did(&a).starts_with("did:key:z6Mk"));
    }
}
