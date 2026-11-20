use crate::did::DidKey;
use crate::error::Result;
use crate::proof::ProofOrArray;
use crate::template::RoomTemplate;
use serde::{Deserialize, Serialize};

pub const TIERS: [&str; 4] = ["observe", "communicate", "control", "terminal"];

pub fn tier_rank(t: &str) -> Option<u8> {
    TIERS.iter().position(|x| *x == t).map(|i| i as u8)
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum Record {
    RoomCreated(RoomCreated),
    Message(Message),
    Join(Join),
    Leave(Leave),
    Redact(Redact),
    Refusal(Refusal),
    HumanOverride(HumanOverride),
    PortLanding(PortLanding),
    Bookmark(Bookmark),
    Presence(Presence),
}

impl Record {
    pub fn hash(&self) -> Result<String> { crate::hash::hash_of(self) }
    pub fn seq(&self) -> u64 {
        match self {
            Record::RoomCreated(_) => 0,
            Record::Message(m) => m.seq,
            Record::Join(j) => j.seq,
            Record::Leave(l) => l.seq,
            Record::Redact(r) => r.seq,
            Record::Refusal(r) => r.seq,
            Record::HumanOverride(o) => o.seq,
            Record::PortLanding(p) => p.seq,
            Record::Bookmark(b) => b.seq,
            Record::Presence(p) => p.seq,
        }
    }
    pub fn prev(&self) -> Option<&String> {
        match self {
            Record::RoomCreated(_) => None,
            Record::Message(m) => m.prev.as_ref(),
            Record::Join(j) => j.prev.as_ref(),
            Record::Leave(l) => l.prev.as_ref(),
            Record::Redact(r) => r.prev.as_ref(),
            Record::Refusal(r) => r.prev.as_ref(),
            Record::HumanOverride(o) => o.prev.as_ref(),
            Record::PortLanding(p) => p.prev.as_ref(),
            Record::Bookmark(b) => b.prev.as_ref(),
            Record::Presence(p) => p.prev.as_ref(),
        }
    }
    pub fn proof(&self) -> &ProofOrArray {
        match self {
            Record::RoomCreated(r) => &r.proof,
            Record::Message(m) => &m.proof,
            Record::Join(j) => &j.proof,
            Record::Leave(l) => &l.proof,
            Record::Redact(r) => &r.proof,
            Record::Refusal(r) => &r.proof,
            Record::HumanOverride(o) => &o.proof,
            Record::PortLanding(p) => &p.proof,
            Record::Bookmark(b) => &b.proof,
            Record::Presence(p) => &p.proof,
        }
    }
    pub fn world_id(&self) -> &DidKey {
        match self {
            Record::RoomCreated(r) => &r.world_id,
            Record::Message(m) => &m.world_id,
            Record::Join(j) => &j.world_id,
            Record::Leave(l) => &l.world_id,
            Record::Redact(r) => &r.world_id,
            Record::Refusal(r) => &r.world_id,
            Record::HumanOverride(o) => &o.world_id,
            Record::PortLanding(p) => &p.world_id,
            Record::Bookmark(b) => &b.world_id,
            Record::Presence(p) => &p.world_id,
        }
    }
    pub fn author_id(&self) -> Option<&DidKey> {
        match self {
            Record::Message(m) => Some(&m.author_id),
            Record::Redact(r) => Some(&r.subject_id),
            Record::Join(j) => Some(&j.subject_id),
            Record::Leave(l) => Some(&l.subject_id),
            Record::HumanOverride(o) => Some(&o.overridden_by),
            Record::RoomCreated(r) => Some(&r.creator_id),
            Record::Refusal(_) => None,
            Record::PortLanding(_) => None,
            Record::Bookmark(_) => None,
            Record::Presence(_) => None,
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct RoomCreated {
    pub world_id: DidKey,
    pub template: RoomTemplate,
    pub creator_id: DidKey,
    pub ts: String,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Message {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: Option<String>,
    pub author_id: DidKey,
    pub text: String,
    pub kind: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub in_reply_to: Option<String>,
    pub ts: String,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Join {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: Option<String>,
    pub subject_id: DidKey,
    pub tier: String,
    pub is_ai: bool,
    pub ts: String,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Leave {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: Option<String>,
    pub subject_id: DidKey,
    pub ts: String,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Redact {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: Option<String>,
    pub subject_id: DidKey,
    pub target_hash: String,
    pub actor_role: String,   // "author" | "moderator" (| "keeper" future)
    pub rule: String,         // must be in template.redaction_rules
    pub reason: String,
    pub ts: String,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Refusal {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: Option<String>,
    pub request_hash: String,
    pub requester_id: DidKey,
    pub reason: String,
    pub ts: String,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct HumanOverride {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: Option<String>,
    pub overrides_hash: String,
    pub overridden_by: DidKey,
    pub action: String,   // "none" | "restore"
    pub reason: String,
    pub ts: String,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PortLanding {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: Option<String>,
    pub transcript: crate::transcript::Transcript,
    pub intent: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub target_room: Option<DidKey>,
    pub ts: String,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Bookmark {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: Option<String>,
    pub room_id: DidKey,
    pub note: String,
    pub ts: String,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Presence {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: Option<String>,
    pub subject_id: DidKey,
    pub rooms: Vec<DidKey>,
    pub ttl: u64,
    pub ts: String,
    pub proof: ProofOrArray,
}

// ---- Constructors ----

impl RoomCreated {
    pub fn new(world_id: DidKey, template: RoomTemplate, creator_id: DidKey) -> Self {
        RoomCreated { world_id, template, creator_id, ts: crate::now(), proof: ProofOrArray::placeholder() }
    }
}
impl Message {
    pub fn new(world_id: DidKey, seq: u64, prev: Option<String>, author_id: DidKey, text: String, kind: String) -> Self {
        Message { world_id, seq, prev, author_id, text, kind, in_reply_to: None, ts: crate::now(), proof: ProofOrArray::placeholder() }
    }
}
impl Join {
    pub fn new(world_id: DidKey, seq: u64, prev: Option<String>, subject_id: DidKey, tier: String, is_ai: bool) -> Self {
        Join { world_id, seq, prev, subject_id, tier, is_ai, ts: crate::now(), proof: ProofOrArray::placeholder() }
    }
}
impl Leave {
    pub fn new(world_id: DidKey, seq: u64, prev: Option<String>, subject_id: DidKey) -> Self {
        Leave { world_id, seq, prev, subject_id, ts: crate::now(), proof: ProofOrArray::placeholder() }
    }
}
impl Redact {
    pub fn new(
        world_id: DidKey, seq: u64, prev: Option<String>,
        subject_id: DidKey, target_hash: String,
        actor_role: String, rule: String, reason: String,
    ) -> Self {
        Redact {
            world_id, seq, prev, subject_id, target_hash,
            actor_role, rule, reason,
            ts: crate::now(), proof: ProofOrArray::placeholder(),
        }
    }
}
impl Refusal {
    pub fn new(world_id: DidKey, seq: u64, prev: Option<String>, request_hash: String, requester_id: DidKey, reason: String) -> Self {
        Refusal { world_id, seq, prev, request_hash, requester_id, reason, ts: crate::now(), proof: ProofOrArray::placeholder() }
    }
}
impl HumanOverride {
    pub fn new(world_id: DidKey, seq: u64, prev: Option<String>, overrides_hash: String, overridden_by: DidKey, action: String, reason: String) -> Self {
        HumanOverride { world_id, seq, prev, overrides_hash, overridden_by, action, reason, ts: crate::now(), proof: ProofOrArray::placeholder() }
    }
}
impl PortLanding {
    pub fn new(world_id: DidKey, seq: u64, prev: Option<String>, transcript: crate::transcript::Transcript, intent: String, target_room: Option<DidKey>) -> Self {
        PortLanding { world_id, seq, prev, transcript, intent, target_room, ts: crate::now(), proof: ProofOrArray::placeholder() }
    }
}
impl Bookmark {
    pub fn new(world_id: DidKey, seq: u64, prev: Option<String>, room_id: DidKey, note: String) -> Self {
        Bookmark { world_id, seq, prev, room_id, note, ts: crate::now(), proof: ProofOrArray::placeholder() }
    }
}
impl Presence {
    pub fn new(world_id: DidKey, seq: u64, prev: Option<String>, subject_id: DidKey, rooms: Vec<DidKey>, ttl: u64) -> Self {
        Presence { world_id, seq, prev, subject_id, rooms, ttl, ts: crate::now(), proof: ProofOrArray::placeholder() }
    }
}
