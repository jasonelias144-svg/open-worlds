//! A plant world: its log, its head, its birth, and its template. Tests
//! may unwrap and index.
#![allow(clippy::unwrap_used, clippy::indexing_slicing)]

use formats::records::{check, dial_problems, record_hash};
use plant_world::rule::{Dials, Pot};
use plant_world::vectors::{TRIAL_CODE, TRIAL_TIME};
use plant_world::world::{PlantWorld, did, law_hash, log_problems, template, trial_secret};
use serde_json::{Value, json};

const TIME: &str = "2026-11-15T00:00:00Z";

fn made(dials: Dials, pot: Option<Pot>) -> ([u8; 32], Value, PlantWorld) {
    let keeper = trial_secret(0, "template keeper");
    let template = template(&keeper, TRIAL_CODE.0, TRIAL_CODE.1, TRIAL_TIME).unwrap();
    let secret = trial_secret(1, "plant world");
    let world =
        PlantWorld::new(&did(&secret), &record_hash(&template).unwrap(), dials, pot).unwrap();
    (secret, template, world)
}

fn grown(dials: Dials) -> PlantWorld {
    let (_, _, mut world) = made(dials, None);
    world.grow_until_finished(64).unwrap();
    world
}

#[test]
fn it_grows_then_finishes_once() {
    let mut world = grown(Dials::default());
    let kinds: Vec<&str> = world
        .log()
        .iter()
        .map(|e| e["kind"].as_str().unwrap())
        .collect();
    assert_eq!(
        kinds,
        ["world_created", "grew", "grew", "grew", "grew", "finished"]
    );
    assert_eq!(world.segments().len(), 1 + 2 + 4 + 8);
    assert!(world.finished() && world.frontier().is_empty());
    assert_eq!(world.tick(), 5);
    let length = world.log().len();
    assert!(!world.grow().unwrap());
    assert_eq!(world.log().len(), length);
}

#[test]
fn with_no_water_it_finishes_at_once() {
    let world = grown(Dials {
        water: 0,
        ..Dials::default()
    });
    assert_eq!(world.log().len(), 2);
    assert_eq!(world.log()[1]["kind"], "finished");
    assert!(world.segments().is_empty());
}

#[test]
fn its_log_holds_by_the_common_check_and_by_its_rule() {
    let world = grown(Dials {
        branch_length: 3,
        max_depth: 8,
        ..Dials::default()
    });
    let log = Value::Array(world.log().to_vec());
    assert_eq!(world_log::verify_log(&log).unwrap(), world.last_hash());
    assert!(log_problems(world.log()).is_empty());
}

#[test]
fn the_same_dials_give_the_same_log() {
    let dials = Dials {
        branch_length: 4,
        max_depth: 6,
        ..Dials::default()
    };
    assert_eq!(grown(dials).log(), grown(dials).log());
}

#[test]
fn a_log_cut_short_still_holds_by_its_rule() {
    let world = grown(Dials::default());
    assert!(log_problems(&world.log()[..3]).is_empty());
}

#[test]
fn a_plant_that_didnt_grow_by_its_rule_is_caught() {
    let world = grown(Dials::default());
    // A branch moved, and every hash written again, so the chain holds.
    let mut log = world.log().to_vec();
    log[2]["data"]["segments"][0][2] = json!(1);
    let mut prev = log[1]["hash"].as_str().unwrap().to_string();
    for entry in log.iter_mut().skip(2) {
        let object = entry.as_object_mut().unwrap();
        object.remove("hash");
        object.insert("prev".into(), json!(prev));
        let hash = world_log::digest(entry).unwrap();
        entry["hash"] = json!(hash);
        prev = hash;
    }
    assert!(world_log::verify_log(&Value::Array(log.clone())).is_ok());
    assert_eq!(log_problems(&log), ["[2]: not what the rule makes here"]);
}

#[test]
fn a_log_that_goes_on_past_finished_is_caught() {
    let world = grown(Dials::default());
    let mut log = world.log().to_vec();
    log.push(log[1].clone());
    assert_eq!(log_problems(&log), ["[6]: an entry after `finished`"]);
}

#[test]
fn a_log_of_another_kind_is_refused() {
    assert_eq!(log_problems(&[]), ["the log is empty"]);
    let world = grown(Dials::default());
    let mut log = world.log().to_vec();
    log[0]["data"]["rule"] = json!("another rule");
    assert_eq!(
        log_problems(&log),
        ["[0]: not a plant world's world_created entry"]
    );
    let mut log = world.log().to_vec();
    log[0]["data"]["dials"]["water"] = json!(11);
    assert!(log_problems(&log)[0].starts_with("[0]: water: 11"));
}

#[test]
fn dials_out_of_range_and_bad_names_are_refused() {
    let key = did(&trial_secret(1, "plant world"));
    let hash = "a".repeat(64);
    let bad = Dials {
        max_depth: 13,
        ..Dials::default()
    };
    assert!(PlantWorld::new(&key, &hash, bad, None).is_err());
    assert!(PlantWorld::new("did:web:example.org", &hash, Dials::default(), None).is_err());
    assert!(PlantWorld::new(&key, "A".repeat(64).as_str(), Dials::default(), None).is_err());
    assert!(PlantWorld::new(&key, &hash, Dials::default(), None).is_ok());
}

#[test]
fn its_head_and_birth_hold_and_only_its_key_signs_them() {
    let (secret, template, mut world) = made(
        Dials {
            branch_length: 3,
            max_depth: 5,
            ..Dials::default()
        },
        None,
    );
    world.grow_until_finished(64).unwrap();
    let head = world.head(&secret, TIME).unwrap();
    let fields = check(&head).unwrap();
    assert_eq!(fields["length"], json!(world.log().len()));
    assert_eq!(fields["last"], json!(world.last_hash()));
    assert_eq!(fields["tick"], json!(world.tick()));
    let birth = world.birth(&secret, "A first plant", TIME).unwrap();
    assert_eq!(check(&birth).unwrap()["law"], json!(law_hash().unwrap()));
    assert!(dial_problems(&birth, &template).unwrap().is_empty());
    let other = trial_secret(2, "plant world");
    assert!(world.head(&other, TIME).is_err());
    assert!(world.birth(&other, "Not mine", TIME).is_err());
}

#[test]
fn the_template_names_each_dial_with_its_range() {
    let (_, template, _) = made(Dials::default(), None);
    let fields = check(&template).unwrap();
    let parameters = fields["parameters"].as_object().unwrap();
    assert_eq!(parameters.len(), 4);
    assert_eq!(parameters["maxDepth"]["min"], 1);
    assert_eq!(parameters["maxDepth"]["max"], 12);
    assert_eq!(parameters["branchLength"]["unit"], "{cell}");
}

#[test]
fn a_world_with_a_pot_names_it_and_its_log_holds() {
    let pot = Pot {
        x: -6,
        y: -10,
        width: 13,
        height: 11,
    };
    let (_, _, mut world) = made(Dials::default(), Some(pot));
    world.grow_until_finished(64).unwrap();
    assert_eq!(world.log()[0]["data"]["pot"], json!([-6, -10, 13, 11]));
    assert!(log_problems(world.log()).is_empty());
}
