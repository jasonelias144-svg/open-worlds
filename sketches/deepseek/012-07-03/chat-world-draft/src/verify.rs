use crate::did::DidKey;
use crate::error::{Error, Result};
use crate::hash;
use crate::record::*;
use crate::room::Room;
use std::collections::{HashMap, HashSet};

/// Full offline verification: chain integrity, signatures, and
/// policy replay. Returns Ok(()) if the room's log is valid.
pub fn verify_room(room: &Room) -> Result<()> {
    let world_id = room.world_id();
    let mut prev: Option<String> = None;
    let mut members: HashMap<DidKey, String> = HashMap::new();
    let mut redacted: HashSet<String> = HashSet::new();

    for (i, rec) in room.records().iter().enumerate() {
        // Chain
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

        // Signature
        let body = hash::body_for_signing(rec)?;
        let proofs = rec.proof();

        // Room proof required for all records except Leave (which
        // is signed by subject only).
        let room_proof = proofs.find_by_method(world_id);
        if !matches!(rec, Record::Leave(_)) {
            let Some(rp) = room_proof else {
                return Err(Error::Verification(format!(
                    "record {i}: missing room proof"
                )));
            };
            rp.verify(&body)?;
        }

        // Record-specific checks
        match rec {
            Record::RoomCreated(r) => {
                // Creator signer must match creator_id
                let creator_proof = proofs.find_by_method(&r.creator_id).ok_or_else(|| {
                    Error::Verification(format!("record {i}: missing creator proof"))
                })?;
                creator_proof.verify(&body)?;
                members.insert(r.creator_id.clone(), "terminal".into());
            }
            Record::Message(m) => {
                let Some(tier) = members.get(&m.author_id) else {
                    return Err(Error::Policy(format!("record {i}: author not a member")));
                };
                if tier_rank(tier).unwrap_or(0) < tier_rank("communicate").unwrap() {
                    return Err(Error::Policy(format!(
                        "record {i}: author tier insufficient"
                    )));
                }
                let author_proof = proofs.find_by_method(&m.author_id).ok_or_else(|| {
                    Error::Verification(format!("record {i}: missing author proof"))
                })?;
                author_proof.verify(&body)?;
                // Reference target hash if redacted
                let msg_hash = rec.hash()?;
                if redacted.contains(&msg_hash) {
                    // Fine — redacted messages remain in log
                }
            }
            Record::Join(j) => {
                let subject_proof = proofs.find_by_method(&j.subject_id).ok_or_else(|| {
                    Error::Verification(format!("record {i}: missing subject proof"))
                })?;
                subject_proof.verify(&body)?;
                members.insert(j.subject_id.clone(), j.tier.clone());
            }
            Record::Leave(l) => {
                let subject_proof = proofs.find_by_method(&l.subject_id).ok_or_else(|| {
                    Error::Verification(format!("record {i}: missing subject proof"))
                })?;
                subject_proof.verify(&body)?;
                members.remove(&l.subject_id);
            }
            Record::Redact(r) => {
                let subject_proof = proofs.find_by_method(&r.subject_id).ok_or_else(|| {
                    Error::Verification(format!("record {i}: missing subject proof"))
                })?;
                subject_proof.verify(&body)?;
                // Verify the target exists
                let target_exists = room
                    .records()
                    .iter()
                    .any(|x| x.hash().ok().as_deref() == Some(&r.target_hash));
                if !target_exists {
                    return Err(Error::Policy(format!(
                        "record {i}: redact target not found"
                    )));
                }
                redacted.insert(r.target_hash.clone());
            }
            Record::HumanOverride(o) => {
                let overrider_proof = proofs
                    .find_by_method(&o.overridden_by)
                    .ok_or_else(|| {
                        Error::Verification(format!(
                            "record {i}: missing overrider proof"
                        ))
                    })?;
                overrider_proof.verify(&body)?;
                // Overriders must be humans with control
                let Some(tier) = members.get(&o.overridden_by) else {
                    return Err(Error::Policy(format!(
                        "record {i}: overrider not a member"
                    )));
                };
                if tier_rank(tier).unwrap_or(0) < tier_rank("control").unwrap() {
                    return Err(Error::Policy(format!(
                        "record {i}: overrider tier insufficient"
                    )));
                }
            }
            Record::Refusal(r) => {
                // Room proof verified above; no other proof needed
                let _ = r;
            }
        }

        prev = Some(rec.hash()?);
    }

    // Personal room closure
    if room.template().personal {
        for rec in room.records() {
            if let Record::Join(j) = rec {
                if &j.subject_id != world_id {
                    return Err(Error::Policy(
                        "personal room contains non-seed member".into(),
                    ));
                }
            }
        }
    }

    Ok(())
}

/// Verify the room's `prev` chain without checking signatures.
/// Useful for cheap chain integrity checks.
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
