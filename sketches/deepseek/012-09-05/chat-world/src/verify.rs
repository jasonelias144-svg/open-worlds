use crate::did::DidKey;
use crate::error::{Error, Result};
use crate::hash;
use crate::record::*;
use crate::room::{Member, Room};
use std::collections::{HashMap, HashSet};

/// Full offline verification: chain, signatures, and policy replay.
pub fn verify_room(room: &Room) -> Result<()> {
    let world_id = room.world_id();
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

        // Room proof required for all records except Leave.
        if !matches!(rec, Record::Leave(_)) {
            let Some(rp) = proofs.find_by_method(world_id) else {
                return Err(Error::Verification(format!("record {i}: missing room proof")));
            };
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
                match target {
                    Some(Record::Message(m)) => {
                        let is_author = m.author_id == r.subject_id;
                        let is_mod = tier_rank(&mem.tier).unwrap_or(0) >= tier_rank("control").unwrap();
                        if !is_author && !is_mod {
                            return Err(Error::Policy(format!("record {i}: redaction not permitted")));
                        }
                    }
                    _ => return Err(Error::Policy(format!("record {i}: redact target not a message"))),
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
            }
            Record::Refusal(r) => {
                let _ = r;
            }
        }

        prev = Some(rec.hash()?);
    }

    if room.template().personal {
        for rec in room.records() {
            if let Record::Join(j) = rec {
                if &j.subject_id != world_id {
                    return Err(Error::Policy("personal room contains non-seed member".into()));
                }
            }
        }
    }

    Ok(())
}

/// Chain integrity only — useful when signatures are known-good.
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
