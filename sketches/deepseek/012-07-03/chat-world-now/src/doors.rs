use crate::commons::{
    verify_commons_log, verify_registration, CommonsLog,
    CommonsRecord,
};
use crate::did::DidKey;
use crate::error::{Error, Result};
use crate::head::WorldHead;
use crate::record::Record;
use crate::room::RoomLog;
use serde::{Deserialize, Serialize};
use std::collections::{HashMap, HashSet};

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DoorLaw {
    pub join_policy: String,
    pub membership: String,
    pub moderation: String,
    pub mode: String,
    pub personal: bool,
    #[serde(default)]
    pub welcome: Option<String>,
    pub count_hidden: bool,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DoorCount {
    pub members: u64,
    pub at_record: u64,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Door {
    pub room_id: DidKey,
    pub topic: String,
    #[serde(default)]
    pub own_topic: Option<String>,
    pub template_hash: String,
    pub registration_seq: u64,
    pub registration_hash: String,
    #[serde(default)]
    pub law: Option<DoorLaw>,
    #[serde(default)]
    pub count: Option<DoorCount>,
}

#[derive(Clone, Debug, PartialEq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct DoorList {
    pub commons_id: DidKey,
    pub drawn_from: u64,
    #[serde(default)]
    pub log_head: Option<String>,
    pub doors: Vec<Door>,
}

pub fn draw(log: &CommonsLog, rooms: &[RoomLog]) -> Result<DoorList> {
    verify_commons_log(log)?;

    let drawn_from = log.records.len() as u64;
    let log_head = match log.records.last() {
        Some(rec) => Some(rec.hash()?),
        None => None,
    };

    let mut reg_by_room: HashMap<DidKey, &crate::commons::RoomRegistered> = HashMap::new();
    for rec in &log.records {
        if let CommonsRecord::RoomRegistered(r) = rec {
            reg_by_room.insert(r.room_id.clone(), r);
        }
    }

    let mut rooms_by_id: HashMap<DidKey, &RoomLog> = HashMap::new();
    for room_log in rooms {
        let Some(&reg) = reg_by_room.get(&room_log.world_id) else {
            return Err(Error::Policy(format!(
                "room {} is not registered in this Commons",
                room_log.world_id.as_str()
            )));
        };
        if rooms_by_id.insert(room_log.world_id.clone(), room_log).is_some() {
            return Err(Error::Policy(format!(
                "duplicate room log for {}",
                room_log.world_id.as_str()
            )));
        }
        verify_registration(reg, room_log)?;
    }

    let mut doors = Vec::new();
    for rec in &log.records {
        if let CommonsRecord::RoomRegistered(r) = rec {
            let registration_hash = rec.hash()?;
            let (own_topic, law, count) = if let Some(&room_log) = rooms_by_id.get(&r.room_id) {
                let mut present: HashSet<DidKey> = HashSet::new();
                for (idx, room_rec) in room_log.records.iter().enumerate() {
                    match room_rec {
                        Record::RoomCreated(rc) => {
                            present.insert(rc.creator_id.clone());
                        }
                        Record::Join(j) => {
                            present.insert(j.subject_id.clone());
                        }
                        Record::Leave(l) => {
                            if !present.remove(&l.subject_id) {
                                return Err(Error::Policy(format!(
                                    "room {} record {}: leave by non-member {}",
                                    room_log.world_id.as_str(),
                                    idx,
                                    l.subject_id.as_str()
                                )));
                            }
                        }
                        _ => {}
                    }
                }

                let t = &room_log.template;
                let door_law = DoorLaw {
                    join_policy: t.join_policy.clone(),
                    membership: t.membership.clone(),
                    moderation: t.moderation.clone(),
                    mode: t.mode.clone(),
                    personal: t.personal,
                    welcome: t.welcome.clone(),
                    count_hidden: t.count_hidden,
                };
                let door_count = if t.count_hidden {
                    None
                } else {
                    Some(DoorCount {
                        members: present.len() as u64,
                        at_record: room_log.records.len() as u64,
                    })
                };
                (Some(t.topic.clone()), Some(door_law), door_count)
            } else {
                (None, None, None)
            };

            doors.push(Door {
                room_id: r.room_id.clone(),
                topic: r.topic.clone(),
                own_topic,
                template_hash: r.template_hash.clone(),
                registration_seq: r.seq,
                registration_hash,
                law,
                count,
            });
        }
    }

    Ok(DoorList {
        commons_id: log.commons_id.clone(),
        drawn_from,
        log_head,
        doors,
    })
}

pub fn check(list: &DoorList, log: &CommonsLog, rooms: &[RoomLog]) -> Result<()> {
    let expected = draw(log, rooms)?;
    if list.commons_id != expected.commons_id {
        return Err(Error::Verification("door list: commons_id mismatch".into()));
    }
    if list.drawn_from != expected.drawn_from {
        return Err(Error::Verification(format!(
            "door list: drawn_from {} != expected {}",
            list.drawn_from, expected.drawn_from
        )));
    }
    if list.log_head != expected.log_head {
        return Err(Error::Verification("door list: log_head mismatch".into()));
    }
    if list.doors.len() != expected.doors.len() {
        return Err(Error::Verification(format!(
            "door list: door count {} != expected {}",
            list.doors.len(),
            expected.doors.len()
        )));
    }
    for (i, (got, exp)) in list.doors.iter().zip(expected.doors.iter()).enumerate() {
        if got != exp {
            return Err(Error::Verification(format!(
                "door list: door at index {i} differs"
            )));
        }
    }
    Ok(())
}

fn verify_heads_against_rooms(rooms: &[RoomLog], heads: &[WorldHead]) -> Result<()> {
    for head in heads {
        let room_log = rooms
            .iter()
            .find(|r| r.world_id == head.world)
            .ok_or_else(|| {
                Error::Policy(format!(
                    "head names room {} whose log was not given",
                    head.world.as_str()
                ))
            })?;
        room_log.verify_head(head)?;
    }
    Ok(())
}

pub fn draw_at(
    log: &CommonsLog,
    rooms: &[RoomLog],
    heads: &[WorldHead],
) -> Result<DoorList> {
    verify_heads_against_rooms(rooms, heads)?;
    draw(log, rooms)
}

pub fn check_at(
    list: &DoorList,
    log: &CommonsLog,
    rooms: &[RoomLog],
    heads: &[WorldHead],
) -> Result<()> {
    verify_heads_against_rooms(rooms, heads)?;
    check(list, log, rooms)
}

pub fn ranked(list: &DoorList) -> Vec<&Door> {
    let mut with_count: Vec<(usize, &Door, u64)> = Vec::new();
    let mut without_count: Vec<&Door> = Vec::new();

    for (idx, door) in list.doors.iter().enumerate() {
        match &door.count {
            Some(c) => with_count.push((idx, door, c.members)),
            None => without_count.push(door),
        }
    }

    with_count.sort_by(|a, b| b.2.cmp(&a.2).then_with(|| a.0.cmp(&b.0)));

    let mut out: Vec<&Door> = with_count.into_iter().map(|(_, d, _)| d).collect();
    out.extend(without_count);
    out
}

fn quote_ascii(s: &str) -> String {
    let mut out = String::with_capacity(s.len() + 2);
    out.push('"');
    for c in s.chars() {
        let code = c as u32;
        if (0x20..=0x7e).contains(&code) && c != '"' && c != '\\' {
            out.push(c);
        } else {
            let mut buf = [0u16; 2];
            for unit in c.encode_utf16(&mut buf) {
                out.push_str(&format!("\\u{:04x}", unit));
            }
        }
    }
    out.push('"');
    out
}

pub fn as_text(list: &DoorList) -> String {
    let mut out = String::new();
    out.push_str(&format!("DOORS OF {}\n", quote_ascii(list.commons_id.as_str())));
    let head_str = match &list.log_head {
        Some(h) => quote_ascii(h),
        None => "none".to_string(),
    };
    out.push_str(&format!(
        "drawn from {} records, head {}\n",
        list.drawn_from, head_str
    ));
    out.push_str(&format!("{} doors\n", list.doors.len()));

    for (idx, door) in list.doors.iter().enumerate() {
        let n = idx + 1;
        out.push_str(&format!("{}. topic {}\n", n, quote_ascii(&door.topic)));
        if let Some(own) = &door.own_topic {
            if own != &door.topic {
                out.push_str(&format!("   its own topic {}\n", quote_ascii(own)));
            }
        }
        out.push_str(&format!("   room {}\n", quote_ascii(door.room_id.as_str())));
        out.push_str(&format!("   law {}\n", quote_ascii(&door.template_hash)));
        out.push_str(&format!(
            "   registered at {} as {}\n",
            door.registration_seq,
            quote_ascii(&door.registration_hash)
        ));
        match &door.law {
            Some(law) => {
                out.push_str(&format!(
                    "   join {}, membership {}, moderation {}, mode {}, personal {}\n",
                    quote_ascii(&law.join_policy),
                    quote_ascii(&law.membership),
                    quote_ascii(&law.moderation),
                    quote_ascii(&law.mode),
                    law.personal
                ));
                if let Some(welcome) = &law.welcome {
                    out.push_str(&format!("   welcome {}\n", quote_ascii(welcome)));
                }
                match &door.count {
                    Some(c) => {
                        out.push_str(&format!(
                            "   members {}, counted at record {}\n",
                            c.members, c.at_record
                        ));
                    }
                    None => {
                        out.push_str("   members not shown\n");
                    }
                }
            }
            None => {
                out.push_str("   law not held\n");
            }
        }
    }

    out
}
