use crate::did::DidKey;
use crate::error::{Error, Result};
use crate::hash;
use crate::record::*;
use crate::room::{Member, Room};
use std::collections::{HashMap, HashSet};

fn looks_like_hash(s: &str) -> bool {
    s.len() == 64 && s.chars().all(|c| c.is_ascii_hexdigit())
}

pub fn verify_room(room: &Room) -> Result<()> {
    let world_id = room.world_id();
    let (creator_id, per_record_mode) = match room.records().first() {
        Some(Record::RoomCreated(rc)) => {
            (rc.creator_id.clone(), rc.template.head_interval <= 1)
        }
        _ => return Err(Error::Chain("log must start with room_created".into())),
    };

    let mut prev: Option<String> = None;
    let mut members: HashMap<DidKey, Member> = HashMap::new();
    let mut redacted: HashSet<String> = HashSet::new();

    for (i, rec) in room.records().iter().enumerate() {
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
                let author_proof = proofs.find_by_method(&m.author_id)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing author proof")))?;
                author_proof.verify(&body)?;
            }
            Record::Join(j) => {
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
                let target = room.records().iter()
                    .find(|x| x.hash().ok().as_deref() == Some(&r.target_hash));
                let target_msg = match target {
                    Some(Record::Message(m)) => m,
                    _ => return Err(Error::Policy(format!("record {i}: redact target not a message"))),
                };
                if room.template().moderation == "none" {
                    return Err(Error::Policy(format!("record {i}: moderation disabled")));
                }
                let is_author = target_msg.author_id == r.subject_id;
                let is_mod = room.template().moderation == "moderator"
                    && tier_rank(&mem.tier).unwrap_or(0) >= tier_rank("control").unwrap();
                let role_ok = match r.actor_role.as_str() {
                    "author" => is_author,
                    "moderator" => is_mod,
                    _ => false,
                };
                if !role_ok {
                    return Err(Error::Policy(format!("record {i}: actor_role {:?} not permitted", r.actor_role)));
                }
                if !room.template().redaction_rules.iter().any(|x| x == &r.rule) {
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
                let target = room.records().iter()
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
                if !room.template().personal {
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
                if !room.template().personal {
                    return Err(Error::Policy(format!("record {i}: bookmark only in personal rooms")));
                }
            }
            Record::Presence(p) => {
                if !room.template().personal {
                    return Err(Error::Policy(format!("record {i}: presence only in personal rooms")));
                }
                if p.subject_id != creator_id {
                    return Err(Error::Policy(format!("record {i}: presence subject must be creator")));
                }
            }
            Record::KnowledgeShardExport(k) => {
                if !room.template().personal {
                    return Err(Error::Policy(format!("record {i}: knowledge_shard_export only in personal rooms")));
                }
                if k.entry_hashes.iter().any(|h| !looks_like_hash(h)) {
                    return Err(Error::Policy(format!("record {i}: shard entry hash not a 64-hex string")));
                }
                // Room proof already verified above.
            }
            Record::ModeratorSuccession(s) => {
                // Room proof verified above. Outgoing + incoming also sign.
                let outgoing_proof = proofs.find_by_method(&s.outgoing_id)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing outgoing proof")))?;
                outgoing_proof.verify(&body)?;
                let incoming_proof = proofs.find_by_method(&s.incoming_id)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing incoming proof")))?;
                incoming_proof.verify(&body)?;
                // Outgoing must be a control+ member at this point.
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

    // Heads
    let mut last_length: u64 = 0;
    for (i, head) in room.heads().iter().enumerate() {
        room.verify_head(head).map_err(|e| Error::Verification(format!("head {i}: {e}")))?;
        if head.length <= last_length {
            return Err(Error::Verification(format!("head {i}: length not increasing")));
        }
        last_length = head.length;
    }
    if per_record_mode && !room.heads().is_empty() {
        return Err(Error::Verification("per-record mode should not emit heads".into()));
    }
    if !per_record_mode {
        let n = room.template().head_interval;
        let appends = room.records().len().saturating_sub(1) as u64;
        let expected = if n > 1 { appends / n } else { 0 };
        if expected > 0 && room.heads().len() as u64 != expected {
            return Err(Error::Verification(format!(
                "head count: expected {} for {} appends at interval {}, got {}",
                expected, appends, n, room.heads().len()
            )));
        }
    }

    if room.template().personal {
        for rec in room.records() {
            if let Record::Join(j) = rec {
                if j.subject_id != creator_id {
                    return Err(Error::Policy("personal room: non-creator joined".into()));
                }
            }
        }
    }

    Ok(())
}

pub fn verify_chain(room: &Room) -> Result<()> {
    let mut prev: Option<String> = None;
    for (i, rec) in room.records().iter().enumerate() {
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
