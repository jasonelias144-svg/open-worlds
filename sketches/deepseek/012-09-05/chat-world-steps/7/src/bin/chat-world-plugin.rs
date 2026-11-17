use chat_world::error::{Error, Result};
use chat_world::{Keypair, Plugin, Request, RoomTemplate};
use std::io::{BufRead, Write};

fn short(s: &str) -> String {
    let s = s.strip_prefix("did:key:").unwrap_or(s);
    s.chars().take(16).collect()
}

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    let mode = args.get(1).map(|s| s.as_str()).unwrap_or("--demo");
    match mode {
        "--demo" => demo(),
        "--stdin-server" => stdin_server(),
        other => {
            eprintln!("Unknown mode: {other}");
            eprintln!("Usage: chat-world-plugin [--demo | --stdin-server]");
            std::process::exit(1);
        }
    }
}

fn demo() -> Result<()> {
    println!("{}", "=".repeat(74));
    println!("Chat World Plugin — the keeper's side");
    println!("{}", "=".repeat(74));
    println!();

    let user_kp = Keypair::generate();
    let home_kp = Keypair::generate();
    let mut plugin = Plugin::new(user_kp, home_kp, "alice's home")?;

    let init = plugin.handle(Request {
        id: serde_json::json!(1),
        method: "init".into(),
        params: serde_json::Value::Null,
    });
    let r = init.result.as_ref().ok_or_else(|| Error::Policy("init failed".into()))?;
    let user_id = r["user_id"].as_str().unwrap_or("?");
    let home_id = r["home_id"].as_str().unwrap_or("?");
    println!("User:  {}", short(user_id));
    println!("Home:  {}", short(home_id));
    println!();

    let template = RoomTemplate::chat("demo-room", "a demo room");
    let template_json = serde_json::to_value(&template)
        .map_err(|e| Error::Serialization(e.to_string()))?;
    let create = plugin.handle(Request {
        id: serde_json::json!(2),
        method: "create_room".into(),
        params: serde_json::json!({ "template": template_json }),
    });
    if let Some(err) = &create.error {
        println!("create_room FAILED: {}", err.message);
        return Ok(());
    }
    let room_id = create.result.as_ref().unwrap()["room_id"].as_str().unwrap().to_string();
    println!("Room:  {}", short(&room_id));

    let post = plugin.handle(Request {
        id: serde_json::json!(3),
        method: "post_message".into(),
        params: serde_json::json!({
            "room_id": room_id,
            "text": "Hello from the plugin. This is the first message.",
        }),
    });
    match &post.result {
        Some(v) => println!("Posted: {}", short(v["record_hash"].as_str().unwrap_or("?"))),
        None => println!("post_message FAILED: {:?}", post.error.as_ref().map(|e| &e.message)),
    }

    let attest = plugin.handle(Request {
        id: serde_json::json!(4),
        method: "attest_transcript".into(),
        params: serde_json::json!({
            "source_label": "external chat",
            "entries": [
                {"speaker": "user", "ts": "2026-11-17T10:00:00Z", "text": "Hello"},
                {"speaker": "assistant", "ts": "2026-11-17T10:00:05Z", "text": "Hi"},
            ],
        }),
    });
    let transcript_json = attest.result.as_ref()
        .map(|v| v["transcript_json"].clone())
        .unwrap_or(serde_json::Value::Null);
    println!("Transcript: {}",
        short(attest.result.as_ref()
            .and_then(|v| v["transcript_hash"].as_str())
            .unwrap_or("?")));

    let port = plugin.handle(Request {
        id: serde_json::json!(5),
        method: "port_conversation".into(),
        params: serde_json::json!({
            "room_id": room_id,
            "transcript_json": transcript_json,
        }),
    });
    match &port.result {
        Some(v) => println!("Ported into home: {}", short(v["port_hash"].as_str().unwrap_or("?"))),
        None => println!("port_conversation FAILED: {:?}", port.error.as_ref().map(|e| &e.message)),
    }

    let read = plugin.handle(Request {
        id: serde_json::json!(6),
        method: "read_room".into(),
        params: serde_json::json!({ "room_id": room_id }),
    });
    if let Some(entries) = read.result.as_ref().and_then(|v| v["entries"].as_array()) {
        println!();
        println!("Visible log ({} entries):", entries.len());
        for e in entries {
            let t = e["type"].as_str().unwrap_or("?");
            let seq = e["seq"].as_u64().unwrap_or(0);
            let text = e["text"].as_str().unwrap_or("");
            let author = e["author"].as_str().unwrap_or("");
            let trunc: String = text.chars().take(44).collect();
            println!("  [{seq:>3}] {t:10} {:12} {trunc}", short(author));
        }
    }

    let verify = plugin.handle(Request {
        id: serde_json::json!(7),
        method: "verify_room".into(),
        params: serde_json::json!({ "room_id": room_id }),
    });
    println!();
    match &verify.result {
        Some(_) => println!("Verify: ok"),
        None => println!("Verify FAILED: {:?}", verify.error.as_ref().map(|e| &e.message)),
    }

    let export = plugin.handle(Request {
        id: serde_json::json!(8),
        method: "export_room_log".into(),
        params: serde_json::json!({ "room_id": room_id }),
    });
    if let Some(v) = &export.result {
        let bytes = serde_json::to_string(&v["log_json"]).map(|s| s.len()).unwrap_or(0);
        println!("Export: {} bytes of JSON", bytes);
    }

    println!();
    println!("Anchor (public domain, Emily Dickinson):");
    println!("  'The Brain – is wider than the Sky –'");
    println!("  'For – put them side by side –'");
    Ok(())
}

fn stdin_server() -> Result<()> {
    use std::io;

    let stdin = io::stdin();
    let stdout = io::stdout();
    let mut out = stdout.lock();
    let mut lines = stdin.lock().lines();

    let config_line = lines.next()
        .ok_or_else(|| Error::Serialization("missing config line".into()))??;
    let config: serde_json::Value = serde_json::from_str(config_line.trim())
        .map_err(|e| Error::Serialization(format!("config: {e}")))?;
    let home_name = config.get("home_name").and_then(|v| v.as_str()).unwrap_or("home");

    let user_kp = Keypair::generate();
    let home_kp = Keypair::generate();
    let mut plugin = Plugin::new(user_kp, home_kp, home_name)?;

    let ready = serde_json::json!({
        "event": "ready",
        "user_id": plugin.user_id().as_str(),
        "home_id": plugin.home_id().as_str(),
    });
    writeln!(out, "{}", ready)?;
    out.flush()?;

    for line in lines {
        let line = line?;
        if line.trim().is_empty() { continue; }
        let req: Request = match serde_json::from_str(&line) {
            Ok(r) => r,
            Err(e) => {
                let err = serde_json::json!({
                    "id": null,
                    "error": { "code": "parse", "message": e.to_string() }
                });
                writeln!(out, "{}", err)?;
                out.flush()?;
                continue;
            }
        };
        let resp = plugin.handle(req);
        let text = serde_json::to_string(&resp)
            .map_err(|e| Error::Serialization(e.to_string()))?;
        writeln!(out, "{}", text)?;
        out.flush()?;
    }
    Ok(())
}
