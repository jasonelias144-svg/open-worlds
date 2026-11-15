//! The Ur-garden: the Ur-world as a signed microverse garden.
//!
//! A small 3D garden where fractal plants grow, residents walk
//! between them, and the keeper tends it. Composes with
//! `ur-world`'s Cell, `world-log`'s chain, and `formats::proof`.
//!
//! Correspondence to the Python reference (`ur_garden.py`):
//!
//!   Python                        Rust
//!   ────────────────────────────  ────────────────────────────
//!   Cell(x, y)                    ur_world::Cell { x, y, z }
//!   Plant.position: Cell          Plant.position: Cell
//!   GardenWorld._log: List[Dict]  Garden.log: Vec<Entry>
//!   GardenWorld.world_kp          Garden.curator: SigningKey
//!   GardenAdapter                 impl Mind for GardenResident
//!   garden.walk/observe/speak     GardenAction::{Walk,Observe,Speak}
//!   Plant (FractalHost)           Plant (hosts a Fractal)
//!
//! Rust-specific:
//!   - Cell is 3D. The Python reference used 2D for clarity;
//!     Rust uses 3D to match ur-world's actual geometry.
//!   - Every log entry is a `formats::proof` signed record.
//!     The chain uses `world-log`'s `prev`/`hash` discipline.
//!   - The `Mind` trait drives residents. A `ScriptedMind` ships
//!     here; the tiny RNN lives in a future crate or module.

use std::collections::{HashMap, HashSet};

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};

use crate::world::{Cell, World};
use formats::proof::{Proof, SigningKey, VerifyingKey};

// ────────────────────────────────────────────────────────────
// Errors
// ────────────────────────────────────────────────────────────

#[derive(Debug)]
pub enum GardenError {
    SignatureInvalid,
    ChainBroken { at: usize },
    UnknownPlant(String),
    PositionOutOfBounds(Cell),
    PositionOccupied(Cell),
    Refused(String),
    UnknownAct(String),
}

// ────────────────────────────────────────────────────────────
// Plant kinds and events
// ────────────────────────────────────────────────────────────

/// What kind of fractal a plant is.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum PlantKind {
    /// Barnsley fern, chaos game.
    Fern,
    /// Sierpinski gasket, chaos game.
    Tree,
    /// Rule 30 elementary CA.
    Vine,
}

/// A single plant event — a fact about how the fractal grew.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlantEvent {
    /// SHA-256 of the canonical event body, hex.
    pub hash: String,
    /// `"chaos_step"` or `"ca_row"`.
    pub kind: &'static str,
    /// Kind-specific payload.
    pub data: EventData,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "shape")]
pub enum EventData {
    ChaosStep { point: [i64; 3] },
    CaRow { cells: Vec<i32> },
}

// ────────────────────────────────────────────────────────────
// Fractal primitives (minimal, deterministic)
// ────────────────────────────────────────────────────────────

/// Xorshift64* — deterministic, no floats.
struct XorShift64(u64);

impl XorShift64 {
    fn next(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.0 = x;
        x.wrapping_mul(0x2545F4914F6CDD1D)
    }
    fn pick(&mut self, n: u64) -> u64 { self.next() % n }
}

/// Barnsley fern step (simplified): pick transform by weight,
/// apply in fixed-point.
fn barnsley_step(p: [i64; 3], rng: &mut XorShift64) -> [i64; 3] {
    // (a,b,c,d,e,f,denom,weight) — classic Barnsley coefficients
    // scaled by 1000 for integer math. Four transforms, weighted
    // 1:7:7:85.
    const T: [[i64; 8]; 4] = [
        [0, 0, 0, 0, 160, 0, 1000, 1],
        [200, -260, 0, 230, 220, 1_600_000, 1000, 7],
        [-150, 280, 0, 260, 240, 440_000, 1000, 7],
        [850, 40, 0, -40, 850, 1_600_000, 1000, 85],
    ];
    let pick = rng.pick(100);
    let t = if pick < 1 { &T[0] }
        else if pick < 8 { &T[1] }
        else if pick < 15 { &T[2] }
        else { &T[3] };
    let nx = (t[0] * p[0] + t[1] * p[1] + t[2]) / t[6];
    let ny = (t[3] * p[0] + t[4] * p[1] + t[5]) / t[6];
    [nx, ny, p[2]]
}

/// Sierpinski triangle step (midpoint to one of 3 vertices).
fn sierpinski_step(p: [i64; 3], rng: &mut XorShift64) -> [i64; 3] {
    // Vertices: (0,0), (1000,0), (500,866). Scale 1000.
    let v = rng.pick(3);
    let (vx, vy) = match v {
        0 => (0, 0),
        1 => (1000, 0),
        _ => (500, 866),
    };
    [(p[0] + vx) / 2, (p[1] + vy) / 2, p[2]]
}

/// One generation of a Wolfram elementary CA (rule encoded in a u8).
fn step_elementary_ca(cells: &[i32], rule: u8) -> Vec<i32> {
    if cells.is_empty() {
        return vec![];
    }
    let mut next = vec![0; cells.len() + 2];
    // Pad by 1 on each side (implicit 0 boundary)
    let padded: Vec<i32> = [vec![0], cells.to_vec(), vec![0]].concat();
    for i in 1..padded.len() - 1 {
        let n = (padded[i - 1] << 2) | (padded[i] << 1) | padded[i + 1];
        let bit = (rule >> (7 - n)) & 1;
        next[i - 1] = bit as i32;
    }
    next
}

// ────────────────────────────────────────────────────────────
// Plant
// ────────────────────────────────────────────────────────────

/// A hosted fractal plant.
pub struct Plant {
    pub id: String,
    pub kind: PlantKind,
    pub position: Cell,
    pub description: String,
    events: Vec<PlantEvent>,
    state: PlantState,
}

enum PlantState {
    Fern { p: [i64; 3], rng: XorShift64 },
    Tree { p: [i64; 3], rng: XorShift64 },
    Vine { cells: Vec<i32>, rule: u8 },
}

impl Plant {
    pub fn new(id: String, kind: PlantKind, position: Cell, seed: u64) -> Self {
        let state = match kind {
            PlantKind::Fern => PlantState::Fern { p: [500, 500, 0], rng: XorShift64(seed | 1) },
            PlantKind::Tree => PlantState::Tree { p: [500, 500, 0], rng: XorShift64(seed | 1) },
            PlantKind::Vine => PlantState::Vine { cells: vec![1], rule: 30 },
        };
        Self {
            id,
            kind,
            position,
            description: String::new(),
            events: Vec::new(),
            state,
        }
    }

    /// Advance the fractal by `steps`. Returns references to the
    /// new events (not to old ones).
    pub fn advance(&mut self, steps: usize) -> Vec<&PlantEvent> {
        let start = self.events.len();
        for _ in 0..steps {
            self.events.push(self.step_and_capture());
        }
        self.events[start..].iter().collect()
    }

    fn step_and_capture(&mut self) -> PlantEvent {
        match &mut self.state {
            PlantState::Fern { p, rng } => {
                *p = barnsley_step(*p, rng);
                let body = json!({"kind":"fern_step","point": p});
                let h = sha256_hex(&serde_jcs::to_vec(&body).unwrap());
                PlantEvent {
                    hash: h,
                    kind: "chaos_step",
                    data: EventData::ChaosStep { point: *p },
                }
            }
            PlantState::Tree { p, rng } => {
                *p = sierpinski_step(*p, rng);
                let body = json!({"kind":"tree_step","point": p});
                let h = sha256_hex(&serde_jcs::to_vec(&body).unwrap());
                PlantEvent {
                    hash: h,
                    kind: "chaos_step",
                    data: EventData::ChaosStep { point: *p },
                }
            }
            PlantState::Vine { cells, rule } => {
                *cells = step_elementary_ca(cells, *rule);
                let body = json!({"kind":"vine_row","cells": cells});
                let h = sha256_hex(&serde_jcs::to_vec(&body).unwrap());
                PlantEvent {
                    hash: h,
                    kind: "ca_row",
                    data: EventData::CaRow { cells: cells.clone() },
                }
            }
        }
    }

    pub fn events(&self) -> &[PlantEvent] { &self.events }
}

// ────────────────────────────────────────────────────────────
// Garden actions
// ────────────────────────────────────────────────────────────

/// A resident's act. Maps to `Mind::Action` for garden residents.
#[derive(Debug, Clone)]
pub enum GardenAction {
    Enter { at: Cell },
    Walk { direction: Direction },
    Observe,
    Speak { text: String },
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Direction { North, South, East, West }

impl Direction {
    fn delta(self) -> (i64, i64, i64) {
        match self {
            Direction::North => (0, -1, 0),
            Direction::South => (0, 1, 0),
            Direction::East => (1, 0, 0),
            Direction::West => (-1, 0, 0),
        }
    }
}

/// A keeper's act. Signed by the garden's curator key.
#[derive(Debug, Clone)]
pub enum KeeperAction {
    PlantAdded { plant: Plant },
    PlantRetired { plant_id: String, reason: String },
    CycleAdvanced { cycle: u64, plant_event_hashes: Vec<String> },
}

// ────────────────────────────────────────────────────────────
// Log entries
// ────────────────────────────────────────────────────────────

/// A signed entry. `body` is the factual record; `proof` is the
/// W3C DataIntegrityProof over the JCS canonical form of `body`.
/// `prev` and `hash` implement the `world-log` chain.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Entry {
    pub body: Value,
    pub proof: Proof,
    pub prev: Option<String>,
    pub hash: String,
}

/// What kind of entry `body` describes.
#[derive(Debug, Clone, Copy)]
pub enum EntryKind {
    Admission,
    AgentEntered,
    AgentWalked,
    AgentObserved,
    AgentSpoke,
    PlantAdded,
    PlantRetired,
    CycleAdvanced,
}

// ────────────────────────────────────────────────────────────
// The Garden
// ────────────────────────────────────────────────────────────

pub struct Garden {
    pub world: World,
    pub log: Vec<Entry>,
    pub plants_active: HashMap<String, Plant>,
    pub plants_all: HashMap<String, Plant>,
    pub agent_positions: HashMap<String, Cell>,
    pub agent_visited: HashMap<String, HashSet<(i64, i64, i64)>>,
    pub admitted: HashMap<String, String>,
    pub cycle: u64,
    pub description: String,
    pub curator_key: SigningKey,
    pub curator_did: String,
    pub width: i64,
    pub height: i64,
    pub depth: i64,
}

impl Garden {
    /// Create a new garden. `curator_key` signs every entry.
    pub fn new(
        world: World,
        description: String,
        curator_key: SigningKey,
        width: i64,
        height: i64,
        depth: i64,
    ) -> Self {
        let curator_did = curator_key.did();
        Self {
            world,
            log: Vec::new(),
            plants_active: HashMap::new(),
            plants_all: HashMap::new(),
            agent_positions: HashMap::new(),
            agent_visited: HashMap::new(),
            admitted: HashMap::new(),
            cycle: 0,
            description,
            curator_key,
            curator_did,
            width,
            height,
            depth,
        }
    }

    // ── Log primitives ──────────────────────────────────────

    fn append(&mut self, body: Value) -> Result<&Entry, GardenError> {
        let prev = self.log.last().map(|e| e.hash.clone());
        let jcs = serde_jcs::to_vec(&body)
            .map_err(|_| GardenError::ChainBroken { at: self.log.len() })?;
        let hash = sha256_hex(&jcs);
        let proof = formats::proof::sign(
            formats::proof::Suite::EddsaJcs2022,
            &self.curator_key,
            &body,
        )
        .map_err(|_| GardenError::SignatureInvalid)?;
        self.log.push(Entry {
            body,
            proof,
            prev,
            hash,
        });
        Ok(self.log.last().unwrap())
    }

    // ── Keeper acts ─────────────────────────────────────────

    pub fn add_plant(
        &mut self,
        id: String,
        kind: PlantKind,
        position: Cell,
        seed: u64,
    ) -> Result<(), GardenError> {
        if !self.in_bounds(position) {
            return Err(GardenError::PositionOutOfBounds(position));
        }
        if self.plant_at(position).is_some() {
            return Err(GardenError::PositionOccupied(position));
        }
        if self.plants_all.contains_key(&id) {
            return Err(GardenError::Refused(
                format!("plant {} already exists", id),
            ));
        }
        let plant = Plant::new(id.clone(), kind, position, seed);
        self.plants_active.insert(id.clone(), Plant::new(id.clone(), kind, position, seed));
        self.plants_all.insert(id.clone(), plant);
        self.append(json!({
            "kind": "plant_added",
            "actor": self.curator_did,
            "plant_id": id,
            "plant_kind": kind,
            "position": [position.x, position.y, position.z],
            "ts": now_iso8601(),
        }))?;
        Ok(())
    }

    pub fn retire_plant(
        &mut self,
        id: &str,
        reason: &str,
    ) -> Result<(), GardenError> {
        let plant = self.plants_active.remove(id)
            .ok_or_else(|| GardenError::UnknownPlant(id.to_string()))?;
        self.append(json!({
            "kind": "plant_retired",
            "actor": self.curator_did,
            "plant_id": id,
            "position": [plant.position.x, plant.position.y, plant.position.z],
            "reason": reason,
            "ts": now_iso8601(),
        }))?;
        Ok(())
    }

    pub fn advance_cycle(&mut self, steps: usize) -> Result<(), GardenError> {
        self.cycle += 1;
        let mut hashes = Vec::new();
        for plant in self.plants_active.values_mut() {
            for ev in plant.advance(steps) {
                hashes.push(ev.hash.clone());
            }
        }
        self.append(json!({
            "kind": "cycle_advanced",
            "actor": self.curator_did,
            "cycle": self.cycle,
            "plant_event_hashes": hashes,
            "ts": now_iso8601(),
        }))?;
        Ok(())
    }

    // ── Agent acts ──────────────────────────────────────────

    pub fn admit(
        &mut self,
        agent_did: &str,
        name: &str,
    ) -> Result<(), GardenError> {
        if self.admitted.contains_key(agent_did) {
            return Err(GardenError::Refused("already admitted".into()));
        }
        self.admitted.insert(agent_did.to_string(), name.to_string());
        self.append(json!({
            "kind": "admission",
            "actor": agent_did,
            "name": name,
            "ts": now_iso8601(),
        }))?;
        Ok(())
    }

    pub fn apply_action(
        &mut self,
        agent_did: &str,
        action: GardenAction,
    ) -> Result<(), GardenError> {
        if !self.admitted.contains_key(agent_did) {
            return Err(GardenError::Refused("not admitted".into()));
        }
        match action {
            GardenAction::Enter { at } => self.handle_enter(agent_did, at),
            GardenAction::Walk { direction } => self.handle_walk(agent_did, direction),
            GardenAction::Observe => self.handle_observe(agent_did),
            GardenAction::Speak { text } => self.handle_speak(agent_did, text),
        }
    }

    fn handle_enter(&mut self, agent_did: &str, at: Cell) -> Result<(), GardenError> {
        if !self.in_bounds(at) {
            return Err(GardenError::PositionOutOfBounds(at));
        }
        if self.plant_at(at).is_some() {
            return Err(GardenError::PositionOccupied(at));
        }
        self.agent_positions.insert(agent_did.to_string(), at);
        self.agent_visited
            .entry(agent_did.to_string())
            .or_default()
            .insert((at.x, at.y, at.z));
        self.append(json!({
            "kind": "agent_entered",
            "actor": agent_did,
            "position": [at.x, at.y, at.z],
            "ts": now_iso8601(),
        }))?;
        Ok(())
    }

    fn handle_walk(&mut self, agent_did: &str, dir: Direction) -> Result<(), GardenError> {
        let pos = self.agent_positions.get(agent_did).copied()
            .ok_or_else(|| GardenError::Refused("not in garden".into()))?;
        let (dx, dy, dz) = dir.delta();
        let next = Cell { x: pos.x + dx, y: pos.y + dy, z: pos.z + dz };
        if !self.in_bounds(next) {
            return Err(GardenError::PositionOutOfBounds(next));
        }
        if self.plant_at(next).is_some() {
            return Err(GardenError::PositionOccupied(next));
        }
        self.agent_positions.insert(agent_did.to_string(), next);
        self.agent_visited
            .entry(agent_did.to_string())
            .or_default()
            .insert((next.x, next.y, next.z));
        self.append(json!({
            "kind": "agent_walked",
            "actor": agent_did,
            "from": [pos.x, pos.y, pos.z],
            "to": [next.x, next.y, next.z],
            "direction": match dir {
                Direction::North => "N",
                Direction::South => "S",
                Direction::East => "E",
                Direction::West => "W",
            },
            "ts": now_iso8601(),
        }))?;
        Ok(())
    }

    fn handle_observe(&mut self, agent_did: &str) -> Result<(), GardenError> {
        let pos = self.agent_positions.get(agent_did).copied()
            .ok_or_else(|| GardenError::Refused("not in garden".into()))?;
        let adjacent: Vec<&Plant> = self.plants_active.values()
            .filter(|p| p.position.is_adjacent(&pos))
            .collect();
        if adjacent.is_empty() {
            self.append(json!({
                "kind": "agent_observed",
                "actor": agent_did,
                "position": [pos.x, pos.y, pos.z],
                "result": "nothing_adjacent",
                "ts": now_iso8601(),
            }))?;
            return Ok(());
        }
        let plant = adjacent[0];
        let events = plant.events();
        if events.is_empty() {
            return Err(GardenError::Refused("plant has no events".into()));
        }
        let latest = &events[events.len() - 1];
        let (plant_id, ev_hash, ev_kind) = (
            plant.id.clone(),
            latest.hash.clone(),
            latest.kind,
        );
        self.append(json!({
            "kind": "agent_observed",
            "actor": agent_did,
            "position": [pos.x, pos.y, pos.z],
            "result": "observed_plant",
            "plant_id": plant_id,
            "plant_event_hash": ev_hash,
            "plant_event_kind": ev_kind,
            "ts": now_iso8601(),
        }))?;
        Ok(())
    }

    fn handle_speak(&mut self, agent_did: &str, text: String) -> Result<(), GardenError> {
        if text.trim().is_empty() {
            return Err(GardenError::Refused("text required".into()));
        }
        let pos = self.agent_positions.get(agent_did).copied()
            .ok_or_else(|| GardenError::Refused("not in garden".into()))?;
        let heard: Vec<String> = self.agent_positions.iter()
            .filter(|(aid, p)| {
                aid.as_str() != agent_did
                    && p.distance(&pos) <= 2
            })
            .map(|(aid, _)| aid.clone())
            .collect();
        self.append(json!({
            "kind": "agent_spoke",
            "actor": agent_did,
            "position": [pos.x, pos.y, pos.z],
            "heard_by": heard,
            "text": text,
            "ts": now_iso8601(),
        }))?;
        Ok(())
    }

    // ── Helpers ─────────────────────────────────────────────

    fn in_bounds(&self, c: Cell) -> bool {
        c.x >= 0 && c.x < self.width
            && c.y >= 0 && c.y < self.height
            && c.z >= 0 && c.z < self.depth
    }

    pub fn plant_at(&self, c: Cell) -> Option<&Plant> {
        self.plants_active.values().find(|p| p.position == c)
    }

    // ── Verification ────────────────────────────────────────

    /// Verify the chain: `prev` links match, `hash` matches
    /// JCS(body), and every entry's proof verifies against the
    /// actor's key (which, in v0.1, is the curator for keeper
    /// entries and the agent for agent entries).
    pub fn verify_log(&self) -> Result<(), GardenError> {
        let mut prev: Option<String> = None;
        for (i, entry) in self.log.iter().enumerate() {
            if entry.prev != prev {
                return Err(GardenError::ChainBroken { at: i });
            }
            let jcs = serde_jcs::to_vec(&entry.body)
                .map_err(|_| GardenError::ChainBroken { at: i })?;
            let hash = sha256_hex(&jcs);
            if entry.hash != hash {
                return Err(GardenError::ChainBroken { at: i });
            }
            let actor_did = entry.body.get("actor")
                .and_then(|v| v.as_str())
                .ok_or(GardenError::SignatureInvalid)?;
            let vk = VerifyingKey::from_did(actor_did)
                .map_err(|_| GardenError::SignatureInvalid)?;
            formats::proof::verify(
                formats::proof::Suite::EddsaJcs2022,
                &entry.proof,
                &entry.body,
                &vk,
            ).map_err(|_| GardenError::SignatureInvalid)?;
            prev = Some(entry.hash.clone());
        }
        Ok(())
    }

    /// Verify that every `agent_observed` entry references a real
    /// plant event.
    pub fn verify_cross_references(&self) -> Result<(), GardenError> {
        for (i, entry) in self.log.iter().enumerate() {
            let kind = entry.body.get("kind").and_then(|v| v.as_str());
            if kind != Some("agent_observed") {
                continue;
            }
            if entry.body.get("result").and_then(|v| v.as_str())
                != Some("observed_plant")
            {
                continue;
            }
            let plant_id = entry.body.get("plant_id")
                .and_then(|v| v.as_str())
                .ok_or(GardenError::ChainBroken { at: i })?;
            let target_hash = entry.body.get("plant_event_hash")
                .and_then(|v| v.as_str())
                .ok_or(GardenError::ChainBroken { at: i })?;
            let plant = self.plants_all.get(plant_id)
                .ok_or_else(|| GardenError::UnknownPlant(plant_id.to_string()))?;
            let found = plant.events().iter()
                .any(|ev| ev.hash == target_hash);
            if !found {
                return Err(GardenError::ChainBroken { at: i });
            }
        }
        Ok(())
    }
}

// ────────────────────────────────────────────────────────────
// Cell helper extension (if `ur-world`'s Cell doesn't have these)
// ────────────────────────────────────────────────────────────

trait CellOps {
    fn is_adjacent(&self, other: &Cell) -> bool;
    fn distance(&self, other: &Cell) -> i64;
}

impl CellOps for Cell {
    fn is_adjacent(&self, other: &Cell) -> bool {
        (self.x - other.x).abs()
            + (self.y - other.y).abs()
            + (self.z - other.z).abs() == 1
    }
    fn distance(&self, other: &Cell) -> i64 {
        (self.x - other.x).abs()
            + (self.y - other.y).abs()
            + (self.z - other.z).abs()
    }
}

// ────────────────────────────────────────────────────────────
// Small utilities
// ────────────────────────────────────────────────────────────

fn sha256_hex(bytes: &[u8]) -> String {
    use sha2::{Digest, Sha256};
    let mut h = Sha256::new();
    h.update(bytes);
    hex_encode(&h.finalize())
}

fn hex_encode(bytes: &[u8]) -> String {
    const H: &[u8] = b"0123456789abcdef";
    let mut s = String::with_capacity(bytes.len() * 2);
    for &b in bytes {
        s.push(H[(b >> 4) as usize] as char);
        s.push(H[(b & 0xf) as usize] as char);
    }
    s
}

fn now_iso8601() -> String {
    // Replace with `time` or `chrono` when integrating.
    // Placeholder for the module to be reviewed.
    "2026-11-15T00:00:00Z".to_string()
}
