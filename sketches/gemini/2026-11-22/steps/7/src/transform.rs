//! Transformation World over the six-line binary carrier H = {0, 1}^6 (EX03).
//!
//! Turns group actions, sequence inversion, orbit equivalence, and exhaustive
//! invariant checks into a playable, dual-signed, offline-verifiable world.

use crate::did::{DidKey, Keypair};
use crate::error::{Error, Result};
use crate::hash::{body_for_signing, hash_of};
use crate::proof::{Proof, ProofOrArray};
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet, VecDeque};

/// A six-bit binary configuration (x_1, ..., x_6) in bottom-to-top order.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct HexWord([u8; 6]);

impl HexWord {
    pub fn new(bits: [u8; 6]) -> Result<Self> {
        if bits.iter().any(|&b| b > 1) {
            return Err(Error::Policy("hex word bits must each be 0 or 1".into()));
        }
        Ok(HexWord(bits))
    }

    pub fn parse(s: &str) -> Result<Self> {
        let bytes = s.as_bytes();
        if bytes.len() != 6 {
            return Err(Error::Serialization(format!(
                "hex word must be exactly 6 bits, got {:?}",
                s
            )));
        }
        let mut bits = [0u8; 6];
        for (i, &b) in bytes.iter().enumerate() {
            match b {
                b'0' => bits[i] = 0,
                b'1' => bits[i] = 1,
                _ => {
                    return Err(Error::Serialization(format!(
                        "hex word contains non-binary character in {:?}",
                        s
                    )));
                }
            }
        }
        Ok(HexWord(bits))
    }

    /// Returns all 64 words of H = {0, 1}^6 in exact lexicographic order.
    pub fn all() -> Vec<HexWord> {
        let mut out = Vec::with_capacity(64);
        for idx in 0u8..64 {
            let bits = [
                (idx >> 5) & 1,
                (idx >> 4) & 1,
                (idx >> 3) & 1,
                (idx >> 2) & 1,
                (idx >> 1) & 1,
                idx & 1,
            ];
            out.push(HexWord(bits));
        }
        out
    }

    pub fn bits(&self) -> [u8; 6] {
        self.0
    }

    pub fn as_bit_string(&self) -> String {
        self.0
            .iter()
            .map(|&b| if b == 0 { '0' } else { '1' })
            .collect()
    }

    /// Number of ones n(x) in [0, 6].
    pub fn weight(&self) -> u8 {
        self.0.iter().sum()
    }

    /// Unordered pair {n(x), 6 - n(x)}, sorted as (min, max).
    pub fn weight_pair(&self) -> (u8, u8) {
        let w = self.weight();
        let c = 6 - w;
        if w <= c {
            (w, c)
        } else {
            (c, w)
        }
    }

    /// Hamming distance d_H(x, y) = sum_i |x_i - y_i|.
    pub fn hamming_distance(&self, other: HexWord) -> u8 {
        let mut dist = 0u8;
        for i in 0..6 {
            if self.0[i] != other.0[i] {
                dist += 1;
            }
        }
        dist
    }
}

impl std::fmt::Display for HexWord {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.as_bit_string())
    }
}

impl Serialize for HexWord {
    fn serialize<S: Serializer>(&self, s: S) -> std::result::Result<S::Ok, S::Error> {
        s.serialize_str(&self.as_bit_string())
    }
}

impl<'de> Deserialize<'de> for HexWord {
    fn deserialize<D: Deserializer<'de>>(d: D) -> std::result::Result<Self, D::Error> {
        let s = String::deserialize(d)?;
        HexWord::parse(&s).map_err(serde::de::Error::custom)
    }
}

/// Elementary total bijections on H = {0, 1}^6.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Op {
    /// id(x) = x
    Identity,
    /// C(x) = (1 - x_1, ..., 1 - x_6)
    Complement,
    /// R(x) = (x_6, x_5, x_4, x_3, x_2, x_1)
    Reverse,
    /// S(x) = (x_4, x_5, x_6, x_1, x_2, x_3) = T^3(x)
    SwapTrigrams,
    /// T(x) = (x_6, x_1, x_2, x_3, x_4, x_5)
    Rotate,
    /// T^-1(x) = (x_2, x_3, x_4, x_5, x_6, x_1)
    RotateInverse,
}

impl Op {
    pub fn apply(self, w: HexWord) -> HexWord {
        let b = w.0;
        match self {
            Op::Identity => w,
            Op::Complement => HexWord([
                1 - b[0],
                1 - b[1],
                1 - b[2],
                1 - b[3],
                1 - b[4],
                1 - b[5],
            ]),
            Op::Reverse => HexWord([b[5], b[4], b[3], b[2], b[1], b[0]]),
            Op::SwapTrigrams => HexWord([b[3], b[4], b[5], b[0], b[1], b[2]]),
            Op::Rotate => HexWord([b[5], b[0], b[1], b[2], b[3], b[4]]),
            Op::RotateInverse => HexWord([b[1], b[2], b[3], b[4], b[5], b[0]]),
        }
    }

    pub fn inverse(self) -> Op {
        match self {
            Op::Rotate => Op::RotateInverse,
            Op::RotateInverse => Op::Rotate,
            other => other,
        }
    }
}

/// Applies operations in execution order (first element acts first).
pub fn apply_sequence(mut word: HexWord, ops: &[Op]) -> HexWord {
    for &op in ops {
        word = op.apply(word);
    }
    word
}

/// Computes the exact inverse sequence: (g ∘ f)^-1 = f^-1 ∘ g^-1.
pub fn invert_sequence(ops: &[Op]) -> Vec<Op> {
    ops.iter().rev().map(|op| op.inverse()).collect()
}

/// Computes the full orbit of `start` under `generators`.
/// Because every `Op` is a finite-order bijection on H, forward closure
/// equals the full generated subgroup orbit.
pub fn orbit_under(start: HexWord, generators: &[Op]) -> BTreeSet<HexWord> {
    let mut visited = BTreeSet::new();
    let mut queue = VecDeque::new();
    visited.insert(start);
    queue.push_back(start);

    while let Some(cur) = queue.pop_front() {
        for &op in generators {
            let next = op.apply(cur);
            if visited.insert(next) {
                queue.push_back(next);
            }
        }
    }
    visited
}

/// Lexicographically least representative of `word`'s orbit under `generators`.
pub fn canonical_rep(word: HexWord, generators: &[Op]) -> HexWord {
    *orbit_under(word, generators).iter().next().unwrap()
}

/// Partitions all 64 words of H into disjoint orbits under `generators`,
/// ordered by each orbit's lexicographically least representative.
pub fn partition_orbits(generators: &[Op]) -> Vec<BTreeSet<HexWord>> {
    let mut seen = BTreeSet::new();
    let mut orbits = Vec::new();
    for w in HexWord::all() {
        if !seen.contains(&w) {
            let orb = orbit_under(w, generators);
            for &member in &orb {
                seen.insert(member);
            }
            orbits.push(orb);
        }
    }
    orbits
}

/// Shortest sequence of explicitly `admitted_ops` transforming `start` into `target`.
pub fn shortest_path(start: HexWord, target: HexWord, admitted_ops: &[Op]) -> Option<Vec<Op>> {
    if start == target {
        return Some(Vec::new());
    }
    let mut parent: HashMap<HexWord, (HexWord, Op)> = HashMap::new();
    let mut visited: HashSet<HexWord> = HashSet::new();
    let mut queue = VecDeque::new();
    visited.insert(start);
    queue.push_back(start);

    while let Some(cur) = queue.pop_front() {
        for &op in admitted_ops {
            let next = op.apply(cur);
            if visited.insert(next) {
                parent.insert(next, (cur, op));
                if next == target {
                    let mut path = Vec::new();
                    let mut node = target;
                    while let Some(&(prev, used_op)) = parent.get(&node) {
                        path.push(used_op);
                        node = prev;
                    }
                    path.reverse();
                    return Some(path);
                }
                queue.push_back(next);
            }
        }
    }
    None
}

// =====================================================================
// MACHINE-CHECKED INVARIANT CONJECTURES
// =====================================================================

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "claim_kind", rename_all = "snake_case")]
pub enum InvariantClaim {
    SameOrbit { a: HexWord, b: HexWord },
    FixedPoint { word: HexWord, op: Op },
    PreservesWeight { op: Op },
    PreservesWeightPair { op: Op },
    PreservesHammingDistance { op: Op },
    WeightPairClassifiesOrbits,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ClaimEvaluation {
    pub holds: bool,
    pub witness: String,
}

pub fn evaluate_claim(claim: &InvariantClaim, admitted_ops: &[Op]) -> ClaimEvaluation {
    match claim {
        InvariantClaim::SameOrbit { a, b } => match shortest_path(*a, *b, admitted_ops) {
            Some(path) => ClaimEvaluation {
                holds: true,
                witness: format!("reachable in {} admitted step(s)", path.len()),
            },
            None => {
                let rep_a = canonical_rep(*a, admitted_ops);
                let rep_b = canonical_rep(*b, admitted_ops);
                ClaimEvaluation {
                    holds: false,
                    witness: format!("distinct orbit representatives {} vs {}", rep_a, rep_b),
                }
            }
        },
        InvariantClaim::FixedPoint { word, op } => {
            let img = op.apply(*word);
            if img == *word {
                ClaimEvaluation {
                    holds: true,
                    witness: format!("{:?}({}) = {}", op, word, img),
                }
            } else {
                ClaimEvaluation {
                    holds: false,
                    witness: format!("{:?}({}) = {} != {}", op, word, img, word),
                }
            }
        }
        InvariantClaim::PreservesWeight { op } => {
            for w in HexWord::all() {
                let img = op.apply(w);
                if img.weight() != w.weight() {
                    return ClaimEvaluation {
                        holds: false,
                        witness: format!(
                            "counterexample {} (weight {}) -> {} (weight {})",
                            w,
                            w.weight(),
                            img,
                            img.weight()
                        ),
                    };
                }
            }
            ClaimEvaluation {
                holds: true,
                witness: "verified across all 64 words".into(),
            }
        }
        InvariantClaim::PreservesWeightPair { op } => {
            for w in HexWord::all() {
                let img = op.apply(w);
                if img.weight_pair() != w.weight_pair() {
                    return ClaimEvaluation {
                        holds: false,
                        witness: format!(
                            "counterexample {} ({:?}) -> {} ({:?})",
                            w,
                            w.weight_pair(),
                            img,
                            img.weight_pair()
                        ),
                    };
                }
            }
            ClaimEvaluation {
                holds: true,
                witness: "verified across all 64 words".into(),
            }
        }
        InvariantClaim::PreservesHammingDistance { op } => {
            let all = HexWord::all();
            for &x in &all {
                let ox = op.apply(x);
                for &y in &all {
                    let oy = op.apply(y);
                    let d_before = x.hamming_distance(y);
                    let d_after = ox.hamming_distance(oy);
                    if d_before != d_after {
                        return ClaimEvaluation {
                            holds: false,
                            witness: format!(
                                "counterexample d({}, {}) = {} != d({}, {}) = {}",
                                x, y, d_before, ox, oy, d_after
                            ),
                        };
                    }
                }
            }
            ClaimEvaluation {
                holds: true,
                witness: "verified across all 4096 word pairs".into(),
            }
        }
        InvariantClaim::WeightPairClassifiesOrbits => {
            let orbits = partition_orbits(admitted_ops);
            let mut by_pair: BTreeMap<(u8, u8), HexWord> = BTreeMap::new();
            for orb in orbits {
                let rep = *orb.iter().next().unwrap();
                let wp = rep.weight_pair();
                if let Some(prev_rep) = by_pair.insert(wp, rep) {
                    return ClaimEvaluation {
                        holds: false,
                        witness: format!(
                            "counterexample {} and {} share weight pair {:?} in distinct orbits",
                            prev_rep, rep, wp
                        ),
                    };
                }
            }
            ClaimEvaluation {
                holds: true,
                witness: "weight pair uniquely identifies every orbit".into(),
            }
        }
    }
}

// =====================================================================
// TRANSFORMATION WORLD LAW, RECORDS, ARTIFACTS, AND LOG VERIFIER
// =====================================================================

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TransformLaw {
    pub topic: String,
    pub admitted_ops: Vec<Op>,
    pub initial_word: HexWord,
    pub target_word: Option<HexWord>,
}

impl TransformLaw {
    pub fn validate(&self) -> Result<()> {
        if self.topic.trim().is_empty() {
            return Err(Error::Policy("transform law: topic cannot be empty".into()));
        }
        if self.admitted_ops.is_empty() {
            return Err(Error::Policy(
                "transform law: must admit at least one operation".into(),
            ));
        }
        let mut seen = HashSet::new();
        for &op in &self.admitted_ops {
            if !seen.insert(op) {
                return Err(Error::Policy("transform law: duplicate admitted_ops".into()));
            }
        }
        Ok(())
    }

    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }
}

/// Portable artifact exported from a Transformation World for reuse in
/// Retelling Worlds, Pattern Cards, or Shared Library shelves.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TransformArtifact {
    pub world_id: DidKey,
    pub start_word: HexWord,
    pub sequence: Vec<Op>,
    pub end_word: HexWord,
    pub prompt_for_next_visitor: String,
    pub author: DidKey,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WorldOpened {
    pub world_id: DidKey,
    pub law: TransformLaw,
    pub creator_id: DidKey,
    pub ts: u64,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ParticipantJoined {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: String,
    pub participant_id: DidKey,
    pub ts: u64,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct MoveApplied {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: String,
    pub actor_id: DidKey,
    pub op: Op,
    pub prev_word: HexWord,
    pub next_word: HexWord,
    pub note: Option<String>,
    pub ts: u64,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct UndoSequenceApplied {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: String,
    pub actor_id: DidKey,
    pub count: u64,
    pub inverse_ops: Vec<Op>,
    pub prev_word: HexWord,
    pub next_word: HexWord,
    pub ts: u64,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct InvariantClaimChecked {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: String,
    pub proposer_id: DidKey,
    pub claim: InvariantClaim,
    pub evaluation: ClaimEvaluation,
    pub ts: u64,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ChallengeLeft {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: String,
    pub artifact: TransformArtifact,
    pub ts: u64,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum TransformRecord {
    WorldOpened(WorldOpened),
    ParticipantJoined(ParticipantJoined),
    MoveApplied(MoveApplied),
    UndoSequenceApplied(UndoSequenceApplied),
    InvariantClaimChecked(InvariantClaimChecked),
    ChallengeLeft(ChallengeLeft),
}

impl TransformRecord {
    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }

    pub fn seq(&self) -> u64 {
        match self {
            TransformRecord::WorldOpened(_) => 0,
            TransformRecord::ParticipantJoined(r) => r.seq,
            TransformRecord::MoveApplied(r) => r.seq,
            TransformRecord::UndoSequenceApplied(r) => r.seq,
            TransformRecord::InvariantClaimChecked(r) => r.seq,
            TransformRecord::ChallengeLeft(r) => r.seq,
        }
    }

    pub fn prev(&self) -> Option<&str> {
        match self {
            TransformRecord::WorldOpened(_) => None,
            TransformRecord::ParticipantJoined(r) => Some(&r.prev),
            TransformRecord::MoveApplied(r) => Some(&r.prev),
            TransformRecord::UndoSequenceApplied(r) => Some(&r.prev),
            TransformRecord::InvariantClaimChecked(r) => Some(&r.prev),
            TransformRecord::ChallengeLeft(r) => Some(&r.prev),
        }
    }

    pub fn world_id(&self) -> &DidKey {
        match self {
            TransformRecord::WorldOpened(r) => &r.world_id,
            TransformRecord::ParticipantJoined(r) => &r.world_id,
            TransformRecord::MoveApplied(r) => &r.world_id,
            TransformRecord::UndoSequenceApplied(r) => &r.world_id,
            TransformRecord::InvariantClaimChecked(r) => &r.world_id,
            TransformRecord::ChallengeLeft(r) => &r.world_id,
        }
    }

    pub fn proof(&self) -> &ProofOrArray {
        match self {
            TransformRecord::WorldOpened(r) => &r.proof,
            TransformRecord::ParticipantJoined(r) => &r.proof,
            TransformRecord::MoveApplied(r) => &r.proof,
            TransformRecord::UndoSequenceApplied(r) => &r.proof,
            TransformRecord::InvariantClaimChecked(r) => &r.proof,
            TransformRecord::ChallengeLeft(r) => &r.proof,
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TransformLog {
    pub world_id: DidKey,
    pub law: TransformLaw,
    pub records: Vec<TransformRecord>,
}

fn sign_transform_dual<T, F>(
    mut rec: T,
    actor: &Keypair,
    world: &Keypair,
    wrap: fn(T) -> TransformRecord,
    set_proof: F,
) -> Result<T>
where
    T: Clone,
    F: FnOnce(&mut T, ProofOrArray),
{
    let body = body_for_signing(&wrap(rec.clone()))?;
    let a_sig = actor.sign(&body);
    let w_sig = world.sign(&body);
    set_proof(
        &mut rec,
        ProofOrArray::array(vec![
            Proof::create(actor, &a_sig),
            Proof::create(world, &w_sig),
        ]),
    );
    Ok(rec)
}

/// Interactive Transformation World where participants collaboratively test
/// operations, undo sequences, verify invariants, and leave open challenges.
pub struct TransformationWorld {
    world_id: DidKey,
    law: TransformLaw,
    keypair: Keypair,
    participants: HashSet<DidKey>,
    current_word: HexWord,
    move_stack: Vec<Op>,
    records: Vec<TransformRecord>,
}

impl TransformationWorld {
    pub fn open(
        law: TransformLaw,
        world_kp: Keypair,
        creator_kp: &Keypair,
        now: u64,
    ) -> Result<Self> {
        law.validate()?;
        let world_id = world_kp.did();
        let creator_id = creator_kp.did();
        let opened = WorldOpened {
            world_id: world_id.clone(),
            law: law.clone(),
            creator_id: creator_id.clone(),
            ts: now,
            proof: ProofOrArray::placeholder(),
        };
        let signed = sign_transform_dual(
            opened,
            creator_kp,
            &world_kp,
            TransformRecord::WorldOpened,
            |r, p| r.proof = p,
        )?;
        let mut participants = HashSet::new();
        participants.insert(creator_id);
        let initial_word = law.initial_word;
        Ok(TransformationWorld {
            world_id,
            law,
            keypair: world_kp,
            participants,
            current_word: initial_word,
            move_stack: Vec::new(),
            records: vec![TransformRecord::WorldOpened(signed)],
        })
    }

    pub fn world_id(&self) -> &DidKey {
        &self.world_id
    }

    pub fn law(&self) -> &TransformLaw {
        &self.law
    }

    pub fn current_word(&self) -> HexWord {
        self.current_word
    }

    pub fn target_reached(&self) -> bool {
        self.law.target_word == Some(self.current_word)
    }

    pub fn log(&self) -> TransformLog {
        TransformLog {
            world_id: self.world_id.clone(),
            law: self.law.clone(),
            records: self.records.clone(),
        }
    }

    fn next_seq(&self) -> u64 {
        self.records.len() as u64
    }

    fn last_hash(&self) -> Result<String> {
        self.records
            .last()
            .ok_or_else(|| Error::Chain("transform world has no seed record".into()))?
            .hash()
    }

    pub fn join(&mut self, participant_kp: &Keypair, now: u64) -> Result<TransformRecord> {
        let pid = participant_kp.did();
        if self.participants.contains(&pid) {
            return Err(Error::Policy("participant already joined".into()));
        }
        let rec = ParticipantJoined {
            world_id: self.world_id.clone(),
            seq: self.next_seq(),
            prev: self.last_hash()?,
            participant_id: pid.clone(),
            ts: now,
            proof: ProofOrArray::placeholder(),
        };
        let signed = sign_transform_dual(
            rec,
            participant_kp,
            &self.keypair,
            TransformRecord::ParticipantJoined,
            |r, p| r.proof = p,
        )?;
        let wrapped = TransformRecord::ParticipantJoined(signed);
        self.participants.insert(pid);
        self.records.push(wrapped.clone());
        Ok(wrapped)
    }

    pub fn apply_move(
        &mut self,
        actor_kp: &Keypair,
        op: Op,
        note: Option<String>,
        now: u64,
    ) -> Result<TransformRecord> {
        let actor_id = actor_kp.did();
        if !self.participants.contains(&actor_id) {
            return Err(Error::Policy("actor is not a participant".into()));
        }
        if !self.law.admitted_ops.contains(&op) {
            return Err(Error::Policy(format!(
                "operation {:?} is not admitted by this world's law",
                op
            )));
        }
        let prev_word = self.current_word;
        let next_word = op.apply(prev_word);
        let rec = MoveApplied {
            world_id: self.world_id.clone(),
            seq: self.next_seq(),
            prev: self.last_hash()?,
            actor_id,
            op,
            prev_word,
            next_word,
            note,
            ts: now,
            proof: ProofOrArray::placeholder(),
        };
        let signed = sign_transform_dual(
            rec,
            actor_kp,
            &self.keypair,
            TransformRecord::MoveApplied,
            |r, p| r.proof = p,
        )?;
        let wrapped = TransformRecord::MoveApplied(signed);
        self.current_word = next_word;
        self.move_stack.push(op);
        self.records.push(wrapped.clone());
        Ok(wrapped)
    }

    /// Undoes the last `count` applied moves by applying their exact inverse
    /// sequence `(g ∘ f)^-1 = f^-1 ∘ g^-1`. Refuses if any required inverse
    /// operation is not admitted by the world's law.
    pub fn undo_last(
        &mut self,
        actor_kp: &Keypair,
        count: u64,
        now: u64,
    ) -> Result<TransformRecord> {
        let actor_id = actor_kp.did();
        if !self.participants.contains(&actor_id) {
            return Err(Error::Policy("actor is not a participant".into()));
        }
        if count == 0 || (count as usize) > self.move_stack.len() {
            return Err(Error::Policy("invalid undo count for move stack".into()));
        }
        let split_at = self.move_stack.len() - (count as usize);
        let to_undo = &self.move_stack[split_at..];
        let inverse_ops = invert_sequence(to_undo);
        for &inv_op in &inverse_ops {
            if !self.law.admitted_ops.contains(&inv_op) {
                return Err(Error::Policy(format!(
                    "inverse operation {:?} is not admitted by this world's law",
                    inv_op
                )));
            }
        }
        let prev_word = self.current_word;
        let next_word = apply_sequence(prev_word, &inverse_ops);

        let rec = UndoSequenceApplied {
            world_id: self.world_id.clone(),
            seq: self.next_seq(),
            prev: self.last_hash()?,
            actor_id,
            count,
            inverse_ops,
            prev_word,
            next_word,
            ts: now,
            proof: ProofOrArray::placeholder(),
        };
        let signed = sign_transform_dual(
            rec,
            actor_kp,
            &self.keypair,
            TransformRecord::UndoSequenceApplied,
            |r, p| r.proof = p,
        )?;
        let wrapped = TransformRecord::UndoSequenceApplied(signed);
        self.move_stack.truncate(split_at);
        self.current_word = next_word;
        self.records.push(wrapped.clone());
        Ok(wrapped)
    }

    /// Tests a formal invariant conjecture against the world's law and records
    /// the deterministic verdict plus witness or counterexample.
    pub fn check_claim(
        &mut self,
        proposer_kp: &Keypair,
        claim: InvariantClaim,
        now: u64,
    ) -> Result<ClaimEvaluation> {
        let proposer_id = proposer_kp.did();
        if !self.participants.contains(&proposer_id) {
            return Err(Error::Policy("proposer is not a participant".into()));
        }
        let evaluation = evaluate_claim(&claim, &self.law.admitted_ops);
        let rec = InvariantClaimChecked {
            world_id: self.world_id.clone(),
            seq: self.next_seq(),
            prev: self.last_hash()?,
            proposer_id,
            claim,
            evaluation: evaluation.clone(),
            ts: now,
            proof: ProofOrArray::placeholder(),
        };
        let signed = sign_transform_dual(
            rec,
            proposer_kp,
            &self.keypair,
            TransformRecord::InvariantClaimChecked,
            |r, p| r.proof = p,
        )?;
        self.records
            .push(TransformRecord::InvariantClaimChecked(signed));
        Ok(evaluation)
    }

    /// Exports the current net move sequence as a signed, portable challenge
    /// artifact for later visitors or downstream worlds.
    pub fn leave_challenge(
        &mut self,
        author_kp: &Keypair,
        prompt_for_next_visitor: &str,
        now: u64,
    ) -> Result<TransformArtifact> {
        let author = author_kp.did();
        if !self.participants.contains(&author) {
            return Err(Error::Policy("author is not a participant".into()));
        }
        if prompt_for_next_visitor.trim().is_empty() {
            return Err(Error::Policy("challenge prompt cannot be empty".into()));
        }
        let artifact = TransformArtifact {
            world_id: self.world_id.clone(),
            start_word: self.law.initial_word,
            sequence: self.move_stack.clone(),
            end_word: self.current_word,
            prompt_for_next_visitor: prompt_for_next_visitor.to_string(),
            author,
        };
        let rec = ChallengeLeft {
            world_id: self.world_id.clone(),
            seq: self.next_seq(),
            prev: self.last_hash()?,
            artifact: artifact.clone(),
            ts: now,
            proof: ProofOrArray::placeholder(),
        };
        let signed = sign_transform_dual(
            rec,
            author_kp,
            &self.keypair,
            TransformRecord::ChallengeLeft,
            |r, p| r.proof = p,
        )?;
        self.records.push(TransformRecord::ChallengeLeft(signed));
        Ok(artifact)
    }
}

/// Independently replays and verifies an entire `TransformLog` offline.
pub fn verify_transform_log(log: &TransformLog) -> Result<()> {
    log.law.validate()?;
    let Some(TransformRecord::WorldOpened(seed)) = log.records.first() else {
        return Err(Error::Chain(
            "transform log must begin with world_opened".into(),
        ));
    };
    if seed.world_id != log.world_id {
        return Err(Error::Verification(
            "transform log: seed world_id mismatch".into(),
        ));
    }
    if seed.law.hash()? != log.law.hash()? {
        return Err(Error::Verification(
            "transform log: seed law does not match log law".into(),
        ));
    }

    let mut prev: Option<String> = None;
    let mut participants: HashSet<DidKey> = HashSet::new();
    let mut current_word = log.law.initial_word;
    let mut move_stack: Vec<Op> = Vec::new();

    for (i, rec) in log.records.iter().enumerate() {
        if rec.seq() != i as u64 {
            return Err(Error::Chain(format!(
                "transform log record {i}: seq {} != expected {i}",
                rec.seq()
            )));
        }
        if rec.world_id() != &log.world_id {
            return Err(Error::Verification(format!(
                "transform log record {i}: world_id mismatch"
            )));
        }
        match rec {
            TransformRecord::WorldOpened(_) => {
                if i != 0 {
                    return Err(Error::Chain(format!(
                        "transform log record {i}: world_opened not at start"
                    )));
                }
            }
            _ => {
                if rec.prev() != prev.as_deref() {
                    return Err(Error::Chain(format!(
                        "transform log record {i}: prev hash mismatch"
                    )));
                }
            }
        }

        let body = body_for_signing(rec)?;
        let world_proof = rec
            .proof()
            .find_by_method(&log.world_id)
            .ok_or_else(|| Error::Verification(format!("record {i}: missing world proof")))?;
        world_proof.verify(&body)?;

        match rec {
            TransformRecord::WorldOpened(r) => {
                let cp = r
                    .proof
                    .find_by_method(&r.creator_id)
                    .ok_or_else(|| Error::Verification("seed: missing creator proof".into()))?;
                cp.verify(&body)?;
                participants.insert(r.creator_id.clone());
            }
            TransformRecord::ParticipantJoined(r) => {
                if !participants.insert(r.participant_id.clone()) {
                    return Err(Error::Policy(format!(
                        "record {i}: participant already joined"
                    )));
                }
                let pp = r.proof.find_by_method(&r.participant_id).ok_or_else(|| {
                    Error::Verification(format!("record {i}: missing participant proof"))
                })?;
                pp.verify(&body)?;
            }
            TransformRecord::MoveApplied(r) => {
                if !participants.contains(&r.actor_id) {
                    return Err(Error::Policy(format!("record {i}: actor not a participant")));
                }
                if !log.law.admitted_ops.contains(&r.op) {
                    return Err(Error::Policy(format!(
                        "record {i}: operation {:?} not admitted by law",
                        r.op
                    )));
                }
                if r.prev_word != current_word {
                    return Err(Error::Verification(format!(
                        "record {i}: prev_word {} != expected {}",
                        r.prev_word, current_word
                    )));
                }
                let expected_next = r.op.apply(current_word);
                if r.next_word != expected_next {
                    return Err(Error::Verification(format!(
                        "record {i}: next_word {} != expected {}",
                        r.next_word, expected_next
                    )));
                }
                let ap = r
                    .proof
                    .find_by_method(&r.actor_id)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing actor proof")))?;
                ap.verify(&body)?;
                current_word = expected_next;
                move_stack.push(r.op);
            }
            TransformRecord::UndoSequenceApplied(r) => {
                if !participants.contains(&r.actor_id) {
                    return Err(Error::Policy(format!("record {i}: actor not a participant")));
                }
                if r.count == 0 || (r.count as usize) > move_stack.len() {
                    return Err(Error::Policy(format!("record {i}: invalid undo count")));
                }
                let split_at = move_stack.len() - (r.count as usize);
                let expected_inv = invert_sequence(&move_stack[split_at..]);
                if r.inverse_ops != expected_inv {
                    return Err(Error::Verification(format!(
                        "record {i}: inverse_ops does not match reverse-inverted move stack"
                    )));
                }
                for &inv_op in &r.inverse_ops {
                    if !log.law.admitted_ops.contains(&inv_op) {
                        return Err(Error::Policy(format!(
                            "record {i}: inverse op {:?} not admitted by law",
                            inv_op
                        )));
                    }
                }
                if r.prev_word != current_word {
                    return Err(Error::Verification(format!(
                        "record {i}: undo prev_word mismatch"
                    )));
                }
                let expected_next = apply_sequence(current_word, &r.inverse_ops);
                if r.next_word != expected_next {
                    return Err(Error::Verification(format!(
                        "record {i}: undo next_word mismatch"
                    )));
                }
                let ap = r
                    .proof
                    .find_by_method(&r.actor_id)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing actor proof")))?;
                ap.verify(&body)?;
                move_stack.truncate(split_at);
                current_word = expected_next;
            }
            TransformRecord::InvariantClaimChecked(r) => {
                if !participants.contains(&r.proposer_id) {
                    return Err(Error::Policy(format!(
                        "record {i}: proposer not a participant"
                    )));
                }
                let expected_eval = evaluate_claim(&r.claim, &log.law.admitted_ops);
                if r.evaluation != expected_eval {
                    return Err(Error::Verification(format!(
                        "record {i}: claim evaluation does not match deterministic check"
                    )));
                }
                let pp = r.proof.find_by_method(&r.proposer_id).ok_or_else(|| {
                    Error::Verification(format!("record {i}: missing proposer proof"))
                })?;
                pp.verify(&body)?;
            }
            TransformRecord::ChallengeLeft(r) => {
                if !participants.contains(&r.artifact.author) {
                    return Err(Error::Policy(format!(
                        "record {i}: challenge author not a participant"
                    )));
                }
                if r.artifact.world_id != log.world_id
                    || r.artifact.start_word != log.law.initial_word
                    || r.artifact.sequence != move_stack
                    || r.artifact.end_word != current_word
                {
                    return Err(Error::Verification(format!(
                        "record {i}: challenge artifact does not match world state"
                    )));
                }
                let ap = r.proof.find_by_method(&r.artifact.author).ok_or_else(|| {
                    Error::Verification(format!("record {i}: missing author proof"))
                })?;
                ap.verify(&body)?;
            }
        }

        prev = Some(rec.hash()?);
    }

    Ok(())
}
