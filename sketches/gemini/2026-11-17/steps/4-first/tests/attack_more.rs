use chat_world::error::Result;
use chat_world::hash::body_for_signing;
use chat_world::record::*;
use chat_world::verify::verify_log;
use chat_world::{Keypair, Proof, ProofOrArray, Room, RoomTemplate};

fn sign_single(rec: &Record, signer: &Keypair) -> ProofOrArray {
    let body = body_for_signing(rec).unwrap();
    let sig = signer.sign(&body);
    ProofOrArray::Single(Proof::create(signer, &sig))
}

fn sign_dual(rec: &Record, subj: &Keypair, room_kp: &Keypair) -> ProofOrArray {
    let body = body_for_signing(rec).unwrap();
    let s1 = subj.sign(&body);
    let s2 = room_kp.sign(&body);
    ProofOrArray::array(vec![
        Proof::create(subj, &s1),
        Proof::create(room_kp, &s2),
    ])
}

fn sign_triple(rec: &Record, a: &Keypair, b: &Keypair, room_kp: &Keypair) -> ProofOrArray {
    let body = body_for_signing(rec).unwrap();
    let sa = a.sign(&body);
    let sb = b.sign(&body);
    let sroom = room_kp.sign(&body);
    ProofOrArray::array(vec![
        Proof::create(a, &sa),
        Proof::create(b, &sb),
        Proof::create(room_kp, &sroom),
    ])
}

// =====================================================================
// ATTACKS ON THE SEVEN UNATTACKED RECORD KINDS
// =====================================================================

#[test]
fn attack_more_human_override_by_non_member() -> Result<()> {
    // Expected: PASS (verify_log refuses human override by a non-member)
    let alice = Keypair::generate();
    let ai = Keypair::generate();
    let outsider = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.moderation = "moderator".into();
    let mut room = Room::create(template, room_kp.clone(), &alice)?;
    room.join(&ai, "control", true)?;
    let ai_msg = room.post(&ai, "ai output", "normal")?;
    let msg_hash = ai_msg.hash()?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut ov = HumanOverride::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        msg_hash,
        outsider.did(),
        "none".into(),
        "unauthorized override".into(),
    );
    let wrapped = Record::HumanOverride(ov.clone());
    ov.proof = sign_dual(&wrapped, &outsider, &room_kp);
    log.records.push(Record::HumanOverride(ov));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_more_human_override_by_communicate_tier() -> Result<()> {
    // Expected: PASS (verify_log refuses human override by a user with only communicate tier)
    let alice = Keypair::generate();
    let ai = Keypair::generate();
    let bob = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.moderation = "moderator".into();
    let mut room = Room::create(template, room_kp.clone(), &alice)?;
    room.join(&ai, "control", true)?;
    room.join(&bob, "communicate", false)?;
    let ai_msg = room.post(&ai, "ai output", "normal")?;
    let msg_hash = ai_msg.hash()?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut ov = HumanOverride::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        msg_hash,
        bob.did(),
        "none".into(),
        "insufficient tier override".into(),
    );
    let wrapped = Record::HumanOverride(ov.clone());
    ov.proof = sign_dual(&wrapped, &bob, &room_kp);
    log.records.push(Record::HumanOverride(ov));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_more_human_override_targeting_human_message() -> Result<()> {
    // Expected: PASS (verify_log refuses human override targeting a human-authored message instead of AI)
    let alice = Keypair::generate();
    let human_mod = Keypair::generate();
    let bob = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.moderation = "moderator".into();
    let mut room = Room::create(template, room_kp.clone(), &alice)?;
    room.join(&human_mod, "control", false)?;
    room.join(&bob, "communicate", false)?;
    let bob_msg = room.post(&bob, "human statement", "normal")?;
    let msg_hash = bob_msg.hash()?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut ov = HumanOverride::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        msg_hash,
        human_mod.did(),
        "none".into(),
        "invalid target override".into(),
    );
    let wrapped = Record::HumanOverride(ov.clone());
    ov.proof = sign_dual(&wrapped, &human_mod, &room_kp);
    log.records.push(Record::HumanOverride(ov));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_more_human_override_unknown_action() -> Result<()> {
    // Expected: PASS (verify_log refuses human override with an unrecognized action string)
    let alice = Keypair::generate();
    let human_mod = Keypair::generate();
    let ai = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.moderation = "moderator".into();
    let mut room = Room::create(template, room_kp.clone(), &alice)?;
    room.join(&human_mod, "control", false)?;
    room.join(&ai, "control", true)?;
    let ai_msg = room.post(&ai, "ai speech", "normal")?;
    let msg_hash = ai_msg.hash()?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut ov = HumanOverride::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        msg_hash,
        human_mod.did(),
        "destroy_universe".into(),
        "bad action".into(),
    );
    let wrapped = Record::HumanOverride(ov.clone());
    ov.proof = sign_dual(&wrapped, &human_mod, &room_kp);
    log.records.push(Record::HumanOverride(ov));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_more_port_landing_in_non_personal_room() -> Result<()> {
    // Expected: PASS (verify_log refuses PortLanding in a standard chat room)
    let alice = Keypair::generate();
    let room_kp = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "test"), room_kp.clone(), &alice)?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let t = chat_world::transcript::sign_transcript("label", vec![], &alice)?;
    let mut port = PortLanding::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        t,
        "journal".into(),
        None,
    );
    let wrapped = Record::PortLanding(port.clone());
    port.proof = sign_single(&wrapped, &room_kp);
    log.records.push(Record::PortLanding(port));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_more_bookmark_in_non_personal_room() -> Result<()> {
    // Expected: PASS (verify_log refuses Bookmark in a standard chat room)
    let alice = Keypair::generate();
    let room_kp = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "test"), room_kp.clone(), &alice)?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut bm = Bookmark::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        Keypair::generate().did(),
        "note".into(),
    );
    let wrapped = Record::Bookmark(bm.clone());
    bm.proof = sign_single(&wrapped, &room_kp);
    log.records.push(Record::Bookmark(bm));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_more_presence_in_non_personal_room() -> Result<()> {
    // Expected: PASS (verify_log refuses Presence in a standard chat room)
    let alice = Keypair::generate();
    let room_kp = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "test"), room_kp.clone(), &alice)?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut pres = Presence::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        alice.did(),
        vec![],
        300,
    );
    let wrapped = Record::Presence(pres.clone());
    pres.proof = sign_single(&wrapped, &room_kp);
    log.records.push(Record::Presence(pres));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_more_knowledge_shard_export_in_non_personal_room() -> Result<()> {
    // Expected: PASS (verify_log refuses KnowledgeShardExport in a standard chat room)
    let alice = Keypair::generate();
    let room_kp = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "test"), room_kp.clone(), &alice)?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut exp = KnowledgeShardExport::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        Keypair::generate().did(),
        Keypair::generate().did(),
        vec!["00".repeat(32)],
    );
    let wrapped = Record::KnowledgeShardExport(exp.clone());
    exp.proof = sign_single(&wrapped, &room_kp);
    log.records.push(Record::KnowledgeShardExport(exp));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_more_moderator_succession_non_control_outgoing() -> Result<()> {
    // Expected: PASS (verify_log refuses ModeratorSuccession when outgoing tier is communicate)
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let incoming = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "test"), room_kp.clone(), &alice)?;
    room.join(&bob, "communicate", true)?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut succ = ModeratorSuccession::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        bob.did(),
        incoming.did(),
        "00".repeat(32),
        "unauthorized succession".into(),
    );
    let wrapped = Record::ModeratorSuccession(succ.clone());
    succ.proof = sign_triple(&wrapped, &bob, &incoming, &room_kp);
    log.records.push(Record::ModeratorSuccession(succ));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_more_moderator_succession_same_outgoing_incoming() -> Result<()> {
    // Expected: PASS (verify_log refuses ModeratorSuccession where outgoing == incoming)
    let alice = Keypair::generate();
    let ai = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "test"), room_kp.clone(), &alice)?;
    room.join(&ai, "control", true)?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut succ = ModeratorSuccession::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        ai.did(),
        ai.did(),
        "00".repeat(32),
        "self succession".into(),
    );
    let wrapped = Record::ModeratorSuccession(succ.clone());
    succ.proof = sign_triple(&wrapped, &ai, &ai, &room_kp);
    log.records.push(Record::ModeratorSuccession(succ));

    assert!(verify_log(&log).is_err());
    Ok(())
}
