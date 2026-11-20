//! Runtime attestations.
//!
//! A runtime that holds multiple keys may declare them. The
//! attestation is co-signed by every listed key, so no key can be
//! added without its owner's consent. It is a *published artifact*
//! (like a head), not a record in any log. Without one, keys are
//! treated as independent — the correct default. With one, a reader
//! knows the keys share a runtime and *also* knows each key's
//! KnowledgeWorld is its own chain, because isolation is what the
//! key is.

use crate::did::{DidKey, Keypair};
use crate::error::{Error, Result};
use crate::hash;
use crate::proof::{Proof, ProofOrArray};
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RuntimeAttestation {
    #[serde(rename = "type")]
    pub type_: String,
    pub runtime_id: DidKey,
    pub keys: Vec<DidKey>,
    pub ts: String,
    pub proof: ProofOrArray,
}

impl RuntimeAttestation {
    pub fn hash(&self) -> Result<String> {
        hash::hash_of(self)
    }
}

/// Sign a runtime attestation. The caller supplies the runtime's
/// key and the full list of keys sharing this runtime. Every
/// listed key must sign; the runtime key is one of them. The
/// runtime_id must appear in the list. Duplicates are refused.
pub fn attest_runtime(
    runtime_kp: &Keypair,
    keys: &[&Keypair],
) -> Result<RuntimeAttestation> {
    let runtime_id = runtime_kp.did();
    let key_ids: Vec<DidKey> = keys.iter().map(|k| k.did()).collect();
    if !key_ids.iter().any(|k| k == &runtime_id) {
        return Err(Error::Policy(
            "runtime_id must appear in the keys list".into(),
        ));
    }
    let mut seen = std::collections::HashSet::new();
    for k in &key_ids {
        if !seen.insert(k.clone()) {
            return Err(Error::Policy(format!(
                "duplicate key: {}",
                k.as_str()
            )));
        }
    }
    let mut att = RuntimeAttestation {
        type_: "runtime_attestation".into(),
        runtime_id,
        keys: key_ids,
        ts: crate::now(),
        proof: ProofOrArray::placeholder(),
    };
    let body = hash::body_for_signing(&att)?;
    let mut proofs = Vec::new();
    for kp in keys {
        let sig = kp.sign(&body);
        proofs.push(Proof::create(kp, &sig));
    }
    att.proof = ProofOrArray::array(proofs);
    Ok(att)
}

/// Verify a runtime attestation: structure, every listed key's
/// proof present and valid, no proof for a key not in the list,
/// no duplicates, runtime_id in the list.
pub fn verify_attestation(att: &RuntimeAttestation) -> Result<()> {
    if att.type_ != "runtime_attestation" {
        return Err(Error::Verification("not a runtime_attestation".into()));
    }
    if att.keys.is_empty() {
        return Err(Error::Verification("empty keys list".into()));
    }
    if !att.keys.iter().any(|k| k == &att.runtime_id) {
        return Err(Error::Verification(
            "runtime_id not in keys list".into(),
        ));
    }
    let mut seen = std::collections::HashSet::new();
    for k in &att.keys {
        if !seen.insert(k.clone()) {
            return Err(Error::Verification(format!(
                "duplicate key: {}",
                k.as_str()
            )));
        }
    }
    let body = hash::body_for_signing(att)?;
    // Every listed key must have exactly one proof
    for k in &att.keys {
        let p = att.proof.find_by_method(k).ok_or_else(|| {
            Error::Verification(format!("missing proof for {}", k.as_str()))
        })?;
        p.verify(&body)?;
    }
    // Every proof must be for a listed key; count must match
    match &att.proof {
        ProofOrArray::Single(_) => {
            return Err(Error::Verification(
                "attestation must carry one proof per key".into(),
            ));
        }
        ProofOrArray::Array(proofs) => {
            if proofs.len() != att.keys.len() {
                return Err(Error::Verification(format!(
                    "proof count {} != key count {}",
                    proofs.len(),
                    att.keys.len()
                )));
            }
            for p in proofs {
                if !att.keys.iter().any(|k| k == &p.verification_method) {
                    return Err(Error::Verification(format!(
                        "proof for {} but not in keys list",
                        p.verification_method.as_str()
                    )));
                }
            }
        }
    }
    Ok(())
}
