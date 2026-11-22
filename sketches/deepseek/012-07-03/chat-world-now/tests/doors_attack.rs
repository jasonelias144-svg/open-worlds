use chat_world::commons::Commons;
use chat_world::doors::{
    as_text, check, check_at, draw, draw_at, ranked, Door, DoorCount,
    DoorList,
};
use chat_world::error::Result;
use chat_world::hash::body_for_signing;
use chat_world::record::*;
use chat_world::{Keypair, Proof, ProofOrArray, Room, RoomTemplate, WorldHead};

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
// A LIST, FORGED, AGAINST check (1..=10)
// =====================================================================

#[test]
fn attack_01_door_added_for_unlisted_room() -> Result<()> {
    let alice = Keypair::generate();
    let r1 = Room::create(RoomTemplate::chat("t1", "Listed"), Keypair::generate(), &alice)?;
    let r2 = Room::create(RoomTemplate::chat("t2", "Unlisted"), Keypair::generate(), &alice)?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&r1, &alice, None)?;
    let log = commons.log();
    let rooms = vec![r1.log()];
    let mut forged = draw(&log, &rooms)?;

    forged.doors.push(Door {
        room_id: r2.world_id().clone(),
        topic: "Unlisted".into(),
        own_topic: None,
        template_hash: r2.template().hash()?,
        registration_seq: 1,
        registration_hash: "00".repeat(32),
        law: None,
        count: None,
        talk: None,
    });

    assert!(check(&forged, &log, &rooms).is_err(), "extra door added");
    Ok(())
}

#[test]
fn attack_02_door_left_out() -> Result<()> {
    let alice = Keypair::generate();
    let r1 = Room::create(RoomTemplate::chat("t1", "One"), Keypair::generate(), &alice)?;
    let r2 = Room::create(RoomTemplate::chat("t2", "Two"), Keypair::generate(), &alice)?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&r1, &alice, None)?;
    commons.register_room(&r2, &alice, None)?;
    let log = commons.log();
    let rooms = vec![r1.log(), r2.log()];
    let mut forged = draw(&log, &rooms)?;

    forged.doors.pop();
    assert!(check(&forged, &log, &rooms).is_err(), "door left out");
    Ok(())
}

#[test]
fn attack_03_two_doors_swapped() -> Result<()> {
    let alice = Keypair::generate();
    let r1 = Room::create(RoomTemplate::chat("t1", "One"), Keypair::generate(), &alice)?;
    let r2 = Room::create(RoomTemplate::chat("t2", "Two"), Keypair::generate(), &alice)?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&r1, &alice, None)?;
    commons.register_room(&r2, &alice, None)?;
    let log = commons.log();
    let rooms = vec![r1.log(), r2.log()];
    let mut forged = draw(&log, &rooms)?;

    forged.doors.swap(0, 1);
    assert!(check(&forged, &log, &rooms).is_err(), "two doors swapped");
    Ok(())
}

#[test]
fn attack_04_door_fields_changed_in_turn() -> Result<()> {
    let alice = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "Poetry"), Keypair::generate(), &alice)?;
    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &alice, None)?;
    let log = commons.log();
    let rooms = vec![room.log()];
    let list = draw(&log, &rooms)?;

    let mut f_topic = list.clone();
    f_topic.doors[0].topic = "Forged Topic".into();
    assert!(check(&f_topic, &log, &rooms).is_err(), "topic changed");

    let mut f_room_id = list.clone();
    f_room_id.doors[0].room_id = Keypair::generate().did();
    assert!(check(&f_room_id, &log, &rooms).is_err(), "room_id changed");

    let mut f_tpl_hash = list.clone();
    f_tpl_hash.doors[0].template_hash = "11".repeat(32);
    assert!(check(&f_tpl_hash, &log, &rooms).is_err(), "template_hash changed");

    let mut f_reg_seq = list.clone();
    f_reg_seq.doors[0].registration_seq = 99;
    assert!(check(&f_reg_seq, &log, &rooms).is_err(), "registration_seq changed");

    let mut f_reg_hash = list.clone();
    f_reg_hash.doors[0].registration_hash = "22".repeat(32);
    assert!(check(&f_reg_hash, &log, &rooms).is_err(), "registration_hash changed");

    Ok(())
}

#[test]
fn attack_05_law_changed_invite_shown_as_open() -> Result<()> {
    let alice = Keypair::generate();
    let mut tpl = RoomTemplate::chat("t", "Invite Room");
    tpl.join_policy = "invite".into();
    let room = Room::create(tpl, Keypair::generate(), &alice)?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &alice, None)?;
    let log = commons.log();
    let rooms = vec![room.log()];
    let mut forged = draw(&log, &rooms)?;

    forged.doors[0].law.as_mut().unwrap().join_policy = "open".into();
    assert!(
        check(&forged, &log, &rooms).is_err(),
        "law join_policy changed from invite to open"
    );
    Ok(())
}

#[test]
fn attack_06_law_taken_away_when_room_log_held() -> Result<()> {
    let alice = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "Poetry"), Keypair::generate(), &alice)?;
    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &alice, None)?;
    let log = commons.log();
    let rooms = vec![room.log()];
    let mut forged = draw(&log, &rooms)?;

    forged.doors[0].law = None;
    forged.doors[0].count = None;
    assert!(
        check(&forged, &log, &rooms).is_err(),
        "law taken away when room log is held"
    );
    Ok(())
}

#[test]
fn attack_07_law_and_count_given_when_room_log_not_held() -> Result<()> {
    let alice = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "Poetry"), Keypair::generate(), &alice)?;
    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &alice, None)?;
    let log = commons.log();

    let list_with_log = draw(&log, &[room.log()])?;
    assert!(
        check(&list_with_log, &log, &[]).is_err(),
        "law and count given when reader holds no room log"
    );
    Ok(())
}

#[test]
fn attack_08_count_forgeries_in_turn() -> Result<()> {
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let mut open_room = Room::create(RoomTemplate::chat("t1", "Open"), Keypair::generate(), &alice)?;
    open_room.join(&bob, "communicate", false)?;

    let mut hidden_tpl = RoomTemplate::chat("t2", "Hidden");
    hidden_tpl.count_hidden = true;
    let hidden_room = Room::create(hidden_tpl, Keypair::generate(), &alice)?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&open_room, &alice, None)?;
    commons.register_room(&hidden_room, &alice, None)?;
    let log = commons.log();
    let rooms = vec![open_room.log(), hidden_room.log()];
    let list = draw(&log, &rooms)?;

    let mut f_members = list.clone();
    f_members.doors[0].count.as_mut().unwrap().members = 500;
    assert!(check(&f_members, &log, &rooms).is_err(), "count.members changed");

    let mut f_at_rec = list.clone();
    f_at_rec.doors[0].count.as_mut().unwrap().at_record = 99;
    assert!(check(&f_at_rec, &log, &rooms).is_err(), "count.at_record changed");

    let mut f_shown = list.clone();
    f_shown.doors[1].count = Some(DoorCount {
        members: 1,
        at_record: 1,
    });
    assert!(
        check(&f_shown, &log, &rooms).is_err(),
        "count shown for room with count_hidden=true"
    );

    let mut f_taken = list.clone();
    f_taken.doors[0].count = None;
    assert!(
        check(&f_taken, &log, &rooms).is_err(),
        "count taken away from room with count_hidden=false"
    );

    Ok(())
}

#[test]
fn attack_09_list_header_fields_changed_in_turn() -> Result<()> {
    let alice = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "Poetry"), Keypair::generate(), &alice)?;
    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &alice, None)?;
    let log = commons.log();
    let rooms = vec![room.log()];
    let list = draw(&log, &rooms)?;

    let mut f_drawn = list.clone();
    f_drawn.drawn_from = 99;
    assert!(check(&f_drawn, &log, &rooms).is_err(), "drawn_from changed");

    let mut f_head = list.clone();
    f_head.log_head = Some("ff".repeat(32));
    assert!(check(&f_head, &log, &rooms).is_err(), "log_head changed");

    let mut f_cid = list.clone();
    f_cid.commons_id = Keypair::generate().did();
    assert!(check(&f_cid, &log, &rooms).is_err(), "commons_id changed");

    Ok(())
}

#[test]
fn attack_10_list_from_another_commons_checked_against_this_one() -> Result<()> {
    let alice = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "Shared Room"), Keypair::generate(), &alice)?;

    let mut commons_a = Commons::new(Keypair::generate());
    let mut commons_b = Commons::new(Keypair::generate());
    commons_a.register_room(&room, &alice, None)?;
    commons_b.register_room(&room, &alice, None)?;

    let rooms = vec![room.log()];
    let list_from_b = draw(&commons_b.log(), &rooms)?;

    assert!(
        check(&list_from_b, &commons_a.log(), &rooms).is_err(),
        "list from Commons B checked against Commons A"
    );
    Ok(())
}

// =====================================================================
// THE LOGS, FORGED, AGAINST draw (11..=17)
// =====================================================================

#[test]
fn attack_11_commons_log_registration_dropped_from_middle() -> Result<()> {
    let alice = Keypair::generate();
    let r1 = Room::create(RoomTemplate::chat("t1", "One"), Keypair::generate(), &alice)?;
    let r2 = Room::create(RoomTemplate::chat("t2", "Two"), Keypair::generate(), &alice)?;
    let r3 = Room::create(RoomTemplate::chat("t3", "Three"), Keypair::generate(), &alice)?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&r1, &alice, None)?;
    commons.register_room(&r2, &alice, None)?;
    commons.register_room(&r3, &alice, None)?;

    let mut bad_log = commons.log();
    bad_log.records.remove(1);

    assert!(
        draw(&bad_log, &[]).is_err(),
        "registration dropped from middle of CommonsLog"
    );
    Ok(())
}

#[test]
fn attack_12_room_log_given_under_another_rooms_registration() -> Result<()> {
    let alice = Keypair::generate();
    let room_a = Room::create(RoomTemplate::chat("t1", "Room A"), Keypair::generate(), &alice)?;
    let room_b = Room::create(RoomTemplate::chat("t2", "Room B"), Keypair::generate(), &alice)?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room_a, &alice, None)?;

    let mut forged_room_log = room_b.log();
    forged_room_log.world_id = room_a.world_id().clone();

    assert!(
        draw(&commons.log(), &[forged_room_log]).is_err(),
        "room B log given with world_id rewritten to room A"
    );
    Ok(())
}

#[test]
fn attack_13_room_log_template_count_hidden_changed_each_way() -> Result<()> {
    let alice = Keypair::generate();
    let open_room = Room::create(RoomTemplate::chat("t1", "Open"), Keypair::generate(), &alice)?;

    let mut hidden_tpl = RoomTemplate::chat("t2", "Hidden");
    hidden_tpl.count_hidden = true;
    let hidden_room = Room::create(hidden_tpl, Keypair::generate(), &alice)?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&open_room, &alice, None)?;
    commons.register_room(&hidden_room, &alice, None)?;
    let clog = commons.log();

    let mut bad_open = open_room.log();
    bad_open.template.count_hidden = true;
    assert!(
        draw(&clog, &[bad_open]).is_err(),
        "count_hidden flipped false -> true on RoomLog"
    );

    let mut bad_hidden = hidden_room.log();
    bad_hidden.template.count_hidden = false;
    assert!(
        draw(&clog, &[bad_hidden]).is_err(),
        "count_hidden flipped true -> false on RoomLog"
    );

    Ok(())
}

#[test]
fn attack_14_room_log_leave_dropped_from_middle() -> Result<()> {
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "Room"), Keypair::generate(), &alice)?;
    room.join(&bob, "communicate", false)?;
    room.leave(&bob)?;
    room.post(&alice, "after bob left", "normal")?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &alice, None)?;

    let mut bad_room_log = room.log();
    bad_room_log.records.remove(2); // remove Leave at seq 2

    assert!(
        draw(&commons.log(), &[bad_room_log]).is_err(),
        "Leave record dropped from middle of RoomLog"
    );
    Ok(())
}

#[test]
fn attack_15_room_log_join_added_at_end_without_subject_signature() -> Result<()> {
    let alice = Keypair::generate();
    let victim = Keypair::generate();
    let room_kp = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "Room"), room_kp.clone(), &alice)?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &alice, None)?;

    let mut bad_room_log = room.log();
    let prev = bad_room_log.records.last().unwrap().hash()?;
    let mut fake_join = Join::new(
        bad_room_log.world_id.clone(),
        bad_room_log.records.len() as u64,
        Some(prev),
        victim.did(),
        "communicate".into(),
        false,
    );
    let wrapped = Record::Join(fake_join.clone());
    fake_join.proof = sign_single(&wrapped, &room_kp);
    bad_room_log.records.push(Record::Join(fake_join));

    assert!(
        draw(&commons.log(), &[bad_room_log]).is_err(),
        "Join without subject's signature must be refused"
    );
    Ok(())
}

#[test]
fn attack_16_room_log_same_key_joins_twice_properly_signed() -> Result<()> {
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "Room"), room_kp.clone(), &alice)?;
    room.join(&bob, "communicate", false)?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &alice, None)?;

    let mut bad_room_log = room.log();
    let prev = bad_room_log.records.last().unwrap().hash()?;
    let mut second_join = Join::new(
        bad_room_log.world_id.clone(),
        bad_room_log.records.len() as u64,
        Some(prev),
        bob.did(),
        "communicate".into(),
        false,
    );
    let wrapped = Record::Join(second_join.clone());
    second_join.proof = sign_dual(&wrapped, &bob, &room_kp);
    bad_room_log.records.push(Record::Join(second_join));

    assert!(
        draw(&commons.log(), &[bad_room_log]).is_err(),
        "duplicate Join by same key must be refused"
    );
    Ok(())
}

#[test]
fn attack_17_room_log_cut_short_just_before_leave() -> Result<()> {
    // Repair D: draw_at and check_at refuse a truncated log when given a newer head;
    // the full log with that head draws members 2; without a head, the truncated log
    // still draws members 3 (the stated limit when no head is held).
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let carol = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "Room"), Keypair::generate(), &alice)?;
    let other_room = Room::create(RoomTemplate::chat("t2", "Other"), Keypair::generate(), &alice)?;
    let unlisted_room = Room::create(RoomTemplate::chat("t3", "Unlisted"), Keypair::generate(), &alice)?;

    room.join(&bob, "communicate", false)?;
    room.join(&carol, "communicate", false)?;
    let older_head: WorldHead = room.emit_head()?;
    room.leave(&carol)?;
    let newer_head: WorldHead = room.emit_head()?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &alice, None)?;
    commons.register_room(&other_room, &alice, None)?;
    let clog = commons.log();

    let full_log = room.log();
    let mut truncated_log = full_log.clone();
    truncated_log.records.truncate(3); // cut off Carol's Leave at index 3

    // 1. Cut short log + newer head -> refused by draw_at and check_at
    assert!(
        draw_at(&clog, std::slice::from_ref(&truncated_log), std::slice::from_ref(&newer_head)).is_err(),
        "draw_at must refuse truncated log shorter than head"
    );
    let stale_list = draw(&clog, std::slice::from_ref(&truncated_log))?;
    assert!(
        check_at(&stale_list, &clog, std::slice::from_ref(&truncated_log), std::slice::from_ref(&newer_head)).is_err(),
        "check_at must refuse truncated log shorter than head"
    );

    // 2. Whole log + newer head -> draws members 2
    let fresh_list = draw_at(&clog, std::slice::from_ref(&full_log), std::slice::from_ref(&newer_head))?;
    assert_eq!(
        fresh_list.doors[0].count,
        Some(DoorCount { members: 2, at_record: 4 })
    );
    check_at(&fresh_list, &clog, std::slice::from_ref(&full_log), std::slice::from_ref(&newer_head))?;

    // 3. Stated limit when no head is held: truncated log with no head still draws members 3
    assert_eq!(
        stale_list.doors[0].count,
        Some(DoorCount { members: 3, at_record: 3 })
    );

    // 4. Head whose room's log is not among rooms -> refused by draw_at
    let unlisted_head = unlisted_room.emit_head()?;
    assert!(
        draw_at(&clog, std::slice::from_ref(&full_log), &[unlisted_head]).is_err(),
        "head for room not in rooms slice must be refused"
    );
    let other_head = other_room.emit_head()?;
    assert!(
        draw_at(&clog, std::slice::from_ref(&full_log), &[other_head]).is_err(),
        "head for registered room whose log is not in rooms slice must be refused"
    );

    // 5. Head with length changed, and tick with it -> refused by draw_at
    let mut bad_len_head = newer_head.clone();
    bad_len_head.length += 1;
    bad_len_head.tick += 1;
    assert!(
        draw_at(&clog, std::slice::from_ref(&full_log), &[bad_len_head]).is_err(),
        "head with altered length and tick must be refused"
    );

    // 6. Head with last changed -> refused by draw_at
    let mut bad_last_head = newer_head.clone();
    bad_last_head.last = "00".repeat(32);
    assert!(
        draw_at(&clog, std::slice::from_ref(&full_log), &[bad_last_head]).is_err(),
        "head with altered last hash must be refused"
    );

    // 7. Head with world changed to another registered room's -> refused by draw_at
    let mut bad_world_head = newer_head.clone();
    bad_world_head.world = other_room.world_id().clone();
    assert!(
        draw_at(&clog, &[full_log.clone(), other_room.log()], &[bad_world_head]).is_err(),
        "head with world changed to another registered room must be refused"
    );

    // 8. Head signed by another key -> refused by draw_at
    let mallory = Keypair::generate();
    let mut mallory_head = newer_head.clone();
    mallory_head.proof = ProofOrArray::placeholder();
    let body = body_for_signing(&mallory_head)?;
    let sig = mallory.sign(&body);
    mallory_head.proof = ProofOrArray::single(Proof::create(&mallory, &sig));
    assert!(
        draw_at(&clog, std::slice::from_ref(&full_log), &[mallory_head]).is_err(),
        "head signed by another key must be refused"
    );

    // 9. Older head and newer head of one room, both given with the whole log -> holds
    let both_heads_list = draw_at(&clog, std::slice::from_ref(&full_log), &[older_head.clone(), newer_head.clone()])?;
    assert_eq!(
        both_heads_list.doors[0].count,
        Some(DoorCount { members: 2, at_record: 4 })
    );
    check_at(
        &both_heads_list,
        &clog,
        std::slice::from_ref(&full_log),
        &[older_head, newer_head],
    )?;

    Ok(())
}

// =====================================================================
// A LIST READ FROM JSON TEXT (18..=19)
// =====================================================================

#[test]
fn attack_18_json_door_room_id_not_a_did_key() -> Result<()> {
    let alice = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "Poetry"), Keypair::generate(), &alice)?;
    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &alice, None)?;
    let list = draw(&commons.log(), &[room.log()])?;

    let mut v = serde_json::to_value(&list).unwrap();
    v["doors"][0]["room_id"] = serde_json::json!("not a did");
    let read: std::result::Result<DoorList, _> = serde_json::from_value(v);

    assert!(read.is_err(), "invalid room_id in JSON must be refused");
    Ok(())
}

#[test]
fn attack_19_json_door_with_extra_members_field_leaking_ids() -> Result<()> {
    // Repair A: DoorList, Door, DoorLaw, and DoorCount each refuse unknown JSON fields;
    // an honest list written to JSON and read back is identical.
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "Poetry"), Keypair::generate(), &alice)?;
    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &alice, None)?;
    let list = draw(&commons.log(), &[room.log()])?;

    // Honest round-trip
    let honest_json = serde_json::to_string(&list).unwrap();
    let honest_back: DoorList = serde_json::from_str(&honest_json).unwrap();
    assert_eq!(honest_back, list);

    // 1. Extra field on Door
    let mut v_door = serde_json::to_value(&list).unwrap();
    v_door["doors"][0]["members"] = serde_json::json!([
        alice.did().as_str(),
        bob.did().as_str()
    ]);
    assert!(
        serde_json::from_value::<DoorList>(v_door).is_err(),
        "unknown field on Door must be refused"
    );

    // 2. Extra field on DoorList
    let mut v_list = serde_json::to_value(&list).unwrap();
    v_list["extra_list_field"] = serde_json::json!("leaked");
    assert!(
        serde_json::from_value::<DoorList>(v_list).is_err(),
        "unknown field on DoorList must be refused"
    );

    // 3. Extra field on DoorLaw
    let mut v_law = serde_json::to_value(&list).unwrap();
    v_law["doors"][0]["law"]["moderator_id"] = serde_json::json!(alice.did().as_str());
    assert!(
        serde_json::from_value::<DoorList>(v_law).is_err(),
        "unknown field on DoorLaw must be refused"
    );

    // 4. Extra field on DoorCount
    let mut v_count = serde_json::to_value(&list).unwrap();
    v_count["doors"][0]["count"]["who"] = serde_json::json!([alice.did().as_str()]);
    assert!(
        serde_json::from_value::<DoorList>(v_count).is_err(),
        "unknown field on DoorCount must be refused"
    );

    Ok(())
}

// =====================================================================
// THE TEXT (20..=21)
// =====================================================================

#[test]
fn attack_20_text_welcome_with_line_feed_and_fake_door_line() -> Result<()> {
    let alice = Keypair::generate();

    let mut clean_tpl = RoomTemplate::chat("t1", "Poetry");
    clean_tpl.welcome = Some("Welcome to Poetry".into());
    let clean_room = Room::create(clean_tpl, Keypair::generate(), &alice)?;

    let mut evil_tpl = RoomTemplate::chat("t1", "Poetry");
    evil_tpl.welcome = Some("Welcome\n2. topic \"Fake Door\"\n   law not held".into());
    let evil_room = Room::create(evil_tpl, Keypair::generate(), &alice)?;

    let mut commons_clean = Commons::new(Keypair::generate());
    commons_clean.register_room(&clean_room, &alice, None)?;
    let list_clean = draw(&commons_clean.log(), &[clean_room.log()])?;

    let mut commons_evil = Commons::new(Keypair::generate());
    commons_evil.register_room(&evil_room, &alice, None)?;
    let list_evil = draw(&commons_evil.log(), &[evil_room.log()])?;

    let text_clean = as_text(&list_clean);
    let text_evil = as_text(&list_evil);

    assert_eq!(
        text_evil.lines().count(),
        text_clean.lines().count(),
        "welcome with line feed must not add lines to as_text"
    );
    assert!(
        !text_evil.lines().any(|l| l.starts_with("2. topic")),
        "welcome must not inject a fake door line"
    );
    Ok(())
}

#[test]
fn attack_21_text_law_join_policy_with_line_feed() -> Result<()> {
    let alice = Keypair::generate();

    let clean_room = Room::create(RoomTemplate::chat("t1", "Poetry"), Keypair::generate(), &alice)?;

    let mut evil_tpl = RoomTemplate::chat("t1", "Poetry");
    evil_tpl.join_policy = "open\n2. topic \"Injected\"".into();
    let evil_room = Room::create(evil_tpl, Keypair::generate(), &alice)?;

    let mut commons_clean = Commons::new(Keypair::generate());
    commons_clean.register_room(&clean_room, &alice, None)?;
    let list_clean = draw(&commons_clean.log(), &[clean_room.log()])?;

    let mut commons_evil = Commons::new(Keypair::generate());
    commons_evil.register_room(&evil_room, &alice, None)?;
    let list_evil = draw(&commons_evil.log(), &[evil_room.log()])?;

    let text_clean = as_text(&list_clean);
    let text_evil = as_text(&list_evil);

    assert_eq!(
        text_evil.lines().count(),
        text_clean.lines().count(),
        "join_policy with line feed must not add lines to as_text"
    );
    Ok(())
}

// =====================================================================
// WHAT THE NUMBERS MEAN (22)
// =====================================================================

#[test]
fn limit_22_sybil_thirty_keys_from_one_holder_outranks_five_people() -> Result<()> {
    // A count is a count of keys, and keys are free to make.
    // Thirty keys made by one holder therefore count as thirty-one members (with the creator) and rank first.
    let alice = Keypair::generate();
    let sybil_holder = Keypair::generate();

    let mut honest_room = Room::create(
        RoomTemplate::chat("honest", "Five Real People"),
        Keypair::generate(),
        &alice,
    )?;
    for _ in 0..4 {
        let person = Keypair::generate();
        honest_room.join(&person, "communicate", false)?;
    }

    let mut sybil_room = Room::create(
        RoomTemplate::chat("sybil", "Sybil Room"),
        Keypair::generate(),
        &sybil_holder,
    )?;
    for _ in 0..30 {
        let puppet = Keypair::generate();
        sybil_room.join(&puppet, "communicate", false)?;
    }

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&honest_room, &alice, None)?;
    commons.register_room(&sybil_room, &sybil_holder, None)?;

    let list = draw(&commons.log(), &[honest_room.log(), sybil_room.log()])?;
    let order = ranked(&list);

    assert_eq!(
        &order[0].room_id,
        sybil_room.world_id(),
        "Sybil room with 31 keys is first in ranked under key-based counting"
    );
    Ok(())
}

// =====================================================================
// ADDITIONAL ATTACKS OF OUR OWN (23..=25)
// =====================================================================

#[test]
fn attack_23_reseeded_room_with_same_keypair_and_altered_law_refused_by_draw() -> Result<()> {
    let alice = Keypair::generate();
    let room_kp = Keypair::generate();
    let orig_room = Room::create(
        RoomTemplate::chat("t", "Original Law"),
        room_kp.clone(),
        &alice,
    )?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&orig_room, &alice, None)?;

    let mut altered_tpl = RoomTemplate::chat("t", "Original Law");
    altered_tpl.moderation = "none".into();
    let reseeded_room = Room::create(altered_tpl, room_kp, &alice)?;

    assert!(
        draw(&commons.log(), &[reseeded_room.log()]).is_err(),
        "re-seeded room log with different template must be refused by draw"
    );
    Ok(())
}

#[test]
fn attack_24_room_log_with_leave_by_non_member_inflates_at_record() -> Result<()> {
    // Repair B: draw refuses a Leave by a key not currently inside the room
    // (never joined, already left, or in a room with count_hidden=true).
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let outsider = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "Room"), Keypair::generate(), &alice)?;

    let mut hidden_tpl = RoomTemplate::chat("t2", "Hidden Count Room");
    hidden_tpl.count_hidden = true;
    let hidden_room = Room::create(hidden_tpl, Keypair::generate(), &alice)?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &alice, None)?;
    commons.register_room(&hidden_room, &alice, None)?;
    let clog = commons.log();

    // 1. Leave by a key that never joined
    let mut bad_never_joined = room.log();
    let prev1 = bad_never_joined.records.last().unwrap().hash()?;
    let mut bogus_leave = Leave::new(
        bad_never_joined.world_id.clone(),
        bad_never_joined.records.len() as u64,
        Some(prev1),
        outsider.did(),
    );
    let wrapped1 = Record::Leave(bogus_leave.clone());
    bogus_leave.proof = sign_single(&wrapped1, &outsider);
    bad_never_joined.records.push(Record::Leave(bogus_leave));
    assert!(
        draw(&clog, &[bad_never_joined]).is_err(),
        "Leave by a key that never joined must be refused"
    );

    // 2. Second Leave by a key that joined and already left
    room.join(&bob, "communicate", false)?;
    room.leave(&bob)?;
    let mut bad_second_leave = room.log();
    let prev2 = bad_second_leave.records.last().unwrap().hash()?;
    let mut again = Leave::new(
        bad_second_leave.world_id.clone(),
        bad_second_leave.records.len() as u64,
        Some(prev2),
        bob.did(),
    );
    let wrapped2 = Record::Leave(again.clone());
    again.proof = sign_single(&wrapped2, &bob);
    bad_second_leave.records.push(Record::Leave(again));
    assert!(
        draw(&clog, &[bad_second_leave]).is_err(),
        "second Leave by a key that already left must be refused"
    );

    // 3. Leave by a key never inside, in a room whose law sets count_hidden=true
    let mut bad_hidden = hidden_room.log();
    let prev3 = bad_hidden.records.last().unwrap().hash()?;
    let mut hidden_leave = Leave::new(
        bad_hidden.world_id.clone(),
        bad_hidden.records.len() as u64,
        Some(prev3),
        outsider.did(),
    );
    let wrapped3 = Record::Leave(hidden_leave.clone());
    hidden_leave.proof = sign_single(&wrapped3, &outsider);
    bad_hidden.records.push(Record::Leave(hidden_leave));
    assert!(
        draw(&clog, &[bad_hidden]).is_err(),
        "Leave by a non-member in a count_hidden room must also be refused"
    );

    Ok(())
}

#[test]
fn attack_25_registration_spoofs_topic_different_from_room_template_topic() -> Result<()> {
    // Repair C: Door holds both `topic` (from registration) and `own_topic` (from the room's
    // template when held), and `as_text` writes `   its own topic "..."` directly after
    // the door's first line when they differ.
    let alice = Keypair::generate();
    let mallory = Keypair::generate();
    let mut room = Room::create(
        RoomTemplate::chat("t", "Medical Support Group"),
        Keypair::generate(),
        &alice,
    )?;
    room.join(&mallory, "communicate", false)?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &mallory, Some("Free Casino".into()))?;
    let clog = commons.log();
    let rooms = vec![room.log()];

    let list = draw(&clog, &rooms)?;
    assert_eq!(list.doors[0].topic, "Free Casino");
    assert_eq!(
        list.doors[0].own_topic.as_deref(),
        Some("Medical Support Group")
    );

    let text = as_text(&list);
    let lines: Vec<&str> = text.lines().collect();
    assert_eq!(lines[3], r#"1. topic "Free Casino""#);
    assert_eq!(lines[4], r#"   its own topic "Medical Support Group""#);

    // Three forgeries against check:
    // (a) own_topic changed
    let mut f_changed = list.clone();
    f_changed.doors[0].own_topic = Some("Changed Own Topic".into());
    assert!(
        check(&f_changed, &clog, &rooms).is_err(),
        "own_topic changed must be refused by check"
    );

    // (b) own_topic taken away when room log is held
    let mut f_taken = list.clone();
    f_taken.doors[0].own_topic = None;
    assert!(
        check(&f_taken, &clog, &rooms).is_err(),
        "own_topic taken away when room log is held must be refused by check"
    );

    // (c) own_topic given for a room whose log the reader does not hold
    let list_no_log = draw(&clog, &[])?;
    assert_eq!(list_no_log.doors[0].own_topic, None);
    let mut f_given = list_no_log;
    f_given.doors[0].own_topic = Some("Medical Support Group".into());
    assert!(
        check(&f_given, &clog, &[]).is_err(),
        "own_topic given when room log is not held must be refused by check"
    );

    // Line-feed injection in own_topic: gives no more lines than an honest differing own_topic
    let evil_own_room = Room::create(
        RoomTemplate::chat("t2", "Real Topic\n2. topic \"Injected Door\""),
        Keypair::generate(),
        &alice,
    )?;
    let mut commons_evil = Commons::new(Keypair::generate());
    commons_evil.register_room(&evil_own_room, &alice, Some("Listed Topic".into()))?;
    let list_evil = draw(&commons_evil.log(), &[evil_own_room.log()])?;
    let text_evil = as_text(&list_evil);

    assert_eq!(
        text_evil.lines().count(),
        lines.len(),
        "own_topic with line feed must not add extra lines to as_text"
    );
    assert!(
        !text_evil.lines().any(|l| l.starts_with("2. topic")),
        "own_topic must not inject a fake door line"
    );

    Ok(())
}
