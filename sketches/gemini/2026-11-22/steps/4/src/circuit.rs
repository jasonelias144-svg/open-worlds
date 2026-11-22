//! Interacting World Circuits: s_i(t+1) = F_i(s_i(t), m_i(t)).
//!
//! Models a cluster of small deterministic worlds connected by typed,
//! delayed signal routes. Every inter-world signal and per-tick state
//! transition is signed by its owning world's keypair and can be
//! replayed and verified offline.

use crate::did::{DidKey, Keypair};
use crate::error::{Error, Result};
use crate::hash::{body_for_signing, hash_of};
use crate::proof::{Proof, ProofOrArray};
use serde::{Deserialize, Serialize};
use std::collections::{BTreeMap, HashMap, HashSet};

#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SignalKind {
    Bool,
    Int,
    Token,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "kind", content = "value", rename_all = "snake_case")]
pub enum SignalValue {
    Bool(bool),
    Int(i64),
    Token(String),
}

impl SignalValue {
    pub fn kind(&self) -> SignalKind {
        match self {
            SignalValue::Bool(_) => SignalKind::Bool,
            SignalValue::Int(_) => SignalKind::Int,
            SignalValue::Token(_) => SignalKind::Token,
        }
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct PortSpec {
    pub name: String,
    pub kind: SignalKind,
}

/// Deterministic local law F_i governing one world node in a circuit.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "rule", rename_all = "snake_case")]
pub enum WorldRule {
    /// Accumulates integer drive and disturbance inputs and emits its current state.
    Plant { initial: i64 },
    /// Holds a reference target, compares incoming readings against it, and emits error = reading - target.
    Comparator { target: i64 },
    /// Applies bounded negative proportional feedback: -(error * gain_num) / gain_den clamped to [-max_out, max_out].
    FeedbackController {
        gain_num: i64,
        gain_den: i64,
        max_out: i64,
    },
    /// Integrate-and-fire neuron world with weighted integer inputs, leak toward zero, and refractory period.
    Neuron {
        threshold: i64,
        leak: i64,
        refractory_ticks: u64,
        weights: BTreeMap<String, i64>,
    },
    /// 1-bit persistent memory cell (RAM latch) with set/reset boolean ports.
    MemoryLatch { initial: bool },
    /// Integer memory register with write/clear ports.
    Register { initial: i64 },
}

/// Internal state s_i(t) of a world node.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(tag = "state_kind", rename_all = "snake_case")]
pub enum WorldState {
    Plant { value: i64 },
    Comparator { target: i64, last_error: i64 },
    FeedbackController { last_out: i64 },
    Neuron {
        potential: i64,
        refractory_left: u64,
        fired_count: u64,
    },
    MemoryLatch { stored: bool },
    Register { value: i64 },
}

impl WorldRule {
    pub fn validate(&self) -> Result<()> {
        match self {
            WorldRule::FeedbackController {
                gain_den, max_out, ..
            } => {
                if *gain_den <= 0 {
                    return Err(Error::Policy(
                        "feedback controller gain_den must be > 0".into(),
                    ));
                }
                if *max_out < 0 {
                    return Err(Error::Policy(
                        "feedback controller max_out must be >= 0".into(),
                    ));
                }
            }
            WorldRule::Neuron {
                threshold,
                leak,
                weights,
                ..
            } => {
                if *threshold <= 0 {
                    return Err(Error::Policy("neuron threshold must be > 0".into()));
                }
                if *leak < 0 {
                    return Err(Error::Policy("neuron leak must be >= 0".into()));
                }
                if weights.is_empty() {
                    return Err(Error::Policy(
                        "neuron must declare at least one weighted input port".into(),
                    ));
                }
            }
            _ => {}
        }
        Ok(())
    }

    pub fn initial_state(&self) -> WorldState {
        match self {
            WorldRule::Plant { initial } => WorldState::Plant { value: *initial },
            WorldRule::Comparator { target } => WorldState::Comparator {
                target: *target,
                last_error: 0,
            },
            WorldRule::FeedbackController { .. } => WorldState::FeedbackController { last_out: 0 },
            WorldRule::Neuron { .. } => WorldState::Neuron {
                potential: 0,
                refractory_left: 0,
                fired_count: 0,
            },
            WorldRule::MemoryLatch { initial } => WorldState::MemoryLatch { stored: *initial },
            WorldRule::Register { initial } => WorldState::Register { value: *initial },
        }
    }

    pub fn input_ports(&self) -> Vec<PortSpec> {
        match self {
            WorldRule::Plant { .. } => vec![
                PortSpec {
                    name: "drive".into(),
                    kind: SignalKind::Int,
                },
                PortSpec {
                    name: "disturbance".into(),
                    kind: SignalKind::Int,
                },
            ],
            WorldRule::Comparator { .. } => vec![
                PortSpec {
                    name: "reading".into(),
                    kind: SignalKind::Int,
                },
                PortSpec {
                    name: "set_target".into(),
                    kind: SignalKind::Int,
                },
            ],
            WorldRule::FeedbackController { .. } => vec![PortSpec {
                name: "error".into(),
                kind: SignalKind::Int,
            }],
            WorldRule::Neuron { weights, .. } => weights
                .keys()
                .map(|k| PortSpec {
                    name: k.clone(),
                    kind: SignalKind::Int,
                })
                .collect(),
            WorldRule::MemoryLatch { .. } => vec![
                PortSpec {
                    name: "set".into(),
                    kind: SignalKind::Bool,
                },
                PortSpec {
                    name: "reset".into(),
                    kind: SignalKind::Bool,
                },
            ],
            WorldRule::Register { .. } => vec![
                PortSpec {
                    name: "write".into(),
                    kind: SignalKind::Int,
                },
                PortSpec {
                    name: "clear".into(),
                    kind: SignalKind::Bool,
                },
            ],
        }
    }

    pub fn output_ports(&self) -> Vec<PortSpec> {
        match self {
            WorldRule::Plant { .. } => vec![PortSpec {
                name: "state".into(),
                kind: SignalKind::Int,
            }],
            WorldRule::Comparator { .. } => vec![PortSpec {
                name: "error".into(),
                kind: SignalKind::Int,
            }],
            WorldRule::FeedbackController { .. } => vec![PortSpec {
                name: "control".into(),
                kind: SignalKind::Int,
            }],
            WorldRule::Neuron { .. } => vec![PortSpec {
                name: "spike".into(),
                kind: SignalKind::Bool,
            }],
            WorldRule::MemoryLatch { .. } => vec![PortSpec {
                name: "stored".into(),
                kind: SignalKind::Bool,
            }],
            WorldRule::Register { .. } => vec![PortSpec {
                name: "value".into(),
                kind: SignalKind::Int,
            }],
        }
    }

    pub fn input_kind(&self, port: &str) -> Option<SignalKind> {
        self.input_ports()
            .into_iter()
            .find(|p| p.name == port)
            .map(|p| p.kind)
    }

    pub fn output_kind(&self, port: &str) -> Option<SignalKind> {
        self.output_ports()
            .into_iter()
            .find(|p| p.name == port)
            .map(|p| p.kind)
    }

    /// Pure transition s_i(t+1) = F_i(s_i(t), m_i(t)), returning the next state
    /// and all (output_port, value) emissions for this tick.
    pub fn step(
        &self,
        state: &WorldState,
        incoming: &[(String, SignalValue)],
    ) -> Result<(WorldState, Vec<(String, SignalValue)>)> {
        match (self, state) {
            (WorldRule::Plant { .. }, WorldState::Plant { value }) => {
                let mut delta: i64 = 0;
                for (port, sig) in incoming {
                    match (port.as_str(), sig) {
                        ("drive", SignalValue::Int(v)) | ("disturbance", SignalValue::Int(v)) => {
                            delta = delta.saturating_add(*v);
                        }
                        _ => {
                            return Err(Error::Policy(format!(
                                "plant received invalid input on port {:?}",
                                port
                            )));
                        }
                    }
                }
                let next = value.saturating_add(delta);
                Ok((
                    WorldState::Plant { value: next },
                    vec![("state".into(), SignalValue::Int(next))],
                ))
            }
            (
                WorldRule::Comparator { .. },
                WorldState::Comparator { target, last_error },
            ) => {
                let mut next_target = *target;
                let mut latest_reading: Option<i64> = None;
                for (port, sig) in incoming {
                    match (port.as_str(), sig) {
                        ("set_target", SignalValue::Int(v)) => next_target = *v,
                        ("reading", SignalValue::Int(v)) => latest_reading = Some(*v),
                        _ => {
                            return Err(Error::Policy(format!(
                                "comparator received invalid input on port {:?}",
                                port
                            )));
                        }
                    }
                }
                if let Some(reading) = latest_reading {
                    let err = reading.saturating_sub(next_target);
                    Ok((
                        WorldState::Comparator {
                            target: next_target,
                            last_error: err,
                        },
                        vec![("error".into(), SignalValue::Int(err))],
                    ))
                } else {
                    Ok((
                        WorldState::Comparator {
                            target: next_target,
                            last_error: *last_error,
                        },
                        Vec::new(),
                    ))
                }
            }
            (
                WorldRule::FeedbackController {
                    gain_num,
                    gain_den,
                    max_out,
                },
                WorldState::FeedbackController { last_out },
            ) => {
                let mut latest_error: Option<i64> = None;
                for (port, sig) in incoming {
                    match (port.as_str(), sig) {
                        ("error", SignalValue::Int(v)) => latest_error = Some(*v),
                        _ => {
                            return Err(Error::Policy(format!(
                                "controller received invalid input on port {:?}",
                                port
                            )));
                        }
                    }
                }
                if let Some(err) = latest_error {
                    let scaled = err.saturating_mul(*gain_num).saturating_neg() / *gain_den;
                    let clamped = scaled.clamp(-*max_out, *max_out);
                    Ok((
                        WorldState::FeedbackController { last_out: clamped },
                        vec![("control".into(), SignalValue::Int(clamped))],
                    ))
                } else {
                    Ok((
                        WorldState::FeedbackController {
                            last_out: *last_out,
                        },
                        Vec::new(),
                    ))
                }
            }
            (
                WorldRule::Neuron {
                    threshold,
                    leak,
                    refractory_ticks,
                    weights,
                },
                WorldState::Neuron {
                    potential,
                    refractory_left,
                    fired_count,
                },
            ) => {
                if *refractory_left > 0 {
                    for (port, sig) in incoming {
                        if !weights.contains_key(port) || !matches!(sig, SignalValue::Int(_)) {
                            return Err(Error::Policy(format!(
                                "neuron received invalid input on port {:?}",
                                port
                            )));
                        }
                    }
                    return Ok((
                        WorldState::Neuron {
                            potential: *potential,
                            refractory_left: refractory_left - 1,
                            fired_count: *fired_count,
                        },
                        vec![("spike".into(), SignalValue::Bool(false))],
                    ));
                }

                let decayed = if *potential > *leak {
                    potential - leak
                } else if *potential < -*leak {
                    potential + leak
                } else {
                    0
                };

                let mut weighted_sum: i64 = 0;
                for (port, sig) in incoming {
                    match (weights.get(port), sig) {
                        (Some(&w), SignalValue::Int(v)) => {
                            weighted_sum = weighted_sum.saturating_add(w.saturating_mul(*v));
                        }
                        _ => {
                            return Err(Error::Policy(format!(
                                "neuron received invalid input on port {:?}",
                                port
                            )));
                        }
                    }
                }

                let next_pot = decayed.saturating_add(weighted_sum);
                if next_pot >= *threshold {
                    Ok((
                        WorldState::Neuron {
                            potential: 0,
                            refractory_left: *refractory_ticks,
                            fired_count: fired_count.saturating_add(1),
                        },
                        vec![("spike".into(), SignalValue::Bool(true))],
                    ))
                } else {
                    Ok((
                        WorldState::Neuron {
                            potential: next_pot,
                            refractory_left: 0,
                            fired_count: *fired_count,
                        },
                        vec![("spike".into(), SignalValue::Bool(false))],
                    ))
                }
            }
            (WorldRule::MemoryLatch { .. }, WorldState::MemoryLatch { stored }) => {
                let mut set_high = false;
                let mut reset_low = false;
                for (port, sig) in incoming {
                    match (port.as_str(), sig) {
                        ("set", SignalValue::Bool(b)) => set_high |= *b,
                        ("reset", SignalValue::Bool(b)) => reset_low |= *b,
                        _ => {
                            return Err(Error::Policy(format!(
                                "memory latch received invalid input on port {:?}",
                                port
                            )));
                        }
                    }
                }
                let next = if reset_low {
                    false
                } else if set_high {
                    true
                } else {
                    *stored
                };
                Ok((
                    WorldState::MemoryLatch { stored: next },
                    vec![("stored".into(), SignalValue::Bool(next))],
                ))
            }
            (WorldRule::Register { .. }, WorldState::Register { value }) => {
                let mut cleared = false;
                let mut written: Option<i64> = None;
                for (port, sig) in incoming {
                    match (port.as_str(), sig) {
                        ("clear", SignalValue::Bool(b)) => cleared |= *b,
                        ("write", SignalValue::Int(v)) => written = Some(*v),
                        _ => {
                            return Err(Error::Policy(format!(
                                "register received invalid input on port {:?}",
                                port
                            )));
                        }
                    }
                }
                let next = if cleared {
                    0
                } else if let Some(v) = written {
                    v
                } else {
                    *value
                };
                Ok((
                    WorldState::Register { value: next },
                    vec![("value".into(), SignalValue::Int(next))],
                ))
            }
            _ => Err(Error::Verification(
                "world state variant does not match world rule".into(),
            )),
        }
    }
}

/// Directed, typed, delayed wire connecting one world's output port to another's input port.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Route {
    pub from_world: DidKey,
    pub from_port: String,
    pub to_world: DidKey,
    pub to_port: String,
    pub delay: u64,
}

/// Signed signal traveling along a declared route from one world to another.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SignalEnvelope {
    pub from_world: DidKey,
    pub from_port: String,
    pub to_world: DidKey,
    pub to_port: String,
    pub emitted_at: u64,
    pub deliver_at: u64,
    pub payload: SignalValue,
    pub proof: ProofOrArray,
}

impl SignalEnvelope {
    pub fn sign(
        from_kp: &Keypair,
        route: &Route,
        emitted_at: u64,
        payload: SignalValue,
    ) -> Result<Self> {
        if from_kp.did() != route.from_world {
            return Err(Error::Policy("signer does not match route.from_world".into()));
        }
        let mut env = SignalEnvelope {
            from_world: route.from_world.clone(),
            from_port: route.from_port.clone(),
            to_world: route.to_world.clone(),
            to_port: route.to_port.clone(),
            emitted_at,
            deliver_at: emitted_at.saturating_add(route.delay),
            payload,
            proof: ProofOrArray::placeholder(),
        };
        let body = body_for_signing(&env)?;
        let sig = from_kp.sign(&body);
        env.proof = ProofOrArray::single(Proof::create(from_kp, &sig));
        Ok(env)
    }

    pub fn hash(&self) -> Result<String> {
        hash_of(self)
    }

    pub fn verify(&self) -> Result<()> {
        if self.deliver_at <= self.emitted_at {
            return Err(Error::Verification(
                "signal envelope: deliver_at must be > emitted_at".into(),
            ));
        }
        let body = body_for_signing(self)?;
        let proof = self
            .proof
            .find_by_method(&self.from_world)
            .ok_or_else(|| Error::Verification("signal envelope: missing sender proof".into()))?;
        proof.verify(&body)
    }
}

/// External input injected into a world's input port at a specific tick.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct ExternalInput {
    pub to_world: DidKey,
    pub to_port: String,
    pub value: SignalValue,
}

/// Signed commitment emitted by one world node after completing a tick.
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct NodeTickRecord {
    pub world_id: DidKey,
    pub tick: u64,
    pub prev_state_hash: String,
    pub next_state_hash: String,
    pub consumed_signal_hashes: Vec<String>,
    pub emitted_signal_hashes: Vec<String>,
    pub proof: ProofOrArray,
}

impl NodeTickRecord {
    pub fn verify(&self) -> Result<()> {
        let body = body_for_signing(self)?;
        let proof = self
            .proof
            .find_by_method(&self.world_id)
            .ok_or_else(|| Error::Verification("node tick record: missing world proof".into()))?;
        proof.verify(&body)
    }
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct NodeSpec {
    pub world_id: DidKey,
    pub name: String,
    pub rule: WorldRule,
    pub initial_state: WorldState,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CircuitTopology {
    pub nodes: Vec<NodeSpec>,
    pub routes: Vec<Route>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct TickRecord {
    pub tick: u64,
    pub external_inputs: Vec<ExternalInput>,
    pub delivered_signals: Vec<SignalEnvelope>,
    pub node_records: Vec<NodeTickRecord>,
    pub emitted_signals: Vec<SignalEnvelope>,
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct CircuitTrace {
    pub topology: CircuitTopology,
    pub ticks: Vec<TickRecord>,
}

struct LiveNode {
    name: String,
    keypair: Keypair,
    rule: WorldRule,
    initial_state: WorldState,
    state: WorldState,
}

/// Executable multi-world circuit producing a signed, offline-verifiable trace.
pub struct WorldCircuit {
    node_order: Vec<DidKey>,
    nodes: HashMap<DidKey, LiveNode>,
    routes: Vec<Route>,
    in_flight: Vec<SignalEnvelope>,
    tick: u64,
    history: Vec<TickRecord>,
}

impl Default for WorldCircuit {
    fn default() -> Self {
        Self::new()
    }
}

impl WorldCircuit {
    pub fn new() -> Self {
        WorldCircuit {
            node_order: Vec::new(),
            nodes: HashMap::new(),
            routes: Vec::new(),
            in_flight: Vec::new(),
            tick: 0,
            history: Vec::new(),
        }
    }

    pub fn add_world(&mut self, name: &str, keypair: Keypair, rule: WorldRule) -> Result<DidKey> {
        if !self.history.is_empty() {
            return Err(Error::Policy(
                "cannot add worlds after circuit execution has started".into(),
            ));
        }
        if name.trim().is_empty() {
            return Err(Error::Policy("world name cannot be empty".into()));
        }
        rule.validate()?;
        let world_id = keypair.did();
        if self.nodes.contains_key(&world_id) {
            return Err(Error::Policy("duplicate world_id in circuit".into()));
        }
        let initial_state = rule.initial_state();
        self.node_order.push(world_id.clone());
        self.nodes.insert(
            world_id.clone(),
            LiveNode {
                name: name.to_string(),
                keypair,
                rule,
                initial_state: initial_state.clone(),
                state: initial_state,
            },
        );
        Ok(world_id)
    }

    pub fn add_route(&mut self, route: Route) -> Result<()> {
        if !self.history.is_empty() {
            return Err(Error::Policy(
                "cannot add routes after circuit execution has started".into(),
            ));
        }
        if route.delay == 0 {
            return Err(Error::Policy(
                "route delay must be >= 1 tick for causal synchronous updates".into(),
            ));
        }
        let from_node = self
            .nodes
            .get(&route.from_world)
            .ok_or_else(|| Error::Policy("route.from_world not found in circuit".into()))?;
        let to_node = self
            .nodes
            .get(&route.to_world)
            .ok_or_else(|| Error::Policy("route.to_world not found in circuit".into()))?;

        let out_kind = from_node.rule.output_kind(&route.from_port).ok_or_else(|| {
            Error::Policy(format!(
                "source world {} has no output port {:?}",
                from_node.name, route.from_port
            ))
        })?;
        let in_kind = to_node.rule.input_kind(&route.to_port).ok_or_else(|| {
            Error::Policy(format!(
                "destination world {} has no input port {:?}",
                to_node.name, route.to_port
            ))
        })?;
        if out_kind != in_kind {
            return Err(Error::Policy(format!(
                "port type mismatch: {:?} ({:?}) -> {:?} ({:?})",
                route.from_port, out_kind, route.to_port, in_kind
            )));
        }
        let duplicate = self.routes.iter().any(|r| {
            r.from_world == route.from_world
                && r.from_port == route.from_port
                && r.to_world == route.to_world
                && r.to_port == route.to_port
        });
        if duplicate {
            return Err(Error::Policy("duplicate route between identical ports".into()));
        }
        self.routes.push(route);
        Ok(())
    }

    pub fn state(&self, world_id: &DidKey) -> Option<&WorldState> {
        self.nodes.get(world_id).map(|n| &n.state)
    }

    pub fn tick(&self) -> u64 {
        self.tick
    }

    /// Advance the entire circuit by one synchronous tick, delivering due
    /// in-flight signals plus `external_inputs`, updating every world, and
    /// signing all emitted envelopes and node tick records.
    pub fn step(&mut self, external_inputs: Vec<ExternalInput>) -> Result<TickRecord> {
        let current_tick = self.tick;

        // Validate external inputs before mutating any state.
        for ext in &external_inputs {
            let node = self
                .nodes
                .get(&ext.to_world)
                .ok_or_else(|| Error::Policy("external input targets unknown world".into()))?;
            let expected_kind = node.rule.input_kind(&ext.to_port).ok_or_else(|| {
                Error::Policy(format!(
                    "world {} has no input port {:?}",
                    node.name, ext.to_port
                ))
            })?;
            if ext.value.kind() != expected_kind {
                return Err(Error::Policy(format!(
                    "external input kind mismatch on port {:?}",
                    ext.to_port
                )));
            }
        }

        // Partition in-flight signals into those due now vs. still traveling.
        let mut delivered_signals = Vec::new();
        let mut remaining = Vec::new();
        for env in self.in_flight.drain(..) {
            if env.deliver_at == current_tick {
                delivered_signals.push(env);
            } else {
                remaining.push(env);
            }
        }
        self.in_flight = remaining;

        let mut node_records = Vec::with_capacity(self.node_order.len());
        let mut emitted_signals = Vec::new();
        let mut next_states: HashMap<DidKey, WorldState> = HashMap::new();

        for wid in &self.node_order {
            let node = self.nodes.get(wid).unwrap();

            let mut incoming: Vec<(String, SignalValue)> = Vec::new();
            let mut consumed_hashes: Vec<String> = Vec::new();
            for env in &delivered_signals {
                if &env.to_world == wid {
                    env.verify()?;
                    incoming.push((env.to_port.clone(), env.payload.clone()));
                    consumed_hashes.push(env.hash()?);
                }
            }
            for ext in &external_inputs {
                if &ext.to_world == wid {
                    incoming.push((ext.to_port.clone(), ext.value.clone()));
                }
            }
            consumed_hashes.sort();

            let prev_state_hash = hash_of(&node.state)?;
            let (next_state, outputs) = node.rule.step(&node.state, &incoming)?;
            let next_state_hash = hash_of(&next_state)?;

            let mut node_emitted_hashes: Vec<String> = Vec::new();
            for (out_port, out_val) in outputs {
                for route in &self.routes {
                    if &route.from_world == wid && route.from_port == out_port {
                        let env = SignalEnvelope::sign(
                            &node.keypair,
                            route,
                            current_tick,
                            out_val.clone(),
                        )?;
                        node_emitted_hashes.push(env.hash()?);
                        emitted_signals.push(env);
                    }
                }
            }
            node_emitted_hashes.sort();

            let mut rec = NodeTickRecord {
                world_id: wid.clone(),
                tick: current_tick,
                prev_state_hash,
                next_state_hash,
                consumed_signal_hashes: consumed_hashes,
                emitted_signal_hashes: node_emitted_hashes,
                proof: ProofOrArray::placeholder(),
            };
            let body = body_for_signing(&rec)?;
            let sig = node.keypair.sign(&body);
            rec.proof = ProofOrArray::single(Proof::create(&node.keypair, &sig));
            node_records.push(rec);
            next_states.insert(wid.clone(), next_state);
        }

        for (wid, ns) in next_states {
            self.nodes.get_mut(&wid).unwrap().state = ns;
        }
        self.in_flight.extend(emitted_signals.iter().cloned());

        let record = TickRecord {
            tick: current_tick,
            external_inputs,
            delivered_signals,
            node_records,
            emitted_signals,
        };
        self.history.push(record.clone());
        self.tick += 1;
        Ok(record)
    }

    pub fn trace(&self) -> CircuitTrace {
        let nodes = self
            .node_order
            .iter()
            .map(|wid| {
                let n = self.nodes.get(wid).unwrap();
                NodeSpec {
                    world_id: wid.clone(),
                    name: n.name.clone(),
                    rule: n.rule.clone(),
                    initial_state: n.initial_state.clone(),
                }
            })
            .collect();
        CircuitTrace {
            topology: CircuitTopology {
                nodes,
                routes: self.routes.clone(),
            },
            ticks: self.history.clone(),
        }
    }
}

/// Independently verify an entire `CircuitTrace` offline:
/// validates topology, port types, signatures, causal signal delivery,
/// and deterministic state replay for every world at every tick.
pub fn verify_circuit_trace(trace: &CircuitTrace) -> Result<()> {
    let mut rules: HashMap<DidKey, &WorldRule> = HashMap::new();
    let mut states: HashMap<DidKey, WorldState> = HashMap::new();
    let mut seen_nodes: HashSet<DidKey> = HashSet::new();

    for spec in &trace.topology.nodes {
        spec.rule.validate()?;
        if !seen_nodes.insert(spec.world_id.clone()) {
            return Err(Error::Verification(
                "circuit trace: duplicate world_id in topology".into(),
            ));
        }
        if spec.initial_state != spec.rule.initial_state() {
            return Err(Error::Verification(
                "circuit trace: initial_state does not match rule".into(),
            ));
        }
        rules.insert(spec.world_id.clone(), &spec.rule);
        states.insert(spec.world_id.clone(), spec.initial_state.clone());
    }

    for route in &trace.topology.routes {
        if route.delay == 0 {
            return Err(Error::Verification("circuit trace: route delay is 0".into()));
        }
        let from_rule = rules
            .get(&route.from_world)
            .ok_or_else(|| Error::Verification("circuit trace: unknown route.from_world".into()))?;
        let to_rule = rules
            .get(&route.to_world)
            .ok_or_else(|| Error::Verification("circuit trace: unknown route.to_world".into()))?;
        let out_kind = from_rule
            .output_kind(&route.from_port)
            .ok_or_else(|| Error::Verification("circuit trace: invalid route.from_port".into()))?;
        let in_kind = to_rule
            .input_kind(&route.to_port)
            .ok_or_else(|| Error::Verification("circuit trace: invalid route.to_port".into()))?;
        if out_kind != in_kind {
            return Err(Error::Verification(
                "circuit trace: route port kind mismatch".into(),
            ));
        }
    }

    let mut expected_in_flight: Vec<SignalEnvelope> = Vec::new();

    for (expected_tick, tick_rec) in trace.ticks.iter().enumerate() {
        let t = expected_tick as u64;
        if tick_rec.tick != t {
            return Err(Error::Chain(format!(
                "circuit trace: tick {} != expected {}",
                tick_rec.tick, t
            )));
        }

        // Check that delivered_signals exactly matches previously emitted signals due at tick t.
        let mut due_now = Vec::new();
        let mut still_flying = Vec::new();
        for env in expected_in_flight.drain(..) {
            if env.deliver_at == t {
                due_now.push(env);
            } else {
                still_flying.push(env);
            }
        }
        expected_in_flight = still_flying;

        let mut expected_due_hashes: Vec<String> = due_now
            .iter()
            .map(|e| e.hash())
            .collect::<Result<Vec<_>>>()?;
        let mut actual_due_hashes: Vec<String> = tick_rec
            .delivered_signals
            .iter()
            .map(|e| {
                e.verify()?;
                e.hash()
            })
            .collect::<Result<Vec<_>>>()?;
        expected_due_hashes.sort();
        actual_due_hashes.sort();
        if expected_due_hashes != actual_due_hashes {
            return Err(Error::Verification(format!(
                "circuit trace tick {t}: delivered_signals mismatch against scheduled flights"
            )));
        }

        // Verify all emitted_signals signatures up front and index by hash.
        let mut emitted_by_hash: HashMap<String, &SignalEnvelope> = HashMap::new();
        for env in &tick_rec.emitted_signals {
            env.verify()?;
            if env.emitted_at != t {
                return Err(Error::Verification(format!(
                    "circuit trace tick {t}: emitted signal has emitted_at {}",
                    env.emitted_at
                )));
            }
            emitted_by_hash.insert(env.hash()?, env);
        }

        if tick_rec.node_records.len() != trace.topology.nodes.len() {
            return Err(Error::Verification(format!(
                "circuit trace tick {t}: node_records count mismatch"
            )));
        }

        let mut accounted_emitted_hashes: HashSet<String> = HashSet::new();
        let mut next_states: HashMap<DidKey, WorldState> = HashMap::new();

        for (spec, node_rec) in trace.topology.nodes.iter().zip(tick_rec.node_records.iter()) {
            let wid = &spec.world_id;
            if &node_rec.world_id != wid || node_rec.tick != t {
                return Err(Error::Verification(format!(
                    "circuit trace tick {t}: node record world_id or tick mismatch"
                )));
            }
            node_rec.verify()?;

            let cur_state = states.get(wid).unwrap();
            if node_rec.prev_state_hash != hash_of(cur_state)? {
                return Err(Error::Verification(format!(
                    "circuit trace tick {t}: prev_state_hash mismatch for {}",
                    spec.name
                )));
            }

            let mut incoming = Vec::new();
            let mut consumed_hashes = Vec::new();
            for env in &tick_rec.delivered_signals {
                if &env.to_world == wid {
                    incoming.push((env.to_port.clone(), env.payload.clone()));
                    consumed_hashes.push(env.hash()?);
                }
            }
            for ext in &tick_rec.external_inputs {
                if &ext.to_world == wid {
                    incoming.push((ext.to_port.clone(), ext.value.clone()));
                }
            }
            consumed_hashes.sort();
            if node_rec.consumed_signal_hashes != consumed_hashes {
                return Err(Error::Verification(format!(
                    "circuit trace tick {t}: consumed_signal_hashes mismatch for {}",
                    spec.name
                )));
            }

            let (expected_next, expected_outputs) = spec.rule.step(cur_state, &incoming)?;
            if node_rec.next_state_hash != hash_of(&expected_next)? {
                return Err(Error::Verification(format!(
                    "circuit trace tick {t}: next_state_hash mismatch for {}",
                    spec.name
                )));
            }

            // Reconcile expected routed outputs against emitted_signals claimed by this node.
            let mut expected_route_payloads: Vec<(String, DidKey, String, u64, SignalValue)> =
                Vec::new();
            for (out_port, out_val) in expected_outputs {
                for route in &trace.topology.routes {
                    if &route.from_world == wid && route.from_port == out_port {
                        expected_route_payloads.push((
                            route.from_port.clone(),
                            route.to_world.clone(),
                            route.to_port.clone(),
                            t.saturating_add(route.delay),
                            out_val.clone(),
                        ));
                    }
                }
            }

            if node_rec.emitted_signal_hashes.len() != expected_route_payloads.len() {
                return Err(Error::Verification(format!(
                    "circuit trace tick {t}: emitted signal count mismatch for {}",
                    spec.name
                )));
            }

            let mut remaining_expected = expected_route_payloads;
            for h in &node_rec.emitted_signal_hashes {
                let env = emitted_by_hash.get(h).ok_or_else(|| {
                    Error::Verification(format!(
                        "circuit trace tick {t}: node references missing emitted signal"
                    ))
                })?;
                if &env.from_world != wid {
                    return Err(Error::Verification(format!(
                        "circuit trace tick {t}: emitted signal sender mismatch"
                    )));
                }
                let pos = remaining_expected
                    .iter()
                    .position(|(fp, tw, tp, da, pv)| {
                        fp == &env.from_port
                            && tw == &env.to_world
                            && tp == &env.to_port
                            && *da == env.deliver_at
                            && pv == &env.payload
                    })
                    .ok_or_else(|| {
                        Error::Verification(format!(
                            "circuit trace tick {t}: unauthorized or mismatched emitted signal for {}",
                            spec.name
                        ))
                    })?;
                remaining_expected.remove(pos);
                accounted_emitted_hashes.insert(h.clone());
            }

            next_states.insert(wid.clone(), expected_next);
        }

        if accounted_emitted_hashes.len() != tick_rec.emitted_signals.len() {
            return Err(Error::Verification(format!(
                "circuit trace tick {t}: extraneous unaccounted emitted signals"
            )));
        }

        expected_in_flight.extend(tick_rec.emitted_signals.iter().cloned());
        states = next_states;
    }

    Ok(())
}
