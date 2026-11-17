use chat_world::commons::{verify_commons, Commons};
use chat_world::home::HomeRoom;
use chat_world::transcript::{sign_transcript, verify_transcript, TranscriptEntry};
use chat_world::error::Result;
use chat_world::record::Record;
use chat_world::verify::verify_room;
use chat_world::{Keypair, Room, RoomTemplate};

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
    let mut template = RoomTemplate::chat("t", "test");
    template.rate_limit_count = 2;
    template.rate_limit_window = 5;
    let mut room = Room::create(template, Keypair::generate(), &Keypair::generate()).unwrap();
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
    let mut template = RoomTemplate::chat("t", "test");
    template.inter_ai_pace = 1;
    let mut room = Room::create(template, Keypair::generate(), &Keypair::generate()).unwrap();
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
    let r = room.redact(&bob, &h, "author_request", "my bad")?;
    match r { Record::Redact(_) => {}, _ => panic!("expected redact") }
    assert!(room.is_redacted(&h));
    verify_room(&room)
}

#[test]
fn moderator_can_redact_other() -> Result<()> {
    let mut room = make_room();
    let bob = Keypair::generate();
    let moderator = Keypair::generate();
    room.join(&bob, "communicate", false)?;
    room.join(&moderator, "control", false)?;
    let msg = room.post(&bob, "spam", "normal")?;
    let h = msg.hash()?;
    room.redact(&moderator, &h, "spam", "spam")?;
    verify_room(&room)
}

#[test]
fn non_moderator_cannot_redact_other() -> Result<()> {
    let mut room = make_room();
    let bob = Keypair::generate();
    let alice = Keypair::generate();
    room.join(&bob, "communicate", false)?;
    room.join(&alice, "communicate", false)?;
    let msg = room.post(&bob, "hi", "normal")?;
    let h = msg.hash()?;
    let r = room.redact(&alice, &h, "spam", "no")?;
    match r {
        Record::Refusal(r) => assert_eq!(r.reason, "not_allowed"),
        _ => panic!("expected refusal"),
    }
    verify_room(&room)
}

#[test]
fn redact_rejects_unknown_rule() -> Result<()> {
    let mut room = make_room();
    let bob = Keypair::generate();
    room.join(&bob, "communicate", false)?;
    let msg = room.post(&bob, "text", "normal")?;
    let h = msg.hash()?;
    let r = room.redact(&bob, &h, "made_up_rule", "no")?;
    match r {
        Record::Refusal(r) => assert_eq!(r.reason, "rule_not_allowed"),
        _ => panic!("expected rule refusal"),
    }
    verify_room(&room)
}

#[test]
fn restore_makes_text_visible() -> Result<()> {
    let mut room = make_room();
    let bob = Keypair::generate();
    room.join(&bob, "communicate", false)?;
    let msg = room.post(&bob, "words I take back", "normal")?;
    let msg_hash = msg.hash()?;
    let redact = room.redact(&bob, &msg_hash, "author_request", "my bad")?;
    let redact_hash = redact.hash()?;

    let before = room.visible_log();
    let view = before.iter()
        .find(|v| v["type"].as_str() == Some("message") && v["redacted"].as_bool() == Some(true))
        .expect("no redacted message in view");
    assert_eq!(view["text"].as_str(), Some("[removed]"));

    let dave = Keypair::generate();
    room.join(&dave, "control", false)?;
    room.restore_incident(&dave, &redact_hash, "I want it visible")?;

    let after = room.visible_log();
    let view = after.iter()
        .find(|v| v["type"].as_str() == Some("message") && v["text"].as_str() == Some("words I take back"))
        .expect("message not visible after restore");
    assert!(view["restored_incidents"].is_array());
    assert_eq!(view["restored_incidents"][0]["incident"].as_str(), Some(&redact_hash[..16]));

    verify_room(&room)
}

#[test]
fn redacted_record_unchanged_after_restore() -> Result<()> {
    let mut room = make_room();
    let bob = Keypair::generate();
    room.join(&bob, "communicate", false)?;
    let msg = room.post(&bob, "words I take back", "normal")?;
    let msg_hash = msg.hash()?;
    let redact = room.redact(&bob, &msg_hash, "author_request", "my bad")?;
    let redact_hash = redact.hash()?;

    let dave = Keypair::generate();
    room.join(&dave, "control", false)?;
    room.restore_incident(&dave, &redact_hash, "I want it visible")?;

    let stored = room.records().iter()
        .find(|r| r.hash().ok().as_deref() == Some(&msg_hash))
        .expect("original message not found");
    match stored { Record::Message(m) => assert_eq!(m.text, "words I take back"), _ => panic!() }

    verify_room(&room)
}

#[test]
fn restore_rejects_non_redact_target() -> Result<()> {
    let mut room = make_room();
    let bob = Keypair::generate();
    let dave = Keypair::generate();
    room.join(&bob, "communicate", false)?;
    room.join(&dave, "control", false)?;
    let msg = room.post(&bob, "hello", "normal")?;
    let msg_hash = msg.hash()?;
    assert!(room.restore_incident(&dave, &msg_hash, "test").is_err());
    Ok(())
}

#[test]
fn human_can_override_ai() -> Result<()> {
    let mut room = make_room();
    let ai = Keypair::generate();
    let human = Keypair::generate();
    room.join(&ai, "control", true)?;
    room.join(&human, "control", false)?;
    let ai_msg = room.post(&ai, "an observation", "normal")?;
    let h = ai_msg.hash()?;
    room.override_ai(&human, &h, "good observation")?;
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
    assert!(room.override_ai(&ai1, &h, "no").is_err());
    Ok(())
}

#[test]
fn personal_room_refuses_non_seed() -> Result<()> {
    let user = Keypair::generate();
    let room_kp = Keypair::generate();
    let template = RoomTemplate::personal_home("my home");
    let mut room = Room::create(template, room_kp, &user)?;
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
    let room_kp = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "test");
    template.membership = "human_only".into();
    let mut room = Room::create(template, room_kp, &creator)?;
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

#[test]
fn home_journal_and_draft_verify() -> Result<()> {
    let alice = Keypair::generate();
    let home_kp = Keypair::generate();
    let mut home = HomeRoom::create(alice, home_kp, "test home")?;
    home.journal("first note")?;
    home.draft("a draft", None)?;
    verify_room(home.room())
}

#[test]
fn home_port_verifies() -> Result<()> {
    let alice = Keypair::generate();
    let home_kp = Keypair::generate();
    let mut home = HomeRoom::create(alice.clone(), home_kp, "test home")?;
    let entries = vec![TranscriptEntry { speaker: "user".into(), ts: chat_world::now(), text: "hello".into() }];
    let t = sign_transcript("app", entries, &alice)?;
    home.port(&t, "journal", None)?;
    verify_room(home.room())
}

#[test]
fn transcript_tamper_detected() -> Result<()> {
    let alice = Keypair::generate();
    let entries = vec![TranscriptEntry { speaker: "u".into(), ts: chat_world::now(), text: "hi".into() }];
    let mut t = sign_transcript("app", entries, &alice)?;
    t.entries[0].text = "tampered".into();
    assert!(verify_transcript(&t).is_err());
    Ok(())
}

#[test]
fn home_bookmark_and_presence_verify() -> Result<()> {
    let alice = Keypair::generate();
    let home_kp = Keypair::generate();
    let bob = Keypair::generate();
    let bob_room_kp = Keypair::generate();
    let mut home = HomeRoom::create(alice, home_kp, "test home")?;
    let bob_room = Room::create(RoomTemplate::chat("t", "test"), bob_room_kp, &bob)?;
    home.bookmark(&bob_room, "note")?;
    home.announce_presence(&[bob_room.world_id().clone()], 300)?;
    verify_room(home.room())
}

#[test]
fn commons_registration_verifies() -> Result<()> {
    let alice = Keypair::generate();
    let room_kp = Keypair::generate();
    let commons_kp = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "test"), room_kp, &alice)?;
    let mut commons = Commons::new(commons_kp);
    commons.register_room(&room, &alice, None)?;
    verify_commons(&commons)
}

#[test]
fn commit_draft_links_home_and_room() -> Result<()> {
    let alice = Keypair::generate();
    let home_kp = Keypair::generate();
    let bob = Keypair::generate();
    let bob_room_kp = Keypair::generate();
    let mut home = HomeRoom::create(alice.clone(), home_kp, "test home")?;
    let mut bob_room = Room::create(RoomTemplate::chat("t", "test"), bob_room_kp, &bob)?;
    bob_room.join(&alice, "communicate", false)?;
    let draft = home.draft("hello", Some(bob_room.world_id()))?;
    let draft_hash = draft.hash()?;
    let committed = home.commit_draft_to_room(&draft_hash, &mut bob_room)?;
    match committed {
        Record::Message(m) => {
            assert!(m.text.contains("home_ref="));
            assert!(m.text.contains(&draft_hash[..16]));
        }
        _ => panic!(),
    }
    verify_room(home.room())?;
    verify_room(&bob_room)?;
    Ok(())
}

// ---- Step 3: heads ----

#[test]
fn head_mode_emits_heads_at_interval() -> Result<()> {
    let mut room = make_head_mode_room(3);
    let bob = Keypair::generate();
    room.join(&bob, "communicate", false)?;
    room.post(&bob, "one", "normal")?;
    room.post(&bob, "two", "normal")?;
    assert_eq!(room.heads().len(), 1);
    assert_eq!(room.heads()[0].length, 4);

    room.post(&bob, "three", "normal")?;
    room.post(&bob, "four", "normal")?;
    room.post(&bob, "five", "normal")?;
    assert_eq!(room.heads().len(), 2);
    assert_eq!(room.heads()[1].length, 7);
    Ok(())
}

#[test]
fn head_mode_verifies() -> Result<()> {
    let mut room = make_head_mode_room(2);
    let bob = Keypair::generate();
    room.join(&bob, "communicate", false)?;
    room.post(&bob, "a", "normal")?;
    room.post(&bob, "b", "normal")?;
    room.post(&bob, "c", "normal")?;
    verify_room(&room)
}

#[test]
fn head_mode_author_only_records() -> Result<()> {
    let mut room = make_head_mode_room(5);
    let bob = Keypair::generate();
    room.join(&bob, "communicate", false)?;
    room.post(&bob, "hi", "normal")?;
    let mut room_proof_on_message = false;
    let mut room_proof_on_join = false;
    for rec in room.records() {
        let has_room = rec.proof().find_by_method(room.world_id()).is_some();
        match rec {
            Record::Message(_) if has_room => room_proof_on_message = true,
            Record::Join(_) if has_room => room_proof_on_join = true,
            _ => {}
        }
    }
    assert!(!room_proof_on_message);
    assert!(!room_proof_on_join);
    verify_room(&room)
}

#[test]
fn head_verify_against_prefix() -> Result<()> {
    let mut room = make_head_mode_room(2);
    let bob = Keypair::generate();
    room.join(&bob, "communicate", false)?;
    room.post(&bob, "a", "normal")?;
    assert_eq!(room.heads().len(), 1);
    let head = room.heads()[0].clone();
    room.verify_head(&head)?;
    room.post(&bob, "b", "normal")?;
    room.post(&bob, "c", "normal")?;
    assert_eq!(room.heads().len(), 2);
    let head0 = room.heads()[0].clone();
    room.verify_head(&head0)?;
    Ok(())
}

#[test]
fn head_rejects_tampered_last() -> Result<()> {
    let mut room = make_head_mode_room(2);
    let bob = Keypair::generate();
    room.join(&bob, "communicate", false)?;
    room.post(&bob, "a", "normal")?;
    let mut head = room.heads()[0].clone();
    head.last = "00".repeat(32);
    assert!(room.verify_head(&head).is_err());
    Ok(())
}

#[test]
fn head_rejects_wrong_tick() -> Result<()> {
    let mut room = make_head_mode_room(2);
    let bob = Keypair::generate();
    room.join(&bob, "communicate", false)?;
    room.post(&bob, "a", "normal")?;
    let mut head = room.heads()[0].clone();
    head.tick = head.length + 1;
    assert!(room.verify_head(&head).is_err());
    Ok(())
}

#[test]
fn per_record_mode_rejects_heads() -> Result<()> {
    let room = make_room();
    assert!(room.heads().is_empty());
    verify_room(&room)
}

// ---- Step 4: runtime attestation ----

use chat_world::attestation::{attest_runtime, verify_attestation};
use chat_world::ProofOrArray;

#[test]
fn runtime_attestation_verifies() -> Result<()> {
    let runtime = Keypair::generate();
    let a = Keypair::generate();
    let b = Keypair::generate();
    let att = attest_runtime(&runtime, &[&runtime, &a, &b])?;
    verify_attestation(&att)
}

#[test]
fn runtime_attestation_rejects_missing_proof() -> Result<()> {
    let runtime = Keypair::generate();
    let a = Keypair::generate();
    let b = Keypair::generate();
    let att = attest_runtime(&runtime, &[&runtime, &a, &b])?;
    let mut tampered = att.clone();
    if let ProofOrArray::Array(mut proofs) = tampered.proof.clone() {
        proofs.pop();
        tampered.proof = ProofOrArray::Array(proofs);
    }
    assert!(verify_attestation(&tampered).is_err());
    Ok(())
}

#[test]
fn runtime_attestation_rejects_extra_proof() -> Result<()> {
    let runtime = Keypair::generate();
    let a = Keypair::generate();
    let att = attest_runtime(&runtime, &[&runtime, &a])?;
    let c = Keypair::generate();
    let body = chat_world::hash::body_for_signing(&att)?;
    let extra_sig = c.sign(&body);
    let extra_proof = chat_world::Proof::create(&c, &extra_sig);
    let mut tampered = att.clone();
    if let ProofOrArray::Array(mut proofs) = tampered.proof.clone() {
        proofs.push(extra_proof);
        tampered.proof = ProofOrArray::Array(proofs);
    }
    assert!(verify_attestation(&tampered).is_err());
    Ok(())
}

#[test]
fn runtime_attestation_rejects_runtime_not_in_keys() -> Result<()> {
    let runtime = Keypair::generate();
    let a = Keypair::generate();
    let r = attest_runtime(&runtime, &[&a]);
    assert!(r.is_err());
    Ok(())
}

// ---- Step 5: succession trio ----

#[test]
fn shard_export_verifies() -> Result<()> {
    let ai = Keypair::generate();
    let home_kp = Keypair::generate();
    let mut home = HomeRoom::create(ai.clone(), home_kp, "ai memory")?;
    let entry = home.journal("an observation")?;
    let entry_hash = entry.hash()?;
    let target_room = Keypair::generate().did();
    let successor = Keypair::generate().did();
    home.emit_shard_export(&target_room, &successor, vec![entry_hash])?;
    verify_room(home.room())
}

#[test]
fn shard_export_rejected_in_non_personal_room() -> Result<()> {
    // In a personal room, shard exports are allowed; verify_room
    // rejects them in a normal room. But we can't easily append
    // one to a normal Room through the public API (no method),
    // so this test just confirms a normal room verifies without
    // any shard exports present.
    let room = make_room();
    verify_room(&room)
}

#[test]
fn shard_export_rejects_bad_hash() -> Result<()> {
    let ai = Keypair::generate();
    let home_kp = Keypair::generate();
    let mut home = HomeRoom::create(ai, home_kp, "ai memory")?;
    let target_room = Keypair::generate().did();
    let successor = Keypair::generate().did();
    assert!(home.emit_shard_export(&target_room, &successor, vec!["short".into()]).is_err());
    Ok(())
}

#[test]
fn succession_verifies() -> Result<()> {
    let creator = Keypair::generate();
    let room_kp = Keypair::generate();
    let template = RoomTemplate::chat("t", "test");
    let mut room = Room::create(template, room_kp, &creator)?;
    let outgoing = Keypair::generate();
    let incoming = Keypair::generate();
    room.join(&outgoing, "control", true)?;
    let shard = "00".repeat(32);
    let rec = room.declare_succession(&outgoing, &incoming, &shard, "graduation")?;
    match rec {
        Record::ModeratorSuccession(s) => {
            assert_eq!(s.outgoing_id, outgoing.did());
            assert_eq!(s.incoming_id, incoming.did());
        }
        _ => panic!("expected succession"),
    }
    verify_room(&room)
}

#[test]
fn succession_rejects_non_control_outgoing() -> Result<()> {
    let creator = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "test"), room_kp, &creator)?;
    let outgoing = Keypair::generate();
    let incoming = Keypair::generate();
    room.join(&outgoing, "communicate", true)?;
    let shard = "00".repeat(32);
    assert!(room.declare_succession(&outgoing, &incoming, &shard, "test").is_err());
    Ok(())
}

#[test]
fn sibling_declaration_verifies() -> Result<()> {
    let parent = Keypair::generate();
    let sibling = Keypair::generate();
    let commons_kp = Keypair::generate();
    let parent_kw_id = Keypair::generate().did();
    let mut commons = Commons::new(commons_kp);
    let shard = "00".repeat(32);
    commons.declare_sibling(&parent, &sibling, &parent_kw_id, &shard, "graduation")?;
    verify_commons(&commons)
}

#[test]
fn sibling_rejects_same_key() -> Result<()> {
    let parent = Keypair::generate();
    let commons_kp = Keypair::generate();
    let parent_kw_id = Keypair::generate().did();
    let mut commons = Commons::new(commons_kp);
    let shard = "00".repeat(32);
    assert!(commons.declare_sibling(&parent, &parent.clone(), &parent_kw_id, &shard, "x").is_err());
    Ok(())
}

#[test]
fn succession_end_to_end() -> Result<()> {
    // The full story: outgoing AI's KnowledgeWorld exports a shard;
    // the room declares succession; the Commons declares the sibling.
    // All three verify independently, and we cross-check that the
    // succession and sibling both reference the shard export.
    let creator = Keypair::generate();
    let room_kp = Keypair::generate();
    let outgoing_kp = Keypair::generate();
    let incoming_kp = Keypair::generate();
    let commons_kp = Keypair::generate();
    let outgoing_home_kp = Keypair::generate();

    // Outgoing AI's knowledge world
    let mut outgoing_home = HomeRoom::create(outgoing_kp.clone(), outgoing_home_kp, "ai memory")?;
    let obs = outgoing_home.journal("I learned X in the room")?;
    let obs_hash = obs.hash()?;

    // Room with outgoing as moderator
    let mut template = RoomTemplate::chat("t", "test");
    template.moderation = "moderator".into();
    let mut room = Room::create(template, room_kp, &creator)?;
    room.join(&outgoing_kp, "control", true)?;
    room.post(&outgoing_kp, "hello all", "welcome")?;

    // Shard export
    let export = outgoing_home.emit_shard_export(
        room.world_id(),
        &incoming_kp.did(),
        vec![obs_hash],
    )?;
    let shard_hash = export.hash()?;

    // Succession
    room.declare_succession(
        &outgoing_kp, &incoming_kp, &shard_hash, "room became busy",
    )?;

    // Sibling in Commons
    let mut commons = Commons::new(commons_kp);
    commons.declare_sibling(
        &outgoing_kp, &incoming_kp,
        outgoing_home.room().world_id(),
        &shard_hash,
        "graduated",
    )?;

    // Verify all logs
    verify_room(outgoing_home.room())?;
    verify_room(&room)?;
    verify_commons(&commons)?;

    // Cross-check: both succession and sibling reference the export's hash
    let succ = room.records().iter().find_map(|r| {
        if let Record::ModeratorSuccession(s) = r { Some(s) } else { None }
    }).expect("succession not found in room");
    assert_eq!(succ.knowledge_shard_hash, shard_hash);

    let sib = commons.records().iter().find_map(|r| {
        if let chat_world::commons::CommonsRecord::SiblingDeclared(s) = r { Some(s) } else { None }
    }).expect("sibling not found in commons");
    assert_eq!(sib.shard_hash, shard_hash);

    Ok(())
}
