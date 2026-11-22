use chat_world::error::Result;
use chat_world::joined_room::JoinedRoom;
use chat_world::record::Record;
use chat_world::verify::verify_log;
use chat_world::{Keypair, Room, RoomTemplate};

fn short(s: &str) -> String {
    let s = s.strip_prefix("did:key:").unwrap_or(s);
    s.chars().take(12).collect()
}

fn main() -> Result<()> {
    println!("{}", "=".repeat(74));
    println!("JoinedRoom — a participant posts; the keeper commits");
    println!("{}", "=".repeat(74));
    println!();

    // Alice creates a head-mode room (head_interval = 2).
    let alice = Keypair::generate();
    let room_kp = Keypair::generate();
    let mut template = RoomTemplate::chat("shared", "a shared room");
    template.head_interval = 2;
    let mut alice_room = Room::create(template, room_kp, &alice)?;
    println!("Alice's room: {}", short(alice_room.world_id().as_str()));
    println!("  head_interval: {}", alice_room.head_interval());
    println!();

    // Alice publishes the log (the one artifact Bob needs).
    let log_for_bob = alice_room.log();
    println!("Alice publishes log ({} records).", log_for_bob.records.len());
    println!();

    // Bob fetches and attaches.
    let bob = Keypair::generate();
    let mut bob_joined = JoinedRoom::from_log(log_for_bob, bob.clone())?;
    println!("Bob attaches:   {}", short(bob.did().as_str()));
    println!("  is member: {}", bob_joined.is_member());
    println!();

    // Bob requests join and posts in the same batch.
    println!("Bob builds pending:");
    let join_rec = bob_joined.request_join("communicate", false)?;
    println!("  [1] Join       {}", short(&join_rec.hash()?));
    let msg_rec = bob_joined.post(
        "Hello from Bob — I'm new here.",
        "normal",
    )?;
    println!("  [2] Message    {}", short(&msg_rec.hash()?));
    println!("  is member: {}", bob_joined.is_member());

    // Bob verifies his own pending before sending.
    bob_joined.verify_pending()?;
    println!("  verify_pending: ok");
    println!();

    // Alice receives the batch.
    let batch = bob_joined.export_pending();
    println!("Alice receives {} pending record(s).", batch.len());
    let outcomes = alice_room.accept_pending(&batch)?;
    for (i, o) in outcomes.iter().enumerate() {
        let status = if o.accepted { "accepted" } else { "refused" };
        println!(
            "  [{}] {}  request={}",
            i + 1, status, short(&o.request_hash)
        );
    }
    println!();

    // Alice re-publishes; Bob re-fetches.
    let updated_log = alice_room.log();
    println!("Alice republishes ({} records, {} heads).",
        updated_log.records.len(), updated_log.heads.len());
    verify_log(&updated_log)?;
    println!("  verify_log on new log: ok");
    println!();

    // Bob attaches to the new log.
    bob_joined = JoinedRoom::from_log(updated_log.clone(), bob.clone())?;
    println!("Bob re-attaches to updated log.");
    println!("  is member now: {}", bob_joined.is_member());
    println!();

    // Bob posts a second batch.
    let msg2 = bob_joined.post("A second message, one head later.", "normal")?;
    bob_joined.verify_pending()?;
    println!("Bob posts again: {}", short(&msg2.hash()?));
    let outcomes2 = alice_room.accept_pending(&bob_joined.export_pending())?;
    for (i, o) in outcomes2.iter().enumerate() {
        let status = if o.accepted { "accepted" } else { "refused" };
        println!("  [{}] {}  request={}", i + 1, status, short(&o.request_hash));
    }
    println!();

    // Alice publishes again.
    let final_log = alice_room.log();
    verify_log(&final_log)?;
    println!("Final log: {} records, {} heads. Verifies.",
        final_log.records.len(), final_log.heads.len());
    println!();

    println!("{}", "-".repeat(74));
    println!("Visible log (Alice's view):");
    for entry in final_log.visible_log() {
        let t = entry["type"].as_str().unwrap_or("?");
        let seq = entry["seq"].as_u64().unwrap_or(0);
        match t {
            "message" => {
                let author = entry["author"].as_str().unwrap_or("?");
                let text = entry["text"].as_str().unwrap_or("");
                let trunc: String = text.chars().take(50).collect();
                println!("  [{seq:>3}] {t:10} {:12} {trunc}", short(author));
            }
            "join" => {
                let subj = entry["subject"].as_str().unwrap_or("?");
                let tier = entry["tier"].as_str().unwrap_or("?");
                println!("  [{seq:>3}] {t:10} {:12} tier={tier}", short(subj));
            }
            "created" => println!("  [{seq:>3}] {t}"),
            _ => {}
        }
    }
    println!();

    // Refusal scenario: Bob tries to post too fast.
    println!("{}", "-".repeat(74));
    println!("Refusal scenario: Bob posts twice in one batch (rate limit = 1).");
    let mut limited_room = Room::create({
        let mut t = RoomTemplate::chat("limited", "limited room");
        t.head_interval = 5;
        t.rate_limit_count = 1;
        t.rate_limit_window = 5;
        t
    }, Keypair::generate(), &alice)?;

    // Alice joins Bob first so the batch has a clear slot.
    let log_for_bob2 = limited_room.log();
    let mut bob_joined2 = JoinedRoom::from_log(log_for_bob2, bob.clone())?;
    let j2 = bob_joined2.request_join("communicate", false)?;
    let _ = j2;
    let m1 = bob_joined2.post("first", "normal")?;
    let m2 = bob_joined2.post("second (should be refused)", "normal")?;
    let outcomes = limited_room.accept_pending(&bob_joined2.export_pending())?;
    for (i, o) in outcomes.iter().enumerate() {
        let status = if o.accepted { "accepted" } else {
            let r = o.reason.as_deref().unwrap_or("?");
            return match r {
                _ => { println!("  [{}] refused ({})", i + 1, r); Ok::<(), chat_world::Error>(()) }
            }
        };
        if status == "accepted" {
            println!("  [{}] accepted", i + 1);
        }
    }
    let _ = m1;
    let _ = m2;
    let _ = Record::Message;
    Ok(())
}
