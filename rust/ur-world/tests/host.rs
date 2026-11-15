// rust/ur-world/tests/host.rs
//! Hosting (`ur_world::host`): the garden gives other worlds a place and
//! time, and both logs record each step.

// Tests may unwrap, expect, panic and index: a failure here is a failed
// test, which is what it should be.
#![allow(
    clippy::unwrap_used,
    clippy::expect_used,
    clippy::panic,
    clippy::indexing_slicing
)]

use formats::proof::public_key;
use serde_json::{Value, json};
use ur_world::World;
use ur_world::garden::{SEED, hello_world, hosted_vectors, plants, world_secret};
use ur_world::host::{HostError, Hosted, hosting_problems, place_problem};
use ur_world::space::Cell;

/// A small hosted world for the tests: its log grows one entry a step,
/// for `steps` steps, unless it is set to fail.
struct Stub {
    key: String,
    log: Vec<Value>,
    steps: u64,
    fail: bool,
}

impl Stub {
    fn new(key: &str, steps: u64) -> Stub {
        let mut stub = Stub {
            key: key.to_owned(),
            log: Vec::new(),
            steps,
            fail: false,
        };
        stub.write("world_created", json!({ "world": key }));
        stub
    }

    fn write(&mut self, kind: &str, data: Value) {
        let prev = self
            .log
            .last()
            .and_then(|e| e.get("hash"))
            .and_then(Value::as_str)
            .unwrap_or(world_log::GENESIS)
            .to_owned();
        let mut entry = json!({
            "tick": self.log.len(), "kind": kind, "agent": null, "data": data, "prev": prev,
        });
        let hash = world_log::digest(&entry).unwrap();
        entry["hash"] = json!(hash);
        self.log.push(entry);
    }
}

impl Hosted for Stub {
    fn key(&self) -> &str {
        &self.key
    }
    fn kind(&self) -> &str {
        "a stub"
    }
    fn log(&self) -> &[Value] {
        &self.log
    }
    fn finished(&self) -> bool {
        self.log.len() as u64 > self.steps
    }
    fn tend(&mut self) -> Result<(), String> {
        if self.fail {
            return Err("it was made to fail".into());
        }
        self.write("stepped", json!({}));
        Ok(())
    }
    fn as_any(&self) -> &dyn std::any::Any {
        self
    }
}

fn empty_world() -> World {
    World::new(SEED, &public_key(&world_secret()))
}

fn kinds(world: &World) -> Vec<String> {
    world
        .log()
        .iter()
        .map(|e| e["kind"].as_str().unwrap_or_default().to_owned())
        .collect()
}

fn logs(world: &World) -> Vec<Vec<Value>> {
    world
        .glasshouses()
        .iter()
        .map(|g| g.world.log().to_vec())
        .collect()
}

fn problems(log: &[Value], hosted: &[Vec<Value>]) -> Vec<String> {
    let slices: Vec<&[Value]> = hosted.iter().map(Vec::as_slice).collect();
    hosting_problems(log, &slices)
}

#[test]
fn the_garden_hosts_three_plants_and_tends_each_until_it_finishes() {
    let world = hello_world().unwrap();
    assert_eq!(world.glasshouses().len(), plants().len());
    for (glasshouse, (_, at, _)) in world.glasshouses().iter().zip(plants()) {
        assert_eq!(glasshouse.at, at);
        assert!(glasshouse.world.finished());
        assert!(!glasshouse.untended);
        // Each plant's log grows by its own rule.
        assert_eq!(
            plant_world::world::log_problems(glasshouse.world.log()),
            Vec::<String>::new()
        );
    }
    assert_eq!(problems(world.log(), &logs(&world)), Vec::<String>::new());
    // The Ur-world's own log still holds together, and its arrivals hold.
    world_log::verify_log(&Value::Array(world.log().to_vec())).unwrap();
    assert_eq!(
        ur_world::arrival::arrival_problems(world.log()),
        Vec::<String>::new()
    );
}

#[test]
fn the_hosted_vectors_are_what_the_garden_writes() {
    let path = concat!(
        env!("CARGO_MANIFEST_DIR"),
        "/../../vectors/ur-garden-hosted.json"
    );
    let file: Value = serde_json::from_str(&std::fs::read_to_string(path).unwrap()).unwrap();
    assert_eq!(hosted_vectors(&hello_world().unwrap()).unwrap(), file);
}

#[test]
fn a_glasshouse_stands_only_on_the_gardens_ground() {
    assert_eq!(place_problem(Cell::new(-5, 1, -4)), None);
    assert!(
        place_problem(Cell::new(-5, 2, -4)).is_some(),
        "above the ground"
    );
    assert!(
        place_problem(Cell::new(-5, 0, -4)).is_some(),
        "in the ground"
    );
    assert!(
        place_problem(Cell::new(9, 1, 0)).is_some(),
        "past the radius"
    );
    assert_eq!(
        place_problem(Cell::new(6, 1, 6)),
        None,
        "inside: the whole-number root of 72 is 8"
    );
    assert!(
        place_problem(Cell::new(7, 1, 7)).is_some(),
        "past the radius, diagonally"
    );
    assert_eq!(place_problem(Cell::new(8, 1, 0)), None, "at the radius");
    assert!(place_problem(Cell::new(0, 1, 0)).is_some(), "the trunk");
    assert!(
        place_problem(Cell::new(2, 1, 3)).is_some(),
        "over the spring"
    );
    assert!(place_problem(Cell::new(i64::MIN, 1, i64::MIN)).is_some());
}

#[test]
fn hosting_is_refused_where_it_cant_be_and_twice() {
    let mut world = empty_world();
    let at = Cell::new(-5, 1, -4);
    assert_eq!(
        world.host(Cell::new(0, 1, 0), Box::new(Stub::new("a", 1))),
        Err(HostError::Place("the tree stands there"))
    );
    world.host(at, Box::new(Stub::new("a", 1))).unwrap();
    assert_eq!(
        world.host(at, Box::new(Stub::new("b", 1))),
        Err(HostError::Taken)
    );
    assert_eq!(
        world.host(Cell::new(5, 1, -4), Box::new(Stub::new("a", 1))),
        Err(HostError::AlreadyHosted)
    );
    let own = world.key().to_owned();
    assert_eq!(
        world.host(Cell::new(5, 1, -4), Box::new(Stub::new(&own, 1))),
        Err(HostError::OwnKey)
    );
    let mut nameless = Stub::new("c", 1);
    nameless.log.clear();
    assert_eq!(
        world.host(Cell::new(5, 1, -4), Box::new(nameless)),
        Err(HostError::NoLog)
    );
    let mut misnamed = Stub::new("d", 1);
    misnamed.key = "e".into();
    assert_eq!(
        world.host(Cell::new(5, 1, -4), Box::new(misnamed)),
        Err(HostError::NoLog)
    );
    // Only the one that was hosted is in the log.
    assert_eq!(kinds(&world), ["world_created", "hosted"]);
}

#[test]
fn each_tick_names_the_entry_each_step_wrote() {
    let mut world = empty_world();
    world
        .host(Cell::new(-5, 1, -4), Box::new(Stub::new("a", 2)))
        .unwrap();
    world
        .host(Cell::new(5, 1, -4), Box::new(Stub::new("b", 1)))
        .unwrap();
    world.run(4);
    assert_eq!(
        kinds(&world),
        ["world_created", "hosted", "hosted", "tended", "tended"]
    );
    let hosted = logs(&world);
    let tended: Vec<&Value> = world
        .log()
        .iter()
        .filter(|e| e["kind"] == "tended")
        .collect();
    assert_eq!(
        tended[0]["data"]["worlds"],
        json!([["a", hosted[0][1]["hash"]], ["b", hosted[1][1]["hash"]]])
    );
    assert_eq!(
        tended[1]["data"]["worlds"],
        json!([["a", hosted[0][2]["hash"]]])
    );
    assert_eq!(problems(world.log(), &hosted), Vec::<String>::new());
}

#[test]
fn a_world_that_cant_step_is_left_untended() {
    let mut world = empty_world();
    let mut stub = Stub::new("a", 3);
    stub.fail = true;
    world.host(Cell::new(-5, 1, -4), Box::new(stub)).unwrap();
    world.run(3);
    assert_eq!(kinds(&world), ["world_created", "hosted", "untended"]);
    assert_eq!(world.log()[2]["data"]["reason"], "it was made to fail");
    assert!(world.glasshouses()[0].untended);
    assert_eq!(problems(world.log(), &logs(&world)), Vec::<String>::new());
}

#[test]
fn hosting_problems_finds_what_doesnt_match() {
    let world = hello_world().unwrap();
    let log = world.log().to_vec();
    let hosted = logs(&world);
    let first_tended = log.iter().position(|e| e["kind"] == "tended").unwrap();
    let first_hosted = log.iter().position(|e| e["kind"] == "hosted").unwrap();
    let key = hosted[0][0]["data"]["world"].as_str().unwrap().to_owned();
    let found = |log: &[Value], hosted: &[Vec<Value>], what: &str| {
        let p = problems(log, hosted);
        assert!(p.iter().any(|x| x.contains(what)), "{what} not in {p:?}");
    };

    // A hosted log that isn't given.
    found(&log, &hosted[1..], "whose log isn't given");
    // A given log the Ur-world never hosted.
    let mut extra = hosted.clone();
    extra.push(Stub::new("z", 0).log);
    found(&log, &extra, "z: not hosted in this log");
    // A log that goes on past what was tended.
    let mut longer = hosted.clone();
    let mut grown = Stub::new(&key, 9);
    grown.log = longer[0].clone();
    grown.write("more", json!({}));
    longer[0] = grown.log;
    found(&log, &longer, "goes on past what the Ur-world tended");
    // A tended entry naming the wrong next entry.
    let mut wrong = log.clone();
    wrong[first_tended]["data"]["worlds"][0][1] = json!("0".repeat(64));
    found(&wrong, &hosted, "to an entry that isn't its next");
    // A hosted entry naming another first entry, or an entry it doesn't have.
    let mut other_first = log.clone();
    other_first[first_hosted]["data"]["first"] = json!("0".repeat(64));
    found(&other_first, &hosted, "names another first entry");
    let mut other_from = log.clone();
    other_from[first_hosted]["data"]["from"] = json!("0".repeat(64));
    found(&other_from, &hosted, "names an entry");
    // Hosted twice.
    let mut twice = log.clone();
    twice.insert(first_hosted + 1, log[first_hosted].clone());
    found(&twice, &hosted, "a second time");
    // Tended after it was untended.
    let mut after = log.clone();
    after.insert(
        first_tended,
        json!({"kind": "untended", "data": {"world": key, "reason": "test"}}),
    );
    found(&after, &hosted, "after it was untended");
    // A hosted log that doesn't hold together.
    let mut broken = hosted.clone();
    broken[0][1]["tick"] = json!(99);
    found(&log, &broken, "doesn't hold together");
}
