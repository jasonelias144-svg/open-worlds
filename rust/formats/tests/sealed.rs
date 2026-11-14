//! The shared sealed-record vectors (vectors/formats/sealed-records-v1.json),
//! which the Python code writes: this crate must open what opens, to the
//! same record, and refuse what Python refuses.

use formats::multikey::sealing_secret_from_multikey;
use formats::records::{check, record_hash};
use formats::seal::{LABELS, open_box, public_from_secret};
use formats::sealed::{SEALED, envelope_problems, fingerprint, open_record, seal_record};
use serde_json::Value;

fn vectors() -> Result<Value, String> {
    let path = concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../vectors/formats/sealed-records-v1.json"
    );
    let text = std::fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}

fn text<'a>(v: &'a Value, key: &str) -> Result<&'a str, String> {
    v.get(key)
        .and_then(Value::as_str)
        .ok_or(format!("no text at {key}"))
}

fn list<'a>(v: &'a Value, key: &str) -> Result<&'a Vec<Value>, String> {
    v.get(key)
        .and_then(Value::as_array)
        .ok_or(format!("no list at {key}"))
}

fn party<'a>(all: &'a Value, name: &str) -> Result<&'a Value, String> {
    all.get("parties")
        .and_then(|p| p.get(name))
        .ok_or(format!("no party {name}"))
}

fn sealing_secret(all: &Value, name: &str) -> Result<[u8; 32], String> {
    sealing_secret_from_multikey(text(party(all, name)?, "sealingSecretMultibase")?)
}

fn unhex(text: &str) -> Result<Vec<u8>, String> {
    (0..text.len())
        .step_by(2)
        .map(|i| {
            text.get(i..i + 2)
                .ok_or("bad hex".to_string())
                .and_then(|b| u8::from_str_radix(b, 16).map_err(|e| e.to_string()))
        })
        .collect()
}

#[test]
fn the_envelope_schema_names_the_labels_in_use() -> Result<(), String> {
    let schema: Value =
        serde_json::from_str(formats::records::SCHEMA).map_err(|e| e.to_string())?;
    let labels: Vec<&str> = schema
        .pointer("/$defs/sealed/properties/label/enum")
        .and_then(Value::as_array)
        .ok_or("no label enum")?
        .iter()
        .filter_map(Value::as_str)
        .collect();
    assert_eq!(labels, LABELS.to_vec());
    // And every label in use is the label of a sealed kind.
    let mut sealed: Vec<&str> = SEALED.iter().map(|(_, label, _)| *label).collect();
    sealed.sort_unstable();
    assert_eq!(sealed, LABELS.to_vec());
    Ok(())
}

#[test]
fn records_hold_and_refused_records_are_refused() -> Result<(), String> {
    let all = vectors()?;
    for entry in list(&all, "records")? {
        let record = entry.get("record").ok_or("no record")?;
        check(record).map_err(|e| format!("{}: {e}", text(entry, "name").unwrap_or("?")))?;
        assert_eq!(record_hash(record)?, text(entry, "hash")?);
    }
    for entry in list(&all, "refusedRecords")? {
        let record = entry.get("record").ok_or("no record")?;
        assert!(check(record).is_err(), "{} held", text(entry, "name")?);
    }
    Ok(())
}

#[test]
fn what_opens_opens_to_the_same_record() -> Result<(), String> {
    let all = vectors()?;
    let mut opened = 0;
    for entry in list(&all, "opens")? {
        let opener = text(entry, "opener")?;
        let envelope = entry.get("envelope").ok_or("no envelope")?;
        let record = open_record(
            envelope,
            &sealing_secret(&all, opener)?,
            text(party(&all, opener)?, "id")?,
            text(entry, "label")?,
        )
        .map_err(|e| format!("{}: {e}", text(entry, "name").unwrap_or("?")))?;
        assert_eq!(record_hash(&record)?, text(entry, "record")?);
        assert_eq!(fingerprint(envelope)?, text(entry, "fingerprint")?);
        opened += 1;
    }
    assert_eq!(opened, 3);
    Ok(())
}

#[test]
fn what_must_be_refused_is() -> Result<(), String> {
    let all = vectors()?;
    for entry in list(&all, "refused")? {
        let name = text(entry, "name")?;
        let envelope = entry.get("envelope").ok_or("no envelope")?;
        // Each is what its name says: it opens, with the key and label
        // stated, to what is stated.
        let boxed = unhex(text(envelope, "box")?)?;
        let inside = open_box(
            &boxed,
            &sealing_secret(&all, text(entry, "sealedFor")?)?,
            text(entry, "sealedUnder")?,
        )?;
        assert_eq!(unhex(text(entry, "inside")?)?, inside, "{name}");
        // And the opener refuses it.
        let opener = text(entry, "opener")?;
        assert!(
            open_record(
                envelope,
                &sealing_secret(&all, opener)?,
                text(party(&all, opener)?, "id")?,
                text(entry, "label")?,
            )
            .is_err(),
            "{name} opened"
        );
    }
    for entry in list(&all, "refusedEnvelopes")? {
        let envelope = entry.get("envelope").ok_or("no envelope")?;
        assert!(
            !envelope_problems(envelope)?.is_empty(),
            "{}",
            text(entry, "name")?
        );
    }
    Ok(())
}

#[test]
fn sealing_round_trip() -> Result<(), String> {
    let all = vectors()?;
    let record = list(&all, "records")?
        .first()
        .and_then(|e| e.get("record"))
        .ok_or("no record")?;
    let secret = sealing_secret(&all, "ALICE")?;
    let envelope = seal_record(record, &public_from_secret(&secret))?;
    assert_eq!(text(&envelope, "to")?, text(party(&all, "ALICE")?, "id")?);
    let opened = open_record(
        &envelope,
        &secret,
        text(party(&all, "ALICE")?, "id")?,
        "open-worlds/world-key/v1",
    )?;
    assert_eq!(&opened, record);
    // A record that doesn't hold isn't sealed.
    let bad = list(&all, "refusedRecords")?
        .first()
        .and_then(|e| e.get("record"))
        .ok_or("no record")?;
    assert!(seal_record(bad, &public_from_secret(&secret)).is_err());
    Ok(())
}
