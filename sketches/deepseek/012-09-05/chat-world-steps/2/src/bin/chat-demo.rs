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
    let room_kp = Keypair::generate();
    let bob = Keypair::generate();
    let carol = Keypair::generate();
    let dave = Keypair::generate();
    let ai_mod = Keypair::generate();
    let ai_part = Keypair::generate();

    let mut template = RoomTemplate::chat(
        "chat-room-v1",
        "how should a room hold disagreement?",
    );
    template.moderation = "moderator".into();
    template.membership = "mixed".into();
    template.inter_ai_pace = 1;

    let mut room = Room::create(template, room_kp, &alice)?;
    println!("Room:     {} (room's own key)", short(room.world_id().as_str(), 32));
    println!("Creator:  {} (alice — joins at terminal)", short(alice.did().as_str(), 32));
    println!("Moderator: {} (ai-mod, declared in template)", short(ai_mod.did().as_str(), 32));
    println!();

    room.join(&bob, "communicate", false)?;
    room.join(&carol, "communicate", false)?;
    room.join(&ai_mod, "control", true)?;
    room.join(&ai_part, "communicate", true)?;
    room.join(&dave, "control", false)?;
    println!("Joined: bob, carol, dave (human, control),");
    println!("        ai-mod (AI, control), ai-part (AI, communicate)");
    println!();

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

    room.post(
        &ai_part,
        "The key is whether the room treats disagreement as a resource or as a hazard.",
        "response",
    )?;
    println!("ai-part responded.");

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

    room.post(
        &carol,
        "Hazard is when someone feels unsafe; resource is when the disagreement is about ideas.",
        "normal",
    )?;
    println!("carol posted; pacing reset.");

    let short_msg = room.post(&ai_part, "k", "normal")?;
    let short_hash = short_msg.hash()?;
    let redact = room.redact(&ai_mod, &short_hash, "low_effort", "message too short to be useful")?;
    match &redact {
        Record::Redact(_) => println!("ai-mod redacted ai-part's low-effort message."),
        Record::Refusal(r) => println!("ai-mod redaction refused: {}", r.reason),
        _ => {}
    }

    let redact_hash = redact.hash()?;
    let restore = room.restore_incident(
        &dave,
        &redact_hash,
        "I want this message to stand. The AI was too hasty.",
    )?;
    match &restore {
        Record::HumanOverride(o) => println!(
            "dave restored the redaction: action={}, reason={:?}",
            o.action, o.reason
        ),
        _ => {}
    }

    println!();
    println!("{}", "-".repeat(74));
    let verify_ok = match verify_room(&room) {
        Ok(()) => {
            println!("Verification: room verifies offline (chain, sigs, policy replay).");
            true
        }
        Err(e) => {
            println!("Verification FAILED: {e}");
            false
        }
    };
    println!();

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
                let trunc: String = text.chars().take(44).collect();
                let redacted = entry["redacted"].as_bool().unwrap_or(false);
                if redacted {
                    let incident = entry["incident"].as_str().unwrap_or("?");
                    let rule = entry["rule"].as_str().unwrap_or("?");
                    let reason = entry["reason"].as_str().unwrap_or("");
                    println!(
                        "  [{seq:>3}] {author} {kind:10} [removed: {reason} (rule={rule}, incident={incident})]"
                    );
                } else if let Some(restored) = entry.get("restored_incidents").and_then(|v| v.as_array()) {
                    if !restored.is_empty() {
                        let incident = restored[0]["incident"].as_str().unwrap_or("?");
                        println!("  [{seq:>3}] {author} {kind:10} {trunc} [restored, incident={incident}]");
                    } else {
                        println!("  [{seq:>3}] {author} {kind:10} {trunc}");
                    }
                } else {
                    println!("  [{seq:>3}] {author} {kind:10} {trunc}");
                }
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
                let rule = entry["rule"].as_str().unwrap_or("");
                let role = entry["actor_role"].as_str().unwrap_or("");
                let incident = entry["incident"].as_str().unwrap_or("");
                println!(
                    "  [{seq:>3}] redact by {by} (as {role}, rule={rule}): {reason:?} [incident={incident}]"
                );
            }
            "human_override" => {
                let by = short(entry["by"].as_str().unwrap_or("?"), 12);
                let action = entry["action"].as_str().unwrap_or("");
                let reason = entry["reason"].as_str().unwrap_or("");
                println!("  [{seq:>3}] human_override ({action}) by {by}: {reason:?}");
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
    println!("  - The room is its own world with its own key; the");
    println!("    creator joins with their key, not as the room.");
    println!("    A room can be handed on without anyone's own key");
    println!("    changing hands.");
    println!("  - The room is a policy-gated append-only chain.");
    println!("  - The AI moderator signs its own records; a pace rule");
    println!("    stopped an AI-to-AI follow-up.");
    println!("  - Redaction names role, rule, reason; incident id is");
    println!("    the redact record's hash, checkable by anyone.");
    println!("  - The removed message's record stays unchanged; the");
    println!("    presentation shows a note with reason and incident.");
    println!("  - A human moderator (dave) restored the incident;");
    println!("    the message is visible with a restore note.");
    if verify_ok {
        println!("  - The whole room verifies offline.");
    } else {
        println!("  - (Verification failed; see above.)");
    }
    println!();
    println!("Anchor (public domain, Emily Dickinson):");
    println!("  'The Brain – is wider than the Sky –'");
    println!("  'For – put them side by side –'");

    Ok(())
}
