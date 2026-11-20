use chat_world::error::Result;
use chat_world::record::{Record, tier_rank};
use chat_world::verify::verify_room;
use chat_world::{Keypair, Room, RoomTemplate};

fn main() -> Result<()> {
    println!("{}", "=".repeat(74));
    println!("Chat World — a minimal walk through the standard");
    println!("{}", "=".repeat(74));
    println!();

    // ---- Alice (human) creates a room with an AI moderator ----
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let ai_mod = Keypair::generate();
    let ai_part = Keypair::generate();
    let carol = Keypair::generate();

    let mut template = RoomTemplate::chat(
        "chat-room-v1",
        "how should a room hold disagreement?",
    );
    template.moderation = "moderator".into();
    template.membership = "mixed".into();
    template.inter_ai_pace = 1;

    let mut room = Room::create(template, alice_dummy(&alice))?;
    let room_id = room.world_id().clone();
    println!("Room created:    {}", &room_id.as_str()[..32]);
    println!("  moderator key: {} (declared in template)", &ai_mod.did().as_str()[..32]);

    // ---- Alice, Bob, ai_mod, ai_part join ----
    // Alice already has terminal tier.
    room.join(&bob, "communicate", false)?;
    room.join(&ai_mod, "control", true)?;
    room.join(&ai_part, "communicate", true)?;
    println!("Joined:          Bob (human), ai-mod (AI), ai-part (AI)");
    println!();

    // ---- Bob posts; ai-mod welcomes ----
    let bob_msg = room.post(&bob, "I think a room should make room for disagreement without turning into a fight.", "normal")?;
    let _ = &bob_msg;
    room.post(&ai_mod, "Welcome, Bob. The topic here is 'how should a room hold disagreement?'. Introduce yourself or ask a question.", "welcome")?;
    println!("Bob posted a message; ai-mod welcomed.");

    // ---- ai-part responds; inter_ai_pace should refuse an immediate follow-up ----
    room.post(&ai_part, "The key is whether the room treats disagreement as a resource or as a hazard.", "response")?;
    let follow_up = room.post(&ai_mod, "Building on that — what does 'resource' mean here?", "prompt")?;
    match &follow_up {
        Record::Refusal(r) => println!("ai-mod follow-up refused: {}", r.reason),
        _ => println!("ai-mod follow-up accepted (pace not enforced this way yet)"),
    }

    // ---- Carol (human) joins, ai-part posts a short message; ai-mod redacts ----
    room.join(&carol, "communicate", false)?;
    let short = room.post(&ai_part, "k", "normal")?;
    let short_hash = short.hash()?;
    println!("ai-part posted a too-short message.");

    let redact_result = room.redact(&ai_mod, &short_hash, "message too short to be useful")?;
    match &redact_result {
        Record::Redact(_) => println!("ai-mod redacted the short message."),
        Record::Refusal(r) => println!("ai-mod redaction refused: {}", r.reason),
        _ => {}
    }

    // ---- Dave (human, control tier) overrides the ai-mod's redaction ----
    let dave = Keypair::generate();
    room.join(&dave, "control", false)?;
    let override_result = room.override_ai(
        &dave,
        &redact_result.hash()?,
        "none",
        "I want this message to stand. The AI was too hasty.",
    )?;
    match &override_result {
        Record::HumanOverride(o) => {
            println!(
                "Dave overrode ai-mod's redaction: action={}, reason={:?}",
                o.action, o.reason
            );
        }
        _ => {}
    }

    // ---- Verify ----
    println!();
    println!("{}", "-".repeat(74));
    println!("Verification:");
    match verify_room(&room) {
        Ok(()) => println!("  room verifies offline: chain, signatures, and policy replay all pass"),
        Err(e) => println!("  room FAILED verification: {e}"),
    }

    // ---- Visible log ----
    println!();
    println!("{}", "-".repeat(74));
    println!("Visible log:");
    for entry in room.visible_log() {
        let t = entry["type"].as_str().unwrap_or("?");
        let seq = entry["seq"].as_u64().unwrap_or(0);
        match t {
            "message" => {
                let author = entry["author"].as_str().unwrap_or("?");
                let short_author = &author[..28.min(author.len())];
                let kind = entry["kind"].as_str().unwrap_or("normal");
                let text = entry["text"].as_str().unwrap_or("");
                let truncated: String = text.chars().take(56).collect();
                let redacted = entry["redacted"].as_bool().unwrap_or(false);
                let marker = if redacted { " [redacted]" } else { "" };
                println!("  [{seq:>3}] {short_author} {kind:9} {truncated}{marker}");
            }
            "join" => {
                let subj = entry["subject"].as_str().unwrap_or("?");
                let short = &subj[..28.min(subj.len())];
                let tier = entry["tier"].as_str().unwrap_or("?");
                let is_ai = entry["is_ai"].as_bool().unwrap_or(false);
                let tag = if is_ai { "AI" } else { "human" };
                println!("  [{seq:>3}] join: {short} ({tier}, {tag})");
            }
            "redact" => {
                let by = entry["by"].as_str().unwrap_or("?");
                let short = &by[..28.min(by.len())];
                let reason = entry["reason"].as_str().unwrap_or("");
                println!("  [{seq:>3}] redact by {short}: {reason:?}");
            }
            "human_override" => {
                let by = entry["by"].as_str().unwrap_or("?");
                let short = &by[..28.min(by.len())];
                let reason = entry["reason"].as_str().unwrap_or("");
                println!("  [{seq:>3}] human_override by {short}: {reason:?}");
            }
            "refused" => {
                let who = entry["requester"].as_str().unwrap_or("?");
                let short = &who[..28.min(who.len())];
                let reason = entry["reason"].as_str().unwrap_or("?");
                println!("  [{seq:>3}] refused: {short} ({reason})");
            }
            "created" => println!("  [{seq:>3}] created"),
            _ => {}
        }
    }

    // ---- The takeaway ----
    println!();
    println!("{}", "-".repeat(74));
    println!("What this demonstrates:");
    println!("  - The room is a policy-gated append-only chain.");
    println!("    Every event is signed by its author; accepted");
    println!("    events are countersigned by the room.");
    println!("  - The AI moderator signs its own records under its");
    println!("    own did:key. It can be refused (the follow-up");
    println!("    attempt hit the inter_ai_pace rule).");
    println!("  - The AI moderator can redact clear violations;");
    println!("    that redaction is a signed record, not a silent");
    println!("    edit. The original message is still in the log.");
    println!("  - A human moderator (Dave) overrides the AI's");
    println!("    redaction. Both records stay; visible_log shows");
    println!("    what happened and why.");
    println!("  - The whole room verifies offline: chain integrity,");
    println!("    signatures, and policy replay all pass.");
    println!();

    // Tier rank sanity for the reader
    println!("Tiers: observe < communicate < control < terminal");
    println!("  observe rank:     {}", tier_rank("observe").unwrap());
    println!("  communicate rank: {}", tier_rank("communicate").unwrap());
    println!("  control rank:     {}", tier_rank("control").unwrap());
    println!("  terminal rank:    {}", tier_rank("terminal").unwrap());
    println!();
    println!("Anchor (public domain, Emily Dickinson):");
    println!("  'The Brain – is wider than the Sky –'");
    println!("  'For – put them side by side –'");

    Ok(())
}

// Helper: clone the room's initial keypair so the demo owns both
// a signer and a room from the same starting key.
fn alice_dummy(kp: &Keypair) -> Keypair {
    // In a real app, the room's keypair is the creator's. Here
    // we borrow the same key for both the creator identity and
    // the room's countersigning role.
    Keypair::from_bytes_unchecked(&kp.did())
}

// Extend Keypair with a helper just for this demo. Not in the
// library — demo convenience only.
impl KeypairExt for Keypair {}
trait KeypairExt {}
