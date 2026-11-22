//! Mind adapter wiring a 6-archetype fixed-point `NeuralCluster` into the
//! `open-worlds` observation -> proposal -> world-check -> outcome boundary.
//!
//! Supports deterministic causal lookahead, stdio JSON-lines plugin execution,
//! cryptographically verified snapshot/restart, and full offline session auditing.

use crate::did::{DidKey, Keypair};
use crate::error::{Error, Result};
use crate::hash::{body_for_signing, hash_of};
use crate::neuro::{
    verify_cluster_trace, ClusterTopology, ClusterTrace, NeuralCluster, SynapseWeights, TriSignal,
    UnitState, SCALE,
};
use crate::proof::{Proof, ProofOrArray};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, HashMap};

// =====================================================================
// WORLD <-> MIND PROTOCOL CONTRACTS
// =====================================================================

/// Bounded observation delivered by a world host at the start of `tick`.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct WorldObservation {
    pub world_id: DidKey,
    pub tick: u64,
    pub sensory_field: TriSignal,
    pub available_actions: Vec<String>,
    pub attention_cue: i64,
}

impl WorldObservation {
    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }
}

/// Action proposed by a mind for one specific `(world_id, tick)`.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
pub enum MindAction {
    Wait,
    Act { name: String },
}

/// Signed action proposal bound explicitly to one observation and internal
/// sensory cluster micro-tick (`2T`), preventing stale or cross-world replay.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ActionProposal {
    pub mind_id: DidKey,
    pub cluster_id: DidKey,
    pub world_id: DidKey,
    pub tick: u64,
    pub observation_hash: String,
    pub sensory_tick_hash: String,
    pub action: MindAction,
    pub confidence_red: i64,
    pub brace_level_blue: i64,
    pub order_alert_red: i64,
    pub proof: ProofOrArray,
}

impl ActionProposal {
    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }

    pub fn verify(&self) -> Result<()> {
        let body = body_for_signing(self)?;
        let proof = self
            .proof
            .find_by_method(&self.mind_id)
            .ok_or_else(|| Error::Verification("action proposal: missing mind proof".into()))?;
        proof.verify(&body)
    }
}

/// World-signed consequence of evaluating one `ActionProposal`.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ActionOutcome {
    pub world_id: DidKey,
    pub tick: u64,
    pub proposal_hash: String,
    pub accepted: bool,
    pub refusal_reason: Option<String>,
    pub teaching_action: Option<String>,
    pub shock: i64,
    pub proof: ProofOrArray,
}

impl ActionOutcome {
    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }

    pub fn verify(&self) -> Result<()> {
        let body = body_for_signing(self)?;
        let proof = self
            .proof
            .find_by_method(&self.world_id)
            .ok_or_else(|| Error::Verification("action outcome: missing world proof".into()))?;
        proof.verify(&body)
    }
}

/// Signed per-turn receipt binding an observation, proposal, world outcome,
/// and the internal plasticity micro-tick (`2T + 1`) into one auditable chain.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct MindTurnReceipt {
    pub mind_id: DidKey,
    pub turn_index: u64,
    pub prev: Option<String>,
    pub observation: WorldObservation,
    pub proposal: ActionProposal,
    pub outcome: ActionOutcome,
    pub outcome_tick_hash: String,
    pub proof: ProofOrArray,
}

impl MindTurnReceipt {
    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }

    pub fn verify(&self) -> Result<()> {
        let body = body_for_signing(self)?;
        let proof = self
            .proof
            .find_by_method(&self.mind_id)
            .ok_or_else(|| Error::Verification("mind turn receipt: missing mind proof".into()))?;
        proof.verify(&body)
    }
}

// =====================================================================
// DECLARATIVE BINDINGS & CAUSAL PREVIEW
// =====================================================================

/// Maps world observations and outcomes onto named units inside a `NeuralCluster`.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct MindBindings {
    /// Sensory receptor unit IDs receiving `obs.sensory_field`.
    pub sensory_receptors: Vec<String>,
    /// Maps world action names (e.g. `"act_0"`) to cluster unit IDs.
    pub action_units: BTreeMap<String, String>,
    /// Optional cerebellar Purkinje unit emitting Blue `brace_level` and receiving Yellow `shock`.
    pub purkinje_unit: Option<String>,
    /// Optional Jeffress coincidence unit emitting Red `order_alert`.
    pub coincidence_unit: Option<String>,
    /// Optional Pyramidal unit pulsed on surprise (mismatch or refused action).
    pub pyramidal_unit: Option<String>,
    /// Optional ModulatorNucleus receiving `obs.attention_cue`.
    pub modulator_unit: Option<String>,
    /// Minimum Red output required to emit `MindAction::Act` instead of `Wait`.
    pub action_threshold: i64,
    /// Red drive injected into the target action unit on a teaching correction.
    pub teaching_drive: i64,
    /// Yellow gate injected into action units on a teaching correction.
    pub surprise_yellow: i64,
}

impl MindBindings {
    pub fn validate(&self, topology: &ClusterTopology) -> Result<()> {
        let has = |id: &str| topology.units.iter().any(|u| u.id == id);
        if self.sensory_receptors.is_empty() {
            return Err(Error::Policy(
                "mind bindings: sensory_receptors cannot be empty".into(),
            ));
        }
        for id in &self.sensory_receptors {
            if !has(id) {
                return Err(Error::Policy(format!(
                    "mind bindings: unknown sensory_receptor {:?}",
                    id
                )));
            }
        }
        if self.action_units.is_empty() {
            return Err(Error::Policy(
                "mind bindings: action_units cannot be empty".into(),
            ));
        }
        for (act_name, uid) in &self.action_units {
            if act_name.trim().is_empty() || !has(uid) {
                return Err(Error::Policy(format!(
                    "mind bindings: invalid action_unit mapping {:?} -> {:?}",
                    act_name, uid
                )));
            }
        }
        for (label, opt) in [
            ("purkinje_unit", &self.purkinje_unit),
            ("coincidence_unit", &self.coincidence_unit),
            ("pyramidal_unit", &self.pyramidal_unit),
            ("modulator_unit", &self.modulator_unit),
        ] {
            if let Some(uid) = opt {
                if !has(uid) {
                    return Err(Error::Policy(format!(
                        "mind bindings: unknown {label} {:?}",
                        uid
                    )));
                }
            }
        }
        if self.action_threshold < 0 || self.teaching_drive < 0 || self.surprise_yellow < 0 {
            return Err(Error::Policy(
                "mind bindings: thresholds and drives must be >= 0".into(),
            ));
        }
        Ok(())
    }
}

/// Pure, non-mutating 1-micro-tick causal lookahead of a `NeuralCluster`
/// with zero external inputs, matching `NeuralCluster::step(empty)` exactly.
pub fn preview_next_units(
    topology: &ClusterTopology,
    prev_units: &BTreeMap<String, UnitState>,
    prev_weights: &[SynapseWeights],
) -> BTreeMap<String, UnitState> {
    let mut in_r: HashMap<&str, i64> = HashMap::new();
    let mut in_b: HashMap<&str, i64> = HashMap::new();
    let mut in_y: HashMap<&str, i64> = HashMap::new();

    for u in &topology.units {
        in_r.insert(u.id.as_str(), 0);
        in_b.insert(u.id.as_str(), 0);
        in_y.insert(u.id.as_str(), 0);
    }

    for (spec, w) in topology.synapses.iter().zip(prev_weights.iter()) {
        let pre_out = prev_units[&spec.from].output;
        let eff_r = w.effective_red();
        let dr = (((eff_r as i128) * (pre_out.red as i128)) / (SCALE as i128)).max(0) as i64;
        let db =
            (((spec.base_blue as i128) * (pre_out.blue as i128)) / (SCALE as i128)).max(0) as i64;
        let dy = (((spec.base_yellow as i128) * (pre_out.yellow as i128)) / (SCALE as i128))
            .max(0) as i64;
        *in_r.get_mut(spec.to.as_str()).unwrap() += dr;
        *in_b.get_mut(spec.to.as_str()).unwrap() += db;
        *in_y.get_mut(spec.to.as_str()).unwrap() += dy;
    }

    let mut next_units = BTreeMap::new();
    for u in &topology.units {
        let incoming = TriSignal {
            red: in_r[u.id.as_str()],
            blue: in_b[u.id.as_str()],
            yellow: in_y[u.id.as_str()],
        };
        next_units.insert(u.id.clone(), u.kind.step(&prev_units[&u.id], incoming));
    }
    next_units
}

fn encode_sensory_inputs(
    bindings: &MindBindings,
    obs: &WorldObservation,
) -> BTreeMap<String, TriSignal> {
    let mut ext = BTreeMap::new();
    for uid in &bindings.sensory_receptors {
        ext.insert(uid.clone(), obs.sensory_field);
    }
    if obs.attention_cue > 0 {
        if let Some(mod_id) = &bindings.modulator_unit {
            let entry = ext.entry(mod_id.clone()).or_default();
            entry.yellow = entry.yellow.saturating_add(obs.attention_cue);
        }
    }
    ext
}

fn decode_proposal_outputs(
    bindings: &MindBindings,
    preview: &BTreeMap<String, UnitState>,
    available_actions: &[String],
) -> (MindAction, i64, i64, i64) {
    let mut best_name: Option<String> = None;
    let mut best_score: i64 = 0;

    for (act_name, uid) in &bindings.action_units {
        if !available_actions.iter().any(|a| a == act_name) {
            continue;
        }
        let score = preview.get(uid).map(|st| st.output.red).unwrap_or(0);
        if score >= bindings.action_threshold && score > best_score {
            best_score = score;
            best_name = Some(act_name.clone());
        }
    }

    let action = match best_name {
        Some(name) => MindAction::Act { name },
        None => MindAction::Wait,
    };
    let brace = bindings
        .purkinje_unit
        .as_ref()
        .and_then(|id| preview.get(id))
        .map(|st| st.output.blue)
        .unwrap_or(0);
    let alert = bindings
        .coincidence_unit
        .as_ref()
        .and_then(|id| preview.get(id))
        .map(|st| st.output.red)
        .unwrap_or(0);

    (action, best_score, brace, alert)
}

fn encode_outcome_inputs(
    bindings: &MindBindings,
    proposal: &ActionProposal,
    outcome: &ActionOutcome,
) -> BTreeMap<String, TriSignal> {
    let mut ext: BTreeMap<String, TriSignal> = BTreeMap::new();

    if outcome.shock > 0 {
        if let Some(pid) = &bindings.purkinje_unit {
            ext.insert(pid.clone(), TriSignal::raw(0, 0, outcome.shock));
        }
    }

    let action_mismatch = match (&proposal.action, &outcome.teaching_action) {
        (MindAction::Act { name }, Some(expected)) => name != expected,
        (MindAction::Wait, Some(_)) => true,
        _ => false,
    };
    let surprised = !outcome.accepted || action_mismatch;

    if surprised {
        if let Some(pyr_id) = &bindings.pyramidal_unit {
            let entry = ext.entry(pyr_id.clone()).or_default();
            entry.red = entry.red.saturating_add(SCALE);
        }
        if let Some(expected_action) = &outcome.teaching_action {
            for (act_name, uid) in &bindings.action_units {
                let target_red = if act_name == expected_action {
                    bindings.teaching_drive
                } else {
                    0
                };
                let entry = ext.entry(uid.clone()).or_default();
                entry.red = entry.red.saturating_add(target_red);
                entry.yellow = entry.yellow.saturating_add(bindings.surprise_yellow);
            }
        }
    }

    ext
}

// =====================================================================
// MIND TRAIT, NEUROMIND ADAPTER, STDIO PLUGIN & SNAPSHOT/RESTORE
// =====================================================================

pub trait Mind {
    fn mind_id(&self) -> DidKey;
    fn decide(&mut self, obs: &WorldObservation) -> Result<ActionProposal>;
    fn integrate_outcome(&mut self, outcome: &ActionOutcome) -> Result<MindTurnReceipt>;
}

/// Complete auditable session artifact (and durable restart snapshot).
/// Never contains private key material.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct MindSession {
    pub mind_id: DidKey,
    pub bindings: MindBindings,
    pub cluster_trace: ClusterTrace,
    pub receipts: Vec<MindTurnReceipt>,
}

/// Stdio JSON-lines request envelope for running `NeuroMind` as an isolated plugin process.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(tag = "op", rename_all = "snake_case")]
pub enum PluginRequest {
    Decide { observation: WorldObservation },
    Outcome { outcome: ActionOutcome },
    ExportSession,
}

/// Stdio JSON-lines response envelope emitted by `NeuroMind::handle_json_line`.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(tag = "op", rename_all = "snake_case")]
pub enum PluginResponse {
    Proposal { proposal: ActionProposal },
    Receipt { receipt: MindTurnReceipt },
    Session { session: MindSession },
}

struct PendingTurn {
    observation: WorldObservation,
    proposal: ActionProposal,
    proposal_hash: String,
}

/// Continuing neural participant mind wrapping a 6-archetype `NeuralCluster`.
pub struct NeuroMind {
    mind_kp: Keypair,
    topology: ClusterTopology,
    cluster: NeuralCluster,
    bindings: MindBindings,
    pending: Option<PendingTurn>,
    receipts: Vec<MindTurnReceipt>,
}

impl NeuroMind {
    pub fn new(
        mind_kp: Keypair,
        cluster: NeuralCluster,
        bindings: MindBindings,
    ) -> Result<Self> {
        let topology = cluster.trace().topology;
        topology.validate()?;
        bindings.validate(&topology)?;
        Ok(NeuroMind {
            mind_kp,
            topology,
            cluster,
            bindings,
            pending: None,
            receipts: Vec::new(),
        })
    }

    pub fn cluster(&self) -> &NeuralCluster {
        &self.cluster
    }

    pub fn bindings(&self) -> &MindBindings {
        &self.bindings
    }

    pub fn receipts(&self) -> &[MindTurnReceipt] {
        &self.receipts
    }

    pub fn export_session(&self) -> Result<MindSession> {
        if self.pending.is_some() {
            return Err(Error::Policy(
                "cannot export session while a turn outcome is still pending".into(),
            ));
        }
        Ok(MindSession {
            mind_id: self.mind_kp.did(),
            bindings: self.bindings.clone(),
            cluster_trace: self.cluster.trace(),
            receipts: self.receipts.clone(),
        })
    }

    /// Restores a `NeuroMind` in a fresh process by verifying the exported
    /// `MindSession` offline and deterministically replaying `ClusterTrace`
    /// to recover exact live fast weights, delay buffers, and tonic Yellow.
    pub fn restore(
        session: MindSession,
        mind_kp: Keypair,
        cluster_kp: Keypair,
    ) -> Result<Self> {
        if mind_kp.did() != session.mind_id {
            return Err(Error::Verification(
                "mind restore: mind_kp does not match session.mind_id".into(),
            ));
        }
        if cluster_kp.did() != session.cluster_trace.topology.cluster_id {
            return Err(Error::Verification(
                "mind restore: cluster_kp does not match topology.cluster_id".into(),
            ));
        }
        verify_mind_session(&session)?;

        let topology = session.cluster_trace.topology.clone();
        let mut cluster = NeuralCluster::new(
            &topology.name,
            cluster_kp,
            topology.units.clone(),
            topology.synapses.clone(),
        )?;
        for tick_rec in &session.cluster_trace.ticks {
            cluster.step(tick_rec.external_inputs.clone())?;
        }

        Ok(NeuroMind {
            mind_kp,
            topology,
            cluster,
            bindings: session.bindings,
            pending: None,
            receipts: session.receipts,
        })
    }

    /// Processes one newline-delimited JSON request for `open-worlds` stdio plugin loops.
    pub fn handle_json_line(&mut self, line: &str) -> Result<String> {
        let req: PluginRequest =
            serde_json::from_str(line).map_err(|e| Error::Serialization(e.to_string()))?;
        let resp = match req {
            PluginRequest::Decide { observation } => PluginResponse::Proposal {
                proposal: self.decide(&observation)?,
            },
            PluginRequest::Outcome { outcome } => PluginResponse::Receipt {
                receipt: self.integrate_outcome(&outcome)?,
            },
            PluginRequest::ExportSession => PluginResponse::Session {
                session: self.export_session()?,
            },
        };
        serde_json::to_string(&resp).map_err(|e| Error::Serialization(e.to_string()))
    }
}

impl Mind for NeuroMind {
    fn mind_id(&self) -> DidKey {
        self.mind_kp.did()
    }

    fn decide(&mut self, obs: &WorldObservation) -> Result<ActionProposal> {
        if self.pending.is_some() {
            return Err(Error::Policy(
                "cannot decide next tick before integrating previous turn outcome".into(),
            ));
        }
        let obs_hash = obs.hash()?;
        let ext0 = encode_sensory_inputs(&self.bindings, obs);
        let sensory_rec = self.cluster.step(ext0)?;
        let sensory_tick_hash = sensory_rec.hash()?;

        let preview = preview_next_units(
            &self.topology,
            &sensory_rec.unit_states,
            &sensory_rec.synapse_weights,
        );
        let (action, confidence_red, brace_level_blue, order_alert_red) =
            decode_proposal_outputs(&self.bindings, &preview, &obs.available_actions);

        let mut proposal = ActionProposal {
            mind_id: self.mind_kp.did(),
            cluster_id: self.topology.cluster_id.clone(),
            world_id: obs.world_id.clone(),
            tick: obs.tick,
            observation_hash: obs_hash,
            sensory_tick_hash,
            action,
            confidence_red,
            brace_level_blue,
            order_alert_red,
            proof: ProofOrArray::placeholder(),
        };
        let body = body_for_signing(&proposal)?;
        let sig = self.mind_kp.sign(&body);
        proposal.proof = ProofOrArray::single(Proof::create(&self.mind_kp, &sig));
        let proposal_hash = proposal.hash()?;

        self.pending = Some(PendingTurn {
            observation: obs.clone(),
            proposal: proposal.clone(),
            proposal_hash,
        });
        Ok(proposal)
    }

    fn integrate_outcome(&mut self, outcome: &ActionOutcome) -> Result<MindTurnReceipt> {
        outcome.verify()?;
        let Some(pending) = &self.pending else {
            return Err(Error::Policy(
                "no pending turn awaiting an outcome".into(),
            ));
        };
        if outcome.world_id != pending.observation.world_id
            || outcome.tick != pending.observation.tick
            || outcome.proposal_hash != pending.proposal_hash
        {
            return Err(Error::Verification(
                "outcome does not match pending turn world_id, tick, or proposal_hash".into(),
            ));
        }

        let ext1 = encode_outcome_inputs(&self.bindings, &pending.proposal, outcome);
        let outcome_rec = self.cluster.step(ext1)?;
        let outcome_tick_hash = outcome_rec.hash()?;

        let prev = match self.receipts.last() {
            Some(r) => Some(r.hash()?),
            None => None,
        };
        let pending = self.pending.take().unwrap();
        let mut receipt = MindTurnReceipt {
            mind_id: self.mind_kp.did(),
            turn_index: self.receipts.len() as u64,
            prev,
            observation: pending.observation,
            proposal: pending.proposal,
            outcome: outcome.clone(),
            outcome_tick_hash,
            proof: ProofOrArray::placeholder(),
        };
        let body = body_for_signing(&receipt)?;
        let sig = self.mind_kp.sign(&body);
        receipt.proof = ProofOrArray::single(Proof::create(&self.mind_kp, &sig));
        self.receipts.push(receipt.clone());
        Ok(receipt)
    }
}

// =====================================================================
// OFFLINE SESSION AUDITOR
// =====================================================================

/// Independently audits an entire `MindSession` offline:
/// verifies the internal `ClusterTrace`, every signed turn receipt,
/// exact sensory/outcome encoding, and deterministic causal decoding
/// of every `ActionProposal` from the internal neural state.
pub fn verify_mind_session(session: &MindSession) -> Result<()> {
    verify_cluster_trace(&session.cluster_trace)?;
    session.bindings.validate(&session.cluster_trace.topology)?;

    let expected_ticks = session.receipts.len() * 2;
    if session.cluster_trace.ticks.len() != expected_ticks {
        return Err(Error::Verification(format!(
            "mind session: cluster trace has {} ticks, expected {} (2 per turn)",
            session.cluster_trace.ticks.len(),
            expected_ticks
        )));
    }

    let mut prev_receipt_hash: Option<String> = None;

    for (idx, receipt) in session.receipts.iter().enumerate() {
        if receipt.turn_index != idx as u64 {
            return Err(Error::Chain(format!(
                "mind session turn {idx}: turn_index {} != expected {idx}",
                receipt.turn_index
            )));
        }
        if receipt.mind_id != session.mind_id {
            return Err(Error::Verification(format!(
                "mind session turn {idx}: mind_id mismatch"
            )));
        }
        if receipt.prev != prev_receipt_hash {
            return Err(Error::Chain(format!(
                "mind session turn {idx}: prev receipt hash mismatch"
            )));
        }
        receipt.verify()?;
        receipt.proposal.verify()?;
        receipt.outcome.verify()?;

        if receipt.proposal.mind_id != session.mind_id
            || receipt.proposal.cluster_id != session.cluster_trace.topology.cluster_id
            || receipt.proposal.world_id != receipt.observation.world_id
            || receipt.proposal.tick != receipt.observation.tick
        {
            return Err(Error::Verification(format!(
                "mind session turn {idx}: proposal identity or world/tick binding mismatch"
            )));
        }
        if receipt.proposal.observation_hash != receipt.observation.hash()? {
            return Err(Error::Verification(format!(
                "mind session turn {idx}: proposal observation_hash mismatch"
            )));
        }
        if receipt.outcome.world_id != receipt.observation.world_id
            || receipt.outcome.tick != receipt.observation.tick
            || receipt.outcome.proposal_hash != receipt.proposal.hash()?
        {
            return Err(Error::Verification(format!(
                "mind session turn {idx}: outcome binding mismatch"
            )));
        }

        // Verify micro-tick 2*idx (sensory transduction) and exact causal proposal decoding.
        let sensory_tick = &session.cluster_trace.ticks[2 * idx];
        if receipt.proposal.sensory_tick_hash != sensory_tick.hash()? {
            return Err(Error::Verification(format!(
                "mind session turn {idx}: sensory_tick_hash mismatch"
            )));
        }
        let expected_ext0 = encode_sensory_inputs(&session.bindings, &receipt.observation);
        if sensory_tick.external_inputs != expected_ext0 {
            return Err(Error::Verification(format!(
                "mind session turn {idx}: sensory external_inputs do not match observation"
            )));
        }
        let preview = preview_next_units(
            &session.cluster_trace.topology,
            &sensory_tick.unit_states,
            &sensory_tick.synapse_weights,
        );
        let (exp_action, exp_conf, exp_brace, exp_alert) = decode_proposal_outputs(
            &session.bindings,
            &preview,
            &receipt.observation.available_actions,
        );
        if receipt.proposal.action != exp_action
            || receipt.proposal.confidence_red != exp_conf
            || receipt.proposal.brace_level_blue != exp_brace
            || receipt.proposal.order_alert_red != exp_alert
        {
            return Err(Error::Verification(format!(
                "mind session turn {idx}: proposal does not match deterministic neural decode"
            )));
        }

        // Verify micro-tick 2*idx + 1 (outcome integration) matches outcome encoding
        // and preserves bit-for-bit Purkinje brace & Jeffress coincidence values.
        let outcome_tick = &session.cluster_trace.ticks[2 * idx + 1];
        if receipt.outcome_tick_hash != outcome_tick.hash()? {
            return Err(Error::Verification(format!(
                "mind session turn {idx}: outcome_tick_hash mismatch"
            )));
        }
        let expected_ext1 =
            encode_outcome_inputs(&session.bindings, &receipt.proposal, &receipt.outcome);
        if outcome_tick.external_inputs != expected_ext1 {
            return Err(Error::Verification(format!(
                "mind session turn {idx}: outcome external_inputs do not match outcome"
            )));
        }
        if let Some(pid) = &session.bindings.purkinje_unit {
            if outcome_tick.unit_states[pid].output.blue != receipt.proposal.brace_level_blue {
                return Err(Error::Verification(format!(
                    "mind session turn {idx}: committed purkinje brace != proposed brace"
                )));
            }
        }
        if let Some(cid) = &session.bindings.coincidence_unit {
            if outcome_tick.unit_states[cid].output.red != receipt.proposal.order_alert_red {
                return Err(Error::Verification(format!(
                    "mind session turn {idx}: committed coincidence alert != proposed alert"
                )));
            }
        }

        prev_receipt_hash = Some(receipt.hash()?);
    }

    Ok(())
}

// =====================================================================
// CLOSED-LOOP WORLD HOST: ADAPTIVE ARENA WORLD
// =====================================================================

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ArenaStepSpec {
    pub sensory_field: TriSignal,
    pub available_actions: Vec<String>,
    pub teaching_action: Option<String>,
    pub shock: i64,
    pub attention_cue: i64,
}

/// Deterministic world host verifying proposals against world law without
/// ever needing access to the mind's internal neural weights.
pub struct AdaptiveArenaWorld {
    world_kp: Keypair,
    schedule: Vec<ArenaStepSpec>,
    tick: u64,
    current_obs: Option<WorldObservation>,
}

impl AdaptiveArenaWorld {
    pub fn new(world_kp: Keypair, schedule: Vec<ArenaStepSpec>) -> Result<Self> {
        if schedule.is_empty() {
            return Err(Error::Policy("arena schedule cannot be empty".into()));
        }
        Ok(AdaptiveArenaWorld {
            world_kp,
            schedule,
            tick: 0,
            current_obs: None,
        })
    }

    pub fn world_id(&self) -> DidKey {
        self.world_kp.did()
    }

    pub fn tick(&self) -> u64 {
        self.tick
    }

    pub fn is_finished(&self) -> bool {
        (self.tick as usize) >= self.schedule.len()
    }

    pub fn observe(&mut self) -> Result<WorldObservation> {
        let step = self
            .schedule
            .get(self.tick as usize)
            .ok_or_else(|| Error::Policy("arena schedule completed".into()))?;
        let obs = WorldObservation {
            world_id: self.world_id(),
            tick: self.tick,
            sensory_field: step.sensory_field,
            available_actions: step.available_actions.clone(),
            attention_cue: step.attention_cue,
        };
        self.current_obs = Some(obs.clone());
        Ok(obs)
    }

    /// Checks a mind's signed `ActionProposal` against world identity, tick,
    /// observation hash, and available actions, emitting a signed `ActionOutcome`.
    pub fn apply_proposal(&mut self, proposal: &ActionProposal) -> Result<ActionOutcome> {
        proposal.verify()?;
        let obs = self
            .current_obs
            .as_ref()
            .ok_or_else(|| Error::Policy("world must emit an observation before applying a proposal".into()))?;
        if proposal.world_id != self.world_id() {
            return Err(Error::Policy("proposal targets a different world_id".into()));
        }
        if proposal.tick != self.tick {
            return Err(Error::Policy(format!(
                "stale proposal: tick {} != current world tick {}",
                proposal.tick, self.tick
            )));
        }
        if proposal.observation_hash != obs.hash()? {
            return Err(Error::Verification(
                "proposal observation_hash does not match current observation".into(),
            ));
        }

        let step = &self.schedule[self.tick as usize];
        let (accepted, refusal_reason) = match &proposal.action {
            MindAction::Wait => (true, None),
            MindAction::Act { name } => {
                if step.available_actions.iter().any(|a| a == name) {
                    (true, None)
                } else {
                    (
                        false,
                        Some(format!("action {:?} is not available at tick {}", name, self.tick)),
                    )
                }
            }
        };

        let mut outcome = ActionOutcome {
            world_id: self.world_id(),
            tick: self.tick,
            proposal_hash: proposal.hash()?,
            accepted,
            refusal_reason,
            teaching_action: step.teaching_action.clone(),
            shock: step.shock,
            proof: ProofOrArray::placeholder(),
        };
        let body = body_for_signing(&outcome)?;
        let sig = self.world_kp.sign(&body);
        outcome.proof = ProofOrArray::single(Proof::create(&self.world_kp, &sig));

        self.tick += 1;
        self.current_obs = None;
        Ok(outcome)
    }
}
