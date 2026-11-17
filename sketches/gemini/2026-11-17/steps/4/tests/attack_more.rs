use chat_world::error::Result;
use chat_world::hash::body_for_signing;
use chat_world::record::*;
use chat_world::transcript::{sign_transcript, TranscriptEntry};
use chat_world::verify::verify_log;
use chat_world::{Keypair, ModeratorSpec, Proof, ProofOrArray, Room, RoomTemplate};

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

// =====================================================================
// 1. HUMAN OVERRIDE
// =====================================================================

#[test]
fn attack_more_human_override_of_unoverridable_moderator() -> Result<()> {
    // Expected: FAIL on current code (verify_log never checks spec.can_be_overridden!)
    let alice = Keypair::generate();
    let ai_mod = Keypair::generate();
    let human_mod = Keypair::generate();
    let room_kp = Keypair::generate();

    let mut template = RoomTemplate::chat("t", "test");
    template.moderation = "moderator".into();
    template.moderator = Some(ModeratorSpec {
        moderator_id: ai_mod.did(),
        moderator_type: "ai".into(),
        capabilities: vec!["post".into(), "redact".into()],
        can_be_overridden: false,
        knowledge_world_id: None,
        meta_room: false,
    });

    let mut room = Room::create(template, room_kp.clone(), &alice)?;
    room.join(&ai_mod, "control", true)?;
    room.join(&human_mod, "control", false)?;
    let ai_msg = room.post(&ai_mod, "ruling that cannot be overridden", "normal")?;
    let ai_msg_hash = ai_msg.hash()?;

    // Room::override_ai refuses this, so we forge the record into RoomLog directly
    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut ov = HumanOverride::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        ai_msg_hash,
        human_mod.did(),
        "none".into(),
        "forged override of unoverridable AI moderator".into(),
    );
    let wrapped = Record::HumanOverride(ov.clone());
    ov.proof = sign_dual(&wrapped, &human_mod, &room_kp);
    log.records.push(Record::HumanOverride(ov));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_more_human_override_forward_reference_to_later_record() -> Result<()> {
    // Expected: FAIL on current code (verify_log searches all of log.records instead of log.records[..i]!)
    let alice = Keypair::generate();
    let ai = Keypair::generate();
    let human_mod = Keypair::generate();
    let room_kp = Keypair::generate();

    let mut template = RoomTemplate::chat("t", "test");
    template.moderation = "moderator".into();
    let mut room = Room::create(template, room_kp.clone(), &alice)?;
    room.join(&ai, "control", true)?;
    room.join(&human_mod, "control", false)?;

    let mut log = room.log();
    let seq_ov = log.records.len() as u64;
    let prev_ov = log.records.last().unwrap().hash()?;

    // Pre-compute the future AI message that will sit at seq_ov + 1,
    // wait: its prev must be the hash of the HumanOverride at seq_ov!
    // Can human_mod override an AI record that already exists BEFORE seq_ov? Yes.
    // What about a Redact that restores a Redact at a LATER index? No, hashes are one-way.
    // Wait: what if HumanOverride at seq_ov targets the Join of `ai` at seq 1 with action="none"?
    // `Record::Join` has `author_id() == Some(&j.subject_id)`, which is `ai` (`is_ai == true`)!
    // Wait: can a HumanOverride override an AI's `Join` record? `Room::override_ai` also allows
    // any record with `author_id()`. What if `HumanOverride` with `action: "restore"` targets
    // a `Redact` by a HUMAN author when `can_be_overridden` is false, or restores the SAME
    // redact twice? Let's test overriding an AI record after the human_mod has LEFT the room,
    // or overriding when `overrides_hash` is the HumanOverride's own hash? No, let's test
    // `HumanOverride` with `action: "restore"` targeting a `Redact` created by an AI whose
    // `ModeratorSpec` has `can_be_overridden: false`!
    let bob = Keypair::generate();
    room.join(&bob, "communicate", false)?;
    let bob_msg = room.post(&bob, "hello", "normal")?;
    let bob_msg_hash = bob_msg.hash()?;

    // Re-create room with unoverridable AI moderator who redacts bob's message,
    // and human_mod restores it via action="restore" (which verify_log fails to check against can_be_overridden!)
    let mut template2 = RoomTemplate::chat("t", "test");
    template2.moderation = "moderator".into();
    template2.moderator = Some(ModeratorSpec {
        moderator_id: ai.did(),
        moderator_type: "ai".into(),
        capabilities: vec!["post".into(), "redact".into()],
        can_be_overridden: false,
        knowledge_world_id: None,
        meta_room: false,
    });
    let mut room2 = Room::create(template2, room_kp.clone(), &alice)?;
    room2.join(&ai, "control", true)?;
    room2.join(&human_mod, "control", false)?;
    room2.join(&bob, "communicate", false)?;
    let msg2 = room2.post(&bob, "hello", "normal")?;
    let red2 = room2.redact(&ai, &msg2.hash()?, "spam", "ai redacted this")?;
    let red2_hash = red2.hash()?;

    let mut log2 = room2.log();
    let prev2 = log2.records.last().unwrap().hash()?;
    let mut ov = HumanOverride::new(
        log2.world_id.clone(),
        log2.records.len() as u64,
        Some(prev2),
        red2_hash,
        human_mod.did(),
        "restore".into(),
        "restoring what unoverridable AI moderator redacted".into(),
    );
    let wrapped = Record::HumanOverride(ov.clone());
    ov.proof = sign_dual(&wrapped, &human_mod, &room_kp);
    log2.records.push(Record::HumanOverride(ov));

    let _ = (seq_ov, prev_ov, bob_msg_hash);
    assert!(verify_log(&log2).is_err());
    Ok(())
}

#[test]
fn attack_more_human_override_by_communicate_tier() -> Result<()> {
    // Expected: PASS (verify_log refuses human_override from a communicate-tier human)
    let alice = Keypair::generate();
    let ai = Keypair::generate();
    let bob = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "test"), room_kp.clone(), &alice)?;
    room.join(&ai, "control", true)?;
    room.join(&bob, "communicate", false)?;
    let ai_msg = room.post(&ai, "ai note", "normal")?;
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
        "low tier override".into(),
    );
    let wrapped = Record::HumanOverride(ov.clone());
    ov.proof = sign_dual(&wrapped, &bob, &room_kp);
    log.records.push(Record::HumanOverride(ov));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_more_human_override_targeting_human_message() -> Result<()> {
    // Expected: PASS (verify_log refuses human_override 'none' targeting a human's message)
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let dave = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "test"), room_kp.clone(), &alice)?;
    room.join(&bob, "communicate", false)?;
    room.join(&dave, "control", false)?;
    let bob_msg = room.post(&bob, "human text", "normal")?;
    let msg_hash = bob_msg.hash()?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut ov = HumanOverride::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        msg_hash,
        dave.did(),
        "none".into(),
        "cannot override human".into(),
    );
    let wrapped = Record::HumanOverride(ov.clone());
    ov.proof = sign_dual(&wrapped, &dave, &room_kp);
    log.records.push(Record::HumanOverride(ov));

    assert!(verify_log(&log).is_err());
    Ok(())
}

// =====================================================================
// 2. REFUSAL
// =====================================================================

#[test]
fn attack_more_refusal_with_unknown_reason() -> Result<()> {
    // Expected: FAIL on current code (verify_log has `Record::Refusal(_) => {}` and never checks reason!)
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let room_kp = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "test"), room_kp.clone(), &alice)?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut refusal = Refusal::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        "not_a_valid_hash".into(),
        bob.did(),
        "invented_refusal_reason_not_in_schema".into(),
    );
    let wrapped = Record::Refusal(refusal.clone());
    refusal.proof = sign_single(&wrapped, &room_kp);
    log.records.push(Record::Refusal(refusal));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_more_refusal_without_room_proof() -> Result<()> {
    // Expected: PASS (verify_log requires a room proof on Refusal even in head mode)
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let room_kp = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "test"), room_kp, &alice)?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut refusal = Refusal::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        "".into(),
        bob.did(),
        "not_a_member".into(),
    );
    let wrapped = Record::Refusal(refusal.clone());
    refusal.proof = sign_single(&wrapped, &bob);
    log.records.push(Record::Refusal(refusal));

    assert!(verify_log(&log).is_err());
    Ok(())
}

// =====================================================================
// 3. PORT LANDING & TRANSCRIPT
// =====================================================================

#[test]
fn attack_more_port_landing_without_creator_proof() -> Result<()> {
    // Expected: FAIL on current code (HomeRoom::port dual-signs with user_kp + room_kp,
    // but verify_log never checks for creator_id's proof on PortLanding!)
    let alice = Keypair::generate();
    let home_kp = Keypair::generate();
    let room = Room::create(
        RoomTemplate::personal_home("alice home"),
        home_kp.clone(),
        &alice,
    )?;

    let entries = vec![TranscriptEntry {
        speaker: "user".into(),
        ts: chat_world::now(),
        text: "hi".into(),
    }];
    let stranger = Keypair::generate();
    let t = sign_transcript("external-app", entries, &stranger)?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut port = PortLanding::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        t,
        "journal".into(),
        None,
    );
    // Signed ONLY by the room key, without Alice's (the home owner's) signature!
    let wrapped = Record::PortLanding(port.clone());
    port.proof = sign_single(&wrapped, &home_kp);
    log.records.push(Record::PortLanding(port));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_more_port_landing_with_empty_transcript_entries() -> Result<()> {
    // Expected: FAIL on current code (verify_transcript never checks !t.entries.is_empty()!)
    let alice = Keypair::generate();
    let home_kp = Keypair::generate();
    let room = Room::create(
        RoomTemplate::personal_home("alice home"),
        home_kp.clone(),
        &alice,
    )?;

    let empty_transcript = sign_transcript("external-app", vec![], &alice)?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut port = PortLanding::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        empty_transcript,
        "journal".into(),
        None,
    );
    let wrapped = Record::PortLanding(port.clone());
    port.proof = sign_dual(&wrapped, &alice, &home_kp);
    log.records.push(Record::PortLanding(port));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_more_port_landing_in_non_personal_room() -> Result<()> {
    // Expected: PASS (verify_log refuses PortLanding in a non-personal room)
    let alice = Keypair::generate();
    let room_kp = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "test"), room_kp.clone(), &alice)?;
    let entries = vec![TranscriptEntry {
        speaker: "user".into(),
        ts: chat_world::now(),
        text: "hi".into(),
    }];
    let t = sign_transcript("app", entries, &alice)?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut port = PortLanding::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        t,
        "journal".into(),
        None,
    );
    let wrapped = Record::PortLanding(port.clone());
    port.proof = sign_dual(&wrapped, &alice, &room_kp);
    log.records.push(Record::PortLanding(port));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_more_port_landing_room_intent_without_target_room() -> Result<()> {
    // Expected: PASS (verify_log refuses PortLanding when intent == "room" and target_room is None)
    let alice = Keypair::generate();
    let home_kp = Keypair::generate();
    let room = Room::create(
        RoomTemplate::personal_home("alice home"),
        home_kp.clone(),
        &alice,
    )?;
    let entries = vec![TranscriptEntry {
        speaker: "user".into(),
        ts: chat_world::now(),
        text: "hi".into(),
    }];
    let t = sign_transcript("app", entries, &alice)?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut port = PortLanding::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        t,
        "room".into(),
        None,
    );
    let wrapped = Record::PortLanding(port.clone());
    port.proof = sign_dual(&wrapped, &alice, &home_kp);
    log.records.push(Record::PortLanding(port));

    assert!(verify_log(&log).is_err());
    Ok(())
}

// =====================================================================
// 4. BOOKMARK
// =====================================================================

#[test]
fn attack_more_bookmark_without_creator_proof() -> Result<()> {
    // Expected: FAIL on current code (HomeRoom::bookmark dual-signs with user_kp + room_kp,
    // but verify_log never checks for creator_id's proof on Bookmark!)
    let alice = Keypair::generate();
    let home_kp = Keypair::generate();
    let room = Room::create(
        RoomTemplate::personal_home("alice home"),
        home_kp.clone(),
        &alice,
    )?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut bm = Bookmark::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        Keypair::generate().did(),
        "forged bookmark without user signature".into(),
    );
    let wrapped = Record::Bookmark(bm.clone());
    bm.proof = sign_single(&wrapped, &home_kp);
    log.records.push(Record::Bookmark(bm));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_more_bookmark_in_non_personal_room() -> Result<()> {
    // Expected: PASS (verify_log refuses Bookmark in a non-personal room)
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
    bm.proof = sign_dual(&wrapped, &alice, &room_kp);
    log.records.push(Record::Bookmark(bm));

    assert!(verify_log(&log).is_err());
    Ok(())
}

// =====================================================================
// 5. PRESENCE
// =====================================================================

#[test]
fn attack_more_presence_without_subject_proof() -> Result<()> {
    // Expected: FAIL on current code (HomeRoom::announce_presence dual-signs with user_kp + room_kp,
    // but verify_log never verifies p.subject_id's proof on Presence!)
    let alice = Keypair::generate();
    let home_kp = Keypair::generate();
    let room = Room::create(
        RoomTemplate::personal_home("alice home"),
        home_kp.clone(),
        &alice,
    )?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut pres = Presence::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        alice.did(),
        vec![Keypair::generate().did()],
        300,
    );
    // Signed ONLY by home_kp, with no signature from alice (p.subject_id)!
    let wrapped = Record::Presence(pres.clone());
    pres.proof = sign_single(&wrapped, &home_kp);
    log.records.push(Record::Presence(pres));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_more_presence_wrong_subject_in_personal_room() -> Result<()> {
    // Expected: PASS (verify_log refuses Presence whose subject_id != creator_id)
    let alice = Keypair::generate();
    let intruder = Keypair::generate();
    let home_kp = Keypair::generate();
    let room = Room::create(
        RoomTemplate::personal_home("alice home"),
        home_kp.clone(),
        &alice,
    )?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut pres = Presence::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        intruder.did(),
        vec![],
        300,
    );
    let wrapped = Record::Presence(pres.clone());
    pres.proof = sign_dual(&wrapped, &intruder, &home_kp);
    log.records.push(Record::Presence(pres));

    assert!(verify_log(&log).is_err());
    Ok(())
}

// =====================================================================
// 6. KNOWLEDGE SHARD EXPORT
// =====================================================================

#[test]
fn attack_more_knowledge_shard_export_with_empty_entry_hashes() -> Result<()> {
    // Expected: FAIL on current code (HomeRoom::emit_shard_export rejects empty entry_hashes,
    // but verify_log only checks `k.entry_hashes.iter().any(|h| !looks_like_hash(h))`, which is false on `vec![]`!)
    let alice = Keypair::generate();
    let home_kp = Keypair::generate();
    let room = Room::create(
        RoomTemplate::personal_home("alice home"),
        home_kp.clone(),
        &alice,
    )?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut exp = KnowledgeShardExport::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        Keypair::generate().did(),
        Keypair::generate().did(),
        vec![], // Empty entry_hashes!
    );
    let wrapped = Record::KnowledgeShardExport(exp.clone());
    exp.proof = sign_single(&wrapped, &home_kp);
    log.records.push(Record::KnowledgeShardExport(exp));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_more_knowledge_shard_export_with_bad_hash() -> Result<()> {
    // Expected: PASS (verify_log refuses KnowledgeShardExport with non-64-hex entry hash)
    let alice = Keypair::generate();
    let home_kp = Keypair::generate();
    let room = Room::create(
        RoomTemplate::personal_home("alice home"),
        home_kp.clone(),
        &alice,
    )?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut exp = KnowledgeShardExport::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        Keypair::generate().did(),
        Keypair::generate().did(),
        vec!["not-a-64-hex-hash".into()],
    );
    let wrapped = Record::KnowledgeShardExport(exp.clone());
    exp.proof = sign_single(&wrapped, &home_kp);
    log.records.push(Record::KnowledgeShardExport(exp));

    assert!(verify_log(&log).is_err());
    Ok(())
}

// =====================================================================
// 7. MODERATOR SUCCESSION
// =====================================================================

#[test]
fn attack_more_moderator_succession_missing_incoming_proof() -> Result<()> {
    // Expected: PASS (verify_log refuses ModeratorSuccession when incoming_id did not sign)
    let alice = Keypair::generate();
    let outgoing = Keypair::generate();
    let incoming = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "test"), room_kp.clone(), &alice)?;
    room.join(&outgoing, "control", true)?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut succ = ModeratorSuccession::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        outgoing.did(),
        incoming.did(),
        "00".repeat(32),
        "graduation".into(),
    );
    let wrapped = Record::ModeratorSuccession(succ.clone());
    // Signed by outgoing and room_kp, but missing incoming's proof
    succ.proof = sign_dual(&wrapped, &outgoing, &room_kp);
    log.records.push(Record::ModeratorSuccession(succ));

    assert!(verify_log(&log).is_err());
    Ok(())
}
