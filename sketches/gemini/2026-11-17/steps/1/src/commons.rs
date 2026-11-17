use crate::did::{DidKey, Keypair};
use crate::error::{Error, Result};
use crate::hash;
use crate::proof::{Proof, ProofOrArray};
use crate::room::Room;
use serde::{Deserialize, Deserializer, Serialize, Serializer};

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CommonsLog {
    pub commons_id: DidKey,
    pub records: Vec<CommonsRecord>,
}

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

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct SiblingDeclared {
    #[serde(rename = "type")]
    pub type_: String,
    pub commons_id: DidKey,
    pub seq: u64,
    pub prev: Option<String>,
    pub parent_id: DidKey,
    pub sibling_id: DidKey,
    pub parent_kw_id: DidKey,
    pub shard_hash: String,
    pub purpose: String,
    pub ts: String,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug)]
pub enum CommonsRecord {
    RoomRegistered(RoomRegistered),
    SiblingDeclared(SiblingDeclared),
}

impl Serialize for CommonsRecord {
    fn serialize<S: Serializer>(&self, serializer: S) -> std::result::Result<S::Ok, S::Error> {
        match self {
            CommonsRecord::RoomRegistered(r) => r.serialize(serializer),
            CommonsRecord::SiblingDeclared(s) => s.serialize(serializer),
        }
    }
}

impl<'de> Deserialize<'de> for CommonsRecord {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> std::result::Result<Self, D::Error> {
        let v = serde_json::Value::deserialize(deserializer)?;
        let t = v
            .get("type")
            .and_then(|x| x.as_str())
            .ok_or_else(|| serde::de::Error::missing_field("type"))?;
        match t {
            "room_registered" => {
                let r: RoomRegistered =
                    serde_json::from_value(v).map_err(serde::de::Error::custom)?;
                Ok(CommonsRecord::RoomRegistered(r))
            }
            "sibling_declared" => {
                let s: SiblingDeclared =
                    serde_json::from_value(v).map_err(serde::de::Error::custom)?;
                Ok(CommonsRecord::SiblingDeclared(s))
            }
            other => Err(serde::de::Error::unknown_variant(
                other,
                &["room_registered", "sibling_declared"],
            )),
        }
    }
}

impl CommonsRecord {
    pub fn hash(&self) -> Result<String> {
        match self {
            CommonsRecord::RoomRegistered(r) => hash::hash_of(r),
            CommonsRecord::SiblingDeclared(s) => hash::hash_of(s),
        }
    }
    pub fn prev(&self) -> Option<&String> {
        match self {
            CommonsRecord::RoomRegistered(r) => r.prev.as_ref(),
            CommonsRecord::SiblingDeclared(s) => s.prev.as_ref(),
        }
    }
    pub fn seq(&self) -> u64 {
        match self {
            CommonsRecord::RoomRegistered(r) => r.seq,
            CommonsRecord::SiblingDeclared(s) => s.seq,
        }
    }
    pub fn proof(&self) -> &ProofOrArray {
        match self {
            CommonsRecord::RoomRegistered(r) => &r.proof,
            CommonsRecord::SiblingDeclared(s) => &s.proof,
        }
    }
}

pub struct Commons {
    pub world_id: DidKey,
    keypair: Keypair,
    records: Vec<CommonsRecord>,
}

impl Commons {
    pub fn new(keypair: Keypair) -> Self {
        let world_id = keypair.did();
        Commons { world_id, keypair, records: Vec::new() }
    }

    pub fn records(&self) -> &[CommonsRecord] {
        &self.records
    }

    pub fn log(&self) -> CommonsLog {
        CommonsLog {
            commons_id: self.world_id.clone(),
            records: self.records.clone(),
        }
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
        let seed_hash = room.records().first()
            .ok_or_else(|| Error::Policy("room has no seed".into()))?
            .hash()?;
        let mut rec = RoomRegistered {
            type_: "room_registered".into(),
            commons_id: self.world_id.clone(),
            seq, prev,
            room_id: room.world_id().clone(),
            topic: topic.unwrap_or_else(|| room.template().topic.clone()),
            template_hash: room.template().hash()?,
            room_seed_hash: seed_hash,
            registered_by: registrant_kp.did(),
            also_listed_in: Vec::new(),
            ts: crate::now(),
            proof: ProofOrArray::placeholder(),
        };
        let body = hash::body_for_signing(&rec)?;
        let reg_sig = registrant_kp.sign(&body);
        let commons_sig = self.keypair.sign(&body);
        rec.proof = ProofOrArray::array(vec![
            Proof::create(registrant_kp, &reg_sig),
            Proof::create(&self.keypair, &commons_sig),
        ]);
        self.records.push(CommonsRecord::RoomRegistered(rec.clone()));
        Ok(rec)
    }

    /// Record a sibling declaration in the Commons. Signed by
    /// parent + sibling + Commons. The shard_hash must name a
    /// KnowledgeShardExport record in the parent's KnowledgeWorld;
    /// the crate cannot verify that cross-reference (it's a
    /// reader-side check when both logs are available), so the
    /// hash is taken on faith here.
    pub fn declare_sibling(
        &mut self,
        parent_kp: &Keypair,
        sibling_kp: &Keypair,
        parent_kw_id: &DidKey,
        shard_hash: &str,
        purpose: &str,
    ) -> Result<SiblingDeclared> {
        if parent_kp.did() == sibling_kp.did() {
            return Err(Error::Policy("parent == sibling".into()));
        }
        if shard_hash.len() != 64 || !shard_hash.chars().all(|c| c.is_ascii_hexdigit()) {
            return Err(Error::Policy("shard_hash must be 64 hex chars".into()));
        }
        let seq = self.records.len() as u64;
        let prev = match self.records.last() {
            Some(r) => Some(r.hash()?),
            None => None,
        };
        let mut rec = SiblingDeclared {
            type_: "sibling_declared".into(),
            commons_id: self.world_id.clone(),
            seq, prev,
            parent_id: parent_kp.did(),
            sibling_id: sibling_kp.did(),
            parent_kw_id: parent_kw_id.clone(),
            shard_hash: shard_hash.into(),
            purpose: purpose.into(),
            ts: crate::now(),
            proof: ProofOrArray::placeholder(),
        };
        let body = hash::body_for_signing(&rec)?;
        let p_sig = parent_kp.sign(&body);
        let s_sig = sibling_kp.sign(&body);
        let c_sig = self.keypair.sign(&body);
        rec.proof = ProofOrArray::array(vec![
            Proof::create(parent_kp, &p_sig),
            Proof::create(sibling_kp, &s_sig),
            Proof::create(&self.keypair, &c_sig),
        ]);
        self.records.push(CommonsRecord::SiblingDeclared(rec.clone()));
        Ok(rec)
    }
}

pub fn verify_commons(commons: &Commons) -> Result<()> {
    verify_commons_log(&commons.log())
}

pub fn verify_commons_log(log: &CommonsLog) -> Result<()> {
    let mut prev: Option<String> = None;
    for (i, rec) in log.records.iter().enumerate() {
        match rec {
            CommonsRecord::RoomRegistered(r) => {
                if r.type_ != "room_registered" {
                    return Err(Error::Verification(format!("record {i}: bad type")));
                }
                if r.commons_id != log.commons_id {
                    return Err(Error::Verification(format!("record {i}: commons_id mismatch")));
                }
                if r.prev != prev {
                    return Err(Error::Chain(format!("record {i}: prev mismatch")));
                }
                let body = hash::body_for_signing(r)?;
                let reg = r.proof.find_by_method(&r.registered_by)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing registrant proof")))?;
                reg.verify(&body)?;
                let com = r.proof.find_by_method(&log.commons_id)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing commons proof")))?;
                com.verify(&body)?;
            }
            CommonsRecord::SiblingDeclared(s) => {
                if s.type_ != "sibling_declared" {
                    return Err(Error::Verification(format!("record {i}: bad type")));
                }
                if s.commons_id != log.commons_id {
                    return Err(Error::Verification(format!("record {i}: commons_id mismatch")));
                }
                if s.prev != prev {
                    return Err(Error::Chain(format!("record {i}: prev mismatch")));
                }
                if s.parent_id == s.sibling_id {
                    return Err(Error::Policy(format!("record {i}: parent == sibling")));
                }
                if s.shard_hash.len() != 64 || !s.shard_hash.chars().all(|c| c.is_ascii_hexdigit()) {
                    return Err(Error::Policy(format!("record {i}: bad shard_hash")));
                }
                let body = hash::body_for_signing(s)?;
                let p = s.proof.find_by_method(&s.parent_id)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing parent proof")))?;
                p.verify(&body)?;
                let sib = s.proof.find_by_method(&s.sibling_id)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing sibling proof")))?;
                sib.verify(&body)?;
                let com = s.proof.find_by_method(&log.commons_id)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing commons proof")))?;
                com.verify(&body)?;
            }
        }
        prev = Some(rec.hash()?);
    }
    Ok(())
}
