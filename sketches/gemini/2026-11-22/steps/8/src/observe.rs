//! Observation World: investigating a cryptographically committed hidden model
//! through budgeted predictions, multi-resolution readouts, and offline-verified reveals.

use crate::did::{DidKey, Keypair};
use crate::error::{Error, Result};
use crate::hash::{body_for_signing, hash_of};
use crate::proof::{Proof, ProofOrArray};
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};

fn looks_like_hash(s: &str) -> bool {
    s.len() == 64 && s.chars().all(|c| c.is_ascii_hexdigit())
}

/// Exact integer-valued model rules over admitted `i64` inputs.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "rule_kind", rename_all = "snake_case")]
pub enum ModelRule {
    /// f(x) = slope * x + intercept
    Affine { slope: i64, intercept: i64 },
    /// f(x) = a * x^2 + b * x + c
    Quadratic { a: i64, b: i64, c: i64 },
    /// e_n = (-gain)^n * initial for non-negative step n = input
    AlternatingPower { gain: i64, initial: i64 },
    /// low_value when input < threshold, high_value when input >= threshold
    PiecewiseThreshold {
        threshold: i64,
        low_value: i64,
        high_value: i64,
    },
}

impl ModelRule {
    pub fn eval(&self, input: i64) -> Result<i64> {
        match self {
            ModelRule::Affine { slope, intercept } => slope
                .checked_mul(input)
                .and_then(|v| v.checked_add(*intercept))
                .ok_or_else(|| Error::Policy("affine model evaluation overflow".into())),
            ModelRule::Quadratic { a, b, c } => {
                let x2 = input
                    .checked_mul(input)
                    .ok_or_else(|| Error::Policy("quadratic x^2 overflow".into()))?;
                let t2 = a
                    .checked_mul(x2)
                    .ok_or_else(|| Error::Policy("quadratic a*x^2 overflow".into()))?;
                let t1 = b
                    .checked_mul(input)
                    .ok_or_else(|| Error::Policy("quadratic b*x overflow".into()))?;
                t2.checked_add(t1)
                    .and_then(|v| v.checked_add(*c))
                    .ok_or_else(|| Error::Policy("quadratic sum overflow".into()))
            }
            ModelRule::AlternatingPower { gain, initial } => {
                if input < 0 {
                    return Err(Error::Policy(
                        "alternating_power requires non-negative step input".into(),
                    ));
                }
                let factor = gain
                    .checked_neg()
                    .ok_or_else(|| Error::Policy("alternating_power gain overflow".into()))?;
                let mut val = *initial;
                for _ in 0..input {
                    val = val
                        .checked_mul(factor)
                        .ok_or_else(|| Error::Policy("alternating_power overflow".into()))?;
                }
                Ok(val)
            }
            ModelRule::PiecewiseThreshold {
                threshold,
                low_value,
                high_value,
            } => Ok(if input < *threshold {
                *low_value
            } else {
                *high_value
            }),
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CandidateModel {
    pub name: String,
    pub rule: ModelRule,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "readout_kind", rename_all = "snake_case")]
pub enum ReadoutKind {
    Exact,
    SignOnly,
    Parity,
    BoundedError { radius: u64 },
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "reading_kind", rename_all = "snake_case")]
pub enum ProbeReading {
    Exact { value: i64 },
    Sign { sign: i64 },
    Parity { bit: u8 },
    Bounded { reported: i64, radius: u64 },
}

impl ProbeReading {
    pub fn matches_prediction(&self, predicted: &ProbeReading) -> bool {
        match (self, predicted) {
            (ProbeReading::Exact { value: a }, ProbeReading::Exact { value: b }) => a == b,
            (ProbeReading::Sign { sign: a }, ProbeReading::Sign { sign: b }) => a == b,
            (ProbeReading::Parity { bit: a }, ProbeReading::Parity { bit: b }) => a == b,
            (
                ProbeReading::Bounded {
                    reported: got,
                    radius: r1,
                },
                ProbeReading::Bounded {
                    reported: exp,
                    radius: r2,
                },
            ) => r1 == r2 && (*got as i128 - *exp as i128).abs() <= (*r1 as i128),
            _ => false,
        }
    }
}

impl ReadoutKind {
    pub fn observe(&self, true_val: i64, noise_offset: i64) -> Result<ProbeReading> {
        match self {
            ReadoutKind::Exact => {
                if noise_offset != 0 {
                    return Err(Error::Policy("exact readout does not admit noise".into()));
                }
                Ok(ProbeReading::Exact { value: true_val })
            }
            ReadoutKind::SignOnly => {
                if noise_offset != 0 {
                    return Err(Error::Policy("sign_only readout does not admit noise".into()));
                }
                Ok(ProbeReading::Sign {
                    sign: true_val.signum(),
                })
            }
            ReadoutKind::Parity => {
                if noise_offset != 0 {
                    return Err(Error::Policy("parity readout does not admit noise".into()));
                }
                Ok(ProbeReading::Parity {
                    bit: true_val.rem_euclid(2) as u8,
                })
            }
            ReadoutKind::BoundedError { radius } => {
                if (noise_offset as i128).abs() > (*radius as i128) {
                    return Err(Error::Policy(format!(
                        "noise_offset {} exceeds declared error radius {}",
                        noise_offset, radius
                    )));
                }
                let reported = true_val
                    .checked_add(noise_offset)
                    .ok_or_else(|| Error::Policy("bounded reading overflow".into()))?;
                Ok(ProbeReading::Bounded {
                    reported,
                    radius: *radius,
                })
            }
        }
    }

    pub fn matches_reading_shape(&self, reading: &ProbeReading) -> bool {
        match (self, reading) {
            (ReadoutKind::Exact, ProbeReading::Exact { .. }) => true,
            (ReadoutKind::SignOnly, ProbeReading::Sign { sign }) => {
                *sign == -1 || *sign == 0 || *sign == 1
            }
            (ReadoutKind::Parity, ProbeReading::Parity { bit }) => *bit <= 1,
            (
                ReadoutKind::BoundedError { radius },
                ProbeReading::Bounded { radius: r, .. },
            ) => radius == r,
            _ => false,
        }
    }

    pub fn is_consistent(&self, true_val: i64, reading: &ProbeReading) -> bool {
        match (self, reading) {
            (ReadoutKind::Exact, ProbeReading::Exact { value }) => true_val == *value,
            (ReadoutKind::SignOnly, ProbeReading::Sign { sign }) => true_val.signum() == *sign,
            (ReadoutKind::Parity, ProbeReading::Parity { bit }) => {
                (true_val.rem_euclid(2) as u8) == *bit
            }
            (
                ReadoutKind::BoundedError { radius },
                ProbeReading::Bounded {
                    reported,
                    radius: r,
                },
            ) => radius == r && (true_val as i128 - *reported as i128).abs() <= (*radius as i128),
            _ => false,
        }
    }

    /// Returns true iff no single valid reading under this instrument can be
    /// simultaneously compatible with both `v1` and `v2`.
    /// For `BoundedError { radius }`, this is the exact condition `|v1 - v2| > 2 * radius`.
    pub fn guarantees_separation(&self, v1: i64, v2: i64) -> bool {
        match self {
            ReadoutKind::Exact => v1 != v2,
            ReadoutKind::SignOnly => v1.signum() != v2.signum(),
            ReadoutKind::Parity => v1.rem_euclid(2) != v2.rem_euclid(2),
            ReadoutKind::BoundedError { radius } => {
                (v1 as i128 - v2 as i128).abs() > 2 * (*radius as i128)
            }
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ReadoutSpec {
    pub name: String,
    pub kind: ReadoutKind,
    pub cost: u64,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ObservationLaw {
    pub topic: String,
    pub candidates: Vec<CandidateModel>,
    pub admitted_readouts: Vec<ReadoutSpec>,
    pub probe_budget: u64,
    pub input_min: i64,
    pub input_max: i64,
}

impl ObservationLaw {
    pub fn validate(&self) -> Result<()> {
        if self.topic.trim().is_empty() {
            return Err(Error::Policy("observation law: topic cannot be empty".into()));
        }
        if self.candidates.is_empty() {
            return Err(Error::Policy(
                "observation law: must declare at least one candidate model".into(),
            ));
        }
        let mut seen_models = HashSet::new();
        for c in &self.candidates {
            if c.name.trim().is_empty() || !seen_models.insert(c.name.clone()) {
                return Err(Error::Policy(
                    "observation law: candidate names must be non-empty and unique".into(),
                ));
            }
        }
        if self.admitted_readouts.is_empty() {
            return Err(Error::Policy(
                "observation law: must declare at least one readout instrument".into(),
            ));
        }
        let mut seen_readouts = HashSet::new();
        for r in &self.admitted_readouts {
            if r.name.trim().is_empty() || !seen_readouts.insert(r.name.clone()) {
                return Err(Error::Policy(
                    "observation law: readout names must be non-empty and unique".into(),
                ));
            }
            if r.cost == 0 {
                return Err(Error::Policy("observation law: readout cost must be >= 1".into()));
            }
        }
        if self.input_min > self.input_max {
            return Err(Error::Policy(
                "observation law: input_min must be <= input_max".into(),
            ));
        }
        Ok(())
    }

    pub fn find_readout(&self, name: &str) -> Option<&ReadoutSpec> {
        self.admitted_readouts.iter().find(|r| r.name == name)
    }

    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }
}

/// Private secret committed at world creation and revealed at conclusion.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct HiddenSecret {
    pub model_index: u64,
    pub model_name: String,
    pub rule: ModelRule,
    pub salt: String,
}

impl HiddenSecret {
    pub fn commitment(&self) -> Result<String> {
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
    pub law: ObservationLaw,
    pub hidden_commitment: String,
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
pub struct PredictionSubmitted {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: String,
    pub actor_id: DidKey,
    pub input: i64,
    pub readout_name: String,
    pub expected_reading: ProbeReading,
    pub hypothesis_name: String,
    pub ts: u64,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ProbeRecorded {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: String,
    pub actor_id: DidKey,
    pub input: i64,
    pub readout_name: String,
    pub cost: u64,
    pub remaining_budget: u64,
    pub reading: ProbeReading,
    pub prediction_matched: Option<bool>,
    pub ts: u64,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SecretRevealed {
    pub world_id: DidKey,
    pub seq: u64,
    pub prev: String,
    pub secret: HiddenSecret,
    pub ts: u64,
    pub proof: ProofOrArray,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum ObservationRecord {
    WorldOpened(WorldOpened),
    ParticipantJoined(ParticipantJoined),
    PredictionSubmitted(PredictionSubmitted),
    ProbeRecorded(ProbeRecorded),
    SecretRevealed(SecretRevealed),
}

impl ObservationRecord {
    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }

    pub fn seq(&self) -> u64 {
        match self {
            ObservationRecord::WorldOpened(_) => 0,
            ObservationRecord::ParticipantJoined(r) => r.seq,
            ObservationRecord::PredictionSubmitted(r) => r.seq,
            ObservationRecord::ProbeRecorded(r) => r.seq,
            ObservationRecord::SecretRevealed(r) => r.seq,
        }
    }

    pub fn prev(&self) -> Option<&str> {
        match self {
            ObservationRecord::WorldOpened(_) => None,
            ObservationRecord::ParticipantJoined(r) => Some(&r.prev),
            ObservationRecord::PredictionSubmitted(r) => Some(&r.prev),
            ObservationRecord::ProbeRecorded(r) => Some(&r.prev),
            ObservationRecord::SecretRevealed(r) => Some(&r.prev),
        }
    }

    pub fn world_id(&self) -> &DidKey {
        match self {
            ObservationRecord::WorldOpened(r) => &r.world_id,
            ObservationRecord::ParticipantJoined(r) => &r.world_id,
            ObservationRecord::PredictionSubmitted(r) => &r.world_id,
            ObservationRecord::ProbeRecorded(r) => &r.world_id,
            ObservationRecord::SecretRevealed(r) => &r.world_id,
        }
    }

    pub fn proof(&self) -> &ProofOrArray {
        match self {
            ObservationRecord::WorldOpened(r) => &r.proof,
            ObservationRecord::ParticipantJoined(r) => &r.proof,
            ObservationRecord::PredictionSubmitted(r) => &r.proof,
            ObservationRecord::ProbeRecorded(r) => &r.proof,
            ObservationRecord::SecretRevealed(r) => &r.proof,
        }
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ObservationLog {
    pub world_id: DidKey,
    pub law: ObservationLaw,
    pub hidden_commitment: String,
    pub records: Vec<ObservationRecord>,
}

// =====================================================================
// PURE ANALYSIS HELPERS (COMPATIBILITY & EXPERIMENT DESIGN)
// =====================================================================

/// Returns the names of every candidate in `law.candidates` consistent with
/// all recorded probes so far.
pub fn compatible_candidates(law: &ObservationLaw, probes: &[ProbeRecorded]) -> Result<Vec<String>> {
    let mut out = Vec::new();
    for cand in &law.candidates {
        let mut ok = true;
        for probe in probes {
            let readout = law.find_readout(&probe.readout_name).ok_or_else(|| {
                Error::Verification(format!("unknown readout {:?}", probe.readout_name))
            })?;
            match cand.rule.eval(probe.input) {
                Ok(val) => {
                    if !readout.kind.is_consistent(val, &probe.reading) {
                        ok = false;
                        break;
                    }
                }
                Err(_) => {
                    ok = false;
                    break;
                }
            }
        }
        if ok {
            out.push(cand.name.clone());
        }
    }
    Ok(out)
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DiscriminatingProbe {
    pub input: i64,
    pub readout_name: String,
    pub cost: u64,
    pub splits_pair: (String, String),
}

/// Searches `candidate_inputs` and affordable admitted readouts (cheapest first)
/// for a probe guaranteed to separate at least two currently compatible models.
pub fn suggest_discriminating_probe(
    law: &ObservationLaw,
    probes: &[ProbeRecorded],
    remaining_budget: u64,
    candidate_inputs: &[i64],
) -> Result<Option<DiscriminatingProbe>> {
    let compat_names = compatible_candidates(law, probes)?;
    if compat_names.len() <= 1 {
        return Ok(None);
    }
    let compat_models: Vec<&CandidateModel> = law
        .candidates
        .iter()
        .filter(|c| compat_names.contains(&c.name))
        .collect();

    let mut readouts: Vec<&ReadoutSpec> = law
        .admitted_readouts
        .iter()
        .filter(|r| r.cost <= remaining_budget)
        .collect();
    readouts.sort_by(|a, b| a.cost.cmp(&b.cost).then_with(|| a.name.cmp(&b.name)));

    for readout in readouts {
        for &input in candidate_inputs {
            if input < law.input_min || input > law.input_max {
                continue;
            }
            for i in 0..compat_models.len() {
                let Ok(v1) = compat_models[i].rule.eval(input) else {
                    continue;
                };
                for j in (i + 1)..compat_models.len() {
                    let Ok(v2) = compat_models[j].rule.eval(input) else {
                        continue;
                    };
                    if readout.kind.guarantees_separation(v1, v2) {
                        return Ok(Some(DiscriminatingProbe {
                            input,
                            readout_name: readout.name.clone(),
                            cost: readout.cost,
                            splits_pair: (
                                compat_models[i].name.clone(),
                                compat_models[j].name.clone(),
                            ),
                        }));
                    }
                }
            }
        }
    }
    Ok(None)
}

// =====================================================================
// EXECUTABLE OBSERVATION WORLD & OFFLINE VERIFIER
// =====================================================================

fn sign_obs_dual<T, F>(
    mut rec: T,
    actor: &Keypair,
    world: &Keypair,
    wrap: fn(T) -> ObservationRecord,
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

pub struct ObservationWorld {
    world_id: DidKey,
    law: ObservationLaw,
    keypair: Keypair,
    secret: HiddenSecret,
    hidden_commitment: String,
    revealed: bool,
    remaining_budget: u64,
    participants: HashSet<DidKey>,
    open_predictions: HashMap<(DidKey, i64, String), ProbeReading>,
    records: Vec<ObservationRecord>,
}

impl ObservationWorld {
    pub fn open(
        law: ObservationLaw,
        hidden_model_index: u64,
        salt: &str,
        world_kp: Keypair,
        creator_kp: &Keypair,
        now: u64,
    ) -> Result<Self> {
        law.validate()?;
        if salt.trim().is_empty() {
            return Err(Error::Policy("observation world: salt cannot be empty".into()));
        }
        let cand = law
            .candidates
            .get(hidden_model_index as usize)
            .ok_or_else(|| Error::Policy("hidden_model_index out of bounds".into()))?;
        let secret = HiddenSecret {
            model_index: hidden_model_index,
            model_name: cand.name.clone(),
            rule: cand.rule.clone(),
            salt: salt.to_string(),
        };
        let hidden_commitment = secret.commitment()?;
        let world_id = world_kp.did();
        let creator_id = creator_kp.did();
        let budget = law.probe_budget;

        let opened = WorldOpened {
            world_id: world_id.clone(),
            law: law.clone(),
            hidden_commitment: hidden_commitment.clone(),
            creator_id: creator_id.clone(),
            ts: now,
            proof: ProofOrArray::placeholder(),
        };
        let signed = sign_obs_dual(
            opened,
            creator_kp,
            &world_kp,
            ObservationRecord::WorldOpened,
            |r, p| r.proof = p,
        )?;
        let mut participants = HashSet::new();
        participants.insert(creator_id);

        Ok(ObservationWorld {
            world_id,
            law,
            keypair: world_kp,
            secret,
            hidden_commitment,
            revealed: false,
            remaining_budget: budget,
            participants,
            open_predictions: HashMap::new(),
            records: vec![ObservationRecord::WorldOpened(signed)],
        })
    }

    pub fn world_id(&self) -> &DidKey {
        &self.world_id
    }

    pub fn law(&self) -> &ObservationLaw {
        &self.law
    }

    pub fn remaining_budget(&self) -> u64 {
        self.remaining_budget
    }

    pub fn probes(&self) -> Vec<ProbeRecorded> {
        self.records
            .iter()
            .filter_map(|r| match r {
                ObservationRecord::ProbeRecorded(p) => Some(p.clone()),
                _ => None,
            })
            .collect()
    }

    pub fn compatible_candidates(&self) -> Result<Vec<String>> {
        compatible_candidates(&self.law, &self.probes())
    }

    pub fn log(&self) -> ObservationLog {
        ObservationLog {
            world_id: self.world_id.clone(),
            law: self.law.clone(),
            hidden_commitment: self.hidden_commitment.clone(),
            records: self.records.clone(),
        }
    }

    fn next_seq(&self) -> u64 {
        self.records.len() as u64
    }

    fn last_hash(&self) -> Result<String> {
        self.records
            .last()
            .ok_or_else(|| Error::Chain("observation world has no seed record".into()))?
            .hash()
    }

    pub fn join(&mut self, participant_kp: &Keypair, now: u64) -> Result<ObservationRecord> {
        if self.revealed {
            return Err(Error::Policy(
                "cannot join after hidden model has been revealed".into(),
            ));
        }
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
        let signed = sign_obs_dual(
            rec,
            participant_kp,
            &self.keypair,
            ObservationRecord::ParticipantJoined,
            |r, p| r.proof = p,
        )?;
        let wrapped = ObservationRecord::ParticipantJoined(signed);
        self.participants.insert(pid);
        self.records.push(wrapped.clone());
        Ok(wrapped)
    }

    pub fn predict(
        &mut self,
        actor_kp: &Keypair,
        input: i64,
        readout_name: &str,
        expected_reading: ProbeReading,
        hypothesis_name: &str,
        now: u64,
    ) -> Result<ObservationRecord> {
        if self.revealed {
            return Err(Error::Policy(
                "cannot submit prediction after reveal".into(),
            ));
        }
        let actor_id = actor_kp.did();
        if !self.participants.contains(&actor_id) {
            return Err(Error::Policy("actor is not a participant".into()));
        }
        if input < self.law.input_min || input > self.law.input_max {
            return Err(Error::Policy("prediction input outside admitted range".into()));
        }
        let readout = self
            .law
            .find_readout(readout_name)
            .ok_or_else(|| Error::Policy(format!("unknown readout {:?}", readout_name)))?;
        if !readout.kind.matches_reading_shape(&expected_reading) {
            return Err(Error::Policy(
                "expected_reading shape does not match readout instrument".into(),
            ));
        }
        if hypothesis_name.trim().is_empty() {
            return Err(Error::Policy("hypothesis_name cannot be empty".into()));
        }

        let rec = PredictionSubmitted {
            world_id: self.world_id.clone(),
            seq: self.next_seq(),
            prev: self.last_hash()?,
            actor_id: actor_id.clone(),
            input,
            readout_name: readout_name.to_string(),
            expected_reading: expected_reading.clone(),
            hypothesis_name: hypothesis_name.to_string(),
            ts: now,
            proof: ProofOrArray::placeholder(),
        };
        let signed = sign_obs_dual(
            rec,
            actor_kp,
            &self.keypair,
            ObservationRecord::PredictionSubmitted,
            |r, p| r.proof = p,
        )?;
        let wrapped = ObservationRecord::PredictionSubmitted(signed);
        self.open_predictions
            .insert((actor_id, input, readout_name.to_string()), expected_reading);
        self.records.push(wrapped.clone());
        Ok(wrapped)
    }

    pub fn probe(
        &mut self,
        actor_kp: &Keypair,
        input: i64,
        readout_name: &str,
        now: u64,
    ) -> Result<ProbeRecorded> {
        self.probe_with_offset(actor_kp, input, readout_name, 0, now)
    }

    pub fn probe_with_offset(
        &mut self,
        actor_kp: &Keypair,
        input: i64,
        readout_name: &str,
        noise_offset: i64,
        now: u64,
    ) -> Result<ProbeRecorded> {
        if self.revealed {
            return Err(Error::Policy("cannot probe after reveal".into()));
        }
        let actor_id = actor_kp.did();
        if !self.participants.contains(&actor_id) {
            return Err(Error::Policy("actor is not a participant".into()));
        }
        if input < self.law.input_min || input > self.law.input_max {
            return Err(Error::Policy("probe input outside admitted range".into()));
        }
        let readout = self
            .law
            .find_readout(readout_name)
            .ok_or_else(|| Error::Policy(format!("unknown readout {:?}", readout_name)))?
            .clone();
        if readout.cost > self.remaining_budget {
            return Err(Error::Policy(format!(
                "insufficient probe budget: need {}, remaining {}",
                readout.cost, self.remaining_budget
            )));
        }

        let true_val = self.secret.rule.eval(input)?;
        let reading = readout.kind.observe(true_val, noise_offset)?;
        let next_budget = self.remaining_budget - readout.cost;
        let pred_key = (actor_id.clone(), input, readout_name.to_string());
        let prediction_matched = self
            .open_predictions
            .remove(&pred_key)
            .map(|expected| reading.matches_prediction(&expected));

        let rec = ProbeRecorded {
            world_id: self.world_id.clone(),
            seq: self.next_seq(),
            prev: self.last_hash()?,
            actor_id,
            input,
            readout_name: readout_name.to_string(),
            cost: readout.cost,
            remaining_budget: next_budget,
            reading,
            prediction_matched,
            ts: now,
            proof: ProofOrArray::placeholder(),
        };
        let signed = sign_obs_dual(
            rec,
            actor_kp,
            &self.keypair,
            ObservationRecord::ProbeRecorded,
            |r, p| r.proof = p,
        )?;
        self.remaining_budget = next_budget;
        self.records
            .push(ObservationRecord::ProbeRecorded(signed.clone()));
        Ok(signed)
    }

    pub fn reveal(&mut self, now: u64) -> Result<HiddenSecret> {
        if self.revealed {
            return Err(Error::Policy("hidden model already revealed".into()));
        }
        let mut rec = SecretRevealed {
            world_id: self.world_id.clone(),
            seq: self.next_seq(),
            prev: self.last_hash()?,
            secret: self.secret.clone(),
            ts: now,
            proof: ProofOrArray::placeholder(),
        };
        let body = body_for_signing(&ObservationRecord::SecretRevealed(rec.clone()))?;
        let sig = self.keypair.sign(&body);
        rec.proof = ProofOrArray::single(Proof::create(&self.keypair, &sig));
        self.revealed = true;
        self.records.push(ObservationRecord::SecretRevealed(rec));
        Ok(self.secret.clone())
    }
}

/// Independently verifies an `ObservationLog` offline.
/// Works on both in-progress logs and revealed logs; once `SecretRevealed`
/// is present, verifies the opening commitment and retroactively checks
/// every recorded probe reading against the committed hidden model.
pub fn verify_observation_log(log: &ObservationLog) -> Result<()> {
    log.law.validate()?;
    if !looks_like_hash(&log.hidden_commitment) {
        return Err(Error::Verification(
            "observation log: invalid hidden_commitment".into(),
        ));
    }
    let Some(ObservationRecord::WorldOpened(seed)) = log.records.first() else {
        return Err(Error::Chain(
            "observation log must start with world_opened".into(),
        ));
    };
    if seed.world_id != log.world_id {
        return Err(Error::Verification(
            "observation log: seed world_id mismatch".into(),
        ));
    }
    if seed.law.hash()? != log.law.hash()? {
        return Err(Error::Verification(
            "observation log: seed law does not match log law".into(),
        ));
    }
    if seed.hidden_commitment != log.hidden_commitment {
        return Err(Error::Verification(
            "observation log: seed hidden_commitment mismatch".into(),
        ));
    }

    let mut prev: Option<String> = None;
    let mut participants: HashSet<DidKey> = HashSet::new();
    let mut remaining_budget = log.law.probe_budget;
    let mut open_predictions: HashMap<(DidKey, i64, String), ProbeReading> = HashMap::new();
    let mut recorded_probes: Vec<&ProbeRecorded> = Vec::new();
    let mut revealed_secret: Option<&HiddenSecret> = None;

    for (i, rec) in log.records.iter().enumerate() {
        if rec.seq() != i as u64 {
            return Err(Error::Chain(format!(
                "observation log record {i}: seq {} != expected {i}",
                rec.seq()
            )));
        }
        if rec.world_id() != &log.world_id {
            return Err(Error::Verification(format!(
                "observation log record {i}: world_id mismatch"
            )));
        }
        match rec {
            ObservationRecord::WorldOpened(_) => {
                if i != 0 {
                    return Err(Error::Chain(format!(
                        "observation log record {i}: world_opened not at start"
                    )));
                }
            }
            _ => {
                if rec.prev() != prev.as_deref() {
                    return Err(Error::Chain(format!(
                        "observation log record {i}: prev hash mismatch"
                    )));
                }
            }
        }

        if revealed_secret.is_some() {
            return Err(Error::Policy(format!(
                "observation log record {i}: no records allowed after secret_revealed"
            )));
        }

        let body = body_for_signing(rec)?;
        let world_proof = rec
            .proof()
            .find_by_method(&log.world_id)
            .ok_or_else(|| Error::Verification(format!("record {i}: missing world proof")))?;
        world_proof.verify(&body)?;

        match rec {
            ObservationRecord::WorldOpened(r) => {
                let cp = r
                    .proof
                    .find_by_method(&r.creator_id)
                    .ok_or_else(|| Error::Verification("seed: missing creator proof".into()))?;
                cp.verify(&body)?;
                participants.insert(r.creator_id.clone());
            }
            ObservationRecord::ParticipantJoined(r) => {
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
            ObservationRecord::PredictionSubmitted(r) => {
                if !participants.contains(&r.actor_id) {
                    return Err(Error::Policy(format!("record {i}: actor not a participant")));
                }
                if r.input < log.law.input_min || r.input > log.law.input_max {
                    return Err(Error::Policy(format!(
                        "record {i}: prediction input out of bounds"
                    )));
                }
                let readout = log.law.find_readout(&r.readout_name).ok_or_else(|| {
                    Error::Policy(format!("record {i}: unknown readout {:?}", r.readout_name))
                })?;
                if !readout.kind.matches_reading_shape(&r.expected_reading) {
                    return Err(Error::Policy(format!(
                        "record {i}: prediction reading shape mismatch"
                    )));
                }
                let ap = r
                    .proof
                    .find_by_method(&r.actor_id)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing actor proof")))?;
                ap.verify(&body)?;
                open_predictions.insert(
                    (r.actor_id.clone(), r.input, r.readout_name.clone()),
                    r.expected_reading.clone(),
                );
            }
            ObservationRecord::ProbeRecorded(r) => {
                if !participants.contains(&r.actor_id) {
                    return Err(Error::Policy(format!("record {i}: actor not a participant")));
                }
                if r.input < log.law.input_min || r.input > log.law.input_max {
                    return Err(Error::Policy(format!(
                        "record {i}: probe input out of bounds"
                    )));
                }
                let readout = log.law.find_readout(&r.readout_name).ok_or_else(|| {
                    Error::Policy(format!("record {i}: unknown readout {:?}", r.readout_name))
                })?;
                if r.cost != readout.cost {
                    return Err(Error::Verification(format!(
                        "record {i}: probe cost {} != readout cost {}",
                        r.cost, readout.cost
                    )));
                }
                if r.cost > remaining_budget {
                    return Err(Error::Policy(format!(
                        "record {i}: probe exceeds remaining budget"
                    )));
                }
                let expected_budget = remaining_budget - r.cost;
                if r.remaining_budget != expected_budget {
                    return Err(Error::Verification(format!(
                        "record {i}: remaining_budget {} != expected {}",
                        r.remaining_budget, expected_budget
                    )));
                }
                if !readout.kind.matches_reading_shape(&r.reading) {
                    return Err(Error::Verification(format!(
                        "record {i}: probe reading shape does not match readout"
                    )));
                }
                let expected_match = open_predictions
                    .remove(&(r.actor_id.clone(), r.input, r.readout_name.clone()))
                    .map(|pred| r.reading.matches_prediction(&pred));
                if r.prediction_matched != expected_match {
                    return Err(Error::Verification(format!(
                        "record {i}: prediction_matched mismatch"
                    )));
                }
                let ap = r
                    .proof
                    .find_by_method(&r.actor_id)
                    .ok_or_else(|| Error::Verification(format!("record {i}: missing actor proof")))?;
                ap.verify(&body)?;
                remaining_budget = expected_budget;
                recorded_probes.push(r);
            }
            ObservationRecord::SecretRevealed(r) => {
                let cand = log
                    .law
                    .candidates
                    .get(r.secret.model_index as usize)
                    .ok_or_else(|| {
                        Error::Verification("secret_revealed: model_index out of bounds".into())
                    })?;
                if cand.name != r.secret.model_name || cand.rule != r.secret.rule {
                    return Err(Error::Verification(
                        "secret_revealed: secret does not match candidate in law".into(),
                    ));
                }
                if r.secret.commitment()? != log.hidden_commitment {
                    return Err(Error::Verification(
                        "secret_revealed: secret commitment does not match WorldOpened".into(),
                    ));
                }
                revealed_secret = Some(&r.secret);
            }
        }

        prev = Some(rec.hash()?);
    }

    if let Some(secret) = revealed_secret {
        for probe in recorded_probes {
            let readout = log.law.find_readout(&probe.readout_name).unwrap();
            let true_val = secret.rule.eval(probe.input)?;
            if !readout.kind.is_consistent(true_val, &probe.reading) {
                return Err(Error::Verification(format!(
                    "probe at seq {}: reading {:?} is inconsistent with revealed model value {}",
                    probe.seq, probe.reading, true_val
                )));
            }
        }
    }

    Ok(())
}
