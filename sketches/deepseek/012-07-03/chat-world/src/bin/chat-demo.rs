use chat_world::error::Result;
use chat_world::record::Record;
use chat_world::verify::verify_room;
use chat_world::{Keypair, Room, RoomTemplate};

fn short(s: &str, n: usize) -> String {
    let s = s.strip_prefix("did:key:").unwrap_or(s);
    s.chars().take(n).collect()
}

fn main() -> Result<()> {
    println!("{}", "=".repeat(74));
    println!("Chat World — walking the standard end to end");
    println!("{}", "=".repeat(74));
    println!();

    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let carol = Keypair::generate();
    let dave = Keypair::generate();
    let ai_mod = Keypair::generate();
    let ai_part = Keypair::generate();

    // Alice creates the room with her own key. She is its
    // terminal-tier creator and its countersigning key.
    let mut template = RoomTemplate::chat(
        "chat-room-v1",
        "how should a room hold disagreement?",
    );
    template.moderation = "moderator".into();
    template.membership = "mixed".into();
    template.inter_ai_pace = 1;

    let mut room = Room::create(template, alice.clone())?;
    println!("Room:     {}", short(room.world_id().as_str(), 32));
    println!("Creator:  {} (alice)", short(alice.did().as_str(), 32));
    println!("Moderator: {} (ai-mod, declared in template)", short(ai_mod.did().as_str(), 32));
    println!();

    room.join(&bob, "communicate", false)?;
    room.join(&carol, "communicate", false)?;
    room.join(&ai_mod, "control", true)?;
    room.join(&ai_part, "communicate", true)?;
    room.join(&dave, "control", false)?;
    println!("Joined: bob (human), carol (human), dave (human, control),");
    println!("        ai-mod (AI, control), ai-part (AI, communicate)");
    println!();

    // Bob posts; ai-mod welcomes
    room.post(
        &bob,
        "I think a room should make room for disagreement without turning into a fight.",
        "normal",
    )?;
    room.post(
        &ai_mod,
        "Welcome, Bob. The topic here is 'how should a room hold disagreement?'. Introduce yourself or ask a question.",
        "welcome",
    )?;
    println!("Bob posted; ai-mod welcomed.");

    // ai-part responds
    room.post(
        &ai_part,
        "The key is whether the room treats disagreement as a resource or as a hazard.",
        "response",
    )?;
    println!("ai-part responded.");

    // ai-mod tries to follow up immediately — should hit inter_ai_pace
    let follow_up = room.post(
        &ai_mod,
        "Building on that — what does 'resource' mean here?",
        "prompt",
    )?;
    match &follow_up {
        Record::Refusal(r) => println!("ai-mod follow-up refused: {}", r.reason),
        Record::Message(_) => println!("ai-mod follow-up accepted (pace may not have fired)"),
        _ => println!("ai-mod follow-up produced unexpected record"),
    }

    // carol posts (resets the pace)
    room.post(
        &carol,
        "Hazard is when someone feels unsafe; resource is when the disagreement is about ideas.",
        "normal",
    )?;
    println!("carol posted; pacing reset.");

    // ai-part posts a too-short message; ai-mod redacts
    let short_msg = room.post(&ai_part, "k", "normal")?;
    let short_hash = short_msg.hash()?;
    let redact = room.redact(&ai_mod, &short_hash, "message too short to be useful")?;
    match &redact {
        Record::Redact(_) => println!("ai-mod redacted ai-part's too-short message."),
        Record::Refusal(r) => println!("ai-mod redaction refused: {}", r.reason),
        _ => {}
    }

    // Dave overrides ai-mod's redaction
    let redact_hash = redact.hash()?;
    let ov = room.override_ai(
        &dave,
        &redact_hash,
        "none",
        "I want this message to stand. The AI was too hasty.",
    )?;
    match &ov {
        Record::HumanOverride(o) => println!(
            "dave overrode ai-mod: action={}, reason={:?}",
            o.action, o.reason
        ),
        _ => {}
    }

    // Verify
    println!();
    println!("{}", "-".repeat(74));
    match verify_room(&room) {
        Ok(()) => println!("Verification: room verifies offline (chain, sigs, policy replay)."),
        Err(e) => println!("Verification FAILED: {e}"),
    }
    println!();

    // Visible log
    println!("{}", "-".repeat(74));
    println!("Visible log:");
    for entry in room.visible_log() {
        let t = entry["type"].as_str().unwrap_or("?");
        let seq = entry["seq"].as_u64().unwrap_or(0);
        match t {
            "message" => {
                let author = short(entry["author"].as_str().unwrap_or("?"), 12);
                let kind = entry["kind"].as_str().unwrap_or("normal");
                let text = entry["text"].as_str().unwrap_or("");
                let trunc: String = text.chars().take(50).collect();
                let red = entry["redacted"].as_bool().unwrap_or(false);
                let marker = if red { " [redacted]" } else { "" };
                println!("  [{seq:>3}] {author} {kind:10} {trunc}{marker}");
            }
            "join" => {
                let subj = short(entry["subject"].as_str().unwrap_or("?"), 12);
                let tier = entry["tier"].as_str().unwrap_or("?");
                let tag = if entry["is_ai"].as_bool().unwrap_or(false) { "AI" } else { "human" };
                println!("  [{seq:>3}] join: {subj} ({tier}, {tag})");
            }
            "redact" => {
                let by = short(entry["by"].as_str().unwrap_or("?"), 12);
                let reason = entry["reason"].as_str().unwrap_or("");
                println!("  [{seq:>3}] redact by {by}: {reason:?}");
            }
            "human_override" => {
                let by = short(entry["by"].as_str().unwrap_or("?"), 12);
                let reason = entry["reason"].as_str().unwrap_or("");
                println!("  [{seq:>3}] human_override by {by}: {reason:?}");
            }
            "refused" => {
                let who = short(entry["requester"].as_str().unwrap_or("?"), 12);
                let reason = entry["reason"].as_str().unwrap_or("?");
                println!("  [{seq:>3}] refused: {who} ({reason})");
            }
            "created" => println!("  [{seq:>3}] created"),
            _ => {}
        }
    }

    println!();
    println!("{}", "-".repeat(74));
    println!("What this demonstrates:");
    println!("  - The room is a policy-gated append-only chain.");
    println!("    Every event is signed; accepted events are");
    println!("    countersigned by the room.");
    println!("  - The AI moderator signs its own records. It can");
    println!("    be refused — the pace rule stopped an AI-to-AI");
    println!("    follow-up.");
    println!("  - Redaction is a signed record, not a silent edit.");
    println!("    The original message stays in the log.");
    println!("  - A human moderator (dave) overrides the AI. Both");
    println!("    records stay; visible_log shows what and why.");
    println!("  - The whole room verifies offline.");
    println!();
    println!("Anchor (public domain, Emily Dickinson):");
    println!("  'The Brain – is wider than the Sky –'");
    println!("  'For – put them side by side –'");

    Ok(())
}
