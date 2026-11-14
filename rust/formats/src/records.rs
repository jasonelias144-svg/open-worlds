//! The records the offices keep (course step 2): a grant, a decision
//! record, a suggestion, a rating and a signed log head, as
//! `formats/records.py` checks them, from the same schema file. A record
//! holds when it fits its kind's schema, its proof verifies, and it was
//! signed by the one who must sign that kind.

use serde_json::{Value, json};
use sha2::{Digest, Sha256};

use crate::canonical::canonical;
use crate::multikey::public_multikey;
use crate::proof::verify;

/// The schema, read at build time from `schemas/records-v1.schema.json`.
pub const SCHEMA: &str = include_str!("../../../schemas/records-v1.schema.json");

/// Each format, its schema's name in `$defs`, and the path of the field
/// that names its signer.
pub const KINDS: [(&str, &str, &[&str]); 5] = [
    ("open-worlds/grant/v1", "grant", &["issuer"]),
    ("open-worlds/decision/v1", "decision", &["office", "key"]),
    ("open-worlds/suggestion/v1", "suggestion", &["author"]),
    ("open-worlds/rating/v1", "rating", &["author"]),
    ("open-worlds/log-head/v1", "logHead", &["world"]),
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
    let schema: Value = serde_json::from_str(SCHEMA).map_err(|e| e.to_string())?;
    let defs = schema.get("$defs").ok_or("the schema has no $defs")?;
    let one = json!({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$defs": defs,
        "$ref": format!("#/$defs/{name}"),
    });
    let validator = jsonschema::draft202012::new(&one).map_err(|e| e.to_string())?;
    Ok(validator
        .iter_errors(record)
        .map(|e| format!("{}: {}", e.instance_path(), e))
        .collect())
}

/// `record` without its proof, if it holds.
pub fn check(record: &Value) -> Result<Value, String> {
    let found = problems(record)?;
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
