//! GardenClient — a WCP client for the garden.
//!
//! Wraps the HTTP endpoints in a small typed API so a
//! `TinyRnnMind` can drive a resident over the wire:
//!
//!   let mut client = GardenClient::new(url, key);
//!   client.enter(Cell { x: 0, y: 4, z: 0 })?;
//!   let obs = client.observe()?;
//!   let action = mind.observe(obs);
//!   client.act(action)?;
//!   mind.receive(Outcome { ... });

use serde_json::{json, Value};

use crate::garden::{Direction, GardenAction, PlantKind};
use crate::garden::rnn_mind::Observation;
use crate::world::Cell;
use formats::proof::SigningKey;

pub struct GardenClient {
    base_url: String,
    agent_key: SigningKey,
    agent_did: String,
    garden_size: [i64; 3],
}

impl GardenClient {
    pub fn new(base_url: String, agent_key: SigningKey) -> Self {
        let agent_did = agent_key.did();
        Self {
            base_url: base_url.trim_end_matches('/').to_string(),
            agent_key,
            agent_did,
            garden_size: [9, 8, 1],
        }
    }

    /// Fetch the lobby and remember the garden size (parsed
    /// from the manifest, or defaulted).
    pub fn connect(&mut self) -> Result<Value, String> {
        let m = self.get("/manifest")?;
        // Manifest shape: {manifest: {...}, proof: {...}}
        if let Some(size) = m.get("manifest")
            .and_then(|m| m.get("garden_size"))
        {
            if let Some(arr) = size.as_array() {
                if arr.len() == 3 {
                    self.garden_size = [
                        arr[0].as_i64().unwrap_or(9),
                        arr[1].as_i64().unwrap_or(8),
                        arr[2].as_i64().unwrap_or(1),
                    ];
                }
            }
        }
        Ok(m)
    }

    pub fn petition(&self, name: &str) -> Result<(), String> {
        let body = json!({
            "petitioner_token": self.agent_did,
            "petitioner_name": name,
            "passport_admissions": [],
            "message": "entering via GardenClient",
        });
        let resp = self.post("/petition", &body)?;
        match resp.get("kind").and_then(|v| v.as_str()) {
            Some("admission") => Ok(()),
            Some("refusal") => Err(
                resp.get("reason").and_then(|v| v.as_str())
                    .unwrap_or("refused").to_string()),
            _ => Err(format!("unexpected: {:?}", resp)),
        }
    }

    pub fn enter(&self, at: Cell) -> Result<(), String> {
        self.do_act("garden.walk",
            json!({"start": [at.x, at.y, at.z]}))
    }

    pub fn act(&self, action: GardenAction) -> Result<(), String> {
        match action {
            GardenAction::Walk { direction } => {
                let d = match direction {
                    Direction::North => "N",
                    Direction::South => "S",
                    Direction::East => "E",
                    Direction::West => "W",
                };
                self.do_act("garden.walk",
                    json!({"direction": d}))
            }
            GardenAction::Observe => {
                self.do_act("garden.observe", json!({}))
            }
            GardenAction::Speak { text } => {
                self.do_act("garden.speak", json!({"text": text}))
            }
            GardenAction::Enter { at } => {
                self.do_act("garden.walk",
                    json!({"start": [at.x, at.y, at.z]}))
            }
        }
    }

    fn do_act(&self, ty: &str, payload: Value) -> Result<(), String> {
        let body = json!({
            "actor_token": self.agent_did,
            "type": ty,
            "payload": payload,
        });
        let resp = self.post("/act", &body)?;
        match resp.get("kind").and_then(|v| v.as_str()) {
            Some("ack") => Ok(()),
            Some("refusal") => Err(
                resp.get("reason").and_then(|v| v.as_str())
                    .unwrap_or("refused").to_string()),
            _ => Err(format!("unexpected: {:?}", resp)),
        }
    }

    /// Rebuild an `Observation` for a Mind from the garden
    /// log and current state.
    pub fn observe(&self) -> Result<Observation, String> {
        let log = self.get("/log")?;
        let entries = log.get("entries").and_then(|v| v.as_array())
            .ok_or("no entries")?;

        // Find this agent's position
        let mut position: Option<Cell> = None;
        let mut last_action: u8 = 0;
        let mut last_reward_micros: u64 = 0;
        let mut plants: Vec<(String, Cell)> = Vec::new();
        let mut nearby_agents: Vec<String> = Vec::new();

        for entry in entries {
            let body = match entry.get("body") {
                Some(b) => b,
                None => continue,
            };
            let kind = body.get("kind").and_then(|v| v.as_str());
            let actor = body.get("actor").and_then(|v| v.as_str());
            match kind {
                Some("agent_entered") | Some("agent_walked") => {
                    if actor == Some(self.agent_did.as_str()) {
                        let pos_arr = body.get("position")
                            .or_else(|| body.get("to"))
                            .and_then(|v| v.as_array());
                        if let Some(arr) = pos_arr {
                            if arr.len() == 3 {
                                position = Some(Cell {
                                    x: arr[0].as_i64().unwrap_or(0),
                                    y: arr[1].as_i64().unwrap_or(0),
                                    z: arr[2].as_i64().unwrap_or(0),
                                });
                            }
                        }
                    }
                }
                Some("plant_added") => {
                    if let (Some(id), Some(arr)) = (
                        body.get("plant_id").and_then(|v| v.as_str()),
                        body.get("position").and_then(|v| v.as_array()),
                    ) {
                        if arr.len() == 3 {
                            plants.push((id.to_string(), Cell {
                                x: arr[0].as_i64().unwrap_or(0),
                                y: arr[1].as_i64().unwrap_or(0),
                                z: arr[2].as_i64().unwrap_or(0),
                            }));
                        }
                    }
                }
                Some("plant_retired") => {
                    if let Some(id) = body.get("plant_id")
                        .and_then(|v| v.as_str())
                    {
                        plants.retain(|(k, _)| k != id);
                    }
                }
                Some("agent_spoke") => {
                    if let Some(heard) = body.get("heard_by")
                        .and_then(|v| v.as_array())
                    {
                        for h in heard {
                            if let Some(hd) = h.as_str() {
                                if hd == self.agent_did
                                    && !nearby_agents.iter().any(
                                        |x| x == hd)
                                {
                                    nearby_agents.push(hd.to_string());
                                }
                            }
                        }
                    }
                }
                _ => {}
            }
        }

        let position = position.ok_or("agent not in garden")?;
        let _ = (&last_action, &last_reward_micros);
        Ok(Observation {
            position,
            last_action,
            last_reward_micros,
            plants,
            nearby_agents,
            garden_size: self.garden_size,
        })
    }

    // ── HTTP primitives ────────────────────────────────────

    fn get(&self, path: &str) -> Result<Value, String> {
        let url = format!("{}{}", self.base_url, path);
        let resp = ureq::get(&url).call()
            .map_err(|e| format!("GET {url}: {e}"))?;
        resp.into_json::<Value>()
            .map_err(|e| format!("parse: {e}"))
    }

    fn post(&self, path: &str, body: &Value) -> Result<Value, String> {
        let url = format!("{}{}", self.base_url, path);
        let resp = ureq::post(&url)
            .send_json(body.clone())
            .map_err(|e| format!("POST {url}: {e}"))?;
        resp.into_json::<Value>()
            .map_err(|e| format!("parse: {e}"))
    }
}
