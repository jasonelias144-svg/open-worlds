//! The records the offices keep (course step 2): a grant, a decision
//! record, a suggestion, a rating and a signed log head; an individual's
//! world-key and journal entry; and identity, birth records and the mind
//! record, as
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
pub const KINDS: [(&str, &str, &[&str]); 11] = [
    ("open-worlds/grant/v1", "grant", &["issuer"]),
    ("open-worlds/decision/v1", "decision", &["office", "key"]),
    ("open-worlds/suggestion/v1", "suggestion", &["author"]),
    ("open-worlds/rating/v1", "rating", &["author"]),
    ("open-worlds/log-head/v1", "logHead", &["world"]),
    ("open-worlds/world-key/v1", "worldKey", &["issuer"]),
    ("open-worlds/journal-entry/v1", "journalEntry", &["author"]),
    ("open-worlds/identity/v1", "identity", &["id"]),
    ("open-worlds/birth/v1", "birth", &["world"]),
    ("open-worlds/world-birth/v1", "worldBirth", &["world"]),
    ("open-worlds/mind/v1", "mind", &["issuer"]),
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

/// Each UTC time in `record`, with where it is.
fn times(record: &Value) -> Vec<(String, &Value)> {
    let format = record.get("format").and_then(Value::as_str);
    let field = |name: &str| record.get(name).map(|v| (format!("$.{name}"), v));
    match format {
        Some("open-worlds/grant/v1") => ["validFrom", "validUntil"]
            .iter()
            .filter_map(|name| field(name))
            .collect(),
        Some("open-worlds/birth/v1" | "open-worlds/world-birth/v1") => {
            field("time").into_iter().collect()
        }
        Some("open-worlds/mind/v1") => record
            .get("engines")
            .and_then(Value::as_array)
            .map(|engines| {
                engines
                    .iter()
                    .enumerate()
                    .filter_map(|(i, e)| e.get("from").map(|v| (format!("$.engines.{i}.from"), v)))
                    .collect()
            })
            .unwrap_or_default(),
        _ => Vec::new(),
    }
}

/// Every time must be a real one, a grant must end after it starts, and a
/// mind record's engines are in the order they began, each naming a file
/// once; the schema checks only their shape.
fn time_problems(record: &Value) -> Vec<String> {
    let mut found: Vec<String> = times(record)
        .into_iter()
        .filter(|(_, value)| check_time(Some(value)).is_err())
        .map(|(where_, _)| format!("{where_}: not a real UTC time"))
        .collect();
    if !found.is_empty() {
        return found;
    }
    match record.get("format").and_then(Value::as_str) {
        Some("open-worlds/grant/v1") => {
            let from = record.get("validFrom").and_then(Value::as_str);
            let until = record.get("validUntil").and_then(Value::as_str);
            if let (Some(from), Some(until)) = (from, until)
                && until <= from
            {
                found.push("$.validUntil: not after validFrom".into());
            }
        }
        Some("open-worlds/mind/v1") => {
            let began: Vec<Option<&str>> = record
                .get("engines")
                .and_then(Value::as_array)
                .map(|engines| {
                    engines
                        .iter()
                        .map(|e| e.get("from").and_then(Value::as_str))
                        .collect()
                })
                .unwrap_or_default();
            for (i, pair) in began.windows(2).enumerate() {
                if let [Some(before), Some(after)] = pair
                    && after <= before
                {
                    found.push(format!(
                        "$.engines.{}.from: not after the engine before",
                        i + 1
                    ));
                }
            }
            let engines = record
                .get("engines")
                .and_then(Value::as_array)
                .map(Vec::as_slice)
                .unwrap_or_default();
            for (i, engine) in engines.iter().enumerate() {
                let paths: Vec<&str> = engine
                    .get("files")
                    .and_then(Value::as_array)
                    .map(|files| {
                        files
                            .iter()
                            .filter_map(|f| f.get("path").and_then(Value::as_str))
                            .collect()
                    })
                    .unwrap_or_default();
                let unique: std::collections::BTreeSet<&str> = paths.iter().copied().collect();
                if unique.len() != paths.len() {
                    found.push(format!("$.engines.{i}.files: a path named twice"));
                }
            }
        }
        _ => {}
    }
    found
}

/// An identity's sealing key must be one it is safe to seal to
/// (`crate::seal::check_public`); the schema checks only its shape.
fn key_problems(record: &Value) -> Vec<String> {
    if record.get("format").and_then(Value::as_str) != Some("open-worlds/identity/v1") {
        return Vec::new();
    }
    let Some(text) = record.get("sealingKey").and_then(Value::as_str) else {
        return vec!["$.sealingKey: not a sealing key".into()];
    };
    match crate::multikey::sealing_from_multikey(text)
        .and_then(|key| crate::seal::check_public(&key))
    {
        Ok(()) => Vec::new(),
        Err(e) => vec![format!("$.sealingKey: {e}")],
    }
}

/// `record` without its proof, if it holds.
pub fn check(record: &Value) -> Result<Value, String> {
    let mut found = problems(record)?;
    if found.is_empty() {
        found.extend(time_problems(record));
        found.extend(key_problems(record));
    }
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
