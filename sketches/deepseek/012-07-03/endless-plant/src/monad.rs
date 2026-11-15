//! A single choice neuron per plant.

pub const ACTION_COUNT: usize = 4;
pub const FEATURE_COUNT: usize = 6;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Action {
    Grow,
    Split,
    Rest,
    Drop,
}

impl Action {
    pub fn index(self) -> usize {
        match self {
            Action::Grow => 0,
            Action::Split => 1,
            Action::Rest => 2,
            Action::Drop => 3,
        }
    }

    pub fn name(self) -> &'static str {
        match self {
            Action::Grow => "grow",
            Action::Split => "split",
            Action::Rest => "rest",
            Action::Drop => "drop",
        }
    }
}

#[derive(Clone, Debug)]
pub struct Neuron {
    /// weights[action][feature]
    pub weights: [[i32; FEATURE_COUNT]; ACTION_COUNT],
    pub baseline: i32,
    pub samples: u32,
    pub learning_rate: i32,
}

impl Neuron {
    pub fn new() -> Self {
        Self {
            weights: [[0; FEATURE_COUNT]; ACTION_COUNT],
            baseline: 0,
            samples: 0,
            learning_rate: 1,
        }
    }

    pub fn score(
        &self,
        action: Action,
        features: &[i32; FEATURE_COUNT],
    ) -> i32 {
        let w = &self.weights[action.index()];
        let mut s: i64 = 0;
        for i in 0..FEATURE_COUNT {
            s += (w[i] as i64) * (features[i] as i64);
        }
        (s / 100) as i32
    }

    pub fn choose(
        &self,
        features: &[i32; FEATURE_COUNT],
        feasible: &[Action],
        noise_seed: i32,
    ) -> Action {
        let mut best = feasible[0];
        let mut best_score = i32::MIN;
        for &a in feasible {
            let s = self.score(a, features) + noise_for(a, noise_seed);
            if s > best_score {
                best_score = s;
                best = a;
            }
        }
        best
    }

    pub fn learn(
        &mut self,
        action: Action,
        features: &[i32; FEATURE_COUNT],
        reward: i32,
    ) {
        self.samples = self.samples.saturating_add(1);
        let n = self.samples as i64;
        self.baseline =
            ((self.baseline as i64 * (n - 1) + reward as i64) / n) as i32;
        let delta = reward - self.baseline;
        let w = &mut self.weights[action.index()];
        for i in 0..FEATURE_COUNT {
            let upd =
                (self.learning_rate as i64 * delta as i64
                 * features[i] as i64) / 100;
            w[i] = ((w[i] as i64 + upd).clamp(-100, 100)) as i32;
        }
    }
}

/// Deterministic per-action noise from a tick-derived integer.
fn noise_for(action: Action, seed: i32) -> i32 {
    let mut x = (seed as u64) ^ ((action.index() as u64) << 32);
    x = (x ^ (x >> 30)).wrapping_mul(0xbf58_476d_1ce4_e5b9);
    x = (x ^ (x >> 27)).wrapping_mul(0x94d0_49bb_1331_11eb);
    x ^= x >> 31;
    ((x % 11) as i32) - 5
}
