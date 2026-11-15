//! The garden's keeper: observation, proposal, no auto-apply.
//!
//! The `GardenCurator` reads a `Garden`'s log and current
//! state, forms a `CuratorObservation` (which plants are being
//! observed, which agents are talking, who is isolated), and
//! produces zero or more `GardenProposal`s. The keeper (the
//! garden's operator) decides whether to record and apply each
//! proposal.
//!
//! Composition:
//!   - `Garden` and its log are the observation source.
//!   - `formats::proof::sign` signs each proposal body.
//!   - No new record kind in the schema yet; proposals are
//!     structured `serde_json::Value`s with
//!     `"kind": "garden_curator_proposal"`. Schema integration
//!     and a vector test are the next cycle.
//!
//! The god-game stance is deliberately one-directional: the
//! curator proposes; the keeper applies. The curator never
//! mutates the garden.

use std::collections::HashMap;

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

use crate::garden::{
    Cell, Garden, GardenAction, PlantKind, PlantEvent,
};
use formats::proof::SigningKey;

// ────────────────────────────────────────────────────────────
// Observation
// ────────────────────────────────────────────────────────────

#[derive(Debug, Clone)]
pub struct CuratorObservation {
    pub cycle: u64,
    pub plants: Vec<PlantStatus>,
    pub agents: Vec<AgentStatus>,
    pub recent_speech: Vec<SpeechRecord>,
}

#[derive(Debug, Clone)]
pub struct PlantStatus {
    pub id: String,
    pub kind: PlantKind,
    pub position: Cell,
    pub total_events: usize,
    /// Observations of this plant in the last `window` cycles.
    pub observations_recent: usize,
}

#[derive(Debug, Clone)]
pub struct AgentStatus {
    pub did: String,
    pub name: String,
    pub position: Cell,
    /// DIDs within Manhattan distance 2.
    pub nearby_agents: Vec<String>,
    /// Plant IDs at Manhattan distance 1.
    pub adjacent_plants: Vec<String>,
    pub speech_count_recent: usize,
    pub heard_count_recent: usize,
    pub observation_count_recent: usize,
}

#[derive(Debug, Clone)]
pub struct SpeechRecord {
    pub speaker: String,
    pub text: String,
    pub heard_by: Vec<String>,
    pub cycle_approx: u64,
}

// ────────────────────────────────────────────────────────────
// Proposal
// ────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "proposal_type")]
pub enum GardenProposal {
    /// Move a plant to a new cell.
    #[serde(rename = "move_plant")]
    MovePlant { plant_id: String, to: [i64; 3] },

    /// Add a plant at an empty cell.
    #[serde(rename = "add_plant")]
    AddPlant {
        plant_id: String,
        kind: String,
        at: [i64; 3],
    },

    /// Retire a plant.
    #[serde(rename = "retire_plant")]
    RetirePlant { plant_id: String, reason: String },

    /// Suggest two agents meet.
    #[serde(rename = "invite")]
    Invite {
        agent_a: String,
        agent_b: String,
        at: [i64; 3],
    },

    /// A public (or targeted) hint logged for agents to see
    /// in their next `observe`.
    #[serde(rename = "whisper")]
    Whisper { to: Option<String>, text: String },
}

impl GardenProposal {
    /// The proposal as a signed-record body. The garden's
    /// `record_proposal` signs and chains it.
    pub fn body(&self, curator_did: &str, cycle: u64) -> Value {
        json!({
            "kind": "garden_curator_proposal",
            "curator": curator_did,
            "cycle": cycle,
            "proposal": self,
        })
    }
}

// ────────────────────────────────────────────────────────────
// Curator
// ────────────────────────────────────────────────────────────

pub struct GardenCurator {
    curator_key: SigningKey,
    curator_did: String,
    window: u64,
    isolated_plant_threshold: usize,
    isolated_agent_threshold: usize,
    unheard_speech_threshold: usize,
}

impl GardenCurator {
    /// Construct a curator. Uses the same key as the garden's
    /// keeper in v0.1 — the curator *is* the keeper. A future
    /// cycle can separate them via the world-keys machinery
    /// from `gallery_governance`.
    pub fn new(curator_key: SigningKey) -> Self {
        let curator_did = curator_key.did();
        Self {
            curator_key,
            curator_did,
            window: 10,
            isolated_plant_threshold: 1,
            isolated_agent_threshold: 2,
            unheard_speech_threshold: 3,
        }
    }

    pub fn curator_did(&self) -> &str { &self.curator_did }
    pub fn curator_key(&self) -> &SigningKey { &self.curator_key }

    /// Read the garden into an observation. Pure; never
    /// mutates.
    pub fn observe(&self, garden: &Garden) -> CuratorObservation {
        let current = garden.cycle;
        let cutoff = current.saturating_sub(self.window);

        // Track "what cycle was it when this entry was
        // written" by walking cycle_advanced entries. Entries
        // that never follow a cycle_advanced are considered
        // pre-cycle (cycle 0).
        let mut entry_cycle: u64 = 0;
        let mut plant_obs: HashMap<String, usize> = HashMap::new();
        let mut agent_speech: HashMap<String, (usize, usize)> =
            HashMap::new();
        let mut agent_obs: HashMap<String, usize> = HashMap::new();
        let mut recent_speech: Vec<SpeechRecord> = Vec::new();

        for entry in &garden.log {
            let body = &entry.body;
            let kind = body.get("kind").and_then(|v| v.as_str());

            if kind == Some("cycle_advanced") {
                if let Some(c) = body.get("cycle").and_then(|v| v.as_u64()) {
                    entry_cycle = c;
                }
                continue;
            }
            if entry_cycle < cutoff {
                continue;
            }

            match kind {
                Some("agent_observed") => {
                    if body.get("result").and_then(|v| v.as_str())
                        == Some("observed_plant")
                    {
                        if let Some(pid) =
                            body.get("plant_id").and_then(|v| v.as_str())
                        {
                            *plant_obs.entry(pid.to_string()).or_insert(0) += 1;
                        }
                    }
                    if let Some(aid) =
                        body.get("actor").and_then(|v| v.as_str())
                    {
                        *agent_obs.entry(aid.to_string()).or_insert(0) += 1;
                    }
                }
                Some("agent_spoke") => {
                    let aid = body.get("actor")
                        .and_then(|v| v.as_str()).unwrap_or("");
                    let heard: Vec<String> = body.get("heard_by")
                        .and_then(|v| v.as_array())
                        .map(|arr| arr.iter()
                            .filter_map(|v| v.as_str().map(String::from))
                            .collect())
                        .unwrap_or_default();
                    let e = agent_speech
                        .entry(aid.to_string()).or_insert((0, 0));
                    e.0 += 1;
                    if !heard.is_empty() { e.1 += 1; }
                    recent_speech.push(SpeechRecord {
                        speaker: aid.to_string(),
                        text: body.get("text")
                            .and_then(|v| v.as_str())
                            .unwrap_or("").to_string(),
                        heard_by: heard,
                        cycle_approx: entry_cycle,
                    });
                }
                _ => {}
            }
        }

        let plants: Vec<PlantStatus> = garden.plants_active.iter()
            .map(|(id, p)| PlantStatus {
                id: id.clone(),
                kind: p.kind,
                position: p.position,
                total_events: p.events().len(),
                observations_recent: *plant_obs.get(id).unwrap_or(&0),
            })
            .collect();

        let agents: Vec<AgentStatus> = garden.agent_positions.iter()
            .map(|(did, pos)| {
                let nearby = garden.agent_positions.iter()
                    .filter(|(other, p)| {
                        *other != did && p.distance(pos) <= 2
                    })
                    .map(|(d, _)| d.clone())
                    .collect();
                let adjacent = garden.plants_active.iter()
                    .filter(|(_, p)| p.position.is_adjacent(pos))
                    .map(|(pid, _)| pid.clone())
                    .collect();
                let (s, h) = agent_speech.get(did)
                    .copied().unwrap_or((0, 0));
                AgentStatus {
                    did: did.clone(),
                    name: garden.admitted.get(did)
                        .cloned().unwrap_or_default(),
                    position: *pos,
                    nearby_agents: nearby,
                    adjacent_plants: adjacent,
                    speech_count_recent: s,
                    heard_count_recent: h,
                    observation_count_recent:
                        *agent_obs.get(did).unwrap_or(&0),
                }
            })
            .collect();

        CuratorObservation {
            cycle: current,
            plants,
            agents,
            recent_speech,
        }
    }

    /// Given an observation, produce zero or more proposals.
    /// The keeper decides what to apply.
    pub fn propose(&self, obs: &CuratorObservation) -> Vec<GardenProposal> {
        let mut out: Vec<GardenProposal> = Vec::new();

        // 1. Isolated plants: nobody has looked. Propose a
        //    public whisper so agents notice.
        for p in &obs.plants {
            if p.observations_recent < self.isolated_plant_threshold {
                out.push(GardenProposal::Whisper {
                    to: None,
                    text: format!(
                        "the {} at ({}, {}) has been quiet",
                        plant_kind_str(p.kind),
                        p.position.x, p.position.y,
                    ),
                });
            }
        }

        // 2. Isolated agents: not observing, no one nearby.
        //    Invite them to meet.
        for a in &obs.agents {
            if a.observation_count_recent
                    < self.isolated_agent_threshold
                && a.nearby_agents.is_empty()
            {
                if let Some(other) = obs.agents.iter()
                    .find(|o| o.did != a.did)
                {
                    let mx = (a.position.x + other.position.x) / 2;
                    let my = (a.position.y + other.position.y) / 2;
                    if mx != a.position.x || my != a.position.y {
                        out.push(GardenProposal::Invite {
                            agent_a: a.did.clone(),
                            agent_b: other.did.clone(),
                            at: [mx, my, 0],
                        });
                    }
                }
            }
        }

        // 3. Unheard speakers: they talk; no one hears.
        //    Whisper a suggestion.
        for a in &obs.agents {
            if a.speech_count_recent
                    >= self.unheard_speech_threshold
                && a.heard_count_recent == 0
            {
                out.push(GardenProposal::Whisper {
                    to: Some(a.did.clone()),
                    text: "perhaps walk toward the other \
                           to be heard".into(),
                });
            }
        }

        out
    }

    /// Observe + propose in one call. Signs each proposal's
    /// body with the curator key.
    pub fn observe_and_propose(
        &self,
        garden: &Garden,
    ) -> Vec<Value> {
        let obs = self.observe(garden);
        self.propose(&obs)
            .into_iter()
            .map(|p| p.body(&self.curator_did, obs.cycle))
            .collect()
    }
}

fn plant_kind_str(k: PlantKind) -> &'static str {
    match k {
        PlantKind::Fern => "fern",
        PlantKind::Tree => "tree",
        PlantKind::Vine => "vine",
    }
}
