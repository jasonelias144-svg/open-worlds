//! GardenServer — the garden as a WCP world.
//!
//! Endpoints:
//!   GET  /manifest        signed manifest JSON
//!   GET  /log             unsigned chain (body + prev + hash)
//!   GET  /signed-log      full entries (body + proof + prev + hash)
//!   GET  /lobby           signed lobby view
//!   GET  /plants          current plant map
//!   POST /petition        admission request
//!   POST /act             agent action
//!   POST /advance_cycle   keeper-only; requires keeper-signed body
//!
//! The garden is behind `Arc<Mutex<Garden>>`. Every request
//! takes a short lock. Fine for the garden's size.

use std::io::Read;
use std::sync::{Arc, Mutex};
use std::thread;

use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use tiny_http::{Header, Method, Response, Server, StatusCode};

use crate::garden::{
    Direction, Garden, GardenAction, GardenError, PlantKind,
};
use crate::garden::rnn::XorShift64;
use crate::world::Cell;
use formats::proof::{sign, Suite, VerifyingKey};

// ────────────────────────────────────────────────────────────
// Server
// ────────────────────────────────────────────────────────────

pub struct GardenServer {
    pub garden: Arc<Mutex<Garden>>,
    pub keeper_did: String,
    pub world_url: String,
    pub name: String,
    pub description: String,
}

impl GardenServer {
    pub fn new(
        garden: Arc<Mutex<Garden>>,
        keeper_did: String,
        world_url: String,
        name: String,
        description: String,
    ) -> Self {
        Self { garden, keeper_did, world_url, name, description }
    }

    /// Blocking serve loop. Spawns one thread per connection.
    pub fn run(self, addr: &str) -> std::io::Result<()> {
        let server = Server::http(addr)
            .map_err(|e| std::io::Error::new(
                std::io::ErrorKind::AddrInUse,
                format!("bind: {e}")))?;
        let this = Arc::new(self);
        for request in server.incoming_requests() {
            let this = this.clone();
            thread::spawn(move || {
                if let Err(e) = this.handle(request) {
                    eprintln!("request error: {e}");
                }
            });
        }
        Ok(())
    }

    fn handle(&self, mut req: tiny_http::Request) -> std::io::Result<()> {
        let method = req.method().clone();
        let url = req.url().to_string();
        let (path, _qs) = url.split_once('?').unwrap_or((&url, ""));

        let response = match (method, path) {
            (Method::Get, "/manifest") => self.get_manifest(),
            (Method::Get, "/log") => self.get_log(/*signed=*/false),
            (Method::Get, "/signed-log") => self.get_log(/*signed=*/true),
            (Method::Get, "/lobby") => self.get_lobby(),
            (Method::Get, "/plants") => self.get_plants(),
            (Method::Post, "/petition") => self.post_petition(&mut req),
            (Method::Post, "/act") => self.post_act(&mut req),
            (Method::Post, "/advance_cycle") =>
                self.post_advance_cycle(&mut req),
            _ => Ok(json_error(StatusCode(404), "not found")),
        }?;
        req.respond(response).map_err(|e|
            std::io::Error::other(format!("respond: {e}")))
    }

    // ── Handlers ────────────────────────────────────────────

    fn get_manifest(&self) -> Result<Response<std::io::Cursor<Vec<u8>>>, std::io::Error> {
        let g = self.garden.lock().unwrap();
        let body = json!({
            "entity_id": g.world.entity_id,
            "name": self.name,
            "protocol_version": "WCP/0.2",
            "law_url": format!("garden://{}/law", g.world.entity_id),
            "act_endpoint": format!("{}/act", self.world_url),
            "log_endpoint": format!("{}/log", self.world_url),
            "sub_registry_endpoint": format!("{}/plants", self.world_url),
        });
        let sig = sign(Suite::EddsaJcs2022, &g.curator_key, &body)
            .map_err(|_| std::io::Error::other("sign"))?;
        Ok(json_ok(&json!({
            "manifest": body,
            "proof": sig,
        })))
    }

    fn get_log(&self, signed: bool) -> Result<Response<std::io::Cursor<Vec<u8>>>, std::io::Error> {
        let g = self.garden.lock().unwrap();
        let entries: Vec<Value> = if signed {
            g.log.iter()
                .map(|e| json!({
                    "body": e.body,
                    "proof": e.proof,
                    "prev": e.prev,
                    "hash": e.hash,
                }))
                .collect()
        } else {
            g.log.iter()
                .map(|e| json!({
                    "body": e.body,
                    "prev": e.prev,
                    "hash": e.hash,
                }))
                .collect()
        };
        Ok(json_ok(&json!({ "entries": entries })))
    }

    fn get_plants(&self) -> Result<Response<std::io::Cursor<Vec<u8>>>, std::io::Error> {
        let g = self.garden.lock().unwrap();
        let plants: Vec<Value> = g.plants_active.iter()
            .map(|(id, p)| json!({
                "plant_id": id,
                "kind": format!("{:?}", p.kind).to_lowercase(),
                "position": [p.position.x, p.position.y, p.position.z],
                "event_count": p.events().len(),
            }))
            .collect();
        Ok(json_ok(&json!({ "plants": plants })))
    }

    fn get_lobby(&self) -> Result<Response<std::io::Cursor<Vec<u8>>>, std::io::Error> {
        let g = self.garden.lock().unwrap();
        let body = compute_lobby(&g, &self.world_url, &self.name, &self.description);
        let sig = sign(Suite::EddsaJcs2022, &g.curator_key, &body)
            .map_err(|_| std::io::Error::other("sign"))?;
        let mut out = body.as_object().cloned().unwrap_or_default();
        out.insert("sig".into(), json!(sig));
        Ok(json_ok(&Value::Object(out)))
    }

    fn post_petition(&self, req: &mut tiny_http::Request)
        -> Result<Response<std::io::Cursor<Vec<u8>>>, std::io::Error>
    {
        let mut body = String::new();
        req.as_reader().read_to_string(&mut body)?;
        let payload: Value = match serde_json::from_str(&body) {
            Ok(v) => v,
            Err(_) => return Ok(json_error(StatusCode(400), "malformed")),
        };
        let token = payload.get("petitioner_token").and_then(|v| v.as_str());
        let name = payload.get("petitioner_name").and_then(|v| v.as_str());
        let (token, name) = match (token, name) {
            (Some(t), Some(n)) => (t, n),
            _ => return Ok(json_error(StatusCode(400),
                "petitioner_token and petitioner_name required")),
        };
        let mut g = self.garden.lock().unwrap();
        match g.admit(token, name) {
            Ok(()) => Ok(json_ok(&json!({"kind": "admission"}))),
            Err(GardenError::Refused(r)) =>
                Ok(json_refusal(&r)),
            Err(e) =>
                Ok(json_error(StatusCode(500),
                    &format!("admit: {:?}", e))),
        }
    }

    fn post_act(&self, req: &mut tiny_http::Request)
        -> Result<Response<std::io::Cursor<Vec<u8>>>, std::io::Error>
    {
        let mut body = String::new();
        req.as_reader().read_to_string(&mut body)?;
        let payload: Value = match serde_json::from_str(&body) {
            Ok(v) => v,
            Err(_) => return Ok(json_error(StatusCode(400), "malformed")),
        };
        let actor = payload.get("actor_token").and_then(|v| v.as_str());
        let act_type = payload.get("type").and_then(|v| v.as_str());
        let act_payload = payload.get("payload").cloned()
            .unwrap_or_else(|| json!({}));
        let (actor, act_type) = match (actor, act_type) {
            (Some(a), Some(t)) => (a, t),
            _ => return Ok(json_error(StatusCode(400),
                "actor_token and type required")),
        };

        let action = match parse_action(act_type, &act_payload) {
            Some(a) => a,
            None => return Ok(json_refusal(&format!(
                "unknown act type {act_type}"))),
        };

        let mut g = self.garden.lock().unwrap();
        match g.apply_action(actor, action) {
            Ok(()) => Ok(json_ok(&json!({"kind": "ack"}))),
            Err(GardenError::Refused(r)) => Ok(json_refusal(&r)),
            Err(GardenError::PositionOutOfBounds(c)) =>
                Ok(json_refusal(&format!("out of bounds: {:?}", c))),
            Err(GardenError::PositionOccupied(c)) =>
                Ok(json_refusal(&format!("occupied: {:?}", c))),
            Err(e) =>
                Ok(json_error(StatusCode(500),
                    &format!("act: {:?}", e))),
        }
    }

    fn post_advance_cycle(&self, req: &mut tiny_http::Request)
        -> Result<Response<std::io::Cursor<Vec<u8>>>, std::io::Error>
    {
        let mut body = String::new();
        req.as_reader().read_to_string(&mut body)?;
        let payload: Value = match serde_json::from_str(&body) {
            Ok(v) => v,
            Err(_) => return Ok(json_error(StatusCode(400), "malformed")),
        };
        let signer_did = payload.get("keeper_did").and_then(|v| v.as_str());
        let proof_val = payload.get("proof");
        let steps = payload.get("steps").and_then(|v| v.as_u64())
            .unwrap_or(1) as usize;
        let body_to_verify = json!({"kind": "advance_cycle", "steps": steps});
        let (signer_did, proof_val) = match (signer_did, proof_val) {
            (Some(s), Some(p)) => (s, p),
            _ => return Ok(json_error(StatusCode(400),
                "keeper_did and proof required")),
        };
        let proof: formats::proof::DataIntegrityProof =
            match serde_json::from_value(proof_val.clone()) {
                Ok(p) => p,
                Err(_) => return Ok(json_error(StatusCode(400),
                    "malformed proof")),
            };
        let vk = VerifyingKey::from_did(signer_did).map_err(|_|
            std::io::Error::other("bad did"))?;
        if formats::proof::verify(
            Suite::EddsaJcs2022, &proof, &body_to_verify, &vk,
        ).is_err() {
            return Ok(json_error(StatusCode(401),
                "proof does not verify"));
        }
        let mut g = self.garden.lock().unwrap();
        if signer_did != g.curator_did {
            return Ok(json_error(StatusCode(403),
                "signer is not the keeper"));
        }
        if let Err(e) = g.advance_cycle(steps) {
            return Ok(json_error(StatusCode(500),
                &format!("advance: {:?}", e)));
        }
        Ok(json_ok(&json!({"kind": "ack", "cycle": g.cycle})))
    }
}

// ────────────────────────────────────────────────────────────
// Lobby view
// ────────────────────────────────────────────────────────────

fn compute_lobby(
    g: &Garden, world_url: &str, name: &str, description: &str,
) -> Value {
    let total = g.log.len();
    let recent_from: usize = total.saturating_sub(20);
    let recent: Vec<&crate::garden::Entry> = g.log[recent_from..].iter().collect();

    // distinct actors from the last 20 entries
    let mut actors: Vec<String> = Vec::new();
    for e in recent.iter().rev() {
        if let Some(a) = e.body.get("actor").and_then(|v| v.as_str()) {
            if !actors.iter().any(|x| x == a) {
                actors.push(a.to_string());
                if actors.len() >= 8 { break; }
            }
        }
    }

    let recent_events: Vec<Value> = recent.iter().rev().take(6)
        .map(|e| json!({
            "kind": e.body.get("kind"),
            "actor": e.body.get("actor"),
            "tick": e.body.get("tick"),
        }))
        .collect();

    let plants_active_count = g.plants_active.len();
    let agents_count = g.agent_positions.len();
    let admitted_count = g.admitted.len();

    let body = json!({
        "kind": "lobby_view",
        "world_id": g.world.entity_id,
        "name": name,
        "description": description,
        "world_signer": g.curator_did,
        "live": {
            "log_entries_total": total,
            "recent_actors": actors,
            "recent_events": recent_events,
            "summary": {
                "cycle": g.cycle,
                "plants_active": plants_active_count,
                "agents_present": agents_count,
                "agents_admitted": admitted_count,
            },
        },
        "navigation": {
            "subworlds": [],
            "siblings": [],
            "back_to_map": null,
        },
        "entry": {
            "manifest_url": format!("{world_url}/manifest"),
            "petition_url": format!("{world_url}/petition"),
            "act_url": format!("{world_url}/act"),
            "log_url": format!("{world_url}/log"),
            "signed_log_url": format!("{world_url}/signed-log"),
        },
        "ts": iso8601_now(),
    });
    body
}

// ────────────────────────────────────────────────────────────
// Helpers
// ────────────────────────────────────────────────────────────

fn parse_action(act_type: &str, payload: &Value) -> Option<GardenAction> {
    match act_type {
        "garden.walk" => {
            if let Some(start) = payload.get("start") {
                let arr = start.as_array()?;
                if arr.len() != 3 { return None; }
                return Some(GardenAction::Enter {
                    at: Cell {
                        x: arr[0].as_i64()?,
                        y: arr[1].as_i64()?,
                        z: arr[2].as_i64()?,
                    },
                });
            }
            let dir_str = payload.get("direction")?.as_str()?;
            let direction = match dir_str {
                "N" => Direction::North,
                "S" => Direction::South,
                "E" => Direction::East,
                "W" => Direction::West,
                _ => return None,
            };
            Some(GardenAction::Walk { direction })
        }
        "garden.observe" => Some(GardenAction::Observe),
        "garden.speak" => {
            let text = payload.get("text")?.as_str()?.to_string();
            Some(GardenAction::Speak { text })
        }
        _ => None,
    }
}

fn json_ok(payload: &Value) -> Response<std::io::Cursor<Vec<u8>>> {
    let s = serde_json::to_string(payload)
        .unwrap_or_else(|_| "{}".into());
    Response::from_string(s).with_header(
        Header::from_bytes(b"Content-Type", b"application/json")
            .unwrap())
}

fn json_error(status: StatusCode, msg: &str)
    -> Response<std::io::Cursor<Vec<u8>>>
{
    let s = serde_json::to_string(&json!({
        "error": msg,
    })).unwrap_or_else(|_| "{}".into());
    Response::from_string(s)
        .with_status_code(status)
        .with_header(Header::from_bytes(
            b"Content-Type", b"application/json").unwrap())
}

fn json_refusal(reason: &str) -> Response<std::io::Cursor<Vec<u8>>> {
    json_ok(&json!({"kind": "refusal", "reason": reason}))
}

fn iso8601_now() -> String {
    // Replace with `time` or `chrono` on integration.
    "2026-11-15T00:00:00Z".to_string()
}
