//! Integration test for the external verifier.
//!
//! Starts a garden server, runs the verify_garden example as
//! a subprocess, and asserts the exit code.
//!
//! This is the closest test to "a stranger can verify this":
//! the verifier runs in its own process, with no shared state,
//! and succeeds or fails based purely on what the garden
//! serves over HTTP.

use std::process::Command;
use std::sync::{Arc, Mutex};
use std::time::Duration;

use ur_world::garden::{Garden, GardenAction, PlantKind};
use ur_world::garden_server::{GardenServer, KeeperPolicy};
use ur_world::world::{Cell, World};
use formats::proof::SigningKey;

fn build_garden_and_server()
    -> (Arc<Mutex<Garden>>, SigningKey, String)
{
    let key = SigningKey::generate();
    let mut g = Garden::new(
        World::new("garden:test".to_string(), 0),
        "test".to_string(), key.clone(), 9, 8, 1,
    );
    g.add_plant("fern".into(), PlantKind::Fern,
        Cell { x: 2, y: 2, z: 0 }, 0xAAAA).unwrap();
    g.add_plant("vine".into(), PlantKind::Vine,
        Cell { x: 4, y: 6, z: 0 }, 0xBBBB).unwrap();
    let g = Arc::new(Mutex::new(g));

    let port = 18800;
    let base = format!("http://127.0.0.1:{port}");
    let server = GardenServer::new(
        g.clone(),
        key.clone(),
        base.clone(),
        "test garden".into(),
        "external verify test".into(),
        KeeperPolicy::AutoBroadcastWhispers,
    );
    std::thread::spawn(move || {
        server.run(&format!("127.0.0.1:{port}")).ok();
    });
    std::thread::sleep(Duration::from_millis(200));
    (g, key, base)
}

fn run_verifier(base: &str) -> std::process::Output {
    Command::new(env!("CARGO"))
        .args([
            "run", "--quiet",
            "--example", "verify_garden",
            "--", base,
        ])
        .output()
        .expect("spawn verify_garden")
}

#[test]
fn external_verifier_passes_fresh_garden() {
    let (_g, _key, base) = build_garden_and_server();
    let out = run_verifier(&base);
    let stdout = String::from_utf8_lossy(&out.stdout);
    let stderr = String::from_utf8_lossy(&out.stderr);
    assert!(
        out.status.success(),
        "verifier failed:\nstdout: {stdout}\nstderr: {stderr}");
    assert!(stdout.contains("PASSED"));
    assert!(stdout.contains("reconstructed from log"));
}

#[test]
fn external_verifier_passes_after_activity() {
    let (g, _key, base) = build_garden_and_server();

    // Drive some activity over HTTP
    let agent = SigningKey::generate();
    let mut c = ur_world::garden_client::GardenClient::new(
        base.clone(), agent);
    c.connect().unwrap();
    c.petition("A").unwrap();
    c.enter(Cell { x: 0, y: 4, z: 0 }).unwrap();
    c.act(GardenAction::Walk {
        direction: ur_world::garden::Direction::East,
    }).unwrap();
    c.act(GardenAction::Observe).unwrap();
    c.act(GardenAction::Speak {
        text: "hi".into(),
    }).unwrap();

    g.lock().unwrap().advance_cycle(2).unwrap();

    let out = run_verifier(&base);
    assert!(out.status.success(),
        "verifier failed after activity:\n\
         stdout: {}\nstderr: {}",
        String::from_utf8_lossy(&out.stdout),
        String::from_utf8_lossy(&out.stderr));
}

#[test]
fn external_verifier_fails_on_tampered_log() {
    let (g, _key, base) = build_garden_and_server();

    // Tamper an entry in the garden's log
    {
        let mut gg = g.lock().unwrap();
        let idx = gg.log.iter().position(|e| {
            e.body.get("kind").and_then(|v| v.as_str())
                == Some("plant_added")
        }).unwrap();
        // Change the plant's position — hash will no longer
        // match, and the proof won't verify.
        gg.log[idx].body["position"] =
            serde_json::json!([99, 99, 0]);
    }

    let out = run_verifier(&base);
    assert!(!out.status.success(),
        "verifier should have failed on tampered log");
    let stdout = String::from_utf8_lossy(&out.stdout);
    assert!(stdout.contains("FAILED"));
}
