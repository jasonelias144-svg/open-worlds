use chat_world::commons::{verify_commons, Commons};
use chat_world::error::Result;
use chat_world::home::HomeRoom;
use chat_world::record::Record;
use chat_world::transcript::{sign_transcript, TranscriptEntry};
use chat_world::verify::verify_room;
use chat_world::{Keypair, Room, RoomTemplate};

fn short(s: &str, n: usize) -> String {
    let s = s.strip_prefix("did:key:").unwrap_or(s);
    s.chars().take(n).collect()
}

fn check_home_ref(rec: &Record, home: &HomeRoom) -> Option<String> {
    let text = match rec {
        Record::Message(m) => &m.text,
        _ => return None,
    };
    let idx = text.find("home_ref=")?;
    let rest = &text[idx + 9..];
    let prefix: String = rest.chars().take(16).collect();
    let found = home
        .room()
        .records()
        .iter()
        .any(|r| r.hash().map(|h| h.starts_with(&prefix)).unwrap_or(false));
    Some(format!("home_ref={prefix}: {}", if found { "found" } else { "MISSING" }))
}

fn main() -> Result<()> {
    println!("{}", "=".repeat(74));
    println!("Home Room + Commons — the user's journey outward");
    println!("{}", "=".repeat(74));
    println!();

    let alice = Keypair::generate();
    let home_kp = Keypair::generate();
    let bob = Keypair::generate();
    let bob_room_kp = Keypair::generate();
    let commons_kp = Keypair::generate();

    // ---- Alice creates her home ----
    let mut home = HomeRoom::create(alice.clone(), home_kp, "alice's home")?;
    println!("Alice's home:  {}", short(home.room().world_id().as_str(), 32));
    println!("  (room's own key; alice is creator)");
    println!("  template:    {}", home.room().template().template_id);
    println!("  personal:    {}", home.room().template().personal);
    println!();

    // ---- Journal ----
    home.journal("First entry. I want to understand how composition works at three levels.")?;
    home.journal("Note: the parent supplies, the child decides.")?;
    println!("Journals: 2 entries");

    // ---- Bob creates a room ----
    let bob_template = RoomTemplate::chat("fractal-worlds", "fractal worlds");
    let mut bob_room = Room::create(bob_template, bob_room_kp, &bob)?;
    println!("Bob's room:    {}", short(bob_room.world_id().as_str(), 32));

    // ---- Commons registers Bob's room ----
    let mut commons = Commons::new(commons_kp);
    commons.register_room(&bob_room, &bob, None)?;
    println!("Commons:       {}", short(commons.world_id.as_str(), 32));
    println!("  registered {} room(s)", commons.records().len());
    println!();

    // ---- Alice drafts a message for Bob's room ----
    let draft = home.draft(
        "I've been thinking about the composition rule. What if a plant could refuse even when the garden gives it water?",
        Some(bob_room.world_id()),
    )?;
    let draft_hash = draft.hash()?;
    println!("Draft:     {}", short(&draft_hash, 20));

    // ---- Alice ports an external conversation ----
    let entries = vec![
        TranscriptEntry {
            speaker: "user".into(),
            ts: chat_world::now(),
            text: "What is composition in fractal worlds?".into(),
        },
        TranscriptEntry {
            speaker: "assistant".into(),
            ts: chat_world::now(),
            text: "The parent delegates the child's law to the child. It enforces only interaction rules.".into(),
        },
    ];
    let transcript = sign_transcript("claude.ai session, 2026-11-15", entries, &alice)?;
    let port = home.port(&transcript, "room", Some(bob_room.world_id()))?;
    let port_hash = port.hash()?;
    println!("Port:      {} (from {})", short(&port_hash, 20), transcript.source_label);

    // ---- Bookmark + presence ----
    home.bookmark(&bob_room, "good conversation, come back")?;
    home.announce_presence(&[bob_room.world_id().clone()], 300)?;
    println!("Bookmark + presence recorded.");
    println!();

    // ---- Alice joins Bob's room ----
    bob_room.join(&alice, "communicate", false)?;
    println!("Alice joined Bob's room (tier: communicate).");

    // ---- Alice commits her draft and port ----
    let committed_draft = home.commit_draft_to_room(&draft_hash, &mut bob_room)?;
    println!("Committed draft: {}", short(&committed_draft.hash()?, 20));
    let committed_port = home.commit_port_to_room(&port_hash, &mut bob_room)?;
    println!("Committed port:  {}", short(&committed_port.hash()?, 20));
    println!();

    // ---- Verify all three ----
    println!("{}", "-".repeat(74));
    println!("Verification:");
    match verify_room(home.room()) {
        Ok(()) => println!("  home:    verifies (chain, sigs, policy)"),
        Err(e) => println!("  home:    FAILED: {e}"),
    }
    match verify_room(&bob_room) {
        Ok(()) => println!("  bob's:   verifies"),
        Err(e) => println!("  bob's:   FAILED: {e}"),
    }
    match verify_commons(&commons) {
        Ok(()) => println!("  commons: verifies"),
        Err(e) => println!("  commons: FAILED: {e}"),
    }
    println!();

    // ---- Cross-check home_refs ----
    println!("Cross-references (home_ref in Bob's room → home):");
    for (label, rec) in [("draft", &committed_draft), ("port", &committed_port)] {
        match check_home_ref(rec, &home) {
            Some(msg) => println!("  {label}: {msg}"),
            None => println!("  {label}: no home_ref found"),
        }
    }
    println!();

    // ---- Export ----
    let export = home.export()?;
    let count = export["records"].as_array().map(|a| a.len()).unwrap_or(0);
    println!("Home export: {} records, portable JSON", count);
    println!();

    // ---- Visible log of Bob's room ----
    println!("{}", "-".repeat(74));
    println!("Bob's room — visible log:");
    for entry in bob_room.visible_log() {
        let t = entry["type"].as_str().unwrap_or("?");
        let seq = entry["seq"].as_u64().unwrap_or(0);
        match t {
            "message" => {
                let author = short(entry["author"].as_str().unwrap_or("?"), 10);
                let kind = entry["kind"].as_str().unwrap_or("normal");
                let text = entry["text"].as_str().unwrap_or("");
                let trunc: String = text.chars().take(48).collect();
                println!("  [{seq:>3}] {author} {kind:8} {trunc}");
            }
            "join" => {
                let subj = short(entry["subject"].as_str().unwrap_or("?"), 10);
                let tier = entry["tier"].as_str().unwrap_or("?");
                println!("  [{seq:>3}] join: {subj} ({tier})");
            }
            "created" => println!("  [{seq:>3}] created"),
            _ => {}
        }
    }
    println!();

    println!("What this establishes:");
    println!("  - The room is its own world with its own key; the");
    println!("    creator joins with theirs. A home room's user");
    println!("    persists the room's key (the demo generates fresh).");
    println!("  - The home is a personal room. Only the creator can");
    println!("    be a member. Journals, drafts, ports, bookmarks,");
    println!("    and presence all live in one chain.");
    println!("  - The home is the user's KnowledgeWorld — one");
    println!("    chain, one identity, one export.");
    println!("  - Committing to a room is explicit. The message");
    println!("    carries a home_ref, so the two logs bind.");
    println!("  - The Commons is a directory, not a gatekeeper.");
    println!("  - All three logs verify offline.");
    println!();
    println!("Anchor (public domain, Emily Dickinson):");
    println!("  'I'm Nobody! Who are you?'");
    println!("  'Are you – Nobody – too?'");

    Ok(())
}
