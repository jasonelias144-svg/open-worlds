use chat_world::error::Result;
use chat_world::hash::body_for_signing;
use chat_world::head::{WorldHead, HEAD_FORMAT_V1};
use chat_world::record::*;
use chat_world::verify::verify_log;
use chat_world::{Keypair, Proof, ProofOrArray, Room, RoomLog, RoomTemplate};

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
// 1. PROOFS
// =====================================================================

#[test]
fn attack_proofs_missing_room_proof_in_per_record_mode() -> Result<()> {
    // Expected: PASS (verify_log refuses a message with only author proof in per-record mode)
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "test"), room_kp, &alice)?;
    room.join(&bob, "communicate", false)?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut msg = Message::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        bob.did(),
        "forged without room sig".into(),
        "normal".into(),
    );
    let wrapped = Record::Message(msg.clone());
    msg.proof = sign_single(&wrapped, &bob);
    log.records.push(Record::Message(msg));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_proofs_moved_from_one_record_to_another() -> Result<()> {
    // Expected: PASS (verify_log refuses a proof transplanted onto different message bytes)
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "test"), room_kp, &alice)?;
    room.join(&bob, "communicate", false)?;
    room.post(&bob, "first message", "normal")?;
    room.post(&bob, "second message", "normal")?;

    let mut log = room.log();
    let first_proof = log.records[2].proof().clone();
    if let Record::Message(ref mut m2) = log.records[3] {
        m2.proof = first_proof;
    }

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_proofs_signed_by_key_that_never_joined() -> Result<()> {
    // Expected: PASS (verify_log refuses a message from an unjoined key even with room sig)
    let alice = Keypair::generate();
    let mallory = Keypair::generate();
    let room_kp = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "test"), room_kp.clone(), &alice)?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut msg = Message::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        mallory.did(),
        "never joined".into(),
        "normal".into(),
    );
    let wrapped = Record::Message(msg.clone());
    msg.proof = sign_dual(&wrapped, &mallory, &room_kp);
    log.records.push(Record::Message(msg));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_proofs_signed_by_key_that_has_left() -> Result<()> {
    // Expected: PASS (verify_log refuses a message from a member after their Leave record)
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "test"), room_kp.clone(), &alice)?;
    room.join(&bob, "communicate", false)?;
    room.leave(&bob)?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut msg = Message::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        bob.did(),
        "ghost message after leaving".into(),
        "normal".into(),
    );
    let wrapped = Record::Message(msg.clone());
    msg.proof = sign_dual(&wrapped, &bob, &room_kp);
    log.records.push(Record::Message(msg));

    assert!(verify_log(&log).is_err());
    Ok(())
}

// =====================================================================
// 2. ORDER
// =====================================================================

#[test]
fn attack_order_two_records_swapped() -> Result<()> {
    // Expected: PASS (verify_log refuses when two records are swapped)
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "test"), room_kp, &alice)?;
    room.join(&bob, "communicate", false)?;
    room.post(&bob, "msg A", "normal")?;
    room.post(&bob, "msg B", "normal")?;

    let mut log = room.log();
    log.records.swap(2, 3);

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_order_record_dropped_from_middle() -> Result<()> {
    // Expected: PASS (verify_log refuses when a middle record is removed)
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "test"), room_kp, &alice)?;
    room.join(&bob, "communicate", false)?;
    room.post(&bob, "msg A", "normal")?;
    room.post(&bob, "msg B", "normal")?;

    let mut log = room.log();
    log.records.remove(2);

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_order_record_repeated() -> Result<()> {
    // Expected: PASS (verify_log refuses when a record is duplicated)
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "test"), room_kp, &alice)?;
    room.join(&bob, "communicate", false)?;
    room.post(&bob, "msg A", "normal")?;

    let mut log = room.log();
    let dup = log.records.last().unwrap().clone();
    log.records.push(dup);

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_order_tail_of_another_rooms_log_joined_on() -> Result<()> {
    // Expected: PASS (verify_log refuses records grafted from another room)
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let room_a_kp = Keypair::generate();
    let room_b_kp = Keypair::generate();
    let mut room_a = Room::create(RoomTemplate::chat("t", "A"), room_a_kp, &alice)?;
    let mut room_b = Room::create(RoomTemplate::chat("t", "B"), room_b_kp, &alice)?;
    room_a.join(&bob, "communicate", false)?;
    room_b.join(&bob, "communicate", false)?;
    room_b.post(&bob, "from room B", "normal")?;

    let mut log_a = room_a.log();
    let log_b = room_b.log();
    log_a.records.push(log_b.records.last().unwrap().clone());

    assert!(verify_log(&log_a).is_err());
    Ok(())
}

// =====================================================================
// 3. CONTENT
// =====================================================================

#[test]
fn attack_content_message_text_changed_after_signing() -> Result<()> {
    // Expected: PASS (verify_log refuses a message whose text was modified after signing)
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "test"), room_kp, &alice)?;
    room.join(&bob, "communicate", false)?;
    room.post(&bob, "original text", "normal")?;

    let mut log = room.log();
    if let Record::Message(ref mut m) = log.records[2] {
        m.text = "tampered text".into();
    }

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_content_record_type_changed() -> Result<()> {
    // Expected: PASS (verify_log refuses when a signed Leave is re-tagged as another record type)
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "test"), room_kp.clone(), &alice)?;
    room.join(&bob, "communicate", false)?;
    room.leave(&bob)?;

    let mut log = room.log();
    let leave_rec = log.records.pop().unwrap();
    if let Record::Leave(l) = leave_rec {
        // Attempt to turn the Leave into a Bookmark carrying the same proofs
        let bm = Bookmark {
            world_id: l.world_id,
            seq: l.seq,
            prev: l.prev,
            room_id: l.subject_id,
            note: "".into(),
            ts: l.ts,
            proof: l.proof,
        };
        log.records.push(Record::Bookmark(bm));
    }

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_content_record_moved_to_another_world_id() -> Result<()> {
    // Expected: PASS (verify_log refuses when a record's world_id is rewritten to another room)
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let room_kp = Keypair::generate();
    let other_room_kp = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "test"), room_kp, &alice)?;
    room.join(&bob, "communicate", false)?;
    room.post(&bob, "hello", "normal")?;

    let mut log = room.log();
    if let Record::Message(ref mut m) = log.records[2] {
        m.world_id = other_room_kp.did();
    }

    assert!(verify_log(&log).is_err());
    Ok(())
}

// =====================================================================
// 4. RULES
// =====================================================================

#[test]
fn attack_rules_redaction_by_non_author_non_moderator() -> Result<()> {
    // Expected: PASS (verify_log refuses a hand-built Redact signed by a non-author communicate member)
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let mallory = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "test"), room_kp.clone(), &alice)?;
    room.join(&bob, "communicate", false)?;
    room.join(&mallory, "communicate", false)?;
    let msg = room.post(&bob, "bob's message", "normal")?;
    let msg_hash = msg.hash()?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut red = Redact::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        mallory.did(),
        msg_hash,
        "moderator".into(),
        "spam".into(),
        "forged redact".into(),
    );
    let wrapped = Record::Redact(red.clone());
    red.proof = sign_dual(&wrapped, &mallory, &room_kp);
    log.records.push(Record::Redact(red));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_rules_redaction_naming_disallowed_rule() -> Result<()> {
    // Expected: PASS (verify_log refuses a hand-built Redact naming a rule not in template.redaction_rules)
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "test"), room_kp.clone(), &alice)?;
    room.join(&bob, "communicate", false)?;
    let msg = room.post(&bob, "bob's message", "normal")?;
    let msg_hash = msg.hash()?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut red = Redact::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        bob.did(),
        msg_hash,
        "author".into(),
        "invented_rule".into(),
        "bad rule".into(),
    );
    let wrapped = Record::Redact(red.clone());
    red.proof = sign_dual(&wrapped, &bob, &room_kp);
    log.records.push(Record::Redact(red));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_rules_second_member_in_personal_room() -> Result<()> {
    // Expected: PASS (verify_log refuses a hand-built Join for a second member in a personal room)
    let alice = Keypair::generate();
    let intruder = Keypair::generate();
    let room_kp = Keypair::generate();
    let room = Room::create(
        RoomTemplate::personal_home("alice home"),
        room_kp.clone(),
        &alice,
    )?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut j = Join::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        intruder.did(),
        "communicate".into(),
        false,
    );
    let wrapped = Record::Join(j.clone());
    j.proof = sign_dual(&wrapped, &intruder, &room_kp);
    log.records.push(Record::Join(j));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_rules_rate_limit_bypassed_in_forged_log() -> Result<()> {
    // Expected: FAIL on current code (verify_log does not replay rate_limit_count/window!)
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.rate_limit_count = 2;
    template.rate_limit_window = 5;
    let mut room = Room::create(template, room_kp.clone(), &alice)?;
    room.join(&bob, "communicate", false)?;
    room.post(&bob, "one", "normal")?;
    room.post(&bob, "two", "normal")?;

    // Build a 3rd message by hand, bypassing Room::post's rate_ok check
    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut msg = Message::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        bob.did(),
        "three (exceeds rate limit)".into(),
        "normal".into(),
    );
    let wrapped = Record::Message(msg.clone());
    msg.proof = sign_dual(&wrapped, &bob, &room_kp);
    log.records.push(Record::Message(msg));

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_rules_human_only_room_with_forged_ai_join() -> Result<()> {
    // Expected: FAIL on current code (verify_log does not check template.membership on Join!)
    let alice = Keypair::generate();
    let ai = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.membership = "human_only".into();
    let room = Room::create(template, room_kp.clone(), &alice)?;

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut j = Join::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        ai.did(),
        "communicate".into(),
        true,
    );
    let wrapped = Record::Join(j.clone());
    j.proof = sign_dual(&wrapped, &ai, &room_kp);
    log.records.push(Record::Join(j));

    assert!(verify_log(&log).is_err());
    Ok(())
}

// =====================================================================
// 5. TEMPLATE
// =====================================================================

#[test]
fn attack_template_log_template_differs_from_room_created() -> Result<()> {
    // Expected: PASS (verify_log refuses when log.template differs from room_created.template)
    let alice = Keypair::generate();
    let room_kp = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "test"), room_kp, &alice)?;

    let mut log = room.log();
    log.template.moderation = "none".into();

    assert!(verify_log(&log).is_err());
    Ok(())
}

// =====================================================================
// 6. HEADS
// =====================================================================

#[test]
fn attack_heads_head_from_another_room() -> Result<()> {
    // Expected: PASS (verify_log refuses a head signed by another room)
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let room_a_kp = Keypair::generate();
    let room_b_kp = Keypair::generate();
    let mut t_a = RoomTemplate::chat("t", "A");
    t_a.head_interval = 2;
    let mut t_b = RoomTemplate::chat("t", "B");
    t_b.head_interval = 2;

    let mut room_a = Room::create(t_a, room_a_kp, &alice)?;
    let mut room_b = Room::create(t_b, room_b_kp, &alice)?;
    room_a.join(&bob, "communicate", false)?;
    room_a.post(&bob, "msg", "normal")?;
    room_b.join(&bob, "communicate", false)?;
    room_b.post(&bob, "msg", "normal")?;

    let mut log_a = room_a.log();
    log_a.heads[0] = room_b.log().heads[0].clone();

    assert!(verify_log(&log_a).is_err());
    Ok(())
}

#[test]
fn attack_heads_head_length_past_end_of_log() -> Result<()> {
    // Expected: PASS (verify_log refuses a head whose length exceeds records.len())
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.head_interval = 2;
    let mut room = Room::create(template, room_kp.clone(), &alice)?;
    room.join(&bob, "communicate", false)?;
    room.post(&bob, "msg", "normal")?;

    let mut log = room.log();
    let last_hash = log.records.last().unwrap().hash()?;
    let mut bad_head = WorldHead {
        format: HEAD_FORMAT_V1.into(),
        world: log.world_id.clone(),
        length: 99,
        last: last_hash,
        tick: 99,
        proof: ProofOrArray::placeholder(),
    };
    let body = body_for_signing(&bad_head)?;
    let sig = room_kp.sign(&body);
    bad_head.proof = ProofOrArray::single(Proof::create(&room_kp, &sig));
    log.heads[0] = bad_head;

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_heads_old_head_given_again_as_newest() -> Result<()> {
    // Expected: PASS (verify_log refuses when an older head is repeated at the end of heads)
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.head_interval = 2;
    let mut room = Room::create(template, room_kp, &alice)?;
    room.join(&bob, "communicate", false)?;
    room.post(&bob, "1", "normal")?;
    room.post(&bob, "2", "normal")?;
    room.post(&bob, "3", "normal")?;
    assert_eq!(room.heads().len(), 2);

    let mut log = room.log();
    let head0 = log.heads[0].clone();
    log.heads[1] = head0;

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_heads_head_in_per_record_mode_room() -> Result<()> {
    // Expected: PASS (verify_log refuses heads attached to a per-record mode room)
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "test"), room_kp, &alice)?;
    room.join(&bob, "communicate", false)?;
    let head = room.emit_head()?;

    let mut log = room.log();
    log.heads.push(head);

    assert!(verify_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_heads_unanchored_trailing_forged_record_in_head_mode() -> Result<()> {
    // Expected: FAIL on current code!
    // In head_interval = 3 mode, after 3 appends (4 records total), 1 head is emitted.
    // An attacker without the room key can take a valid member key (or forge a new Join
    // with a fresh keypair!) and append 1 record (5 records total, appends = 4, 4 / 3 == 1
    // expected head). Because per_record_mode is false, Join and Message do not require a
    // room proof, and the trailing record after the last head is never covered by any head!
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let mallory = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.head_interval = 3;
    let mut room = Room::create(template, room_kp, &alice)?;
    room.join(&bob, "communicate", false)?;
    room.post(&bob, "one", "normal")?;
    room.post(&bob, "two", "normal")?;
    assert_eq!(room.heads().len(), 1);

    let mut log = room.log();
    let prev = log.records.last().unwrap().hash()?;
    // Mallory forges a self-signed Join at the tail without the room's key or a covering head!
    let mut forged_join = Join::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        mallory.did(),
        "terminal".into(),
        false,
    );
    let wrapped = Record::Join(forged_join.clone());
    forged_join.proof = sign_single(&wrapped, &mallory);
    log.records.push(Record::Join(forged_join));

    assert!(verify_log(&log).is_err());
    Ok(())
}
