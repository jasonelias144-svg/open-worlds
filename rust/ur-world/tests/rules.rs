// rust/ur-world/tests/rules.rs
//! The kernel's rules, one at a time: who may enter where, how steps climb
//! and fall, one inhabitant to a cell, whose turn comes first, speech,
//! planting, leaving, the operator's hand, exploration, and the world's
//! edge.

// Tests may unwrap, expect, panic and index: a failure here is a failed
// test, not a world that crashed.
#![allow(
    clippy::unwrap_used,
    clippy::expect_used,
    clippy::panic,
    clippy::indexing_slicing
)]

use std::cell::RefCell;
use std::rc::Rc;

use serde_json::{Value, json};
use ur_world::garden::Script;
use ur_world::generate::{generate, ground};
use ur_world::space::LIMIT;
use ur_world::world::MAX_FALL;
use ur_world::{Action, Cell, ChunkCoord, Dir, EntryError, Material, Mind, Observation, World};

const SEED: u64 = 7;

/// A script that also keeps everything it saw.
struct Watcher {
    script: Script,
    seen: Rc<RefCell<Vec<Observation>>>,
}

impl Mind for Watcher {
    fn act(&mut self, seen: &Observation) -> Action {
        self.seen.borrow_mut().push(seen.clone());
        self.script.act(seen)
    }
}

fn watcher(actions: Vec<Action>) -> (Box<Watcher>, Rc<RefCell<Vec<Observation>>>) {
    let seen = Rc::new(RefCell::new(Vec::new()));
    (
        Box::new(Watcher {
            script: Script::new(actions),
            seen: Rc::clone(&seen),
        }),
        seen,
    )
}

fn script(actions: Vec<Action>) -> Box<Script> {
    Box::new(Script::new(actions))
}

fn kinds(world: &World, who: &str) -> Vec<String> {
    world
        .log()
        .iter()
        .filter(|e| e["agent"] == who)
        .map(|e| e["kind"].as_str().unwrap().to_owned())
        .filter(|k| k != "explored")
        .collect()
}

fn last(world: &World, kind: &str) -> Value {
    world
        .log()
        .iter()
        .rev()
        .find(|e| e["kind"] == kind)
        .cloned()
        .unwrap()
}

// Garden cells (flat grass at 0, so standing height is 1), clear of the tree.
const A: Cell = Cell::new(4, 1, 5);
const B: Cell = Cell::new(5, 1, 5);
const C: Cell = Cell::new(6, 1, 5);

#[test]
fn entering_needs_a_good_name_and_a_free_place_to_stand() {
    let mut w = World::new(SEED);
    assert_eq!(w.add("", script(vec![]), A), Err(EntryError::BadName));
    assert_eq!(w.add("a\nb", script(vec![]), A), Err(EntryError::BadName));
    assert_eq!(
        w.add(&"x".repeat(65), script(vec![]), A),
        Err(EntryError::BadName)
    );
    assert_eq!(
        w.add("in the trunk", script(vec![]), Cell::new(0, 1, 0)),
        Err(EntryError::Solid)
    );
    assert_eq!(
        w.add("in the air", script(vec![]), Cell::new(5, 3, 5)),
        Err(EntryError::NoGround)
    );
    assert_eq!(
        w.add("beyond", script(vec![]), Cell::new(LIMIT + 1, 1, 0)),
        Err(EntryError::Outside)
    );
    assert_eq!(w.add("ALICE", script(vec![]), A), Ok(()));
    assert_eq!(w.add("BOB", script(vec![]), A), Err(EntryError::Occupied));
    assert_eq!(
        w.add("ALICE", script(vec![]), B),
        Err(EntryError::NameTaken)
    );
    // Only ALICE's entry is in the log.
    assert_eq!(w.log().iter().filter(|e| e["kind"] == "entered").count(), 1);
}

#[test]
fn a_step_climbs_one_block_and_falls_off_an_edge() {
    let mut w = World::new(SEED);
    assert!(w.shape(B, Material::Rock));
    w.add(
        "ALICE",
        script(vec![Action::Step(Dir::East), Action::Step(Dir::East)]),
        A,
    )
    .unwrap();
    w.step();
    assert_eq!(w.position("ALICE"), Some(B.above()));
    w.step();
    assert_eq!(w.position("ALICE"), Some(C));
    assert_eq!(
        last(&w, "moved")["data"],
        json!({ "from": [5, 2, 5], "to": [6, 1, 5] })
    );
}

#[test]
fn no_climbing_without_headroom_or_up_a_wall_two_high() {
    let mut w = World::new(SEED);
    w.shape(B, Material::Rock);
    w.shape(A.above(), Material::Rock);
    w.add("ALICE", script(vec![Action::Step(Dir::East)]), A)
        .unwrap();
    w.step();
    assert_eq!(w.position("ALICE"), Some(A));

    let mut w = World::new(SEED);
    w.shape(B, Material::Rock);
    w.shape(B.above(), Material::Rock);
    w.add("ALICE", script(vec![Action::Step(Dir::East)]), A)
        .unwrap();
    w.step();
    assert_eq!(w.position("ALICE"), Some(A));
    assert_eq!(
        last(&w, "blocked")["data"],
        json!({ "action": "step", "dir": "east" })
    );

    // The tree's trunk is four cells high.
    let mut w = World::new(SEED);
    w.add(
        "ALICE",
        script(vec![Action::Step(Dir::East)]),
        Cell::new(-1, 1, 0),
    )
    .unwrap();
    w.step();
    assert_eq!(kinds(&w, "ALICE"), ["entered", "blocked"]);
}

#[test]
fn one_inhabitant_to_a_cell() {
    let mut w = World::new(SEED);
    w.add("ALICE", script(vec![Action::Step(Dir::East)]), A)
        .unwrap();
    w.add("BOB", script(vec![]), B).unwrap();
    w.step();
    assert_eq!(w.position("ALICE"), Some(A));
    assert_eq!(kinds(&w, "ALICE"), ["entered", "blocked"]);
}

#[test]
fn the_first_turn_rotates_each_tick() {
    // Both step into the cell between them; whoever goes first takes it.
    for (waits, winner) in [(0, "P"), (1, "Q")] {
        let mut w = World::new(SEED);
        let mut p = vec![Action::Wait; waits];
        let mut q = p.clone();
        p.push(Action::Step(Dir::East));
        q.push(Action::Step(Dir::West));
        w.add("P", script(p), A).unwrap();
        w.add("Q", script(q), C).unwrap();
        w.run(u64::try_from(waits).unwrap() + 1);
        assert_eq!(w.position(winner), Some(B), "tick {waits}");
    }
}

#[test]
fn everyone_hears_speech_on_the_next_tick_only() {
    let mut w = World::new(SEED);
    w.add(
        "ALICE",
        script(vec![
            Action::Say("Hello, world.".into()),
            Action::Say("x".repeat(300)),
        ]),
        A,
    )
    .unwrap();
    let (bob, seen) = watcher(vec![]);
    w.add("BOB", bob, C).unwrap();
    w.run(3);
    let heard: Vec<Vec<(String, String)>> = seen.borrow().iter().map(|o| o.heard.clone()).collect();
    assert_eq!(heard[0], []);
    assert_eq!(heard[1], [("ALICE".to_owned(), "Hello, world.".to_owned())]);
    assert_eq!(heard[2], [("ALICE".to_owned(), "x".repeat(280))]);
    // BOB sees ALICE two cells west, and the grass under his feet.
    let first = &seen.borrow()[0];
    assert_eq!(first.others, [("ALICE".to_owned(), A)]);
    assert_eq!(first.at(0, -1, 0), Some(Material::Grass));
    assert_eq!(first.at(0, 0, 0), Some(Material::Air));
    assert_eq!(first.at(2, 0, 0), None);
}

#[test]
fn a_flower_needs_open_air_on_grass_or_soil() {
    let mut w = World::new(SEED);
    w.add(
        "ALICE",
        script(vec![Action::Plant(Dir::East), Action::Plant(Dir::East)]),
        A,
    )
    .unwrap();
    w.step();
    assert_eq!(w.material(B), Material::Flower);
    w.step(); // the cell now holds a flower
    assert_eq!(kinds(&w, "ALICE"), ["entered", "planted", "blocked"]);

    // Not over water: the spring is at (2, 0, 3).
    let mut w = World::new(SEED);
    w.add(
        "BOB",
        script(vec![Action::Plant(Dir::South)]),
        Cell::new(2, 1, 2),
    )
    .unwrap();
    w.step();
    assert_eq!(kinds(&w, "BOB"), ["entered", "blocked"]);
    assert!(w.changes().is_empty());
}

#[test]
fn leaving_always_succeeds_and_a_name_is_used_once() {
    let mut w = World::new(SEED);
    w.add(
        "ALICE",
        script(vec![
            Action::Plant(Dir::East),
            Action::Exit,
            Action::Step(Dir::West),
        ]),
        A,
    )
    .unwrap();
    w.add("BOB", script(vec![]), C).unwrap();
    w.run(3);
    assert_eq!(kinds(&w, "ALICE"), ["entered", "planted", "exited"]);
    assert_eq!(w.position("ALICE"), None);
    // What she planted stays.
    assert_eq!(w.material(B), Material::Flower);
    assert_eq!(
        w.add("ALICE", script(vec![]), A),
        Err(EntryError::NameTaken)
    );
    // Her keeper can take BOB out at any time, too.
    w.leave("BOB");
    w.leave("BOB");
    assert_eq!(last(&w, "exited")["data"], json!({ "reason": "requested" }));
    assert!(w.inhabitants().is_empty());
    assert_eq!(
        world_log::verify_log(&Value::Array(w.log().to_vec())).map(str::len),
        Ok(64)
    );
}

#[test]
fn a_cell_is_free_again_once_its_inhabitant_leaves() {
    let mut w = World::new(SEED);
    w.add("ALICE", script(vec![Action::Exit]), A).unwrap();
    w.add(
        "BOB",
        script(vec![Action::Wait, Action::Step(Dir::West)]),
        B,
    )
    .unwrap();
    w.run(2);
    assert_eq!(w.position("BOB"), Some(A));
    w.leave("BOB");
    assert_eq!(w.add("CAROL", script(vec![]), A), Ok(()));
}

#[test]
fn whoever_stands_on_someone_who_walks_away_falls_at_the_end_of_the_tick() {
    let mut w = World::new(SEED);
    w.shape(B, Material::Rock);
    // ALICE steps off the rock onto BOB's head; then BOB walks away.
    w.add("ALICE", script(vec![Action::Step(Dir::East)]), B.above())
        .unwrap();
    w.add(
        "BOB",
        script(vec![Action::Wait, Action::Step(Dir::East)]),
        C,
    )
    .unwrap();
    w.step();
    assert_eq!(w.position("ALICE"), Some(C.above()));
    w.step();
    assert_eq!(w.position("BOB"), Some(Cell::new(7, 1, 5)));
    assert_eq!(w.position("ALICE"), Some(C));
    assert_eq!(
        last(&w, "fell")["data"],
        json!({ "from": [6, 2, 5], "to": [6, 1, 5] })
    );
}

#[test]
fn the_operators_hand_is_recorded_and_whoever_loses_their_ground_falls() {
    let mut w = World::new(SEED);
    w.add("ALICE", script(vec![]), A).unwrap();
    // Nothing solid where someone stands.
    assert!(!w.shape(A, Material::Rock));
    assert!(w.shape(A.below(), Material::Air));
    assert_eq!(w.position("ALICE"), Some(A.below()));
    assert_eq!(
        last(&w, "fell")["data"],
        json!({ "from": [4, 1, 5], "to": [4, 0, 5] })
    );
    assert_eq!(last(&w, "shaped")["agent"], Value::Null);
    // Shaping a cell back to what the generator made removes the change.
    assert!(w.shape(Cell::new(9, 9, 9), Material::Rock));
    assert!(w.shape(Cell::new(9, 9, 9), Material::Air));
    assert_eq!(w.changes().len(), 1);
}

#[test]
fn what_comes_into_view_is_explored_once_and_named_for_its_finder() {
    let mut w = World::new(SEED);
    assert!(w.explored().is_empty());
    w.add("ALICE", script(vec![]), A).unwrap();
    assert_eq!(w.explored().len(), 27);
    w.add("BOB", script(vec![]), C).unwrap();
    assert_eq!(w.explored().len(), 27); // the same chunk: nothing new
    let explored: Vec<&Value> = w.log().iter().filter(|e| e["kind"] == "explored").collect();
    assert!(explored.iter().all(|e| e["agent"] == "ALICE"));
    assert!(w.explored().contains(&ChunkCoord::new(-1, -1, -1)));
    assert!(!w.explored().contains(&ChunkCoord::new(2, 0, 0)));
    assert_eq!(w.surface(4, 4), Some((0, Material::Grass)));
    assert_eq!(w.surface(0, 0), Some((6, Material::Leaves)));
    assert_eq!(w.surface(100, 0), None);
}

#[test]
fn the_world_has_an_edge() {
    let mut w = World::new(SEED);
    let edge = Cell::new(LIMIT, ground(SEED, LIMIT, 0) + 1, 0);
    w.add(
        "ALICE",
        script(vec![Action::Step(Dir::East), Action::Step(Dir::West)]),
        edge,
    )
    .unwrap();
    // Chunks wholly beyond the edge don't come into view.
    assert_eq!(w.explored().len(), 18);
    assert!(w.explored().iter().all(|c| c.origin().x <= LIMIT));
    w.run(2);
    assert_eq!(kinds(&w, "ALICE")[..2], ["entered", "blocked"]);
    assert_eq!(w.position("ALICE").map(|c| c.x), Some(LIMIT - 1));
    // The farthest numbers there are can't be entered, and don't break
    // the check.
    for far in [i64::MIN, i64::MAX] {
        assert_eq!(
            w.add("far", script(vec![]), Cell::new(far, 1, 0)),
            Err(EntryError::Outside)
        );
        assert_eq!(
            w.add("far", script(vec![]), Cell::new(0, far, 0)),
            Err(EntryError::Outside)
        );
    }
}

#[test]
fn what_the_log_says_was_generated_is_what_the_generator_makes() {
    // Found by the independent review of #28: a chunk the operator shaped
    // before anyone saw it was logged with its changes in its hash.
    let mut w = World::new(SEED);
    let cell = Cell::new(5, 10, 5);
    w.shape(cell, Material::Rock);
    w.add("ALICE", script(vec![]), A).unwrap();
    let home = cell.chunk();
    let entry = w
        .log()
        .iter()
        .find(|e| e["kind"] == "explored" && e["data"]["chunk"] == home.json())
        .cloned()
        .unwrap();
    assert_eq!(entry["data"]["hash"], generate(SEED, home).hash());
    assert_ne!(entry["data"]["hash"], w.chunk(home).hash());
}

#[test]
fn whoever_stands_on_someone_taken_out_falls_at_once() {
    let mut w = World::new(SEED);
    w.shape(B, Material::Rock);
    w.add("ALICE", script(vec![Action::Step(Dir::East)]), B.above())
        .unwrap();
    w.add("BOB", script(vec![]), C).unwrap();
    w.step();
    assert_eq!(w.position("ALICE"), Some(C.above()));
    w.leave("BOB");
    assert_eq!(w.position("ALICE"), Some(C));
}

#[test]
fn a_deep_drop_goes_on_at_the_next_tick() {
    let mut w = World::new(SEED);
    let top = Cell::new(4, 1, 4);
    w.add("ALICE", script(vec![]), top).unwrap();
    // Hollow out a shaft a hundred cells deep beneath her, bottom first.
    for depth in (0..100).rev() {
        w.shape(Cell::new(4, -depth, 4), Material::Air);
    }
    assert_eq!(w.position("ALICE"), Some(Cell::new(4, 1 - MAX_FALL, 4)));
    w.step();
    assert_eq!(w.position("ALICE"), Some(Cell::new(4, -99, 4)));
}
