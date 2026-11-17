use chat_world::commons::{
    verify_commons_log, Commons, CommonsLog, CommonsRecord, RoomRegistered,
};
use chat_world::error::Result;
use chat_world::hash::body_for_signing;
use chat_world::{Keypair, Proof, ProofOrArray, Room, RoomTemplate};

fn make_registered_room(alice: &Keypair) -> Room {
    let room_kp = Keypair::generate();
    Room::create(RoomTemplate::chat("t", "test"), room_kp, alice).unwrap()
}

// =====================================================================
// 1. PROOFS
// =====================================================================

#[test]
fn attack_proofs_registration_without_commons_proof() -> Result<()> {
    // Expected: PASS (verify_commons_log refuses a registration missing the Commons' proof)
    let alice = Keypair::generate();
    let commons_kp = Keypair::generate();
    let room = make_registered_room(&alice);
    let mut commons = Commons::new(commons_kp);
    commons.register_room(&room, &alice, None)?;

    let mut log: CommonsLog = commons.log();
    if let CommonsRecord::RoomRegistered(ref mut r) = log.records[0] {
        let body = body_for_signing(r)?;
        let sig = alice.sign(&body);
        r.proof = ProofOrArray::single(Proof::create(&alice, &sig));
    }

    assert!(verify_commons_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_proofs_registration_without_registrant_proof() -> Result<()> {
    // Expected: PASS (verify_commons_log refuses a registration missing the registrant's proof)
    let alice = Keypair::generate();
    let commons_kp = Keypair::generate();
    let room = make_registered_room(&alice);
    let mut commons = Commons::new(commons_kp.clone());
    commons.register_room(&room, &alice, None)?;

    let mut log: CommonsLog = commons.log();
    if let CommonsRecord::RoomRegistered(ref mut r) = log.records[0] {
        let body = body_for_signing(r)?;
        let sig = commons_kp.sign(&body);
        r.proof = ProofOrArray::single(Proof::create(&commons_kp, &sig));
    }

    assert!(verify_commons_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_proofs_moved_from_one_record_to_another() -> Result<()> {
    // Expected: PASS (verify_commons_log refuses when proofs are transplanted between records)
    let alice = Keypair::generate();
    let commons_kp = Keypair::generate();
    let room1 = make_registered_room(&alice);
    let room2 = make_registered_room(&alice);
    let mut commons = Commons::new(commons_kp);
    commons.register_room(&room1, &alice, Some("topic 1".into()))?;
    commons.register_room(&room2, &alice, Some("topic 2".into()))?;

    let mut log: CommonsLog = commons.log();
    let first_proof = log.records[0].proof().clone();
    if let CommonsRecord::RoomRegistered(ref mut r2) = log.records[1] {
        r2.proof = first_proof;
    }

    assert!(verify_commons_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_proofs_registration_signed_by_wrong_registrant_key() -> Result<()> {
    // Expected: PASS (verify_commons_log refuses when registered_by is alice but signed by mallory)
    let alice = Keypair::generate();
    let mallory = Keypair::generate();
    let commons_kp = Keypair::generate();
    let room = make_registered_room(&alice);
    let mut commons = Commons::new(commons_kp.clone());
    commons.register_room(&room, &alice, None)?;

    let mut log: CommonsLog = commons.log();
    if let CommonsRecord::RoomRegistered(ref mut r) = log.records[0] {
        let body = body_for_signing(r)?;
        let mallory_sig = mallory.sign(&body);
        let commons_sig = commons_kp.sign(&body);
        r.proof = ProofOrArray::array(vec![
            Proof::create(&mallory, &mallory_sig),
            Proof::create(&commons_kp, &commons_sig),
        ]);
    }

    assert!(verify_commons_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_proofs_sibling_without_sibling_proof() -> Result<()> {
    // Expected: PASS (verify_commons_log refuses a sibling declaration missing sibling_id's proof)
    let parent = Keypair::generate();
    let sibling = Keypair::generate();
    let commons_kp = Keypair::generate();
    let parent_kw_id = Keypair::generate().did();
    let mut commons = Commons::new(commons_kp.clone());
    let shard = "00".repeat(32);
    commons.declare_sibling(&parent, &sibling, &parent_kw_id, &shard, "graduation")?;

    let mut log: CommonsLog = commons.log();
    if let CommonsRecord::SiblingDeclared(ref mut s) = log.records[0] {
        let body = body_for_signing(s)?;
        let p_sig = parent.sign(&body);
        let c_sig = commons_kp.sign(&body);
        s.proof = ProofOrArray::array(vec![
            Proof::create(&parent, &p_sig),
            Proof::create(&commons_kp, &c_sig),
        ]);
    }

    assert!(verify_commons_log(&log).is_err());
    Ok(())
}

// =====================================================================
// 2. ORDER
// =====================================================================

#[test]
fn attack_order_two_records_swapped() -> Result<()> {
    // Expected: PASS (verify_commons_log refuses when two records are swapped)
    let alice = Keypair::generate();
    let commons_kp = Keypair::generate();
    let room1 = make_registered_room(&alice);
    let room2 = make_registered_room(&alice);
    let mut commons = Commons::new(commons_kp);
    commons.register_room(&room1, &alice, None)?;
    commons.register_room(&room2, &alice, None)?;

    let mut log: CommonsLog = commons.log();
    log.records.swap(0, 1);

    assert!(verify_commons_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_order_record_dropped_from_middle() -> Result<()> {
    // Expected: PASS (verify_commons_log refuses when a middle record is dropped)
    let alice = Keypair::generate();
    let commons_kp = Keypair::generate();
    let room1 = make_registered_room(&alice);
    let room2 = make_registered_room(&alice);
    let room3 = make_registered_room(&alice);
    let mut commons = Commons::new(commons_kp);
    commons.register_room(&room1, &alice, None)?;
    commons.register_room(&room2, &alice, None)?;
    commons.register_room(&room3, &alice, None)?;

    let mut log: CommonsLog = commons.log();
    log.records.remove(1);

    assert!(verify_commons_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_order_record_repeated() -> Result<()> {
    // Expected: PASS (verify_commons_log refuses when a record is duplicated)
    let alice = Keypair::generate();
    let commons_kp = Keypair::generate();
    let room1 = make_registered_room(&alice);
    let mut commons = Commons::new(commons_kp);
    commons.register_room(&room1, &alice, None)?;

    let mut log: CommonsLog = commons.log();
    let dup = log.records[0].clone();
    log.records.push(dup);

    assert!(verify_commons_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_order_record_seq_not_its_place() -> Result<()> {
    // Expected: FAIL on current code (verify_commons_log does not check rec.seq() == i as u64!)
    let alice = Keypair::generate();
    let commons_kp = Keypair::generate();
    let room = make_registered_room(&alice);
    let seed_hash = room.records().first().unwrap().hash()?;

    let mut bad_reg = RoomRegistered {
        type_: "room_registered".into(),
        commons_id: commons_kp.did(),
        seq: 99, // Wrong seq for index 0!
        prev: None,
        room_id: room.world_id().clone(),
        topic: room.template().topic.clone(),
        template_hash: room.template().hash()?,
        room_seed_hash: seed_hash,
        registered_by: alice.did(),
        also_listed_in: Vec::new(),
        ts: chat_world::now(),
        proof: ProofOrArray::placeholder(),
    };
    let body = body_for_signing(&bad_reg)?;
    let reg_sig = alice.sign(&body);
    let com_sig = commons_kp.sign(&body);
    bad_reg.proof = ProofOrArray::array(vec![
        Proof::create(&alice, &reg_sig),
        Proof::create(&commons_kp, &com_sig),
    ]);

    let log = CommonsLog {
        commons_id: commons_kp.did(),
        records: vec![CommonsRecord::RoomRegistered(bad_reg)],
    };

    assert!(verify_commons_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_order_tail_of_another_commons_log_joined_on() -> Result<()> {
    // Expected: PASS (verify_commons_log refuses records grafted from another Commons)
    let alice = Keypair::generate();
    let commons_a = Commons::new(Keypair::generate());
    let mut commons_b = Commons::new(Keypair::generate());
    let room_a = make_registered_room(&alice);
    let room_b = make_registered_room(&alice);

    let mut commons_a = commons_a;
    commons_a.register_room(&room_a, &alice, None)?;
    commons_b.register_room(&room_b, &alice, None)?;

    let mut log_a: CommonsLog = commons_a.log();
    let log_b: CommonsLog = commons_b.log();
    log_a.records.push(log_b.records[0].clone());

    assert!(verify_commons_log(&log_a).is_err());
    Ok(())
}

// =====================================================================
// 3. CONTENT
// =====================================================================

#[test]
fn attack_content_topic_changed_after_signing() -> Result<()> {
    // Expected: PASS (verify_commons_log refuses when topic is mutated after signing)
    let alice = Keypair::generate();
    let commons_kp = Keypair::generate();
    let room = make_registered_room(&alice);
    let mut commons = Commons::new(commons_kp);
    commons.register_room(&room, &alice, Some("honest topic".into()))?;

    let mut log: CommonsLog = commons.log();
    if let CommonsRecord::RoomRegistered(ref mut r) = log.records[0] {
        r.topic = "tampered topic".into();
    }

    assert!(verify_commons_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_content_room_id_changed_after_signing() -> Result<()> {
    // Expected: PASS (verify_commons_log refuses when room_id is mutated after signing)
    let alice = Keypair::generate();
    let commons_kp = Keypair::generate();
    let room = make_registered_room(&alice);
    let mut commons = Commons::new(commons_kp);
    commons.register_room(&room, &alice, None)?;

    let mut log: CommonsLog = commons.log();
    if let CommonsRecord::RoomRegistered(ref mut r) = log.records[0] {
        r.room_id = Keypair::generate().did();
    }

    assert!(verify_commons_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_content_record_moved_to_another_commons_id() -> Result<()> {
    // Expected: PASS (verify_commons_log refuses when a record's commons_id is rewritten)
    let alice = Keypair::generate();
    let commons_kp = Keypair::generate();
    let room = make_registered_room(&alice);
    let mut commons = Commons::new(commons_kp);
    commons.register_room(&room, &alice, None)?;

    let mut log: CommonsLog = commons.log();
    if let CommonsRecord::RoomRegistered(ref mut r) = log.records[0] {
        r.commons_id = Keypair::generate().did();
    }

    assert!(verify_commons_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_content_log_commons_id_differs_from_records() -> Result<()> {
    // Expected: PASS (verify_commons_log refuses when CommonsLog.commons_id does not match its records)
    let alice = Keypair::generate();
    let commons_kp = Keypair::generate();
    let room = make_registered_room(&alice);
    let mut commons = Commons::new(commons_kp);
    commons.register_room(&room, &alice, None)?;

    let mut log: CommonsLog = commons.log();
    log.commons_id = Keypair::generate().did();

    assert!(verify_commons_log(&log).is_err());
    Ok(())
}

// =====================================================================
// 4. MEANING
// =====================================================================

#[test]
fn attack_meaning_same_room_registered_twice() -> Result<()> {
    // Expected: FAIL on current code (neither register_room nor verify_commons_log refuses duplicate room_id!)
    let alice = Keypair::generate();
    let commons_kp = Keypair::generate();
    let room = make_registered_room(&alice);
    let mut commons = Commons::new(commons_kp);
    commons.register_room(&room, &alice, Some("first listing".into()))?;
    let _ = commons.register_room(&room, &alice, Some("duplicate listing".into()));

    // Even if register_room is later guarded, build the duplicate directly in a CommonsLog
    // if needed; here register_room itself currently appends the duplicate record.
    let log: CommonsLog = commons.log();
    assert_eq!(log.records.len(), 2);

    assert!(verify_commons_log(&log).is_err());
    Ok(())
}

#[test]
fn attack_meaning_same_sibling_declared_twice() -> Result<()> {
    // Expected: FAIL on current code (verify_commons_log does not refuse duplicate sibling_id declarations!)
    let parent = Keypair::generate();
    let sibling = Keypair::generate();
    let commons_kp = Keypair::generate();
    let parent_kw_id = Keypair::generate().did();
    let mut commons = Commons::new(commons_kp);
    let shard = "00".repeat(32);
    commons.declare_sibling(&parent, &sibling, &parent_kw_id, &shard, "first")?;
    let _ = commons.declare_sibling(&parent, &sibling, &parent_kw_id, &shard, "duplicate");

    let log: CommonsLog = commons.log();
    assert_eq!(log.records.len(), 2);

    assert!(verify_commons_log(&log).is_err());
    Ok(())
}
