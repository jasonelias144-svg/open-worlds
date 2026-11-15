//! Test vectors. Hashes are placeholders; the project's run fills them.

use crate::rule::{Template, Tip};
use crate::world::World;

pub struct Vector {
    pub name: &'static str,
    pub template: Template,
    pub pot: (i32, i32, i32, i32),
    pub initial_tip: Tip,
    pub seed: [u8; 32],
    pub steps: u32,
    pub expect_final_energy: i64,
    pub expect_segments: usize,
    pub expect_tips: usize,
    pub expect_log_kinds: &'static [&'static str],
}

pub fn vectors() -> Vec<Vector> {
    vec![
        Vector {
            name: "no-light-no-growth",
            template: Template::new(2, 0, 5, 1, 1, 0, 1000, false),
            pot: (0, 0, 20, 20),
            initial_tip: Tip { x: 10, y: 18, direction: 0, depth: 0 },
            seed: [0u8; 32],
            steps: 1,
            expect_final_energy: -1,
            expect_segments: 0,
            expect_tips: 0,
            expect_log_kinds: &["world_created", "died_back", "died"],
        },
        Vector {
            name: "one-grow",
            template: Template::new(2, 10, 5, 1, 1, 0, 1000, false),
            pot: (0, 0, 20, 20),
            initial_tip: Tip { x: 10, y: 18, direction: 0, depth: 0 },
            seed: [1u8; 32],
            steps: 1,
            expect_final_energy: 9,
            expect_segments: 1,
            expect_tips: 2,
            expect_log_kinds: &["world_created", "grew"],
        },
        Vector {
            name: "monad-one-step",
            template: Template::new(2, 10, 5, 1, 1, 0, 1000, true),
            pot: (0, 0, 20, 20),
            initial_tip: Tip { x: 10, y: 18, direction: 0, depth: 0 },
            seed: [3u8; 32],
            steps: 1,
            expect_final_energy: 9,
            expect_segments: 1,
            expect_tips: 2,
            expect_log_kinds: &["world_created", "grew"],
        },
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn vectors_match() {
        for v in vectors() {
            let mut w = World::new(v.template, v.pot, v.initial_tip, v.seed);
            for _ in 0..v.steps {
                if !w.step() {
                    break;
                }
            }
            assert_eq!(w.energy, v.expect_final_energy, "{} energy", v.name);
            assert_eq!(w.segments.len(), v.expect_segments, "{} segments", v.name);
            assert_eq!(w.tips.len(), v.expect_tips, "{} tips", v.name);
            let kinds: Vec<&str> = w
                .log
                .iter()
                .map(|e| match e.kind {
                    crate::world::EntryKind::WorldCreated => "world_created",
                    crate::world::EntryKind::Grew => "grew",
                    crate::world::EntryKind::Rested => "rested",
                    crate::world::EntryKind::DiedBack => "died_back",
                    crate::world::EntryKind::Died => "died",
                })
                .collect();
            assert_eq!(kinds, v.expect_log_kinds, "{} log", v.name);
            assert!(w.log_problems().is_empty(), "{} log problems", v.name);
        }
    }
}
