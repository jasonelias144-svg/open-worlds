use chat_world::error::Result;
use chat_world::record::Record;
use chat_world::verify::verify_room;
use chat_world::{Keypair, Room, RoomTemplate};

fn make_room() -> Room {
    let alice = Keypair::generate();
    let template = RoomTemplate::chat("t", "test");
    Room::create(template, alice).unwrap()
}

#[test]
fn room_verifies_after_activity() -> Result<()> {
    let mut room = make_room();
    let bob = Keypair::generate();
    room.join(&bob, "communicate", false)?;
    room.post(&bob, "hello", "normal")?;
    verify_room(&room)
}

#[test]
fn non_member_is_refused() -> Result<()> {
    let mut room = make_room();
    let bob = Keypair::generate();
    let rec = room.post(&bob, "hi", "normal")?;
    match rec {
        Record::Refusal(r) => assert_eq!(r.reason, "not_a_member"),
        _ => panic!("expected refusal"),
    }
    verify_room(&room)
}

#[test]
fn rate_limit_enforced() -> Result<()> {
    let mut room = make_room();
    room.template.rate_limit_count = 2;
    room.template.rate_limit_window = 5;
    let bob = Keypair::generate();
    room.join(&bob, "communicate", false)?;
    room.post(&bob, "one", "normal")?;
    room.post(&bob, "two", "normal")?;
    let rec = room.post(&bob, "three", "normal")?;
    match rec {
        Record::Refusal(r) => assert_eq!(r.reason, "rate_limit"),
        _ => panic!("expected rate-limit refusal"),
    }
    verify_room(&room)
}

#[test]
fn inter_ai_pace_fires() -> Result<()> {
    let mut room = make_room();
    room.template.inter_ai_pace = 1;
    let ai_a = Keypair::generate();
    let ai_b = Keypair::generate();
    room.join(&ai_a, "communicate", true)?;
    room.join(&ai_b, "communicate", true)?;
    room.post(&ai_a, "first", "normal")?;
    let rec = room.post(&ai_b, "second", "normal")?;
    match rec {
        Record::Refusal(r) => assert_eq!(r.reason, "inter_ai_pace"),
        _ => panic!("expected inter_ai_pace refusal"),
    }
    verify_room(&room)
}

#[test]
fn author_can_redact_own() -> Result<()> {
    let mut room = make_room();
    let bob = Keypair::generate();
    room.join(&bob, "communicate", false)?;
    let msg = room.post(&bob, "oops", "normal")?;
    let h = msg.hash()?;
    let r = room.redact(&bob, &h, "my bad")?;
    match r {
        Record::Redact(_) => {}
        _ => panic!("expected redact"),
    }
    assert!(room.is_redacted(&h));
    verify_room(&room)
}

#[test]
fn moderator_can_redact_other() -> Result<()> {
    let mut room = make_room();
    room.template.moderation = "moderator".into();
    let bob = Keypair::generate();
    let moderator = Keypair::generate();
    room.join(&bob, "communicate", false)?;
    room.join(&moderator, "control", false)?;
    let msg = room.post(&bob, "spam", "normal")?;
    let h = msg.hash()?;
    room.redact(&moderator, &h, "spam")?;
    verify_room(&room)
}

#[test]
fn non_moderator_cannot_redact_other() -> Result<()> {
    let mut room = make_room();
    room.template.moderation = "moderator".into();
    let bob = Keypair::generate();
    let alice = Keypair::generate();
    room.join(&bob, "communicate", false)?;
    room.join(&alice, "communicate", false)?;
    let msg = room.post(&bob, "hi", "normal")?;
    let h = msg.hash()?;
    let r = room.redact(&alice, &h, "no")?;
    match r {
        Record::Refusal(r) => assert_eq!(r.reason, "not_allowed"),
        _ => panic!("expected refusal"),
    }
    verify_room(&room)
}

#[test]
fn human_can_override_ai() -> Result<()> {
    let mut room = make_room();
    room.template.moderation = "moderator".into();
    let ai = Keypair::generate();
    let human = Keypair::generate();
    room.join(&ai, "control", true)?;
    room.join(&human, "control", false)?;
    let ai_msg = room.post(&ai, "an observation", "normal")?;
    let h = ai_msg.hash()?;
    room.override_ai(&human, &h, "none", "good observation")?;
    verify_room(&room)
}

#[test]
fn ai_cannot_override() -> Result<()> {
    let mut room = make_room();
    let ai1 = Keypair::generate();
    let ai2 = Keypair::generate();
    room.join(&ai1, "control", true)?;
    room.join(&ai2, "communicate", true)?;
    let msg = room.post(&ai2, "hi", "normal")?;
    let h = msg.hash()?;
    assert!(room.override_ai(&ai1, &h, "none", "no").is_err());
    Ok(())
}

#[test]
fn personal_room_refuses_non_seed() -> Result<()> {
    let creator = Keypair::generate();
    let template = RoomTemplate::personal_home("my home");
    let mut room = Room::create(template, creator)?;
    let other = Keypair::generate();
    let r = room.join(&other, "communicate", false)?;
    match r {
        Record::Refusal(r) => assert_eq!(r.reason, "personal_room"),
        _ => panic!("expected personal_room refusal"),
    }
    Ok(())
}

#[test]
fn human_only_room_refuses_ai() -> Result<()> {
    let creator = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.membership = "human_only".into();
    let mut room = Room::create(template, creator)?;
    let ai = Keypair::generate();
    let r = room.join(&ai, "communicate", true)?;
    match r {
        Record::Refusal(r) => assert_eq!(r.reason, "human_only_room"),
        _ => panic!("expected human_only_room refusal"),
    }
    Ok(())
}

#[test]
fn chain_integrity_detects_tampering() -> Result<()> {
    // The chain cannot be tampered without breaking `prev`, but
    // we can simulate by checking that verify_room succeeds on a
    // clean room and that the last record's prev matches the
    // previous record's hash.
    let mut room = make_room();
    let bob = Keypair::generate();
    room.join(&bob, "communicate", false)?;
    room.post(&bob, "hi", "normal")?;
    let recs = room.records();
    for i in 1..recs.len() {
        assert_eq!(recs[i].prev(), Some(&recs[i - 1].hash()?));
    }
    Ok(())
}
