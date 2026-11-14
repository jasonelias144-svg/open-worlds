//! Data Integrity proofs with the `eddsa-jcs-2022` cryptosuite (W3C
//! Recommendation, 15 May 2025, section 3.3), read as narrowly as
//! `formats/proof.py` reads them: one proof per record, did:key methods
//! only, `created` written `YYYY-MM-DDTHH:MM:SSZ`, and every value within
//! this project's rules.

use ed25519_dalek::{Signature, Signer, SigningKey, VerifyingKey};
use serde_json::{Map, Value};
use sha2::{Digest, Sha256};

use crate::canonical::canonical;
use crate::multikey::{public_from_verification_method, verification_method};

/// The proof's type.
pub const TYPE: &str = "DataIntegrityProof";
/// The cryptosuite.
pub const CRYPTOSUITE: &str = "eddsa-jcs-2022";

fn check_created(created: Option<&Value>) -> Result<(), String> {
    let text = created
        .and_then(Value::as_str)
        .ok_or("created must be text")?;
    let bytes = text.as_bytes();
    let shape_ok = bytes.len() == 20
        && bytes.iter().enumerate().all(|(i, b)| match i {
            4 | 7 => *b == b'-',
            10 => *b == b'T',
            13 | 16 => *b == b':',
            19 => *b == b'Z',
            _ => b.is_ascii_digit(),
        });
    if !shape_ok {
        return Err("created is written YYYY-MM-DDTHH:MM:SSZ".into());
    }
    let num = |a: usize, b: usize| -> u32 {
        text.get(a..b)
            .and_then(|s| s.parse().ok())
            .unwrap_or(u32::MAX)
    };
    let (year, month, day) = (num(0, 4), num(5, 7), num(8, 10));
    let (hour, minute, second) = (num(11, 13), num(14, 16), num(17, 19));
    let leap = (year % 4 == 0 && year % 100 != 0) || year % 400 == 0;
    let days = match month {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 if leap => 29,
        2 => 28,
        _ => 0,
    };
    if year < 1 || day < 1 || day > days || hour > 23 || minute > 59 || second > 59 {
        return Err("created is written YYYY-MM-DDTHH:MM:SSZ".into());
    }
    Ok(())
}

fn check_options(options: &Map<String, Value>) -> Result<(), String> {
    if options.get("type").and_then(Value::as_str) != Some(TYPE)
        || options.get("cryptosuite").and_then(Value::as_str) != Some(CRYPTOSUITE)
    {
        return Err(format!("not a {TYPE} with {CRYPTOSUITE}"));
    }
    check_created(options.get("created"))?;
    if !options.get("proofPurpose").is_some_and(Value::is_string) {
        return Err("proofPurpose must be text".into());
    }
    Ok(())
}

/// Section 3.3.4: SHA-256 of the options, then SHA-256 of the record, each
/// in RFC 8785 form.
fn hash_data(document: &Value, options: &Value) -> Result<Vec<u8>, String> {
    let mut data = Sha256::digest(canonical(options)?).to_vec();
    data.extend_from_slice(&Sha256::digest(canonical(document)?));
    Ok(data)
}

/// `document` with an `eddsa-jcs-2022` proof by the holder of `secret`,
/// made at `created`. Section 3.3.1.
pub fn sign(
    document: &Value,
    secret: &[u8; 32],
    created: &str,
    purpose: &str,
) -> Result<Value, String> {
    let doc = document.as_object().ok_or("sign a record (an object)")?;
    if doc.contains_key("proof") {
        return Err("sign a record with no proof yet".into());
    }
    let key = SigningKey::from_bytes(secret);
    let mut proof = Map::new();
    proof.insert("type".into(), TYPE.into());
    proof.insert("cryptosuite".into(), CRYPTOSUITE.into());
    proof.insert("created".into(), created.into());
    proof.insert(
        "verificationMethod".into(),
        verification_method(&key.verifying_key().to_bytes()).into(),
    );
    proof.insert("proofPurpose".into(), purpose.into());
    if let Some(context) = doc.get("@context") {
        if !context.is_array() {
            return Err("an @context is read only as a list".into());
        }
        proof.insert("@context".into(), context.clone());
    }
    check_options(&proof)?;
    let signature = key.sign(&hash_data(document, &Value::Object(proof.clone()))?);
    let value = format!("z{}", bs58::encode(signature.to_bytes()).into_string());
    proof.insert("proofValue".into(), value.into());
    let mut signed = doc.clone();
    signed.insert("proof".into(), Value::Object(proof));
    Ok(Value::Object(signed))
}

/// The record without its proof, and the public key that signed it, if
/// the proof holds. Section 3.3.2.
pub fn verify(secured: &Value) -> Result<(Value, [u8; 32]), String> {
    let doc = secured
        .as_object()
        .ok_or("a record with one proof (an object) is read")?;
    let proof = doc
        .get("proof")
        .and_then(Value::as_object)
        .ok_or("a record with one proof (an object) is read")?;
    let mut unsecured = doc.clone();
    unsecured.remove("proof");
    let mut options = proof.clone();
    options.remove("proofValue");
    let value = proof
        .get("proofValue")
        .and_then(Value::as_str)
        .and_then(|v| v.strip_prefix('z'))
        .ok_or("proofValue must be base58-btc, starting with z")?;
    let raw = bs58::decode(value).into_vec().map_err(|e| e.to_string())?;
    let bytes: [u8; 64] = raw
        .try_into()
        .map_err(|_| "proofValue isn't one 64-byte signature")?;
    if bs58::encode(bytes).into_string() != value {
        return Err("proofValue isn't one 64-byte signature".into());
    }
    if let Some(context) = options.get("@context") {
        let wanted = context.as_array();
        let held = doc.get("@context").and_then(Value::as_array);
        match (wanted, held) {
            (Some(w), Some(h)) if h.starts_with(w) => {}
            _ => return Err("the record's @context doesn't start with the proof's".into()),
        }
        unsecured.insert("@context".into(), context.clone());
    }
    check_options(&options)?;
    let method = options
        .get("verificationMethod")
        .and_then(Value::as_str)
        .ok_or("only did:key verification methods are read")?;
    let public = public_from_verification_method(method)?;
    let key = VerifyingKey::from_bytes(&public).map_err(|e| e.to_string())?;
    let unsecured = Value::Object(unsecured);
    let data = hash_data(&unsecured, &Value::Object(options))?;
    key.verify_strict(&data, &Signature::from_bytes(&bytes))
        .map_err(|_| "the signature doesn't hold".to_string())?;
    Ok((unsecured, public))
}
