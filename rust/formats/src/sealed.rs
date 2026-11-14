//! Sealed records (course step 2): a signed record, sealed to the one it
//! names, as `formats/sealed.py` seals and opens them.
//!
//! A world-key is sealed to its holder under `open-worlds/world-key/v1`;
//! a journal entry to its author under `open-worlds/journal/v1`. Each
//! travels in an envelope (`open-worlds/sealed/v1`): the label, the one it
//! is addressed to, and the box in lowercase hex.
//!
//! Opening checks, in order: the envelope's shape, its label and address
//! against the opener's; that the box opens; that what is inside is a
//! record in its one RFC 8785 form, and holds; that it is a kind sealed
//! under that label, and names the opener. So a world-key sealed again to
//! someone else is refused by the one who opens it.

use serde_json::{Value, json};

use crate::canonical::canonical;
use crate::records::{check, def_problems, record_hash};
use crate::seal::{LABELS, open_box, seal};

/// The envelope's format.
pub const ENVELOPE: &str = "open-worlds/sealed/v1";

/// Each sealed kind, the label it is sealed under, and the field naming
/// the one it is sealed to.
pub const SEALED: [(&str, &str, &str); 2] = [
    (
        "open-worlds/world-key/v1",
        "open-worlds/world-key/v1",
        "holder",
    ),
    (
        "open-worlds/journal-entry/v1",
        "open-worlds/journal/v1",
        "author",
    ),
];

fn sealed_kind(format: &str) -> Option<&'static (&'static str, &'static str, &'static str)> {
    SEALED.iter().find(|(f, _, _)| *f == format)
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

fn unhex(text: &str) -> Result<Vec<u8>, String> {
    if !text.len().is_multiple_of(2) {
        return Err("hex in whole bytes".into());
    }
    (0..text.len())
        .step_by(2)
        .map(|i| {
            text.get(i..i + 2)
                .ok_or_else(|| "not hex".to_string())
                .and_then(|b| u8::from_str_radix(b, 16).map_err(|e| e.to_string()))
        })
        .collect()
}

/// Where `envelope` doesn't fit its schema, or an empty list.
pub fn envelope_problems(envelope: &Value) -> Result<Vec<String>, String> {
    if !envelope.is_object() {
        return Ok(vec!["$: not an envelope".into()]);
    }
    def_problems("sealed", envelope)
}

/// `record`, which must hold and be of a sealed kind, sealed to the one it
/// names, whose sealing key is `sealing_public`.
pub fn seal_record(record: &Value, sealing_public: &[u8; 32]) -> Result<Value, String> {
    check(record).map_err(|e| format!("only a record that holds is sealed: {e}"))?;
    let format = record
        .get("format")
        .and_then(Value::as_str)
        .ok_or("no format")?;
    let (_, label, field) =
        sealed_kind(format).ok_or_else(|| format!("{format} isn't a kind that is sealed"))?;
    let to = record.get(*field).ok_or("no recipient")?;
    let boxed = seal(&canonical(record)?, sealing_public, label)?;
    Ok(json!({"format": ENVELOPE, "label": label, "to": to, "box": hex(&boxed)}))
}

/// The record in `envelope`, if it holds, was sealed under `label` to
/// `opener` (a did:key) and names them.
pub fn open_record(
    envelope: &Value,
    sealing_secret: &[u8; 32],
    opener: &str,
    label: &str,
) -> Result<Value, String> {
    if !LABELS.contains(&label) {
        return Err(format!("{label:?} isn't a sealing label in use"));
    }
    let found = envelope_problems(envelope)?;
    if !found.is_empty() {
        return Err(found.join("; "));
    }
    if envelope.get("label").and_then(Value::as_str) != Some(label) {
        return Err("sealed for another purpose".into());
    }
    if envelope.get("to").and_then(Value::as_str) != Some(opener) {
        return Err("addressed to someone else".into());
    }
    let boxed = unhex(
        envelope
            .get("box")
            .and_then(Value::as_str)
            .ok_or("no box")?,
    )?;
    let inside = open_box(&boxed, sealing_secret, label)?;
    let record: Value =
        serde_json::from_slice(&inside).map_err(|_| "what is inside isn't a record")?;
    let same = canonical(&record).map_err(|_| "what is inside isn't a record")?;
    if same != inside {
        return Err("what is inside isn't in its one RFC 8785 form".into());
    }
    check(&record).map_err(|e| format!("what is inside doesn't hold: {e}"))?;
    let format = record
        .get("format")
        .and_then(Value::as_str)
        .ok_or("no format")?;
    let Some((_, _, field)) = sealed_kind(format).filter(|(_, l, _)| *l == label) else {
        return Err(format!("what is inside isn't a kind sealed under {label}"));
    };
    if record.get(*field).and_then(Value::as_str) != Some(opener) {
        return Err("what is inside names someone else".into());
    }
    Ok(record)
}

/// The hash of `envelope`'s RFC 8785 form: what may be made public of a
/// sealed record.
pub fn fingerprint(envelope: &Value) -> Result<String, String> {
    record_hash(envelope)
}
