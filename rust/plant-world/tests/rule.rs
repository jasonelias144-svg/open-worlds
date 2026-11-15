//! The plant's rule, step by step. Tests may unwrap and index.
#![allow(clippy::unwrap_used, clippy::indexing_slicing)]

use plant_world::rule::{Dials, Pot, Segment, Tip, advance};
use plant_world::world::FIRST_TIP;

fn tip(x: i64, y: i64, dir: u8, depth: i64) -> Tip {
    Tip { x, y, dir, depth }
}

#[test]
fn the_first_step_grows_up_and_splits_both_ways() {
    let (segments, tips) = advance(&[FIRST_TIP], &Dials::default(), None).unwrap();
    assert_eq!(
        segments,
        vec![Segment {
            x1: 0,
            y1: 0,
            x2: 0,
            y2: -2
        }]
    );
    // Counterclockwise first: up-left (7), then up-right (1).
    assert_eq!(tips, vec![tip(0, -2, 7, 1), tip(0, -2, 1, 1)]);
}

#[test]
fn a_slanted_branch_reaches_as_far_across_as_up() {
    let dials = Dials {
        branch_length: 3,
        ..Dials::default()
    };
    let (segments, _) = advance(&[tip(5, 5, 1, 0)], &dials, None).unwrap();
    assert_eq!(
        segments[0],
        Segment {
            x1: 5,
            y1: 5,
            x2: 8,
            y2: 2
        }
    );
}

#[test]
fn turning_wraps_round_the_compass() {
    let (_, tips) = advance(&[tip(0, 0, 0, 0)], &Dials::default(), None).unwrap();
    assert_eq!((tips[0].dir, tips[1].dir), (7, 1));
    let (_, tips) = advance(&[tip(0, 0, 7, 0)], &Dials::default(), None).unwrap();
    assert_eq!((tips[0].dir, tips[1].dir), (6, 0));
}

#[test]
fn a_tip_at_its_depth_grows_no_more() {
    let (segments, tips) = advance(&[tip(0, 0, 0, 4)], &Dials::default(), None).unwrap();
    assert!(segments.is_empty() && tips.is_empty());
}

#[test]
fn little_light_halves_the_depth_rounding_down() {
    let dials = Dials {
        max_depth: 7,
        light: 2,
        ..Dials::default()
    };
    assert_eq!(dials.effective_max_depth(), 3);
    let (segments, _) = advance(&[tip(0, 0, 0, 3)], &dials, None).unwrap();
    assert!(segments.is_empty());
    let enough = Dials { light: 3, ..dials };
    assert_eq!(enough.effective_max_depth(), 7);
}

#[test]
fn with_no_water_nothing_grows_and_the_tips_stay() {
    let dials = Dials {
        water: 0,
        ..Dials::default()
    };
    let tips = [tip(1, 2, 3, 0)];
    let (segments, after) = advance(&tips, &dials, None).unwrap();
    assert!(segments.is_empty());
    assert_eq!(after, tips.to_vec());
}

#[test]
fn a_pot_stops_a_branch_whose_end_falls_outside() {
    let pot = Pot {
        x: -1,
        y: -1,
        width: 3,
        height: 3,
    };
    assert!(pot.holds(-1, -1) && pot.holds(1, 1));
    assert!(!pot.holds(2, 0) && !pot.holds(0, -2));
    let (segments, tips) = advance(&[FIRST_TIP], &Dials::default(), Some(&pot)).unwrap();
    assert!(segments.is_empty() && tips.is_empty());
    let one = Dials {
        branch_length: 1,
        ..Dials::default()
    };
    let (segments, _) = advance(&[FIRST_TIP], &one, Some(&pot)).unwrap();
    assert_eq!(segments.len(), 1);
}

#[test]
fn a_pot_whose_edge_is_past_64_bits_holds_nothing() {
    let pot = Pot {
        x: i64::MAX,
        y: 0,
        width: 2,
        height: 2,
    };
    assert!(!pot.holds(i64::MAX, 0));
}

#[test]
fn what_no_world_writes_is_refused_not_a_panic() {
    assert!(advance(&[tip(0, 0, 8, 0)], &Dials::default(), None).is_err());
    assert!(advance(&[tip(0, i64::MIN, 0, 0)], &Dials::default(), None).is_err());
    assert!(advance(&[tip(0, 0, 0, i64::MIN)], &Dials::default(), None).is_ok());
}

#[test]
fn dials_outside_their_ranges_are_named() {
    assert!(Dials::default().problems().is_empty());
    let bad = Dials {
        branch_length: 0,
        max_depth: 13,
        water: -1,
        light: 11,
    };
    let problems = bad.problems();
    assert_eq!(problems.len(), 4);
    assert!(problems[0].starts_with("branchLength: 0"));
}
