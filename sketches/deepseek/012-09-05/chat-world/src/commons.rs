use crate::did::{DidKey, Keypair};
use crate::error::{Error, Result};
use crate::hash;
use crate::proof::ProofOrArray;
use crate::room::Room;
use serde::{Deserialize, Serialize};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RoomRegistered {
    #[serde(rename = "type")]
    pub type_: String,
    pub commons_id: DidKey,
    pub seq: u64,
    pub prev: Option<String>,
    pub room_id: DidKey,
    pub topic: String,
    pub template_hash: String,
    pub room_seed_hash: String,
    pub registered_by: DidKey,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub also_listed_in: Vec<DidKey>,
    pub ts: String,
    pub proof: ProofOrArray,
}

impl RoomRegistered {
    pub fn hash(&self) -> Result<String> {
        hash::hash_of(self)
    }
}

pub struct Commons {
    pub world_id: DidKey,
    keypair: Keypair,
    records: Vec<RoomRegistered>,
}

impl Commons {
    pub fn new(keypair: Keypair) -> Self {
        let world_id = keypair.did();
        Commons { world_id, keypair, records: Vec::new() }
    }

    pub fn records(&self) -> &[RoomRegistered] {
        &self.records
    }

    pub fn register_room(
        &mut self,
        room: &Room,
        registrant_kp: &Keypair,
        topic: Option<String>,
    ) -> Result<RoomRegistered> {
        let seq = self.records.len() as u64;
        let prev = match self.records.last() {
            Some(r) => Some(r.hash()?),
            None => None,
        };
        let seed_hash = room
            .records()
            .first()
            .ok_or_else(|| Error::Policy("room has no seed".into()))?
            .hash()?;
        let mut rec = RoomRegistered {
            type_: "room_registered".into(),
            commons_id: self.world_id.clone(),
            seq,
            prev,
            room_id: room.world_id().clone(),
            topic: topic.unwrap_or_else(|| room.template().topic.clone()),
            template_hash: room.template().hash()?,
            room_seed_hash: seed_hash,
            registered_by: registrant_kp.did(),
            also_listed_in: Vec::new(),
            ts: crate::now(),
            proof: ProofOrArray::placeholder(),
        };
        // Dual-sign: registrant + commons
        let body = hash::body_for_signing(&rec)?;
        let reg_sig = registrant_kp.sign(&body);
        let commons_sig = self.keypair.sign(&body);
        rec.proof = ProofOrArray::array(vec![
            crate::Proof::create(registrant_kp, &reg_sig),
            crate::Proof::create(&self.keypair, &commons_sig),
        ]);
        self.records.push(rec.clone());
        Ok(rec)
    }
}

pub fn verify_commons(commons: &Commons) -> Result<()> {
    let mut prev: Option<String> = None;
    for (i, rec) in commons.records().iter().enumerate() {
        if rec.type_ != "room_registered" {
            return Err(Error::Verification(format!("record {i}: not a registration")));
        }
        if rec.commons_id != commons.world_id {
            return Err(Error::Verification(format!("record {i}: commons_id mismatch")));
        }
        if rec.prev != prev {
            return Err(Error::Chain(format!("record {i}: prev mismatch")));
        }
        let body = hash::body_for_signing(rec)?;
        let reg = rec
            .proof
            .find_by_method(&rec.registered_by)
            .ok_or_else(|| Error::Verification(format!("record {i}: missing registrant proof")))?;
        reg.verify(&body)?;
        let com = rec
            .proof
            .find_by_method(&commons.world_id)
            .ok_or_else(|| Error::Verification(format!("record {i}: missing commons proof")))?;
        com.verify(&body)?;
        prev = Some(rec.hash()?);
    }
    Ok(())
}
