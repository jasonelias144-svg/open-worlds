use chat_world::error::Result;
use chat_world::home::HomeRoom;
use chat_world::transcript::{sign_transcript, TranscriptEntry};
use chat_world::verify::verify_log;
use chat_world::{Keypair, Room, RoomLog, RoomTemplate};

fn make_room() -> Room {
    let alice = Keypair::generate();
    let room_kp = Keypair::generate();
    let template = RoomTemplate::chat("t", "test");
    Room::create(template, room_kp, &alice).unwrap()
}

fn make_head_mode_room(interval: u64) -> Room {
    let alice = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.head_interval = interval;
    Room::create(template, room_kp, &alice).unwrap()
}

#[test]
fn honest_room_log_roundtrips_json_and_verifies() -> Result<()> {
    let mut room = make_room();
    let bob = Keypair::generate();
    room.join(&bob, "communicate", false)?;
    let msg = room.post(&bob, "hello from bob", "normal")?;
    let msg_hash = msg.hash()?;
    room.redact(&bob, &msg_hash, "author_request", "typo")?;

    let json_text = serde_json::to_string(&room.log())
        .expect("serialize RoomLog to JSON");
    let parsed: RoomLog = serde_json::from_str(&json_text)
        .expect("deserialize RoomLog from JSON");

    verify_log(&parsed)
}

#[test]
fn honest_home_log_roundtrips_json_and_verifies() -> Result<()> {
    let alice = Keypair::generate();
    let home_kp = Keypair::generate();
    let mut home = HomeRoom::create(alice.clone(), home_kp, "alice home")?;
    home.journal("first journal entry")?;
    home.draft("draft thought", None)?;
    let entries = vec![TranscriptEntry {
        speaker: "user".into(),
        ts: chat_world::now(),
        text: "ported line".into(),
    }];
    let t = sign_transcript("external-app", entries, &alice)?;
    home.port(&t, "journal", None)?;

    let json_text = serde_json::to_string(&home.room().log())
        .expect("serialize home RoomLog to JSON");
    let parsed: RoomLog = serde_json::from_str(&json_text)
        .expect("deserialize home RoomLog from JSON");

    verify_log(&parsed)
}

#[test]
fn honest_head_mode_room_log_roundtrips_json_and_verifies() -> Result<()> {
    let mut room = make_head_mode_room(2);
    let bob = Keypair::generate();
    room.join(&bob, "communicate", false)?;
    room.post(&bob, "first", "normal")?;
    room.post(&bob, "second", "normal")?;
    room.post(&bob, "third", "normal")?;
    assert_eq!(room.heads().len(), 2);

    let json_text = serde_json::to_string(&room.log())
        .expect("serialize head-mode RoomLog to JSON");
    let parsed: RoomLog = serde_json::from_str(&json_text)
        .expect("deserialize head-mode RoomLog from JSON");

    verify_log(&parsed)
}
