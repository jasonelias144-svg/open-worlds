//! Verify the garden implementation against a fixed reference.
//!
//! The reference file `vectors/garden_reference.json` contains
//! a scenario and the exact hashes a correct implementation
//! must produce. Any language's garden implementation that
//! passes this test is faithful to the Python reference.

use std::fs;
use std::path::PathBuf;

use serde::Deserialize;

use crate::garden::{
    Direction, Garden, GardenAction, PlantKind,
};
use crate::world::{Cell, World};
use formats::proof::{Proof, SigningKey};
use serde_json::Value;

#[derive(Deserialize)]
struct Vector {
    scenario: Scenario,
    expected: Expected,
}

#[derive(Deserialize)]
struct Scenario {
    garden: GardenCfg,
    admitted: Vec<AdmittedAgent>,
    actions: Vec<ActionSpec>,
}

#[derive(Deserialize)]
struct GardenCfg {
    entity_id: String,
    width: i64,
    height: i64,
    depth: i64,
    curator_seed_hex: String,
}

#[derive(Deserialize)]
struct AdmittedAgent {
    name: String,
    seed_hex: String,
}

#[derive(Deserialize)]
#[serde(tag = "type")]
enum ActionSpec {
    #[serde(rename = "add_plant")]
    AddPlant {
        id: String,
        kind: String,
        position: [i64; 3],
        seed: u64,
    },
    #[serde(rename = "admit")]
    Admit { agent: String },
    #[serde(rename = "enter")]
    Enter { agent: String, at: [i64; 3] },
    #[serde(rename = "walk")]
    Walk { agent: String, direction: String },
    #[serde(rename = "observe")]
    Observe { agent: String },
    #[serde(rename = "speak")]
    Speak { agent: String, text: String },
    #[serde(rename = "cycle_advance")]
    CycleAdvance { steps: usize },
}

#[derive(Deserialize)]
struct Expected {
    log_length: usize,
    entry_hashes: Vec<String>,
    plant_event_hashes: std::collections::HashMap<String, Vec<String>>,
    cross_reference_count: usize,
    alice_final_position: Option<[i64; 3]>,
    bob_final_position: Option<[i64; 3]>,
}

fn load_vector() -> Vector {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("..")
        .join("vectors")
        .join("garden_reference.json");
    let text = fs::read_to_string(&path)
        .unwrap_or_else(|_| panic!(
            "vectors/garden_reference.json not found at {:?}; \
             run `python vectors/gen_garden_reference.py` first",
            path));
    serde_json::from_str(&text).expect("vector file is malformed")
}

fn signing_key_from_seed(seed_hex: &str) -> SigningKey {
    let bytes = hex::decode(seed_hex).expect("bad seed hex");
    SigningKey::from_ed25519_seed(&bytes)
        .expect("bad seed length")
}

fn direction_from_str(s: &str) -> Direction {
    match s {
        "N" => Direction::North,
        "S" => Direction::South,
        "E" => Direction::East,
        "W" => Direction::West,
        _ => panic!("bad direction"),
    }
}

#[test]
fn garden_reference_scenario() {
    let v = load_vector();

    // Construct the curator key from the seed.
    let curator_key = signing_key_from_seed(&v.scenario.garden.curator_seed_hex);

    // Build the world and garden.
    let world = World::new(
        v.scenario.garden.entity_id.clone(),
        0,
    );
    let mut garden = Garden::new(
        world,
        "fixed test vector".to_string(),
        curator_key,
        v.scenario.garden.width,
        v.scenario.garden.height,
        v.scenario.garden.depth,
    );

    // Derive agent DIDs from seeds; map name → DID.
    let mut agent_dids: std::collections::HashMap<String, String> =
        std::collections::HashMap::new();
    for a in &v.scenario.admitted {
        let key = signing_key_from_seed(&a.seed_hex);
        agent_dids.insert(a.name.clone(), key.did());
    }

    // Run the actions.
    for action in &v.scenario.actions {
        match action {
            ActionSpec::AddPlant { id, kind, position, seed } => {
                let pk = match kind.as_str() {
                    "fern" => PlantKind::Fern,
                    "tree" => PlantKind::Tree,
                    "vine" => PlantKind::Vine,
                    other => panic!("unknown kind {}", other),
                };
                garden.add_plant(
                    id.clone(),
                    pk,
                    Cell { x: position[0], y: position[1], z: position[2] },
                    *seed,
                ).unwrap();
            }
            ActionSpec::Admit { agent } => {
                let did = agent_dids.get(agent).expect("unknown agent");
                garden.admit(did, agent).unwrap();
            }
            ActionSpec::Enter { agent, at } => {
                let did = agent_dids.get(agent).expect("unknown agent");
                garden.apply_action(did, GardenAction::Enter {
                    at: Cell { x: at[0], y: at[1], z: at[2] },
                }).unwrap();
            }
            ActionSpec::Walk { agent, direction } => {
                let did = agent_dids.get(agent).expect("unknown agent");
                garden.apply_action(did, GardenAction::Walk {
                    direction: direction_from_str(direction),
                }).unwrap();
            }
            ActionSpec::Observe { agent } => {
                let did = agent_dids.get(agent).expect("unknown agent");
                garden.apply_action(did, GardenAction::Observe).unwrap();
            }
            ActionSpec::Speak { agent, text } => {
                let did = agent_dids.get(agent).expect("unknown agent");
                garden.apply_action(did, GardenAction::Speak {
                    text: text.clone(),
                }).unwrap();
            }
            ActionSpec::CycleAdvance { steps } => {
                garden.advance_cycle(*steps).unwrap();
            }
        }
    }

    // ── Assertions against the vector ─────────────────────

    // 1. Log length
    assert_eq!(
        garden.log.len(),
        v.expected.log_length,
        "log length mismatch"
    );

    // 2. Each entry's hash
    for (i, entry) in garden.log.iter().enumerate() {
        assert_eq!(
            entry.hash,
            v.expected.entry_hashes[i],
            "entry {} hash mismatch",
            i
        );
    }

    // 3. Plant event hashes
    for (pid, expected_hashes) in &v.expected.plant_event_hashes {
        let plant = garden.plants_all.get(pid)
            .unwrap_or_else(|| panic!("plant {} missing", pid));
        let actual: Vec<&str> = plant.events().iter()
            .map(|e| e.hash.as_str())
            .collect();
        assert_eq!(
            actual,
            expected_hashes.iter().map(|s| s.as_str()).collect::<Vec<_>>(),
            "plant {} event hashes mismatch",
            pid
        );
    }

    // 4. Cross-references
    let xref_count = garden.log.iter().filter(|e| {
        e.body.get("kind").and_then(|v| v.as_str())
            == Some("agent_observed")
            && e.body.get("result").and_then(|v| v.as_str())
                == Some("observed_plant")
    }).count();
    assert_eq!(
        xref_count,
        v.expected.cross_reference_count,
        "cross-reference count mismatch"
    );

    // 5. Final positions
    if let Some(expected_pos) = &v.expected.alice_final_position {
        let did = agent_dids.get("ALICE").unwrap();
        let actual = garden.agent_positions.get(did).unwrap();
        assert_eq!(
            [actual.x, actual.y, actual.z],
            *expected_pos,
            "ALICE final position mismatch"
        );
    }
    if let Some(expected_pos) = &v.expected.bob_final_position {
        let did = agent_dids.get("BOB").unwrap();
        let actual = garden.agent_positions.get(did).unwrap();
        assert_eq!(
            [actual.x, actual.y, actual.z],
            *expected_pos,
            "BOB final position mismatch"
        );
    }

    // 6. Chain integrity
    garden.verify_log().expect("chain verification failed");
    garden.verify_cross_references()
        .expect("cross-reference verification failed");
}
