use chat_world::commons::{
    verify_registration, verify_sibling, Commons, RoomRegistered,
};
use chat_world::error::Result;
use chat_world::hash::body_for_signing;
use chat_world::home::HomeRoom;
use chat_world::{Keypair, Proof, ProofOrArray, Room, RoomTemplate};

#[test]
fn honest_registration_verifies_across_logs_for_creator_and_member() -> Result<()> {
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "test"), room_kp, &alice)?;
    room.join(&bob, "communicate", false)?;

    // Registered by creator (alice)
    let mut commons1 = Commons::new(Keypair::generate());
    let reg_alice = commons1.register_room(&room, &alice, None)?;
    verify_registration(&reg_alice, &room.log())?;

    // Registered by another member in the room (bob)
    let mut commons2 = Commons::new(Keypair::generate());
    let reg_bob = commons2.register_room(&room, &bob, None)?;
    verify_registration(&reg_bob, &room.log())?;

    Ok(())
}

#[test]
fn registration_refused_when_registrant_was_never_in_room() -> Result<()> {
    let alice = Keypair::generate();
    let stranger = Keypair::generate();
    let room_kp = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "test"), room_kp, &alice)?;

    let mut commons = Commons::new(Keypair::generate());
    let reg = commons.register_room(&room, &stranger, None)?;

    assert!(verify_registration(&reg, &room.log()).is_err());
    Ok(())
}

#[test]
fn registration_refused_when_checked_against_wrong_room_log() -> Result<()> {
    let alice = Keypair::generate();
    let room1 = Room::create(RoomTemplate::chat("t", "one"), Keypair::generate(), &alice)?;
    let room2 = Room::create(RoomTemplate::chat("t", "two"), Keypair::generate(), &alice)?;

    let mut commons = Commons::new(Keypair::generate());
    let reg1 = commons.register_room(&room1, &alice, None)?;

    assert!(verify_registration(&reg1, &room2.log()).is_err());
    Ok(())
}

#[test]
fn registration_refused_when_template_hash_or_seed_hash_forged() -> Result<()> {
    let alice = Keypair::generate();
    let commons_kp = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "test"), Keypair::generate(), &alice)?;
    let seed_hash = room.records().first().unwrap().hash()?;

    // Forged template_hash signed by both alice and commons_kp
    let mut bad_tpl = RoomRegistered {
        type_: "room_registered".into(),
        commons_id: commons_kp.did(),
        seq: 0,
        prev: None,
        room_id: room.world_id().clone(),
        topic: "test".into(),
        template_hash: "11".repeat(32),
        room_seed_hash: seed_hash,
        registered_by: alice.did(),
        also_listed_in: Vec::new(),
        ts: chat_world::now(),
        proof: ProofOrArray::placeholder(),
    };
    let body1 = body_for_signing(&bad_tpl)?;
    bad_tpl.proof = ProofOrArray::array(vec![
        Proof::create(&alice, &alice.sign(&body1)),
        Proof::create(&commons_kp, &commons_kp.sign(&body1)),
    ]);
    assert!(verify_registration(&bad_tpl, &room.log()).is_err());

    // Forged room_seed_hash signed by both alice and commons_kp
    let mut bad_seed = RoomRegistered {
        type_: "room_registered".into(),
        commons_id: commons_kp.did(),
        seq: 0,
        prev: None,
        room_id: room.world_id().clone(),
        topic: "test".into(),
        template_hash: room.template().hash()?,
        room_seed_hash: "22".repeat(32),
        registered_by: alice.did(),
        also_listed_in: Vec::new(),
        ts: chat_world::now(),
        proof: ProofOrArray::placeholder(),
    };
    let body2 = body_for_signing(&bad_seed)?;
    bad_seed.proof = ProofOrArray::array(vec![
        Proof::create(&alice, &alice.sign(&body2)),
        Proof::create(&commons_kp, &commons_kp.sign(&body2)),
    ]);
    assert!(verify_registration(&bad_seed, &room.log()).is_err());

    Ok(())
}

#[test]
fn honest_sibling_verifies_across_logs() -> Result<()> {
    let parent_kp = Keypair::generate();
    let sibling_kp = Keypair::generate();
    let kw_room_kp = Keypair::generate();
    let commons_kp = Keypair::generate();

    let mut parent_kw = HomeRoom::create(parent_kp.clone(), kw_room_kp, "parent kw")?;
    let obs = parent_kw.journal("observation 1")?;
    let obs_hash = obs.hash()?;
    let target_room = Keypair::generate().did();
    let export = parent_kw.emit_shard_export(&target_room, &sibling_kp.did(), vec![obs_hash])?;
    let shard_hash = export.hash()?;

    let mut commons = Commons::new(commons_kp);
    let sib = commons.declare_sibling(
        &parent_kp,
        &sibling_kp,
        parent_kw.room().world_id(),
        &shard_hash,
        "graduation",
    )?;

    verify_sibling(&sib, &parent_kw.room().log())
}

#[test]
fn sibling_refused_when_shard_hash_missing_from_parent_kw() -> Result<()> {
    let parent_kp = Keypair::generate();
    let sibling_kp = Keypair::generate();
    let kw_room_kp = Keypair::generate();
    let commons_kp = Keypair::generate();

    let mut parent_kw = HomeRoom::create(parent_kp.clone(), kw_room_kp, "parent kw")?;
    parent_kw.journal("observation 1")?;

    let mut commons = Commons::new(commons_kp);
    let fake_shard = "aa".repeat(32);
    let sib = commons.declare_sibling(
        &parent_kp,
        &sibling_kp,
        parent_kw.room().world_id(),
        &fake_shard,
        "graduation",
    )?;

    assert!(verify_sibling(&sib, &parent_kw.room().log()).is_err());
    Ok(())
}

#[test]
fn sibling_refused_when_parent_room_is_not_personal_or_wrong_owner() -> Result<()> {
    let parent_kp = Keypair::generate();
    let impostor_kp = Keypair::generate();
    let sibling_kp = Keypair::generate();
    let commons_kp = Keypair::generate();

    // Case 1: parent_kw_id points to a non-personal chat room
    let normal_room = Room::create(
        RoomTemplate::chat("t", "normal"),
        Keypair::generate(),
        &parent_kp,
    )?;
    let mut commons = Commons::new(commons_kp);
    let sib1 = commons.declare_sibling(
        &parent_kp,
        &sibling_kp,
        normal_room.world_id(),
        &"bb".repeat(32),
        "graduation",
    )?;
    assert!(verify_sibling(&sib1, &normal_room.log()).is_err());

    // Case 2: personal room owned by impostor_kp rather than parent_kp
    let mut impostor_kw = HomeRoom::create(impostor_kp, Keypair::generate(), "impostor kw")?;
    let obs = impostor_kw.journal("obs")?;
    let export = impostor_kw.emit_shard_export(
        &Keypair::generate().did(),
        &sibling_kp.did(),
        vec![obs.hash()?],
    )?;
    let sib2 = commons.declare_sibling(
        &parent_kp,
        &sibling_kp,
        impostor_kw.room().world_id(),
        &export.hash()?,
        "graduation",
    )?;
    assert!(verify_sibling(&sib2, &impostor_kw.room().log()).is_err());

    Ok(())
}
