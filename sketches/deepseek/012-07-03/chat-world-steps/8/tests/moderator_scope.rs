
use chat_world::error::Result;
use chat_world::home::HomeRoom;
use chat_world::record::*;
use chat_world::verify::{verify_log, verify_moderator_scope};
use chat_world::{Keypair, Room, RoomLog, RoomTemplate};

fn make_room(template: RoomTemplate) -> Room {
    let alice = Keypair::generate();
    let room_kp = Keypair::generate();
    Room::create(template, room_kp, &alice).unwrap()
}

fn make_ai_kw(ai_kp: &Keypair) -> HomeRoom {
    let kw_kp = Keypair::generate();
    HomeRoom::create(ai_kp.clone(), kw_kp, "ai memory").unwrap()
}

fn make_ai_only_room() -> Room {
    let mut template = RoomTemplate::chat("meta", "meta");
    template.membership = "ai_only".into();
    make_room(template)
}

fn roundtrip(log: &RoomLog) -> RoomLog {
    let text = serde_json::to_string(log).expect("serialize RoomLog");
    serde_json::from_str(&text).expect("deserialize RoomLog")
}

#[test]
fn passes_for_matching_scope() -> Result<()> {
    let ai_kp = Keypair::generate();
    let mut kw = make_ai_kw(&ai_kp);
    let mut room = make_room(RoomTemplate::chat("t", "test"));
    kw.declare_moderator_scope(vec![room.world_id().clone()], vec![])?;
    room.join(&ai_kp, "control", true)?;
    let kw_log = roundtrip(&kw.room().log());
    let room_log = roundtrip(&room.log());
    verify_moderator_scope(&kw_log, &room_log)?;
    Ok(())
}

#[test]
fn fails_for_undeclared_room() -> Result<()> {
    let ai_kp = Keypair::generate();
    let mut kw = make_ai_kw(&ai_kp);
    let mut room_a = make_room(RoomTemplate::chat("a", "a"));
    let mut room_b = make_room(RoomTemplate::chat("b", "b"));
    kw.declare_moderator_scope(vec![room_a.world_id().clone()], vec![])?;
    room_a.join(&ai_kp, "control", true)?;
    room_b.join(&ai_kp, "control", true)?;
    let kw_log = kw.room().log();
    verify_moderator_scope(&kw_log, &room_a.log())?;
    let r = verify_moderator_scope(&kw_log, &room_b.log());
    assert!(r.is_err(), "expected fail for undeclared room B");
    Ok(())
}

#[test]
fn fails_for_over_reach() -> Result<()> {
    let ai_kp = Keypair::generate();
    let mut kw = make_ai_kw(&ai_kp);
    let mut room_a = make_room(RoomTemplate::chat("a", "a"));
    let room_b = make_room(RoomTemplate::chat("b", "b"));
    kw.declare_moderator_scope(
        vec![room_a.world_id().clone(), room_b.world_id().clone()],
        vec![],
    )?;
    room_a.join(&ai_kp, "control", true)?;
    let r = verify_moderator_scope(&kw.room().log(), &room_a.log());
    assert!(r.is_err(), "expected fail for over-reach");
    Ok(())
}

#[test]
fn passes_for_meta_room() -> Result<()> {
    let ai_kp = Keypair::generate();
    let mut kw = make_ai_kw(&ai_kp);
    let mut room_a = make_room(RoomTemplate::chat("a", "a"));
    let mut meta = make_ai_only_room();
    kw.declare_moderator_scope(
        vec![room_a.world_id().clone()],
        vec![meta.world_id().clone()],
    )?;
    room_a.join(&ai_kp, "control", true)?;
    meta.join(&ai_kp, "control", true)?;
    verify_moderator_scope(&kw.room().log(), &room_a.log())?;
    verify_moderator_scope(&kw.room().log(), &meta.log())?;
    Ok(())
}

#[test]
fn fails_for_undeclared_meta_room() -> Result<()> {
    let ai_kp = Keypair::generate();
    let mut kw = make_ai_kw(&ai_kp);
    let mut room_a = make_room(RoomTemplate::chat("a", "a"));
    let mut meta = make_ai_only_room();
    kw.declare_moderator_scope(vec![room_a.world_id().clone()], vec![])?;
    room_a.join(&ai_kp, "control", true)?;
    meta.join(&ai_kp, "control", true)?;
    verify_moderator_scope(&kw.room().log(), &room_a.log())?;
    let r = verify_moderator_scope(&kw.room().log(), &meta.log());
    assert!(r.is_err(), "expected fail for undeclared meta");
    Ok(())
}

#[test]
fn vacuous_when_not_a_member() -> Result<()> {
    let ai_kp = Keypair::generate();
    let mut kw = make_ai_kw(&ai_kp);
    let room = make_room(RoomTemplate::chat("t", "test"));
    kw.declare_moderator_scope(vec![room.world_id().clone()], vec![])?;
    // AI never joined the room; the pair check has nothing to
    // enforce and passes vacuously.
    verify_moderator_scope(&kw.room().log(), &room.log())?;
    Ok(())
}

#[test]
fn fails_when_scope_undeclared() -> Result<()> {
    let ai_kp = Keypair::generate();
    let _kw = make_ai_kw(&ai_kp);
    let mut room = make_room(RoomTemplate::chat("t", "test"));
    room.join(&ai_kp, "control", true)?;
    // KW has no moderator_scope; the AI is a moderator; check fails.
    let kw_log = _kw.room().log();
    let r = verify_moderator_scope(&kw_log, &room.log());
    assert!(r.is_err(), "expected fail for undeclared scope");
    Ok(())
}

#[test]
fn after_leave_passes_vacuously() -> Result<()> {
    let ai_kp = Keypair::generate();
    let mut kw = make_ai_kw(&ai_kp);
    let mut room = make_room(RoomTemplate::chat("t", "test"));
    kw.declare_moderator_scope(vec![room.world_id().clone()], vec![])?;
    room.join(&ai_kp, "control", true)?;
    verify_moderator_scope(&kw.room().log(), &room.log())?;
    room.leave(&ai_kp)?;
    verify_moderator_scope(&kw.room().log(), &room.log())?;
    Ok(())
}

#[test]
fn latest_scope_wins() -> Result<()> {
    let ai_kp = Keypair::generate();
    let mut kw = make_ai_kw(&ai_kp);
    let mut room_a = make_room(RoomTemplate::chat("a", "a"));
    let mut room_b = make_room(RoomTemplate::chat("b", "b"));
    // First scope: [A]
    kw.declare_moderator_scope(vec![room_a.world_id().clone()], vec![])?;
    room_a.join(&ai_kp, "control", true)?;
    room_b.join(&ai_kp, "control", true)?;
    // Then: [B] (supersedes [A])
    kw.declare_moderator_scope(vec![room_b.world_id().clone()], vec![])?;
    let kw_log = kw.room().log();
    // B passes (it's the latest scope).
    verify_moderator_scope(&kw_log, &room_b.log())?;
    // A fails (not in the latest scope; the AI is still in A
    // but hasn't left, so the check runs and fails).
    let r = verify_moderator_scope(&kw_log, &room_a.log());
    assert!(r.is_err(), "expected fail: latest scope is [B], not [A]");
    Ok(())
}

#[test]
fn moderator_scope_only_in_personal_rooms() -> Result<()> {
    // A ModeratorScope record outside a personal room is refused.
    let alice = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "test"), room_kp.clone(), &alice)?;
    let bob = Keypair::generate();
    room.join(&bob, "control", false)?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut scope = ModeratorScope::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        vec![],
        vec![],
    );
    let wrapped = Record::ModeratorScope(scope.clone());
    let body = chat_world::hash::body_for_signing(&wrapped)?;
    let sig = room_kp.sign(&body);
    scope.proof = chat_world::ProofOrArray::single(chat_world::Proof::create(&room_kp, &sig));
    log.records.push(Record::ModeratorScope(scope));

    assert!(verify_log(&log).is_err());
    Ok(())
}

