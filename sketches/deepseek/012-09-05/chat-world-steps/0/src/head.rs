//! World heads — signed commitments to a log's state at a point.
//!
//! A head is a *published artifact*, not a record in the log. The
//! world emits heads on demand and publishes them (plugin, file,
//! peer). A peer who receives a head can:
//!
//!   - verify its signature (the world attests to it)
//!   - hold it as a binding commitment to the log's prefix
//!   - later verify against the full log (or a state snapshot)
//!
//! The head commits to:
//!   chain_head  — the last record's hash at publish time
//!   log_len     — number of records at publish time
//!   state_hash  — hash of the renderable state at publish time
//!   params_hash — the current params hash (template hash for chat)
//!   template_hash — the template hash (constant for chat)

use crate::did::DidKey;
use crate::error::{Error, Result};
use crate::hash;
use crate::proof::{Proof, ProofOrArray};
use crate::room::Room;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct WorldHead {
    #[serde(rename = "type")]
    pub type_: String,
    pub world_id: DidKey,
    pub tick: u64,
    pub chain_head: String,
    pub log_len: u64,
    pub state_hash: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub ext_rain_commitment: Option<String>,
    pub params_hash: String,
    pub template_hash: String,
    pub ts: String,
    pub proof: ProofOrArray,
}

impl WorldHead {
    pub fn hash(&self) -> Result<String> {
        hash::hash_of(self)
    }
}

/// Emit a fresh head for a room. Does NOT append to the room's log.
pub fn emit_head(room: &Room) -> Result<WorldHead> {
    let records = room.records();
    let last = records
        .last()
        .ok_or_else(|| Error::Policy("cannot emit head for empty room".into()))?;
    let chain_head = last.hash()?;
    let log_len = records.len() as u64;
    let state = crate::record::visible_log_from(records);
    let state_hash = hash::hash_of(&state)?;
    let template_hash = room.template().hash()?;

    let mut head = WorldHead {
        type_: "world_head".into(),
        world_id: room.world_id().clone(),
        tick: log_len.saturating_sub(1),
        chain_head,
        log_len,
        state_hash,
        ext_rain_commitment: None,
        params_hash: template_hash.clone(),
        template_hash,
        ts: crate::now(),
        proof: ProofOrArray::placeholder(),
    };

    let body = hash::body_for_signing(&head)?;
    let sig = room.keypair().sign(&body);
    head.proof = ProofOrArray::single(Proof::create(room.keypair(), &sig));
    Ok(head)
}

/// Verify a head against the *current* room. Stricter than
/// `verify::verify_head_against_log`: requires the log's length to
/// match the head's `log_len` exactly.
pub fn verify_head(head: &WorldHead, room: &Room) -> Result<()> {
    if head.world_id != *room.world_id() {
        return Err(Error::Verification("world_id mismatch".into()));
    }
    if room.records().len() as u64 != head.log_len {
        return Err(Error::Verification(format!(
            "log_len mismatch: room has {}, head says {}",
            room.records().len(),
            head.log_len
        )));
    }
    crate::verify::verify_head_against_log(head, room.records())
}
