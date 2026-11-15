// rust/ur-world/tests/architectures.rs
//! The architectures (course step 3a, part four), checked: each run's
//! logs hold; the octopus's brain gives few intents while its arms take
//! their own steps, and their reflex takes them round the tree; the
//! relay's leader acts only when enough senses fire at once; the swarm's
//! flowers grow as one patch, each planted beside the one its planter
//! stood on; and no world's log names another world or another world's
//! presence.

// Tests may unwrap, expect, panic and index: a failure here is a failed
// test, not a world that crashed.
#![allow(
    clippy::unwrap_used,
    clippy::expect_used,
    clippy::panic,
    clippy::indexing_slicing
)]

use std::collections::BTreeSet;

use serde_json::Value;
use ur_world::architecture::octopus::{self, Intent};
use ur_world::architecture::{council, relay, swarm};
use ur_world::arrival::arrival_problems;
use ur_world::garden::SECOND_AT;
use ur_world::link::link_log_problems;
use ur_world::person::Person;
use ur_world::{Cell, Dir, Material, World};

fn holds(world: &World) {
    world_log::verify_log(&Value::Array(world.log().to_vec())).unwrap();
    assert_eq!(arrival_problems(world.log()), Vec::<String>::new());
    assert_eq!(link_log_problems(world.log()), Vec::<String>::new());
}

fn of<'a>(world: &'a World, kind: &str, agent: &str) -> Vec<&'a Value> {
    world
        .log()
        .iter()
        .filter(|e| e["kind"] == kind && e["agent"] == agent)
        .collect()
}

fn cell(v: &Value) -> Cell {
    Cell::new(
        v[0].as_i64().unwrap(),
        v[1].as_i64().unwrap(),
        v[2].as_i64().unwrap(),
    )
}

/// No world's log names another of `worlds`, or the presence `person`
/// has in it (counter 0), by key or by name (`names`, in the same order),
/// and none names the person.
fn kept_apart(worlds: &[World], names: &[&str], person: &Person) {
    for (i, w) in worlds.iter().enumerate() {
        let log = Value::Array(w.log().to_vec()).to_string();
        assert!(!log.contains(person.key().as_str()), "world {i}");
        let agents: BTreeSet<&str> = w.log().iter().filter_map(|e| e["agent"].as_str()).collect();
        for (j, other) in worlds.iter().enumerate() {
            if i != j {
                assert!(!log.contains(other.key()), "{i} names {j}");
                let presence = person.presence(other.key(), 0).unwrap();
                assert!(!log.contains(presence.as_str()), "{i} names {j}'s");
                // A presence's name is its own (decision 3): no other
                // world has anyone under it.
                assert!(!agents.contains(names[j]), "{i} has {}", names[j]);
            }
        }
    }
}

#[test]
fn the_octopus_brain_gives_intents_and_its_arms_find_their_own_way() {
    let o = octopus::run().unwrap();
    for w in &o.worlds {
        holds(w);
    }
    let names: Vec<&str> = octopus::ARMS.iter().map(|(_, n, _)| *n).collect();
    kept_apart(&o.worlds, &names, &o.person);
    // Three intents for each arm, each given only once all had done the
    // last: go, then plant, then rest.
    let issued = o.brain.issued();
    assert_eq!(issued.len(), 3 * octopus::ARMS.len());
    for arm in 0..octopus::ARMS.len() {
        let mine: Vec<Intent> = issued
            .iter()
            .filter(|(_, a, _)| *a == arm)
            .map(|(_, _, i)| *i)
            .collect();
        assert_eq!(
            mine,
            vec![
                Intent::Go(SECOND_AT),
                Intent::Plant(Dir::East),
                Intent::Rest
            ]
        );
    }
    // Every arm reported every tick, and stepped aside by its own reflex
    // once, where the trunk stood in its way.
    let reports = o.brain.reports();
    assert_eq!(
        u64::try_from(reports.len()).unwrap(),
        octopus::TICKS * u64::try_from(octopus::ARMS.len()).unwrap()
    );
    for ((_, name, start), w) in octopus::ARMS.iter().zip(&o.worlds) {
        let blocked = of(w, "blocked", name);
        assert_eq!(blocked.len(), 1, "{name}");
        assert_eq!(blocked[0]["data"]["dir"], "east");
        // Blocked by the trunk, after its steps east to the cell before it.
        assert_eq!(blocked[0]["tick"], -1 - start.x, "{name}");
        // Its own steps: the brain chose none of them.
        assert!(of(w, "moved", name).len() >= 8, "{name}");
        let planted = of(w, "planted", name);
        assert_eq!(planted.len(), 1, "{name}");
        assert_eq!(cell(&planted[0]["data"]["at"]), Cell::new(4, 1, 0));
        assert_eq!(w.position(name), Some(SECOND_AT));
    }
    assert_eq!(reports.iter().filter(|r| r.reflex).count(), 3);
    // The brain sent them to plant only after all three had reported
    // arriving, the last two ticks after the others.
    let plant_after = issued
        .iter()
        .find(|(_, _, i)| matches!(i, Intent::Plant(_)))
        .and_then(|(t, _, _)| *t)
        .unwrap();
    // The first intents were given before the run, and only they.
    assert!(
        issued
            .iter()
            .all(|(t, _, i)| t.is_none() == matches!(i, Intent::Go(_)))
    );
    for arm in 0..octopus::ARMS.len() {
        let arrived = reports
            .iter()
            .find(|r| r.arm == arm && r.at == SECOND_AT)
            .unwrap()
            .tick;
        assert!(arrived <= plant_after, "arm {arm}");
    }
    let arrivals: Vec<u64> = (0..octopus::ARMS.len())
        .map(|arm| {
            reports
                .iter()
                .find(|r| r.arm == arm && r.at == SECOND_AT)
                .unwrap()
                .tick
        })
        .collect();
    assert_eq!(arrivals[2], arrivals[0] + 2);
    assert_eq!(plant_after, arrivals[2]);
}

#[test]
fn the_relay_leader_acts_only_when_enough_senses_fire() {
    let r = relay::run().unwrap();
    for w in &r.worlds {
        holds(w);
    }
    let names: Vec<&str> = relay::PRESENCES.iter().map(|(_, n)| *n).collect();
    kept_apart(&r.worlds, &names, &r.person);
    let fired = r.board.fired();
    let first: Vec<u64> = fired
        .iter()
        .filter(|(_, s)| *s == 0)
        .map(|(t, _)| *t)
        .collect();
    let second: Vec<u64> = fired
        .iter()
        .filter(|(_, s)| *s == 1)
        .map(|(t, _)| *t)
        .collect();
    assert_eq!(first, (4..relay::TICKS).collect::<Vec<_>>());
    assert_eq!(second, (9..relay::TICKS).collect::<Vec<_>>());
    // One sense firing alone, for five ticks, moved nothing.
    let leader = &r.worlds[2];
    let planted = of(leader, "planted", relay::PRESENCES[2].1);
    assert_eq!(planted.len(), 1);
    assert_eq!(planted[0]["tick"], 9);
    // Nothing else: the leader acted once, and otherwise only waited.
    let acts: Vec<&str> = leader
        .log()
        .iter()
        .filter(|e| e["agent"] == relay::PRESENCES[2].1 && e["kind"] != "explored")
        .map(|e| e["kind"].as_str().unwrap())
        .collect();
    assert_eq!(acts, vec!["entered", "planted"]);
    // The leader's world sees no one but the leader.
    assert_eq!(of(leader, "entered", "STRANGER").len(), 0);
    assert_eq!(leader.inhabitants().len(), 1);
}

#[test]
fn the_swarm_grows_one_patch_with_no_brain() {
    let s = swarm::run().unwrap();
    holds(&s.world);
    let flowers: BTreeSet<Cell> = s
        .world
        .changes()
        .iter()
        .filter(|(_, m)| **m == Material::Flower)
        .map(|(c, _)| *c)
        .collect();
    // The run is the same every time: 52 flowers, as PERSONS.md says.
    assert_eq!(flowers.len(), 52);
    // The units' person is named nowhere: the units are its presences.
    let log = Value::Array(s.world.log().to_vec()).to_string();
    assert!(!log.contains(s.person.key().as_str()));
    // Replayed from the log: every flower a unit planted is beside one
    // that was there before, the one its planter stood on.
    let mut grown = BTreeSet::from([swarm::FIRST_FLOWER]);
    let mut planters = BTreeSet::new();
    let mut at: std::collections::BTreeMap<String, Cell> = std::collections::BTreeMap::new();
    for e in s.world.log() {
        let who = e["agent"].as_str().unwrap_or("").to_owned();
        match e["kind"].as_str().unwrap() {
            "entered" => {
                at.insert(who, cell(&e["data"]["pos"]));
            }
            "moved" | "fell" => {
                at.insert(who, cell(&e["data"]["to"]));
            }
            "planted" => {
                let flower = cell(&e["data"]["at"]);
                let stood = at[&who];
                assert!(grown.contains(&stood), "{who} planted off a flower");
                let (dx, dz) = (flower.x - stood.x, flower.z - stood.z);
                assert_eq!(dx.abs() + dz.abs(), 1, "{who}: not beside");
                grown.insert(flower);
                planters.insert(who);
            }
            _ => {}
        }
    }
    assert_eq!(grown, flowers);
    // Four of the five planted, and BEE-4 never found the patch: no one
    // of them is the swarm.
    assert_eq!(
        planters,
        BTreeSet::from(["BEE-1", "BEE-2", "BEE-3", "BEE-5"].map(String::from))
    );
    // One patch: every flower reached from the first, side by side.
    let mut reached = BTreeSet::from([swarm::FIRST_FLOWER]);
    let mut frontier = vec![swarm::FIRST_FLOWER];
    while let Some(c) = frontier.pop() {
        for d in Dir::ALL {
            let (dx, dz) = d.step();
            let next = c.offset(dx, 0, dz);
            if flowers.contains(&next) && reached.insert(next) {
                frontier.push(next);
            }
        }
    }
    assert_eq!(reached, flowers);
}

#[test]
fn the_council_counts_persons_not_presences() {
    let c = council::run().unwrap();
    holds(&c.world);
    // Five presences in the council's world, of four persons.
    assert_eq!(c.world.inhabitants().len(), 5);
    let t = &c.tally;
    // Three counted: the first person once though present twice, the
    // third by their later vote, and not the fourth, born far away.
    assert_eq!(t.counts, vec![3, 0]);
    assert_eq!(t.persons, 3);
    assert_eq!(t.outcome, Some(0));
    assert_eq!(t.counted, vec![0, 1, 3]);
    assert_eq!(
        t.problems,
        vec!["votes[4]: by one whose birth no trusted world signed".to_owned()]
    );
    // Each vote is the person's, signed by their identity key.
    let voters = [0, 1, 2, 2, 3];
    for (vote, who) in c.votes.iter().zip(voters) {
        formats::records::check(vote).unwrap();
        assert_eq!(vote["person"], c.persons[who].key().as_str());
    }
    assert_eq!(c.proposal["council"], council::council_key().as_str());
    // The world saw presences, never a person: no identity key in its log.
    let log = Value::Array(c.world.log().to_vec()).to_string();
    for p in &c.persons {
        assert!(!log.contains(p.key().as_str()));
    }
}

#[test]
fn each_run_is_the_same_every_time() {
    let log = |w: &World| w.log().to_vec();
    let (a, b) = (octopus::run().unwrap(), octopus::run().unwrap());
    assert_eq!(log(&a.worlds[0]), log(&b.worlds[0]));
    let (a, b) = (relay::run().unwrap(), relay::run().unwrap());
    assert_eq!(log(&a.worlds[2]), log(&b.worlds[2]));
    let (a, b) = (swarm::run().unwrap(), swarm::run().unwrap());
    assert_eq!(log(&a.world), log(&b.world));
    let (a, b) = (council::run().unwrap(), council::run().unwrap());
    assert_eq!(a.votes, b.votes);
    assert_eq!(a.tally, b.tally);
}
