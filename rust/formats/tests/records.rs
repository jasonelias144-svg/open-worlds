//! The shared record vectors (vectors/formats/records-v1.json), which the
//! Python code writes and checks: every record that holds holds here too,
//! with the same hash and the same signature, and every refused one is
//! refused.

use formats::multikey::secret_from_multikey;
use formats::proof::sign;
use formats::records::{
    check, dial_problems, key_list_chain_problems, key_list_problems, published_entries_problems,
    record_hash,
};
use serde_json::Value;

fn vectors() -> Result<Value, String> {
    let path = concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../vectors/formats/records-v1.json"
    );
    let text = std::fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}

#[test]
fn each_valid_record_holds_with_its_hash_and_signature() -> Result<(), String> {
    let all = vectors()?;
    let created = all
        .get("created")
        .and_then(Value::as_str)
        .ok_or("no created")?;
    let cases = all
        .get("valid")
        .and_then(Value::as_array)
        .ok_or("no valid")?;
    assert!(!cases.is_empty());
    for case in cases {
        let name = case.get("name").and_then(Value::as_str).ok_or("no name")?;
        let record = case.get("record").ok_or("no record")?;
        let unsecured = check(record).map_err(|e| format!("{name}: {e}"))?;
        assert_eq!(
            Some(record_hash(record)?.as_str()),
            case.get("hash").and_then(Value::as_str),
            "{name}"
        );
        let signer = case
            .get("signer")
            .and_then(Value::as_str)
            .ok_or("no signer")?;
        let secret = all
            .pointer(&format!("/parties/{signer}/secretKeyMultibase"))
            .and_then(Value::as_str)
            .ok_or("no party")?;
        let again = sign(
            &unsecured,
            &secret_from_multikey(secret)?,
            created,
            "assertionMethod",
        )?;
        assert_eq!(&again, record, "{name}");
    }
    Ok(())
}

#[test]
fn each_refused_record_is_refused() -> Result<(), String> {
    let all = vectors()?;
    let cases = all
        .get("refused")
        .and_then(Value::as_array)
        .ok_or("no refused")?;
    assert!(!cases.is_empty());
    for case in cases {
        let name = case.get("name").and_then(Value::as_str).ok_or("no name")?;
        let record = case.get("record").ok_or("no record")?;
        assert!(check(record).is_err(), "not refused: {name}");
    }
    Ok(())
}

#[test]
fn each_world_agrees_or_disagrees_with_its_template_as_stated() -> Result<(), String> {
    let all = vectors()?;
    let valid = all
        .get("valid")
        .and_then(Value::as_array)
        .ok_or("no valid")?;
    let cases = all
        .get("dials")
        .and_then(Value::as_array)
        .ok_or("no dials")?;
    assert!(!cases.is_empty());
    for case in cases {
        let name = case.get("name").and_then(Value::as_str).ok_or("no name")?;
        let template_name = case.get("template").and_then(Value::as_str);
        let template = valid
            .iter()
            .find(|v| v.get("name").and_then(Value::as_str) == template_name)
            .and_then(|v| v.get("record"))
            .ok_or("no template")?;
        let world_birth = case.get("worldBirth").ok_or("no world birth")?;
        let holds = case
            .get("holds")
            .and_then(Value::as_bool)
            .ok_or("no holds")?;
        let found = dial_problems(world_birth, template).map_err(|e| format!("{name}: {e}"))?;
        assert_eq!(found.is_empty(), holds, "{name}: {found:?}");
    }
    Ok(())
}

#[test]
fn each_key_list_follows_the_one_before_or_not_as_stated() -> Result<(), String> {
    let all = vectors()?;
    let valid = all
        .get("valid")
        .and_then(Value::as_array)
        .ok_or("no valid")?;
    let cases = all
        .get("keyListChains")
        .and_then(Value::as_array)
        .ok_or("no keyListChains")?;
    assert!(!cases.is_empty());
    for case in cases {
        let name = case.get("name").and_then(Value::as_str).ok_or("no name")?;
        let previous_name = case.get("previous").and_then(Value::as_str);
        let previous = valid
            .iter()
            .find(|v| v.get("name").and_then(Value::as_str) == previous_name)
            .and_then(|v| v.get("record"))
            .ok_or("no previous")?;
        let key_list = case.get("keyList").ok_or("no key list")?;
        let holds = case
            .get("holds")
            .and_then(Value::as_bool)
            .ok_or("no holds")?;
        let found = key_list_problems(key_list, previous).map_err(|e| format!("{name}: {e}"))?;
        assert_eq!(found.is_empty(), holds, "{name}: {found:?}");
    }
    Ok(())
}

#[test]
fn each_history_of_the_key_list_holds_or_not_as_stated() -> Result<(), String> {
    let all = vectors()?;
    let valid = all
        .get("valid")
        .and_then(Value::as_array)
        .ok_or("no valid")?;
    let cases = all
        .get("keyListHistories")
        .and_then(Value::as_array)
        .ok_or("no keyListHistories")?;
    assert!(!cases.is_empty());
    for case in cases {
        let name = case.get("name").and_then(Value::as_str).ok_or("no name")?;
        let mut versions = Vec::new();
        for version in case
            .get("versions")
            .and_then(Value::as_array)
            .ok_or("no versions")?
        {
            let record = valid
                .iter()
                .find(|v| v.get("name") == Some(version))
                .and_then(|v| v.get("record"))
                .ok_or("no such version")?;
            versions.push(record.clone());
        }
        let holds = case
            .get("holds")
            .and_then(Value::as_bool)
            .ok_or("no holds")?;
        let found = key_list_chain_problems(&versions);
        assert_eq!(found.is_empty(), holds, "{name}: {found:?}");
    }
    Ok(())
}

#[test]
fn a_new_history_keeps_the_old_ones_individuals_and_worlds() -> Result<(), String> {
    let all = vectors()?;
    let valid = all
        .get("valid")
        .and_then(Value::as_array)
        .ok_or("no valid")?;
    let by = |name: &str| {
        valid
            .iter()
            .find(|v| v.get("name").and_then(Value::as_str) == Some(name))
            .and_then(|v| v.get("record"))
            .ok_or(format!("no {name}"))
    };
    let first = by("the first key list, signed by its root")?;
    let last = by("the key list after, signed by the new root")?;
    assert!(published_entries_problems(first, last)?.is_empty());
    let changed = all
        .get("keyListChains")
        .and_then(Value::as_array)
        .and_then(|cases| {
            cases.iter().find(|c| {
                c.get("name").and_then(Value::as_str) == Some("a version giving ALICE another key")
            })
        })
        .and_then(|c| c.get("keyList"))
        .ok_or("no changed key list")?;
    assert_eq!(
        published_entries_problems(changed, last)?,
        vec!["$.keys: ALICE's entry changed or dropped".to_string()]
    );
    Ok(())
}
