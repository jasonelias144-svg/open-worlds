//! Complete 6-archetype heterogeneous 3-channel neural library with dissolving
//! fast weights, sparse dead-zone Yellow gating, composite-color receptor
//! broadcast, and cerebellar/Jeffress delay lines.
//!
//! All values use deterministic fixed-point `i64` arithmetic (`SCALE = 1000`,
//! where `1000` represents `1.0`) with `i128` intermediates so states, delay
//! buffers, weights, and traces canonicalize cleanly and verify offline.

use crate::did::{DidKey, Keypair};
use crate::error::{Error, Result};
use crate::hash::{body_for_signing, hash_of};
use crate::proof::{Proof, ProofOrArray};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, HashMap, HashSet};

pub const SCALE: i64 = 1000;
pub const MAX_SIGNAL: i64 = 2000;

fn isqrt_u128(n: u128) -> u128 {
    if n < 2 {
        return n;
    }
    let shift = (128 - n.leading_zeros() + 1) / 2;
    let mut x = 1u128 << shift;
    loop {
        let y = (x + n / x) / 2;
        if y >= x {
            return x;
        }
        x = y;
    }
}

/// Output channel selector for broadcast receptors.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum Channel {
    Red,
    Blue,
    Yellow,
}

/// Three-channel neurotransmitter / color signal.
/// - `red`: fast excitatory drive (or basal bottom-up input / delay stream A)
/// - `blue`: fast divisive shunting inhibition (or delay stream B / Purkinje cancel)
/// - `yellow`: neuromodulatory attention / salience (or apical context / climbing-fiber error)
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TriSignal {
    pub red: i64,
    pub blue: i64,
    pub yellow: i64,
}

impl TriSignal {
    /// Clamped unit-level signal in `[0, MAX_SIGNAL]`.
    pub fn new(red: i64, blue: i64, yellow: i64) -> Self {
        TriSignal {
            red: red.clamp(0, MAX_SIGNAL),
            blue: blue.clamp(0, MAX_SIGNAL),
            yellow: yellow.clamp(0, MAX_SIGNAL),
        }
    }

    /// Unclamped non-negative external sensory field (supports 0.05x..20x+ scales).
    pub fn raw(red: i64, blue: i64, yellow: i64) -> Self {
        TriSignal {
            red: red.max(0),
            blue: blue.max(0),
            yellow: yellow.max(0),
        }
    }

    pub fn red_only(red: i64) -> Self {
        Self::new(red, 0, 0)
    }

    pub fn blue_only(blue: i64) -> Self {
        Self::new(0, blue, 0)
    }

    pub fn yellow_only(yellow: i64) -> Self {
        Self::new(0, 0, yellow)
    }
}

/// Operating mode for Archetype 6 (`DelayLine`).
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "delay_mode", rename_all = "snake_case")]
pub enum DelayMode {
    /// Jeffress spatiotemporal order & interval detector:
    /// checks geometric mean of Red stream at `lag_a` and Blue stream at `lag_b`.
    Coincidence {
        lag_a: usize,
        lag_b: usize,
        threshold: i64,
    },
    /// Cerebellar Purkinje predictive cancellation:
    /// reads warning cues on Red, emits timed Blue cancellation over `base_taps + fast_taps`,
    /// and updates dissolving `fast_taps` from Yellow climbing-fiber error (`shock - cancel`).
    PurkinjeCancel {
        lr_fast: i64,
        decay_quiet: i64,
        decay_error: i64,
        error_threshold: i64,
        tap_cap: i64,
        base_taps: Vec<i64>,
    },
}

/// Six specialized neural unit archetypes.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "unit_kind", rename_all = "snake_case")]
pub enum UnitKind {
    /// Archetype 1: Excitatory / working-memory cell with divisive Blue shunting
    /// and slow-decaying Yellow gain modulation.
    TriChannel {
        leak_g0: i64,
        threshold: i64,
        yellow_decay: i64,
        blue_gain: i64,
        yellow_gain: i64,
    },
    /// Archetype 2: Apical-basal coincidence & surprise cell.
    /// Basal = Red, Apical = Yellow, Shunting = Blue.
    Pyramidal {
        leak_g0: i64,
        threshold: i64,
        apical_threshold: i64,
        coincidence_boost: i64,
        yellow_decay: i64,
    },
    /// Archetype 3: Fast inhibitory stabilizer broadcasting Blue shunting inhibition.
    ShuntingInterneuron {
        threshold: i64,
        blue_gain: i64,
    },
    /// Archetype 4: Slow neuromodulatory nucleus broadcasting a tonic Yellow attention field.
    ModulatorNucleus {
        tonic_decay: i64,
        red_trigger_gain: i64,
        threshold: i64,
    },
    /// Archetype 5: Composite-color volume-transmission receiver.
    /// Uses a pure rational Michaelis-Menten / Cauchy hue binding curve plus
    /// divisive intensity shunting so composite hues decode identically across 400x scales.
    ReceptorBroadcast {
        /// Chromaticity affinity on the `[R, B, Y]` simplex (non-negative, summing to `SCALE = 1000`).
        affinity: [i64; 3],
        /// Hue tuning half-width in fixed-point units (e.g. `160` = `0.16`).
        sigma: i64,
        /// Intensity shunting baseline conductance (e.g. `15` = `0.015`).
        g0: i64,
        /// Minimum activation in `[0, 1000]` required to emit.
        threshold: i64,
        emit_channel: Channel,
    },
    /// Archetype 6: Tapped shift-register timing unit (Jeffress coincidence or Purkinje cancellation).
    DelayLine {
        max_lag: usize,
        mode: DelayMode,
    },
}

impl UnitKind {
    pub fn validate(&self) -> Result<()> {
        match self {
            UnitKind::TriChannel {
                leak_g0,
                threshold,
                yellow_decay,
                blue_gain,
                yellow_gain,
            } => {
                if *leak_g0 <= 0 {
                    return Err(Error::Policy("tri_channel leak_g0 must be > 0".into()));
                }
                if *threshold < 0 || *blue_gain < 0 || *yellow_gain < 0 {
                    return Err(Error::Policy(
                        "tri_channel threshold and gains must be >= 0".into(),
                    ));
                }
                if !(0..=SCALE).contains(yellow_decay) {
                    return Err(Error::Policy(
                        "tri_channel yellow_decay must be in [0, 1000]".into(),
                    ));
                }
            }
            UnitKind::Pyramidal {
                leak_g0,
                threshold,
                apical_threshold,
                coincidence_boost,
                yellow_decay,
            } => {
                if *leak_g0 <= 0 {
                    return Err(Error::Policy("pyramidal leak_g0 must be > 0".into()));
                }
                if *threshold < 0 || *apical_threshold < 0 || *coincidence_boost < 0 {
                    return Err(Error::Policy(
                        "pyramidal thresholds and boost must be >= 0".into(),
                    ));
                }
                if !(0..=SCALE).contains(yellow_decay) {
                    return Err(Error::Policy(
                        "pyramidal yellow_decay must be in [0, 1000]".into(),
                    ));
                }
            }
            UnitKind::ShuntingInterneuron {
                threshold,
                blue_gain,
            } => {
                if *threshold < 0 || *blue_gain < 0 {
                    return Err(Error::Policy(
                        "shunting_interneuron threshold and blue_gain must be >= 0".into(),
                    ));
                }
            }
            UnitKind::ModulatorNucleus {
                tonic_decay,
                red_trigger_gain,
                threshold,
            } => {
                if !(0..=SCALE).contains(tonic_decay) {
                    return Err(Error::Policy(
                        "modulator_nucleus tonic_decay must be in [0, 1000]".into(),
                    ));
                }
                if *red_trigger_gain < 0 || *threshold < 0 {
                    return Err(Error::Policy(
                        "modulator_nucleus gains and threshold must be >= 0".into(),
                    ));
                }
            }
            UnitKind::ReceptorBroadcast {
                affinity,
                sigma,
                g0,
                threshold,
                ..
            } => {
                if affinity.iter().any(|&a| a < 0) || affinity.iter().sum::<i64>() != SCALE {
                    return Err(Error::Policy(
                        "receptor_broadcast affinity components must be >= 0 and sum to 1000".into(),
                    ));
                }
                if *sigma <= 0 || *g0 <= 0 {
                    return Err(Error::Policy(
                        "receptor_broadcast sigma and g0 must be > 0".into(),
                    ));
                }
                if !(0..=SCALE).contains(threshold) {
                    return Err(Error::Policy(
                        "receptor_broadcast threshold must be in [0, 1000]".into(),
                    ));
                }
            }
            UnitKind::DelayLine { max_lag, mode } => {
                if *max_lag == 0 {
                    return Err(Error::Policy("delay_line max_lag must be >= 1".into()));
                }
                match mode {
                    DelayMode::Coincidence {
                        lag_a,
                        lag_b,
                        threshold,
                    } => {
                        if *lag_a > *max_lag || *lag_b > *max_lag {
                            return Err(Error::Policy(
                                "delay_line coincidence lags must be <= max_lag".into(),
                            ));
                        }
                        if *threshold < 0 {
                            return Err(Error::Policy(
                                "delay_line coincidence threshold must be >= 0".into(),
                            ));
                        }
                    }
                    DelayMode::PurkinjeCancel {
                        lr_fast,
                        decay_quiet,
                        decay_error,
                        error_threshold,
                        tap_cap,
                        base_taps,
                    } => {
                        if base_taps.len() != *max_lag {
                            return Err(Error::Policy(
                                "purkinje_cancel base_taps length must equal max_lag".into(),
                            ));
                        }
                        if *lr_fast < 0 || *error_threshold < 0 || *tap_cap < 0 {
                            return Err(Error::Policy(
                                "purkinje_cancel lr_fast, error_threshold, and tap_cap must be >= 0"
                                    .into(),
                            ));
                        }
                        if !(0..=SCALE).contains(decay_quiet) || !(0..=SCALE).contains(decay_error)
                        {
                            return Err(Error::Policy(
                                "purkinje_cancel decays must be in [0, 1000]".into(),
                            ));
                        }
                    }
                }
            }
        }
        Ok(())
    }

    /// Deterministic unit state transition returning the full next `UnitState`.
    pub fn step(&self, prev: &UnitState, incoming: TriSignal) -> UnitState {
        let r_in = incoming.red.max(0);
        let b_in = incoming.blue.max(0);
        let y_in = incoming.yellow.max(0);

        match self {
            UnitKind::TriChannel {
                leak_g0,
                threshold,
                yellow_decay,
                blue_gain,
                yellow_gain,
            } => {
                let next_yellow = (((prev.yellow_level as i128) * (*yellow_decay as i128))
                    / (SCALE as i128)
                    + (y_in as i128))
                    .clamp(0, MAX_SIGNAL as i128) as i64;
                let denom = (*leak_g0 as i128) + (b_in as i128);
                let shunted = ((r_in as i128) * (SCALE as i128)) / denom;
                let gain = (SCALE as i128) + (next_yellow as i128) / 2;
                let drive = (shunted * gain) / (SCALE as i128);
                let out_r = (drive - (*threshold as i128)).clamp(0, MAX_SIGNAL as i128) as i64;
                let out_b = (((out_r as i128) * (*blue_gain as i128)) / (SCALE as i128))
                    .clamp(0, MAX_SIGNAL as i128) as i64;
                let out_y = (((out_r as i128) * (*yellow_gain as i128)) / (SCALE as i128))
                    .clamp(0, MAX_SIGNAL as i128) as i64;
                UnitState {
                    yellow_level: next_yellow,
                    output: TriSignal::new(out_r, out_b, out_y),
                    delay_buf_a: Vec::new(),
                    delay_buf_b: Vec::new(),
                    fast_taps: Vec::new(),
                }
            }
            UnitKind::Pyramidal {
                leak_g0,
                threshold,
                apical_threshold,
                coincidence_boost,
                yellow_decay,
            } => {
                let next_yellow = (((prev.yellow_level as i128) * (*yellow_decay as i128))
                    / (SCALE as i128)
                    + (y_in as i128))
                    .clamp(0, MAX_SIGNAL as i128) as i64;
                let denom = (*leak_g0 as i128) + (b_in as i128);
                let shunted_basal = (((r_in as i128) * (SCALE as i128)) / denom) as i64;

                let (out_r, out_y) = if shunted_basal >= *threshold && y_in >= *apical_threshold {
                    let boost =
                        (((y_in as i128) * (*coincidence_boost as i128)) / (SCALE as i128)) as i64;
                    let r = (shunted_basal + boost - *threshold).clamp(0, MAX_SIGNAL);
                    (r, 0)
                } else if shunted_basal >= *threshold && y_in < *apical_threshold {
                    let r = (shunted_basal - *threshold).clamp(0, MAX_SIGNAL);
                    let y = (shunted_basal - y_in).clamp(0, MAX_SIGNAL);
                    (r, y)
                } else {
                    (0, 0)
                };
                UnitState {
                    yellow_level: next_yellow,
                    output: TriSignal::new(out_r, 0, out_y),
                    delay_buf_a: Vec::new(),
                    delay_buf_b: Vec::new(),
                    fast_taps: Vec::new(),
                }
            }
            UnitKind::ShuntingInterneuron {
                threshold,
                blue_gain,
            } => {
                let drive = (r_in - *threshold).max(0);
                let out_b = (((drive as i128) * (*blue_gain as i128)) / (SCALE as i128))
                    .clamp(0, MAX_SIGNAL as i128) as i64;
                UnitState {
                    yellow_level: 0,
                    output: TriSignal::new(0, out_b, 0),
                    delay_buf_a: Vec::new(),
                    delay_buf_b: Vec::new(),
                    fast_taps: Vec::new(),
                }
            }
            UnitKind::ModulatorNucleus {
                tonic_decay,
                red_trigger_gain,
                threshold,
            } => {
                let red_trig =
                    (((r_in as i128) * (*red_trigger_gain as i128)) / (SCALE as i128)) as i64;
                let next_yellow = (((prev.yellow_level as i128) * (*tonic_decay as i128))
                    / (SCALE as i128)
                    + (y_in as i128)
                    + (red_trig as i128))
                    .clamp(0, MAX_SIGNAL as i128) as i64;
                let out_y = if next_yellow >= *threshold {
                    next_yellow
                } else {
                    0
                };
                UnitState {
                    yellow_level: next_yellow,
                    output: TriSignal::new(0, 0, out_y),
                    delay_buf_a: Vec::new(),
                    delay_buf_b: Vec::new(),
                    fast_taps: Vec::new(),
                }
            }
            UnitKind::ReceptorBroadcast {
                affinity,
                sigma,
                g0,
                threshold,
                emit_channel,
            } => {
                let intensity = (r_in as i128) + (b_in as i128) + (y_in as i128);
                let out_val = if intensity <= 0 {
                    0
                } else {
                    let h0 = ((r_in as i128) * (SCALE as i128)) / intensity;
                    let h1 = ((b_in as i128) * (SCALE as i128)) / intensity;
                    let h2 = ((y_in as i128) * (SCALE as i128)) / intensity;
                    let d0 = h0 - (affinity[0] as i128);
                    let d1 = h1 - (affinity[1] as i128);
                    let d2 = h2 - (affinity[2] as i128);
                    let dist_sq = d0 * d0 + d1 * d1 + d2 * d2;
                    let s2 = (*sigma as i128) * (*sigma as i128);
                    let hue_match = (s2 * (SCALE as i128)) / (s2 + dist_sq);
                    let shunted_int = (intensity * (SCALE as i128)) / ((*g0 as i128) + intensity);
                    let act = ((hue_match * shunted_int) / (SCALE as i128)) as i64;

                    if act < *threshold {
                        0
                    } else if *threshold >= SCALE {
                        SCALE
                    } else {
                        (((act - *threshold) as i128 * (SCALE as i128))
                            / ((SCALE - *threshold) as i128))
                            .clamp(0, SCALE as i128) as i64
                    }
                };
                let output = match emit_channel {
                    Channel::Red => TriSignal::new(out_val, 0, 0),
                    Channel::Blue => TriSignal::new(0, out_val, 0),
                    Channel::Yellow => TriSignal::new(0, 0, out_val),
                };
                UnitState {
                    yellow_level: 0,
                    output,
                    delay_buf_a: Vec::new(),
                    delay_buf_b: Vec::new(),
                    fast_taps: Vec::new(),
                }
            }
            UnitKind::DelayLine { max_lag, mode } => {
                let mut buf_a = Vec::with_capacity(*max_lag + 1);
                buf_a.push(r_in);
                for &v in prev.delay_buf_a.iter().take(*max_lag) {
                    buf_a.push(v);
                }
                while buf_a.len() < *max_lag + 1 {
                    buf_a.push(0);
                }

                let mut buf_b = Vec::with_capacity(*max_lag + 1);
                buf_b.push(b_in);
                for &v in prev.delay_buf_b.iter().take(*max_lag) {
                    buf_b.push(v);
                }
                while buf_b.len() < *max_lag + 1 {
                    buf_b.push(0);
                }

                match mode {
                    DelayMode::Coincidence {
                        lag_a,
                        lag_b,
                        threshold,
                    } => {
                        let va = buf_a[*lag_a].max(0) as u128;
                        let vb = buf_b[*lag_b].max(0) as u128;
                        let score = isqrt_u128(va * vb) as i64;
                        let out_r = if score >= *threshold {
                            score.clamp(0, MAX_SIGNAL)
                        } else {
                            0
                        };
                        UnitState {
                            yellow_level: 0,
                            output: TriSignal::new(out_r, 0, 0),
                            delay_buf_a: buf_a,
                            delay_buf_b: buf_b,
                            fast_taps: Vec::new(),
                        }
                    }
                    DelayMode::PurkinjeCancel {
                        lr_fast,
                        decay_quiet,
                        decay_error,
                        error_threshold,
                        tap_cap,
                        base_taps,
                    } => {
                        let mut cancel_sum: i128 = 0;
                        for k in 0..*max_lag {
                            let ft = prev.fast_taps.get(k).copied().unwrap_or(0);
                            let eff_w = (base_taps[k] as i128) + (ft as i128);
                            cancel_sum += (eff_w * (buf_a[k + 1] as i128)) / (SCALE as i128);
                        }
                        let out_b = cancel_sum.clamp(0, MAX_SIGNAL as i128) as i64;

                        // Climbing-fiber Yellow residual error updates dissolving fast taps.
                        let err = (y_in as i128) - (out_b as i128);
                        let lam = if err.abs() >= (*error_threshold as i128) {
                            *decay_error as i128
                        } else {
                            *decay_quiet as i128
                        };
                        let cap = *tap_cap as i128;
                        let mut next_fast = Vec::with_capacity(*max_lag);
                        for k in 0..*max_lag {
                            let ft = prev.fast_taps.get(k).copied().unwrap_or(0) as i128;
                            let dec = (ft * lam) / (SCALE as i128);
                            let delta = ((*lr_fast as i128) * err * (buf_a[k + 1] as i128))
                                / ((SCALE as i128) * (SCALE as i128));
                            next_fast.push((dec + delta).clamp(-cap, cap) as i64);
                        }
                        UnitState {
                            yellow_level: 0,
                            output: TriSignal::new(0, out_b, 0),
                            delay_buf_a: buf_a,
                            delay_buf_b: buf_b,
                            fast_taps: next_fast,
                        }
                    }
                }
            }
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct UnitSpec {
    pub id: String,
    pub kind: UnitKind,
}

#[derive(Clone, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct UnitState {
    pub yellow_level: i64,
    pub output: TriSignal,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub delay_buf_a: Vec<i64>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub delay_buf_b: Vec<i64>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub fast_taps: Vec<i64>,
}

impl UnitState {
    pub fn for_kind(kind: &UnitKind) -> Self {
        match kind {
            UnitKind::DelayLine { max_lag, mode } => UnitState {
                yellow_level: 0,
                output: TriSignal::default(),
                delay_buf_a: vec![0; *max_lag + 1],
                delay_buf_b: vec![0; *max_lag + 1],
                fast_taps: match mode {
                    DelayMode::PurkinjeCancel { .. } => vec![0; *max_lag],
                    DelayMode::Coincidence { .. } => Vec::new(),
                },
            },
            _ => UnitState::default(),
        }
    }
}

/// Fast-weight local update rule for plastic Red synapses.
#[derive(Clone, Copy, Debug, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum PlasticityRule {
    /// Three-factor associative Hebbian update: `pre_red * post_red`.
    #[default]
    Hebbian,
    /// Three-factor error-correcting Delta update: `pre_red * (post_ext_red - post_syn_red)`.
    /// Enables one-shot surgical overwriting of previous bindings.
    Delta,
}

/// Directed 3-channel synapse with baseline weights, sparse dead-zone Yellow
/// write gating, dissolving fast Red trace, and thresholded consolidation.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SynapseSpec {
    pub from: String,
    pub to: String,
    pub base_red: i64,
    pub base_blue: i64,
    pub base_yellow: i64,
    /// Decay factor (in `[0, 1000]`) when postsynaptic Yellow attention is `0`.
    pub decay_min: i64,
    /// Decay factor (in `[0, 1000]`) when postsynaptic Yellow attention is `>= 1000`.
    pub decay_max: i64,
    /// Sparse dead-zone threshold in `[0, 1000]`: Yellow levels `<= write_deadzone`
    /// produce exact `write_att = 0` (zero distractor write bleed).
    #[serde(default)]
    pub write_deadzone: i64,
    /// Three-factor fast-weight learning rate (in `[0, 2000]`).
    pub learning_rate: i64,
    /// Slow consolidation bleed into `base_red` once `|fast_red| >= consolidation_threshold`.
    pub consolidation_rate: i64,
    pub consolidation_threshold: i64,
    pub fast_cap: i64,
    #[serde(default)]
    pub plasticity: PlasticityRule,
}

impl SynapseSpec {
    pub fn static_channel(from: &str, to: &str, red: i64, blue: i64, yellow: i64) -> Self {
        SynapseSpec {
            from: from.to_string(),
            to: to.to_string(),
            base_red: red,
            base_blue: blue,
            base_yellow: yellow,
            decay_min: 0,
            decay_max: 0,
            write_deadzone: 0,
            learning_rate: 0,
            consolidation_rate: 0,
            consolidation_threshold: 0,
            fast_cap: 0,
            plasticity: PlasticityRule::Hebbian,
        }
    }

    pub fn validate(&self) -> Result<()> {
        if self.from.trim().is_empty() || self.to.trim().is_empty() {
            return Err(Error::Policy(
                "synapse endpoints must be non-empty".into(),
            ));
        }
        if !(0..=SCALE).contains(&self.decay_min)
            || !(0..=SCALE).contains(&self.decay_max)
            || self.decay_min > self.decay_max
        {
            return Err(Error::Policy(
                "synapse decay bounds must satisfy 0 <= decay_min <= decay_max <= 1000".into(),
            ));
        }
        if !(0..=SCALE).contains(&self.write_deadzone) {
            return Err(Error::Policy(
                "synapse write_deadzone must be in [0, 1000]".into(),
            ));
        }
        if self.learning_rate < 0
            || self.consolidation_rate < 0
            || self.consolidation_threshold < 0
            || self.fast_cap < 0
        {
            return Err(Error::Policy(
                "synapse plasticity parameters must be >= 0".into(),
            ));
        }
        Ok(())
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SynapseWeights {
    pub base_red: i64,
    pub fast_red: i64,
}

impl SynapseWeights {
    pub fn effective_red(&self) -> i64 {
        self.base_red.saturating_add(self.fast_red)
    }
}

/// Applies attention-gated dissolution, sparse dead-zone 3-factor Hebbian or
/// Delta fast-weight updates, and thresholded consolidation to one synapse.
pub fn update_synapse(
    spec: &SynapseSpec,
    weights: SynapseWeights,
    pre_red: i64,
    post_red: i64,
    post_ext_red: i64,
    post_syn_red: i64,
    post_yellow_level: i64,
) -> SynapseWeights {
    if spec.learning_rate == 0 && weights.fast_red == 0 {
        return weights;
    }
    let raw_att = post_yellow_level.clamp(0, SCALE) as i128;
    let decay = (spec.decay_min as i128)
        + (((spec.decay_max - spec.decay_min) as i128) * raw_att) / (SCALE as i128);
    let decayed_fast = ((weights.fast_red as i128) * decay) / (SCALE as i128);

    // Sparse dead-zone write gate: exact 0 below `write_deadzone`.
    let dz = spec.write_deadzone as i128;
    let write_att = if raw_att <= dz || dz >= (SCALE as i128) {
        0
    } else {
        ((raw_att - dz) * (SCALE as i128)) / ((SCALE as i128) - dz)
    };

    let drive = match spec.plasticity {
        PlasticityRule::Hebbian => {
            ((pre_red.max(0) as i128) * (post_red.max(0) as i128)) / (SCALE as i128)
        }
        PlasticityRule::Delta => {
            let err = (post_ext_red.max(0) as i128) - (post_syn_red.max(0) as i128);
            ((pre_red.max(0) as i128) * err) / (SCALE as i128)
        }
    };

    let delta_fast =
        ((spec.learning_rate as i128) * write_att * drive) / ((SCALE as i128) * (SCALE as i128));
    let cap = spec.fast_cap as i128;
    let next_fast = (decayed_fast + delta_fast).clamp(-cap, cap) as i64;

    let delta_base = if spec.consolidation_rate > 0
        && next_fast.abs() >= spec.consolidation_threshold
    {
        (((next_fast as i128) * (spec.consolidation_rate as i128)) / (SCALE as i128)) as i64
    } else {
        0
    };

    SynapseWeights {
        base_red: weights.base_red.saturating_add(delta_base),
        fast_red: next_fast,
    }
}

// =====================================================================
// HETEROGENEOUS NEURAL CLUSTER & SIGNED TRACE VERIFICATION
// =====================================================================

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ClusterTopology {
    pub cluster_id: DidKey,
    pub name: String,
    pub units: Vec<UnitSpec>,
    pub synapses: Vec<SynapseSpec>,
}

impl ClusterTopology {
    pub fn validate(&self) -> Result<()> {
        if self.name.trim().is_empty() {
            return Err(Error::Policy("cluster name cannot be empty".into()));
        }
        if self.units.is_empty() {
            return Err(Error::Policy(
                "cluster must contain at least one neural unit".into(),
            ));
        }
        let mut unit_ids = HashSet::new();
        for u in &self.units {
            if u.id.trim().is_empty() || !unit_ids.insert(u.id.clone()) {
                return Err(Error::Policy(
                    "unit ids must be non-empty and unique".into(),
                ));
            }
            u.kind.validate()?;
        }
        let mut seen_edges = HashSet::new();
        for s in &self.synapses {
            s.validate()?;
            if !unit_ids.contains(&s.from) || !unit_ids.contains(&s.to) {
                return Err(Error::Policy(format!(
                    "synapse {} -> {} references unknown unit",
                    s.from, s.to
                )));
            }
            if !seen_edges.insert((s.from.clone(), s.to.clone())) {
                return Err(Error::Policy(format!(
                    "duplicate synapse {} -> {}",
                    s.from, s.to
                )));
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
pub struct ClusterTickRecord {
    pub cluster_id: DidKey,
    pub tick: u64,
    pub prev: Option<String>,
    pub external_inputs: BTreeMap<String, TriSignal>,
    pub unit_states: BTreeMap<String, UnitState>,
    pub synapse_weights: Vec<SynapseWeights>,
    pub proof: ProofOrArray,
}

impl ClusterTickRecord {
    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }

    pub fn verify(&self) -> Result<()> {
        let body = body_for_signing(self)?;
        let proof = self
            .proof
            .find_by_method(&self.cluster_id)
            .ok_or_else(|| Error::Verification("cluster tick: missing cluster proof".into()))?;
        proof.verify(&body)
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ClusterTrace {
    pub topology: ClusterTopology,
    pub ticks: Vec<ClusterTickRecord>,
}

/// Pure one-tick execution step shared by live simulation and offline replay.
fn step_cluster_pure(
    topology: &ClusterTopology,
    prev_units: &BTreeMap<String, UnitState>,
    prev_weights: &[SynapseWeights],
    external_inputs: &BTreeMap<String, TriSignal>,
) -> Result<(BTreeMap<String, UnitState>, Vec<SynapseWeights>)> {
    let mut in_r: HashMap<&str, i64> = HashMap::new();
    let mut in_b: HashMap<&str, i64> = HashMap::new();
    let mut in_y: HashMap<&str, i64> = HashMap::new();
    let mut ext_r: HashMap<&str, i64> = HashMap::new();
    let mut syn_r: HashMap<&str, i64> = HashMap::new();

    for u in &topology.units {
        let ext = external_inputs.get(&u.id).copied().unwrap_or_default();
        let er = ext.red.max(0);
        in_r.insert(u.id.as_str(), er);
        in_b.insert(u.id.as_str(), ext.blue.max(0));
        in_y.insert(u.id.as_str(), ext.yellow.max(0));
        ext_r.insert(u.id.as_str(), er);
        syn_r.insert(u.id.as_str(), 0);
    }
    for key in external_inputs.keys() {
        if !in_r.contains_key(key.as_str()) {
            return Err(Error::Policy(format!(
                "external input targets unknown unit {:?}",
                key
            )));
        }
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
        *syn_r.get_mut(spec.to.as_str()).unwrap() += dr;
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
        let next_st = u.kind.step(&prev_units[&u.id], incoming);
        next_units.insert(u.id.clone(), next_st);
    }

    let mut next_weights = Vec::with_capacity(topology.synapses.len());
    for (spec, &w) in topology.synapses.iter().zip(prev_weights.iter()) {
        let pre_r = prev_units[&spec.from].output.red;
        let post = &next_units[&spec.to];
        next_weights.push(update_synapse(
            spec,
            w,
            pre_r,
            post.output.red,
            ext_r[spec.to.as_str()],
            syn_r[spec.to.as_str()],
            post.yellow_level,
        ));
    }

    Ok((next_units, next_weights))
}

pub struct NeuralCluster {
    keypair: Keypair,
    topology: ClusterTopology,
    unit_states: BTreeMap<String, UnitState>,
    synapse_weights: Vec<SynapseWeights>,
    ticks: Vec<ClusterTickRecord>,
}

impl NeuralCluster {
    pub fn new(
        name: &str,
        keypair: Keypair,
        units: Vec<UnitSpec>,
        synapses: Vec<SynapseSpec>,
    ) -> Result<Self> {
        let topology = ClusterTopology {
            cluster_id: keypair.did(),
            name: name.to_string(),
            units,
            synapses,
        };
        topology.validate()?;

        let mut unit_states = BTreeMap::new();
        for u in &topology.units {
            unit_states.insert(u.id.clone(), UnitState::for_kind(&u.kind));
        }
        let synapse_weights = topology
            .synapses
            .iter()
            .map(|s| SynapseWeights {
                base_red: s.base_red,
                fast_red: 0,
            })
            .collect();

        Ok(NeuralCluster {
            keypair,
            topology,
            unit_states,
            synapse_weights,
            ticks: Vec::new(),
        })
    }

    pub fn unit_state(&self, id: &str) -> Option<&UnitState> {
        self.unit_states.get(id)
    }

    pub fn synapse_weights(&self, from: &str, to: &str) -> Option<SynapseWeights> {
        self.topology
            .synapses
            .iter()
            .position(|s| s.from == from && s.to == to)
            .map(|idx| self.synapse_weights[idx])
    }

    pub fn step(
        &mut self,
        external_inputs: BTreeMap<String, TriSignal>,
    ) -> Result<ClusterTickRecord> {
        let (next_units, next_weights) = step_cluster_pure(
            &self.topology,
            &self.unit_states,
            &self.synapse_weights,
            &external_inputs,
        )?;
        let prev = match self.ticks.last() {
            Some(r) => Some(r.hash()?),
            None => None,
        };
        let mut rec = ClusterTickRecord {
            cluster_id: self.topology.cluster_id.clone(),
            tick: self.ticks.len() as u64,
            prev,
            external_inputs,
            unit_states: next_units.clone(),
            synapse_weights: next_weights.clone(),
            proof: ProofOrArray::placeholder(),
        };
        let body = body_for_signing(&rec)?;
        let sig = self.keypair.sign(&body);
        rec.proof = ProofOrArray::single(Proof::create(&self.keypair, &sig));

        self.unit_states = next_units;
        self.synapse_weights = next_weights;
        self.ticks.push(rec.clone());
        Ok(rec)
    }

    pub fn trace(&self) -> ClusterTrace {
        ClusterTrace {
            topology: self.topology.clone(),
            ticks: self.ticks.clone(),
        }
    }
}

/// Independently replays and verifies an entire `ClusterTrace` offline, checking
/// topology validity, hash chain, cluster signatures, every unit state (including
/// delay buffers and Purkinje fast taps), and every dissolving synapse weight.
pub fn verify_cluster_trace(trace: &ClusterTrace) -> Result<()> {
    trace.topology.validate()?;

    let mut cur_units = BTreeMap::new();
    for u in &trace.topology.units {
        cur_units.insert(u.id.clone(), UnitState::for_kind(&u.kind));
    }
    let mut cur_weights: Vec<SynapseWeights> = trace
        .topology
        .synapses
        .iter()
        .map(|s| SynapseWeights {
            base_red: s.base_red,
            fast_red: 0,
        })
        .collect();
    let mut prev: Option<String> = None;

    for (idx, rec) in trace.ticks.iter().enumerate() {
        if rec.tick != idx as u64 {
            return Err(Error::Chain(format!(
                "cluster trace: tick {} != expected {}",
                rec.tick, idx
            )));
        }
        if rec.cluster_id != trace.topology.cluster_id {
            return Err(Error::Verification(format!(
                "cluster trace tick {idx}: cluster_id mismatch"
            )));
        }
        if rec.prev != prev {
            return Err(Error::Chain(format!(
                "cluster trace tick {idx}: prev hash mismatch"
            )));
        }
        rec.verify()?;

        let (expected_units, expected_weights) = step_cluster_pure(
            &trace.topology,
            &cur_units,
            &cur_weights,
            &rec.external_inputs,
        )?;
        if rec.unit_states != expected_units {
            return Err(Error::Verification(format!(
                "cluster trace tick {idx}: unit_states mismatch"
            )));
        }
        if rec.synapse_weights != expected_weights {
            return Err(Error::Verification(format!(
                "cluster trace tick {idx}: synapse_weights mismatch"
            )));
        }

        cur_units = expected_units;
        cur_weights = expected_weights;
        prev = Some(rec.hash()?);
    }

    Ok(())
}
