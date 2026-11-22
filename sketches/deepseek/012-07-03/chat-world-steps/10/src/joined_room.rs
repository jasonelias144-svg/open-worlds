//! A joined room — a participant's view of a room they do not
//! hold the key of.
//!
//! The participant has the room's published `RoomLog`, their own
//! `Keypair`, and a `pending` list of author-signed records they
//! intend to submit. Head-mode rooms accept author-signed records
//! past the last head; the keeper appends them (see
//! `Room::accept_pending`) and the next head covers them. In
//! per-record mode, only the keeper can post, because every
//! record needs the room's countersignature and that changes its
//! hash.

use crate::did::{DidKey, Keypair};
use crate::error::{Error, Result};
use crate::record::*;
use crate::room::RoomLog;
use crate::verify::verify_log;

pub struct JoinedRoom {
    log: RoomLog,
    user_kp: Keypair,
    pending: Vec<Record>,
}

impl JoinedRoom {
    /// Attach to a published room. Verifies the log before
    /// accepting it — an invalid log is not a room to join.
    pub fn from_log(log: RoomLog, user_kp: Keypair) -> Result<Self> {
        verify_log(&log)?;
        Ok(JoinedRoom { log, user_kp, pending: Vec::new() })
    }

    pub fn log(&self) -> &RoomLog { &self.log }
    pub fn pending(&self) -> &[Record] { &self.pending }
    pub fn user_id(&self) -> DidKey { self.user_kp.did() }

    pub fn visible_log(&self) -> Vec<serde_json::Value> {
        let mut out = self.log.visible_log();
        out.extend(crate::room::visible_log_from(&self.pending));
        out
    }

    fn head_mode_ok(&self) -> Result<()> {
        if self.log.template.head_interval <= 1 {
            return Err(Error::Policy(
                "joined_room: pending records require head mode (head_interval > 1)".into(),
            ));
        }
        Ok(())
    }

    fn next_seq(&self) -> u64 {
        (self.log.records.len() + self.pending.len()) as u64
    }

    fn last_hash(&self) -> Option<String> {
        if let Some(r) = self.pending.last() {
            r.hash().ok()
        } else {
            self.log.records.last().and_then(|r| r.hash().ok())
        }
    }

    fn replay_membership(&self) -> (bool, Option<String>) {
        let user_id = self.user_kp.did();
        let mut is_member = false;
        let mut tier: Option<String> = None;
        for rec in self.log.records.iter().chain(self.pending.iter()) {
            match rec {
                Record::RoomCreated(rc) if rc.creator_id == user_id => {
                    is_member = true;
                    tier = Some("terminal".into());
                }
                Record::Join(j) if j.subject_id == user_id => {
                    is_member = true;
                    tier = Some(j.tier.clone());
                }
                Record::Leave(l) if l.subject_id == user_id => {
                    is_member = false;
                    tier = None;
                }
                _ => {}
            }
        }
        (is_member, tier)
    }

    pub fn is_member(&self) -> bool {
        self.replay_membership().0
    }

    pub fn request_join(&mut self, tier: &str, is_ai: bool) -> Result<Record> {
        self.head_mode_ok()?;
        let (already_member, _) = self.replay_membership();
        if already_member {
            return Err(Error::Policy("joined_room: already a member".into()));
        }
        if tier_rank(tier).is_none() {
            return Err(Error::Policy(format!("unknown tier: {tier}")));
        }
        let rec = Join::new(
            self.log.world_id.clone(),
            self.next_seq(),
            self.last_hash(),
            self.user_kp.did(),
            tier.into(),
            is_ai,
        );
        let signed = crate::sign_record(rec, &self.user_kp, Record::Join, |r, p| r.proof = p)?;
        let out = Record::Join(signed);
        self.pending.push(out.clone());
        Ok(out)
    }

    pub fn post(&mut self, text: &str, kind: &str) -> Result<Record> {
        self.head_mode_ok()?;
        let (is_member, tier) = self.replay_membership();
        if !is_member {
            return Err(Error::Policy("joined_room: not a member; call request_join first".into()));
        }
        if tier_rank(tier.as_deref().unwrap_or("")).unwrap_or(0) < tier_rank("communicate").unwrap() {
            return Err(Error::Policy("joined_room: insufficient tier to post".into()));
        }
        if text.len() as u64 > self.log.template.max_msg_len {
            return Err(Error::Policy("joined_room: message too long".into()));
        }
        let rec = Message::new(
            self.log.world_id.clone(),
            self.next_seq(),
            self.last_hash(),
            self.user_kp.did(),
            text.into(),
            kind.into(),
        );
        let signed = crate::sign_record(rec, &self.user_kp, Record::Message, |r, p| r.proof = p)?;
        let out = Record::Message(signed);
        self.pending.push(out.clone());
        Ok(out)
    }

    pub fn leave(&mut self) -> Result<Record> {
        self.head_mode_ok()?;
        let (is_member, _) = self.replay_membership();
        if !is_member {
            return Err(Error::Policy("joined_room: not a member".into()));
        }
        let rec = Leave::new(
            self.log.world_id.clone(),
            self.next_seq(),
            self.last_hash(),
            self.user_kp.did(),
        );
        let signed = crate::sign_record(rec, &self.user_kp, Record::Leave, |r, p| r.proof = p)?;
        let out = Record::Leave(signed);
        self.pending.push(out.clone());
        Ok(out)
    }

    pub fn export_pending(&self) -> Vec<Record> {
        self.pending.clone()
    }

    pub fn clear_pending(&mut self) {
        self.pending.clear();
    }

    /// Verify the pending records (seq, prev, author proof). Does
    /// not check policy — that's the keeper's job. This catches
    /// local formatting errors before sending.
    pub fn verify_pending(&self) -> Result<()> {
        let mut running_seq = self.log.records.len() as u64;
        let mut running_prev = self.log.records.last().and_then(|r| r.hash().ok());
        for (i, rec) in self.pending.iter().enumerate() {
            if rec.seq() != running_seq {
                return Err(Error::Chain(format!(
                    "pending {i}: seq {} != expected {}",
                    rec.seq(), running_seq
                )));
            }
            if rec.prev() != running_prev.as_ref() {
                return Err(Error::Chain(format!("pending {i}: prev mismatch")));
            }
            let Some(author) = rec.author_id() else {
                return Err(Error::Policy(format!("pending {i}: no author")));
            };
            let body = crate::hash::body_for_signing(rec)?;
            let proof = rec.proof().find_by_method(author)
                .ok_or_else(|| Error::Verification(format!(
                    "pending {i}: missing author proof"
                )))?;
            proof.verify(&body)?;
            running_seq += 1;
            running_prev = Some(rec.hash()?);
        }
        Ok(())
    }
}
