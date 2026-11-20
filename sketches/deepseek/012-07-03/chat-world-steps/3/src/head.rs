//! Signed heads.
//!
//! A head is a small, signed commitment to a log's prefix: how
//! many entries it holds, what the last one hashes to, and when
//! (in the room's sense of "when"). It is a *published artifact*,
//! not a record in the log. A room in `head_interval > 1` mode
//! emits a head every N appended records; peers can verify a
//! head alone and know the log's prefix is fixed.

use crate::did::DidKey;
use crate::error::{Error, Result};
use crate::hash;
use crate::proof::{Proof, ProofOrArray};
use crate::room::Room;
use serde::{Deserialize, Serialize};

pub const HEAD_FORMAT_V1: &str = "open-worlds/log-head/v1";

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct WorldHead {
    pub format: String,
    pub world: DidKey,
    pub length: u64,
    pub last: String,
    pub tick: u64,
    pub proof: ProofOrArray,
}

impl WorldHead {
    pub fn hash(&self) -> Result<String> {
        hash::hash_of(self)
    }
}

impl Room {
    /// Emit a head for the room's current state. Does NOT append
    /// to the room's log; the head is a published artifact.
    pub fn emit_head(&self) -> Result<WorldHead> {
        let last_rec = self
            .records()
            .last()
            .ok_or_else(|| Error::Policy("cannot emit head for empty room".into()))?;
        let last_hash = last_rec.hash()?;
        let length = self.records().len() as u64;
        let mut head = WorldHead {
            format: HEAD_FORMAT_V1.into(),
            world: self.world_id().clone(),
            length,
            last: last_hash,
            tick: length,
            proof: ProofOrArray::placeholder(),
        };
        let body = hash::body_for_signing(&head)?;
        let sig = self.keypair().sign(&body);
        head.proof = ProofOrArray::single(Proof::create(self.keypair(), &sig));
        Ok(head)
    }

    /// Verify a head against the room it claims to be about.
    /// The room must be at least as long as the head; the head's
    /// prefix must be intact and its signature valid.
    pub fn verify_head(&self, head: &WorldHead) -> Result<()> {
        if head.format != HEAD_FORMAT_V1 {
            return Err(Error::Verification(format!(
                "head: bad format {:?}",
                head.format
            )));
        }
        if head.world != *self.world_id() {
            return Err(Error::Verification("head: world mismatch".into()));
        }
        if head.length as usize > self.records().len() {
            return Err(Error::Verification(format!(
                "head: length {} exceeds log length {}",
                head.length,
                self.records().len()
            )));
        }
        if head.length == 0 {
            return Err(Error::Verification("head: length 0".into()));
        }
        if head.length != head.tick {
            return Err(Error::Verification(format!(
                "head: tick {} != length {}",
                head.tick, head.length
            )));
        }
        let prefix = &self.records()[..head.length as usize];
        let last_hash = prefix[prefix.len() - 1].hash()?;
        if last_hash != head.last {
            return Err(Error::Verification("head: last mismatch".into()));
        }
        let body = hash::body_for_signing(head)?;
        let proof = head
            .proof
            .find_by_method(self.world_id())
            .ok_or_else(|| Error::Verification("head: missing room proof".into()))?;
        proof.verify(&body)
    }
}
