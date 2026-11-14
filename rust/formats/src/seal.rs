//! Sealing: a message that only one key can open, with HPKE (RFC 9180), as
//! `formats/seal.py` does it.
//!
//! - **The suite:** base mode, with DHKEM(X25519, HKDF-SHA256),
//!   HKDF-SHA256 and ChaCha20Poly1305, from the `hpke` crate.
//! - **A box** is `enc || ct`, with no associated data.
//! - **HPKE's `info`** is a label from [`LABELS`]. The one opening a box
//!   names the label it expects, and a label not on the list is refused
//!   before anything is tried.
//! - **A sealing key** is refused if it isn't in its one canonical form,
//!   or is of small order ([`check_public`]).
//!
//! What is sealed is signed first and names its recipient; that is checked
//! with each sealed record's own format, not here.

use std::cmp::Ordering;

use hpke::aead::ChaCha20Poly1305;
use hpke::kdf::HkdfSha256;
use hpke::kem::X25519HkdfSha256;
use hpke::rand_core::CryptoRng;
use hpke::{Deserializable, Kem, OpModeR, OpModeS, Serializable};

/// Every label in use; a new one is added by a reviewed change.
pub const LABELS: [&str; 1] = ["open-worlds/world-key/v1"];
/// The length of `enc`, an X25519 public key (RFC 9180, 7.1, Nenc).
pub const ENC_LENGTH: usize = 32;
/// The length of ChaCha20Poly1305's tag (RFC 9180, 7.3, Nt).
pub const TAG_LENGTH: usize = 16;

/// 2^255 - 19, little-endian.
const P: [u8; 32] = [
    0xed, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0x7f,
];
/// Any secret will do (formats/seal.py uses the same one): once clamped it
/// is a multiple of 8, so only a key of small order takes it to zero.
const PROBE: [u8; 32] = [0x01; 32];

type PublicKey = <X25519HkdfSha256 as Kem>::PublicKey;
type SecretKey = <X25519HkdfSha256 as Kem>::PrivateKey;
type EncappedKey = <X25519HkdfSha256 as Kem>::EncappedKey;

fn info(label: &str) -> Result<&[u8], String> {
    if LABELS.contains(&label) {
        Ok(label.as_bytes())
    } else {
        Err(format!("{label:?} isn't a sealing label in use"))
    }
}

/// Refuse a sealing key that isn't safe to seal to: one that is, as a
/// number, 2^255 - 19 or more (another spelling of a smaller key; a key
/// with the top bit set is one), or one of small order, which would give a
/// secret anyone can work out.
pub fn check_public(public: &[u8; 32]) -> Result<(), String> {
    if public.iter().rev().cmp(P.iter().rev()) != Ordering::Less {
        return Err("a sealing key is below 2^255 - 19".into());
    }
    if x25519_dalek::x25519(PROBE, *public) == [0u8; 32] {
        return Err("a sealing key of small order".into());
    }
    Ok(())
}

/// The X25519 public key of a secret key.
pub fn public_from_secret(secret: &[u8; 32]) -> [u8; 32] {
    x25519_dalek::x25519(*secret, x25519_dalek::X25519_BASEPOINT_BYTES)
}

fn public_key(public: &[u8; 32]) -> Result<PublicKey, String> {
    check_public(public)?;
    PublicKey::from_bytes(public).map_err(|e| e.to_string())
}

fn join(enc: &EncappedKey, ciphertext: Vec<u8>) -> Vec<u8> {
    let mut boxed = enc.to_bytes().to_vec();
    boxed.extend(ciphertext);
    boxed
}

/// Seal `message` to `public` for the purpose `label` names, with fresh
/// randomness from the operating system. Each call gives a different box.
pub fn seal(message: &[u8], public: &[u8; 32], label: &str) -> Result<Vec<u8>, String> {
    let info = info(label)?;
    let key = public_key(public)?;
    let (enc, ciphertext) =
        hpke::single_shot_seal::<ChaCha20Poly1305, HkdfSha256, X25519HkdfSha256>(
            &OpModeS::Base,
            &key,
            info,
            message,
            b"",
        )
        .map_err(|e| e.to_string())?;
    Ok(join(&enc, ciphertext))
}

/// [`seal`], with randomness from `rng`, which must be a secure generator.
/// Tests pass a fixed one, to reproduce RFC 9180's vectors and the shared
/// ones.
pub fn seal_with_rng(
    message: &[u8],
    public: &[u8; 32],
    label: &str,
    rng: &mut impl CryptoRng,
) -> Result<Vec<u8>, String> {
    let info = info(label)?;
    let key = public_key(public)?;
    let (enc, ciphertext) = hpke::single_shot_seal_with_rng::<
        ChaCha20Poly1305,
        HkdfSha256,
        X25519HkdfSha256,
    >(&OpModeS::Base, &key, info, message, b"", rng)
    .map_err(|e| e.to_string())?;
    Ok(join(&enc, ciphertext))
}

/// The message in `boxed`, if it was sealed to `secret`'s key with exactly
/// `label`. The error never says why: a wrong key, a wrong label and a
/// changed box all look the same.
pub fn open_box(boxed: &[u8], secret: &[u8; 32], label: &str) -> Result<Vec<u8>, String> {
    let info = info(label)?;
    if boxed.len() < ENC_LENGTH + TAG_LENGTH {
        return Err("too short to be a box".into());
    }
    let (enc, ciphertext) = boxed.split_at(ENC_LENGTH);
    let enc = EncappedKey::from_bytes(enc).map_err(|e| e.to_string())?;
    let key = SecretKey::from_bytes(secret).map_err(|e| e.to_string())?;
    hpke::single_shot_open::<ChaCha20Poly1305, HkdfSha256, X25519HkdfSha256>(
        &OpModeR::Base,
        &key,
        &enc,
        info,
        ciphertext,
        b"",
    )
    .map_err(|_| "the box doesn't open".to_string())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_suite_is_the_one_decided() {
        // RFC 9180, 7.1 to 7.3: KEM 0x0020, KDF 0x0001, AEAD 0x0003.
        assert_eq!(X25519HkdfSha256::KEM_ID, 0x0020);
        assert_eq!(<HkdfSha256 as hpke::kdf::Kdf>::KDF_ID, 0x0001);
        assert_eq!(<ChaCha20Poly1305 as hpke::aead::Aead>::AEAD_ID, 0x0003);
    }
}
