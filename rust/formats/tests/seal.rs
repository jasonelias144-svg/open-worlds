//! The shared sealing vectors (vectors/formats/hpke-base-v1.json), which
//! the Python code writes: this crate must open every box Python made,
//! refuse what must be refused, make its own boxes again byte for byte, and
//! reproduce RFC 9180's own example.

use std::convert::Infallible;

use formats::multikey::{sealing_from_multikey, sealing_multikey, sealing_secret_from_multikey};
use formats::seal::{LABELS, check_public, open_box, public_from_secret, seal, seal_with_rng};
use hpke::aead::ChaCha20Poly1305;
use hpke::kdf::HkdfSha256;
use hpke::kem::X25519HkdfSha256;
use hpke::rand_core::{TryCryptoRng, TryRng};
use hpke::{Deserializable, Kem, OpModeR, OpModeS, Serializable};
use serde_json::Value;

/// Gives the bytes it holds, in place of fresh randomness, and counts how
/// many were asked for. Only for reproducing known boxes.
struct Fixed {
    bytes: Vec<u8>,
    used: usize,
}

impl TryRng for Fixed {
    type Error = Infallible;
    fn try_next_u32(&mut self) -> Result<u32, Infallible> {
        let mut b = [0u8; 4];
        self.try_fill_bytes(&mut b)?;
        Ok(u32::from_le_bytes(b))
    }
    fn try_next_u64(&mut self) -> Result<u64, Infallible> {
        let mut b = [0u8; 8];
        self.try_fill_bytes(&mut b)?;
        Ok(u64::from_le_bytes(b))
    }
    fn try_fill_bytes(&mut self, dst: &mut [u8]) -> Result<(), Infallible> {
        for d in dst.iter_mut() {
            *d = self.bytes.get(self.used).copied().unwrap_or(0);
            self.used += 1;
        }
        Ok(())
    }
}

impl TryCryptoRng for Fixed {}

fn vectors() -> Result<Value, String> {
    let path = concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../vectors/formats/hpke-base-v1.json"
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

fn unhex(text: &str) -> Result<Vec<u8>, String> {
    if !text.len().is_multiple_of(2) {
        return Err("odd hex".into());
    }
    (0..text.len())
        .step_by(2)
        .map(|i| {
            text.get(i..i + 2)
                .ok_or("bad hex".to_string())
                .and_then(|b| u8::from_str_radix(b, 16).map_err(|e| e.to_string()))
        })
        .collect()
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

fn key32(bytes: &[u8]) -> Result<[u8; 32], String> {
    bytes.try_into().map_err(|_| "not 32 bytes".to_string())
}

fn secret_of(all: &Value, name: &str) -> Result<[u8; 32], String> {
    let who = all
        .get("recipients")
        .and_then(|r| r.get(name))
        .ok_or(format!("no recipient {name}"))?;
    sealing_secret_from_multikey(text(who, "secretKeyMultibase")?)
}

#[test]
fn rfc_9180_example_is_reproduced() -> Result<(), String> {
    let all = vectors()?;
    let rfc = all.get("rfc9180").ok_or("no rfc9180")?;
    let sk = key32(&unhex(text(rfc, "skRm")?)?)?;
    let pk = key32(&unhex(text(rfc, "pkRm")?)?)?;
    assert_eq!(public_from_secret(&sk), pk);

    let info = unhex(text(rfc, "info")?)?;
    let pt = unhex(text(rfc, "pt")?)?;
    let aad = unhex(text(rfc, "aad")?)?;
    let mut rng = Fixed {
        bytes: unhex(text(rfc, "ikmE")?)?,
        used: 0,
    };
    let recipient =
        <X25519HkdfSha256 as Kem>::PublicKey::from_bytes(&pk).map_err(|e| e.to_string())?;
    let (enc, ct) =
        hpke::single_shot_seal_with_rng::<ChaCha20Poly1305, HkdfSha256, X25519HkdfSha256>(
            &OpModeS::Base,
            &recipient,
            &info,
            &pt,
            &aad,
            &mut rng,
        )
        .map_err(|e| e.to_string())?;
    assert_eq!(rng.used, 32, "ikmE is the only randomness used");
    assert_eq!(hex(&enc.to_bytes()), text(rfc, "enc")?);
    assert_eq!(hex(&ct), text(rfc, "ct")?);

    let secret =
        <X25519HkdfSha256 as Kem>::PrivateKey::from_bytes(&sk).map_err(|e| e.to_string())?;
    let opened = hpke::single_shot_open::<ChaCha20Poly1305, HkdfSha256, X25519HkdfSha256>(
        &OpModeR::Base,
        &secret,
        &enc,
        &info,
        &ct,
        &aad,
    )
    .map_err(|e| e.to_string())?;
    assert_eq!(opened, pt);
    Ok(())
}

#[test]
fn recipients_match_their_keys() -> Result<(), String> {
    let all = vectors()?;
    let recipients = all
        .get("recipients")
        .and_then(Value::as_object)
        .ok_or("no recipients")?;
    for (name, who) in recipients {
        let secret = sealing_secret_from_multikey(text(who, "secretKeyMultibase")?)?;
        let public = sealing_from_multikey(text(who, "publicKeyMultibase")?)?;
        assert_eq!(public_from_secret(&secret), public, "{name}");
        assert_eq!(sealing_multikey(&public), text(who, "publicKeyMultibase")?);
        check_public(&public)?;
    }
    Ok(())
}

#[test]
fn labels_are_the_same() -> Result<(), String> {
    let all = vectors()?;
    let labels: Vec<&str> = list(&all, "labels")?
        .iter()
        .filter_map(Value::as_str)
        .collect();
    assert_eq!(labels, LABELS.to_vec());
    Ok(())
}

#[test]
fn every_box_in_the_vectors_opens() -> Result<(), String> {
    let all = vectors()?;
    let mut opened = 0;
    for entry in list(&all, "opens")? {
        let secret = secret_of(&all, text(entry, "to")?)?;
        let boxed = unhex(text(entry, "box")?)?;
        let message = open_box(&boxed, &secret, text(entry, "label")?)
            .map_err(|e| format!("{}: {e}", text(entry, "name").unwrap_or("?")))?;
        assert_eq!(hex(&message), text(entry, "message")?);
        opened += 1;
    }
    assert!(opened >= 5);
    Ok(())
}

#[test]
fn boxes_made_by_rust_are_made_again() -> Result<(), String> {
    let all = vectors()?;
    let mut made = 0;
    let mut wrong = Vec::new();
    for entry in list(&all, "opens")? {
        if text(entry, "madeBy")? != "rust" {
            continue;
        }
        let public = public_from_secret(&secret_of(&all, text(entry, "to")?)?);
        let mut rng = Fixed {
            bytes: unhex(text(entry, "ikmE")?)?,
            used: 0,
        };
        let boxed = seal_with_rng(
            &unhex(text(entry, "message")?)?,
            &public,
            text(entry, "label")?,
            &mut rng,
        )?;
        assert_eq!(rng.used, 32, "ikmE is the only randomness used");
        if hex(&boxed) != text(entry, "box")? {
            wrong.push(format!("{}: {}", text(entry, "name")?, hex(&boxed)));
        }
        made += 1;
    }
    assert!(made >= 2);
    // A box missing from the file is printed here, to be pasted in.
    assert!(wrong.is_empty(), "not as recorded:\n{}", wrong.join("\n"));
    Ok(())
}

#[test]
fn what_must_be_refused_is() -> Result<(), String> {
    let all = vectors()?;
    for entry in list(&all, "refused")? {
        let secret = secret_of(&all, text(entry, "to")?)?;
        let boxed = unhex(text(entry, "box")?)?;
        assert!(
            open_box(&boxed, &secret, text(entry, "label")?).is_err(),
            "{} opened",
            text(entry, "name")?
        );
    }
    let first = list(&all, "opens")?.first().ok_or("no boxes")?;
    let boxed = unhex(text(first, "box")?)?;
    let secret = secret_of(&all, text(first, "to")?)?;
    let public = public_from_secret(&secret);
    for label in list(&all, "refusedLabels")? {
        let label = label.as_str().ok_or("a label is text")?;
        assert!(
            open_box(&boxed, &secret, label).is_err(),
            "{label:?} opened"
        );
        assert!(seal(b"x", &public, label).is_err(), "{label:?} sealed");
    }
    for entry in list(&all, "refusedKeys")? {
        let key = key32(&unhex(text(entry, "key")?)?)?;
        assert!(check_public(&key).is_err(), "{}", text(entry, "name")?);
        assert!(seal(b"x", &key, LABELS[0]).is_err());
    }
    for entry in list(&all, "refusedSealingMultikeys")? {
        assert!(sealing_from_multikey(text(entry, "multikey")?).is_err());
    }
    Ok(())
}

#[test]
fn sealing_round_trip_with_fresh_randomness() -> Result<(), String> {
    let all = vectors()?;
    let secret = secret_of(&all, "the earner")?;
    let public = public_from_secret(&secret);
    let one = seal(b"hello", &public, LABELS[0])?;
    let two = seal(b"hello", &public, LABELS[0])?;
    assert_ne!(one, two, "each box is new");
    assert_eq!(open_box(&one, &secret, LABELS[0])?, b"hello");
    assert_eq!(one.len(), 32 + 5 + 16);
    let other = secret_of(&all, "someone else")?;
    assert!(open_box(&one, &other, LABELS[0]).is_err());
    Ok(())
}
