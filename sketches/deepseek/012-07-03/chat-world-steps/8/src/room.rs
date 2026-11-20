use crate::did::{DidKey, Keypair};
use crate::error::{Error, Result};
use crate::head::WorldHead;
use crate::record::*;
use crate::template::RoomTemplate;
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};

fn short_hash(h: &str) -> String {
    h.chars().take(16).collect()
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RoomLog {
    pub world_id: DidKey,
    pub template: RoomTemplate,
    pub records: Vec<Record>,
    pub heads: Vec<WorldHead>,
}

impl RoomLog {
    pub fn visible_log(&self) -> Vec<serde_json::Value> {
        visible_log_from(&self.records)
    }
}

pub fn visible_log_from(records: &[Record]) -> Vec<serde_json::Value> {
    use serde_json::json;

    let hashes: Vec<String> = records.iter()
        .map(|r| r.hash().unwrap_or_default())
        .collect();
    let mut hash_to_idx: HashMap<String, usize> = HashMap::new();
    for (i, h) in hashes.iter().enumerate() {
        hash_to_idx.insert(h.clone(), i);
    }

    let mut redactions_by_target: HashMap<usize, Vec<usize>> = HashMap::new();
    let mut resolved_redacts: HashSet<usize> = HashSet::new();
    for (i, rec) in records.iter().enumerate() {
        match rec {
            Record::Redact(r) => {
                if let Some(&target_idx) = hash_to_idx.get(&r.target_hash) {
                    redactions_by_target.entry(target_idx).or_default().push(i);
                }
            }
            Record::HumanOverride(o) if o.action == "restore" => {
                if let Some(&redact_idx) = hash_to_idx.get(&o.overrides_hash) {
                    resolved_redacts.insert(redact_idx);
                }
            }
            _ => {}
        }
    }

    let mut out = Vec::new();
    for (i, rec) in records.iter().enumerate() {
        match rec {
            Record::Message(m) => {
                let mut still_redacted: Option<usize> = None;
                let mut restored: Vec<usize> = Vec::new();
                if let Some(redact_idxs) = redactions_by_target.get(&i) {
                    for &ri in redact_idxs {
                        if resolved_redacts.contains(&ri) {
                            restored.push(ri);
                        } else if still_redacted.is_none() {
                            still_redacted = Some(ri);
                        }
                    }
                }
                if let Some(ri) = still_redacted {
                    if let Record::Redact(r) = &records[ri] {
                        out.push(json!({
                            "seq": m.seq, "type": "message", "kind": m.kind,
                            "author": m.author_id.as_str(),
                            "text": "[removed]",
                            "redacted": true,
                            "reason": r.reason,
                            "rule": r.rule,
                            "incident": short_hash(&hashes[ri]),
                            "ts": m.ts,
                        }));
                    }
                } else {
                    let mut obj = json!({
                        "seq": m.seq, "type": "message", "kind": m.kind,
                        "author": m.author_id.as_str(),
                        "text": m.text,
                        "redacted": false,
                        "ts": m.ts,
                    });
                    if !restored.is_empty() {
                        let notes: Vec<serde_json::Value> = restored.iter().map(|&ri| {
                            if let Record::Redact(r) = &records[ri] {
                                json!({"incident": short_hash(&hashes[ri]), "reason": r.reason, "rule": r.rule})
                            } else { json!({}) }
                        }).collect();
                        obj["restored_incidents"] = json!(notes);
                    }
                    out.push(obj);
                }
            }
            Record::Redact(r) => {
                out.push(json!({"seq": r.seq, "type": "redact", "by": r.subject_id.as_str(), "reason": r.reason, "target": r.target_hash, "rule": r.rule, "actor_role": r.actor_role, "incident": short_hash(&hashes[i])}));
            }
            Record::Join(j) => {
                out.push(json!({"seq": j.seq, "type": "join", "subject": j.subject_id.as_str(), "tier": j.tier, "is_ai": j.is_ai}));
            }
            Record::Leave(l) => {
                out.push(json!({"seq": l.seq, "type": "leave", "subject": l.subject_id.as_str()}));
            }
            Record::HumanOverride(o) => {
                out.push(json!({"seq": o.seq, "type": "human_override", "by": o.overridden_by.as_str(), "overrides": o.overrides_hash, "action": o.action, "reason": o.reason}));
            }
            Record::Refusal(r) => {
                out.push(json!({"seq": r.seq, "type": "refused", "requester": r.requester_id.as_str(), "reason": r.reason}));
            }
            Record::RoomCreated(rc) => {
                let mut obj = json!({"seq": 0, "type": "created"});
                if let Some(ff) = &rc.forked_from {
                    obj["forked_from"] = json!({
                        "parent_id": ff.parent_id.as_str(),
                        "checkpoint_seq": ff.checkpoint_seq,
                        "checkpoint_hash": ff.checkpoint_hash,
                    });
                }
                out.push(obj);
            }
            Record::ModeratorSuccession(s) => {
                out.push(json!({
                    "seq": s.seq, "type": "moderator_succession",
                    "outgoing": s.outgoing_id.as_str(),
                    "incoming": s.incoming_id.as_str(),
                    "reason": s.reason,
                }));
            }
            Record::ModeratorScope(s) => {
                out.push(json!({
                    "seq": s.seq, "type": "moderator_scope",
                    "human_facing_rooms": s.human_facing_rooms.iter().map(|r| r.as_str()).collect::<Vec<_>>(),
                    "meta_rooms": s.meta_rooms.iter().map(|r| r.as_str()).collect::<Vec<_>>(),
                    "ts": s.ts,
                }));
            }
            Record::KnowledgeShardExport(_) | Record::PortLanding(_) | Record::Bookmark(_) | Record::Presence(_) => {}
        }
    }
    out
}

#[derive(Clone, Debug)]
pub struct Member {
    pub tier: String,
    pub is_ai: bool,
}

pub struct Room {
    world_id: DidKey,
    template: RoomTemplate,
    keypair: Keypair,
    records: Vec<Record>,
    members: HashMap<DidKey, Member>,
    heads: Vec<WorldHead>,
}

impl Room {
    pub fn create(
        template: RoomTemplate,
        room_kp: Keypair,
        creator_kp: &Keypair,
    ) -> Result<Self> {
        let world_id = room_kp.did();
        let creator_id = creator_kp.did();
        let mut members = HashMap::new();
        members.insert(
            creator_id.clone(),
            Member { tier: "terminal".into(), is_ai: false },
        );
        let mut room = Room {
            world_id: world_id.clone(),
            template: template.clone(),
            keypair: room_kp,
            records: Vec::new(),
            members,
            heads: Vec::new(),
        };
        let rec = RoomCreated::new(world_id, template, creator_id);
        let signed = crate::sign_record_dual(
            rec, creator_kp, &room.keypair, Record::RoomCreated, |r, p| r.proof = p,
        )?;
        room.records.push(Record::RoomCreated(signed));
        Ok(room)
    }

    pub fn branch_at(
        &self,
        checkpoint_seq: u64,
        new_template: RoomTemplate,
        branch_kp: Keypair,
        maker_kp: &Keypair,
    ) -> Result<Room> {
        if checkpoint_seq >= self.records.len() as u64 {
            return Err(Error::Policy(format!(
                "checkpoint seq {checkpoint_seq} past end of parent (len {})",
                self.records.len()
            )));
        }
        if self.template.head_interval > 1 {
            let covered = self.heads.last().map(|h| h.length).unwrap_or(0);
            if checkpoint_seq >= covered {
                return Err(Error::Policy(format!(
                    "checkpoint seq {checkpoint_seq} not covered by any published head (last head covers 0..{covered})"
                )));
            }
        }
        let checkpoint_rec = &self.records[checkpoint_seq as usize];
        let checkpoint_hash = checkpoint_rec.hash()?;
        let forked_from = ForkedFrom {
            parent_id: self.world_id.clone(),
            checkpoint_seq,
            checkpoint_hash,
        };
        let branch_world_id = branch_kp.did();
        let maker_id = maker_kp.did();
        let mut members = HashMap::new();
        members.insert(
            maker_id.clone(),
            Member { tier: "terminal".into(), is_ai: false },
        );
        let mut branch = Room {
            world_id: branch_world_id.clone(),
            template: new_template.clone(),
            keypair: branch_kp,
            records: Vec::new(),
            members,
            heads: Vec::new(),
        };
        let rec = RoomCreated::branch(branch_world_id, new_template, maker_id, forked_from);
        let signed = crate::sign_record_dual(
            rec, maker_kp, &branch.keypair, Record::RoomCreated, |r, p| r.proof = p,
        )?;
        branch.records.push(Record::RoomCreated(signed));
        Ok(branch)
    }

    pub fn log(&self) -> RoomLog {
        let mut heads = self.heads.clone();
        if self.template.head_interval > 1 && self.records.len() > 1 {
            let len = self.records.len() as u64;
            let covered = heads.last().map(|h| h.length == len).unwrap_or(false);
            if !covered {
                if let Ok(tail_head) = self.emit_head() {
                    heads.push(tail_head);
                }
            }
        }
        RoomLog {
            world_id: self.world_id.clone(),
            template: self.template.clone(),
            records: self.records.clone(),
            heads,
        }
    }

    pub fn records(&self) -> &[Record] { &self.records }
    pub fn heads(&self) -> &[WorldHead] { &self.heads }
    pub fn last_hash(&self) -> Option<String> { self.records.last().and_then(|r| r.hash().ok()) }
    pub fn world_id(&self) -> &DidKey { &self.world_id }
    pub fn template(&self) -> &RoomTemplate { &self.template }
    pub fn members(&self) -> &HashMap<DidKey, Member> { &self.members }
    pub fn keypair(&self) -> &Keypair { &self.keypair }
    pub fn head_interval(&self) -> u64 { self.template.head_interval }

    pub fn is_redacted(&self, message_hash: &str) -> bool {
        let mut redact_hashes: Vec<String> = Vec::new();
        let mut resolved: HashSet<String> = HashSet::new();
        for rec in &self.records {
            match rec {
                Record::Redact(r) if r.target_hash == message_hash => {
                    if let Ok(h) = rec.hash() { redact_hashes.push(h); }
                }
                Record::HumanOverride(o) if o.action == "restore" => {
                    resolved.insert(o.overrides_hash.clone());
                }
                _ => {}
            }
        }
        redact_hashes.iter().any(|h| !resolved.contains(h))
    }

    fn next_seq(&self) -> u64 { self.records.len() as u64 }

    fn should_emit_head(&self) -> bool {
        let n = self.template.head_interval;
        if n <= 1 { return false; }
        let appends = self.records.len().saturating_sub(1) as u64;
        appends > 0 && appends % n == 0
    }

    pub(crate) fn push(&mut self, rec: Record) -> Result<()> {
        self.records.push(rec);
        if self.should_emit_head() {
            let head = self.emit_head()?;
            self.heads.push(head);
        }
        Ok(())
    }

    fn refuse(&mut self, requester: DidKey, request_hash: String, reason: &str) -> Result<Record> {
        let rec = Refusal::new(
            self.world_id.clone(), self.next_seq(), self.last_hash(),
            request_hash, requester, reason.into(),
        );
        let signed = crate::sign_record(rec, &self.keypair, Record::Refusal, |r, p| r.proof = p)?;
        let out = Record::Refusal(signed);
        self.push(out.clone())?;
        Ok(out)
    }

    fn rate_ok(&self, author: &DidKey) -> bool {
        let window = self.template.rate_limit_window as usize;
        let cap = self.template.rate_limit_count as usize;
        let recent = self.records.iter().rev().take(window)
            .filter(|r| matches!(r, Record::Message(m) if &m.author_id == author))
            .count();
        recent < cap
    }

    fn inter_ai_pace_ok(&self, is_ai: bool) -> bool {
        if !is_ai || self.template.inter_ai_pace == 0 {
            return true;
        }
        let mut last_ai_idx: Option<usize> = None;
        for (i, rec) in self.records.iter().enumerate().rev() {
            if let Record::Message(m) = rec {
                let ai = self.members.get(&m.author_id).map(|x| x.is_ai).unwrap_or(false);
                if ai {
                    last_ai_idx = Some(i);
                    break;
                }
            }
        }
        match last_ai_idx {
            None => true,
            Some(idx) => {
                let since = (self.records.len() - idx - 1) as u64;
                since >= self.template.inter_ai_pace
            }
        }
    }

    pub fn join(&mut self, subject_kp: &Keypair, tier: &str, is_ai: bool) -> Result<Record> {
        let subject = subject_kp.did();
        if self.members.contains_key(&subject) {
            return self.refuse(subject, "".into(), "already_member");
        }
        if tier_rank(tier).is_none() {
            return self.refuse(subject, "".into(), "unknown_tier");
        }
        if self.template.personal {
            return self.refuse(subject, "".into(), "personal_room");
        }
        if self.template.membership == "human_only" && is_ai {
            return self.refuse(subject, "".into(), "human_only_room");
        }
        if self.template.membership == "ai_only" && !is_ai {
            return self.refuse(subject, "".into(), "ai_only_room");
        }
        if self.template.join_policy == "invite" {
            return self.refuse(subject, "".into(), "invite_required");
        }
        if self.template.join_policy == "approval" {
            return self.refuse(subject, "".into(), "approval_required");
        }
        let rec = Join::new(
            self.world_id.clone(), self.next_seq(), self.last_hash(),
            subject.clone(), tier.into(), is_ai,
        );
        let signed = if self.template.head_interval <= 1 {
            crate::sign_record_dual(rec, subject_kp, &self.keypair, Record::Join, |r, p| r.proof = p)?
        } else {
            crate::sign_record(rec, subject_kp, Record::Join, |r, p| r.proof = p)?
        };
        self.members.insert(subject, Member { tier: tier.into(), is_ai });
        let out = Record::Join(signed);
        self.push(out.clone())?;
        Ok(out)
    }

    pub fn leave(&mut self, subject_kp: &Keypair) -> Result<Option<Record>> {
        let subject = subject_kp.did();
        if !self.members.contains_key(&subject) {
            return Ok(None);
        }
        let rec = Leave::new(
            self.world_id.clone(), self.next_seq(), self.last_hash(), subject.clone(),
        );
        let signed = crate::sign_record(rec, subject_kp, Record::Leave, |r, p| r.proof = p)?;
        self.members.remove(&subject);
        let out = Record::Leave(signed);
        self.push(out.clone())?;
        Ok(Some(out))
    }

    pub fn post(&mut self, author_kp: &Keypair, text: &str, kind: &str) -> Result<Record> {
        let author = author_kp.did();
        let Some(m) = self.members.get(&author).cloned() else {
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
        if !self.inter_ai_pace_ok(m.is_ai) {
            return self.refuse(author, "".into(), "inter_ai_pace");
        }
        let rec = Message::new(
            self.world_id.clone(), self.next_seq(), self.last_hash(),
            author.clone(), text.into(), kind.into(),
        );
        let signed = if self.template.head_interval <= 1 {
            crate::sign_record_dual(rec, author_kp, &self.keypair, Record::Message, |r, p| r.proof = p)?
        } else {
            crate::sign_record(rec, author_kp, Record::Message, |r, p| r.proof = p)?
        };
        let out = Record::Message(signed);
        self.push(out.clone())?;
        Ok(out)
    }

    pub fn redact(
        &mut self,
        subject_kp: &Keypair,
        target_hash: &str,
        rule: &str,
        reason: &str,
    ) -> Result<Record> {
        let subject = subject_kp.did();
        let Some(m) = self.members.get(&subject).cloned() else {
            return self.refuse(subject, "".into(), "not_a_member");
        };
        let target = self.records.iter()
            .find(|r| r.hash().ok().as_deref() == Some(target_hash));
        let target_msg = match target {
            Some(Record::Message(msg)) => msg,
            _ => return self.refuse(subject, "".into(), "target_not_found"),
        };
        if self.template.moderation == "none" {
            return self.refuse(subject, "".into(), "moderation_disabled");
        }
        let is_author = target_msg.author_id == subject;
        let is_mod = self.template.moderation == "moderator"
            && tier_rank(&m.tier).unwrap_or(0) >= tier_rank("control").unwrap();
        let actor_role = if is_author {
            "author"
        } else if is_mod {
            "moderator"
        } else {
            return self.refuse(subject, "".into(), "not_allowed");
        };
        if !self.template.redaction_rules.iter().any(|r| r == rule) {
            return self.refuse(subject, "".into(), "rule_not_allowed");
        }
        let rec = Redact::new(
            self.world_id.clone(), self.next_seq(), self.last_hash(),
            subject.clone(), target_hash.into(),
            actor_role.into(), rule.into(), reason.into(),
        );
        let signed = if self.template.head_interval <= 1 {
            crate::sign_record_dual(rec, subject_kp, &self.keypair, Record::Redact, |r, p| r.proof = p)?
        } else {
            crate::sign_record(rec, subject_kp, Record::Redact, |r, p| r.proof = p)?
        };
        let out = Record::Redact(signed);
        self.push(out.clone())?;
        Ok(out)
    }

    pub fn override_ai(&mut self, overrider_kp: &Keypair, overrides_hash: &str, reason: &str) -> Result<Record> {
        let overrider = overrider_kp.did();
        let Some(m) = self.members.get(&overrider).cloned() else {
            return Err(Error::Policy("overrider is not a member".into()));
        };
        if m.is_ai {
            return Err(Error::Policy("only humans can override".into()));
        }
        if tier_rank(&m.tier).unwrap_or(0) < tier_rank("control").unwrap() {
            return Err(Error::Policy("insufficient tier".into()));
        }
        let target = self.records.iter()
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
        if let Some(spec) = &self.template.moderator {
            if &spec.moderator_id == author && !spec.can_be_overridden {
                return Err(Error::Policy("this AI cannot be overridden".into()));
            }
        }
        let rec = HumanOverride::new(
            self.world_id.clone(), self.next_seq(), self.last_hash(),
            overrides_hash.into(), overrider.clone(), "none".into(), reason.into(),
        );
        let signed = if self.template.head_interval <= 1 {
            crate::sign_record_dual(rec, overrider_kp, &self.keypair, Record::HumanOverride, |r, p| r.proof = p)?
        } else {
            crate::sign_record(rec, overrider_kp, Record::HumanOverride, |r, p| r.proof = p)?
        };
        let out = Record::HumanOverride(signed);
        self.push(out.clone())?;
        Ok(out)
    }

    pub fn restore_incident(&mut self, restorer_kp: &Keypair, redact_hash: &str, reason: &str) -> Result<Record> {
        let restorer = restorer_kp.did();
        let Some(m) = self.members.get(&restorer).cloned() else {
            return Err(Error::Policy("restorer is not a member".into()));
        };
        if m.is_ai {
            return Err(Error::Policy("only humans can restore".into()));
        }
        if tier_rank(&m.tier).unwrap_or(0) < tier_rank("control").unwrap() {
            return Err(Error::Policy("insufficient tier".into()));
        }
        let target = self.records.iter()
            .find(|r| r.hash().ok().as_deref() == Some(redact_hash));
        match target {
            Some(Record::Redact(_)) => {}
            _ => return Err(Error::Policy("restore target must be a redact record".into())),
        }
        let rec = HumanOverride::new(
            self.world_id.clone(), self.next_seq(), self.last_hash(),
            redact_hash.into(), restorer.clone(), "restore".into(), reason.into(),
        );
        let signed = if self.template.head_interval <= 1 {
            crate::sign_record_dual(rec, restorer_kp, &self.keypair, Record::HumanOverride, |r, p| r.proof = p)?
        } else {
            crate::sign_record(rec, restorer_kp, Record::HumanOverride, |r, p| r.proof = p)?
        };
        let out = Record::HumanOverride(signed);
        self.push(out.clone())?;
        Ok(out)
    }

    pub fn declare_succession(
        &mut self,
        outgoing_kp: &Keypair,
        incoming_kp: &Keypair,
        shard_hash: &str,
        reason: &str,
    ) -> Result<Record> {
        let outgoing_id = outgoing_kp.did();
        let incoming_id = incoming_kp.did();
        let Some(m) = self.members.get(&outgoing_id) else {
            return Err(Error::Policy("outgoing is not a member".into()));
        };
        if tier_rank(&m.tier).unwrap_or(0) < tier_rank("control").unwrap() {
            return Err(Error::Policy("outgoing must be control or higher".into()));
        }
        if outgoing_id == incoming_id {
            return Err(Error::Policy("outgoing and incoming must differ".into()));
        }
        let rec = ModeratorSuccession::new(
            self.world_id.clone(), self.next_seq(), self.last_hash(),
            outgoing_id, incoming_id, shard_hash.into(), reason.into(),
        );
        let signed = crate::sign_record_triple(
            rec, outgoing_kp, incoming_kp, &self.keypair,
            Record::ModeratorSuccession, |r, p| r.proof = p,
        )?;
        let out = Record::ModeratorSuccession(signed);
        self.push(out.clone())?;
        Ok(out)
    }

    pub fn visible_log(&self) -> Vec<serde_json::Value> {
        visible_log_from(&self.records)
    }
}
