use crate::did::{DidKey, Keypair};
use crate::error::{Error, Result};
use crate::record::*;
use crate::template::RoomTemplate;
use std::collections::{HashMap, HashSet};

#[derive(Clone, Debug)]
pub struct Member {
    pub tier: String,
    pub is_ai: bool,
}

pub struct Room {
    pub world_id: DidKey,
    pub template: RoomTemplate,
    keypair: Keypair,
    records: Vec<Record>,
    members: HashMap<DidKey, Member>,
    redacted: HashSet<String>,
}

impl Room {
    pub fn create(template: RoomTemplate, creator: Keypair) -> Result<Self> {
        let world_id = creator.did();
        let mut members = HashMap::new();
        members.insert(
            world_id.clone(),
            Member { tier: "terminal".into(), is_ai: false },
        );
        let mut room = Room {
            world_id: world_id.clone(),
            template: template.clone(),
            keypair: creator,
            records: Vec::new(),
            members,
            redacted: HashSet::new(),
        };
        let rec = RoomCreated::new(world_id.clone(), template, world_id);
        let signed = crate::sign_record(rec, &room.keypair, |r, p| r.proof = p)?;
        room.records.push(Record::RoomCreated(signed));
        Ok(room)
    }

    // ---- Accessors ----

    pub fn records(&self) -> &[Record] {
        &self.records
    }
    pub fn last_hash(&self) -> Option<String> {
        self.records.last().and_then(|r| r.hash().ok())
    }
    pub fn world_id(&self) -> &DidKey {
        &self.world_id
    }
    pub fn template(&self) -> &RoomTemplate {
        &self.template
    }
    pub fn members(&self) -> &HashMap<DidKey, Member> {
        &self.members
    }
    pub fn keypair(&self) -> &Keypair {
        &self.keypair
    }
    pub fn is_redacted(&self, hash: &str) -> bool {
        self.redacted.contains(hash)
    }

    // ---- Internal helpers ----

    fn next_seq(&self) -> u64 {
        self.records.len() as u64
    }

    fn push(&mut self, rec: Record) {
        self.records.push(rec);
    }

    fn refuse(
        &mut self,
        requester: DidKey,
        request_hash: String,
        reason: &str,
    ) -> Result<Record> {
        let rec = Refusal::new(
            self.world_id.clone(),
            self.next_seq(),
            self.last_hash(),
            request_hash,
            requester,
            reason.into(),
        );
        let signed = crate::sign_record(rec, &self.keypair, |r, p| r.proof = p)?;
        let out = Record::Refusal(signed);
        self.push(out.clone());
        Ok(out)
    }

    fn rate_ok(&self, author: &DidKey) -> bool {
        let window = self.template.rate_limit_window as usize;
        let cap = self.template.rate_limit_count as usize;
        let recent = self
            .records
            .iter()
            .rev()
            .take(window)
            .filter(|r| matches!(r, Record::Message(m) if &m.author_id == author))
            .count();
        recent < cap
    }

    // ---- Operations ----

    pub fn join(
        &mut self,
        subject_kp: &Keypair,
        tier: &str,
        is_ai: bool,
    ) -> Result<Record> {
        let subject = subject_kp.did();
        if self.members.contains_key(&subject) {
            return self.refuse(subject, "".into(), "already_member");
        }
        if tier_rank(tier).is_none() {
            return self.refuse(subject, "".into(), "unknown_tier");
        }
        if self.template.personal && subject != self.world_id {
            return self.refuse(subject, "".into(), "personal_room");
        }
        if self.template.membership == "human_only" && is_ai {
            return self.refuse(subject, "".into(), "human_only_room");
        }
        if self.template.membership == "ai_only" && !is_ai {
            return self.refuse(subject, "".into(), "ai_only_room");
        }
        if self.template.join_policy == "invite" && !self.template.personal {
            return self.refuse(subject, "".into(), "invite_required");
        }
        if self.template.join_policy == "approval" {
            return self.refuse(subject, "".into(), "approval_required");
        }
        let rec = Join::new(
            self.world_id.clone(),
            self.next_seq(),
            self.last_hash(),
            subject.clone(),
            tier.into(),
            is_ai,
        );
        let signed =
            crate::sign_record_dual(rec, subject_kp, &self.keypair, |r, p| r.proof = p)?;
        self.members.insert(
            subject,
            Member { tier: tier.into(), is_ai },
        );
        let out = Record::Join(signed);
        self.push(out.clone());
        Ok(out)
    }

    pub fn leave(&mut self, subject_kp: &Keypair) -> Result<Option<Record>> {
        let subject = subject_kp.did();
        if !self.members.contains_key(&subject) {
            return Ok(None);
        }
        let rec = Leave::new(
            self.world_id.clone(),
            self.next_seq(),
            self.last_hash(),
            subject.clone(),
        );
        // Leave is signed by the subject only — no room countersignature,
        // because the room cannot refuse a leave.
        let signed = crate::sign_record(rec, subject_kp, |r, p| r.proof = p)?;
        self.members.remove(&subject);
        let out = Record::Leave(signed);
        self.push(out.clone());
        Ok(Some(out))
    }

    pub fn post(
        &mut self,
        author_kp: &Keypair,
        text: &str,
        kind: &str,
    ) -> Result<Record> {
        let author = author_kp.did();
        let Some(m) = self.members.get(&author) else {
            return self.refuse(author, "".into(), "not_a_member");
        };
        if tier_rank(&m.tier).unwrap_or(0) < tier_rank("communicate").unwrap() {
            return self.refuse(author, "".into(), "insufficient_tier");
        }
        if text.len() as u64 > self.template.max_msg_len {
            return self.refuse(author, "".into(), "message_too_long");
        }
        if !self.rate_ok(&author) {
            return self.refuse(author, "".into(), "rate_limit");
        }
        let rec = Message::new(
            self.world_id.clone(),
            self.next_seq(),
            self.last_hash(),
            author.clone(),
            text.into(),
            kind.into(),
        );
        let signed =
            crate::sign_record_dual(rec, author_kp, &self.keypair, |r, p| r.proof = p)?;
        let out = Record::Message(signed);
        self.push(out.clone());
        Ok(out)
    }

    pub fn redact(
        &mut self,
        subject_kp: &Keypair,
        target_hash: &str,
        reason: &str,
    ) -> Result<Record> {
        let subject = subject_kp.did();
        let Some(m) = self.members.get(&subject) else {
            return self.refuse(subject, "".into(), "not_a_member");
        };
        let target = self
            .records
            .iter()
            .find(|r| r.hash().ok().as_deref() == Some(target_hash));
        let target_msg = match target {
            Some(Record::Message(msg)) => msg,
            _ => return self.refuse(subject, "".into(), "target_not_found"),
        };
        let is_author = target_msg.author_id == subject;
        let is_mod = self.template.moderation == "moderator"
            && tier_rank(&m.tier).unwrap_or(0) >= tier_rank("control").unwrap();
        if self.template.moderation == "none" {
            return self.refuse(subject, "".into(), "moderation_disabled");
        }
        if !is_author && !is_mod {
            return self.refuse(subject, "".into(), "not_allowed");
        }
        let rec = Redact::new(
            self.world_id.clone(),
            self.next_seq(),
            self.last_hash(),
            subject.clone(),
            target_hash.into(),
            reason.into(),
        );
        let signed =
            crate::sign_record_dual(rec, subject_kp, &self.keypair, |r, p| r.proof = p)?;
        self.redacted.insert(target_hash.into());
        let out = Record::Redact(signed);
        self.push(out.clone());
        Ok(out)
    }

    pub fn override_ai(
        &mut self,
        overrider_kp: &Keypair,
        overrides_hash: &str,
        action: &str,
        reason: &str,
    ) -> Result<Record> {
        let overrider = overrider_kp.did();
        let Some(m) = self.members.get(&overrider) else {
            return Err(Error::Policy("overrider is not a member".into()));
        };
        if m.is_ai {
            return Err(Error::Policy("only humans can override".into()));
        }
        if tier_rank(&m.tier).unwrap_or(0) < tier_rank("control").unwrap() {
            return Err(Error::Policy("insufficient tier".into()));
        }
        let target = self
            .records
            .iter()
            .find(|r| r.hash().ok().as_deref() == Some(overrides_hash));
        let Some(target_rec) = target else {
            return Err(Error::Policy("target not found".into()));
        };
        let Some(author) = target_rec.author_id() else {
            return Err(Error::Policy("target has no author".into()));
        };
        let is_ai = self.members.get(author).map(|m| m.is_ai).unwrap_or(false);
        if !is_ai {
            return Err(Error::Policy("can only override AI records".into()));
        }
        // Honour moderator spec can_be_overridden
        if let Some(spec) = &self.template.moderator {
            if &spec.moderator_id == author && !spec.can_be_overridden {
                return Err(Error::Policy("this AI cannot be overridden".into()));
            }
        }
        let rec = HumanOverride::new(
            self.world_id.clone(),
            self.next_seq(),
            self.last_hash(),
            overrides_hash.into(),
            overrider.clone(),
            action.into(),
            reason.into(),
        );
        let signed =
            crate::sign_record_dual(rec, overrider_kp, &self.keypair, |r, p| r.proof = p)?;
        let out = Record::HumanOverride(signed);
        self.push(out.clone());
        Ok(out)
    }

    /// Return a serializable view of the log, with redacted text hidden.
    pub fn visible_log(&self) -> Vec<serde_json::Value> {
        use serde_json::json;
        let mut out = Vec::new();
        let mut redacted_hashes: HashSet<String> = HashSet::new();
        for rec in &self.records {
            match rec {
                Record::Redact(r) => {
                    redacted_hashes.insert(r.target_hash.clone());
                    out.push(json!({
                        "seq": r.seq,
                        "type": "redact",
                        "by": r.subject_id.as_str(),
                        "reason": r.reason,
                        "target": r.target_hash,
                    }));
                }
                Record::Message(m) => {
                    let hash = m.hash().unwrap_or_default();
                    let hidden = redacted_hashes.contains(&hash);
                    let text = if hidden { "[redacted]".to_string() } else { m.text.clone() };
                    out.push(json!({
                        "seq": m.seq,
                        "type": "message",
                        "kind": m.kind,
                        "author": m.author_id.as_str(),
                        "text": text,
                        "redacted": hidden,
                        "ts": m.ts,
                    }));
                }
                Record::Join(j) => {
                    out.push(json!({
                        "seq": j.seq,
                        "type": "join",
                        "subject": j.subject_id.as_str(),
                        "tier": j.tier,
                        "is_ai": j.is_ai,
                    }));
                }
                Record::Leave(l) => {
                    out.push(json!({
                        "seq": l.seq,
                        "type": "leave",
                        "subject": l.subject_id.as_str(),
                    }));
                }
                Record::HumanOverride(o) => {
                    out.push(json!({
                        "seq": o.seq,
                        "type": "human_override",
                        "by": o.overridden_by.as_str(),
                        "overrides": o.overrides_hash,
                        "action": o.action,
                        "reason": o.reason,
                    }));
                }
                Record::Refusal(r) => {
                    out.push(json!({
                        "seq": r.seq,
                        "type": "refused",
                        "requester": r.requester_id.as_str(),
                        "reason": r.reason,
                    }));
                }
                Record::RoomCreated(_) => {
                    out.push(json!({
                        "seq": 0,
                        "type": "created",
                    }));
                }
            }
        }
        out
    }
}
