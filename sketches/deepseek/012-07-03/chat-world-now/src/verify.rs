use crate::did::DidKey;
use crate::error::{Error, Result};
use crate::hash;
use crate::record::*;
use crate::room::{Member, Room};
pub use crate::room::RoomLog;
use std::collections::{HashMap, HashSet};

fn looks_like_hash(s: &str) -> bool {
    s.len() == 64 && s.chars().all(|c| c.is_ascii_hexdigit())
}

pub fn verify_room(room: &Room) -> Result<()> {
    verify_log(&room.log())
}

pub fn verify_log(log: &RoomLog) -> Result<()> {
    let (world_id, creator_id, template, per_record_mode) = match log.records.first() {
        Some(Record::RoomCreated(rc)) => {
            if rc.world_id != log.world_id {
                return Err(Error::Verification(
                    "room_created world_id does not match log world_id".into(),
                ));
            }
            if rc.template.hash()? != log.template.hash()? {
                return Err(Error::Verification(
                    "room_created template does not match log template".into(),
                ));
            }
            (
                &rc.world_id,
                rc.creator_id.clone(),
                &rc.template,
                rc.template.head_interval <= 1,
            )
        }
        _ => return Err(Error::Chain("log must start with room_created".into())),
    };

    let mut prev: Option<String> = None;
    let mut members: HashMap<DidKey, Member> = HashMap::new();
    let mut redacted: HashSet<String> = HashSet::new();

    for (i, rec) in log.records.iter().enumerate() {
        if rec.seq() != i as u64 {
            return Err(Error::Chain(format!(
                "record {i}: seq {} != expected {}",
                rec.seq(),
                i
            )));
        }
        match rec {
            Record::RoomCreated(_) => {
                if i != 0 {
                    return Err(Error::Chain(format!("record {i}: room_created not at start")));
                }
            }
            _ => {
                if rec.prev() != prev.as_ref() {
                    return Err(Error::Chain(format!("record {i}: prev mismatch")));
                }
            }
        }

        if rec.world_id() != world_id {
            return Err(Error::Verification(format!(
                "record {i}: world_id mismatch"
            )));
        }

        let body = hash::body_for_signing(rec)?;
        let proofs = rec.proof();

        let requires_room_proof = match rec {
            Record::RoomCreated(_) => true,
            Record::Refusal(_) => true,
            Record::KnowledgeShardExport(_) => true,
            Record::ModeratorSuccession(_) => true,
            Record::Leave(_) => false,
            _ => per_record_mode,
        };
        if requires_room_proof {
            let rp = proofs.find_by_method(world_id).ok_or_else(|| {
                Error::Verification(format!("record {i}: missing room proof"))
            })?;
            rp.verify(&body)?;
        }

        match rec {
            Record::RoomCreated(r) => {
                let creator_proof = proofs.find_by_method(&r.creator_id)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing creator proof")))?;
                creator_proof.verify(&body)?;
                members.insert(r.creator_id.clone(), Member { tier: "terminal".into(), is_ai: false });
            }
            Record::Message(m) => {
                let Some(mem) = members.get(&m.author_id) else {
                    return Err(Error::Policy(format!("record {i}: author not a member")));
                };
                if tier_rank(&mem.tier).unwrap_or(0) < tier_rank("communicate").unwrap() {
                    return Err(Error::Policy(format!("record {i}: author tier insufficient")));
                }
                if m.text.len() as u64 > template.max_msg_len {
                    return Err(Error::Policy(format!("record {i}: message_too_long")));
                }
                let window = template.rate_limit_window as usize;
                let cap = template.rate_limit_count as usize;
                let recent = log.records[..i]
                    .iter()
                    .rev()
                    .take(window)
                    .filter(|r| matches!(r, Record::Message(prev_m) if prev_m.author_id == m.author_id))
                    .count();
                if recent >= cap {
                    return Err(Error::Policy(format!("record {i}: rate_limit exceeded")));
                }
                if mem.is_ai && template.inter_ai_pace > 0 {
                    let mut last_ai_idx: Option<usize> = None;
                    for (prev_idx, prev_rec) in log.records[..i].iter().enumerate().rev() {
                        if let Record::Message(prev_m) = prev_rec {
                            let prev_ai = members
                                .get(&prev_m.author_id)
                                .map(|x| x.is_ai)
                                .unwrap_or(false);
                            if prev_ai {
                                last_ai_idx = Some(prev_idx);
                                break;
                            }
                        }
                    }
                    if let Some(idx) = last_ai_idx {
                        let since = (i - idx - 1) as u64;
                        if since < template.inter_ai_pace {
                            return Err(Error::Policy(format!("record {i}: inter_ai_pace violated")));
                        }
                    }
                }
                let author_proof = proofs.find_by_method(&m.author_id)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing author proof")))?;
                author_proof.verify(&body)?;
            }
            Record::Join(j) => {
                if members.contains_key(&j.subject_id) {
                    return Err(Error::Policy(format!("record {i}: already_member")));
                }
                if tier_rank(&j.tier).is_none() {
                    return Err(Error::Policy(format!("record {i}: unknown_tier")));
                }
                if template.personal {
                    return Err(Error::Policy(format!("record {i}: personal_room")));
                }
                if template.membership == "human_only" && j.is_ai {
                    return Err(Error::Policy(format!("record {i}: human_only_room")));
                }
                if template.membership == "ai_only" && !j.is_ai {
                    return Err(Error::Policy(format!("record {i}: ai_only_room")));
                }
                if template.join_policy == "invite" {
                    return Err(Error::Policy(format!("record {i}: invite_required")));
                }
                if template.join_policy == "approval" {
                    return Err(Error::Policy(format!("record {i}: approval_required")));
                }
                let subject_proof = proofs.find_by_method(&j.subject_id)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing subject proof")))?;
                subject_proof.verify(&body)?;
                members.insert(j.subject_id.clone(), Member { tier: j.tier.clone(), is_ai: j.is_ai });
            }
            Record::Leave(l) => {
                let subject_proof = proofs.find_by_method(&l.subject_id)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing subject proof")))?;
                subject_proof.verify(&body)?;
                members.remove(&l.subject_id);
            }
            Record::Redact(r) => {
                let subject_proof = proofs.find_by_method(&r.subject_id)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing subject proof")))?;
                subject_proof.verify(&body)?;
                let Some(mem) = members.get(&r.subject_id) else {
                    return Err(Error::Policy(format!("record {i}: redactor not a member")));
                };
                let target = log.records.iter()
                    .find(|x| x.hash().ok().as_deref() == Some(&r.target_hash));
                let target_msg = match target {
                    Some(Record::Message(m)) => m,
                    _ => return Err(Error::Policy(format!("record {i}: redact target not a message"))),
                };
                if template.moderation == "none" {
                    return Err(Error::Policy(format!("record {i}: moderation disabled")));
                }
                let is_author = target_msg.author_id == r.subject_id;
                let is_mod = template.moderation == "moderator"
                    && tier_rank(&mem.tier).unwrap_or(0) >= tier_rank("control").unwrap();
                let role_ok = match r.actor_role.as_str() {
                    "author" => is_author,
                    "moderator" => is_mod,
                    _ => false,
                };
                if !role_ok {
                    return Err(Error::Policy(format!("record {i}: actor_role {:?} not permitted", r.actor_role)));
                }
                if !template.redaction_rules.iter().any(|x| x == &r.rule) {
                    return Err(Error::Policy(format!("record {i}: rule {:?} not allowed", r.rule)));
                }
                redacted.insert(r.target_hash.clone());
            }
            Record::HumanOverride(o) => {
                let overrider_proof = proofs.find_by_method(&o.overridden_by)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing overrider proof")))?;
                overrider_proof.verify(&body)?;
                let Some(mem) = members.get(&o.overridden_by) else {
                    return Err(Error::Policy(format!("record {i}: overrider not a member")));
                };
                if mem.is_ai {
                    return Err(Error::Policy(format!("record {i}: only humans can override")));
                }
                if tier_rank(&mem.tier).unwrap_or(0) < tier_rank("control").unwrap() {
                    return Err(Error::Policy(format!("record {i}: overrider tier insufficient")));
                }
                let target = log.records.iter()
                    .find(|x| x.hash().ok().as_deref() == Some(&o.overrides_hash));
                let Some(target) = target else {
                    return Err(Error::Policy(format!("record {i}: override target not found")));
                };
                match o.action.as_str() {
                    "none" => {
                        let Some(author) = target.author_id() else {
                            return Err(Error::Policy(format!("record {i}: override 'none' target has no author")));
                        };
                        let target_is_ai = members.get(author).map(|m| m.is_ai).unwrap_or(false);
                        if !target_is_ai {
                            return Err(Error::Policy(format!("record {i}: override 'none' target must be AI-authored")));
                        }
                    }
                    "restore" => {
                        if !matches!(target, Record::Redact(_)) {
                            return Err(Error::Policy(format!("record {i}: restore target must be a redact record")));
                        }
                    }
                    other => {
                        return Err(Error::Policy(format!("record {i}: unknown override action {other:?}")));
                    }
                }
            }
            Record::Refusal(_) => {}
            Record::PortLanding(p) => {
                if !template.personal {
                    return Err(Error::Policy(format!("record {i}: port_landing only in personal rooms")));
                }
                crate::transcript::verify_transcript(&p.transcript)
                    .map_err(|e| Error::Verification(format!("record {i}: transcript: {e}")))?;
                if p.intent != "journal" && p.intent != "room" {
                    return Err(Error::Policy(format!("record {i}: unknown port intent")));
                }
                if p.intent == "room" && p.target_room.is_none() {
                    return Err(Error::Policy(format!("record {i}: intent 'room' without target_room")));
                }
            }
            Record::Bookmark(_) => {
                if !template.personal {
                    return Err(Error::Policy(format!("record {i}: bookmark only in personal rooms")));
                }
            }
            Record::Presence(p) => {
                if !template.personal {
                    return Err(Error::Policy(format!("record {i}: presence only in personal rooms")));
                }
                if p.subject_id != creator_id {
                    return Err(Error::Policy(format!("record {i}: presence subject must be creator")));
                }
            }
            Record::KnowledgeShardExport(k) => {
                if !template.personal {
                    return Err(Error::Policy(format!("record {i}: knowledge_shard_export only in personal rooms")));
                }
                if k.entry_hashes.iter().any(|h| !looks_like_hash(h)) {
                    return Err(Error::Policy(format!("record {i}: shard entry hash not a 64-hex string")));
                }
            }
            Record::ModeratorSuccession(s) => {
                let outgoing_proof = proofs.find_by_method(&s.outgoing_id)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing outgoing proof")))?;
                outgoing_proof.verify(&body)?;
                let incoming_proof = proofs.find_by_method(&s.incoming_id)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing incoming proof")))?;
                incoming_proof.verify(&body)?;
                let Some(mem) = members.get(&s.outgoing_id) else {
                    return Err(Error::Policy(format!("record {i}: outgoing not a member")));
                };
                if tier_rank(&mem.tier).unwrap_or(0) < tier_rank("control").unwrap() {
                    return Err(Error::Policy(format!("record {i}: outgoing tier insufficient")));
                }
                if s.outgoing_id == s.incoming_id {
                    return Err(Error::Policy(format!("record {i}: outgoing == incoming")));
                }
                if !looks_like_hash(&s.knowledge_shard_hash) {
                    return Err(Error::Policy(format!("record {i}: knowledge_shard_hash not a 64-hex string")));
                }
            }
        }

        prev = Some(rec.hash()?);
    }

    let mut last_length: u64 = 0;
    for (i, head) in log.heads.iter().enumerate() {
        log.verify_head(head).map_err(|e| Error::Verification(format!("head {i}: {e}")))?;
        if head.length <= last_length {
            return Err(Error::Verification(format!("head {i}: length not increasing")));
        }
        last_length = head.length;
    }
    if per_record_mode && !log.heads.is_empty() {
        return Err(Error::Verification("per-record mode should not emit heads".into()));
    }
    if !per_record_mode {
        let n = template.head_interval;
        let appends = log.records.len().saturating_sub(1) as u64;
        if appends > 0 {
            let periodic = appends / n;
            let rem = appends % n;
            let expected = if rem == 0 { periodic } else { periodic + 1 };
            if log.heads.len() as u64 != expected {
                return Err(Error::Verification(format!(
                    "head count: expected {} for {} appends at interval {}, got {}",
                    expected, appends, n, log.heads.len()
                )));
            }
            for (k, head) in log.heads.iter().enumerate() {
                let k_u64 = k as u64;
                let expected_len = if k_u64 < periodic {
                    1 + (k_u64 + 1) * n
                } else {
                    log.records.len() as u64
                };
                if head.length != expected_len {
                    return Err(Error::Verification(format!(
                        "head {k}: expected length {expected_len}, got {}",
                        head.length
                    )));
                }
            }
        } else if !log.heads.is_empty() {
            return Err(Error::Verification(
                "head mode: no heads expected when no records appended after seed".into(),
            ));
        }
    }

    if template.personal {
        for rec in &log.records {
            if let Record::Join(j) = rec {
                if j.subject_id != creator_id {
                    return Err(Error::Policy("personal room: non-creator joined".into()));
                }
            }
        }
    }

    Ok(())
}

/// Hold a branch and its parent together. Checks:
///   - the branch's log verifies on its own;
///   - the parent's log verifies on its own;
///   - the branch names this parent (world_id match);
///   - the checkpoint seq is within the parent's log;
///   - the record at that seq in the parent hashes to the hash the
///     branch names;
///   - in head mode, the checkpoint is covered by the parent's
///     last published head (so the parent has committed to it);
///   - the branch's creator was a member of the parent at that
///     point (replayed from the parent's joins and leaves).
///
/// It does not check that the branch's law differs from the
/// parent's, or anything else about the branch's content: those are
/// the branch's own business, checked by `verify_log(branch)`.
pub fn verify_branch(parent: &RoomLog, branch: &RoomLog) -> Result<()> {
    verify_log(branch)?;
    verify_log(parent)?;

    let forked = match branch.records.first() {
        Some(Record::RoomCreated(rc)) => rc.forked_from.as_ref(),
        _ => return Err(Error::Chain("branch: no room_created record".into())),
    };
    let Some(forked) = forked else {
        return Err(Error::Policy(
            "verify_branch: branch log names no parent".into(),
        ));
    };

    if forked.parent_id != parent.world_id {
        return Err(Error::Policy(format!(
            "verify_branch: branch names parent {} but parent is {}",
            forked.parent_id.as_str(),
            parent.world_id.as_str()
        )));
    }

    let seq = forked.checkpoint_seq as usize;
    if seq >= parent.records.len() {
        return Err(Error::Policy(format!(
            "verify_branch: checkpoint seq {} past end of parent (len {})",
            seq,
            parent.records.len()
        )));
    }

    let actual_hash = parent.records[seq].hash()?;
    if actual_hash != forked.checkpoint_hash {
        return Err(Error::Policy(format!(
            "verify_branch: checkpoint hash mismatch at seq {seq}"
        )));
    }

    // In head mode, the checkpoint must be covered by the last
    // published head; otherwise the parent has not committed to it.
    if parent.template.head_interval > 1 {
        let covered = parent.heads.last().map(|h| h.length as usize).unwrap_or(0);
        // head.length is the count of records covered; the
        // record at that seq is the last covered one (index
        // head.length - 1). Any seq < head.length is covered.
        if seq >= covered {
            return Err(Error::Policy(format!(
                "verify_branch: checkpoint seq {seq} not covered by parent's last head (covers 0..{covered})"
            )));
        }
    }

    // Replay the parent's memberships up to and including the
    // checkpoint, and check the branch's creator was a member.
    let creator = match branch.records.first() {
        Some(Record::RoomCreated(rc)) => rc.creator_id.clone(),
        _ => unreachable!(),
    };
    let mut is_member_at_checkpoint = false;
    {
        let mut members: HashMap<DidKey, ()> = HashMap::new();
        for (i, rec) in parent.records[..=seq].iter().enumerate() {
            match rec {
                Record::RoomCreated(rc) => {
                    members.insert(rc.creator_id.clone(), ());
                }
                Record::Join(j) => {
                    if members.contains_key(&j.subject_id) {
                        return Err(Error::Chain(format!(
                            "verify_branch: parent record {i}: already_member"
                        )));
                    }
                    members.insert(j.subject_id.clone(), ());
                }
                Record::Leave(l) => {
                    members.remove(&l.subject_id);
                }
                _ => {}
            }
        }
        is_member_at_checkpoint = members.contains_key(&creator);
    }
    if !is_member_at_checkpoint {
        return Err(Error::Policy(format!(
            "verify_branch: branch's creator {} was not a member of the parent at checkpoint {}",
            creator.as_str(),
            seq
        )));
    }

    Ok(())
}

pub fn verify_chain(room: &Room) -> Result<()> {
    verify_log_chain(&room.log())
}

pub fn verify_log_chain(log: &RoomLog) -> Result<()> {
    let mut prev: Option<String> = None;
    for (i, rec) in log.records.iter().enumerate() {
        match rec {
            Record::RoomCreated(_) if i != 0 => {
                return Err(Error::Chain("room_created not at start".into()));
            }
            Record::RoomCreated(_) => {}
            _ => {
                if rec.prev() != prev.as_ref() {
                    return Err(Error::Chain(format!("record {i}: prev mismatch")));
                }
            }
        }
        prev = Some(rec.hash()?);
    }
    Ok(())
}
