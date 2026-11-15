//! Shared W3C DataIntegrity verification.
//!
//! Used by both the HTTP verifier (`verify_garden`) and the
//! offline vector runner (`verify_proof_offline`). Contains no
//! HTTP, no state reconstruction — only the algorithm.

use ed25519_dalek::{Signature, Verifier, VerifyingKey};
use serde_json::Value;
use sha2::{Digest, Sha256};

pub const PROOF_TYPE: &str = "DataIntegrityProof";
pub const PROOF_CRYPTOSUITE: &str = "eddsa-jcs-2022";
pub const PROOF_PURPOSE: &str = "assertionMethod";

pub fn check_proof_metadata(proof: &Value) -> Result<(), String> {
    let ptype = proof.get("type").and_then(|v| v.as_str())
        .ok_or("proof missing 'type'")?;
    if ptype != PROOF_TYPE {
        return Err(format!(
            "proof.type must be {PROOF_TYPE:?}, got {ptype:?}"));
    }
    let suite = proof.get("cryptosuite").and_then(|v| v.as_str())
        .ok_or("proof missing 'cryptosuite'")?;
    if suite != PROOF_CRYPTOSUITE {
        return Err(format!(
            "cryptosuite must be {PROOF_CRYPTOSUITE:?}, \
             got {suite:?}"));
    }
    let purpose = proof.get("proofPurpose")
        .and_then(|v| v.as_str())
        .ok_or("proof missing 'proofPurpose'")?;
    if purpose != PROOF_PURPOSE {
        return Err(format!(
            "proofPurpose must be {PROOF_PURPOSE:?}, \
             got {purpose:?}"));
    }
    let created = proof.get("created").and_then(|v| v.as_str())
        .ok_or("proof missing 'created'")?;
    if created.len() < 20 || !created.contains('T') {
        return Err(format!(
            "proof.created is not ISO 8601: {created:?}"));
    }
    Ok(())
}

pub fn verify_proof(
    body: &Value, proof: &Value, expected_did: &str,
) -> Result<(), String> {
    check_proof_metadata(proof)?;
    let proof_value = proof.get("proofValue")
        .and_then(|v| v.as_str())
        .ok_or("proof missing proofValue")?;
    let Some(b58) = proof_value.strip_prefix('z') else {
        return Err(format!(
            "proofValue must be base58btc, got {proof_value:?}"));
    };
    let sig_bytes = bs58::decode(b58).into_vec()
        .map_err(|e| format!("base58 proofValue: {e}"))?;
    if sig_bytes.len() != 64 {
        return Err(format!(
            "signature length {} != 64", sig_bytes.len()));
    }
    let signature = Signature::from_slice(&sig_bytes)
        .map_err(|_| "invalid signature bytes")?;

    let vm = proof.get("verificationMethod")
        .and_then(|v| v.as_str())
        .ok_or("proof missing verificationMethod")?;
    let did = vm.split('#').next().unwrap_or(vm);
    if did != expected_did {
        return Err(format!(
            "verificationMethod {did} != expected {expected_did}"));
    }

    let mut options = proof.as_object()
        .ok_or("proof is not an object")?.clone();
    options.remove("proofValue");
    let options_jcs = serde_jcs::to_vec(
        &Value::Object(options))
        .map_err(|e| format!("jcs options: {e}"))?;
    let body_jcs = serde_jcs::to_vec(body)
        .map_err(|e| format!("jcs body: {e}"))?;

    let mut payload = Vec::with_capacity(64);
    payload.extend_from_slice(&Sha256::digest(&options_jcs));
    payload.extend_from_slice(&Sha256::digest(&body_jcs));

    let vk = verifying_key_from_did(expected_did)?;
    vk.verify(&payload, &signature)
        .map_err(|_| "signature does not verify")
}

pub fn verifying_key_from_did(did: &str) -> Result<VerifyingKey, String> {
    let Some(multikey) = did.strip_prefix("did:key:") else {
        return Err(format!("unsupported DID: {did}"));
    };
    let Some(b58) = multikey.strip_prefix('z') else {
        return Err("DID key must be base58btc".into());
    };
    let bytes = bs58::decode(b58).into_vec()
        .map_err(|e| format!("base58 DID: {e}"))?;
    if bytes.len() != 34 || bytes[0] != 0xed || bytes[1] != 0x01 {
        return Err("DID key is not an Ed25519 public key".into());
    }
    let mut key = [0u8; 32];
    key.copy_from_slice(&bytes[2..34]);
    VerifyingKey::from_bytes(&key)
        .map_err(|e| format!("ed25519 key: {e}"))
}
