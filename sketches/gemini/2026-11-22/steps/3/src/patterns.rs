//! Practical Problem-Solution Pattern Engine.
//!
//! Separates reusable conditional claims (`PatternCard`), domain-specific
//! bindings (`PatternApplication`), and observed outcomes (`ApplicationEvidence`),
//! with deterministic compatibility checks for multi-pattern strategy composition.

use crate::did::{DidKey, Keypair};
use crate::error::{Error, Result};
use crate::hash::{body_for_signing, hash_of};
use crate::proof::{Proof, ProofOrArray};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet, HashMap};

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PatternContext {
    pub roles: Vec<String>,
    pub constraints: Vec<String>,
    pub assumptions: Vec<String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PatternTransformation {
    pub actions: Vec<String>,
    pub observations: Vec<String>,
    pub stop_conditions: Vec<String>,
}

/// Unsigned payload used to create a signed `PatternCard`.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PatternDraft {
    pub pattern_id: String,
    pub version: u64,
    pub derived_from: Option<String>,
    pub title: String,
    pub problem: String,
    pub goal: String,
    pub context: PatternContext,
    pub requires: Vec<String>,
    pub provides: Vec<String>,
    pub destroys: Vec<String>,
    pub exclusions: Vec<String>,
    pub transformation: PatternTransformation,
    pub mechanism: String,
    pub costs: Vec<String>,
    pub known_failures: Vec<String>,
    pub sharing_terms: String,
    pub created_at: u64,
}

/// A signed, versioned, conditional problem-solution pattern.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PatternCard {
    pub pattern_id: String,
    pub version: u64,
    pub derived_from: Option<String>,
    pub title: String,
    pub problem: String,
    pub goal: String,
    pub context: PatternContext,
    pub requires: Vec<String>,
    pub provides: Vec<String>,
    pub destroys: Vec<String>,
    pub exclusions: Vec<String>,
    pub transformation: PatternTransformation,
    pub mechanism: String,
    pub costs: Vec<String>,
    pub known_failures: Vec<String>,
    pub sharing_terms: String,
    pub author: DidKey,
    pub created_at: u64,
    pub proof: ProofOrArray,
}

impl PatternCard {
    pub fn sign(draft: PatternDraft, author_kp: &Keypair) -> Result<Self> {
        if draft.pattern_id.trim().is_empty() {
            return Err(Error::Policy("pattern_id cannot be empty".into()));
        }
        if draft.version == 0 {
            return Err(Error::Policy("pattern version must be >= 1".into()));
        }
        if draft.version == 1 && draft.derived_from.is_some() {
            return Err(Error::Policy(
                "version 1 pattern cannot declare derived_from".into(),
            ));
        }
        if draft.problem.trim().is_empty() || draft.goal.trim().is_empty() {
            return Err(Error::Policy("pattern problem and goal must be non-empty".into()));
        }
        if draft.transformation.actions.is_empty() {
            return Err(Error::Policy(
                "pattern transformation must specify at least one action".into(),
            ));
        }

        let mut card = PatternCard {
            pattern_id: draft.pattern_id,
            version: draft.version,
            derived_from: draft.derived_from,
            title: draft.title,
            problem: draft.problem,
            goal: draft.goal,
            context: draft.context,
            requires: draft.requires,
            provides: draft.provides,
            destroys: draft.destroys,
            exclusions: draft.exclusions,
            transformation: draft.transformation,
            mechanism: draft.mechanism,
            costs: draft.costs,
            known_failures: draft.known_failures,
            sharing_terms: draft.sharing_terms,
            author: author_kp.did(),
            created_at: draft.created_at,
            proof: ProofOrArray::placeholder(),
        };
        let body = body_for_signing(&card)?;
        let sig = author_kp.sign(&body);
        card.proof = ProofOrArray::single(Proof::create(author_kp, &sig));
        Ok(card)
    }

    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }

    pub fn verify(&self) -> Result<()> {
        if self.pattern_id.trim().is_empty() {
            return Err(Error::Verification("pattern: empty pattern_id".into()));
        }
        if self.version == 0 {
            return Err(Error::Verification("pattern: version must be >= 1".into()));
        }
        let body = body_for_signing(self)?;
        let proof = self
            .proof
            .find_by_method(&self.author)
            .ok_or_else(|| Error::Verification("pattern: missing author proof".into()))?;
        proof.verify(&body)
    }
}

/// Unsigned payload describing one concrete application of a `PatternCard`
/// in a receiving domain.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ApplicationDraft {
    pub pattern_id: String,
    pub pattern_version: u64,
    pub pattern_hash: String,
    pub domain: String,
    pub setting_summary: String,
    /// Maps each abstract role declared in `PatternCard::context.roles`
    /// to a concrete role or entity in the receiving domain.
    pub role_mapping: BTreeMap<String, String>,
    /// Preconditions verified present in the receiving domain.
    pub present_conditions: BTreeSet<String>,
    pub applied_at: u64,
}

/// Signed record binding a specific `PatternCard` revision to a concrete domain.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PatternApplication {
    pub pattern_id: String,
    pub pattern_version: u64,
    pub pattern_hash: String,
    pub domain: String,
    pub setting_summary: String,
    pub role_mapping: BTreeMap<String, String>,
    pub present_conditions: BTreeSet<String>,
    pub actor: DidKey,
    pub applied_at: u64,
    pub proof: ProofOrArray,
}

impl PatternApplication {
    pub fn sign(draft: ApplicationDraft, actor_kp: &Keypair) -> Result<Self> {
        if draft.domain.trim().is_empty() {
            return Err(Error::Policy("application domain cannot be empty".into()));
        }
        let mut app = PatternApplication {
            pattern_id: draft.pattern_id,
            pattern_version: draft.pattern_version,
            pattern_hash: draft.pattern_hash,
            domain: draft.domain,
            setting_summary: draft.setting_summary,
            role_mapping: draft.role_mapping,
            present_conditions: draft.present_conditions,
            actor: actor_kp.did(),
            applied_at: draft.applied_at,
            proof: ProofOrArray::placeholder(),
        };
        let body = body_for_signing(&app)?;
        let sig = actor_kp.sign(&body);
        app.proof = ProofOrArray::single(Proof::create(actor_kp, &sig));
        Ok(app)
    }

    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }

    pub fn verify(&self) -> Result<()> {
        if self.domain.trim().is_empty() {
            return Err(Error::Verification("application: empty domain".into()));
        }
        let body = body_for_signing(self)?;
        let proof = self
            .proof
            .find_by_method(&self.actor)
            .ok_or_else(|| Error::Verification("application: missing actor proof".into()))?;
        proof.verify(&body)
    }

    /// Check that this application legitimately maps the target `PatternCard`,
    /// satisfies every declared prerequisite, and triggers no exclusion.
    pub fn verify_against(&self, card: &PatternCard) -> Result<()> {
        self.verify()?;
        card.verify()?;

        let expected_hash = card.hash()?;
        if self.pattern_hash != expected_hash {
            return Err(Error::Verification(
                "application pattern_hash does not match card".into(),
            ));
        }
        if self.pattern_id != card.pattern_id || self.pattern_version != card.version {
            return Err(Error::Verification(
                "application pattern_id or version does not match card".into(),
            ));
        }
        for role in &card.context.roles {
            match self.role_mapping.get(role) {
                Some(mapped) if !mapped.trim().is_empty() => {}
                _ => {
                    return Err(Error::Policy(format!(
                        "application missing mapping for required role {:?}",
                        role
                    )));
                }
            }
        }
        for excl in &card.exclusions {
            if self.present_conditions.contains(excl) {
                return Err(Error::Policy(format!(
                    "application triggers exclusion condition {:?}",
                    excl
                )));
            }
        }
        for req in &card.requires {
            if !self.present_conditions.contains(req) {
                return Err(Error::Policy(format!(
                    "application missing required precondition {:?}",
                    req
                )));
            }
        }
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum EvidenceVerdict {
    Supported,
    Partial,
    Failed,
    Inapplicable,
}

/// Explicitly separates inspectable public source cases from confidential
/// cases whose general lesson is shared without exposing the originating room.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "visibility", rename_all = "snake_case")]
pub enum SourceVisibility {
    Public { source_ref: String },
    ConfidentialUninspectable,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct EvidenceDraft {
    pub application_hash: String,
    pub verdict: EvidenceVerdict,
    pub observed_effects: Vec<String>,
    pub failure_or_limit_note: Option<String>,
    pub source_visibility: SourceVisibility,
    pub reported_at: u64,
}

/// Signed empirical report attached to one `PatternApplication`.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ApplicationEvidence {
    pub application_hash: String,
    pub verdict: EvidenceVerdict,
    pub observed_effects: Vec<String>,
    pub failure_or_limit_note: Option<String>,
    pub source_visibility: SourceVisibility,
    pub reporter: DidKey,
    pub reported_at: u64,
    pub proof: ProofOrArray,
}

impl ApplicationEvidence {
    pub fn sign(draft: EvidenceDraft, reporter_kp: &Keypair) -> Result<Self> {
        if draft.observed_effects.is_empty() {
            return Err(Error::Policy(
                "evidence must record at least one observed effect".into(),
            ));
        }
        if matches!(
            draft.verdict,
            EvidenceVerdict::Failed | EvidenceVerdict::Inapplicable
        ) && draft
            .failure_or_limit_note
            .as_deref()
            .unwrap_or("")
            .trim()
            .is_empty()
        {
            return Err(Error::Policy(
                "failed or inapplicable evidence must include a failure_or_limit_note".into(),
            ));
        }
        if let SourceVisibility::Public { ref source_ref } = draft.source_visibility {
            if source_ref.trim().is_empty() {
                return Err(Error::Policy(
                    "public source visibility requires a non-empty source_ref".into(),
                ));
            }
        }

        let mut ev = ApplicationEvidence {
            application_hash: draft.application_hash,
            verdict: draft.verdict,
            observed_effects: draft.observed_effects,
            failure_or_limit_note: draft.failure_or_limit_note,
            source_visibility: draft.source_visibility,
            reporter: reporter_kp.did(),
            reported_at: draft.reported_at,
            proof: ProofOrArray::placeholder(),
        };
        let body = body_for_signing(&ev)?;
        let sig = reporter_kp.sign(&body);
        ev.proof = ProofOrArray::single(Proof::create(reporter_kp, &sig));
        Ok(ev)
    }

    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }

    pub fn verify(&self) -> Result<()> {
        let body = body_for_signing(self)?;
        let proof = self
            .proof
            .find_by_method(&self.reporter)
            .ok_or_else(|| Error::Verification("evidence: missing reporter proof".into()))?;
        proof.verify(&body)
    }

    pub fn verify_against(&self, app: &PatternApplication) -> Result<()> {
        self.verify()?;
        app.verify()?;
        if self.application_hash != app.hash()? {
            return Err(Error::Verification(
                "evidence application_hash does not match application".into(),
            ));
        }
        if self.reported_at < app.applied_at {
            return Err(Error::Verification(
                "evidence reported_at precedes application applied_at".into(),
            ));
        }
        Ok(())
    }
}

// =====================================================================
// STRATEGY COMPOSITION CHECKER
// =====================================================================

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct CompositionStep {
    pub step_index: usize,
    pub pattern_id: String,
    pub pattern_version: u64,
    pub active_after: BTreeSet<String>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct CompositionTrace {
    pub steps: Vec<CompositionStep>,
    pub final_conditions: BTreeSet<String>,
    pub cumulative_costs: Vec<String>,
}

/// Checks whether an ordered sequence of `PatternCard`s can compose from
/// `initial_conditions`: verifies every card, enforces prerequisites,
/// detects conditions destroyed by earlier steps, and blocks triggered exclusions.
pub fn check_composition(
    initial_conditions: &BTreeSet<String>,
    steps: &[&PatternCard],
) -> Result<CompositionTrace> {
    if steps.is_empty() {
        return Err(Error::Policy("composition requires at least one pattern".into()));
    }

    let mut active: BTreeSet<String> = initial_conditions.clone();
    let mut destroyed_by: HashMap<String, (usize, String)> = HashMap::new();
    let mut trace_steps = Vec::with_capacity(steps.len());
    let mut cumulative_costs = Vec::new();

    for (idx, card) in steps.iter().enumerate() {
        card.verify()?;

        for excl in &card.exclusions {
            if active.contains(excl) {
                return Err(Error::Policy(format!(
                    "composition step {idx} ({}): active condition {:?} triggers exclusion",
                    card.pattern_id, excl
                )));
            }
        }

        for req in &card.requires {
            if !active.contains(req) {
                if let Some((by_idx, by_id)) = destroyed_by.get(req) {
                    return Err(Error::Policy(format!(
                        "composition step {idx} ({}): prerequisite {:?} was destroyed by step {by_idx} ({by_id})",
                        card.pattern_id, req
                    )));
                }
                return Err(Error::Policy(format!(
                    "composition step {idx} ({}): missing prerequisite {:?}",
                    card.pattern_id, req
                )));
            }
        }

        for d in &card.destroys {
            if active.remove(d) {
                destroyed_by.insert(d.clone(), (idx, card.pattern_id.clone()));
            }
        }
        for p in &card.provides {
            active.insert(p.clone());
            destroyed_by.remove(p);
        }
        cumulative_costs.extend(card.costs.iter().cloned());

        trace_steps.push(CompositionStep {
            step_index: idx,
            pattern_id: card.pattern_id.clone(),
            pattern_version: card.version,
            active_after: active.clone(),
        });
    }

    Ok(CompositionTrace {
        steps: trace_steps,
        final_conditions: active,
        cumulative_costs,
    })
}

// =====================================================================
// VERIFIABLE PATTERN LEDGER
// =====================================================================

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
pub struct EvidenceSummary {
    pub pattern_id: String,
    pub version: u64,
    pub applications: usize,
    pub distinct_domains: BTreeSet<String>,
    pub supported: usize,
    pub partial: usize,
    pub failed: usize,
    pub inapplicable: usize,
    pub public_reports: usize,
    pub confidential_reports: usize,
    pub recorded_limits: Vec<String>,
}

/// Verified catalog linking patterns, their domain applications, and
/// observed evidence without collapsing failures into a single popularity score.
#[derive(Default)]
pub struct PatternLedger {
    cards: HashMap<String, PatternCard>,
    applications: HashMap<String, PatternApplication>,
    evidence: HashMap<String, ApplicationEvidence>,
}

impl PatternLedger {
    pub fn new() -> Self {
        Self::default()
    }

    pub fn register_card(&mut self, card: PatternCard) -> Result<String> {
        card.verify()?;
        if let Some(parent_hash) = &card.derived_from {
            let parent = self.cards.get(parent_hash).ok_or_else(|| {
                Error::Policy("derived_from references unknown parent pattern hash".into())
            })?;
            if parent.pattern_id != card.pattern_id {
                return Err(Error::Policy(
                    "derived pattern must preserve pattern_id of its parent".into(),
                ));
            }
            if card.version <= parent.version {
                return Err(Error::Policy(
                    "derived pattern version must be strictly greater than parent version".into(),
                ));
            }
        }
        let h = card.hash()?;
        self.cards.insert(h.clone(), card);
        Ok(h)
    }

    pub fn register_application(&mut self, app: PatternApplication) -> Result<String> {
        let card = self.cards.get(&app.pattern_hash).ok_or_else(|| {
            Error::Policy("application references unknown pattern_hash".into())
        })?;
        app.verify_against(card)?;
        let h = app.hash()?;
        self.applications.insert(h.clone(), app);
        Ok(h)
    }

    pub fn register_evidence(&mut self, ev: ApplicationEvidence) -> Result<String> {
        let app = self.applications.get(&ev.application_hash).ok_or_else(|| {
            Error::Policy("evidence references unknown application_hash".into())
        })?;
        ev.verify_against(app)?;
        let h = ev.hash()?;
        self.evidence.insert(h.clone(), ev);
        Ok(h)
    }

    pub fn get_card(&self, hash: &str) -> Option<&PatternCard> {
        self.cards.get(hash)
    }

    /// Find all registered patterns that claim to provide a given capability or state.
    pub fn find_providing(&self, capability: &str) -> Vec<&PatternCard> {
        let mut out: Vec<&PatternCard> = self
            .cards
            .values()
            .filter(|c| c.provides.iter().any(|p| p == capability))
            .collect();
        out.sort_by(|a, b| {
            a.pattern_id
                .cmp(&b.pattern_id)
                .then_with(|| a.version.cmp(&b.version))
        });
        out
    }

    /// Compute an auditable summary for one exact `PatternCard` hash.
    /// Evidence on an earlier revision stays on that revision.
    pub fn evidence_summary(&self, card_hash: &str) -> Result<EvidenceSummary> {
        let card = self
            .cards
            .get(card_hash)
            .ok_or_else(|| Error::Policy("pattern hash not found".into()))?;

        let mut app_hashes = BTreeSet::new();
        let mut distinct_domains = BTreeSet::new();
        for (ah, app) in &self.applications {
            if app.pattern_hash == card_hash {
                app_hashes.insert(ah.clone());
                distinct_domains.insert(app.domain.clone());
            }
        }

        let mut supported = 0;
        let mut partial = 0;
        let mut failed = 0;
        let mut inapplicable = 0;
        let mut public_reports = 0;
        let mut confidential_reports = 0;
        let mut recorded_limits = Vec::new();

        for ev in self.evidence.values() {
            if app_hashes.contains(&ev.application_hash) {
                match ev.verdict {
                    EvidenceVerdict::Supported => supported += 1,
                    EvidenceVerdict::Partial => partial += 1,
                    EvidenceVerdict::Failed => failed += 1,
                    EvidenceVerdict::Inapplicable => inapplicable += 1,
                }
                match ev.source_visibility {
                    SourceVisibility::Public { .. } => public_reports += 1,
                    SourceVisibility::ConfidentialUninspectable => confidential_reports += 1,
                }
                if let Some(note) = &ev.failure_or_limit_note {
                    recorded_limits.push(note.clone());
                }
            }
        }
        recorded_limits.sort();

        Ok(EvidenceSummary {
            pattern_id: card.pattern_id.clone(),
            version: card.version,
            applications: app_hashes.len(),
            distinct_domains,
            supported,
            partial,
            failed,
            inapplicable,
            public_reports,
            confidential_reports,
            recorded_limits,
        })
    }
}
