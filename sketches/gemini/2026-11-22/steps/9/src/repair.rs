//! Repair World: cooperative multi-station fault diagnosis, non-destructive
//! trial branches, station-scoped commits, and offline-verifiable repair logs.

use crate::did::{DidKey, Keypair};
use crate::error::{Error, Result};
use crate::hash::{body_for_signing, hash_of};
use crate::proof::{Proof, ProofOrArray};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LinkSpec {
    pub link_id: String,
    pub from: String,
    pub to: String,
    pub delay: u64,
    pub min_delay: u64,
    pub max_delay: u64,
    pub enabled: bool,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GateSpec {
    pub gate_id: String,
    pub open_at: u64,
    pub close_at: u64,
    pub max_close_at: u64,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct MechanismConfig {
    pub source_node: String,
    pub sink_node: String,
    pub links: Vec<LinkSpec>,
    pub gates: Vec<GateSpec>,
}

impl MechanismConfig {
    pub fn validate(&self) -> Result<()> {
        if self.source_node.trim().is_empty() || self.sink_node.trim().is_empty() {
            return Err(Error::Policy(
                "mechanism: source_node and sink_node must be non-empty".into(),
            ));
        }
        if self.links.is_empty() {
            return Err(Error::Policy(
                "mechanism: must declare at least one link".into(),
            ));
        }
        let mut seen_links = HashSet::new();
        for link in &self.links {
            if link.link_id.trim().is_empty() || !seen_links.insert(link.link_id.clone()) {
                return Err(Error::Policy(
                    "mechanism: link_ids must be non-empty and unique".into(),
                ));
            }
            if link.from.trim().is_empty() || link.to.trim().is_empty() {
                return Err(Error::Policy(
                    "mechanism: link endpoints must be non-empty".into(),
                ));
            }
            if link.min_delay == 0 || link.min_delay > link.max_delay {
                return Err(Error::Policy(
                    "mechanism: link min_delay must be >= 1 and <= max_delay".into(),
                ));
            }
            if link.delay < link.min_delay || link.delay > link.max_delay {
                return Err(Error::Policy(
                    "mechanism: link delay outside [min_delay, max_delay]".into(),
                ));
            }
        }
        let mut seen_gates = HashSet::new();
        for gate in &self.gates {
            if gate.gate_id.trim().is_empty() || !seen_gates.insert(gate.gate_id.clone()) {
                return Err(Error::Policy(
                    "mechanism: gate_ids must be non-empty and unique".into(),
                ));
            }
            if gate.open_at > gate.close_at || gate.close_at > gate.max_close_at {
                return Err(Error::Policy(
                    "mechanism: gate must satisfy open_at <= close_at <= max_close_at".into(),
                ));
            }
        }
        Ok(())
    }

    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RepairTestCase {
    pub name: String,
    pub input_time: u64,
    pub max_delivery_time: u64,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RepairLaw {
    pub topic: String,
    pub initial_config: MechanismConfig,
    pub declared_suite: Vec<RepairTestCase>,
    pub horizon: u64,
    pub material_budget: u64,
    pub max_trials: u64,
}

impl RepairLaw {
    pub fn validate(&self) -> Result<()> {
        if self.topic.trim().is_empty() {
            return Err(Error::Policy("repair law: topic cannot be empty".into()));
        }
        self.initial_config.validate()?;
        if self.declared_suite.is_empty() {
            return Err(Error::Policy(
                "repair law: declared_suite must contain at least one test case".into(),
            ));
        }
        if self.horizon == 0 {
            return Err(Error::Policy("repair law: horizon must be >= 1".into()));
        }
        let mut seen_cases = HashSet::new();
        for tc in &self.declared_suite {
            if tc.name.trim().is_empty() || !seen_cases.insert(tc.name.clone()) {
                return Err(Error::Policy(
                    "repair law: test case names must be non-empty and unique".into(),
                ));
            }
            if tc.input_time > tc.max_delivery_time || tc.max_delivery_time > self.horizon {
                return Err(Error::Policy(
                    "repair law: test case must satisfy input_time <= max_delivery_time <= horizon"
                        .into(),
                ));
            }
        }
        Ok(())
    }

    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum StationRole {
    RoutingStation,
    TimingStation,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "adjustment", rename_all = "snake_case")]
pub enum Adjustment {
    SetLinkDelay { link_id: String, new_delay: u64 },
    SetLinkEnabled { link_id: String, enabled: bool },
    SetGateWindow {
        gate_id: String,
        open_at: u64,
        close_at: u64,
    },
}

impl Adjustment {
    pub fn required_station(&self) -> StationRole {
        match self {
            Adjustment::SetLinkDelay { .. } | Adjustment::SetLinkEnabled { .. } => {
                StationRole::RoutingStation
            }
            Adjustment::SetGateWindow { .. } => StationRole::TimingStation,
        }
    }
}

pub fn apply_adjustment(config: &MechanismConfig, adj: &Adjustment) -> Result<MechanismConfig> {
    let mut next = config.clone();
    match adj {
        Adjustment::SetLinkDelay { link_id, new_delay } => {
            let link = next
                .links
                .iter_mut()
                .find(|l| &l.link_id == link_id)
                .ok_or_else(|| Error::Policy(format!("unknown link {:?}", link_id)))?;
            if *new_delay < link.min_delay || *new_delay > link.max_delay {
                return Err(Error::Policy(format!(
                    "link {:?} delay {} outside physical bounds [{}..={}]",
                    link_id, new_delay, link.min_delay, link.max_delay
                )));
            }
            link.delay = *new_delay;
        }
        Adjustment::SetLinkEnabled { link_id, enabled } => {
            let link = next
                .links
                .iter_mut()
                .find(|l| &l.link_id == link_id)
                .ok_or_else(|| Error::Policy(format!("unknown link {:?}", link_id)))?;
            link.enabled = *enabled;
        }
        Adjustment::SetGateWindow {
            gate_id,
            open_at,
            close_at,
        } => {
            let gate = next
                .gates
                .iter_mut()
                .find(|g| &g.gate_id == gate_id)
                .ok_or_else(|| Error::Policy(format!("unknown gate {:?}", gate_id)))?;
            if open_at > close_at || *close_at > gate.max_close_at {
                return Err(Error::Policy(format!(
                    "gate {:?} window [{}..={}] exceeds physical limit {}",
                    gate_id, open_at, close_at, gate.max_close_at
                )));
            }
            gate.open_at = *open_at;
            gate.close_at = *close_at;
        }
    }
    Ok(next)
}

// =====================================================================
// DETERMINISTIC MECHANISM SIMULATION & STATION-SCOPED VIEWS
// =====================================================================

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct LinkObservation {
    pub link_id: String,
    pub from: String,
    pub to: String,
    pub sent_at: u64,
    pub arrived_at: u64,
    pub within_horizon: bool,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GateObservation {
    pub gate_id: String,
    pub arrival_time: u64,
    pub open_at: u64,
    pub close_at: u64,
    pub passed: bool,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SimulationOutcome {
    pub input_time: u64,
    pub delivered_at: Option<u64>,
    pub link_events: Vec<LinkObservation>,
    pub gate_events: Vec<GateObservation>,
}

/// Pure deterministic propagation of one pulse injected at `source_node` at `input_time`.
/// Because every link has `delay >= 1`, simulation terminates strictly within `horizon`.
pub fn simulate(config: &MechanismConfig, input_time: u64, horizon: u64) -> SimulationOutcome {
    let mut arrivals: BTreeMap<u64, BTreeSet<String>> = BTreeMap::new();
    if input_time <= horizon {
        arrivals
            .entry(input_time)
            .or_default()
            .insert(config.source_node.clone());
    }

    let mut link_events = Vec::new();
    let mut gate_events = Vec::new();
    let mut delivered_at: Option<u64> = None;

    while let Some(&t) = arrivals.keys().next() {
        let nodes = arrivals.remove(&t).unwrap();
        if t > horizon {
            break;
        }
        for node in nodes {
            let mut passed = true;
            if let Some(gate) = config.gates.iter().find(|g| g.gate_id == node) {
                passed = gate.open_at <= t && t <= gate.close_at;
                gate_events.push(GateObservation {
                    gate_id: gate.gate_id.clone(),
                    arrival_time: t,
                    open_at: gate.open_at,
                    close_at: gate.close_at,
                    passed,
                });
            }
            if !passed {
                continue;
            }
            if node == config.sink_node && delivered_at.is_none() {
                delivered_at = Some(t);
            }
            for link in &config.links {
                if link.enabled && link.from == node {
                    let arrived_at = t.saturating_add(link.delay);
                    let within_horizon = arrived_at <= horizon;
                    link_events.push(LinkObservation {
                        link_id: link.link_id.clone(),
                        from: link.from.clone(),
                        to: link.to.clone(),
                        sent_at: t,
                        arrived_at,
                        within_horizon,
                    });
                    if within_horizon {
                        arrivals
                            .entry(arrived_at)
                            .or_default()
                            .insert(link.to.clone());
                    }
                }
            }
        }
    }

    SimulationOutcome {
        input_time,
        delivered_at,
        link_events,
        gate_events,
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CaseResult {
    pub case_name: String,
    pub input_time: u64,
    pub max_delivery_time: u64,
    pub delivered_at: Option<u64>,
    pub passed: bool,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SuiteResult {
    pub all_passed: bool,
    pub cases: Vec<CaseResult>,
}

pub fn run_suite(
    config: &MechanismConfig,
    suite: &[RepairTestCase],
    horizon: u64,
) -> SuiteResult {
    let mut cases = Vec::with_capacity(suite.len());
    for tc in suite {
        let outcome = simulate(config, tc.input_time, horizon);
        let passed = outcome
            .delivered_at
            .map(|d| d <= tc.max_delivery_time)
            .unwrap_or(false);
        cases.push(CaseResult {
            case_name: tc.name.clone(),
            input_time: tc.input_time,
            max_delivery_time: tc.max_delivery_time,
            delivered_at: outcome.delivered_at,
            passed,
        });
    }
    let all_passed = cases.iter().all(|c| c.passed);
    SuiteResult { all_passed, cases }
}

/// Partitioned partial observation exposed to one station.
/// Routing sees links only; Timing sees gate windows only.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "station_view", rename_all = "snake_case")]
pub enum StationView {
    Routing {
        input_time: u64,
        links: Vec<LinkSpec>,
        link_events: Vec<LinkObservation>,
        delivered_at: Option<u64>,
    },
    Timing {
        input_time: u64,
        gates: Vec<GateSpec>,
        gate_events: Vec<GateObservation>,
        delivered_at: Option<u64>,
    },
}

// =====================================================================
// PORTABLE REPAIR REPORT & LOG RECORDS
// =====================================================================

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RepairReport {
    pub world_id: DidKey,
    pub final_config: MechanismConfig,
    pub committed_adjustments: Vec<Adjustment>,
    pub checked_suite: SuiteResult,
    pub unresolved_cases: Vec<String>,
    pub lesson_note: String,
    pub author: DidKey,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct WorldOpened {
    pub world_id: DidKey,
    pub law: RepairLaw,
    pub creator_id: DidKey,
    pub ts: u64,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ParticipantJoined {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: String,
    pub participant_id: DidKey,
    pub ts: u64,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct StationAssigned {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: String,
    pub participant_id: DidKey,
    pub station: StationRole,
    pub ts: u64,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TrialBranchTested {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: String,
    pub actor_id: DidKey,
    pub branch_id: String,
    pub adjustments: Vec<Adjustment>,
    pub suite_result: SuiteResult,
    pub remaining_trials: u64,
    pub ts: u64,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AdjustmentCommitted {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: String,
    pub actor_id: DidKey,
    pub station: StationRole,
    pub adjustment: Adjustment,
    pub remaining_material: u64,
    pub config_hash: String,
    pub ts: u64,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct CheckSuiteRun {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: String,
    pub actor_id: DidKey,
    pub config_hash: String,
    pub suite_result: SuiteResult,
    pub ts: u64,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ReportExported {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: String,
    pub report: RepairReport,
    pub ts: u64,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum RepairRecord {
    WorldOpened(WorldOpened),
    ParticipantJoined(ParticipantJoined),
    StationAssigned(StationAssigned),
    TrialBranchTested(TrialBranchTested),
    AdjustmentCommitted(AdjustmentCommitted),
    CheckSuiteRun(CheckSuiteRun),
    ReportExported(ReportExported),
}

impl RepairRecord {
    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }

    pub fn seq(&self) -> u64 {
        match self {
            RepairRecord::WorldOpened(_) => 0,
            RepairRecord::ParticipantJoined(r) => r.seq,
            RepairRecord::StationAssigned(r) => r.seq,
            RepairRecord::TrialBranchTested(r) => r.seq,
            RepairRecord::AdjustmentCommitted(r) => r.seq,
            RepairRecord::CheckSuiteRun(r) => r.seq,
            RepairRecord::ReportExported(r) => r.seq,
        }
    }

    pub fn prev(&self) -> Option<&str> {
        match self {
            RepairRecord::WorldOpened(_) => None,
            RepairRecord::ParticipantJoined(r) => Some(&r.prev),
            RepairRecord::StationAssigned(r) => Some(&r.prev),
            RepairRecord::TrialBranchTested(r) => Some(&r.prev),
            RepairRecord::AdjustmentCommitted(r) => Some(&r.prev),
            RepairRecord::CheckSuiteRun(r) => Some(&r.prev),
            RepairRecord::ReportExported(r) => Some(&r.prev),
        }
    }

    pub fn world_id(&self) -> &DidKey {
        match self {
            RepairRecord::WorldOpened(r) => &r.world_id,
            RepairRecord::ParticipantJoined(r) => &r.world_id,
            RepairRecord::StationAssigned(r) => &r.world_id,
            RepairRecord::TrialBranchTested(r) => &r.world_id,
            RepairRecord::AdjustmentCommitted(r) => &r.world_id,
            RepairRecord::CheckSuiteRun(r) => &r.world_id,
            RepairRecord::ReportExported(r) => &r.world_id,
        }
    }

    pub fn proof(&self) -> &ProofOrArray {
        match self {
            RepairRecord::WorldOpened(r) => &r.proof,
            RepairRecord::ParticipantJoined(r) => &r.proof,
            RepairRecord::StationAssigned(r) => &r.proof,
            RepairRecord::TrialBranchTested(r) => &r.proof,
            RepairRecord::AdjustmentCommitted(r) => &r.proof,
            RepairRecord::CheckSuiteRun(r) => &r.proof,
            RepairRecord::ReportExported(r) => &r.proof,
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct RepairLog {
    pub world_id: DidKey,
    pub law: RepairLaw,
    pub records: Vec<RepairRecord>,
}

// =====================================================================
// EXECUTABLE REPAIR WORLD & OFFLINE VERIFIER
// =====================================================================

fn sign_repair_dual<T, F>(
    mut rec: T,
    actor: &Keypair,
    world: &Keypair,
    wrap: fn(T) -> RepairRecord,
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

pub struct RepairWorld {
    world_id: DidKey,
    law: RepairLaw,
    keypair: Keypair,
    participants: HashSet<DidKey>,
    stations: HashMap<DidKey, StationRole>,
    live_config: MechanismConfig,
    committed_adjustments: Vec<Adjustment>,
    remaining_material: u64,
    remaining_trials: u64,
    records: Vec<RepairRecord>,
}

impl RepairWorld {
    pub fn open(
        law: RepairLaw,
        world_kp: Keypair,
        creator_kp: &Keypair,
        now: u64,
    ) -> Result<Self> {
        law.validate()?;
        let world_id = world_kp.did();
        let creator_id = creator_kp.did();
        let live_config = law.initial_config.clone();
        let remaining_material = law.material_budget;
        let remaining_trials = law.max_trials;

        let opened = WorldOpened {
            world_id: world_id.clone(),
            law: law.clone(),
            creator_id: creator_id.clone(),
            ts: now,
            proof: ProofOrArray::placeholder(),
        };
        let signed = sign_repair_dual(
            opened,
            creator_kp,
            &world_kp,
            RepairRecord::WorldOpened,
            |r, p| r.proof = p,
        )?;
        let mut participants = HashSet::new();
        participants.insert(creator_id);

        Ok(RepairWorld {
            world_id,
            law,
            keypair: world_kp,
            participants,
            stations: HashMap::new(),
            live_config,
            committed_adjustments: Vec::new(),
            remaining_material,
            remaining_trials,
            records: vec![RepairRecord::WorldOpened(signed)],
        })
    }

    pub fn world_id(&self) -> &DidKey {
        &self.world_id
    }

    pub fn law(&self) -> &RepairLaw {
        &self.law
    }

    pub fn live_config(&self) -> &MechanismConfig {
        &self.live_config
    }

    pub fn remaining_material(&self) -> u64 {
        self.remaining_material
    }

    pub fn remaining_trials(&self) -> u64 {
        self.remaining_trials
    }

    pub fn log(&self) -> RepairLog {
        RepairLog {
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
            .ok_or_else(|| Error::Chain("repair world has no seed record".into()))?
            .hash()
    }

    pub fn join(&mut self, participant_kp: &Keypair, now: u64) -> Result<RepairRecord> {
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
        let signed = sign_repair_dual(
            rec,
            participant_kp,
            &self.keypair,
            RepairRecord::ParticipantJoined,
            |r, p| r.proof = p,
        )?;
        let wrapped = RepairRecord::ParticipantJoined(signed);
        self.participants.insert(pid);
        self.records.push(wrapped.clone());
        Ok(wrapped)
    }

    /// Take or revisit a station. Changing stations allows collaborators to
    /// inspect the view their partner was seeing.
    pub fn assign_station(
        &mut self,
        participant_kp: &Keypair,
        station: StationRole,
        now: u64,
    ) -> Result<RepairRecord> {
        let pid = participant_kp.did();
        if !self.participants.contains(&pid) {
            return Err(Error::Policy("actor is not a participant".into()));
        }
        let rec = StationAssigned {
            world_id: self.world_id.clone(),
            seq: self.next_seq(),
            prev: self.last_hash()?,
            participant_id: pid.clone(),
            station,
            ts: now,
            proof: ProofOrArray::placeholder(),
        };
        let signed = sign_repair_dual(
            rec,
            participant_kp,
            &self.keypair,
            RepairRecord::StationAssigned,
            |r, p| r.proof = p,
        )?;
        let wrapped = RepairRecord::StationAssigned(signed);
        self.stations.insert(pid, station);
        self.records.push(wrapped.clone());
        Ok(wrapped)
    }

    /// Read-only partial observation scoped strictly to the actor's current station.
    pub fn inspect_station(&self, actor_id: &DidKey, input_time: u64) -> Result<StationView> {
        if !self.participants.contains(actor_id) {
            return Err(Error::Policy("actor is not a participant".into()));
        }
        let Some(&station) = self.stations.get(actor_id) else {
            return Err(Error::Policy("actor has not taken a station yet".into()));
        };
        if input_time > self.law.horizon {
            return Err(Error::Policy("input_time exceeds world horizon".into()));
        }
        let outcome = simulate(&self.live_config, input_time, self.law.horizon);
        match station {
            StationRole::RoutingStation => Ok(StationView::Routing {
                input_time,
                links: self.live_config.links.clone(),
                link_events: outcome.link_events,
                delivered_at: outcome.delivered_at,
            }),
            StationRole::TimingStation => Ok(StationView::Timing {
                input_time,
                gates: self.live_config.gates.clone(),
                gate_events: outcome.gate_events,
                delivered_at: outcome.delivered_at,
            }),
        }
    }

    /// Evaluates a proposed sequence of adjustments in an isolated trial branch
    /// against `declared_suite` without mutating `live_config` or spending materials.
    pub fn test_trial_branch(
        &mut self,
        actor_kp: &Keypair,
        branch_id: &str,
        adjustments: Vec<Adjustment>,
        now: u64,
    ) -> Result<SuiteResult> {
        let actor_id = actor_kp.did();
        if !self.participants.contains(&actor_id) {
            return Err(Error::Policy("actor is not a participant".into()));
        }
        if branch_id.trim().is_empty() {
            return Err(Error::Policy("branch_id cannot be empty".into()));
        }
        if adjustments.is_empty() {
            return Err(Error::Policy(
                "trial branch requires at least one adjustment".into(),
            ));
        }
        if self.remaining_trials == 0 {
            return Err(Error::Policy("trial branch budget exhausted".into()));
        }

        let mut trial_cfg = self.live_config.clone();
        for adj in &adjustments {
            trial_cfg = apply_adjustment(&trial_cfg, adj)?;
        }
        let suite_result = run_suite(&trial_cfg, &self.law.declared_suite, self.law.horizon);
        let next_trials = self.remaining_trials - 1;

        let rec = TrialBranchTested {
            world_id: self.world_id.clone(),
            seq: self.next_seq(),
            prev: self.last_hash()?,
            actor_id,
            branch_id: branch_id.to_string(),
            adjustments,
            suite_result: suite_result.clone(),
            remaining_trials: next_trials,
            ts: now,
            proof: ProofOrArray::placeholder(),
        };
        let signed = sign_repair_dual(
            rec,
            actor_kp,
            &self.keypair,
            RepairRecord::TrialBranchTested,
            |r, p| r.proof = p,
        )?;
        self.remaining_trials = next_trials;
        self.records.push(RepairRecord::TrialBranchTested(signed));
        Ok(suite_result)
    }

    /// Commits one adjustment to `live_config`, requiring the actor to occupy
    /// the station that owns that control and spending 1 material unit.
    pub fn commit_adjustment(
        &mut self,
        actor_kp: &Keypair,
        adjustment: Adjustment,
        now: u64,
    ) -> Result<RepairRecord> {
        let actor_id = actor_kp.did();
        if !self.participants.contains(&actor_id) {
            return Err(Error::Policy("actor is not a participant".into()));
        }
        let Some(&station) = self.stations.get(&actor_id) else {
            return Err(Error::Policy("actor has not taken a station yet".into()));
        };
        let required = adjustment.required_station();
        if station != required {
            return Err(Error::Policy(format!(
                "adjustment requires {:?}, but actor occupies {:?}",
                required, station
            )));
        }
        if self.remaining_material == 0 {
            return Err(Error::Policy("repair material budget exhausted".into()));
        }

        let next_cfg = apply_adjustment(&self.live_config, &adjustment)?;
        let config_hash = next_cfg.hash()?;
        let next_material = self.remaining_material - 1;

        let rec = AdjustmentCommitted {
            world_id: self.world_id.clone(),
            seq: self.next_seq(),
            prev: self.last_hash()?,
            actor_id,
            station,
            adjustment: adjustment.clone(),
            remaining_material: next_material,
            config_hash,
            ts: now,
            proof: ProofOrArray::placeholder(),
        };
        let signed = sign_repair_dual(
            rec,
            actor_kp,
            &self.keypair,
            RepairRecord::AdjustmentCommitted,
            |r, p| r.proof = p,
        )?;
        let wrapped = RepairRecord::AdjustmentCommitted(signed);
        self.live_config = next_cfg;
        self.committed_adjustments.push(adjustment);
        self.remaining_material = next_material;
        self.records.push(wrapped.clone());
        Ok(wrapped)
    }

    pub fn run_check_suite(&mut self, actor_kp: &Keypair, now: u64) -> Result<SuiteResult> {
        let actor_id = actor_kp.did();
        if !self.participants.contains(&actor_id) {
            return Err(Error::Policy("actor is not a participant".into()));
        }
        let config_hash = self.live_config.hash()?;
        let suite_result = run_suite(
            &self.live_config,
            &self.law.declared_suite,
            self.law.horizon,
        );
        let rec = CheckSuiteRun {
            world_id: self.world_id.clone(),
            seq: self.next_seq(),
            prev: self.last_hash()?,
            actor_id,
            config_hash,
            suite_result: suite_result.clone(),
            ts: now,
            proof: ProofOrArray::placeholder(),
        };
        let signed = sign_repair_dual(
            rec,
            actor_kp,
            &self.keypair,
            RepairRecord::CheckSuiteRun,
            |r, p| r.proof = p,
        )?;
        self.records.push(RepairRecord::CheckSuiteRun(signed));
        Ok(suite_result)
    }

    pub fn export_report(
        &mut self,
        author_kp: &Keypair,
        unresolved_cases: Vec<String>,
        lesson_note: &str,
        now: u64,
    ) -> Result<RepairReport> {
        let author = author_kp.did();
        if !self.participants.contains(&author) {
            return Err(Error::Policy("author is not a participant".into()));
        }
        if lesson_note.trim().is_empty() {
            return Err(Error::Policy("lesson_note cannot be empty".into()));
        }
        let checked_suite = run_suite(
            &self.live_config,
            &self.law.declared_suite,
            self.law.horizon,
        );
        let report = RepairReport {
            world_id: self.world_id.clone(),
            final_config: self.live_config.clone(),
            committed_adjustments: self.committed_adjustments.clone(),
            checked_suite,
            unresolved_cases,
            lesson_note: lesson_note.to_string(),
            author,
        };
        let rec = ReportExported {
            world_id: self.world_id.clone(),
            seq: self.next_seq(),
            prev: self.last_hash()?,
            report: report.clone(),
            ts: now,
            proof: ProofOrArray::placeholder(),
        };
        let signed = sign_repair_dual(
            rec,
            author_kp,
            &self.keypair,
            RepairRecord::ReportExported,
            |r, p| r.proof = p,
        )?;
        self.records.push(RepairRecord::ReportExported(signed));
        Ok(report)
    }
}

/// Independently replays and verifies an entire `RepairLog` offline.
pub fn verify_repair_log(log: &RepairLog) -> Result<()> {
    log.law.validate()?;
    let Some(RepairRecord::WorldOpened(seed)) = log.records.first() else {
        return Err(Error::Chain(
            "repair log must start with world_opened".into(),
        ));
    };
    if seed.world_id != log.world_id {
        return Err(Error::Verification(
            "repair log: seed world_id mismatch".into(),
        ));
    }
    if seed.law.hash()? != log.law.hash()? {
        return Err(Error::Verification(
            "repair log: seed law does not match log law".into(),
        ));
    }

    let mut prev: Option<String> = None;
    let mut participants: HashSet<DidKey> = HashSet::new();
    let mut stations: HashMap<DidKey, StationRole> = HashMap::new();
    let mut live_config = log.law.initial_config.clone();
    let mut committed_adjustments: Vec<Adjustment> = Vec::new();
    let mut remaining_material = log.law.material_budget;
    let mut remaining_trials = log.law.max_trials;

    for (i, rec) in log.records.iter().enumerate() {
        if rec.seq() != i as u64 {
            return Err(Error::Chain(format!(
                "repair log record {i}: seq {} != expected {i}",
                rec.seq()
            )));
        }
        if rec.world_id() != &log.world_id {
            return Err(Error::Verification(format!(
                "repair log record {i}: world_id mismatch"
            )));
        }
        match rec {
            RepairRecord::WorldOpened(_) => {
                if i != 0 {
                    return Err(Error::Chain(format!(
                        "repair log record {i}: world_opened not at start"
                    )));
                }
            }
            _ => {
                if rec.prev() != prev.as_deref() {
                    return Err(Error::Chain(format!(
                        "repair log record {i}: prev hash mismatch"
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
            RepairRecord::WorldOpened(r) => {
                let cp = r
                    .proof
                    .find_by_method(&r.creator_id)
                    .ok_or_else(|| Error::Verification("seed: missing creator proof".into()))?;
                cp.verify(&body)?;
                participants.insert(r.creator_id.clone());
            }
            RepairRecord::ParticipantJoined(r) => {
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
            RepairRecord::StationAssigned(r) => {
                if !participants.contains(&r.participant_id) {
                    return Err(Error::Policy(format!(
                        "record {i}: station assignee not a participant"
                    )));
                }
                let pp = r.proof.find_by_method(&r.participant_id).ok_or_else(|| {
                    Error::Verification(format!("record {i}: missing participant proof"))
                })?;
                pp.verify(&body)?;
                stations.insert(r.participant_id.clone(), r.station);
            }
            RepairRecord::TrialBranchTested(r) => {
                if !participants.contains(&r.actor_id) {
                    return Err(Error::Policy(format!("record {i}: actor not a participant")));
                }
                if r.adjustments.is_empty() {
                    return Err(Error::Policy(format!(
                        "record {i}: trial branch has no adjustments"
                    )));
                }
                if remaining_trials == 0 {
                    return Err(Error::Policy(format!(
                        "record {i}: trial branch exceeds max_trials"
                    )));
                }
                let expected_trials = remaining_trials - 1;
                if r.remaining_trials != expected_trials {
                    return Err(Error::Verification(format!(
                        "record {i}: remaining_trials {} != expected {}",
                        r.remaining_trials, expected_trials
                    )));
                }
                let mut trial_cfg = live_config.clone();
                for adj in &r.adjustments {
                    trial_cfg = apply_adjustment(&trial_cfg, adj)?;
                }
                let expected_suite = run_suite(&trial_cfg, &log.law.declared_suite, log.law.horizon);
                if r.suite_result != expected_suite {
                    return Err(Error::Verification(format!(
                        "record {i}: trial suite_result does not match deterministic replay"
                    )));
                }
                let ap = r
                    .proof
                    .find_by_method(&r.actor_id)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing actor proof")))?;
                ap.verify(&body)?;
                remaining_trials = expected_trials;
            }
            RepairRecord::AdjustmentCommitted(r) => {
                if !participants.contains(&r.actor_id) {
                    return Err(Error::Policy(format!("record {i}: actor not a participant")));
                }
                let Some(&occupied) = stations.get(&r.actor_id) else {
                    return Err(Error::Policy(format!(
                        "record {i}: actor has no assigned station"
                    )));
                };
                if occupied != r.station || r.station != r.adjustment.required_station() {
                    return Err(Error::Policy(format!(
                        "record {i}: station authorization mismatch for adjustment"
                    )));
                }
                if remaining_material == 0 {
                    return Err(Error::Policy(format!(
                        "record {i}: material budget exhausted"
                    )));
                }
                let expected_material = remaining_material - 1;
                if r.remaining_material != expected_material {
                    return Err(Error::Verification(format!(
                        "record {i}: remaining_material {} != expected {}",
                        r.remaining_material, expected_material
                    )));
                }
                let next_cfg = apply_adjustment(&live_config, &r.adjustment)?;
                if r.config_hash != next_cfg.hash()? {
                    return Err(Error::Verification(format!(
                        "record {i}: committed config_hash mismatch"
                    )));
                }
                let ap = r
                    .proof
                    .find_by_method(&r.actor_id)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing actor proof")))?;
                ap.verify(&body)?;
                live_config = next_cfg;
                committed_adjustments.push(r.adjustment.clone());
                remaining_material = expected_material;
            }
            RepairRecord::CheckSuiteRun(r) => {
                if !participants.contains(&r.actor_id) {
                    return Err(Error::Policy(format!("record {i}: actor not a participant")));
                }
                if r.config_hash != live_config.hash()? {
                    return Err(Error::Verification(format!(
                        "record {i}: check suite config_hash mismatch"
                    )));
                }
                let expected_suite =
                    run_suite(&live_config, &log.law.declared_suite, log.law.horizon);
                if r.suite_result != expected_suite {
                    return Err(Error::Verification(format!(
                        "record {i}: check suite_result mismatch"
                    )));
                }
                let ap = r
                    .proof
                    .find_by_method(&r.actor_id)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing actor proof")))?;
                ap.verify(&body)?;
            }
            RepairRecord::ReportExported(r) => {
                if !participants.contains(&r.report.author) {
                    return Err(Error::Policy(format!(
                        "record {i}: report author not a participant"
                    )));
                }
                let expected_suite =
                    run_suite(&live_config, &log.law.declared_suite, log.law.horizon);
                if r.report.world_id != log.world_id
                    || r.report.final_config != live_config
                    || r.report.committed_adjustments != committed_adjustments
                    || r.report.checked_suite != expected_suite
                {
                    return Err(Error::Verification(format!(
                        "record {i}: exported report does not match world state"
                    )));
                }
                let ap = r
                    .proof
                    .find_by_method(&r.report.author)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing author proof")))?;
                ap.verify(&body)?;
            }
        }

        prev = Some(rec.hash()?);
    }

    Ok(())
}
