// Ours, not DeepSeek's (see ../README.md): the technical lead's review
// of the endless-plant sketch, as tests. review/run.sh copies the sketch
// to a scratch folder, adds review/missing.rs to its rule.rs, puts this
// file in as tests/review.rs, and runs `cargo test`. Each test pins one
// finding in the README, so each says what the sketch does, as written.

use endless_plant::{EntryKind, Template, Tip, World};

const POT: (i32, i32, i32, i32) = (0, 0, 20, 20);
const START: Tip = Tip { x: 10, y: 18, direction: 0, depth: 0 };

fn sunny(has_monad: bool) -> Template {
    Template::new(2, 10, 5, 1, 1, 0, 1000, has_monad)
}

fn run(template: Template, seed: [u8; 32], ticks: u32) -> World {
    let mut world = World::new(template, POT, START, seed);
    for _ in 0..ticks {
        if !world.step() {
            break;
        }
    }
    world
}

/// Finding 2: the vector "no-light-no-growth" expects energy -1, no
/// tips, and the log [world_created, died_back, died]. The code rests:
/// nothing gathered, nothing to maintain, so nothing to die back.
#[test]
fn no_light_rests_instead_of_dying() {
    let world = run(Template::new(2, 0, 5, 1, 1, 0, 1000, false), [0; 32], 1);
    assert_eq!(world.energy, 0);
    assert_eq!(world.tips.len(), 1);
    assert!(world.alive);
    let kinds: Vec<EntryKind> = world.log.iter().map(|e| e.kind).collect();
    assert_eq!(kinds, [EntryKind::WorldCreated, EntryKind::Rested]);
}

/// Finding 4: a growth leaves two tips at one point, sharing the one
/// segment that leads there. Dropping a tip removes every segment that
/// ends where it is, and pays back one segment's maintenance, so when
/// both siblings are dropped the segment is paid back twice. Here, when
/// the light goes out, one tick drops 9 tips and removes 5 segments,
/// paying back 9; and the plant dies with 8 segments standing.
#[test]
fn dieback_pays_back_segments_twice_and_leaves_segments() {
    let mut world = run(sunny(false), [1; 32], 6);
    world.template.light = 0;
    // (tips dropped, segments removed, energy paid back) per dieback.
    // With no light, nothing is gathered, so what a tick pays back is
    // its change in energy plus the maintenance it took.
    let mut diebacks = Vec::new();
    loop {
        let (before, energy) = (world.segments.len(), world.energy);
        let more = world.step();
        // The tick's own entry: the last one, or the one before "died".
        let entry = world.log.iter().rev().find(|e| e.kind != EntryKind::Died);
        if let Some(e) = entry.filter(|e| e.kind == EntryKind::DiedBack) {
            let removed = before.saturating_sub(world.segments.len());
            let upkeep = before as i64 * i64::from(world.template.maintenance);
            diebacks.push((e.tips_dropped, removed, world.energy - energy + upkeep));
        }
        if !more {
            break;
        }
    }
    assert_eq!(diebacks.first(), Some(&(9, 5, 9)));
    assert!(!world.alive);
    assert!(world.tips.is_empty());
    assert_eq!(world.segments.len(), 8, "a dead plant's segments");
}

/// Finding 5: nothing stops a segment growing where one already is, and
/// stored energy has no bound. After 2,000 ticks in a 20 by 20 pot the
/// plant has grown 2,000 segments, only 477 of them distinct, and holds
/// over two million units of energy.
#[test]
fn segments_overlap_and_energy_is_unbounded() {
    let world = run(sunny(false), [7; 32], 2000);
    assert!(world.alive);
    assert_eq!(world.segments.len(), 2000);
    let mut distinct = world.segments.clone();
    distinct.sort();
    distinct.dedup();
    assert_eq!(distinct.len(), 477);
    assert_eq!(world.energy, 2_189_945);
}

/// Finding 6: the neuron's noise reads only the seed's first byte, so
/// two seeds that differ only after it give the same run.
#[test]
fn noise_reads_only_the_first_byte_of_the_seed() {
    let mut other = [7; 32];
    other[31] = 8;
    let (a, b) = (run(sunny(true), [7; 32], 200), run(sunny(true), other, 200));
    let energies = |w: &World| w.log.iter().map(|e| e.energy).collect::<Vec<_>>();
    assert_eq!(energies(&a), energies(&b));
    assert_eq!(a.segments, b.segments);
}

/// Finding 2, the other side: the sketch's other two vectors hold, as
/// written ("one-grow" and "monad-one-step": energy 9, one segment, two
/// tips, the log [world_created, grew]).
#[test]
fn the_other_two_vectors_hold() {
    for (has_monad, seed) in [(false, [1; 32]), (true, [3; 32])] {
        let world = run(sunny(has_monad), seed, 1);
        assert_eq!(world.energy, 9);
        assert_eq!(world.segments.len(), 1);
        assert_eq!(world.tips.len(), 2);
        let kinds: Vec<EntryKind> = world.log.iter().map(|e| e.kind).collect();
        assert_eq!(kinds, [EntryKind::WorldCreated, EntryKind::Grew]);
    }
}
