use chat_world::commons::{Commons, CommonsRecord};
use chat_world::doors::{
    as_text, check, draw, ranked, Door, DoorCount, DoorLaw,
    DoorList,
};
use chat_world::error::Result;
use chat_world::hash::body_for_signing;
use chat_world::record::*;
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

// =====================================================================
// A LIST, FORGED, AGAINST check (1..=10)
// =====================================================================

#[test]
fn attack_01_door_added_for_unlisted_room() -> Result<()> {
    // Expected: PASS (check refuses a list with an extra door not in CommonsLog)
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
        template_hash: r2.template().hash()?,
        registration_seq: 1,
        registration_hash: "00".repeat(32),
        law: None,
        count: None,
    });

    assert!(check(&forged, &log, &rooms).is_err(), "extra door added");
    Ok(())
}

#[test]
fn attack_02_door_left_out() -> Result<()> {
    // Expected: PASS (check refuses a list missing a registered door)
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
    // Expected: PASS (check refuses when two doors are swapped out of log order)
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
    // Expected: PASS (check refuses each of the 5 core Door field mutations)
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
    // Expected: PASS (check refuses when a room's join_policy "invite" is shown as "open")
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
    // Expected: PASS (check refuses when law is stripped even though the reader holds the room's log)
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
    // Expected: PASS (check refuses when law/count are claimed for a room whose log the reader does not hold)
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
    // Expected: PASS (check refuses all 4 count forgeries)
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

    // (a) members changed
    let mut f_members = list.clone();
    f_members.doors[0].count.as_mut().unwrap().members = 500;
    assert!(check(&f_members, &log, &rooms).is_err(), "count.members changed");

    // (b) at_record changed
    let mut f_at_rec = list.clone();
    f_at_rec.doors[0].count.as_mut().unwrap().at_record = 99;
    assert!(check(&f_at_rec, &log, &rooms).is_err(), "count.at_record changed");

    // (c) count shown for a room whose law hides it
    let mut f_shown = list.clone();
    f_shown.doors[1].count = Some(DoorCount {
        members: 1,
        at_record: 1,
    });
    assert!(
        check(&f_shown, &log, &rooms).is_err(),
        "count shown for room with count_hidden=true"
    );

    // (d) count taken away from a room whose law shows it
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
    // Expected: PASS (check refuses drawn_from, log_head, and commons_id mutations)
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
    // Expected: PASS (check refuses a DoorList honestly drawn from another Commons listing the same room)
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
    // Expected: PASS (draw refuses a CommonsLog with a middle registration removed)
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
    // Expected: PASS (draw refuses when room B's log has its world_id rewritten to room A's)
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
    // Expected: PASS (draw refuses when template.count_hidden is flipped in either direction)
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
    // Expected: PASS (draw refuses when a Leave record is dropped from the middle of a RoomLog)
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
    // Expected: PASS (draw refuses a Join at the end of a RoomLog signed only by the room key)
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
    // Expected: PASS (draw refuses when the same key joins twice, even with valid dual signatures)
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
    // Expected: FAIL (a truncated per-record RoomLog is still a valid log on its own;
    // catching it requires holding a signed WorldHead or fresher checkpoint from the room).
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let carol = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "Room"), Keypair::generate(), &alice)?;
    room.join(&bob, "communicate", false)?;
    room.join(&carol, "communicate", false)?;
    room.leave(&carol)?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &alice, None)?;

    let mut truncated_log = room.log();
    truncated_log.records.truncate(3); // cut off Carol's Leave at index 3

    assert!(
        draw(&commons.log(), &[truncated_log]).is_err(),
        "truncated log hiding a Leave should be refused if freshness is enforced"
    );
    Ok(())
}

// =====================================================================
// A LIST READ FROM JSON TEXT (18..=19)
// =====================================================================

#[test]
fn attack_18_json_door_room_id_not_a_did_key() -> Result<()> {
    // Expected: PASS (DidKey::deserialize refuses a room_id that is not a valid did:key)
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
    // Expected: FAIL on current code (Door lacks #[serde(deny_unknown_fields)], so serde_json
    // accepts an extra "members" array of personal DidKeys in JSON without error!)
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "Poetry"), Keypair::generate(), &alice)?;
    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &alice, None)?;
    let list = draw(&commons.log(), &[room.log()])?;

    let mut v = serde_json::to_value(&list).unwrap();
    v["doors"][0]["members"] = serde_json::json!([
        alice.did().as_str(),
        bob.did().as_str()
    ]);
    let read: std::result::Result<DoorList, _> = serde_json::from_value(v);

    assert!(
        read.is_err(),
        "Door JSON with unknown 'members' field leaking personal IDs must be refused"
    );
    Ok(())
}

// =====================================================================
// THE TEXT (20..=21)
// =====================================================================

#[test]
fn attack_20_text_welcome_with_line_feed_and_fake_door_line() -> Result<()> {
    // Expected: PASS (quote_ascii escapes \n in welcome so no extra line is written)
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
    // Expected: PASS (quote_ascii escapes \n in law.join_policy so no extra line is written)
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
fn attack_22_sybil_thirty_keys_from_one_holder_outranks_five_people() -> Result<()> {
    // Expected: FAIL (without runtime attestation or proof-of-personhood on Join,
    // 30 keys generated by one holder inflate the member count to 31 and outrank 5 distinct people).
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

    // Assert what the system SHOULD ideally protect against: a single holder's 30 keys
    // should not place sybil_room above the 5-person honest_room.
    assert_eq!(
        &order[0].room_id,
        honest_room.world_id(),
        "Sybil room with 30 puppet keys from one holder outranked 5 real people"
    );
    Ok(())
}

// =====================================================================
// ADDITIONAL ATTACKS OF OUR OWN (23..=25)
// =====================================================================

#[test]
fn attack_23_reseeded_room_with_same_keypair_and_altered_law_refused_by_draw() -> Result<()> {
    // Expected: PASS (draw refuses when a room keeper creates a new RoomLog with the same room_kp
    // but a changed template after registering the original room in the Commons)
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
    // Expected: FAIL on current code (verify_log never checks that Leave.subject_id is a member,
    // and Leave requires no room proof, so any outsider can append Leave records to inflate at_record!)
    let alice = Keypair::generate();
    let outsider = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "Room"), Keypair::generate(), &alice)?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &alice, None)?;

    let mut bad_room_log = room.log();
    let prev = bad_room_log.records.last().unwrap().hash()?;
    let mut bogus_leave = Leave::new(
        bad_room_log.world_id.clone(),
        bad_room_log.records.len() as u64,
        Some(prev),
        outsider.did(),
    );
    let wrapped = Record::Leave(bogus_leave.clone());
    bogus_leave.proof = sign_single(&wrapped, &outsider);
    bad_room_log.records.push(Record::Leave(bogus_leave));

    assert!(
        draw(&commons.log(), &[bad_room_log]).is_err(),
        "Leave by a key that is not a member of the room must be refused"
    );
    Ok(())
}

#[test]
fn attack_25_registration_spoofs_topic_different_from_room_template_topic() -> Result<()> {
    // Expected: FAIL on current code (a member can register a room in Commons with Some("Fake Topic")
    // that contradicts room.template.topic, and DoorLaw does not expose room.template.topic!)
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

    let list = draw(&commons.log(), &[room.log()])?;
    assert_eq!(
        list.doors[0].topic,
        room.template().topic,
        "registration topic contradicted the room's own signed template.topic"
    );
    Ok(())
}
