// rust/formats/src/records/garden_curator_proposal.rs

//! `garden_curator_proposal` — a W3C DataIntegrity record.
//!
//! Composes with the existing `formats::records` discipline.
//! A signed proposal is a `GardenCuratorProposalPayload`
//! (the body) plus a `DataIntegrityProof`.
//!
//! Body shape:
//!   {
//!     "kind": "garden_curator_proposal",
//!     "curator_did": "did:key:z...",
//!     "cycle": <u64>,
//!     "proposal": { ... per-variant fields ... }
//!   }
//!
//! Every field in the body is deterministic. Signatures are
//! Ed25519, deterministic given the same key and body. The
//! body hash (SHA-256 of JCS body) is the vector observable.

use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::canonical::jcs_bytes;
use crate::proof::{DataIntegrityProof, SigningKey, VerifyingKey};

// ────────────────────────────────────────────────────────────
// The proposal variants
// ────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "proposal_type", rename_all = "snake_case")]
pub enum GardenProposal {
    MovePlant {
        plant_id: String,
        to: [i64; 3],
    },
    AddPlant {
        plant_id: String,
        kind: String,
        at: [i64; 3],
    },
    RetirePlant {
        plant_id: String,
        reason: String,
    },
    Invite {
        agent_a: String,
        agent_b: String,
        at: [i64; 3],
    },
    Whisper {
        to: Option<String>,
        text: String,
    },
}

// ────────────────────────────────────────────────────────────
// Payload and signed record
// ────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct GardenCuratorProposalPayload {
    pub kind: GardenProposalKindTag,
    pub curator_did: String,
    pub cycle: u64,
    pub proposal: GardenProposal,
}

/// Phantom tag: only ever `"garden_curator_proposal"`.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum GardenProposalKindTag {
    #[serde(rename = "garden_curator_proposal")]
    GardenCuratorProposal,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SignedGardenCuratorProposal {
    #[serde(flatten)]
    pub payload: GardenCuratorProposalPayload,
    pub proof: DataIntegrityProof,
}

impl GardenCuratorProposalPayload {
    /// The body hash — the deterministic observable that
    /// implementations must agree on.
    pub fn body_hash(&self) -> [u8; 32] {
        use sha2::{Digest, Sha256};
        let mut h = Sha256::new();
        h.update(jcs_bytes(self));
        h.finalize().into()
    }

    /// Turn a payload into a signed record. The proof is over
    /// the JCS-canonical form of the payload.
    pub fn sign(
        self,
        key: &SigningKey,
    ) -> Result<SignedGardenCuratorProposal, ProofError> {
        let proof = crate::proof::sign(
            crate::proof::Suite::EddsaJcs2022,
            key,
            &serde_json::to_value(&self)
                .map_err(|_| ProofError::Serialize)?,
        )?;
        Ok(SignedGardenCuratorProposal {
            payload: self,
            proof,
        })
    }
}

impl SignedGardenCuratorProposal {
    /// Verify the record's proof against its declared curator
    /// DID. Never raises for malformed input; returns an error.
    pub fn verify(&self) -> Result<(), ProofError> {
        let vk = VerifyingKey::from_did(&self.payload.curator_did)
            .map_err(|_| ProofError::BadDid)?;
        crate::proof::verify(
            crate::proof::Suite::EddsaJcs2022,
            &self.proof,
            &serde_json::to_value(&self.payload)
                .map_err(|_| ProofError::Serialize)?,
            &vk,
        )
    }

    /// Body hash — matches `payload.body_hash()` for a valid
    /// record.
    pub fn body_hash(&self) -> [u8; 32] {
        self.payload.body_hash()
    }
}

// ────────────────────────────────────────────────────────────
// Errors
// ────────────────────────────────────────────────────────────

#[derive(Debug)]
pub enum ProofError {
    Sign,
    Verify,
    Serialize,
    BadDid,
}
