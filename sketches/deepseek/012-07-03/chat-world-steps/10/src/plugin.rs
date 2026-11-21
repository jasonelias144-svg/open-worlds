use crate::did::{DidKey, Keypair};
use crate::error::{Error, Result};
use crate::home::HomeRoom;
use crate::joined_room::JoinedRoom;
use crate::room::{Room, RoomLog};
use crate::template::RoomTemplate;
use crate::transcript::{sign_transcript, Transcript, TranscriptEntry};
use crate::verify::verify_log;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Deserialize)]
pub struct Request {
    pub id: serde_json::Value,
    pub method: String,
    #[serde(default)]
    pub params: serde_json::Value,
}

#[derive(Debug, Serialize)]
pub struct Response {
    pub id: serde_json::Value,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub result: Option<serde_json::Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<ErrorBody>,
}

#[derive(Debug, Serialize)]
pub struct ErrorBody {
    pub code: String,
    pub message: String,
}

pub struct Plugin {
    user_kp: Keypair,
    home: HomeRoom,
    rooms: HashMap<DidKey, Room>,
    joined: HashMap<DidKey, JoinedRoom>,
    logs: HashMap<DidKey, RoomLog>,
}

impl Plugin {
    pub fn new(user_kp: Keypair, home_kp: Keypair, home_name: &str) -> Result<Self> {
        let home = HomeRoom::create(user_kp.clone(), home_kp, home_name)?;
        Ok(Plugin {
            user_kp,
            home,
            rooms: HashMap::new(),
            joined: HashMap::new(),
            logs: HashMap::new(),
        })
    }

    pub fn user_id(&self) -> DidKey { self.user_kp.did() }
    pub fn home_id(&self) -> DidKey { self.home.room().world_id().clone() }

    pub fn handle(&mut self, req: Request) -> Response {
        let id = req.id.clone();
        match self.dispatch(&req.method, req.params) {
            Ok(v) => Response { id, result: Some(v), error: None },
            Err(e) => Response {
                id,
                result: None,
                error: Some(ErrorBody { code: "error".into(), message: e.to_string() }),
            },
        }
    }

    fn dispatch(&mut self, method: &str, params: serde_json::Value) -> Result<serde_json::Value> {
        use serde_json::json;
        match method {
            "init" => Ok(json!({
                "user_id": self.user_id().as_str(),
                "home_id": self.home_id().as_str(),
            })),
            "create_room" => {
                let template: RoomTemplate = serde_json::from_value(
                    params.get("template").cloned().unwrap_or(serde_json::Value::Null)
                ).map_err(|e| Error::Serialization(format!("template: {e}")))?;
                let room_kp = Keypair::generate();
                let room = Room::create(template, room_kp, &self.user_kp)?;
                let room_id = room.world_id().clone();
                let seed_hash = room.records().first().ok_or_else(|| {
                    Error::Policy("new room has no seed".into())
                })?.hash()?;
                self.rooms.insert(room_id.clone(), room);
                Ok(json!({
                    "room_id": room_id.as_str(),
                    "seed_hash": seed_hash,
                }))
            }
            "post_message" => {
                let room_id = parse_room_id(&params, "room_id")?;
                let text = params.get("text").and_then(|v| v.as_str())
                    .ok_or_else(|| Error::Serialization("missing text".into()))?
                    .to_string();
                let kind = params.get("kind").and_then(|v| v.as_str())
                    .unwrap_or("normal").to_string();
                let user_kp = self.user_kp.clone();
                let room = self.rooms.get_mut(&room_id)
                    .ok_or_else(|| Error::Policy(format!("room not held: {}", room_id.as_str())))?;
                let rec = room.post(&user_kp, &text, &kind)?;
                Ok(json!({
                    "record_hash": rec.hash()?,
                    "record_json": rec,
                }))
            }
            "read_room" => {
                let room_id = parse_room_id(&params, "room_id")?;
                let entries = if let Some(room) = self.lookup_room(&room_id) {
                    room.visible_log()
                } else if let Some(joined) = self.joined.get(&room_id) {
                    joined.visible_log()
                } else if let Some(log) = self.logs.get(&room_id) {
                    log.visible_log()
                } else {
                    return Err(Error::Policy(format!("unknown room: {}", room_id.as_str())));
                };
                Ok(json!({
                    "room_id": room_id.as_str(),
                    "entries": entries,
                }))
            }
            "attest_transcript" => {
                let source_label = params.get("source_label").and_then(|v| v.as_str())
                    .ok_or_else(|| Error::Serialization("missing source_label".into()))?
                    .to_string();
                let entries: Vec<TranscriptEntry> = serde_json::from_value(
                    params.get("entries").cloned().unwrap_or(serde_json::Value::Null)
                ).map_err(|e| Error::Serialization(format!("entries: {e}")))?;
                let t = sign_transcript(&source_label, entries, &self.user_kp)?;
                let t_hash = t.hash()?;
                Ok(json!({
                    "transcript_hash": t_hash,
                    "transcript_json": t,
                }))
            }
            "port_conversation" => {
                let room_id = parse_room_id(&params, "room_id")?;
                let transcript: Transcript = serde_json::from_value(
                    params.get("transcript_json").cloned().unwrap_or(serde_json::Value::Null)
                ).map_err(|e| Error::Serialization(format!("transcript_json: {e}")))?;
                let rec = self.home.port(&transcript, "room", Some(&room_id))?;
                Ok(json!({
                    "port_hash": rec.hash()?,
                    "record_json": rec,
                }))
            }
            "export_room_log" => {
                let room_id = parse_room_id(&params, "room_id")?;
                let log = if let Some(room) = self.lookup_room(&room_id) {
                    room.log()
                } else if let Some(log) = self.logs.get(&room_id) {
                    log.clone()
                } else {
                    return Err(Error::Policy(format!("unknown room: {}", room_id.as_str())));
                };
                Ok(json!({
                    "room_id": room_id.as_str(),
                    "log_json": log,
                }))
            }
            "import_room_log" => {
                let log: RoomLog = serde_json::from_value(
                    params.get("log_json").cloned().unwrap_or(serde_json::Value::Null)
                ).map_err(|e| Error::Serialization(format!("log_json: {e}")))?;
                let room_id = log.world_id.clone();
                self.logs.insert(room_id.clone(), log);
                Ok(json!({
                    "room_id": room_id.as_str(),
                }))
            }
            "verify_room" => {
                let room_id = parse_room_id(&params, "room_id")?;
                if let Some(room) = self.lookup_room(&room_id) {
                    verify_log(&room.log())?;
                } else if let Some(joined) = self.joined.get(&room_id) {
                    verify_log(joined.log())?;
                } else if let Some(log) = self.logs.get(&room_id) {
                    verify_log(log)?;
                } else {
                    return Err(Error::Policy(format!("unknown room: {}", room_id.as_str())));
                }
                Ok(json!({ "ok": true }))
            }
            "join_external_room" => {
                let log: RoomLog = serde_json::from_value(
                    params.get("log_json").cloned().unwrap_or(serde_json::Value::Null)
                ).map_err(|e| Error::Serialization(format!("log_json: {e}")))?;
                let room_id = log.world_id.clone();
                let joined = JoinedRoom::from_log(log, self.user_kp.clone())?;
                self.joined.insert(room_id.clone(), joined);
                Ok(json!({
                    "room_id": room_id.as_str(),
                }))
            }
            "request_join_external" => {
                let room_id = parse_room_id(&params, "room_id")?;
                let tier = params.get("tier").and_then(|v| v.as_str())
                    .unwrap_or("communicate").to_string();
                let is_ai = params.get("is_ai").and_then(|v| v.as_bool())
                    .unwrap_or(false);
                let joined = self.joined.get_mut(&room_id)
                    .ok_or_else(|| Error::Policy(format!("not joined: {}", room_id.as_str())))?;
                let rec = joined.request_join(&tier, is_ai)?;
                Ok(json!({
                    "record_hash": rec.hash()?,
                    "record_json": rec,
                }))
            }
            "post_as_participant" => {
                let room_id = parse_room_id(&params, "room_id")?;
                let text = params.get("text").and_then(|v| v.as_str())
                    .ok_or_else(|| Error::Serialization("missing text".into()))?
                    .to_string();
                let kind = params.get("kind").and_then(|v| v.as_str())
                    .unwrap_or("normal").to_string();
                let joined = self.joined.get_mut(&room_id)
                    .ok_or_else(|| Error::Policy(format!("not joined: {}", room_id.as_str())))?;
                let rec = joined.post(&text, &kind)?;
                Ok(json!({
                    "record_hash": rec.hash()?,
                    "record_json": rec,
                }))
            }
            "export_pending_for" => {
                let room_id = parse_room_id(&params, "room_id")?;
                let joined = self.joined.get(&room_id)
                    .ok_or_else(|| Error::Policy(format!("not joined: {}", room_id.as_str())))?;
                joined.verify_pending()?;
                Ok(json!({
                    "room_id": room_id.as_str(),
                    "pending": joined.export_pending(),
                }))
            }
            "clear_pending_for" => {
                let room_id = parse_room_id(&params, "room_id")?;
                let joined = self.joined.get_mut(&room_id)
                    .ok_or_else(|| Error::Policy(format!("not joined: {}", room_id.as_str())))?;
                joined.clear_pending();
                Ok(json!({ "ok": true }))
            }
            "accept_pending" => {
                let room_id = parse_room_id(&params, "room_id")?;
                let pending: Vec<crate::record::Record> = serde_json::from_value(
                    params.get("pending").cloned().unwrap_or(serde_json::Value::Null)
                ).map_err(|e| Error::Serialization(format!("pending: {e}")))?;
                let room = self.rooms.get_mut(&room_id)
                    .ok_or_else(|| Error::Policy(format!("room not held: {}", room_id.as_str())))?;
                let outcomes = room.accept_pending(&pending)?;
                Ok(json!({
                    "room_id": room_id.as_str(),
                    "outcomes": outcomes,
                }))
            }
            other => Err(Error::Policy(format!("unknown method: {other}"))),
        }
    }

    fn lookup_room(&self, room_id: &DidKey) -> Option<&Room> {
        if room_id == self.home.room().world_id() {
            Some(self.home.room())
        } else {
            self.rooms.get(room_id)
        }
    }
}

fn parse_room_id(params: &serde_json::Value, key: &str) -> Result<DidKey> {
    let s = params.get(key).and_then(|v| v.as_str())
        .ok_or_else(|| Error::Serialization(format!("missing {key}")))?;
    DidKey::parse(s)
}
