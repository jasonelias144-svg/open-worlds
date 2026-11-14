//! The records the offices keep (course step 2): a grant, a decision
//! record, a suggestion, a rating and a signed log head, and an
//! individual's world-key and journal entry, as
//! `formats/records.py` checks them, from the same schema file. A record
//! holds when it fits its kind's schema, its proof verifies, and it was
//! signed by the one who must sign that kind.

use serde_json::{Value, json};
use sha2::{Digest, Sha256};

use crate::canonical::canonical;
use crate::multikey::public_multikey;
use crate::proof::{check_time, verify};

/// The schema, read at build time from `schemas/records-v1.schema.json`.
pub const SCHEMA: &str = include_str!("../../../schemas/records-v1.schema.json");

/// Each format, its schema's name in `$defs`, and the path of the field
/// that names its signer.
pub const KINDS: [(&str, &str, &[&str]); 7] = [
    ("open-worlds/grant/v1", "grant", &["issuer"]),
    ("open-worlds/decision/v1", "decision", &["office", "key"]),
    ("open-worlds/suggestion/v1", "suggestion", &["author"]),
    ("open-worlds/rating/v1", "rating", &["author"]),
    ("open-worlds/log-head/v1", "logHead", &["world"]),
    ("open-worlds/world-key/v1", "worldKey", &["issuer"]),
    ("open-worlds/journal-entry/v1", "journalEntry", &["author"]),
];

fn kind(record: &Value) -> Option<&'static (&'static str, &'static str, &'static [&'static str])> {
    let format = record.get("format")?.as_str()?;
    KINDS.iter().find(|(f, _, _)| *f == format)
}

/// Where `record` doesn't fit its kind's schema, or an empty list.
pub fn problems(record: &Value) -> Result<Vec<String>, String> {
    let Some((_, name, _)) = kind(record) else {
        return Ok(vec!["$: not a record of a kind in records-v1".into()]);
    };
    def_problems(name, record)
}

/// Where `value` doesn't fit the schema's `$defs/<name>`, or an empty list.
pub fn def_problems(name: &str, value: &Value) -> Result<Vec<String>, String> {
    let schema: Value = serde_json::from_str(SCHEMA).map_err(|e| e.to_string())?;
    let defs = schema.get("$defs").ok_or("the schema has no $defs")?;
    let one = json!({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$defs": defs,
        "$ref": format!("#/$defs/{name}"),
    });
    let validator = jsonschema::draft202012::new(&one).map_err(|e| e.to_string())?;
    Ok(validator
        .iter_errors(value)
        .map(|e| format!("{}: {}", e.instance_path(), e))
        .collect())
}

/// A grant's times must be real, and it must end after it starts; the
/// schema checks only their shape.
fn time_problems(record: &Value) -> Vec<String> {
    if record.get("format").and_then(Value::as_str) != Some("open-worlds/grant/v1") {
        return Vec::new();
    }
    let mut found: Vec<String> = ["validFrom", "validUntil"]
        .iter()
        .filter(|field| {
            record
                .get(**field)
                .is_some_and(|value| check_time(Some(value)).is_err())
        })
        .map(|field| format!("$.{field}: not a real UTC time"))
        .collect();
    let from = record.get("validFrom").and_then(Value::as_str);
    let until = record.get("validUntil").and_then(Value::as_str);
    if found.is_empty()
        && let (Some(from), Some(until)) = (from, until)
        && until <= from
    {
        found.push("$.validUntil: not after validFrom".into());
    }
    found
}

/// `record` without its proof, if it holds.
pub fn check(record: &Value) -> Result<Value, String> {
    let mut found = problems(record)?;
    found.extend(time_problems(record));
    if !found.is_empty() {
        return Err(found.join("; "));
    }
    let (_, _, path) = kind(record).ok_or("not a record of a kind in records-v1")?;
    let (unsecured, public) = verify(record)?;
    let mut signer = record;
    for key in path.iter() {
        signer = signer.get(*key).ok_or("no signer field")?;
    }
    if signer.as_str() != Some(format!("did:key:{}", public_multikey(&public)).as_str()) {
        return Err("signed by another key than the one that must sign".into());
    }
    Ok(unsecured)
}

/// SHA-256 of `record`'s RFC 8785 form, proof included, in lowercase hex.
pub fn record_hash(record: &Value) -> Result<String, String> {
    let digest = Sha256::digest(canonical(record)?);
    Ok(digest.iter().map(|b| format!("{b:02x}")).collect())
}
