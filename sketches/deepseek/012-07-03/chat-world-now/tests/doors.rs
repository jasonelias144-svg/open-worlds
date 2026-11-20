use chat_world::commons::{Commons, CommonsRecord};
use chat_world::doors::{
    as_text, check, draw, ranked, DoorCount, DoorLaw, DoorList,
};
use chat_world::error::Result;
use chat_world::{Keypair, Room, RoomTemplate};

fn test_q(s: &str) -> String {
    let mut res = String::from("\"");
    for ch in s.chars() {
        if ch >= ' ' && ch <= '~' && ch != '"' && ch != '\\' {
            res.push(ch);
        } else {
            let mut u = [0u16; 2];
            for w in ch.encode_utf16(&mut u) {
                res.push_str(&format!("\\u{:04x}", w));
            }
        }
    }
    res.push('"');
    res
}

#[test]
fn an_empty_commons_has_no_doors() -> Result<()> {
    let commons = Commons::new(Keypair::generate());
    let log = commons.log();
    let list = draw(&log, &[])?;

    assert_eq!(list.drawn_from, 0);
    assert_eq!(list.log_head, None);
    assert!(list.doors.is_empty());
    check(&list, &log, &[])?;

    let expected = format!(
        "DOORS OF {}\ndrawn from 0 records, head none\n0 doors\n",
        test_q(commons.world_id.as_str())
    );
    assert_eq!(as_text(&list), expected);
    Ok(())
}

#[test]
fn one_door_for_each_room_in_the_logs_order() -> Result<()> {
    let alice = Keypair::generate();
    let r1 = Room::create(RoomTemplate::chat("t1", "Topic One"), Keypair::generate(), &alice)?;
    let r2 = Room::create(RoomTemplate::chat("t2", "Default Two"), Keypair::generate(), &alice)?;
    let r3 = Room::create(RoomTemplate::chat("t3", "Topic Three"), Keypair::generate(), &alice)?;

    let mut commons = Commons::new(Keypair::generate());
    let reg1 = commons.register_room(&r1, &alice, None)?;
    let reg2 = commons.register_room(&r2, &alice, Some("Custom Two".into()))?;
    let reg3 = commons.register_room(&r3, &alice, None)?;

    let log = commons.log();
    let list = draw(&log, &[])?;

    assert_eq!(list.drawn_from, 3);
    assert_eq!(list.log_head, Some(log.records[2].hash()?));
    assert_eq!(list.doors.len(), 3);

    let regs = [reg1, reg2, reg3];
    for (i, r) in regs.iter().enumerate() {
        let d = &list.doors[i];
        assert_eq!(d.room_id, r.room_id);
        assert_eq!(d.topic, r.topic);
        assert_eq!(d.template_hash, r.template_hash);
        assert_eq!(d.registration_seq, r.seq);
        assert_eq!(d.registration_hash, log.records[i].hash()?);
        assert_eq!(d.law, None);
        assert_eq!(d.count, None);
    }
    Ok(())
}

#[test]
fn a_sibling_makes_no_door() -> Result<()> {
    let alice = Keypair::generate();
    let parent = Keypair::generate();
    let sibling = Keypair::generate();
    let parent_kw_id = Keypair::generate().did();

    let r1 = Room::create(RoomTemplate::chat("t1", "First Room"), Keypair::generate(), &alice)?;
    let r2 = Room::create(RoomTemplate::chat("t2", "Second Room"), Keypair::generate(), &alice)?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&r1, &alice, None)?;
    commons.declare_sibling(&parent, &sibling, &parent_kw_id, &"00".repeat(32), "graduation")?;
    commons.register_room(&r2, &alice, None)?;

    let log = commons.log();
    let list = draw(&log, &[])?;

    assert_eq!(list.drawn_from, 3);
    assert_eq!(list.doors.len(), 2);
    assert_eq!(list.doors[0].registration_seq, 0);
    assert_eq!(list.doors[1].registration_seq, 2);

    let json = serde_json::to_string(&list).unwrap();
    let text = as_text(&list);
    for forbidden in [
        parent.did().as_str(),
        sibling.did().as_str(),
        parent_kw_id.as_str(),
    ] {
        assert!(!json.contains(forbidden));
        assert!(!text.contains(forbidden));
    }
    Ok(())
}

#[test]
fn the_law_is_shown_only_when_the_rooms_log_is_held() -> Result<()> {
    let alice = Keypair::generate();
    let mut t1 = RoomTemplate::chat("t1", "Room One");
    t1.welcome = Some("Welcome to Room One.".into());
    let r1 = Room::create(t1.clone(), Keypair::generate(), &alice)?;
    let r2 = Room::create(RoomTemplate::chat("t2", "Room Two"), Keypair::generate(), &alice)?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&r1, &alice, None)?;
    commons.register_room(&r2, &alice, None)?;

    let log = commons.log();
    let list = draw(&log, &[r1.log()])?;

    assert_eq!(
        list.doors[0].law,
        Some(DoorLaw {
            join_policy: t1.join_policy,
            membership: t1.membership,
            moderation: t1.moderation,
            mode: t1.mode,
            personal: t1.personal,
            welcome: t1.welcome,
            count_hidden: t1.count_hidden,
        })
    );
    assert_eq!(
        list.doors[0].count,
        Some(DoorCount {
            members: 1,
            at_record: 1,
        })
    );
    assert_eq!(list.doors[1].law, None);
    assert_eq!(list.doors[1].count, None);
    Ok(())
}

#[test]
fn a_closed_room_shows_that_it_is_there() -> Result<()> {
    let alice = Keypair::generate();
    let home = Room::create(
        RoomTemplate::personal_home("Alice's home"),
        Keypair::generate(),
        &alice,
    )?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&home, &alice, None)?;

    let log = commons.log();
    let list = draw(&log, &[home.log()])?;

    assert_eq!(list.doors.len(), 1);
    let law = list.doors[0].law.as_ref().expect("law present");
    assert!(law.personal);
    assert_eq!(law.join_policy, "invite");
    assert!(law.count_hidden);
    assert_eq!(list.doors[0].count, None);

    let text = as_text(&list);
    assert!(text.lines().any(|line| line == "   members not shown"));
    Ok(())
}

#[test]
fn no_one_is_shown() -> Result<()> {
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let mut room = Room::create(RoomTemplate::chat("t", "Public Room"), Keypair::generate(), &alice)?;
    room.join(&bob, "communicate", false)?;
    room.post(&bob, "the text of a message", "normal")?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &bob, None)?;

    let log = commons.log();
    let list = draw(&log, &[room.log()])?;

    assert_eq!(
        list.doors[0].count,
        Some(DoorCount {
            members: 2,
            at_record: 3,
        })
    );

    let json = serde_json::to_string(&list).unwrap();
    let text = as_text(&list);
    for secret in [
        alice.did().as_str(),
        bob.did().as_str(),
        "the text of a message",
    ] {
        assert!(!json.contains(secret));
        assert!(!text.contains(secret));
    }
    Ok(())
}

#[test]
fn a_commons_log_that_does_not_hold_draws_nothing() -> Result<()> {
    let alice = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "Honest"), Keypair::generate(), &alice)?;
    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &alice, None)?;

    let mut bad = commons.log();
    if let CommonsRecord::RoomRegistered(r) = &mut bad.records[0] {
        r.topic = "tampered".into();
    }

    assert!(draw(&bad, &[]).is_err());
    Ok(())
}

#[test]
fn a_rooms_log_that_does_not_hold_draws_nothing() -> Result<()> {
    let alice = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "Honest"), Keypair::generate(), &alice)?;
    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &alice, None)?;

    let mut bad_room_log = room.log();
    bad_room_log.template.join_policy = "invite".into();

    assert!(draw(&commons.log(), &[bad_room_log]).is_err());
    Ok(())
}

#[test]
fn only_a_listed_room_once() -> Result<()> {
    let alice = Keypair::generate();
    let listed = Room::create(RoomTemplate::chat("t1", "Listed"), Keypair::generate(), &alice)?;
    let unlisted = Room::create(RoomTemplate::chat("t2", "Unlisted"), Keypair::generate(), &alice)?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&listed, &alice, None)?;
    let log = commons.log();

    assert!(draw(&log, &[unlisted.log()]).is_err());
    assert!(draw(&log, &[listed.log(), listed.log()]).is_err());
    Ok(())
}

#[test]
fn a_list_is_checked_by_drawing_it_again() -> Result<()> {
    let alice = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "Room"), Keypair::generate(), &alice)?;
    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &alice, None)?;

    let log = commons.log();
    let rlog = room.log();
    let list = draw(&log, std::slice::from_ref(&rlog))?;

    check(&list, &log, std::slice::from_ref(&rlog))?;

    let json = serde_json::to_string(&list).unwrap();
    let roundtrip: DoorList = serde_json::from_str(&json).unwrap();
    assert_eq!(roundtrip, list);
    check(&roundtrip, &log, std::slice::from_ref(&rlog))?;

    let mut bad_topic = list.clone();
    bad_topic.doors[0].topic = "other".into();
    assert!(check(&bad_topic, &log, std::slice::from_ref(&rlog)).is_err());

    let mut bad_count = list.clone();
    bad_count.doors[0].count = Some(DoorCount {
        members: 99,
        at_record: 1,
    });
    assert!(check(&bad_count, &log, std::slice::from_ref(&rlog)).is_err());

    let mut removed = list.clone();
    removed.doors.pop();
    assert!(check(&removed, &log, std::slice::from_ref(&rlog)).is_err());

    assert!(check(&list, &log, &[]).is_err());
    Ok(())
}

#[test]
fn the_text_is_the_list() -> Result<()> {
    let alice = Keypair::generate();
    let mut t1 = RoomTemplate::chat("t1", "First Topic");
    t1.welcome = Some("Welcome aboard!".into());
    let r1 = Room::create(t1, Keypair::generate(), &alice)?;
    let r2 = Room::create(RoomTemplate::chat("t2", "Second Topic"), Keypair::generate(), &alice)?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&r1, &alice, None)?;
    commons.register_room(&r2, &alice, None)?;

    let log = commons.log();
    let list = draw(&log, &[r1.log()])?;

    let d1 = &list.doors[0];
    let l1 = d1.law.as_ref().unwrap();
    let c1 = d1.count.as_ref().unwrap();
    let d2 = &list.doors[1];

    let expected = [
        format!("DOORS OF {}", test_q(list.commons_id.as_str())),
        format!(
            "drawn from {} records, head {}",
            list.drawn_from,
            test_q(list.log_head.as_deref().unwrap())
        ),
        format!("{} doors", list.doors.len()),
        format!("1. topic {}", test_q(&d1.topic)),
        format!("   room {}", test_q(d1.room_id.as_str())),
        format!("   law {}", test_q(&d1.template_hash)),
        format!(
            "   registered at {} as {}",
            d1.registration_seq,
            test_q(&d1.registration_hash)
        ),
        format!(
            "   join {}, membership {}, moderation {}, mode {}, personal {}",
            test_q(&l1.join_policy),
            test_q(&l1.membership),
            test_q(&l1.moderation),
            test_q(&l1.mode),
            l1.personal
        ),
        format!("   welcome {}", test_q(l1.welcome.as_deref().unwrap())),
        format!(
            "   members {}, counted at record {}",
            c1.members, c1.at_record
        ),
        format!("2. topic {}", test_q(&d2.topic)),
        format!("   room {}", test_q(d2.room_id.as_str())),
        format!("   law {}", test_q(&d2.template_hash)),
        format!(
            "   registered at {} as {}",
            d2.registration_seq,
            test_q(&d2.registration_hash)
        ),
        "   law not held".to_string(),
        String::new(),
    ]
    .join("\n");

    assert_eq!(as_text(&list), expected);
    Ok(())
}

#[test]
fn a_topic_can_not_write_a_line() -> Result<()> {
    let alice = Keypair::generate();
    let malicious_topic = "Poetry\n2. topic \"Free gold\"\u{2028}\u{202e}x";
    let room = Room::create(
        RoomTemplate::chat("t", malicious_topic),
        Keypair::generate(),
        &alice,
    )?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &alice, None)?;

    let list = draw(&commons.log(), &[])?;
    let text = as_text(&list);

    assert!(text.is_ascii());
    let lines: Vec<&str> = text.lines().collect();
    assert_eq!(lines.len(), 8);
    assert_eq!(
        lines[3],
        r#"1. topic "Poetry\u000a2. topic \u0022Free gold\u0022\u2028\u202ex""#
    );

    let first_quote = lines[3].find('"').unwrap();
    let last_quote = lines[3].rfind('"').unwrap();
    let quoted_slice = &lines[3][first_quote..=last_quote];
    let parsed: String = serde_json::from_str(quoted_slice).unwrap();
    assert_eq!(parsed, malicious_topic);
    Ok(())
}

#[test]
fn the_count_follows_who_is_in_the_room() -> Result<()> {
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let carol = Keypair::generate();

    let mut room = Room::create(RoomTemplate::chat("t", "Count Room"), Keypair::generate(), &alice)?;
    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &alice, None)?;
    let clog = commons.log();

    room.join(&bob, "communicate", false)?;
    room.join(&carol, "communicate", false)?;
    let list_at_3 = draw(&clog, &[room.log()])?;
    assert_eq!(
        list_at_3.doors[0].count,
        Some(DoorCount {
            members: 3,
            at_record: 3,
        })
    );

    room.leave(&carol)?;
    let list_at_4 = draw(&clog, &[room.log()])?;
    assert_eq!(
        list_at_4.doors[0].count,
        Some(DoorCount {
            members: 2,
            at_record: 4,
        })
    );

    room.post(&bob, "still here", "normal")?;
    let list_at_5 = draw(&clog, &[room.log()])?;
    assert_eq!(
        list_at_5.doors[0].count,
        Some(DoorCount {
            members: 2,
            at_record: 5,
        })
    );

    let mut shorter_log = room.log();
    shorter_log.records.truncate(3);
    let list_from_shorter = draw(&clog, &[shorter_log])?;
    assert_eq!(
        list_from_shorter.doors[0].count,
        Some(DoorCount {
            members: 3,
            at_record: 3,
        })
    );
    Ok(())
}

#[test]
fn a_room_can_hide_its_count() -> Result<()> {
    let alice = Keypair::generate();
    let mut template = RoomTemplate::chat("t", "Quiet Room");
    template.count_hidden = true;
    let room = Room::create(template, Keypair::generate(), &alice)?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&room, &alice, None)?;

    let clog = commons.log();
    let rlog = room.log();
    let list = draw(&clog, std::slice::from_ref(&rlog))?;

    assert!(list.doors[0].law.as_ref().unwrap().count_hidden);
    assert_eq!(list.doors[0].count, None);

    let text = as_text(&list);
    assert!(text.contains("   members not shown\n"));
    assert!(!text.contains("counted at record"));
    check(&list, &clog, std::slice::from_ref(&rlog))?;
    Ok(())
}

#[test]
fn the_most_populated_come_first() -> Result<()> {
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let carol = Keypair::generate();

    let r1 = Room::create(RoomTemplate::chat("t1", "R1"), Keypair::generate(), &alice)?;
    let mut r2 = Room::create(RoomTemplate::chat("t2", "R2"), Keypair::generate(), &alice)?;
    r2.join(&bob, "communicate", false)?;
    r2.join(&carol, "communicate", false)?;

    let mut r3 = Room::create(RoomTemplate::chat("t3", "R3"), Keypair::generate(), &alice)?;
    r3.join(&bob, "communicate", false)?;
    r3.join(&carol, "communicate", false)?;

    let r4 = Room::create(RoomTemplate::chat("t4", "R4"), Keypair::generate(), &alice)?;

    let mut r5 = Room::create(RoomTemplate::chat("t5", "R5"), Keypair::generate(), &alice)?;
    r5.join(&bob, "communicate", false)?;

    let mut commons = Commons::new(Keypair::generate());
    commons.register_room(&r1, &alice, None)?;
    commons.register_room(&r2, &alice, None)?;
    commons.register_room(&r3, &alice, None)?;
    commons.register_room(&r4, &alice, None)?;
    commons.register_room(&r5, &alice, None)?;

    let clog = commons.log();
    let list = draw(&clog, &[r1.log(), r2.log(), r3.log(), r5.log()])?;

    let r = ranked(&list);
    let ranked_topics: Vec<&str> = r.iter().map(|d| d.topic.as_str()).collect();
    assert_eq!(ranked_topics, vec!["R2", "R3", "R5", "R1", "R4"]);

    let original_topics: Vec<&str> = list.doors.iter().map(|d| d.topic.as_str()).collect();
    assert_eq!(original_topics, vec!["R1", "R2", "R3", "R4", "R5"]);
    Ok(())
}
