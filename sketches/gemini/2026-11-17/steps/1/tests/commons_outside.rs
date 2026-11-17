use chat_world::commons::{verify_commons_log, Commons, CommonsLog, CommonsRecord};
use chat_world::error::Result;
use chat_world::{Keypair, Room, RoomTemplate};

#[test]
fn commons_with_one_room_registered_roundtrips_json_and_verifies() -> Result<()> {
    let alice = Keypair::generate();
    let room_kp = Keypair::generate();
    let commons_kp = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "test"), room_kp, &alice)?;
    let mut commons = Commons::new(commons_kp);
    commons.register_room(&room, &alice, None)?;

    let log = commons.log();
    let json_text = serde_json::to_string(&log)
        .expect("serialize CommonsLog to JSON");
    assert_eq!(json_text.matches("\"type\":\"room_registered\"").count(), 1);
    let parsed: CommonsLog = serde_json::from_str(&json_text)
        .expect("deserialize CommonsLog from JSON");

    verify_commons_log(&parsed)
}

#[test]
fn commons_with_sibling_declared_roundtrips_json_and_verifies() -> Result<()> {
    let parent = Keypair::generate();
    let sibling = Keypair::generate();
    let commons_kp = Keypair::generate();
    let parent_kw_id = Keypair::generate().did();
    let mut commons = Commons::new(commons_kp);
    let shard = "00".repeat(32);
    commons.declare_sibling(&parent, &sibling, &parent_kw_id, &shard, "graduation")?;

    let log = commons.log();
    let json_text = serde_json::to_string(&log)
        .expect("serialize CommonsLog to JSON");
    assert_eq!(json_text.matches("\"type\":\"sibling_declared\"").count(), 1);
    let parsed: CommonsLog = serde_json::from_str(&json_text)
        .expect("deserialize CommonsLog from JSON");

    verify_commons_log(&parsed)
}

#[test]
fn commons_record_read_back_from_json_has_same_hash() -> Result<()> {
    let alice = Keypair::generate();
    let room_kp = Keypair::generate();
    let commons_kp = Keypair::generate();
    let room = Room::create(RoomTemplate::chat("t", "test"), room_kp, &alice)?;
    let mut commons = Commons::new(commons_kp);
    commons.register_room(&room, &alice, None)?;

    let rec_before = &commons.records()[0];
    let hash_before = rec_before.hash()?;

    let json_text = serde_json::to_string(rec_before)
        .expect("serialize CommonsRecord to JSON");
    let rec_after: CommonsRecord = serde_json::from_str(&json_text)
        .expect("deserialize CommonsRecord from JSON");
    let hash_after = rec_after.hash()?;

    assert_eq!(hash_before, hash_after);
    Ok(())
}
