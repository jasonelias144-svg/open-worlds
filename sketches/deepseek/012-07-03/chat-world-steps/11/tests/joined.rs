use chat_world::error::Result;
use chat_world::hash::body_for_signing;
use chat_world::joined_room::JoinedRoom;
use chat_world::record::*;
use chat_world::verify::verify_log;
use chat_world::{Keypair, Proof, ProofOrArray, Room, RoomLog, RoomTemplate};

fn make_head_mode_room(interval: u64) -> Room {
    let alice = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.head_interval = interval;
    Room::create(template, room_kp, &alice).unwrap()
}

fn sign_single(rec: &Record, signer: &Keypair) -> ProofOrArray {
    let body = body_for_signing(rec).unwrap();
    let sig = signer.sign(&body);
    ProofOrArray::Single(Proof::create(signer, &sig))
}

#[test]
fn join_and_post_roundtrip() -> Result<()> {
    let mut alice_room = make_head_mode_room(2);
    let bob = Keypair::generate();

    let mut joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
    assert!(!joined.is_member());
    joined.request_join("communicate", false)?;
    joined.post("hello from bob", "normal")?;
    joined.verify_pending()?;
    assert!(joined.is_member());

    let outcomes = alice_room.accept_pending(&joined.export_pending())?;
    assert_eq!(outcomes.len(), 2);
    assert!(outcomes.iter().all(|o| o.accepted));

    verify_log(&alice_room.log())?;
    Ok(())
}

#[test]
fn joined_room_refuses_per_record_mode() -> Result<()> {
    let mut alice_room = make_head_mode_room(1);
    let bob = Keypair::generate();
    let mut joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
    let r = joined.request_join("communicate", false);
    assert!(r.is_err());
    Ok(())
}

#[test]
fn accept_pending_refuses_per_record_mode() -> Result<()> {
    let mut alice_room = make_head_mode_room(1);
    let batch: Vec<Record> = vec![];
    let r = alice_room.accept_pending(&batch);
    assert!(r.is_err());
    Ok(())
}

#[test]
fn non_member_post_is_refused() -> Result<()> {
    let mut alice_room = make_head_mode_room(2);
    let bob = Keypair::generate();
    let mut joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
    let r = joined.post("hello", "normal");
    assert!(r.is_err());
    Ok(())
}

#[test]
fn rate_limit_is_refused_by_keeper() -> Result<()> {
    let alice = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.head_interval = 5;
    template.rate_limit_count = 1;
    template.rate_limit_window = 5;
    let mut alice_room = Room::create(template, Keypair::generate(), &alice)?;
    let bob = Keypair::generate();

    let mut joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
    joined.request_join("communicate", false)?;
    joined.post("first", "normal")?;
    joined.post("second", "normal")?;
    joined.verify_pending()?;
    let outcomes = alice_room.accept_pending(&joined.export_pending())?;
    assert_eq!(outcomes.len(), 3);
    assert!(outcomes[0].accepted, "join should be accepted");
    assert!(outcomes[1].accepted, "first message should be accepted");
    assert!(!outcomes[2].accepted, "second message should be refused");
    assert_eq!(outcomes[2].reason.as_deref(), Some("rate_limit"));
    Ok(())
}

#[test]
fn refusal_consumes_seq_keeping_batch_aligned() -> Result<()> {
    let alice = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.head_interval = 5;
    template.rate_limit_count = 1;
    template.rate_limit_window = 100;
    let mut alice_room = Room::create(template, Keypair::generate(), &alice)?;
    let bob = Keypair::generate();

    let mut joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
    joined.request_join("communicate", false)?;
    joined.post("first", "normal")?;
    joined.post("second (refused)", "normal")?;
    joined.post("third (accepted)", "normal")?;
    let outcomes = alice_room.accept_pending(&joined.export_pending())?;
    assert_eq!(outcomes.len(), 4);
    assert!(outcomes[0].accepted);
    assert!(outcomes[1].accepted);
    assert!(!outcomes[2].accepted);
    assert!(outcomes[3].accepted);

    verify_log(&alice_room.log())?;
    Ok(())
}

#[test]
fn tampered_pending_breaks_proof() -> Result<()> {
    let mut alice_room = make_head_mode_room(2);
    let bob = Keypair::generate();
    let mut joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
    joined.request_join("communicate", false)?;
    joined.post("hello", "normal")?;

    let mut batch = joined.export_pending();
    if let Record::Message(ref mut m) = batch[1] {
        m.text = "tampered".into();
    }
    let r = alice_room.accept_pending(&batch);
    assert!(r.is_err(), "tampered pending should error, not refuse");
    Ok(())
}

#[test]
fn join_then_post_in_separate_batches() -> Result<()> {
    let mut alice_room = make_head_mode_room(3);
    let bob = Keypair::generate();

    {
        let mut joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
        joined.request_join("communicate", false)?;
        let outcomes = alice_room.accept_pending(&joined.export_pending())?;
        assert_eq!(outcomes.len(), 1);
        assert!(outcomes[0].accepted);
    }

    {
        let mut joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
        assert!(joined.is_member());
        joined.post("hello from a second batch", "normal")?;
        let outcomes = alice_room.accept_pending(&joined.export_pending())?;
        assert_eq!(outcomes.len(), 1);
        assert!(outcomes[0].accepted);
    }

    verify_log(&alice_room.log())?;
    Ok(())
}

#[test]
fn join_refused_when_already_member() -> Result<()> {
    let alice = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.head_interval = 5;
    let mut alice_room = Room::create(template, room_kp, &alice)?;
    let bob = Keypair::generate();

    {
        let mut joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
        joined.request_join("communicate", false)?;
        alice_room.accept_pending(&joined.export_pending())?;
    }

    let joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
    assert!(joined.is_member());
    let mut joined_mut = joined;
    let r = joined_mut.request_join("communicate", false);
    assert!(r.is_err());
    Ok(())
}

#[test]
fn leave_via_pending() -> Result<()> {
    let alice = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.head_interval = 5;
    let mut alice_room = Room::create(template, Keypair::generate(), &alice)?;
    let bob = Keypair::generate();

    {
        let mut joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
        joined.request_join("communicate", false)?;
        alice_room.accept_pending(&joined.export_pending())?;
    }

    {
        let mut joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
        assert!(joined.is_member());
        joined.leave()?;
        let outcomes = alice_room.accept_pending(&joined.export_pending())?;
        assert!(outcomes[0].accepted);
    }

    let joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
    assert!(!joined.is_member());
    verify_log(&alice_room.log())?;
    Ok(())
}

#[test]
fn invalid_log_refused_at_attach() -> Result<()> {
    let mut alice_room = make_head_mode_room(2);
    let bob = Keypair::generate();
    let mut log = alice_room.log();
    log.heads.clear();
    let r = JoinedRoom::from_log(log, bob);
    assert!(r.is_err());
    Ok(())
}

// ---- The fix: accept_one now refuses malformed Redact / HumanOverride ----

#[test]
fn forged_redact_wrong_role_refused() -> Result<()> {
    // Bob is a member but not the message's author and not a
    // moderator. Forge a Redact claiming the "author" role; the
    // keeper must refuse it (not silently commit it).
    let alice = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.head_interval = 5;
    let mut alice_room = Room::create(template, Keypair::generate(), &alice)?;

    // Alice posts a message.
    alice_room.post(&alice, "alice's message", "normal")?;
    let alice_msg_hash = alice_room.records().last().unwrap().hash()?;

    // Bob joins.
    let bob = Keypair::generate();
    {
        let mut joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
        joined.request_join("communicate", false)?;
        alice_room.accept_pending(&joined.export_pending())?;
    }

    // Bob forges a Redact claiming "author" role on Alice's message.
    let mut log = alice_room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut forged = Redact::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        bob.did(),
        alice_msg_hash,
        "author".into(),   // <-- false: Bob isn't the author
        "harassment".into(),
        "forged".into(),
    );
    let wrapped = Record::Redact(forged.clone());
    forged.proof = sign_single(&wrapped, &bob);

    let outcomes = alice_room.accept_pending(&[Record::Redact(forged)])?;
    assert_eq!(outcomes.len(), 1);
    assert!(!outcomes[0].accepted, "forged redact must be refused");
    assert_eq!(outcomes[0].reason.as_deref(), Some("not_allowed"));

    verify_log(&alice_room.log())?;
    Ok(())
}

#[test]
fn forged_override_by_ai_refused() -> Result<()> {
    let alice = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.head_interval = 5;
    let mut alice_room = Room::create(template, Keypair::generate(), &alice)?;

    // Alice posts; her record is a valid override target for an AI
    // override only if the target is AI-authored. Here we use an
    // AI-authored target.
    let ai = Keypair::generate();
    {
        let mut joined = JoinedRoom::from_log(alice_room.log(), ai.clone())?;
        joined.request_join("communicate", true)?;
        joined.post("an AI observation", "normal")?;
        alice_room.accept_pending(&joined.export_pending())?;
    }
    let ai_msg_hash = alice_room.records().last().unwrap().hash()?;

    // Another AI tries to override. Only humans can override.
    let ai2 = Keypair::generate();
    {
        let mut joined = JoinedRoom::from_log(alice_room.log(), ai2.clone())?;
        joined.request_join("control", true)?;
        alice_room.accept_pending(&joined.export_pending())?;
    }

    let mut log = alice_room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut forged = HumanOverride::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        ai_msg_hash,
        ai2.did(),
        "none".into(),
        "forged override".into(),
    );
    let wrapped = Record::HumanOverride(forged.clone());
    forged.proof = sign_single(&wrapped, &ai2);

    let outcomes = alice_room.accept_pending(&[Record::HumanOverride(forged)])?;
    assert_eq!(outcomes.len(), 1);
    assert!(!outcomes[0].accepted, "AI override must be refused");
    assert_eq!(outcomes[0].reason.as_deref(), Some("only_humans_can_override"));

    verify_log(&alice_room.log())?;
    Ok(())
}

#[test]
fn override_target_must_be_ai_author() -> Result<()> {
    let alice = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.head_interval = 5;
    let mut alice_room = Room::create(template, Keypair::generate(), &alice)?;
    // Alice posts (human-authored).
    let alice_msg = alice_room.post(&alice, "alice's message", "normal")?;
    let alice_msg_hash = alice_msg.hash()?;

    // A second human joins at control and forges an override
    // targeting Alice's human-authored message.
    let carol = Keypair::generate();
    {
        let mut joined = JoinedRoom::from_log(alice_room.log(), carol.clone())?;
        joined.request_join("control", false)?;
        alice_room.accept_pending(&joined.export_pending())?;
    }
    let mut log = alice_room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut forged = HumanOverride::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        alice_msg_hash,
        carol.did(),
        "none".into(),
        "forged".into(),
    );
    let wrapped = Record::HumanOverride(forged.clone());
    forged.proof = sign_single(&wrapped, &carol);

    let outcomes = alice_room.accept_pending(&[Record::HumanOverride(forged)])?;
    assert_eq!(outcomes.len(), 1);
    assert!(!outcomes[0].accepted);
    assert_eq!(outcomes[0].reason.as_deref(), Some("override_target_must_be_ai"));
    Ok(())
}

#[test]
fn port_landing_refused_in_chat_room() -> Result<()> {
    // A PortLanding is personal-only. A participant who tries to
    // submit one to a chat room gets a refusal.
    let alice = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.head_interval = 5;
    let mut alice_room = Room::create(template, Keypair::generate(), &alice)?;
    let bob = Keypair::generate();
    {
        let mut joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
        joined.request_join("communicate", false)?;
        alice_room.accept_pending(&joined.export_pending())?;
    }

    let transcript = chat_world::transcript::sign_transcript(
        "ext",
        vec![chat_world::transcript::TranscriptEntry {
            speaker: "u".into(),
            ts: chat_world::now(),
            text: "hi".into(),
        }],
        &bob,
    )?;

    let mut log = alice_room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut forged = PortLanding::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        transcript,
        "journal".into(),
        None,
    );
    let wrapped = Record::PortLanding(forged.clone());
    forged.proof = sign_single(&wrapped, &bob);

    let outcomes = alice_room.accept_pending(&[Record::PortLanding(forged)])?;
    assert_eq!(outcomes.len(), 1);
    assert!(!outcomes[0].accepted);
    assert_eq!(outcomes[0].reason.as_deref(), Some("not_valid_in_chat_room"));
    Ok(())
}

// ---- Head-mode coverage: legitimate redact, override, succession ----

#[test]
fn head_mode_author_redacts_own_message() -> Result<()> {
    let mut alice_room = make_head_mode_room(3);
    let bob = Keypair::generate();
    let msg_hash = {
        let mut joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
        joined.request_join("communicate", false)?;
        let msg = joined.post("oops", "normal")?;
        let h = msg.hash()?;
        alice_room.accept_pending(&joined.export_pending())?;
        h
    };

    // Bob redacts his own message via pending.
    {
        let mut joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
        // Local JoinedRoom has no redact method; forge it with the
        // right shape (author role on own message) and submit.
        let log = joined.log();
        let prev = log.records.last().unwrap().hash()?;
        let mut red = Redact::new(
            log.world_id.clone(),
            log.records.len() as u64,
            Some(prev),
            bob.did(),
            msg_hash,
            "author".into(),
            "author_request".into(),
            "my bad".into(),
        );
        let wrapped = Record::Redact(red.clone());
        red.proof = sign_single(&wrapped, &bob);
        let outcomes = alice_room.accept_pending(&[Record::Redact(red)])?;
        assert_eq!(outcomes.len(), 1);
        assert!(outcomes[0].accepted);
    }

    verify_log(&alice_room.log())?;
    Ok(())
}

#[test]
fn head_mode_human_override_of_ai_works() -> Result<()> {
    let alice = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.head_interval = 3;
    let mut alice_room = Room::create(template, Keypair::generate(), &alice)?;

    // AI joins and posts.
    let ai = Keypair::generate();
    {
        let mut joined = JoinedRoom::from_log(alice_room.log(), ai.clone())?;
        joined.request_join("communicate", true)?;
        joined.post("an AI note", "normal")?;
        alice_room.accept_pending(&joined.export_pending())?;
    }
    let ai_msg_hash = alice_room.records().last().unwrap().hash()?;

    // A human at control overrides.
    let human = Keypair::generate();
    {
        let mut joined = JoinedRoom::from_log(alice_room.log(), human.clone())?;
        joined.request_join("control", false)?;
        alice_room.accept_pending(&joined.export_pending())?;
    }

    let log = alice_room.log();
    let prev = log.records.last().unwrap().hash()?;
    let mut ov = HumanOverride::new(
        log.world_id.clone(),
        log.records.len() as u64,
        Some(prev),
        ai_msg_hash,
        human.did(),
        "none".into(),
        "good note".into(),
    );
    let wrapped = Record::HumanOverride(ov.clone());
    ov.proof = sign_single(&wrapped, &human);
    let outcomes = alice_room.accept_pending(&[Record::HumanOverride(ov)])?;
    assert_eq!(outcomes.len(), 1);
    assert!(outcomes[0].accepted);

    verify_log(&alice_room.log())?;
    Ok(())
}
