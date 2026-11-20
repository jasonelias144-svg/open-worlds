use chat_world::error::Result;
use chat_world::head::{emit_head, verify_head};
use chat_world::home::HomeRoom;
use chat_world::record::Record;
use chat_world::verify::verify_head_against_log;
use chat_world::Keypair;

fn short(s: &str, n: usize) -> String {
    let s = s.strip_prefix("did:key:").unwrap_or(s);
    s.chars().take(n).collect()
}

fn main() -> Result<()> {
    println!("{}", "=".repeat(74));
    println!("World Heads — signed commitments, histories at home");
    println!("{}", "=".repeat(74));
    println!();

    let alice = Keypair::generate();
    let mut home = HomeRoom::create(alice.clone(), "alice's home")?;

    // Alice journals a few things
    home.journal("First entry.")?;
    home.journal("Second entry.")?;
    home.journal("Third entry.")?;
    println!("Alice's home: {} records (created + 3 journals)", home.room().records().len());

    // Emit head H1
    let h1 = emit_head(home.room())?;
    println!("H1 emitted:   log_len={}, chain_head={}...",
             h1.log_len, short(&h1.chain_head, 16));
    println!("  state_hash: {}...", short(&h1.state_hash, 16));

    // Alice journals two more
    home.journal("Fourth entry.")?;
    home.journal("Fifth entry.")?;
    println!();
    println!("Alice journals 2 more; log now has {} records", home.room().records().len());

    // Emit head H2
    let h2 = emit_head(home.room())?;
    println!("H2 emitted:   log_len={}, chain_head={}...",
             h2.log_len, short(&h2.chain_head, 16));

    // ---- Verification: fresh head ----
    println!();
    println!("{}", "-".repeat(74));
    println!("Verification:");
    match verify_head(&h2, home.room()) {
        Ok(()) => println!("  H2 vs current room (log_len={}): verifies", h2.log_len),
        Err(e) => println!("  H2 vs current room: FAILED: {e}"),
    }

    // H1 vs current room should fail (log grew)
    match verify_head(&h1, home.room()) {
        Ok(()) => println!("  H1 vs current room: UNEXPECTED pass"),
        Err(_) => println!("  H1 vs current room: correctly fails (log has grown past H1)"),
    }

    // H1 vs the log prefix (this is what a peer does when they
    // receive a head + the full log after the fact)
    let records = home.room().records().to_vec();
    match verify_head_against_log(&h1, &records) {
        Ok(()) => println!("  H1 vs log prefix (len={}): verifies", h1.log_len),
        Err(e) => println!("  H1 vs log prefix: FAILED: {e}"),
    }
    match verify_head_against_log(&h2, &records) {
        Ok(()) => println!("  H2 vs log prefix (len={}): verifies", h2.log_len),
        Err(e) => println!("  H2 vs log prefix: FAILED: {e}"),
    }

    // ---- Federation story: Bob receives H1 only ----
    println!();
    println!("{}", "-".repeat(74));
    println!("Federation scenario: Bob receives H1 from Alice (no log yet).");
    println!("  Bob stores H1. Its signature verifies.");
    println!("  Bob now has a binding commitment: if Alice ever produces a");
    println!("  log whose prefix has length {} but whose last record is not", h1.log_len);
    println!("  {}, Bob knows the log was rewritten.", short(&h1.chain_head, 16));

    // ---- Tampering: Bob receives a tampered log ----
    println!();
    println!("{}", "-".repeat(74));
    println!("Tampering scenario:");
    let mut tampered = records.clone();
    // Tamper record 2 (a journal message)
    if let Record::Message(m) = &mut tampered[2] {
        m.text = "TAMPERED".into();
    }
    match verify_head_against_log(&h1, &tampered) {
        Ok(()) => println!("  H1 vs tampered log: UNEXPECTED pass"),
        Err(e) => println!("  H1 vs tampered log: correctly fails: {e}"),
    }

    // Shortened log (removed the last record)
    let shortened = records[..records.len() - 1].to_vec();
    match verify_head_against_log(&h2, &shortened) {
        Ok(()) => println!("  H2 vs shortened log: UNEXPECTED pass"),
        Err(e) => println!("  H2 vs shortened log: correctly fails: {e}"),
    }

    // ---- Extension is fine ----
    println!();
    println!("Extension scenario:");
    println!("  The log grew from {} to {} records.", h1.log_len, h2.log_len);
    match verify_head_against_log(&h1, &records) {
        Ok(()) => println!("  H1 still verifies against the extended log's prefix. ✓"),
        Err(e) => println!("  H1 vs extended log: FAILED: {e}"),
    }

    println!();
    println!("What this establishes:");
    println!("  - A head is a small, signed commitment: chain_head,");
    println!("    log_len, state_hash, template_hash, world_id, ts.");
    println!("  - It is a published artifact, not a log record. The log");
    println!("    stays clean; heads are on demand.");
    println!("  - A peer can verify a head against a log prefix (the");
    println!("    world has grown since, but the prefix is intact).");
    println!("  - Tampering with any record breaks the chain, so the");
    println!("    head's chain_head no longer matches.");
    println!("  - Removing records makes the log shorter than the head");
    println!("    claims, which fails.");
    println!("  - Extension is fine: the head verifies against the prefix.");
    println!();
    println!("Anchor (public domain, Emily Dickinson):");
    println!("  'Forever – is composed of Nows –'");
    println!("  'Tis not a different time –'");

    Ok(())
}
