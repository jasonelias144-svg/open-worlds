//! verify_garden.rs — external verification without arc-internal
//! code.
//!
//! Verifies a garden's signed log against its manifest, using
//! only:
//!   - `serde_jcs`        for RFC 8785 canonical JSON
//!   - `sha2`             for SHA-256
//!   - `ed25519-dalek`    for Ed25519 signature verification
//!   - `bs58`             for base58 decoding
//!
//! No import of `formats`, `world-log`, or `ur-world`. If this
//! verifier succeeds, then a garden's history is verifiable by
//! any Rust program with those crates — the standard, not the
//! arc's implementation of it, is what makes the log legible.
//!
//! Usage:
//!     cargo run --example verify_garden -- http://127.0.0.1:8765
//!
//! What it verifies:
//!   1. The manifest's proof verifies against its declared
//!      key, per eddsa-jcs-2022:
//!        payload = SHA256(JCS(proofOptions)) ||
//!                  SHA256(JCS(document))
//!   2. Every log entry's proof verifies the same way, against
//!      the actor's DID.
//!   3. Every entry's `hash` equals SHA-256(JCS(body)).
//!   4. The chain: entry[i].prev == entry[i-1].hash (or None
//!      for entry[0]).
//!   5. The current garden state (plants, agents, cycle) is
//!      reconstructible from the log alone.

use std::env;

use ed25519_dalek::{Signature, Verifier, VerifyingKey};
use serde_json::Value;
use sha2::{Digest, Sha256};

// ────────────────────────────────────────────────────────────
// Entry point
// ────────────────────────────────────────────────────────────

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: verify_garden <url>");
        std::process::exit(2);
    }
    let url = args[1].trim_end_matches('/').to_string();
    match verify(&url) {
        Ok(summary) => {
            println!("=== External verification: PASSED ===");
            print!("{summary}");
        }
        Err(e) => {
            println!("=== External verification: FAILED ===");
            println!("{e}");
            std::process::exit(1);
        }
    }
}

// ────────────────────────────────────────────────────────────
// The verification
// ────────────────────────────────────────────────────────────

fn verify(base: &str) -> Result<String, String> {
    // ── 1. Manifest ──────────────────────────────────────
    let manifest_json = fetch(&format!("{base}/manifest"))?;
    let manifest_body = manifest_json.get("manifest")
        .ok_or("manifest missing 'manifest' field")?;
    let manifest_proof = manifest_json.get("proof")
        .ok_or("manifest missing 'proof' field")?;
    let garden_did = proof_verification_method(manifest_proof)?;

    verify_proof(manifest_body, manifest_proof, &garden_did)
        .map_err(|e| format!("manifest proof: {e}"))?;
    println!("  ✓ manifest proof verifies against {garden_did}");

    // ── 2. Signed log ────────────────────────────────────
    let log_json = fetch(&format!("{base}/signed-log"))?;
    let entries = log_json.get("entries")
        .and_then(|v| v.as_array())
        .ok_or("signed-log missing 'entries'")?;
    println!("  ✓ fetched {} log entries", entries.len());

    // ── 3. Per-entry and per-chain verification ──────────
    let mut prev_hash: Option<String> = None;
    let mut state = GardenState::default();
    for (i, entry) in entries.iter().enumerate() {
        let body = entry.get("body")
            .ok_or_else(|| format!("entry[{i}]: missing body"))?;
        let proof = entry.get("proof")
            .ok_or_else(|| format!("entry[{i}]: missing proof"))?;
        let actor = body.get("actor").and_then(|v| v.as_str())
            .ok_or_else(|| format!("entry[{i}]: missing actor"))?;

        verify_proof(body, proof, actor)
            .map_err(|e| format!("entry[{i}] proof: {e}"))?;

        // Hash = SHA-256(JCS(body))
        let jcs = serde_jcs::to_vec(body)
            .map_err(|e| format!("entry[{i}] jcs: {e}"))?;
        let computed = hex_sha256(&jcs);
        let stored = entry.get("hash").and_then(|v| v.as_str())
            .ok_or_else(|| format!("entry[{i}]: missing hash"))?;
        if computed != stored {
            return Err(format!(
                "entry[{i}]: hash mismatch \
                 (stored {stored}, computed {computed})"));
        }

        // Chain: entry.prev == prev_hash
        let stored_prev = entry.get("prev").and_then(|v| v.as_str());
        match (stored_prev, &prev_hash) {
            (None, None) => {} // genesis
            (Some(p), Some(prev)) if p == prev => {}
            (Some(p), Some(prev)) => {
                return Err(format!(
                    "entry[{i}]: prev mismatch \
                     (stored {p}, chain {prev})"));
            }
            (Some(p), None) => {
                return Err(format!(
                    "entry[{i}]: prev={p} but chain has no \
                     predecessor"));
            }
            (None, Some(_)) => {
                return Err(format!(
                    "entry[{i}]: prev is null but chain has \
                     predecessors"));
            }
            (Some(_), Some(_)) => unreachable!(),
        }

        // Apply to state (may fail on malformed kind-specific
        // fields — that's a verification failure, not a state
        // error).
        state.apply(body, i)?;
        prev_hash = Some(stored.to_string());
    }
    println!("  ✓ all {} entry proofs verify", entries.len());
    println!("  ✓ all {} chain links verify", entries.len());

    // ── 4. Report reconstructed state ────────────────────
    let mut plant_lines: Vec<String> = state.plants.iter()
        .map(|(id, pos)| format!("    {id}: [{}, {}, {}]",
            pos[0], pos[1], pos[2]))
        .collect();
    plant_lines.sort();
    let mut agent_lines: Vec<String> = state.agents.iter()
        .map(|(did, pos)| format!("    {}: [{}, {}, {}]",
            &did[..did.len().min(24)], pos[0], pos[1], pos[2]))
        .collect();
    agent_lines.sort();

    Ok(format!(
        "\n  Reconstructed from log:\n\
         \x20   cycle:  {}\n\
         \x20   plants: {} ({} plants)\n{}\
         \x20   agents: {} ({} agents)\n{}",
        state.cycle,
        state.plants.len(),
        state.plants.len(),
        plant_lines.into_iter()
            .map(|l| format!("{l}\n"))
            .collect::<String>(),
        state.agents.len(),
        state.agents.len(),
        agent_lines.into_iter()
            .map(|l| format!("{l}\n"))
            .collect::<String>(),
    ))
}

// ────────────────────────────────────────────────────────────
// HTTP
// ────────────────────────────────────────────────────────────

fn fetch(url: &str) -> Result<Value, String> {
    let resp = ureq::get(url).call()
        .map_err(|e| format!("GET {url}: {e}"))?;
    resp.into_json()
        .map_err(|e| format!("parse {url}: {e}"))
}

// ────────────────────────────────────────────────────────────
// W3C DataIntegrity — eddsa-jcs-2022
// ────────────────────────────────────────────────────────────
//
//   verifyProof(proof, document):
//     options = copy(proof) without proofValue
//     payload = SHA256(JCS(options)) || SHA256(JCS(document))
//     sig = base58_decode(proof.proofValue[1..])
//     verify(verifying_key_from_DID, sig, payload)
//
// That's the whole algorithm. This implementation follows the
// W3C spec directly.

fn verify_proof(
    body: &Value, proof: &Value, expected_did: &str,
) -> Result<(), String> {
    // 1. Extract proofValue — must be base58btc ("z...")
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

    // 2. Extract the verificationMethod and confirm it matches
    // the expected DID.
    let vm = proof_verification_method(proof)?;
    if vm != expected_did {
        return Err(format!(
            "verificationMethod {vm} != expected {expected_did}"));
    }

    // 3. Build the eddsa-jcs-2022 payload:
    //    SHA256(JCS(proofOptions)) || SHA256(JCS(document))
    let mut options_obj = proof.as_object()
        .ok_or("proof is not an object")?.clone();
    options_obj.remove("proofValue");
    let options_jcs = serde_jcs::to_vec(
        &Value::Object(options_obj))
        .map_err(|e| format!("jcs options: {e}"))?;
    let body_jcs = serde_jcs::to_vec(body)
        .map_err(|e| format!("jcs body: {e}"))?;

    let mut payload = Vec::with_capacity(64);
    payload.extend_from_slice(&Sha256::digest(&options_jcs));
    payload.extend_from_slice(&Sha256::digest(&body_jcs));

    // 4. Resolve the Ed25519 key from the DID and verify.
    let vk = verifying_key_from_did(expected_did)?;
    vk.verify(&payload, &signature)
        .map_err(|_| "signature does not verify")?;
    Ok(())
}

fn proof_verification_method(proof: &Value) -> Result<String, String> {
    let vm = proof.get("verificationMethod")
        .and_then(|v| v.as_str())
        .ok_or("proof missing verificationMethod")?;
    Ok(extract_did(vm))
}

fn extract_did(s: &str) -> String {
    match s.find('#') {
        Some(idx) => s[..idx].to_string(),
        None => s.to_string(),
    }
}

fn verifying_key_from_did(did: &str) -> Result<VerifyingKey, String> {
    let Some(multikey) = did.strip_prefix("did:key:") else {
        return Err(format!(
            "unsupported DID prefix in {did:?}"));
    };
    let Some(b58) = multikey.strip_prefix('z') else {
        return Err("DID key must be base58btc");
    };
    let bytes = bs58::decode(b58).into_vec()
        .map_err(|e| format!("base58 DID: {e}"))?;
    // Ed25519 multikey prefix: 0xed 0x01
    if bytes.len() != 34
        || bytes[0] != 0xed
        || bytes[1] != 0x01
    {
        return Err("DID key is not an Ed25519 public key");
    }
    let mut key = [0u8; 32];
    key.copy_from_slice(&bytes[2..34]);
    VerifyingKey::from_bytes(&key)
        .map_err(|e| format!("ed25519 key: {e}"))
}

// ────────────────────────────────────────────────────────────
// SHA-256 as hex
// ────────────────────────────────────────────────────────────

fn hex_sha256(bytes: &[u8]) -> String {
    let mut h = Sha256::new();
    h.update(bytes);
    let mut out = String::with_capacity(64);
    for b in h.finalize() {
        out.push_str(&format!("{b:02x}"));
    }
    out
}

// ────────────────────────────────────────────────────────────
// State reconstruction — from log alone, no garden types
// ────────────────────────────────────────────────────────────

#[derive(Default)]
struct GardenState {
    cycle: u64,
    plants: std::collections::HashMap<String, [i64; 3]>,
    agents: std::collections::HashMap<String, [i64; 3]>,
}

impl GardenState {
    fn apply(&mut self, body: &Value, index: usize)
        -> Result<(), String>
    {
        let kind = body.get("kind")
            .and_then(|v| v.as_str())
            .ok_or_else(|| format!(
                "entry[{index}]: body missing 'kind'"))?;
        match kind {
            "admission" => {
                // actor is the admitted agent — no position yet
            }
            "plant_added" => {
                let id = body.get("plant_id")
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| format!(
                        "entry[{index}]: plant_added missing plant_id"))?;
                let pos = parse_3d(body.get("position"))
                    .map_err(|e| format!("entry[{index}]: {e}"))?;
                self.plants.insert(id.to_string(), pos);
            }
            "plant_retired" => {
                let id = body.get("plant_id")
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| format!(
                        "entry[{index}]: plant_retired missing plant_id"))?;
                self.plants.remove(id);
            }
            "agent_entered" | "agent_walked" => {
                let actor = body.get("actor")
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| format!(
                        "entry[{index}]: {kind} missing actor"))?;
                let pos = body.get("position")
                    .or_else(|| body.get("to"))
                    .ok_or_else(|| format!(
                        "entry[{index}]: {kind} missing position/to"))?;
                self.agents.insert(
                    actor.to_string(), parse_3d(Some(pos))?);
            }
            "cycle_advanced" => {
                self.cycle = body.get("cycle")
                    .and_then(|v| v.as_u64())
                    .unwrap_or(self.cycle);
            }
            // Proposals, whispers, observations, refusals:
            // no state effect. We accept them; we simply
            // don't record anything.
            _ => {}
        }
        Ok(())
    }
}

fn parse_3d(v: Option<&Value>) -> Result<[i64; 3], String> {
    let arr = v.and_then(|v| v.as_array())
        .ok_or("expected 3-element array")?;
    if arr.len() != 3 {
        return Err(format!(
            "expected 3 elements, got {}", arr.len()));
    }
    Ok([
        arr[0].as_i64().ok_or("non-integer")?,
        arr[1].as_i64().ok_or("non-integer")?,
        arr[2].as_i64().ok_or("non-integer")?,
    ])
}
