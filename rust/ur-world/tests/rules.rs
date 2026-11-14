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

use formats::proof::public_key;
use serde_json::{Value, json};
use ur_world::arrival::{self, trial_secret};
use ur_world::garden::Script;
use ur_world::generate::{generate, ground};
use ur_world::space::LIMIT;
use ur_world::world::{MAX_FALL, MAX_SAY};
use ur_world::{
    Action, Cell, ChunkCoord, Dir, EntryError, Material, Mind, Observation, Outcome, World,
};

const SEED: u64 = 7;

/// A world for these tests, with a trial key of its own.
fn world() -> World {
    World::new(SEED, &public_key(&trial_secret(SEED, "a test world")))
}

/// Entering as the tests here do: each name with its own trial key, over
/// the world as it is now.
trait Add {
    fn add(&mut self, name: &str, mind: Box<dyn Mind>, at: Cell) -> Result<(), EntryError>;
}

impl Add for World {
    fn add(&mut self, name: &str, mind: Box<dyn Mind>, at: Cell) -> Result<(), EntryError> {
        let secret = trial_secret(SEED, name);
        let arrival = arrival::sign(self, &secret, name, "2026-11-14T00:00:00Z").unwrap();
        self.enter(&arrival, mind, at).map(|_| ())
    }
}

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
    let mut w = world();
    // A name that records-v1 refuses can't be in an arrival that holds.
    for name in [String::new(), "x".repeat(65), "   ".into()] {
        assert!(matches!(
            w.add(&name, script(vec![]), A),
            Err(EntryError::BadArrival(why)) if why.contains("/name")
        ));
    }
    // records-v1 allows line breaks in text; a name here has none.
    assert_eq!(w.add("a\nb", script(vec![]), A), Err(EntryError::BadName));
    assert_eq!(w.add("a\tb", script(vec![]), A), Err(EntryError::BadName));
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
    assert_eq!(w.add("TRIAL-1", script(vec![]), A), Ok(()));
    assert_eq!(
        w.add("TRIAL-2", script(vec![]), A),
        Err(EntryError::Occupied)
    );
    assert_eq!(
        w.add("TRIAL-1", script(vec![]), B),
        Err(EntryError::AlreadyHere)
    );
    // Only TRIAL-1's entry is in the log.
    assert_eq!(w.log().iter().filter(|e| e["kind"] == "entered").count(), 1);
}

#[test]
fn a_step_climbs_one_block_and_falls_off_an_edge() {
    let mut w = world();
    assert!(w.shape(B, Material::Rock));
    w.add(
        "TRIAL-1",
        script(vec![Action::Step(Dir::East), Action::Step(Dir::East)]),
        A,
    )
    .unwrap();
    w.step();
    assert_eq!(w.position("TRIAL-1"), Some(B.above()));
    w.step();
    assert_eq!(w.position("TRIAL-1"), Some(C));
    assert_eq!(
        last(&w, "moved")["data"],
        json!({ "from": [5, 2, 5], "to": [6, 1, 5] })
    );
}

#[test]
fn no_climbing_without_headroom_or_up_a_wall_two_high() {
    let mut w = world();
    w.shape(B, Material::Rock);
    w.shape(A.above(), Material::Rock);
    w.add("TRIAL-1", script(vec![Action::Step(Dir::East)]), A)
        .unwrap();
    w.step();
    assert_eq!(w.position("TRIAL-1"), Some(A));

    let mut w = world();
    w.shape(B, Material::Rock);
    w.shape(B.above(), Material::Rock);
    w.add("TRIAL-1", script(vec![Action::Step(Dir::East)]), A)
        .unwrap();
    w.step();
    assert_eq!(w.position("TRIAL-1"), Some(A));
    assert_eq!(
        last(&w, "blocked")["data"],
        json!({ "action": "step", "dir": "east" })
    );

    // The tree's trunk is four cells high.
    let mut w = world();
    w.add(
        "TRIAL-1",
        script(vec![Action::Step(Dir::East)]),
        Cell::new(-1, 1, 0),
    )
    .unwrap();
    w.step();
    assert_eq!(kinds(&w, "TRIAL-1"), ["entered", "blocked"]);
}

#[test]
fn one_inhabitant_to_a_cell() {
    let mut w = world();
    w.add("TRIAL-1", script(vec![Action::Step(Dir::East)]), A)
        .unwrap();
    w.add("TRIAL-2", script(vec![]), B).unwrap();
    w.step();
    assert_eq!(w.position("TRIAL-1"), Some(A));
    assert_eq!(kinds(&w, "TRIAL-1"), ["entered", "blocked"]);
}

#[test]
fn the_first_turn_rotates_each_tick() {
    // Both step into the cell between them; whoever goes first takes it.
    for (waits, winner) in [(0, "P"), (1, "Q")] {
        let mut w = world();
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
    let mut w = world();
    w.add(
        "TRIAL-1",
        script(vec![
            Action::Say("Hello, world.".into()),
            Action::Say("x".repeat(300)),
        ]),
        A,
    )
    .unwrap();
    let (bob, seen) = watcher(vec![]);
    w.add("TRIAL-2", bob, C).unwrap();
    w.run(3);
    let heard: Vec<Vec<(String, String)>> = seen.borrow().iter().map(|o| o.heard.clone()).collect();
    assert_eq!(heard[0], []);
    assert_eq!(
        heard[1],
        [("TRIAL-1".to_owned(), "Hello, world.".to_owned())]
    );
    assert_eq!(heard[2], [("TRIAL-1".to_owned(), "x".repeat(280))]);
    // TRIAL-2 sees TRIAL-1 two cells west, and the grass underfoot.
    let first = &seen.borrow()[0];
    assert_eq!(first.others, [("TRIAL-1".to_owned(), A)]);
    assert_eq!(first.at(0, -1, 0), Some(Material::Grass));
    assert_eq!(first.at(0, 0, 0), Some(Material::Air));
    assert_eq!(first.at(2, 0, 0), None);
}

#[test]
fn a_flower_needs_open_air_on_grass_or_soil() {
    let mut w = world();
    w.add(
        "TRIAL-1",
        script(vec![Action::Plant(Dir::East), Action::Plant(Dir::East)]),
        A,
    )
    .unwrap();
    w.step();
    assert_eq!(w.material(B), Material::Flower);
    w.step(); // the cell now holds a flower
    assert_eq!(kinds(&w, "TRIAL-1"), ["entered", "planted", "blocked"]);

    // Not over water: the spring is at (2, 0, 3).
    let mut w = world();
    w.add(
        "TRIAL-2",
        script(vec![Action::Plant(Dir::South)]),
        Cell::new(2, 1, 2),
    )
    .unwrap();
    w.step();
    assert_eq!(kinds(&w, "TRIAL-2"), ["entered", "blocked"]);
    assert!(w.changes().is_empty());
}

#[test]
fn leaving_always_succeeds_and_the_one_who_left_can_come_back() {
    let mut w = world();
    w.add(
        "TRIAL-1",
        script(vec![
            Action::Plant(Dir::East),
            Action::Exit,
            Action::Step(Dir::West),
        ]),
        A,
    )
    .unwrap();
    w.add("TRIAL-2", script(vec![]), C).unwrap();
    w.run(3);
    assert_eq!(kinds(&w, "TRIAL-1"), ["entered", "planted", "exited"]);
    assert_eq!(w.position("TRIAL-1"), None);
    // What TRIAL-1 planted stays.
    assert_eq!(w.material(B), Material::Flower);
    // TRIAL-1 can come back, with the same key; the name is still TRIAL-1's.
    assert_eq!(w.add("TRIAL-1", script(vec![]), A), Ok(()));
    assert_eq!(kinds(&w, "TRIAL-1").last().unwrap(), "entered");
    w.leave("TRIAL-1");
    // A keeper can take TRIAL-2 out at any time, too.
    w.leave("TRIAL-2");
    w.leave("TRIAL-2");
    assert_eq!(last(&w, "exited")["data"], json!({ "reason": "requested" }));
    assert!(w.inhabitants().is_empty());
    assert_eq!(
        world_log::verify_log(&Value::Array(w.log().to_vec())).map(str::len),
        Ok(64)
    );
}

#[test]
fn a_cell_is_free_again_once_its_inhabitant_leaves() {
    let mut w = world();
    w.add("TRIAL-1", script(vec![Action::Exit]), A).unwrap();
    w.add(
        "TRIAL-2",
        script(vec![Action::Wait, Action::Step(Dir::West)]),
        B,
    )
    .unwrap();
    w.run(2);
    assert_eq!(w.position("TRIAL-2"), Some(A));
    w.leave("TRIAL-2");
    assert_eq!(w.add("CAROL", script(vec![]), A), Ok(()));
}

#[test]
fn whoever_stands_on_someone_who_walks_away_falls_at_the_end_of_the_tick() {
    let mut w = world();
    w.shape(B, Material::Rock);
    // TRIAL-1 steps off the rock onto TRIAL-2's head; then TRIAL-2 walks away.
    w.add("TRIAL-1", script(vec![Action::Step(Dir::East)]), B.above())
        .unwrap();
    w.add(
        "TRIAL-2",
        script(vec![Action::Wait, Action::Step(Dir::East)]),
        C,
    )
    .unwrap();
    w.step();
    assert_eq!(w.position("TRIAL-1"), Some(C.above()));
    w.step();
    assert_eq!(w.position("TRIAL-2"), Some(Cell::new(7, 1, 5)));
    assert_eq!(w.position("TRIAL-1"), Some(C));
    assert_eq!(
        last(&w, "fell")["data"],
        json!({ "from": [6, 2, 5], "to": [6, 1, 5] })
    );
}

#[test]
fn the_operators_hand_is_recorded_and_whoever_loses_their_ground_falls() {
    let mut w = world();
    w.add("TRIAL-1", script(vec![]), A).unwrap();
    // Nothing solid where someone stands.
    assert!(!w.shape(A, Material::Rock));
    assert!(w.shape(A.below(), Material::Air));
    assert_eq!(w.position("TRIAL-1"), Some(A.below()));
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
    let mut w = world();
    assert!(w.explored().is_empty());
    w.add("TRIAL-1", script(vec![]), A).unwrap();
    assert_eq!(w.explored().len(), 27);
    w.add("TRIAL-2", script(vec![]), C).unwrap();
    assert_eq!(w.explored().len(), 27); // the same chunk: nothing new
    let explored: Vec<&Value> = w.log().iter().filter(|e| e["kind"] == "explored").collect();
    assert!(explored.iter().all(|e| e["agent"] == "TRIAL-1"));
    assert!(w.explored().contains(&ChunkCoord::new(-1, -1, -1)));
    assert!(!w.explored().contains(&ChunkCoord::new(2, 0, 0)));
    assert_eq!(w.surface(4, 4), Some((0, Material::Grass)));
    assert_eq!(w.surface(0, 0), Some((6, Material::Leaves)));
    assert_eq!(w.surface(100, 0), None);
}

#[test]
fn the_world_has_an_edge() {
    let mut w = world();
    let edge = Cell::new(LIMIT, ground(SEED, LIMIT, 0) + 1, 0);
    w.add(
        "TRIAL-1",
        script(vec![Action::Step(Dir::East), Action::Step(Dir::West)]),
        edge,
    )
    .unwrap();
    // Chunks wholly beyond the edge don't come into view.
    assert_eq!(w.explored().len(), 18);
    assert!(w.explored().iter().all(|c| c.origin().x <= LIMIT));
    w.run(2);
    assert_eq!(kinds(&w, "TRIAL-1")[..2], ["entered", "blocked"]);
    assert_eq!(w.position("TRIAL-1").map(|c| c.x), Some(LIMIT - 1));
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
    let mut w = world();
    let cell = Cell::new(5, 10, 5);
    w.shape(cell, Material::Rock);
    w.add("TRIAL-1", script(vec![]), A).unwrap();
    let home = cell.chunk();
    let entry = w
        .log()
        .iter()
        .find(|e| e["kind"] == "explored" && e["data"]["chunk"] == home.json())
        .cloned()
        .unwrap();
    assert_eq!(entry["data"]["hash"], generate(SEED, home).unwrap().hash());
    assert_ne!(entry["data"]["hash"], w.chunk(home).unwrap().hash());
}

#[test]
fn whoever_stands_on_someone_taken_out_falls_at_once() {
    let mut w = world();
    w.shape(B, Material::Rock);
    w.add("TRIAL-1", script(vec![Action::Step(Dir::East)]), B.above())
        .unwrap();
    w.add("TRIAL-2", script(vec![]), C).unwrap();
    w.step();
    assert_eq!(w.position("TRIAL-1"), Some(C.above()));
    w.leave("TRIAL-2");
    assert_eq!(w.position("TRIAL-1"), Some(C));
}

#[test]
fn a_deep_drop_goes_on_at_the_next_tick() {
    let mut w = world();
    let top = Cell::new(4, 1, 4);
    w.add("TRIAL-1", script(vec![]), top).unwrap();
    // Hollow out a shaft a hundred cells deep beneath TRIAL-1, bottom first.
    for depth in (0..100).rev() {
        w.shape(Cell::new(4, -depth, 4), Material::Air);
    }
    assert_eq!(w.position("TRIAL-1"), Some(Cell::new(4, 1 - MAX_FALL, 4)));
    w.step();
    assert_eq!(w.position("TRIAL-1"), Some(Cell::new(4, -99, 4)));
}

#[test]
fn a_stack_falls_together() {
    // Found by the independent review of #28: settling went in name order,
    // so X, on top and first by name, floated a tick when Z left.
    let mut w = world();
    w.shape(B, Material::Rock);
    w.add("Y", script(vec![Action::Step(Dir::East)]), B.above())
        .unwrap();
    w.add("Z", script(vec![]), C).unwrap();
    w.step();
    assert_eq!(w.position("Y"), Some(C.above()));
    w.shape(B.above(), Material::Rock);
    w.add(
        "X",
        script(vec![Action::Step(Dir::East)]),
        B.above().above(),
    )
    .unwrap();
    w.step();
    assert_eq!(w.position("X"), Some(C.above().above()));
    w.leave("Z");
    assert_eq!(w.position("Y"), Some(C));
    assert_eq!(w.position("X"), Some(C.above()));
}

#[test]
fn each_hears_what_came_of_its_last_action() {
    let (mind, seen) = watcher(vec![
        Action::Step(Dir::East),
        Action::Step(Dir::North),
        Action::Say("Hello.".into()),
        Action::Plant(Dir::West),
        Action::Plant(Dir::West),
        Action::Wait,
        Action::Unreadable("I think I will go north".into()),
        Action::Unanswered,
    ]);
    let mut w = world();
    w.shape(A.offset(1, 0, -1), Material::Rock);
    w.shape(A.offset(1, 1, -1), Material::Rock);
    w.add("TRIAL-1", mind, A).unwrap();
    w.run(9);
    let told: Vec<Option<Outcome>> = seen.borrow().iter().map(|o| o.last.clone()).collect();
    assert_eq!(
        told,
        [
            None,
            Some(Outcome::Moved {
                dir: Dir::East,
                to: B
            }),
            Some(Outcome::StepBlocked(Dir::North)),
            Some(Outcome::Said("Hello.".into())),
            Some(Outcome::Planted {
                dir: Dir::West,
                at: A
            }),
            Some(Outcome::PlantBlocked(Dir::West)),
            Some(Outcome::Waited),
            Some(Outcome::Unreadable),
            Some(Outcome::Unanswered),
        ]
    );
    assert_eq!(
        last(&w, "unreadable")["data"],
        json!({ "reply": "I think I will go north" })
    );
    assert_eq!(last(&w, "unanswered")["data"], json!({}));
}

#[test]
fn an_unreadable_reply_is_recorded_cut_short() {
    let long = "x".repeat(MAX_SAY * 3);
    let mut w = world();
    w.add("TRIAL-1", script(vec![Action::Unreadable(long)]), A)
        .unwrap();
    w.step();
    let reply = last(&w, "unreadable")["data"]["reply"]
        .as_str()
        .unwrap()
        .to_owned();
    assert_eq!(reply.chars().count(), MAX_SAY);
    assert_eq!(w.position("TRIAL-1"), Some(A));
}
