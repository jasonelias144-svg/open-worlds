use chat_world::plugin::{Plugin, Request};
use chat_world::transcript::{verify_transcript, Transcript};
use chat_world::{Keypair, RoomTemplate};

fn make_plugin() -> Plugin {
    let user = Keypair::generate();
    let home = Keypair::generate();
    Plugin::new(user, home, "test home").unwrap()
}

fn req(id: u64, method: &str, params: serde_json::Value) -> Request {
    Request {
        id: serde_json::json!(id),
        method: method.into(),
        params,
    }
}

fn template_json() -> serde_json::Value {
    let t = RoomTemplate::chat("t", "test");
    serde_json::to_value(&t).unwrap()
}

#[test]
fn init_returns_user_and_home() {
    let mut p = make_plugin();
    let user_id = p.user_id().as_str().to_string();
    let home_id = p.home_id().as_str().to_string();
    let resp = p.handle(req(1, "init", serde_json::Value::Null));
    assert!(resp.error.is_none(), "{:?}", resp.error);
    let r = resp.result.unwrap();
    assert_eq!(r["user_id"].as_str().unwrap(), user_id);
    assert_eq!(r["home_id"].as_str().unwrap(), home_id);
}

#[test]
fn create_room_and_post() {
    let mut p = make_plugin();
    let resp = p.handle(req(1, "create_room", serde_json::json!({
        "template": template_json(),
    })));
    assert!(resp.error.is_none(), "{:?}", resp.error);
    let room_id = resp.result.unwrap()["room_id"].as_str().unwrap().to_string();

    let resp = p.handle(req(2, "post_message", serde_json::json!({
        "room_id": room_id,
        "text": "hello",
    })));
    assert!(resp.error.is_none(), "{:?}", resp.error);
    let record_hash = resp.result.unwrap()["record_hash"].as_str().unwrap().to_string();
    assert_eq!(record_hash.len(), 64);
}

#[test]
fn read_room_returns_visible_log() {
    let mut p = make_plugin();
    let create = p.handle(req(1, "create_room", serde_json::json!({
        "template": template_json(),
    })));
    let room_id = create.result.unwrap()["room_id"].as_str().unwrap().to_string();
    p.handle(req(2, "post_message", serde_json::json!({
        "room_id": room_id,
        "text": "hello",
    })));

    let resp = p.handle(req(3, "read_room", serde_json::json!({ "room_id": room_id })));
    assert!(resp.error.is_none(), "{:?}", resp.error);
    let entries = resp.result.unwrap()["entries"].as_array().cloned().unwrap();
    let msg = entries.iter()
        .find(|e| e["type"].as_str() == Some("message"))
        .expect("no message entry");
    assert_eq!(msg["text"].as_str(), Some("hello"));
}

#[test]
fn post_to_unknown_room_fails() {
    let mut p = make_plugin();
    let fake = Keypair::generate().did();
    let resp = p.handle(req(1, "post_message", serde_json::json!({
        "room_id": fake.as_str(),
        "text": "hello",
    })));
    assert!(resp.error.is_some());
}

#[test]
fn attest_transcript_roundtrips() {
    let mut p = make_plugin();
    let resp = p.handle(req(1, "attest_transcript", serde_json::json!({
        "source_label": "test",
        "entries": [
            {"speaker": "user", "ts": "2026-11-17T10:00:00Z", "text": "hi"},
        ],
    })));
    assert!(resp.error.is_none(), "{:?}", resp.error);
    let r = resp.result.unwrap();
    let transcript_json = r["transcript_json"].clone();
    let t: Transcript = serde_json::from_value(transcript_json).unwrap();
    verify_transcript(&t).unwrap();
}

#[test]
fn export_and_import_roundtrip() {
    let mut p1 = make_plugin();
    let create = p1.handle(req(1, "create_room", serde_json::json!({
        "template": template_json(),
    })));
    let room_id = create.result.unwrap()["room_id"].as_str().unwrap().to_string();
    p1.handle(req(2, "post_message", serde_json::json!({
        "room_id": room_id,
        "text": "hello",
    })));

    let export = p1.handle(req(3, "export_room_log", serde_json::json!({ "room_id": room_id })));
    let log_json = export.result.unwrap()["log_json"].clone();

    let mut p2 = make_plugin();
    let import = p2.handle(req(1, "import_room_log", serde_json::json!({
        "log_json": log_json,
    })));
    assert!(import.error.is_none(), "{:?}", import.error);

    let verify = p2.handle(req(2, "verify_room", serde_json::json!({ "room_id": room_id })));
    assert!(verify.error.is_none(), "{:?}", verify.error);
}

#[test]
fn port_conversation_into_room() {
    let mut p = make_plugin();
    let create = p.handle(req(1, "create_room", serde_json::json!({
        "template": template_json(),
    })));
    let room_id = create.result.unwrap()["room_id"].as_str().unwrap().to_string();

    let attest = p.handle(req(2, "attest_transcript", serde_json::json!({
        "source_label": "ext",
        "entries": [
            {"speaker": "user", "ts": "2026-11-17T10:00:00Z", "text": "hi"},
        ],
    })));
    let transcript_json = attest.result.unwrap()["transcript_json"].clone();

    let port = p.handle(req(3, "port_conversation", serde_json::json!({
        "room_id": room_id,
        "transcript_json": transcript_json,
    })));
    assert!(port.error.is_none(), "{:?}", port.error);
}

#[test]
fn unknown_method_errors() {
    let mut p = make_plugin();
    let resp = p.handle(req(1, "nonexistent", serde_json::Value::Null));
    assert!(resp.error.is_some());
}

#[test]
fn verify_room_passes_for_valid_room() {
    let mut p = make_plugin();
    let create = p.handle(req(1, "create_room", serde_json::json!({
        "template": template_json(),
    })));
    let room_id = create.result.unwrap()["room_id"].as_str().unwrap().to_string();
    p.handle(req(2, "post_message", serde_json::json!({
        "room_id": room_id,
        "text": "hello",
    })));

    let verify = p.handle(req(3, "verify_room", serde_json::json!({ "room_id": room_id })));
    assert!(verify.error.is_none(), "{:?}", verify.error);
}
