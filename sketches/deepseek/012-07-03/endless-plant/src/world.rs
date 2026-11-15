//! The world: seed, log, tick, regrow check.
//!
//! Stand-in: the log hash uses FNV-1a for legibility. The real
//! implementation must use `formats::canonical` + SHA-256 and the
//! signed entry shape.

use crate::monad::{Action, Neuron, FEATURE_COUNT};
use crate::rule::{
    dieback_priority, gathered_at, grow_from, growth_priority, next_cell,
    shadow_count, shadow_map, Segment, Template, Tip,
};
use std::collections::HashMap;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum EntryKind {
    WorldCreated,
    Grew,
    Rested,
    DiedBack,
    Died,
}

#[derive(Clone, Debug)]
pub struct Entry {
    pub kind: EntryKind,
    pub tick: u32,
    pub energy: i64,
    pub segments_added: u32,
    pub tips_dropped: u32,
    pub prev_hash: String,
    pub hash: String,
    pub body: String,
}

#[derive(Clone, Debug)]
pub struct World {
    pub template: Template,
    pub pot: (i32, i32, i32, i32),
    pub initial_tip: Tip,
    pub seed: [u8; 32],
    pub energy: i64,
    pub segments: Vec<Segment>,
    pub tips: Vec<Tip>,
    pub alive: bool,
    pub tick: u32,
    pub neuron: Option<Neuron>,
    pub log: Vec<Entry>,
    prev_hash: String,
}

impl World {
    pub fn new(
        template: Template,
        pot: (i32, i32, i32, i32),
        initial_tip: Tip,
        seed: [u8; 32],
    ) -> Self {
        let neuron = if template.has_monad {
            Some(Neuron::new())
        } else {
            None
        };
        let mut w = Self {
            template,
            pot,
            initial_tip,
            seed,
            energy: template.reserve as i64,
            segments: Vec::new(),
            tips: vec![initial_tip],
            alive: true,
            tick: 0,
            neuron,
            log: Vec::new(),
            prev_hash: String::new(),
        };
        w.push_entry(EntryKind::WorldCreated, 0, 0);
        w
    }

    pub fn step(&mut self) -> bool {
        if !self.alive {
            return false;
        }
        let energy_before = self.energy;

        // 1. Gather
        let map = shadow_map(&self.segments);
        let mut gathered: i64 = 0;
        for tip in &self.tips {
            gathered += gathered_at(&self.template, &map, tip) as i64;
        }
        self.energy += gathered;

        // 2. Maintain
        let maint =
            (self.segments.len() as i64) * (self.template.maintenance as i64);
        self.energy -= maint;

        // 3. Dieback if needed
        let mut dropped = 0u32;
        while self.energy < 0 && !self.tips.is_empty() {
            let Some(idx) = self.worst_tip(&map) else { break };
            let tip = self.tips.remove(idx);
            self.segments
                .retain(|s| !(s.x2 == tip.x && s.y2 == tip.y));
            self.energy += self.template.maintenance as i64;
            dropped += 1;
        }

        // 4. Choose and apply an action
        let mut segments_added = 0u32;
        let features = self.features(&map);
        let action = self.choose_action(&map);
        match action {
            Action::Grow | Action::Split => {
                if self.energy >= self.template.growth_cost as i64 {
                    if let Some(idx) = self.best_tip(&map) {
                        let tip = self.tips[idx];
                        if let Some((seg, new_tips)) =
                            grow_from(&self.template, &tip, self.pot)
                        {
                            self.tips.remove(idx);
                            self.tips.extend_from_slice(&new_tips);
                            self.segments.push(seg);
                            self.energy -= self.template.growth_cost as i64;
                            segments_added = 1;
                        }
                    }
                }
            }
            Action::Rest => {}
            Action::Drop => {
                if let Some(idx) = self.worst_tip(&map) {
                    let tip = self.tips.remove(idx);
                    self.segments
                        .retain(|s| !(s.x2 == tip.x && s.y2 == tip.y));
                    self.energy += self.template.maintenance as i64;
                    dropped += 1;
                }
            }
        }

        // 5. Learn
        if let Some(neuron) = self.neuron.as_mut() {
            let reward = (self.energy - energy_before) as i32;
            neuron.learn(action, &features, reward);
        }

        // 6. Log
        self.tick += 1;
        let kind = if segments_added > 0 {
            EntryKind::Grew
        } else if dropped > 0 {
            EntryKind::DiedBack
        } else {
            EntryKind::Rested
        };
        self.push_entry(kind, segments_added, dropped);

        // 7. Death
        if self.tips.is_empty() {
            self.alive = false;
            self.push_entry(EntryKind::Died, 0, 0);
            return false;
        }
        true
    }

    fn best_tip(&self, map: &HashMap<i32, Vec<i32>>) -> Option<usize> {
        self.tips
            .iter()
            .enumerate()
            .filter(|(_, t)| next_cell(&self.template, t, self.pot).is_some())
            .max_by_key(|(_, t)| growth_priority(&self.template, map, t))
            .map(|(i, _)| i)
    }

    fn worst_tip(&self, map: &HashMap<i32, Vec<i32>>) -> Option<usize> {
        self.tips
            .iter()
            .enumerate()
            .max_by_key(|(_, t)| dieback_priority(&self.template, map, t))
            .map(|(i, _)| i)
    }

    fn features(&self, map: &HashMap<i32, Vec<i32>>) -> [i32; FEATURE_COUNT] {
        let tip = self
            .best_tip(map)
            .map(|i| self.tips[i])
            .unwrap_or(self.initial_tip);
        let light_here = gathered_at(&self.template, map, &tip) as i32;
        let shade_here = shadow_count(map, tip.x, tip.y) as i32;
        let height = self.pot.3 - tip.y;
        let crowding = self
            .tips
            .iter()
            .filter(|t| {
                (t.x - tip.x).abs() + (t.y - tip.y).abs()
                    <= self.template.branch_length as i32
            })
            .count() as i32;
        let energy = self.energy.clamp(-100, 100) as i32;
        let age = self.tick.min(100) as i32;
        [light_here, shade_here, height, crowding, energy, age]
    }

    fn choose_action(&self, map: &HashMap<i32, Vec<i32>>) -> Action {
        let feasible = self.feasible_actions(map);
        if let Some(neuron) = &self.neuron {
            let features = self.features(map);
            let noise_seed = (self.seed[0] as i32) ^ (self.tick as i32);
            neuron.choose(&features, &feasible, noise_seed)
        } else if self.energy >= self.template.growth_cost as i64
            && self.best_tip(map).is_some()
        {
            Action::Grow
        } else {
            Action::Rest
        }
    }

    fn feasible_actions(&self, map: &HashMap<i32, Vec<i32>>) -> Vec<Action> {
        let mut v = vec![Action::Rest];
        if self.energy >= self.template.growth_cost as i64
            && self.best_tip(map).is_some()
        {
            v.push(Action::Grow);
            v.push(Action::Split);
        }
        if !self.tips.is_empty() {
            v.push(Action::Drop);
        }
        v
    }

    fn push_entry(
        &mut self,
        kind: EntryKind,
        segments_added: u32,
        tips_dropped: u32,
    ) {
        let body = format!(
            "{}:{}:{}:{}:{}",
            kind_str(kind),
            self.tick,
            self.energy,
            segments_added,
            tips_dropped
        );
        let prev = self.prev_hash.clone();
        let hash = format!("{:x}", fnv1a(&prev, &body));
        self.log.push(Entry {
            kind,
            tick: self.tick,
            energy: self.energy,
            segments_added,
            tips_dropped,
            prev_hash: prev,
            hash: hash.clone(),
            body,
        });
        self.prev_hash = hash;
    }

    pub fn log_problems(&self) -> Vec<String> {
        let mut problems = Vec::new();
        let mut prev = String::new();
        for (i, e) in self.log.iter().enumerate() {
            if e.prev_hash != prev {
                problems.push(format!("entry {i}: prev mismatch"));
            }
            let body = format!(
                "{}:{}:{}:{}:{}",
                kind_str(e.kind),
                e.tick,
                e.energy,
                e.segments_added,
                e.tips_dropped
            );
            let hash = format!("{:x}", fnv1a(&prev, &body));
            if hash != e.hash {
                problems.push(format!("entry {i}: hash mismatch"));
            }
            prev = hash;
        }
        problems
    }
}

fn kind_str(k: EntryKind) -> &'static str {
    match k {
        EntryKind::WorldCreated => "world_created",
        EntryKind::Grew => "grew",
        EntryKind::Rested => "rested",
        EntryKind::DiedBack => "died_back",
        EntryKind::Died => "died",
    }
}

fn fnv1a(a: &str, b: &str) -> u64 {
    let mut h: u64 = 0xcbf2_9ce4_8422_2325;
    for byte in a.bytes().chain(b.bytes()) {
        h ^= byte as u64;
        h = h.wrapping_mul(0x0000_0100_0000_01b3);
    }
    h
}
