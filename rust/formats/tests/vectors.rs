//! The shared vectors (vectors/formats/eddsa-jcs-2022.json), which the
//! Python code writes and checks: this crate must agree with them, byte
//! for byte, and with the W3C specification's own example.

use formats::canonical::{canonical, check};
use formats::multikey::{public_multikey, secret_from_multikey};
use formats::proof::{sign, verify};
use serde_json::Value;
use sha2::{Digest, Sha256};

fn vectors() -> Result<Value, String> {
    let path = concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../vectors/formats/eddsa-jcs-2022.json"
    );
    let text = std::fs::read_to_string(path).map_err(|e| e.to_string())?;
    serde_json::from_str(&text).map_err(|e| e.to_string())
}

fn text<'a>(v: &'a Value, key: &str) -> Result<&'a str, String> {
    v.get(key)
        .and_then(Value::as_str)
        .ok_or(format!("no text at {key}"))
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

#[test]
fn the_w3c_example_step_by_step() -> Result<(), String> {
    let all = vectors()?;
    let w3c = all.get("w3c").ok_or("no w3c")?;
    let document = w3c.get("document").ok_or("no document")?;
    let form = canonical(document)?;
    assert_eq!(
        String::from_utf8(form.clone()).map_err(|e| e.to_string())?,
        text(w3c, "canonicalDocument")?
    );
    assert_eq!(hex(&Sha256::digest(&form)), text(w3c, "documentHash")?);
    let options: Value =
        serde_json::from_str(text(w3c, "canonicalOptions")?).map_err(|e| e.to_string())?;
    assert_eq!(
        hex(&Sha256::digest(canonical(&options)?)),
        text(w3c, "optionsHash")?
    );

    let secret = secret_from_multikey(text(w3c, "secretKeyMultibase")?)?;
    let signed = sign(document, &secret, text(w3c, "created")?, "assertionMethod")?;
    let value = signed
        .pointer("/proof/proofValue")
        .and_then(Value::as_str)
        .ok_or("no proofValue")?;
    assert_eq!(value, text(w3c, "proofValue")?);
    let raw = bs58::decode(value.trim_start_matches('z'))
        .into_vec()
        .map_err(|e| e.to_string())?;
    assert_eq!(hex(&raw), text(w3c, "signature")?);

    let (unsecured, public) = verify(&signed)?;
    assert_eq!(&unsecured, document);
    assert_eq!(public_multikey(&public), text(w3c, "publicKeyMultibase")?);
    Ok(())
}

#[test]
fn our_records_sign_and_verify_as_python_wrote_them() -> Result<(), String> {
    let all = vectors()?;
    let cases = all
        .get("signed")
        .and_then(Value::as_array)
        .ok_or("no signed")?;
    assert!(!cases.is_empty());
    for case in cases {
        let name = text(case, "name")?;
        let document = case.get("document").ok_or("no document")?;
        let form = String::from_utf8(canonical(document)?).map_err(|e| e.to_string())?;
        assert_eq!(form, text(case, "canonicalDocument")?, "{name}");
        let secret = secret_from_multikey(text(case, "secretKeyMultibase")?)?;
        let signed = sign(document, &secret, text(case, "created")?, "assertionMethod")?;
        assert_eq!(Some(&signed), case.get("signed"), "{name}");
        let (unsecured, public) = verify(&signed)?;
        assert_eq!(&unsecured, document, "{name}");
        assert_eq!(
            public_multikey(&public),
            text(case, "publicKeyMultibase")?,
            "{name}"
        );
    }
    Ok(())
}

#[test]
fn each_refused_proof_is_refused() -> Result<(), String> {
    let all = vectors()?;
    let cases = all
        .get("refused")
        .and_then(Value::as_array)
        .ok_or("no refused")?;
    assert!(!cases.is_empty());
    for case in cases {
        let secured = case.get("secured").ok_or("no secured")?;
        assert!(
            verify(secured).is_err(),
            "not refused: {}",
            text(case, "name")?
        );
    }
    Ok(())
}

#[test]
fn an_at_context_that_isnt_a_list_is_not_signed() -> Result<(), String> {
    let all = vectors()?;
    let secret = secret_from_multikey(
        all.pointer("/signed/0/secretKeyMultibase")
            .and_then(Value::as_str)
            .ok_or("no key")?,
    )?;
    let record = serde_json::json!({"@context": "https://example.org"});
    assert!(sign(&record, &secret, "2026-11-14T00:00:00Z", "assertionMethod").is_err());
    Ok(())
}

#[test]
fn each_value_that_breaks_a_rule_is_refused() -> Result<(), String> {
    let all = vectors()?;
    let cases = all
        .get("refusedValues")
        .and_then(Value::as_array)
        .ok_or("no refusedValues")?;
    assert!(!cases.is_empty());
    for case in cases {
        let value: Value = serde_json::from_str(text(case, "json")?).map_err(|e| e.to_string())?;
        assert!(
            check(&value).is_some(),
            "not refused: {}",
            text(case, "name")?
        );
        assert!(canonical(&value).is_err());
    }
    Ok(())
}
