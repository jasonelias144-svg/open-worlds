//! Continuing Project & Multi-AI Handoff Infrastructure.
//!
//! Makes the project the durable unit of collaboration across apps, models,
//! and sessions: native and imported conversation records, revision-bound
//! edit proposals, explicit review coverage, stale-safe acceptance decisions,
//! and authority-filtered generated handoff packages.

use crate::did::{DidKey, Keypair};
use crate::error::{Error, Result};
use crate::hash::{body_for_signing, hash_of, sha256_hex};
use crate::proof::{Proof, ProofOrArray};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, HashMap};

fn looks_like_hash(s: &str) -> bool {
    s.len() == 64 && s.chars().all(|c| c.is_ascii_hexdigit())
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ProjectPermission {
    Read,
    CommentOrReview,
    ProposeChanges,
    AcceptChanges,
    AssignTasks,
    Publish,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ParticipantRole {
    pub participant_id: DidKey,
    pub label: String,
    pub permissions: Vec<ProjectPermission>,
}

// =====================================================================
// CONVERSATION CAPTURE & IMPORT PROVENANCE
// =====================================================================

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "turn_role", rename_all = "snake_case")]
pub enum TurnRole {
    Prompt,
    Response,
    RegeneratedAlternative,
    EditedPrompt { supersedes_turn_hash: String },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "gap", rename_all = "snake_case")]
pub enum GapMarker {
    MissingPrompt,
    TruncatedResponse,
    UnavailableAttachment { name: String },
    UnknownCompleteness,
}

/// Distinguishes direct authenticated participation from an imported transcript.
/// An importer's signature attests to what the importer submitted, never
/// retrospectively forging the original speaker's signature.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "provenance", rename_all = "snake_case")]
pub enum CaptureProvenance {
    NativeSigned,
    Imported {
        submitted_by: DidKey,
        claimed_speaker: String,
        source_format: String,
        raw_source_sha256: String,
    },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TurnDraft {
    pub project_id: String,
    pub thread_id: String,
    pub turn_index: u64,
    pub role: TurnRole,
    pub text: String,
    pub attachments: Vec<String>,
    pub gaps: Vec<GapMarker>,
    pub provenance: CaptureProvenance,
    pub ts: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ConversationTurn {
    pub project_id: String,
    pub thread_id: String,
    pub turn_index: u64,
    pub role: TurnRole,
    pub text: String,
    pub attachments: Vec<String>,
    pub gaps: Vec<GapMarker>,
    pub provenance: CaptureProvenance,
    pub signer: DidKey,
    pub ts: u64,
    pub proof: ProofOrArray,
}

impl ConversationTurn {
    pub fn sign(draft: TurnDraft, signer_kp: &Keypair) -> Result<Self> {
        let mut turn = ConversationTurn {
            project_id: draft.project_id,
            thread_id: draft.thread_id,
            turn_index: draft.turn_index,
            role: draft.role,
            text: draft.text,
            attachments: draft.attachments,
            gaps: draft.gaps,
            provenance: draft.provenance,
            signer: signer_kp.did(),
            ts: draft.ts,
            proof: ProofOrArray::placeholder(),
        };
        turn.validate_fields()?;
        let body = body_for_signing(&turn)?;
        let sig = signer_kp.sign(&body);
        turn.proof = ProofOrArray::single(Proof::create(signer_kp, &sig));
        Ok(turn)
    }

    fn validate_fields(&self) -> Result<()> {
        if self.project_id.trim().is_empty() || self.thread_id.trim().is_empty() {
            return Err(Error::Policy(
                "conversation turn: project_id and thread_id must be non-empty".into(),
            ));
        }
        if let TurnRole::EditedPrompt {
            ref supersedes_turn_hash,
        } = self.role
        {
            if !looks_like_hash(supersedes_turn_hash) {
                return Err(Error::Policy(
                    "conversation turn: supersedes_turn_hash must be 64 hex chars".into(),
                ));
            }
        }
        if let CaptureProvenance::Imported {
            ref submitted_by,
            ref claimed_speaker,
            ref source_format,
            ref raw_source_sha256,
        } = self.provenance
        {
            if submitted_by != &self.signer {
                return Err(Error::Policy(
                    "imported turn: signer must match provenance.submitted_by".into(),
                ));
            }
            if claimed_speaker.trim().is_empty() || source_format.trim().is_empty() {
                return Err(Error::Policy(
                    "imported turn: claimed_speaker and source_format must be non-empty".into(),
                ));
            }
            if !looks_like_hash(raw_source_sha256) {
                return Err(Error::Policy(
                    "imported turn: raw_source_sha256 must be 64 hex chars".into(),
                ));
            }
        }
        Ok(())
    }

    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }

    pub fn verify(&self) -> Result<()> {
        self.validate_fields()?;
        let body = body_for_signing(self)?;
        let proof = self
            .proof
            .find_by_method(&self.signer)
            .ok_or_else(|| Error::Verification("conversation turn: missing signer proof".into()))?;
        proof.verify(&body)
    }
}

// =====================================================================
// ARTIFACT REVISIONS, TASKS, PROPOSALS, REVIEWS, AND ACCEPTANCE
// =====================================================================

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RevisionDraft {
    pub project_id: String,
    pub artifact_id: String,
    pub revision_num: u64,
    pub parent_revision_hash: Option<String>,
    pub content: String,
    pub derived_from_proposals: Vec<String>,
    pub summary: String,
    pub created_at: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ArtifactRevision {
    pub project_id: String,
    pub artifact_id: String,
    pub revision_num: u64,
    pub parent_revision_hash: Option<String>,
    pub content: String,
    pub content_sha256: String,
    pub derived_from_proposals: Vec<String>,
    pub summary: String,
    pub author: DidKey,
    pub created_at: u64,
    pub proof: ProofOrArray,
}

impl ArtifactRevision {
    pub fn sign(draft: RevisionDraft, author_kp: &Keypair) -> Result<Self> {
        let content_sha256 = sha256_hex(draft.content.as_bytes());
        let mut rev = ArtifactRevision {
            project_id: draft.project_id,
            artifact_id: draft.artifact_id,
            revision_num: draft.revision_num,
            parent_revision_hash: draft.parent_revision_hash,
            content: draft.content,
            content_sha256,
            derived_from_proposals: draft.derived_from_proposals,
            summary: draft.summary,
            author: author_kp.did(),
            created_at: draft.created_at,
            proof: ProofOrArray::placeholder(),
        };
        rev.validate_fields()?;
        let body = body_for_signing(&rev)?;
        let sig = author_kp.sign(&body);
        rev.proof = ProofOrArray::single(Proof::create(author_kp, &sig));
        Ok(rev)
    }

    fn validate_fields(&self) -> Result<()> {
        if self.project_id.trim().is_empty() || self.artifact_id.trim().is_empty() {
            return Err(Error::Policy(
                "artifact revision: project_id and artifact_id must be non-empty".into(),
            ));
        }
        if self.revision_num == 0 {
            return Err(Error::Policy(
                "artifact revision: revision_num must be >= 1".into(),
            ));
        }
        if self.revision_num == 1 && self.parent_revision_hash.is_some() {
            return Err(Error::Policy(
                "artifact revision: revision 1 cannot declare parent_revision_hash".into(),
            ));
        }
        if let Some(parent) = &self.parent_revision_hash {
            if !looks_like_hash(parent) {
                return Err(Error::Policy(
                    "artifact revision: parent_revision_hash must be 64 hex chars".into(),
                ));
            }
        }
        if self.content_sha256 != sha256_hex(self.content.as_bytes()) {
            return Err(Error::Verification(
                "artifact revision: content_sha256 does not match content".into(),
            ));
        }
        Ok(())
    }

    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }

    pub fn verify(&self) -> Result<()> {
        self.validate_fields()?;
        let body = body_for_signing(self)?;
        let proof = self
            .proof
            .find_by_method(&self.author)
            .ok_or_else(|| Error::Verification("artifact revision: missing author proof".into()))?;
        proof.verify(&body)
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TaskDraft {
    pub task_id: String,
    pub project_id: String,
    pub assignee: DidKey,
    pub artifact_id: String,
    pub base_revision_hash: String,
    pub objective: String,
    pub constraints: Vec<String>,
    pub stop_condition: String,
    /// When true, generated handoffs for this task hide competing proposals
    /// targeting the same base revision so drafts remain independent.
    pub independent_of_other_drafts: bool,
    pub assigned_at: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TaskAssignment {
    pub task_id: String,
    pub project_id: String,
    pub assignee: DidKey,
    pub artifact_id: String,
    pub base_revision_hash: String,
    pub objective: String,
    pub constraints: Vec<String>,
    pub stop_condition: String,
    pub independent_of_other_drafts: bool,
    pub assigner: DidKey,
    pub assigned_at: u64,
    pub proof: ProofOrArray,
}

impl TaskAssignment {
    pub fn sign(draft: TaskDraft, assigner_kp: &Keypair) -> Result<Self> {
        if draft.task_id.trim().is_empty() || draft.objective.trim().is_empty() {
            return Err(Error::Policy(
                "task assignment: task_id and objective must be non-empty".into(),
            ));
        }
        if !looks_like_hash(&draft.base_revision_hash) {
            return Err(Error::Policy(
                "task assignment: base_revision_hash must be 64 hex chars".into(),
            ));
        }
        let mut task = TaskAssignment {
            task_id: draft.task_id,
            project_id: draft.project_id,
            assignee: draft.assignee,
            artifact_id: draft.artifact_id,
            base_revision_hash: draft.base_revision_hash,
            objective: draft.objective,
            constraints: draft.constraints,
            stop_condition: draft.stop_condition,
            independent_of_other_drafts: draft.independent_of_other_drafts,
            assigner: assigner_kp.did(),
            assigned_at: draft.assigned_at,
            proof: ProofOrArray::placeholder(),
        };
        let body = body_for_signing(&task)?;
        let sig = assigner_kp.sign(&body);
        task.proof = ProofOrArray::single(Proof::create(assigner_kp, &sig));
        Ok(task)
    }

    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }

    pub fn verify(&self) -> Result<()> {
        if self.task_id.trim().is_empty() || self.objective.trim().is_empty() {
            return Err(Error::Verification(
                "task assignment: empty task_id or objective".into(),
            ));
        }
        if !looks_like_hash(&self.base_revision_hash) {
            return Err(Error::Verification(
                "task assignment: invalid base_revision_hash".into(),
            ));
        }
        let body = body_for_signing(self)?;
        let proof = self
            .proof
            .find_by_method(&self.assigner)
            .ok_or_else(|| Error::Verification("task assignment: missing assigner proof".into()))?;
        proof.verify(&body)
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ProposalDraft {
    pub proposal_id: String,
    pub project_id: String,
    pub task_id: Option<String>,
    pub artifact_id: String,
    pub base_revision_hash: String,
    pub proposed_content: String,
    pub rationale: String,
    pub preserved_invariants: Vec<String>,
    pub synthesizes_proposals: Vec<String>,
    pub created_at: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EditProposal {
    pub proposal_id: String,
    pub project_id: String,
    pub task_id: Option<String>,
    pub artifact_id: String,
    pub base_revision_hash: String,
    pub proposed_content: String,
    pub rationale: String,
    pub preserved_invariants: Vec<String>,
    pub synthesizes_proposals: Vec<String>,
    pub proposer: DidKey,
    pub created_at: u64,
    pub proof: ProofOrArray,
}

impl EditProposal {
    pub fn sign(draft: ProposalDraft, proposer_kp: &Keypair) -> Result<Self> {
        if draft.proposal_id.trim().is_empty() || draft.rationale.trim().is_empty() {
            return Err(Error::Policy(
                "edit proposal: proposal_id and rationale must be non-empty".into(),
            ));
        }
        if !looks_like_hash(&draft.base_revision_hash) {
            return Err(Error::Policy(
                "edit proposal: base_revision_hash must be 64 hex chars".into(),
            ));
        }
        for sh in &draft.synthesizes_proposals {
            if !looks_like_hash(sh) {
                return Err(Error::Policy(
                    "edit proposal: synthesizes_proposals entries must be 64 hex chars".into(),
                ));
            }
        }
        let mut prop = EditProposal {
            proposal_id: draft.proposal_id,
            project_id: draft.project_id,
            task_id: draft.task_id,
            artifact_id: draft.artifact_id,
            base_revision_hash: draft.base_revision_hash,
            proposed_content: draft.proposed_content,
            rationale: draft.rationale,
            preserved_invariants: draft.preserved_invariants,
            synthesizes_proposals: draft.synthesizes_proposals,
            proposer: proposer_kp.did(),
            created_at: draft.created_at,
            proof: ProofOrArray::placeholder(),
        };
        let body = body_for_signing(&prop)?;
        let sig = proposer_kp.sign(&body);
        prop.proof = ProofOrArray::single(Proof::create(proposer_kp, &sig));
        Ok(prop)
    }

    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }

    pub fn verify(&self) -> Result<()> {
        if self.proposal_id.trim().is_empty() || self.rationale.trim().is_empty() {
            return Err(Error::Verification(
                "edit proposal: empty proposal_id or rationale".into(),
            ));
        }
        if !looks_like_hash(&self.base_revision_hash) {
            return Err(Error::Verification(
                "edit proposal: invalid base_revision_hash".into(),
            ));
        }
        let body = body_for_signing(self)?;
        let proof = self
            .proof
            .find_by_method(&self.proposer)
            .ok_or_else(|| Error::Verification("edit proposal: missing proposer proof".into()))?;
        proof.verify(&body)
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ReviewVerdict {
    Approve,
    ApproveWithNotes,
    RequestChanges,
    Reject,
}

/// Makes review scope inspectable so a partial check never masquerades as a
/// complete audit across handoffs.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ReviewCoverage {
    pub sections_supplied: Vec<String>,
    pub sections_examined: Vec<String>,
    pub checks_performed: Vec<String>,
    pub missing_or_unexamined: Vec<String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ReviewDraft {
    pub project_id: String,
    pub target_hash: String,
    pub base_revision_hash: String,
    pub verdict: ReviewVerdict,
    pub coverage: ReviewCoverage,
    pub findings: Vec<String>,
    pub unresolved_questions: Vec<String>,
    pub reviewed_at: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ReviewRecord {
    pub project_id: String,
    pub target_hash: String,
    pub base_revision_hash: String,
    pub verdict: ReviewVerdict,
    pub coverage: ReviewCoverage,
    pub findings: Vec<String>,
    pub unresolved_questions: Vec<String>,
    pub reviewer: DidKey,
    pub reviewed_at: u64,
    pub proof: ProofOrArray,
}

impl ReviewRecord {
    pub fn sign(draft: ReviewDraft, reviewer_kp: &Keypair) -> Result<Self> {
        if !looks_like_hash(&draft.target_hash) || !looks_like_hash(&draft.base_revision_hash) {
            return Err(Error::Policy(
                "review record: target_hash and base_revision_hash must be 64 hex chars".into(),
            ));
        }
        if draft.coverage.sections_supplied.is_empty()
            || draft.coverage.sections_examined.is_empty()
        {
            return Err(Error::Policy(
                "review record: sections_supplied and sections_examined must be non-empty".into(),
            ));
        }
        let mut rev = ReviewRecord {
            project_id: draft.project_id,
            target_hash: draft.target_hash,
            base_revision_hash: draft.base_revision_hash,
            verdict: draft.verdict,
            coverage: draft.coverage,
            findings: draft.findings,
            unresolved_questions: draft.unresolved_questions,
            reviewer: reviewer_kp.did(),
            reviewed_at: draft.reviewed_at,
            proof: ProofOrArray::placeholder(),
        };
        let body = body_for_signing(&rev)?;
        let sig = reviewer_kp.sign(&body);
        rev.proof = ProofOrArray::single(Proof::create(reviewer_kp, &sig));
        Ok(rev)
    }

    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }

    pub fn verify(&self) -> Result<()> {
        if !looks_like_hash(&self.target_hash) || !looks_like_hash(&self.base_revision_hash) {
            return Err(Error::Verification(
                "review record: invalid target_hash or base_revision_hash".into(),
            ));
        }
        if self.coverage.sections_supplied.is_empty()
            || self.coverage.sections_examined.is_empty()
        {
            return Err(Error::Verification(
                "review record: empty coverage declarations".into(),
            ));
        }
        let body = body_for_signing(self)?;
        let proof = self
            .proof
            .find_by_method(&self.reviewer)
            .ok_or_else(|| Error::Verification("review record: missing reviewer proof".into()))?;
        proof.verify(&body)
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AcceptanceDraft {
    pub project_id: String,
    pub artifact_id: String,
    pub expected_current_revision_hash: String,
    pub accepted_proposal_hashes: Vec<String>,
    pub resulting_revision_hash: String,
    pub rationale: String,
    pub decided_at: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct AcceptanceDecision {
    pub project_id: String,
    pub artifact_id: String,
    pub expected_current_revision_hash: String,
    pub accepted_proposal_hashes: Vec<String>,
    pub resulting_revision_hash: String,
    pub rationale: String,
    pub decider: DidKey,
    pub decided_at: u64,
    pub proof: ProofOrArray,
}

impl AcceptanceDecision {
    pub fn sign(draft: AcceptanceDraft, decider_kp: &Keypair) -> Result<Self> {
        if !looks_like_hash(&draft.expected_current_revision_hash)
            || !looks_like_hash(&draft.resulting_revision_hash)
        {
            return Err(Error::Policy(
                "acceptance decision: revision hashes must be 64 hex chars".into(),
            ));
        }
        if draft.accepted_proposal_hashes.is_empty() {
            return Err(Error::Policy(
                "acceptance decision: must name at least one accepted proposal".into(),
            ));
        }
        for ph in &draft.accepted_proposal_hashes {
            if !looks_like_hash(ph) {
                return Err(Error::Policy(
                    "acceptance decision: proposal hash must be 64 hex chars".into(),
                ));
            }
        }
        let mut dec = AcceptanceDecision {
            project_id: draft.project_id,
            artifact_id: draft.artifact_id,
            expected_current_revision_hash: draft.expected_current_revision_hash,
            accepted_proposal_hashes: draft.accepted_proposal_hashes,
            resulting_revision_hash: draft.resulting_revision_hash,
            rationale: draft.rationale,
            decider: decider_kp.did(),
            decided_at: draft.decided_at,
            proof: ProofOrArray::placeholder(),
        };
        let body = body_for_signing(&dec)?;
        let sig = decider_kp.sign(&body);
        dec.proof = ProofOrArray::single(Proof::create(decider_kp, &sig));
        Ok(dec)
    }

    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }

    pub fn verify(&self) -> Result<()> {
        if !looks_like_hash(&self.expected_current_revision_hash)
            || !looks_like_hash(&self.resulting_revision_hash)
        {
            return Err(Error::Verification(
                "acceptance decision: invalid revision hash".into(),
            ));
        }
        if self.accepted_proposal_hashes.is_empty() {
            return Err(Error::Verification(
                "acceptance decision: empty accepted_proposal_hashes".into(),
            ));
        }
        let body = body_for_signing(self)?;
        let proof = self
            .proof
            .find_by_method(&self.decider)
            .ok_or_else(|| Error::Verification("acceptance decision: missing decider proof".into()))?;
        proof.verify(&body)
    }
}

// =====================================================================
// GENERATED HANDOFF PACKAGE & PORTABLE PROJECT SNAPSHOT
// =====================================================================

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HandoffPackage {
    pub project_id: String,
    pub purpose: String,
    pub stage: String,
    pub settled_terminology: BTreeMap<String, String>,
    pub recipient: DidKey,
    pub granted_permissions: Vec<ProjectPermission>,
    pub current_approved_revisions: BTreeMap<String, String>,
    pub current_document_contents: BTreeMap<String, String>,
    pub relevant_decisions: Vec<String>,
    pub assignment: Option<TaskAssignment>,
    pub visible_proposals: Vec<String>,
    pub open_questions: Vec<String>,
    pub coverage_limits: Vec<String>,
    pub snapshot_event_count: u64,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ProjectSnapshot {
    pub project_id: String,
    pub purpose: String,
    pub stage: String,
    pub owner: DidKey,
    pub created_at: u64,
    pub participants: Vec<ParticipantRole>,
    pub settled_terminology: BTreeMap<String, String>,
    pub open_questions: Vec<String>,
    pub turns: BTreeMap<String, ConversationTurn>,
    pub revisions: BTreeMap<String, ArtifactRevision>,
    pub current_approved: BTreeMap<String, String>,
    pub tasks: BTreeMap<String, TaskAssignment>,
    pub proposals: BTreeMap<String, EditProposal>,
    pub reviews: BTreeMap<String, ReviewRecord>,
    pub decisions: BTreeMap<String, AcceptanceDecision>,
}

/// Durable project workspace governing collaboration across sessions and apps.
pub struct ProjectWorkspace {
    project_id: String,
    purpose: String,
    stage: String,
    owner: DidKey,
    created_at: u64,
    participants: HashMap<DidKey, ParticipantRole>,
    settled_terminology: BTreeMap<String, String>,
    open_questions: Vec<String>,
    turns: BTreeMap<String, ConversationTurn>,
    revisions: BTreeMap<String, ArtifactRevision>,
    current_approved: BTreeMap<String, String>,
    tasks: BTreeMap<String, TaskAssignment>,
    proposals: BTreeMap<String, EditProposal>,
    reviews: BTreeMap<String, ReviewRecord>,
    decisions: BTreeMap<String, AcceptanceDecision>,
}

impl ProjectWorkspace {
    pub fn create(
        project_id: &str,
        purpose: &str,
        stage: &str,
        owner: DidKey,
        owner_label: &str,
        created_at: u64,
    ) -> Result<Self> {
        if project_id.trim().is_empty() || purpose.trim().is_empty() {
            return Err(Error::Policy(
                "project: project_id and purpose must be non-empty".into(),
            ));
        }
        let mut participants = HashMap::new();
        participants.insert(
            owner.clone(),
            ParticipantRole {
                participant_id: owner.clone(),
                label: owner_label.to_string(),
                permissions: vec![
                    ProjectPermission::Read,
                    ProjectPermission::CommentOrReview,
                    ProjectPermission::ProposeChanges,
                    ProjectPermission::AcceptChanges,
                    ProjectPermission::AssignTasks,
                    ProjectPermission::Publish,
                ],
            },
        );
        Ok(ProjectWorkspace {
            project_id: project_id.to_string(),
            purpose: purpose.to_string(),
            stage: stage.to_string(),
            owner,
            created_at,
            participants,
            settled_terminology: BTreeMap::new(),
            open_questions: Vec::new(),
            turns: BTreeMap::new(),
            revisions: BTreeMap::new(),
            current_approved: BTreeMap::new(),
            tasks: BTreeMap::new(),
            proposals: BTreeMap::new(),
            reviews: BTreeMap::new(),
            decisions: BTreeMap::new(),
        })
    }

    pub fn has_permission(&self, did: &DidKey, perm: ProjectPermission) -> bool {
        self.participants
            .get(did)
            .map(|r| r.permissions.contains(&perm))
            .unwrap_or(false)
    }

    pub fn add_participant(
        &mut self,
        acting_did: &DidKey,
        role: ParticipantRole,
    ) -> Result<()> {
        if acting_did != &self.owner
            && !self.has_permission(acting_did, ProjectPermission::AssignTasks)
        {
            return Err(Error::Policy(
                "actor lacks permission to add participants".into(),
            ));
        }
        self.participants.insert(role.participant_id.clone(), role);
        Ok(())
    }

    pub fn set_terminology(&mut self, term: &str, definition: &str) {
        self.settled_terminology
            .insert(term.to_string(), definition.to_string());
    }

    pub fn add_open_question(&mut self, question: &str) {
        if !self.open_questions.iter().any(|q| q == question) {
            self.open_questions.push(question.to_string());
        }
    }

    pub fn resolve_open_question(&mut self, question: &str) {
        self.open_questions.retain(|q| q != question);
    }

    pub fn current_revision_hash(&self, artifact_id: &str) -> Option<&str> {
        self.current_approved.get(artifact_id).map(|s| s.as_str())
    }

    pub fn current_revision(&self, artifact_id: &str) -> Option<&ArtifactRevision> {
        let h = self.current_approved.get(artifact_id)?;
        self.revisions.get(h)
    }

    pub fn turns_count(&self) -> usize {
        self.turns.len()
    }

    pub fn decisions_count(&self) -> usize {
        self.decisions.len()
    }

    /// Seed the initial approved revision (version 1) of a project artifact.
    pub fn seed_artifact(&mut self, rev: ArtifactRevision) -> Result<String> {
        rev.verify()?;
        if rev.project_id != self.project_id {
            return Err(Error::Policy("artifact revision project_id mismatch".into()));
        }
        if !self.has_permission(&rev.author, ProjectPermission::AcceptChanges) {
            return Err(Error::Policy(
                "only a participant with AcceptChanges may seed an artifact".into(),
            ));
        }
        if rev.revision_num != 1 || rev.parent_revision_hash.is_some() {
            return Err(Error::Policy(
                "seed_artifact requires revision_num 1 with no parent".into(),
            ));
        }
        if self.current_approved.contains_key(&rev.artifact_id) {
            return Err(Error::Policy("artifact already seeded".into()));
        }
        let h = rev.hash()?;
        self.current_approved
            .insert(rev.artifact_id.clone(), h.clone());
        self.revisions.insert(h.clone(), rev);
        Ok(h)
    }

    /// Capture a native turn or import a conversation record. Idempotent by hash.
    pub fn record_turn(&mut self, turn: ConversationTurn) -> Result<String> {
        turn.verify()?;
        if turn.project_id != self.project_id {
            return Err(Error::Policy("conversation turn project_id mismatch".into()));
        }
        if !self.has_permission(&turn.signer, ProjectPermission::Read) {
            return Err(Error::Policy(
                "turn signer is not an authorized participant".into(),
            ));
        }
        if let TurnRole::EditedPrompt {
            ref supersedes_turn_hash,
        } = turn.role
        {
            if !self.turns.contains_key(supersedes_turn_hash) {
                return Err(Error::Policy(
                    "edited prompt references unknown supersedes_turn_hash".into(),
                ));
            }
        }
        let h = turn.hash()?;
        self.turns.entry(h.clone()).or_insert(turn);
        Ok(h)
    }

    /// Record a bounded task assignment against an existing revision.
    pub fn assign_task(&mut self, task: TaskAssignment) -> Result<String> {
        task.verify()?;
        if task.project_id != self.project_id {
            return Err(Error::Policy("task project_id mismatch".into()));
        }
        if !self.has_permission(&task.assigner, ProjectPermission::AssignTasks) {
            return Err(Error::Policy(
                "assigner lacks AssignTasks permission".into(),
            ));
        }
        if !self.has_permission(&task.assignee, ProjectPermission::Read) {
            return Err(Error::Policy(
                "task assignee is not an authorized participant".into(),
            ));
        }
        let base_rev = self
            .revisions
            .get(&task.base_revision_hash)
            .ok_or_else(|| Error::Policy("task references unknown base_revision_hash".into()))?;
        if base_rev.artifact_id != task.artifact_id {
            return Err(Error::Policy(
                "task artifact_id does not match base_revision_hash".into(),
            ));
        }
        let h = task.hash()?;
        self.tasks.entry(task.task_id.clone()).or_insert(task);
        Ok(h)
    }

    /// Record an edit proposal against a specific base revision. Idempotent by hash.
    pub fn submit_proposal(&mut self, prop: EditProposal) -> Result<String> {
        prop.verify()?;
        if prop.project_id != self.project_id {
            return Err(Error::Policy("proposal project_id mismatch".into()));
        }
        if !self.has_permission(&prop.proposer, ProjectPermission::ProposeChanges) {
            return Err(Error::Policy(
                "proposer lacks ProposeChanges permission".into(),
            ));
        }
        let base_rev = self
            .revisions
            .get(&prop.base_revision_hash)
            .ok_or_else(|| Error::Policy("proposal references unknown base_revision_hash".into()))?;
        if base_rev.artifact_id != prop.artifact_id {
            return Err(Error::Policy(
                "proposal artifact_id does not match base_revision_hash".into(),
            ));
        }
        for sh in &prop.synthesizes_proposals {
            if !self.proposals.contains_key(sh) {
                return Err(Error::Policy(
                    "proposal synthesizes unknown proposal hash".into(),
                ));
            }
        }
        let h = prop.hash()?;
        self.proposals.entry(h.clone()).or_insert(prop);
        Ok(h)
    }

    /// Record a review with explicit coverage attached to an existing revision or proposal.
    pub fn submit_review(&mut self, review: ReviewRecord) -> Result<String> {
        review.verify()?;
        if review.project_id != self.project_id {
            return Err(Error::Policy("review project_id mismatch".into()));
        }
        if !self.has_permission(&review.reviewer, ProjectPermission::CommentOrReview) {
            return Err(Error::Policy(
                "reviewer lacks CommentOrReview permission".into(),
            ));
        }
        if !self.revisions.contains_key(&review.base_revision_hash) {
            return Err(Error::Policy(
                "review references unknown base_revision_hash".into(),
            ));
        }
        let target_exists = self.revisions.contains_key(&review.target_hash)
            || self.proposals.contains_key(&review.target_hash);
        if !target_exists {
            return Err(Error::Policy(
                "review target_hash is neither a known revision nor a known proposal".into(),
            ));
        }
        let h = review.hash()?;
        self.reviews.entry(h.clone()).or_insert(review);
        Ok(h)
    }

    /// Accept one or more proposals and advance the artifact's authoritative revision.
    /// Strictly refuses stale proposals targeting a superseded revision, while
    /// remaining idempotent on duplicate delivery of the exact same decision.
    pub fn accept_revision(
        &mut self,
        decision: AcceptanceDecision,
        resulting_revision: ArtifactRevision,
    ) -> Result<String> {
        decision.verify()?;
        resulting_revision.verify()?;

        let dec_hash = decision.hash()?;
        if self.decisions.contains_key(&dec_hash) {
            return Ok(dec_hash);
        }

        if decision.project_id != self.project_id
            || resulting_revision.project_id != self.project_id
        {
            return Err(Error::Policy("acceptance project_id mismatch".into()));
        }
        if !self.has_permission(&decision.decider, ProjectPermission::AcceptChanges) {
            return Err(Error::Policy(
                "decider lacks AcceptChanges permission".into(),
            ));
        }

        let current_hash = self
            .current_approved
            .get(&decision.artifact_id)
            .ok_or_else(|| Error::Policy("artifact has no current approved revision".into()))?
            .clone();
        if decision.expected_current_revision_hash != current_hash {
            return Err(Error::Policy(format!(
                "stale acceptance refused: expected current revision {}, actual is {}",
                decision.expected_current_revision_hash, current_hash
            )));
        }

        for ph in &decision.accepted_proposal_hashes {
            let prop = self.proposals.get(ph).ok_or_else(|| {
                Error::Policy("acceptance references unknown proposal hash".into())
            })?;
            if prop.artifact_id != decision.artifact_id {
                return Err(Error::Policy(
                    "accepted proposal targets a different artifact".into(),
                ));
            }
            if prop.base_revision_hash != current_hash {
                return Err(Error::Policy(
                    "stale proposal refused: proposal base_revision_hash does not match current revision; reconcile first"
                        .into(),
                ));
            }
        }

        let current_rev = self.revisions.get(&current_hash).unwrap();
        let res_hash = resulting_revision.hash()?;
        if res_hash != decision.resulting_revision_hash {
            return Err(Error::Verification(
                "resulting_revision hash does not match decision.resulting_revision_hash".into(),
            ));
        }
        if resulting_revision.artifact_id != decision.artifact_id {
            return Err(Error::Policy(
                "resulting_revision artifact_id mismatch".into(),
            ));
        }
        if resulting_revision.parent_revision_hash.as_deref() != Some(current_hash.as_str()) {
            return Err(Error::Chain(
                "resulting_revision parent_revision_hash must equal current revision".into(),
            ));
        }
        if resulting_revision.revision_num != current_rev.revision_num + 1 {
            return Err(Error::Chain(
                "resulting_revision revision_num must increment by 1".into(),
            ));
        }

        self.revisions.insert(res_hash.clone(), resulting_revision);
        self.current_approved
            .insert(decision.artifact_id.clone(), res_hash);
        self.decisions.insert(dec_hash.clone(), decision);
        Ok(dec_hash)
    }

    /// Generate a portable, authority-scoped handoff package directly from
    /// authoritative project state.
    pub fn generate_handoff(
        &self,
        recipient: &DidKey,
        task_id: Option<&str>,
    ) -> Result<HandoffPackage> {
        let role = self
            .participants
            .get(recipient)
            .ok_or_else(|| Error::Policy("handoff recipient is not a project participant".into()))?;
        if !role.permissions.contains(&ProjectPermission::Read) {
            return Err(Error::Policy(
                "handoff recipient lacks Read permission".into(),
            ));
        }

        let assignment = match task_id {
            Some(tid) => {
                let task = self
                    .tasks
                    .get(tid)
                    .ok_or_else(|| Error::Policy("requested task_id not found".into()))?;
                if &task.assignee != recipient {
                    return Err(Error::Policy(
                        "requested task is assigned to a different participant".into(),
                    ));
                }
                Some(task.clone())
            }
            None => None,
        };

        let mut current_document_contents = BTreeMap::new();
        for (art_id, rev_hash) in &self.current_approved {
            if let Some(rev) = self.revisions.get(rev_hash) {
                current_document_contents.insert(art_id.clone(), rev.content.clone());
            }
        }

        // If this task requires independent drafting, hide competing proposals
        // targeting the same base revision so collaborators work independently.
        let mut visible_proposals = Vec::new();
        for (ph, prop) in &self.proposals {
            let hide = match &assignment {
                Some(t) if t.independent_of_other_drafts => {
                    prop.base_revision_hash == t.base_revision_hash && &prop.proposer != recipient
                }
                _ => false,
            };
            if !hide {
                visible_proposals.push(ph.clone());
            }
        }

        let relevant_decisions: Vec<String> = self
            .decisions
            .values()
            .map(|d| format!("{} -> {}", d.artifact_id, d.rationale))
            .collect();

        let mut coverage_limits = Vec::new();
        for rev in self.reviews.values() {
            if !rev.coverage.missing_or_unexamined.is_empty() {
                coverage_limits.push(format!(
                    "review of {} left unexamined: {}",
                    &rev.target_hash[..16],
                    rev.coverage.missing_or_unexamined.join(", ")
                ));
            }
        }
        for turn in self.turns.values() {
            if !turn.gaps.is_empty() {
                coverage_limits.push(format!(
                    "thread {} turn {} carries {} recorded gap(s)",
                    turn.thread_id,
                    turn.turn_index,
                    turn.gaps.len()
                ));
            }
        }

        let snapshot_event_count = (self.turns.len()
            + self.revisions.len()
            + self.tasks.len()
            + self.proposals.len()
            + self.reviews.len()
            + self.decisions.len()) as u64;

        Ok(HandoffPackage {
            project_id: self.project_id.clone(),
            purpose: self.purpose.clone(),
            stage: self.stage.clone(),
            settled_terminology: self.settled_terminology.clone(),
            recipient: recipient.clone(),
            granted_permissions: role.permissions.clone(),
            current_approved_revisions: self.current_approved.clone(),
            current_document_contents,
            relevant_decisions,
            assignment,
            visible_proposals,
            open_questions: self.open_questions.clone(),
            coverage_limits,
            snapshot_event_count,
        })
    }

    pub fn export_snapshot(&self) -> ProjectSnapshot {
        let mut participants: Vec<ParticipantRole> = self.participants.values().cloned().collect();
        participants.sort_by(|a, b| a.participant_id.as_str().cmp(b.participant_id.as_str()));

        ProjectSnapshot {
            project_id: self.project_id.clone(),
            purpose: self.purpose.clone(),
            stage: self.stage.clone(),
            owner: self.owner.clone(),
            created_at: self.created_at,
            participants,
            settled_terminology: self.settled_terminology.clone(),
            open_questions: self.open_questions.clone(),
            turns: self.turns.clone(),
            revisions: self.revisions.clone(),
            current_approved: self.current_approved.clone(),
            tasks: self.tasks.clone(),
            proposals: self.proposals.clone(),
            reviews: self.reviews.clone(),
            decisions: self.decisions.clone(),
        }
    }

    /// Restore a workspace in a fresh session, re-verifying every signature,
    /// hash key, and approved-revision reference before trusting the state.
    pub fn restore(snap: ProjectSnapshot) -> Result<Self> {
        let mut participants = HashMap::new();
        for p in snap.participants {
            participants.insert(p.participant_id.clone(), p);
        }
        if !participants.contains_key(&snap.owner) {
            return Err(Error::Verification(
                "project restore: owner missing from participants".into(),
            ));
        }
        for (h, turn) in &snap.turns {
            turn.verify()?;
            if &turn.hash()? != h {
                return Err(Error::Verification("project restore: turn hash mismatch".into()));
            }
        }
        for (h, rev) in &snap.revisions {
            rev.verify()?;
            if &rev.hash()? != h {
                return Err(Error::Verification(
                    "project restore: revision hash mismatch".into(),
                ));
            }
        }
        for rev_hash in snap.current_approved.values() {
            if !snap.revisions.contains_key(rev_hash) {
                return Err(Error::Verification(
                    "project restore: current_approved references missing revision".into(),
                ));
            }
        }
        for task in snap.tasks.values() {
            task.verify()?;
        }
        for (h, prop) in &snap.proposals {
            prop.verify()?;
            if &prop.hash()? != h {
                return Err(Error::Verification(
                    "project restore: proposal hash mismatch".into(),
                ));
            }
        }
        for (h, review) in &snap.reviews {
            review.verify()?;
            if &review.hash()? != h {
                return Err(Error::Verification(
                    "project restore: review hash mismatch".into(),
                ));
            }
        }
        for (h, dec) in &snap.decisions {
            dec.verify()?;
            if &dec.hash()? != h {
                return Err(Error::Verification(
                    "project restore: decision hash mismatch".into(),
                ));
            }
        }

        Ok(ProjectWorkspace {
            project_id: snap.project_id,
            purpose: snap.purpose,
            stage: snap.stage,
            owner: snap.owner,
            created_at: snap.created_at,
            participants,
            settled_terminology: snap.settled_terminology,
            open_questions: snap.open_questions,
            turns: snap.turns,
            revisions: snap.revisions,
            current_approved: snap.current_approved,
            tasks: snap.tasks,
            proposals: snap.proposals,
            reviews: snap.reviews,
            decisions: snap.decisions,
        })
    }
}
