use crate::did::{DidKey, Keypair};
use crate::error::{Error, Result};
use crate::record::*;
use crate::room::Room;
use crate::template::RoomTemplate;
use crate::transcript::{verify_transcript, Transcript};

pub struct HomeRoom {
    room: Room,
    user_kp: Keypair,
}

impl HomeRoom {
    /// Create a home. The user is the creator and the only member;
    /// the room has its own key (`room_kp`), which an app should
    /// persist so the home's identity survives restarts.
    pub fn create(user_kp: Keypair, room_kp: Keypair, display_name: &str) -> Result<Self> {
        let template = RoomTemplate::personal_home(display_name);
        let room = Room::create(template, room_kp, &user_kp)?;
        Ok(HomeRoom { room, user_kp })
    }

    pub fn room(&self) -> &Room { &self.room }
    pub fn user_id(&self) -> DidKey { self.user_kp.did() }

    pub fn journal(&mut self, text: &str) -> Result<Record> {
        self.room.post(&self.user_kp, text, "journal")
    }

    pub fn draft(&mut self, text: &str, target_room: Option<&DidKey>) -> Result<Record> {
        let text = match target_room {
            Some(t) => format!("[draft→{}] {}", t.as_str(), text),
            None => format!("[draft] {}", text),
        };
        self.room.post(&self.user_kp, &text, "draft")
    }

    pub fn port(
        &mut self,
        transcript: &Transcript,
        intent: &str,
        target_room: Option<&DidKey>,
    ) -> Result<Record> {
        verify_transcript(transcript)?;
        if intent != "journal" && intent != "room" {
            return Err(Error::Policy(format!("unknown intent {intent}")));
        }
        if intent == "room" && target_room.is_none() {
            return Err(Error::Policy("intent 'room' requires target_room".into()));
        }
        let rec = PortLanding::new(
            self.room.world_id().clone(),
            self.room.records().len() as u64,
            self.room.last_hash(),
            transcript.clone(),
            intent.into(),
            target_room.cloned(),
        );
        let signed = crate::sign_record(rec, &self.user_kp, Record::PortLanding, |r, p| r.proof = p)?;
        let record = Record::PortLanding(signed);
        self.room.push(record.clone())?;
        Ok(record)
    }

    pub fn bookmark(&mut self, room: &Room, note: &str) -> Result<Record> {
        let rec = Bookmark::new(
            self.room.world_id().clone(),
            self.room.records().len() as u64,
            self.room.last_hash(),
            room.world_id().clone(),
            note.into(),
        );
        let signed = crate::sign_record(rec, &self.user_kp, Record::Bookmark, |r, p| r.proof = p)?;
        let record = Record::Bookmark(signed);
        self.room.push(record.clone())?;
        Ok(record)
    }

    pub fn announce_presence(&mut self, rooms: &[DidKey], ttl: u64) -> Result<Record> {
        let rec = Presence::new(
            self.room.world_id().clone(),
            self.room.records().len() as u64,
            self.room.last_hash(),
            self.user_kp.did(),
            rooms.to_vec(),
            ttl,
        );
        let signed = crate::sign_record(rec, &self.user_kp, Record::Presence, |r, p| r.proof = p)?;
        let record = Record::Presence(signed);
        self.room.push(record.clone())?;
        Ok(record)
    }

    pub fn commit_draft_to_room(
        &self,
        draft_hash: &str,
        room: &mut Room,
    ) -> Result<Record> {
        let draft_text: String = {
            let draft = self
                .room
                .records()
                .iter()
                .find(|r| {
                    r.hash().ok().as_deref() == Some(draft_hash)
                        && matches!(r, Record::Message(m) if m.kind == "draft")
                })
                .ok_or_else(|| Error::Policy("draft not found".into()))?;
            match draft {
                Record::Message(m) => m.text.clone(),
                _ => unreachable!(),
            }
        };
        let prefix = format!("[home_ref={}] ", &draft_hash[..16.min(draft_hash.len())]);
        let full_text = format!("{prefix}{draft_text}");
        room.post(&self.user_kp, &full_text, "normal")
    }

    pub fn commit_port_to_room(
        &self,
        port_hash: &str,
        room: &mut Room,
    ) -> Result<Record> {
        let (label, entries_json, target_ok): (String, String, Option<DidKey>) = {
            let port = self
                .room
                .records()
                .iter()
                .find(|r| {
                    r.hash().ok().as_deref() == Some(port_hash)
                        && matches!(r, Record::PortLanding(_))
                })
                .ok_or_else(|| Error::Policy("port not found".into()))?;
            match port {
                Record::PortLanding(p) => {
                    let entries_json = serde_json::to_string(&p.transcript.entries)
                        .map_err(|e| Error::Serialization(e.to_string()))?;
                    (p.transcript.source_label.clone(), entries_json, p.target_room.clone())
                }
                _ => unreachable!(),
            }
        };
        if let Some(target) = &target_ok {
            if target != room.world_id() {
                return Err(Error::Policy(
                    "port target_room does not match this room".into(),
                ));
            }
        }
        let prefix = format!(
            "[home_ref={}] [ported from {}] ",
            &port_hash[..16.min(port_hash.len())],
            label
        );
        let full_text = format!("{prefix}{entries_json}");
        room.post(&self.user_kp, &full_text, "port")
    }

    pub fn export(&self) -> Result<serde_json::Value> {
        let mut records = Vec::new();
        for rec in self.room.records() {
            let body = serde_json::to_value(rec)
                .map_err(|e| Error::Serialization(e.to_string()))?;
            records.push(serde_json::json!({
                "hash": rec.hash()?,
                "body": body,
            }));
        }
        Ok(serde_json::json!({
            "world_id": self.room.world_id().as_str(),
            "template": self.room.template(),
            "records": records,
        }))
    }
}
