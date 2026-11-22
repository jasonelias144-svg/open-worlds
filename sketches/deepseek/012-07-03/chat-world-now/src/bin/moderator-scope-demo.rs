
use chat_world::error::Result;
use chat_world::home::HomeRoom;
use chat_world::verify::verify_moderator_scope;
use chat_world::{Keypair, Room, RoomTemplate};

fn short(s: &str) -> String {
    let s = s.strip_prefix("did:key:").unwrap_or(s);
    s.chars().take(12).collect()
}

fn report(label: &str, r: Result<()>) {
    match r {
        Ok(()) => println!("  {label}: PASS"),
        Err(e) => println!("  {label}: FAIL ({e})"),
    }
}

fn main() -> Result<()> {
    println!("{}", "=".repeat(74));
    println!("Moderator Scope — the one-moderator-room rule as a pair check");
    println!("{}", "=".repeat(74));
    println!();

    let ai_kp = Keypair::generate();
    let kw_kp = Keypair::generate();
    let mut kw = HomeRoom::create(ai_kp.clone(), kw_kp, "ai memory")?;
    println!("AI:  {}", short(ai_kp.did().as_str()));
    println!("KW:  {}", short(kw.room().world_id().as_str()));
    println!();

    let alice = Keypair::generate();
    let mut room_a = Room::create(
        RoomTemplate::chat("a", "first room"),
        Keypair::generate(),
        &alice,
    )?;
    let mut room_b = Room::create(
        RoomTemplate::chat("b", "second room"),
        Keypair::generate(),
        &alice,
    )?;
    println!("Room A: {}", short(room_a.world_id().as_str()));
    println!("Room B: {}", short(room_b.world_id().as_str()));
    println!();

    println!("1. AI declares scope [A].");
    kw.declare_moderator_scope(vec![room_a.world_id().clone()], vec![])?;

    println!("2. AI joins A at control.");
    room_a.join(&ai_kp, "control", true)?;

    println!("3. Pair check (KW, A):");
    report("KW vs A", verify_moderator_scope(&kw.room().log(), &room_a.log()));
    println!();

    println!("4. AI joins B at control (no scope update).");
    room_b.join(&ai_kp, "control", true)?;

    println!("5. Pair check (KW, B) — should fail (B not declared):");
    report("KW vs B", verify_moderator_scope(&kw.room().log(), &room_b.log()));
    println!();

    println!("6. AI declares scope [A, B] — over-reach.");
    kw.declare_moderator_scope(
        vec![room_a.world_id().clone(), room_b.world_id().clone()],
        vec![],
    )?;

    println!("7. Pair check (KW, A) — should fail (over-reach, 2 rooms):");
    report("KW vs A", verify_moderator_scope(&kw.room().log(), &room_a.log()));
    println!();

    println!("8. AI leaves A.");
    room_a.leave(&ai_kp)?;

    println!("9. AI declares scope [B].");
    kw.declare_moderator_scope(vec![room_b.world_id().clone()], vec![])?;

    println!("10. Pair check (KW, B) — should pass:");
    report("KW vs B", verify_moderator_scope(&kw.room().log(), &room_b.log()));

    println!("11. Pair check (KW, A) — vacuous pass (AI left A):");
    report("KW vs A", verify_moderator_scope(&kw.room().log(), &room_a.log()));
    println!();

    println!("The rule is a pair check: the AI's KW and the room together.");
    println!("A single log verifies on its own; only the pair proves the");
    println!("AI is honest about which human-facing room it moderates.");
    println!();
    println!("Anchor (public domain, Emily Dickinson):");
    println!("  'One need not be a Chamber – to be Haunted –'");
    println!("  'One need not be a House –'");

    Ok(())
}

