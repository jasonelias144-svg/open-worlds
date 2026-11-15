//! Cross-implementation verification.
//!
//! Two independent implementations of eddsa-jcs-2022 — one in
//! Rust, one in Python — must reach the same verdict on the
//! same garden. Agreement is the strongest form of validation
//! for a standard.

use std::path::PathBuf;
use std::process::Command;
use std::sync::{Arc, Mutex};
use std::time::Duration;

use formats::proof::SigningKey;
use ur_world::garden::{Garden, PlantKind};
use ur_world::garden_server::{GardenServer, KeeperPolicy};
use ur_world::world::{Cell, World};

fn start_garden(port: u16) -> (Arc<Mutex<Garden>>, SigningKey, String) {
    let key = SigningKey::generate();
    let mut g = Garden::new(
        World::new("garden:test".to_string(), 0),
        "test".into(), key.clone(), 9, 8, 1,
    );
    g.add_plant("fern".into(), PlantKind::Fern,
        Cell { x: 2, y: 2, z: 0 }, 0xAAAA).unwrap();
    g.add_plant("vine".into(), PlantKind::Vine,
        Cell { x: 4, y: 6, z: 0 }, 0xBBBB).unwrap();
    let g = Arc::new(Mutex::new(g));
    let base = format!("http://127.0.0.1:{port}");
    let server = GardenServer::new(
        g.clone(), key.clone(), base.clone(),
        "test garden".into(), "cross-impl".into(),
        KeeperPolicy::AutoBroadcastWhispers,
    );
    std::thread::spawn(move || {
        server.run(&format!("127.0.0.1:{port}")).ok();
    });
    std::thread::sleep(Duration::from_millis(200));
    (g, key, base)
}

fn run_rust(url: &str) -> bool {
    Command::new(env!("CARGO"))
        .args(["run", "--quiet", "--example", "verify_garden",
               "--", url])
        .output()
        .map(|o| o.status.success())
        .unwrap_or(false)
}

fn run_python(url: &str) -> Option<bool> {
    let script = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("examples").join("verify_garden.py");
    let python = std::env::var("PYTHON")
        .unwrap_or_else(|_| "python3".into());
    let out = Command::new(&python)
        .arg(&script).arg(url)
        .output().ok()?;
    out.status.code()?;
    Some(out.status.success())
}

#[test]
fn both_verifiers_agree_on_clean_garden() {
    let (_g, _key, base) = start_garden(18810);
    let rust = run_rust(&base);
    let python = run_python(&base);
    assert!(rust, "Rust verifier should pass a clean garden");
    match python {
        Some(ok) => assert!(ok,
            "Python verifier should pass a clean garden; \
             the two implementations must agree"),
        None => eprintln!(
            "python3 not available — Python check skipped"),
    }
}

#[test]
fn both_verifiers_agree_on_tampered_log() {
    let (g, _key, base) = start_garden(18811);

    // Tamper: change a plant's position in the log
    {
        let mut gg = g.lock().unwrap();
        let idx = gg.log.iter().position(|e| {
            e.body.get("kind").and_then(|v| v.as_str())
                == Some("plant_added")
        }).expect("a plant_added entry exists");
        gg.log[idx].body["position"] =
            serde_json::json!([99, 99, 0]);
    }

    let rust = run_rust(&base);
    let python = run_python(&base);
    assert!(!rust, "Rust verifier must reject a tampered log");
    match python {
        Some(ok) => assert!(!ok,
            "Python verifier must reject a tampered log; \
             the two implementations must agree"),
        None => eprintln!(
            "python3 not available — Python check skipped"),
    }
}

#[test]
fn both_verifiers_agree_after_activity() {
    let (g, _key, base) = start_garden(18812);

    // Drive some activity via the client
    let agent = SigningKey::generate();
    let mut c = ur_world::garden_client::GardenClient::new(
        base.clone(), agent);
    c.connect().unwrap();
    c.petition("A").unwrap();
    c.enter(Cell { x: 0, y: 4, z: 0 }).unwrap();
    c.act(ur_world::garden::GardenAction::Walk {
        direction: ur_world::garden::Direction::East,
    }).unwrap();
    c.act(ur_world::garden::GardenAction::Observe).unwrap();
    g.lock().unwrap().advance_cycle(2).unwrap();

    let rust = run_rust(&base);
    let python = run_python(&base);
    assert!(rust);
    match python {
        Some(ok) => assert!(ok),
        None => eprintln!("python3 not available"),
    }
}
