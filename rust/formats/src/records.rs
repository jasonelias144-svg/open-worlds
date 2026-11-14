//! The records the offices keep (course step 2): a grant, a decision
//! record, a suggestion, a rating and a signed log head; an individual's
//! world-key and journal entry; identity, birth records and the mind
//! record; a world's template; and the project's key list, as
//! `formats/records.py` checks them, from the same schema file. A record
//! holds when it fits its kind's schema, its proof verifies, and it was
//! signed by the one who must sign that kind. `dial_problems` checks a
//! world's birth record against the template it names, and
//! `key_list_problems` a key list against the version before it.

use serde_json::{Value, json};
use sha2::{Digest, Sha256};

use crate::canonical::canonical;
use crate::multikey::public_multikey;
use crate::proof::{check_time, verify};

/// The schema, read at build time from `schemas/records-v1.schema.json`.
pub const SCHEMA: &str = include_str!("../../../schemas/records-v1.schema.json");

/// Each format, its schema's name in `$defs`, and the path of the field
/// that names its signer.
pub const KINDS: [(&str, &str, &[&str]); 13] = [
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
    ("open-worlds/template/v1", "template", &["issuer"]),
    ("open-worlds/key-list/v1", "keyList", &["issuer"]),
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
fn sealing_key_problem(place: &str, value: Option<&Value>) -> Vec<String> {
    let Some(text) = value.and_then(Value::as_str) else {
        return vec![format!("{place}: not a sealing key")];
    };
    match crate::multikey::sealing_from_multikey(text)
        .and_then(|key| crate::seal::check_public(&key))
    {
        Ok(()) => Vec::new(),
        Err(e) => vec![format!("{place}: {e}")],
    }
}

/// A sealing key must be one it is safe to seal to, and a key list must
/// name one root, each key once, and, in its first version, be signed by
/// that root; the schema checks only shapes.
fn key_problems(record: &Value) -> Vec<String> {
    match record.get("format").and_then(Value::as_str) {
        Some("open-worlds/identity/v1") => {
            sealing_key_problem("$.sealingKey", record.get("sealingKey"))
        }
        Some("open-worlds/key-list/v1") => key_list_entry_problems(record),
        _ => Vec::new(),
    }
}

fn key_list_entry_problems(record: &Value) -> Vec<String> {
    let entries: &[Value] = record
        .get("keys")
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .unwrap_or_default();
    let mut found = Vec::new();
    let roots: Vec<&Value> = entries
        .iter()
        .filter(|e| e.get("role").and_then(Value::as_str) == Some("root"))
        .collect();
    if let [root] = roots.as_slice() {
        if int(record, "version") == Some(1)
            && record.get("issuer").and_then(Value::as_str)
                != root.get("signing").and_then(Value::as_str)
        {
            found.push("$.issuer: the first version must be signed by its own root".into());
        }
    } else {
        found.push("$.keys: not exactly one root".into());
    }
    let mut seen = std::collections::BTreeSet::new();
    for (i, e) in entries.iter().enumerate() {
        let text = |k: &str| e.get(k).and_then(Value::as_str);
        if text("role") == Some("root") && e.get("sealing").is_some() {
            found.push(format!(
                "$.keys.{i}: the root signs key lists only, so nothing is sealed to it"
            ));
        }
        let named = [
            Some(format!("name {}", text("name").unwrap_or(""))),
            text("signing").map(|s| format!("key {s}")),
            text("sealing").map(|s| format!("key {s}")),
        ];
        for what in named.into_iter().flatten() {
            if !seen.insert(what) {
                found.push(format!("$.keys.{i}: a name or key named twice"));
            }
        }
        if e.get("sealing").is_some() {
            found.extend(sealing_key_problem(
                &format!("$.keys.{i}.sealing"),
                e.get("sealing"),
            ));
        }
    }
    found
}

fn int(value: &Value, key: &str) -> Option<i64> {
    value.get(key).and_then(Value::as_i64)
}

/// A template's dial must have room to turn, and its value must be within
/// its range; the schema checks only that min and max come together.
fn range_problems(record: &Value) -> Vec<String> {
    if record.get("format").and_then(Value::as_str) != Some("open-worlds/template/v1") {
        return Vec::new();
    }
    let Some(parameters) = record.get("parameters").and_then(Value::as_object) else {
        return Vec::new();
    };
    let mut names: Vec<&String> = parameters.keys().collect();
    names.sort();
    let mut found = Vec::new();
    for name in names {
        let p = &parameters[name];
        let (Some(min), Some(max), Some(value)) = (int(p, "min"), int(p, "max"), int(p, "value"))
        else {
            continue;
        };
        if min >= max {
            found.push(format!("$.parameters.{name}: min is not below max"));
        } else if !(min..=max).contains(&value) {
            found.push(format!("$.parameters.{name}: value is outside its range"));
        }
    }
    found
}

/// `record` without its proof, if it holds.
pub fn check(record: &Value) -> Result<Value, String> {
    let mut found = problems(record)?;
    if found.is_empty() {
        found.extend(time_problems(record));
        found.extend(key_problems(record));
        found.extend(range_problems(record));
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

/// The did:key of the root a key list names.
pub fn key_list_root(key_list: &Value) -> Option<&str> {
    key_list
        .get("keys")?
        .as_array()?
        .iter()
        .find(|e| e.get("role").and_then(Value::as_str) == Some("root"))?
        .get("signing")?
        .as_str()
}

/// The roles whose entries a key list only publishes: who an individual or
/// a world is follows its birth key and its own successions, never a later
/// key list (docs/research/KEYS.md, point 9).
pub const PUBLISHED_ONLY: [&str; 2] = ["individual", "world"];

fn key_list(record: &Value) -> Result<(), String> {
    check(record)?;
    if record.get("format").and_then(Value::as_str) != Some("open-worlds/key-list/v1") {
        return Err("$.format: not open-worlds/key-list/v1".into());
    }
    Ok(())
}

fn key_entries(key_list: &Value) -> &[Value] {
    key_list
        .get("keys")
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .unwrap_or_default()
}

fn role_and_name(entry: &Value) -> (Option<&str>, Option<&str>) {
    (
        entry.get("role").and_then(Value::as_str),
        entry.get("name").and_then(Value::as_str),
    )
}

/// Where a key list fails to follow the version before it, or an empty
/// list: it must name that version by hash, be the next number, be signed
/// by that version's root, be no earlier, and keep every individual's and
/// world's entry as it was. Both lists must hold.
pub fn key_list_problems(new: &Value, previous: &Value) -> Result<Vec<String>, String> {
    for record in [new, previous] {
        key_list(record)?;
    }
    let mut found = Vec::new();
    if new.get("previous").and_then(Value::as_str) != Some(record_hash(previous)?.as_str()) {
        found.push("$.previous: names another version".into());
    }
    let next = int(previous, "version").and_then(|v| v.checked_add(1));
    if int(new, "version") != next {
        found.push("$.version: not the next version".into());
    }
    if new.get("issuer").and_then(Value::as_str) != key_list_root(previous) {
        found.push("$.issuer: not the root of the version before".into());
    }
    let time = |r: &Value| {
        r.get("time")
            .and_then(Value::as_str)
            .unwrap_or("")
            .to_owned()
    };
    if time(new) < time(previous) {
        found.push("$.time: earlier than the version before".into());
    }
    found.extend(published_entries_problems(new, previous)?);
    Ok(found)
}

/// Where a key list fails to keep every individual's and world's entry of
/// an older one as it was, or an empty list: the kind of each entry is the
/// older list's. Part of `key_list_problems`; on its own, it checks a new
/// history, begun after a lost root, against the last version of the old
/// one (docs/research/KEYS.md, "Honest limits").
pub fn published_entries_problems(new: &Value, older: &Value) -> Result<Vec<String>, String> {
    for record in [new, older] {
        key_list(record)?;
    }
    let mut found = Vec::new();
    for e in key_entries(older) {
        let (role, name) = role_and_name(e);
        if !role.is_some_and(|r| PUBLISHED_ONLY.contains(&r)) {
            continue;
        }
        let kept = key_entries(new)
            .iter()
            .find(|n| role_and_name(n) == (role, name));
        if kept != Some(e) {
            found.push(format!(
                "$.keys: {}'s entry changed or dropped",
                name.unwrap_or("")
            ));
        }
    }
    Ok(found)
}

/// Where a key list's history fails, or an empty list: from version 1,
/// each version following the one before, and ending on a version whose
/// root has signed it, since a version naming a new root is published
/// together with the version that root signs (docs/research/KEYS.md).
/// Each problem names the version's place in `versions`.
pub fn key_list_chain_problems(versions: &[Value]) -> Vec<String> {
    let Some(last) = versions.last() else {
        return vec!["[]: no versions".into()];
    };
    let found: Vec<String> = versions
        .iter()
        .enumerate()
        .filter_map(|(i, r)| key_list(r).err().map(|e| format!("[{i}] {e}")))
        .collect();
    if !found.is_empty() {
        return found;
    }
    let mut found = Vec::new();
    if versions.first().and_then(|v| int(v, "version")) != Some(1) {
        found.push("[0] $.version: the history doesn't start at 1".into());
    }
    for (i, pair) in versions.windows(2).enumerate() {
        let [previous, new] = pair else { continue };
        let at = i + 1;
        match key_list_problems(new, previous) {
            Ok(problems) => found.extend(problems.into_iter().map(|p| format!("[{at}] {p}"))),
            Err(e) => found.push(format!("[{at}] {e}")),
        }
    }
    if key_list_root(last) != last.get("issuer").and_then(Value::as_str) {
        found.push(format!(
            "[{}] $.keys: names a new root that hasn't signed a version yet",
            versions.len() - 1
        ));
    }
    found
}

/// Where a world's birth record and the template it names disagree, or an
/// empty list: it must name that template by hash, and each dial it set
/// must be one of the template's dials, within its range, and changed
/// from the template's own value. Both records must hold.
pub fn dial_problems(world_birth: &Value, template: &Value) -> Result<Vec<String>, String> {
    for (record, kind) in [
        (world_birth, "open-worlds/world-birth/v1"),
        (template, "open-worlds/template/v1"),
    ] {
        check(record)?;
        if record.get("format").and_then(Value::as_str) != Some(kind) {
            return Err(format!("$.format: not {kind}"));
        }
    }
    let Some(named) = world_birth.get("template").and_then(Value::as_str) else {
        return Ok(vec!["$.template: names no template".into()]);
    };
    if named != record_hash(template)? {
        return Ok(vec!["$.template: names another template".into()]);
    }
    let parameters = template
        .get("parameters")
        .and_then(Value::as_object)
        .ok_or("no parameters")?;
    let mut dials: Vec<(&String, &Value)> = world_birth
        .get("dials")
        .and_then(Value::as_object)
        .map(|d| d.iter().collect())
        .unwrap_or_default();
    dials.sort_by(|a, b| a.0.cmp(b.0));
    let mut found = Vec::new();
    for (name, value) in dials {
        let value = value.as_i64().ok_or("a dial that isn't an integer")?;
        let Some(p) = parameters.get(name) else {
            found.push(format!("$.dials.{name}: not a parameter of the template"));
            continue;
        };
        let (Some(min), Some(max)) = (int(p, "min"), int(p, "max")) else {
            found.push(format!("$.dials.{name}: fixed in the template, not a dial"));
            continue;
        };
        if !(min..=max).contains(&value) {
            found.push(format!("$.dials.{name}: outside the dial's range"));
        } else if Some(value) == int(p, "value") {
            found.push(format!("$.dials.{name}: set to the template's own value"));
        }
    }
    Ok(found)
}
