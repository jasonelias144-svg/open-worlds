use chat_world::error::Result;
use chat_world::joined_room::JoinedRoom;
use chat_world::record::Record;
use chat_world::verify::verify_log;
use chat_world::{Keypair, Room, RoomTemplate};

fn make_head_mode_room(interval: u64) -> Room {
    let alice = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.head_interval = interval;
    Room::create(template, room_kp, &alice).unwrap()
}

#[test]
fn join_and_post_roundtrip() -> Result<()> {
    let mut alice_room = make_head_mode_room(2);
    let bob = Keypair::generate();

    // Alice publishes; Bob attaches.
    let mut joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
    assert!(!joined.is_member());

    // Bob joins and posts.
    joined.request_join("communicate", false)?;
    joined.post("hello from bob", "normal")?;
    joined.verify_pending()?;
    assert!(joined.is_member());

    // Alice accepts.
    let outcomes = alice_room.accept_pending(&joined.export_pending())?;
    assert_eq!(outcomes.len(), 2);
    assert!(outcomes.iter().all(|o| o.accepted));

    // New log verifies.
    let new_log = alice_room.log();
    verify_log(&new_log)?;
    Ok(())
}

#[test]
fn joined_room_refuses_per_record_mode() -> Result<()> {
    let mut alice_room = make_head_mode_room(1);  // per-record mode
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
    // No request_join; post should fail locally.
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
    // Local verify_pending passes (no policy checks); keeper refuses.
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
    // A refusal in the middle of a batch must not knock the rest
    // of the batch off its seq numbering.
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
    assert!(!outcomes[2].accepted);   // rate limit
    assert!(outcomes[3].accepted);    // third record still lines up

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
    // Tamper the message's text.
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

    // First batch: join only.
    {
        let mut joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
        joined.request_join("communicate", false)?;
        let outcomes = alice_room.accept_pending(&joined.export_pending())?;
        assert_eq!(outcomes.len(), 1);
        assert!(outcomes[0].accepted);
    }

    // Second batch: post only.
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

    // Bob joins via pending.
    {
        let mut joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
        joined.request_join("communicate", false)?;
        alice_room.accept_pending(&joined.export_pending())?;
    }

    // Now he is a member; his re-attached JoinedRoom reflects that.
    let joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
    assert!(joined.is_member());

    // Attempting to request_join again is a local error.
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

    // Bob joins.
    {
        let mut joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
        joined.request_join("communicate", false)?;
        alice_room.accept_pending(&joined.export_pending())?;
    }

    // Bob leaves via pending.
    {
        let mut joined = JoinedRoom::from_log(alice_room.log(), bob.clone())?;
        assert!(joined.is_member());
        joined.leave()?;
        let outcomes = alice_room.accept_pending(&joined.export_pending())?;
        assert!(outcomes[0].accepted);
    }

    // Bob is no longer a member.
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
    // Remove a head to break the log's own validity.
    log.heads.clear();
    let r = JoinedRoom::from_log(log, bob);
    assert!(r.is_err());
    Ok(())
}
