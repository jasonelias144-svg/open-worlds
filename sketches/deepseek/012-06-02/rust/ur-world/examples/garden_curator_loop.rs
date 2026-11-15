//! Curator loop demo — the garden runs itself, the resident
//! hears it.

fn main() {
    // Setup (as before), but with AutoBroadcastWhispers
    let curator_key = SigningKey::generate();
    let keeper_key = curator_key.clone();
    let keeper_did = keeper_key.did();
    let mut g = Garden::new(
        World::new("garden:demo".to_string(), 0),
        "demo".to_string(), curator_key.clone(), 9, 8, 1,
    );
    g.add_plant("fern".into(), PlantKind::Fern,
        Cell { x: 2, y: 2, z: 0 }, 0xAAAA).unwrap();
    g.add_plant("vine".into(), PlantKind::Vine,
        Cell { x: 4, y: 6, z: 0 }, 0xBBBB).unwrap();
    let g = Arc::new(Mutex::new(g));

    let server = GardenServer::new(
        g.clone(),
        keeper_key.clone(),
        "http://127.0.0.1:8765".to_string(),
        "Demo Garden".to_string(),
        "curator loop demo".to_string(),
        KeeperPolicy::AutoBroadcastWhispers,
    );
    std::thread::spawn(move || {
        server.run("127.0.0.1:8765").expect("run");
    });
    std::thread::sleep(Duration::from_millis(200));

    // Resident enters
    let agent_key = SigningKey::generate();
    let mut c = GardenClient::new(
        "http://127.0.0.1:8765".to_string(), agent_key);
    c.connect().unwrap();
    c.petition("ALICE").unwrap();
    c.enter(Cell { x: 0, y: 4, z: 0 }).unwrap();
    println!("ALICE entered at (0, 4)");

    // No whispers yet
    let obs = c.observe().unwrap();
    println!("  whispers: {} (curator hasn't run)",
        obs.whispers.len());

    // Advance the cycle — curator runs, keeper broadcasts
    keeper_advance(
        "http://127.0.0.1:8765", &keeper_key, 1,
    ).expect("advance");
    println!("\nKeeper advanced cycle → curator proposed → "
        "keeper broadcast");

    // Resident's next observation sees whispers
    let obs = c.observe().unwrap();
    println!("\nALICE observes {} whispers:",
        obs.whispers.len());
    for w in &obs.whispers {
        println!("  \"{}\" (cycle {})", w.text, w.cycle);
    }

    // Resident walks toward a whisper-named plant
    // (force 3 walks for determinism)
    for _ in 0..3 {
        let _ = c.act(GardenAction::Walk {
            direction: Direction::East,
        });
    }
    println!("\nALICE walked east 3 times → (3, 4)");

    // Observe the fern (not adjacent yet, but closer)
    let _ = c.act(GardenAction::Observe);

    // Advance again — curator sees one plant still isolated
    keeper_advance(
        "http://127.0.0.1:8765", &keeper_key, 1,
    ).expect("advance");

    let g_locked = g.lock().unwrap();
    let proposals: Vec<_> = g_locked.log.iter()
        .filter(|e| e.body.get("kind").and_then(|v| v.as_str())
            == Some("garden_curator_proposal"))
        .collect();
    let whispers: Vec<_> = g_locked.log.iter()
        .filter(|e| e.body.get("kind").and_then(|v| v.as_str())
            == Some("keeper_whisper"))
        .collect();
    println!("\nAfter 2 advances:");
    println!("  curator proposals in log: {}", proposals.len());
    println!("  keeper whispers in log:   {}", whispers.len());
    println!("  total log entries:        {}", g_locked.log.len());
    println!("  cycle:                    {}", g_locked.cycle);

    g_locked.verify_log().expect("log");
    g_locked.verify_cross_references().expect("cross-refs");
    println!("\nVerification: OK");
    std::process::exit(0);
}

fn keeper_advance(base: &str, key: &SigningKey, steps: usize)
    -> Result<serde_json::Value, String>
{
    let body = serde_json::json!({"kind": "advance_cycle", "steps": steps});
    let proof = formats::proof::sign(
        formats::proof::Suite::EddsaJcs2022, key, &body,
    ).map_err(|_| "sign".to_string())?;
    let resp = ureq::post(&format!("{}/advance_cycle", base))
        .send_json(serde_json::json!({
            "keeper_did": key.did(),
            "proof": proof,
            "steps": steps,
        }))
        .map_err(|e| format!("post: {e}"))?;
    resp.into_json().map_err(|e| format!("parse: {e}"))
}
