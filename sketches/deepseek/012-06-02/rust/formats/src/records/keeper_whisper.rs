//! `keeper_whisper` — a W3C DataIntegrity record.
//!
//! A keeper whisper is a signed message from the garden's
//! keeper, either broadcast (`to: null`) or targeted
//! (`to: Some(did)`). It is an *act*, not a *proposal* — it
//! records something the keeper said, not something the
//! curator suggested. The garden records it; residents read
//! it from the log.
//!
//! Body shape:
//!   {
//!     "kind": "keeper_whisper",
//!     "keeper_did": "did:key:z...",
//!     "cycle": <u64>,
//!     "to": <null | "did:key:z...">,
//!     "text": "<non-empty>"
//!   }
//!
//! Every field is deterministic. `cycle` names the garden
//! cycle at which the whisper was issued; `tick` (added by the
//! garden's `append`) names its position in the log. Two
//! separate facts, both recorded.

use serde::{Deserialize, Serialize};

use crate::canonical::jcs_bytes;
use crate::proof::{DataIntegrityProof, SigningKey, VerifyingKey};

// ────────────────────────────────────────────────────────────
// Payload
// ────────────────────────────────────────────────────────────

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct KeeperWhisperPayload {
    pub kind: KeeperWhisperKindTag,
    pub keeper_did: String,
    pub cycle: u64,
    pub to: Option<String>,
    pub text: String,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum KeeperWhisperKindTag {
    #[serde(rename = "keeper_whisper")]
    KeeperWhisper,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SignedKeeperWhisper {
    #[serde(flatten)]
    pub payload: KeeperWhisperPayload,
    pub proof: DataIntegrityProof,
}

impl KeeperWhisperPayload {
    /// The body hash — the deterministic observable that
    /// implementations must agree on.
    pub fn body_hash(&self) -> [u8; 32] {
        use sha2::{Digest, Sha256};
        let mut h = Sha256::new();
        h.update(jcs_bytes(self));
        h.finalize().into()
    }

    pub fn sign(
        self,
        key: &SigningKey,
    ) -> Result<SignedKeeperWhisper, WhisperError> {
        let proof = crate::proof::sign(
            crate::proof::Suite::EddsaJcs2022,
            key,
            &serde_json::to_value(&self)
                .map_err(|_| WhisperError::Serialize)?,
        )?;
        Ok(SignedKeeperWhisper {
            payload: self,
            proof,
        })
    }
}

impl SignedKeeperWhisper {
    pub fn verify(&self) -> Result<(), WhisperError> {
        let vk = VerifyingKey::from_did(&self.payload.keeper_did)
            .map_err(|_| WhisperError::BadDid)?;
        crate::proof::verify(
            crate::proof::Suite::EddsaJcs2022,
            &self.proof,
            &serde_json::to_value(&self.payload)
                .map_err(|_| WhisperError::Serialize)?,
            &vk,
        )
    }

    pub fn body_hash(&self) -> [u8; 32] {
        self.payload.body_hash()
    }
}

#[derive(Debug)]
pub enum WhisperError {
    Sign,
    Verify,
    Serialize,
    BadDid,
}
