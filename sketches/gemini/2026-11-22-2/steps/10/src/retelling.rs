//! Retelling World: cross-medium transformation chains, explicit preservation
//! and loss accounts, branching comparisons, and bidirectional lineage queries.

use crate::did::{DidKey, Keypair};
use crate::error::{Error, Result};
use crate::hash::{body_for_signing, hash_of, sha256_hex};
use crate::proof::{Proof, ProofOrArray};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet, VecDeque};

fn looks_like_hash(s: &str) -> bool {
    s.len() == 64 && s.chars().all(|c| c.is_ascii_hexdigit())
}

#[derive(Clone, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(tag = "medium", rename_all = "snake_case")]
pub enum Medium {
    Poem,
    ProseScene,
    VisualPattern,
    MusicalScore,
    RelationDiagram,
    WorldTemplate,
    Custom { name: String },
}

impl Medium {
    pub fn validate(&self) -> Result<()> {
        if let Medium::Custom { name } = self {
            if name.trim().is_empty() {
                return Err(Error::Policy("custom medium name cannot be empty".into()));
            }
        }
        Ok(())
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "policy", rename_all = "snake_case")]
pub enum MediumPolicy {
    Any,
    Restricted { allowed: Vec<Medium> },
}

impl MediumPolicy {
    pub fn validate(&self) -> Result<()> {
        if let MediumPolicy::Restricted { allowed } = self {
            if allowed.is_empty() {
                return Err(Error::Policy(
                    "restricted medium policy must allow at least one medium".into(),
                ));
            }
            for m in allowed {
                m.validate()?;
            }
        }
        Ok(())
    }

    pub fn permits(&self, medium: &Medium) -> bool {
        match self {
            MediumPolicy::Any => true,
            MediumPolicy::Restricted { allowed } => allowed.contains(medium),
        }
    }
}

/// Distinguishes a work created natively inside this room from an external
/// artifact carried in from another world (such as a Transformation World).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "origin", rename_all = "snake_case")]
pub enum SourceOrigin {
    NativeSeed,
    ImportedArtifact {
        source_world_id: DidKey,
        artifact_hash: String,
        label: String,
    },
}

impl SourceOrigin {
    pub fn validate(&self) -> Result<()> {
        if let SourceOrigin::ImportedArtifact {
            artifact_hash,
            label,
            ..
        } = self
        {
            if !looks_like_hash(artifact_hash) {
                return Err(Error::Policy(
                    "imported artifact_hash must be 64 hex chars".into(),
                ));
            }
            if label.trim().is_empty() {
                return Err(Error::Policy(
                    "imported artifact label cannot be empty".into(),
                ));
            }
        }
        Ok(())
    }
}

/// Attributable account attached to every retelling step, separating what
/// came from the source from what this interpreter altered or contributed.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TransformationAccount {
    pub preserved: Vec<String>,
    pub changed: Vec<String>,
    pub hard_to_express: Vec<String>,
    pub added_by_interpreter: Vec<String>,
}

impl TransformationAccount {
    pub fn validate(&self, require_explicit_losses: bool) -> Result<()> {
        if self.preserved.is_empty() || self.preserved.iter().any(|s| s.trim().is_empty()) {
            return Err(Error::Policy(
                "transformation account must name at least one preserved element".into(),
            ));
        }
        if require_explicit_losses && self.hard_to_express.is_empty() {
            return Err(Error::Policy(
                "world law requires listing at least one hard_to_express element".into(),
            ));
        }
        Ok(())
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RetellingLaw {
    pub topic: String,
    pub medium_policy: MediumPolicy,
    pub require_explicit_losses: bool,
    pub allow_external_imports: bool,
}

impl RetellingLaw {
    pub fn validate(&self) -> Result<()> {
        if self.topic.trim().is_empty() {
            return Err(Error::Policy("retelling law: topic cannot be empty".into()));
        }
        self.medium_policy.validate()
    }

    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }
}

// =====================================================================
// LOG RECORDS
// =====================================================================

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WorldOpened {
    pub world_id: DidKey,
    pub law: RetellingLaw,
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
pub struct SeedAdded {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: String,
    pub node_id: String,
    pub origin: SourceOrigin,
    pub medium: Medium,
    pub title: String,
    pub audience: String,
    pub content: String,
    pub content_sha256: String,
    pub author_id: DidKey,
    pub ts: u64,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RetellingAdded {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: String,
    pub node_id: String,
    pub parent_node_hashes: Vec<String>,
    pub medium: Medium,
    pub title: String,
    pub audience: String,
    pub content: String,
    pub content_sha256: String,
    pub account: TransformationAccount,
    pub author_id: DidKey,
    pub ts: u64,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ComparisonRecorded {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: String,
    pub left_node_hash: String,
    pub right_node_hash: String,
    pub common_ancestor_hash: Option<String>,
    pub shared_elements: Vec<String>,
    pub divergences: Vec<String>,
    pub author_id: DidKey,
    pub ts: u64,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct InvitationLeft {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: String,
    pub anchor_node_hashes: Vec<String>,
    pub prompt: String,
    pub suggested_media: Vec<Medium>,
    pub author_id: DidKey,
    pub ts: u64,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum RetellingRecord {
    WorldOpened(WorldOpened),
    ParticipantJoined(ParticipantJoined),
    SeedAdded(SeedAdded),
    RetellingAdded(RetellingAdded),
    ComparisonRecorded(ComparisonRecorded),
    InvitationLeft(InvitationLeft),
}

impl RetellingRecord {
    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }

    pub fn seq(&self) -> u64 {
        match self {
            RetellingRecord::WorldOpened(_) => 0,
            RetellingRecord::ParticipantJoined(r) => r.seq,
            RetellingRecord::SeedAdded(r) => r.seq,
            RetellingRecord::RetellingAdded(r) => r.seq,
            RetellingRecord::ComparisonRecorded(r) => r.seq,
            RetellingRecord::InvitationLeft(r) => r.seq,
        }
    }

    pub fn prev(&self) -> Option<&str> {
        match self {
            RetellingRecord::WorldOpened(_) => None,
            RetellingRecord::ParticipantJoined(r) => Some(&r.prev),
            RetellingRecord::SeedAdded(r) => Some(&r.prev),
            RetellingRecord::RetellingAdded(r) => Some(&r.prev),
            RetellingRecord::ComparisonRecorded(r) => Some(&r.prev),
            RetellingRecord::InvitationLeft(r) => Some(&r.prev),
        }
    }

    pub fn world_id(&self) -> &DidKey {
        match self {
            RetellingRecord::WorldOpened(r) => &r.world_id,
            RetellingRecord::ParticipantJoined(r) => &r.world_id,
            RetellingRecord::SeedAdded(r) => &r.world_id,
            RetellingRecord::RetellingAdded(r) => &r.world_id,
            RetellingRecord::ComparisonRecorded(r) => &r.world_id,
            RetellingRecord::InvitationLeft(r) => &r.world_id,
        }
    }

    pub fn proof(&self) -> &ProofOrArray {
        match self {
            RetellingRecord::WorldOpened(r) => &r.proof,
            RetellingRecord::ParticipantJoined(r) => &r.proof,
            RetellingRecord::SeedAdded(r) => &r.proof,
            RetellingRecord::RetellingAdded(r) => &r.proof,
            RetellingRecord::ComparisonRecorded(r) => &r.proof,
            RetellingRecord::InvitationLeft(r) => &r.proof,
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RetellingLog {
    pub world_id: DidKey,
    pub law: RetellingLaw,
    pub records: Vec<RetellingRecord>,
}

// =====================================================================
// LINEAGE & ATTRIBUTION QUERIES
// =====================================================================

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LineageNode {
    pub node_hash: String,
    pub node_id: String,
    pub medium: Medium,
    pub title: String,
    pub author_id: DidKey,
    pub parent_hashes: Vec<String>,
    pub account: Option<TransformationAccount>,
}

/// Separates root seed provenance from each subsequent interpreter's
/// preserved elements, additions, and translation losses.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AttributionTrace {
    pub target_node_hash: String,
    pub root_seeds: Vec<LineageNode>,
    pub transformation_steps: Vec<LineageNode>,
}

#[derive(Default)]
struct LineageGraph {
    nodes: HashMap<String, LineageNode>,
    children: HashMap<String, Vec<String>>,
    node_ids: HashSet<String>,
}

impl LineageGraph {
    fn insert(&mut self, node: LineageNode) -> Result<()> {
        if !self.node_ids.insert(node.node_id.clone()) {
            return Err(Error::Policy(format!(
                "duplicate node_id {:?}",
                node.node_id
            )));
        }
        for p in &node.parent_hashes {
            self.children
                .entry(p.clone())
                .or_default()
                .push(node.node_hash.clone());
        }
        self.nodes.insert(node.node_hash.clone(), node);
        Ok(())
    }

    fn contains(&self, hash: &str) -> bool {
        self.nodes.contains_key(hash)
    }

    /// Returns all ancestors of `start` (inclusive of `start` itself).
    fn ancestors_of(&self, start: &str) -> Result<HashSet<String>> {
        if !self.nodes.contains_key(start) {
            return Err(Error::Policy("unknown work node hash".into()));
        }
        let mut visited = HashSet::new();
        let mut queue = VecDeque::new();
        visited.insert(start.to_string());
        queue.push_back(start.to_string());
        while let Some(cur) = queue.pop_front() {
            if let Some(node) = self.nodes.get(&cur) {
                for p in &node.parent_hashes {
                    if visited.insert(p.clone()) {
                        queue.push_back(p.clone());
                    }
                }
            }
        }
        Ok(visited)
    }

    fn shared_ancestors(&self, left: &str, right: &str) -> Result<Vec<String>> {
        let a = self.ancestors_of(left)?;
        let b = self.ancestors_of(right)?;
        let mut common: Vec<String> = a.intersection(&b).cloned().collect();
        common.sort();
        Ok(common)
    }

    /// Walks forward from `start` to all downstream retellings in BFS order.
    fn descendants_of(&self, start: &str) -> Result<Vec<String>> {
        if !self.nodes.contains_key(start) {
            return Err(Error::Policy("unknown work node hash".into()));
        }
        let mut seen = HashSet::new();
        let mut out = Vec::new();
        let mut queue = VecDeque::new();
        seen.insert(start.to_string());
        queue.push_back(start.to_string());
        while let Some(cur) = queue.pop_front() {
            if let Some(kids) = self.children.get(&cur) {
                for k in kids {
                    if seen.insert(k.clone()) {
                        out.push(k.clone());
                        queue.push_back(k.clone());
                    }
                }
            }
        }
        Ok(out)
    }

    /// Walks backward from `target` to its roots, returning an ordered list
    /// from earliest roots toward `target`.
    fn ancestry_chain(&self, target: &str) -> Result<Vec<LineageNode>> {
        let anc_set = self.ancestors_of(target)?;
        // Order deterministically by topological distance from roots (parents before children).
        let mut in_deg: HashMap<String, usize> = HashMap::new();
        for h in &anc_set {
            let count = self.nodes[h]
                .parent_hashes
                .iter()
                .filter(|p| anc_set.contains(*p))
                .count();
            in_deg.insert(h.clone(), count);
        }
        let mut ready: Vec<String> = in_deg
            .iter()
            .filter(|(_, &deg)| deg == 0)
            .map(|(h, _)| h.clone())
            .collect();
        ready.sort();

        let mut ordered = Vec::with_capacity(anc_set.len());
        while !ready.is_empty() {
            let cur = ready.remove(0);
            ordered.push(self.nodes[&cur].clone());
            if let Some(kids) = self.children.get(&cur) {
                for k in kids {
                    if let Some(d) = in_deg.get_mut(k) {
                        *d -= 1;
                        if *d == 0 {
                            ready.push(k.clone());
                            ready.sort();
                        }
                    }
                }
            }
        }
        Ok(ordered)
    }
}

// =====================================================================
// INPUT DRAFTS & EXECUTABLE RETELLING WORLD
// =====================================================================

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SeedDraft {
    pub node_id: String,
    pub origin: SourceOrigin,
    pub medium: Medium,
    pub title: String,
    pub audience: String,
    pub content: String,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RetellingDraft {
    pub node_id: String,
    pub parent_node_hashes: Vec<String>,
    pub medium: Medium,
    pub title: String,
    pub audience: String,
    pub content: String,
    pub account: TransformationAccount,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ComparisonDraft {
    pub left_node_hash: String,
    pub right_node_hash: String,
    pub common_ancestor_hash: Option<String>,
    pub shared_elements: Vec<String>,
    pub divergences: Vec<String>,
}

fn sign_retelling_dual<T, F>(
    mut rec: T,
    actor: &Keypair,
    world: &Keypair,
    wrap: fn(T) -> RetellingRecord,
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

pub struct RetellingWorld {
    world_id: DidKey,
    law: RetellingLaw,
    keypair: Keypair,
    participants: HashSet<DidKey>,
    graph: LineageGraph,
    records: Vec<RetellingRecord>,
}

impl RetellingWorld {
    pub fn open(
        law: RetellingLaw,
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
        let signed = sign_retelling_dual(
            opened,
            creator_kp,
            &world_kp,
            RetellingRecord::WorldOpened,
            |r, p| r.proof = p,
        )?;
        let mut participants = HashSet::new();
        participants.insert(creator_id);
        Ok(RetellingWorld {
            world_id,
            law,
            keypair: world_kp,
            participants,
            graph: LineageGraph::default(),
            records: vec![RetellingRecord::WorldOpened(signed)],
        })
    }

    pub fn world_id(&self) -> &DidKey {
        &self.world_id
    }

    pub fn law(&self) -> &RetellingLaw {
        &self.law
    }

    pub fn log(&self) -> RetellingLog {
        RetellingLog {
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
            .ok_or_else(|| Error::Chain("retelling world has no seed record".into()))?
            .hash()
    }

    pub fn join(&mut self, participant_kp: &Keypair, now: u64) -> Result<RetellingRecord> {
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
        let signed = sign_retelling_dual(
            rec,
            participant_kp,
            &self.keypair,
            RetellingRecord::ParticipantJoined,
            |r, p| r.proof = p,
        )?;
        let wrapped = RetellingRecord::ParticipantJoined(signed);
        self.participants.insert(pid);
        self.records.push(wrapped.clone());
        Ok(wrapped)
    }

    /// Adds a root seed work (either native or imported from another world).
    /// Returns the 64-hex hash of the signed `SeedAdded` record.
    pub fn add_seed(
        &mut self,
        author_kp: &Keypair,
        draft: SeedDraft,
        now: u64,
    ) -> Result<String> {
        let author_id = author_kp.did();
        if !self.participants.contains(&author_id) {
            return Err(Error::Policy("author is not a participant".into()));
        }
        if draft.node_id.trim().is_empty()
            || draft.title.trim().is_empty()
            || draft.content.trim().is_empty()
        {
            return Err(Error::Policy(
                "seed node_id, title, and content must be non-empty".into(),
            ));
        }
        draft.medium.validate()?;
        if !self.law.medium_policy.permits(&draft.medium) {
            return Err(Error::Policy(format!(
                "medium {:?} is not permitted by this world's law",
                draft.medium
            )));
        }
        draft.origin.validate()?;
        if matches!(draft.origin, SourceOrigin::ImportedArtifact { .. })
            && !self.law.allow_external_imports
        {
            return Err(Error::Policy(
                "external artifact imports are disabled by this world's law".into(),
            ));
        }
        if self.graph.node_ids.contains(&draft.node_id) {
            return Err(Error::Policy(format!(
                "duplicate node_id {:?}",
                draft.node_id
            )));
        }

        let content_sha256 = sha256_hex(draft.content.as_bytes());
        let rec = SeedAdded {
            world_id: self.world_id.clone(),
            seq: self.next_seq(),
            prev: self.last_hash()?,
            node_id: draft.node_id.clone(),
            origin: draft.origin,
            medium: draft.medium.clone(),
            title: draft.title.clone(),
            audience: draft.audience,
            content: draft.content,
            content_sha256,
            author_id: author_id.clone(),
            ts: now,
            proof: ProofOrArray::placeholder(),
        };
        let signed = sign_retelling_dual(
            rec,
            author_kp,
            &self.keypair,
            RetellingRecord::SeedAdded,
            |r, p| r.proof = p,
        )?;
        let wrapped = RetellingRecord::SeedAdded(signed);
        let h = wrapped.hash()?;
        self.graph.insert(LineageNode {
            node_hash: h.clone(),
            node_id: draft.node_id,
            medium: draft.medium,
            title: draft.title,
            author_id,
            parent_hashes: Vec::new(),
            account: None,
        })?;
        self.records.push(wrapped);
        Ok(h)
    }

    /// Adds a retelling (single-parent transformation or multi-parent synthesis)
    /// carrying an explicit `TransformationAccount`. Returns its record hash.
    pub fn add_retelling(
        &mut self,
        author_kp: &Keypair,
        draft: RetellingDraft,
        now: u64,
    ) -> Result<String> {
        let author_id = author_kp.did();
        if !self.participants.contains(&author_id) {
            return Err(Error::Policy("author is not a participant".into()));
        }
        if draft.node_id.trim().is_empty()
            || draft.title.trim().is_empty()
            || draft.content.trim().is_empty()
        {
            return Err(Error::Policy(
                "retelling node_id, title, and content must be non-empty".into(),
            ));
        }
        if draft.parent_node_hashes.is_empty() {
            return Err(Error::Policy(
                "retelling must cite at least one parent_node_hash".into(),
            ));
        }
        let mut seen_parents = HashSet::new();
        for ph in &draft.parent_node_hashes {
            if !self.graph.contains(ph) {
                return Err(Error::Policy(
                    "retelling cites unknown parent_node_hash".into(),
                ));
            }
            if !seen_parents.insert(ph.clone()) {
                return Err(Error::Policy(
                    "retelling lists duplicate parent_node_hash".into(),
                ));
            }
        }
        draft.medium.validate()?;
        if !self.law.medium_policy.permits(&draft.medium) {
            return Err(Error::Policy(format!(
                "medium {:?} is not permitted by this world's law",
                draft.medium
            )));
        }
        draft
            .account
            .validate(self.law.require_explicit_losses)?;
        if self.graph.node_ids.contains(&draft.node_id) {
            return Err(Error::Policy(format!(
                "duplicate node_id {:?}",
                draft.node_id
            )));
        }

        let content_sha256 = sha256_hex(draft.content.as_bytes());
        let rec = RetellingAdded {
            world_id: self.world_id.clone(),
            seq: self.next_seq(),
            prev: self.last_hash()?,
            node_id: draft.node_id.clone(),
            parent_node_hashes: draft.parent_node_hashes.clone(),
            medium: draft.medium.clone(),
            title: draft.title.clone(),
            audience: draft.audience,
            content: draft.content,
            content_sha256,
            account: draft.account.clone(),
            author_id: author_id.clone(),
            ts: now,
            proof: ProofOrArray::placeholder(),
        };
        let signed = sign_retelling_dual(
            rec,
            author_kp,
            &self.keypair,
            RetellingRecord::RetellingAdded,
            |r, p| r.proof = p,
        )?;
        let wrapped = RetellingRecord::RetellingAdded(signed);
        let h = wrapped.hash()?;
        self.graph.insert(LineageNode {
            node_hash: h.clone(),
            node_id: draft.node_id,
            medium: draft.medium,
            title: draft.title,
            author_id,
            parent_hashes: draft.parent_node_hashes,
            account: Some(draft.account),
        })?;
        self.records.push(wrapped);
        Ok(h)
    }

    /// Records a side-by-side comparison of two distinct works without collapsing them.
    pub fn record_comparison(
        &mut self,
        author_kp: &Keypair,
        draft: ComparisonDraft,
        now: u64,
    ) -> Result<String> {
        let author_id = author_kp.did();
        if !self.participants.contains(&author_id) {
            return Err(Error::Policy("author is not a participant".into()));
        }
        if draft.left_node_hash == draft.right_node_hash {
            return Err(Error::Policy(
                "comparison must name two distinct work nodes".into(),
            ));
        }
        if !self.graph.contains(&draft.left_node_hash)
            || !self.graph.contains(&draft.right_node_hash)
        {
            return Err(Error::Policy("comparison cites unknown work node".into()));
        }
        if let Some(anc) = &draft.common_ancestor_hash {
            let shared = self
                .graph
                .shared_ancestors(&draft.left_node_hash, &draft.right_node_hash)?;
            if !shared.contains(anc) {
                return Err(Error::Policy(
                    "claimed common_ancestor_hash is not a shared ancestor of both works".into(),
                ));
            }
        }
        if draft.shared_elements.is_empty() && draft.divergences.is_empty() {
            return Err(Error::Policy(
                "comparison must record at least one shared element or divergence".into(),
            ));
        }

        let rec = ComparisonRecorded {
            world_id: self.world_id.clone(),
            seq: self.next_seq(),
            prev: self.last_hash()?,
            left_node_hash: draft.left_node_hash,
            right_node_hash: draft.right_node_hash,
            common_ancestor_hash: draft.common_ancestor_hash,
            shared_elements: draft.shared_elements,
            divergences: draft.divergences,
            author_id,
            ts: now,
            proof: ProofOrArray::placeholder(),
        };
        let signed = sign_retelling_dual(
            rec,
            author_kp,
            &self.keypair,
            RetellingRecord::ComparisonRecorded,
            |r, p| r.proof = p,
        )?;
        let wrapped = RetellingRecord::ComparisonRecorded(signed);
        let h = wrapped.hash()?;
        self.records.push(wrapped);
        Ok(h)
    }

    /// Leaves an open invitation anchored to one or more works for future visitors.
    pub fn leave_invitation(
        &mut self,
        author_kp: &Keypair,
        anchor_node_hashes: Vec<String>,
        prompt: &str,
        suggested_media: Vec<Medium>,
        now: u64,
    ) -> Result<String> {
        let author_id = author_kp.did();
        if !self.participants.contains(&author_id) {
            return Err(Error::Policy("author is not a participant".into()));
        }
        if anchor_node_hashes.is_empty() || prompt.trim().is_empty() {
            return Err(Error::Policy(
                "invitation requires at least one anchor work and a non-empty prompt".into(),
            ));
        }
        for ah in &anchor_node_hashes {
            if !self.graph.contains(ah) {
                return Err(Error::Policy(
                    "invitation cites unknown anchor_node_hash".into(),
                ));
            }
        }
        for m in &suggested_media {
            m.validate()?;
            if !self.law.medium_policy.permits(m) {
                return Err(Error::Policy(format!(
                    "suggested medium {:?} is not permitted by this world's law",
                    m
                )));
            }
        }

        let rec = InvitationLeft {
            world_id: self.world_id.clone(),
            seq: self.next_seq(),
            prev: self.last_hash()?,
            anchor_node_hashes,
            prompt: prompt.to_string(),
            suggested_media,
            author_id,
            ts: now,
            proof: ProofOrArray::placeholder(),
        };
        let signed = sign_retelling_dual(
            rec,
            author_kp,
            &self.keypair,
            RetellingRecord::InvitationLeft,
            |r, p| r.proof = p,
        )?;
        let wrapped = RetellingRecord::InvitationLeft(signed);
        let h = wrapped.hash()?;
        self.records.push(wrapped);
        Ok(h)
    }

    pub fn ancestry_chain(&self, node_hash: &str) -> Result<Vec<LineageNode>> {
        self.graph.ancestry_chain(node_hash)
    }

    pub fn descendants(&self, node_hash: &str) -> Result<Vec<String>> {
        self.graph.descendants_of(node_hash)
    }

    pub fn shared_ancestors(&self, left_hash: &str, right_hash: &str) -> Result<Vec<String>> {
        self.graph.shared_ancestors(left_hash, right_hash)
    }

    pub fn trace_attribution(&self, target_node_hash: &str) -> Result<AttributionTrace> {
        let chain = self.graph.ancestry_chain(target_node_hash)?;
        let mut root_seeds = Vec::new();
        let mut transformation_steps = Vec::new();
        for node in chain {
            if node.parent_hashes.is_empty() {
                root_seeds.push(node);
            } else {
                transformation_steps.push(node);
            }
        }
        Ok(AttributionTrace {
            target_node_hash: target_node_hash.to_string(),
            root_seeds,
            transformation_steps,
        })
    }
}

/// Independently replays and verifies an entire `RetellingLog` offline.
pub fn verify_retelling_log(log: &RetellingLog) -> Result<()> {
    log.law.validate()?;
    let Some(RetellingRecord::WorldOpened(seed)) = log.records.first() else {
        return Err(Error::Chain(
            "retelling log must start with world_opened".into(),
        ));
    };
    if seed.world_id != log.world_id {
        return Err(Error::Verification(
            "retelling log: seed world_id mismatch".into(),
        ));
    }
    if seed.law.hash()? != log.law.hash()? {
        return Err(Error::Verification(
            "retelling log: seed law does not match log law".into(),
        ));
    }

    let mut prev: Option<String> = None;
    let mut participants: HashSet<DidKey> = HashSet::new();
    let mut graph = LineageGraph::default();

    for (i, rec) in log.records.iter().enumerate() {
        if rec.seq() != i as u64 {
            return Err(Error::Chain(format!(
                "retelling log record {i}: seq {} != expected {i}",
                rec.seq()
            )));
        }
        if rec.world_id() != &log.world_id {
            return Err(Error::Verification(format!(
                "retelling log record {i}: world_id mismatch"
            )));
        }
        match rec {
            RetellingRecord::WorldOpened(_) => {
                if i != 0 {
                    return Err(Error::Chain(format!(
                        "retelling log record {i}: world_opened not at start"
                    )));
                }
            }
            _ => {
                if rec.prev() != prev.as_deref() {
                    return Err(Error::Chain(format!(
                        "retelling log record {i}: prev hash mismatch"
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

        let rec_hash = rec.hash()?;

        match rec {
            RetellingRecord::WorldOpened(r) => {
                let cp = r
                    .proof
                    .find_by_method(&r.creator_id)
                    .ok_or_else(|| Error::Verification("seed: missing creator proof".into()))?;
                cp.verify(&body)?;
                participants.insert(r.creator_id.clone());
            }
            RetellingRecord::ParticipantJoined(r) => {
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
            RetellingRecord::SeedAdded(r) => {
                if !participants.contains(&r.author_id) {
                    return Err(Error::Policy(format!("record {i}: author not a participant")));
                }
                if r.node_id.trim().is_empty()
                    || r.title.trim().is_empty()
                    || r.content.trim().is_empty()
                {
                    return Err(Error::Policy(format!(
                        "record {i}: seed has empty node_id, title, or content"
                    )));
                }
                r.medium.validate()?;
                if !log.law.medium_policy.permits(&r.medium) {
                    return Err(Error::Policy(format!(
                        "record {i}: seed medium not permitted by law"
                    )));
                }
                r.origin.validate()?;
                if matches!(r.origin, SourceOrigin::ImportedArtifact { .. })
                    && !log.law.allow_external_imports
                {
                    return Err(Error::Policy(format!(
                        "record {i}: external imports disallowed by law"
                    )));
                }
                if r.content_sha256 != sha256_hex(r.content.as_bytes()) {
                    return Err(Error::Verification(format!(
                        "record {i}: seed content_sha256 mismatch"
                    )));
                }
                let ap = r.proof.find_by_method(&r.author_id).ok_or_else(|| {
                    Error::Verification(format!("record {i}: missing author proof"))
                })?;
                ap.verify(&body)?;
                graph.insert(LineageNode {
                    node_hash: rec_hash.clone(),
                    node_id: r.node_id.clone(),
                    medium: r.medium.clone(),
                    title: r.title.clone(),
                    author_id: r.author_id.clone(),
                    parent_hashes: Vec::new(),
                    account: None,
                })?;
            }
            RetellingRecord::RetellingAdded(r) => {
                if !participants.contains(&r.author_id) {
                    return Err(Error::Policy(format!("record {i}: author not a participant")));
                }
                if r.node_id.trim().is_empty()
                    || r.title.trim().is_empty()
                    || r.content.trim().is_empty()
                {
                    return Err(Error::Policy(format!(
                        "record {i}: retelling has empty node_id, title, or content"
                    )));
                }
                if r.parent_node_hashes.is_empty() {
                    return Err(Error::Policy(format!(
                        "record {i}: retelling missing parent_node_hashes"
                    )));
                }
                let mut seen_parents = HashSet::new();
                for ph in &r.parent_node_hashes {
                    if !graph.contains(ph) {
                        return Err(Error::Verification(format!(
                            "record {i}: retelling cites unknown or future parent hash"
                        )));
                    }
                    if !seen_parents.insert(ph.clone()) {
                        return Err(Error::Policy(format!(
                            "record {i}: duplicate parent_node_hash"
                        )));
                    }
                }
                r.medium.validate()?;
                if !log.law.medium_policy.permits(&r.medium) {
                    return Err(Error::Policy(format!(
                        "record {i}: retelling medium not permitted by law"
                    )));
                }
                r.account.validate(log.law.require_explicit_losses)?;
                if r.content_sha256 != sha256_hex(r.content.as_bytes()) {
                    return Err(Error::Verification(format!(
                        "record {i}: retelling content_sha256 mismatch"
                    )));
                }
                let ap = r.proof.find_by_method(&r.author_id).ok_or_else(|| {
                    Error::Verification(format!("record {i}: missing author proof"))
                })?;
                ap.verify(&body)?;
                graph.insert(LineageNode {
                    node_hash: rec_hash.clone(),
                    node_id: r.node_id.clone(),
                    medium: r.medium.clone(),
                    title: r.title.clone(),
                    author_id: r.author_id.clone(),
                    parent_hashes: r.parent_node_hashes.clone(),
                    account: Some(r.account.clone()),
                })?;
            }
            RetellingRecord::ComparisonRecorded(r) => {
                if !participants.contains(&r.author_id) {
                    return Err(Error::Policy(format!("record {i}: author not a participant")));
                }
                if r.left_node_hash == r.right_node_hash {
                    return Err(Error::Policy(format!(
                        "record {i}: comparison left and right hashes must differ"
                    )));
                }
                if !graph.contains(&r.left_node_hash) || !graph.contains(&r.right_node_hash) {
                    return Err(Error::Verification(format!(
                        "record {i}: comparison cites unknown work node"
                    )));
                }
                if let Some(anc) = &r.common_ancestor_hash {
                    let shared = graph.shared_ancestors(&r.left_node_hash, &r.right_node_hash)?;
                    if !shared.contains(anc) {
                        return Err(Error::Verification(format!(
                            "record {i}: claimed common_ancestor_hash is not a shared ancestor"
                        )));
                    }
                }
                if r.shared_elements.is_empty() && r.divergences.is_empty() {
                    return Err(Error::Policy(format!(
                        "record {i}: comparison has neither shared_elements nor divergences"
                    )));
                }
                let ap = r.proof.find_by_method(&r.author_id).ok_or_else(|| {
                    Error::Verification(format!("record {i}: missing author proof"))
                })?;
                ap.verify(&body)?;
            }
            RetellingRecord::InvitationLeft(r) => {
                if !participants.contains(&r.author_id) {
                    return Err(Error::Policy(format!("record {i}: author not a participant")));
                }
                if r.anchor_node_hashes.is_empty() || r.prompt.trim().is_empty() {
                    return Err(Error::Policy(format!(
                        "record {i}: invitation missing anchors or prompt"
                    )));
                }
                for ah in &r.anchor_node_hashes {
                    if !graph.contains(ah) {
                        return Err(Error::Verification(format!(
                            "record {i}: invitation cites unknown anchor work"
                        )));
                    }
                }
                for m in &r.suggested_media {
                    m.validate()?;
                    if !log.law.medium_policy.permits(m) {
                        return Err(Error::Policy(format!(
                            "record {i}: invitation suggests disallowed medium"
                        )));
                    }
                }
                let ap = r.proof.find_by_method(&r.author_id).ok_or_else(|| {
                    Error::Verification(format!("record {i}: missing author proof"))
                })?;
                ap.verify(&body)?;
            }
        }

        prev = Some(rec_hash);
    }

    Ok(())
}
