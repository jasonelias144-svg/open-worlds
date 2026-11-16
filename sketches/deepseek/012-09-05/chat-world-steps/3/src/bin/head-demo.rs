use chat_world::error::Result;
use chat_world::verify::verify_room;
use chat_world::{Keypair, Room, RoomTemplate};

fn short(s: &str, n: usize) -> String {
    let s = s.strip_prefix("did:key:").unwrap_or(s);
    s.chars().take(n).collect()
}

fn main() -> Result<()> {
    println!("{}", "=".repeat(74));
    println!("Signed Heads — batched commitment, offline key");
    println!("{}", "=".repeat(74));
    println!();

    let alice = Keypair::generate();
    let room_kp = Keypair::generate();
    let bob = Keypair::generate();

    // A room in head mode: the room signs a head every 3 appends.
    let mut template = RoomTemplate::chat("head-mode-v1", "how does batched signing work?");
    template.head_interval = 3;

    let mut room = Room::create(template, room_kp, &alice)?;
    println!("Room:     {}", short(room.world_id().as_str(), 32));
    println!("Creator:  {} (alice)", short(alice.did().as_str(), 32));
    println!("Mode:     head_interval = 3 (sign every 3 appends)");
    println!("Tick = length (a room's time is its record count)");
    println!();

    room.join(&bob, "communicate", false)?;
    // records.len() = 2, appends = 1, no head yet

    // 10 posts. Heads expected at length 4, 7, 10.
    for i in 1..=10 {
        room.post(
            &bob,
            &format!("message {i}: a small contribution"),
            "normal",
        )?;
        let n = room.heads().len();
        let rec_len = room.records().len();
        if n > 0 {
            let last_head_len = room.heads()[n - 1].length;
            if last_head_len as usize == rec_len {
                println!(
                    "  post {i:>2}: head emitted at length={last_head_len}, last={}...",
                    short(&room.heads()[n - 1].last, 16)
                );
            }
        }
    }
    println!();

    // Summary
    println!("Log length: {}", room.records().len());
    println!("Heads emitted: {}", room.heads().len());
    for (i, head) in room.heads().iter().enumerate() {
        println!(
            "  head {i}: length={}, tick={}, last={}...",
            head.length, head.tick, short(&head.last, 16)
        );
    }
    println!();

    // Uncommitted tail
    let last_head_len = room.heads().last().map(|h| h.length).unwrap_or(0);
    let tail = room.records().len() as u64 - last_head_len;
    if tail > 0 {
        println!(
            "Uncommitted tail: {tail} record(s) beyond the last head (length {last_head_len})."
        );
        println!(
            "  These have author proofs but no head yet; the room has not"
        );
        println!(
            "  committed to them. The next head (at the next interval boundary)"
        );
        println!(
            "  will cover them."
        );
    }
    println!();

    // Verify all heads
    println!("{}", "-".repeat(74));
    println!("Head verification:");
    for (i, head) in room.heads().iter().enumerate() {
        match room.verify_head(head) {
            Ok(()) => println!("  head {i}: verifies"),
            Err(e) => println!("  head {i}: FAILED: {e}"),
        }
    }
    println!();

    // Room verification
    match verify_room(&room) {
        Ok(()) => println!("Room verifies offline: chain + author proofs + heads."),
        Err(e) => println!("Room FAILED: {e}"),
    }
    println!();

    // Tampering demos
    println!("{}", "-".repeat(74));
    println!("Tampering scenarios:");
    let mut h = room.heads()[0].clone();
    h.last = "00".repeat(32);
    match room.verify_head(&h) {
        Ok(()) => println!("  last tampered: UNEXPECTED pass"),
        Err(_) => println!("  last tampered: correctly fails (chain/last mismatch)"),
    }
    let mut h = room.heads()[0].clone();
    h.tick += 1;
    match room.verify_head(&h) {
        Ok(()) => println!("  tick tampered: UNEXPECTED pass"),
        Err(_) => println!("  tick tampered: correctly fails (tick != length)"),
    }
    let mut h = room.heads()[0].clone();
    h.length += 100;
    match room.verify_head(&h) {
        Ok(()) => println!("  length tampered: UNEXPECTED pass"),
        Err(_) => println!("  length tampered: correctly fails (exceeds log)"),
    }
    println!();

    println!("What this establishes:");
    println!("  - The room's signature moves from each record to the head.");
    println!("    Every record still carries its author's proof; the room");
    println!("    commits to batches via signed heads.");
    println!("  - A head is small: format, world, length, last, tick, proof.");
    println!("    Tick = length: a room's time is its record count.");
    println!("  - A head alone is a binding commitment; a peer can verify");
    println!("    it without the full log. Federation follows.");
    println!("  - Records past the last head are the uncommitted tail;");
    println!("    they have author proofs and join the log's chain, but the");
    println!("    room has not yet committed to them. The next head will.");
    println!("  - The room's signing key need only be live at batch");
    println!("    boundaries. This is the security win.");
    println!();
    println!("Anchor (public domain, Emily Dickinson):");
    println!("  'Forever – is composed of Nows –'");
    println!("  'Tis not a different time –'");

    Ok(())
}
