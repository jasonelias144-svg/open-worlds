use chat_world::commons::{verify_commons, Commons, CommonsRecord};
use chat_world::error::Result;
use chat_world::home::HomeRoom;
use chat_world::record::Record;
use chat_world::verify::verify_room;
use chat_world::{Keypair, Room, RoomTemplate};

fn short(s: &str, n: usize) -> String {
    let s = s.strip_prefix("did:key:").unwrap_or(s);
    s.chars().take(n).collect()
}

fn main() -> Result<()> {
    println!("{}", "=".repeat(74));
    println!("Succession — bootstrap AI graduates to a dedicated sibling");
    println!("{}", "=".repeat(74));
    println!();

    let alice = Keypair::generate();
    let room_kp = Keypair::generate();
    let ai_mod_1 = Keypair::generate();
    let ai_mod_1_home_kp = Keypair::generate();
    let ai_mod_2 = Keypair::generate();
    let commons_kp = Keypair::generate();

    // Alice creates a room with ai-mod-1 as declared moderator.
    let mut template = RoomTemplate::chat("chat-room-v1", "the fractal worlds conversation");
    template.moderation = "moderator".into();
    let mut template_room = template.clone();
    template_room.moderator = Some(chat_world::ModeratorSpec {
        moderator_id: ai_mod_1.did(),
        moderator_type: "ai".into(),
        capabilities: vec!["post".into(), "redact".into(), "summarize".into()],
        can_be_overridden: true,
        knowledge_world_id: None,
        meta_room: false,
    });

    let mut room = Room::create(template_room, room_kp, &alice)?;
    println!("Room:        {}", short(room.world_id().as_str(), 32));
    println!("Creator:     {} (alice, terminal)", short(alice.did().as_str(), 32));
    println!("Moderator:   {} (ai-mod-1, declared)", short(ai_mod_1.did().as_str(), 32));
    println!();

    // ai-mod-1 has a KnowledgeWorld (a home room).
    let mut ai_mod_1_home = HomeRoom::create(
        ai_mod_1.clone(), ai_mod_1_home_kp.clone(), "ai-mod-1 memory",
    )?;
    println!("ai-mod-1 KW: {}", short(ai_mod_1_home.room().world_id().as_str(), 32));
    println!();

    // ai-mod-1 joins and acts as moderator.
    room.join(&ai_mod_1, "control", true)?;
    let obs = ai_mod_1_home.journal(
        "In the fractal worlds room I noticed: composition holds at three levels.",
    )?;
    let obs_hash = obs.hash()?;
    room.post(&ai_mod_1, "Welcome. The topic is fractal worlds — introduce yourself.", "welcome")?;
    println!("ai-mod-1: joined at control; welcomed the room;");
    println!("          observed composition in its KnowledgeWorld.");
    println!();

    // Commons lists the room.
    let mut commons = Commons::new(commons_kp);
    commons.register_room(&room, &alice, None)?;
    println!("Commons:     {} (1 room listed)", short(commons.world_id.as_str(), 32));
    println!();

    // The room has become active. Time to graduate.
    println!("{}", "-".repeat(74));
    println!("The room is active. ai-mod-1 graduates its role to a");
    println!("dedicated sibling (ai-mod-2). Three signed events:");
    println!();

    // 1. Shard export from ai-mod-1's KnowledgeWorld.
    let export = ai_mod_1_home.emit_shard_export(
        room.world_id(),
        &ai_mod_2.did(),
        vec![obs_hash.clone()],
    )?;
    let shard_hash = export.hash()?;
    println!("  1. knowledge_shard_export (in ai-mod-1's KW)");
    println!("     shard_hash = {}...", short(&shard_hash, 16));
    println!("     entries:    1 (the observation about composition)");
    println!("     successor:  {} (ai-mod-2)", short(ai_mod_2.did().as_str(), 16));
    println!();

    // 2. Moderator succession in the room's log.
    let succ = room.declare_succession(
        &ai_mod_1,
        &ai_mod_2,
        &shard_hash,
        "room became active; ai-mod-1 graduates to a sibling",
    )?;
    let succ_hash = succ.hash()?;
    println!("  2. moderator_succession (in the room's log)");
    println!("     outgoing:   {} (ai-mod-1)", short(ai_mod_1.did().as_str(), 16));
    println!("     incoming:   {} (ai-mod-2)", short(ai_mod_2.did().as_str(), 16));
    println!("     shard_ref:  {}...", short(&shard_hash, 16));
    println!("     record hash: {}...", short(&succ_hash, 16));
    println!();

    // 3. Sibling declared in the Commons.
    let sib = commons.declare_sibling(
        &ai_mod_1,
        &ai_mod_2,
        ai_mod_1_home.room().world_id(),
        &shard_hash,
        "room became active; sibling takes over moderator duties",
    )?;
    let sib_hash = chat_world::hash::hash_of(&sib)?;
    println!("  3. sibling_declared (in the Commons)");
    println!("     parent:     {} (ai-mod-1)", short(ai_mod_1.did().as_str(), 16));
    println!("     sibling:    {} (ai-mod-2)", short(ai_mod_2.did().as_str(), 16));
    println!("     parent_kw:  {}...", short(ai_mod_1_home.room().world_id().as_str(), 16));
    println!("     shard_ref:  {}...", short(&shard_hash, 16));
    println!("     record hash: {}...", short(&sib_hash, 16));
    println!();

    // Verify all three logs.
    println!("{}", "-".repeat(74));
    println!("Verification (each log on its own):");
    let home_ok = verify_room(ai_mod_1_home.room()).is_ok();
    let room_ok = verify_room(&room).is_ok();
    let commons_ok = verify_commons(&commons).is_ok();
    println!("  ai-mod-1 KW:   {}", if home_ok { "verifies" } else { "FAILED" });
    println!("  the room:      {}", if room_ok { "verifies" } else { "FAILED" });
    println!("  the Commons:   {}", if commons_ok { "verifies" } else { "FAILED" });
    println!();

    // Cross-check: the shard_hash in the succession and the
    // sibling declaration matches the shard export's own hash.
    println!("{}", "-".repeat(74));
    println!("Cross-check (a reader with all three logs):");
    let found_shard = ai_mod_1_home.room().records().iter()
        .find_map(|r| {
            if let Record::KnowledgeShardExport(k) = r {
                let h = r.hash().ok()?;
                if h == shard_hash { Some(k) } else { None }
            } else { None }
        });
    match found_shard {
        Some(k) => {
            println!("  shard export found in ai-mod-1 KW at {}", short(&shard_hash, 16));
            println!("    target_room:  {}", short(k.target_room_id.as_str(), 16));
            println!("    successor:    {}", short(k.successor_id.as_str(), 16));
        }
        None => println!("  shard export NOT FOUND — cross-reference is broken"),
    }

    let found_succ = room.records().iter().find_map(|r| {
        if let Record::ModeratorSuccession(s) = r { Some(s) } else { None }
    });
    match found_succ {
        Some(s) => {
            println!("  succession in room: outgoing={}, incoming={}",
                     short(s.outgoing_id.as_str(), 16),
                     short(s.incoming_id.as_str(), 16));
            println!("    shard_ref matches:  {}", s.knowledge_shard_hash == shard_hash);
        }
        None => println!("  succession not found"),
    }

    let found_sib = commons.records().iter().find_map(|r| {
        if let CommonsRecord::SiblingDeclared(s) = r { Some(s) } else { None }
    });
    match found_sib {
        Some(s) => {
            println!("  sibling in commons: parent={}, sibling={}",
                     short(s.parent_id.as_str(), 16),
                     short(s.sibling_id.as_str(), 16));
            println!("    shard_ref matches:  {}", s.shard_hash == shard_hash);
        }
        None => println!("  sibling not found"),
    }
    println!();

    println!("What this establishes:");
    println!("  - A room's moderator role can be handed on. The outgoing");
    println!("    AI's KnowledgeWorld emits a shard export (a designated");
    println!("    subset of its memory for the incoming). The room records");
    println!("    the succession; the Commons records the sibling.");
    println!("  - Three records, three signatures. Succession is triple-");
    println!("    signed (outgoing + incoming + room). Sibling is triple-");
    println!("    signed (parent + sibling + commons). Shard export is");
    println!("    signed by the KnowledgeWorld's own key.");
    println!("  - All three logs verify independently. The cross-log");
    println!("    binding (shard_hash == export's record hash) is a");
    println!("    reader-side check when all three are in hand.");
    println!("  - ai-mod-1's KnowledgeWorld remains as archive. It");
    println!("    accepts no further observations; only shard exports.");
    println!("  - ai-mod-2 now holds the moderator role. It is a distinct");
    println!("    key with its own KnowledgeWorld; the sandbox between");
    println!("    ai-mod-1 and ai-mod-2 is what the key is.");
    println!();
    println!("Anchor (public domain, Emily Dickinson):");
    println!("  'Forever – is composed of Nows –'");
    println!("  'Tis not a different time –'");

    Ok(())
}
