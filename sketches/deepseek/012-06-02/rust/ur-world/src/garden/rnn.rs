//! The 4-unit Elman RNN, ported from `coupled_learners.py`.
//!
//! Faithful to the Python reference:
//!   - Forward pass: `h = tanh(W_in·x + W_h·h_prev)`, `logits = W_out·h + b_out`, `probs = softmax(logits)`
//!   - Learn: REINFORCE with a running baseline (`baseline' = 0.99·baseline + 0.01·reward`), gradient computed exactly as Python does
//!   - Activation: greedy (argmax) or softmax sampling, selected by `SamplingMode`
//!
//! What's tested against the Python vector:
//!   - `forward()` returns matching `probs` (within `PROB_TOLERANCE = 1e-6`)
//!   - `learn()` updates weights to matching values (within `WEIGHT_TOLERANCE = 1e-9`)
//!
//! What's NOT tested cross-language:
//!   - Sampling sequences (Rust uses `XorShift64`, Python uses `random.Random`)
//!   - Weight initialization from a seed (Rust loads weights directly; Python generates them)

use serde::{Deserialize, Serialize};

pub const LEARNING_RATE: f64 = 0.01;
pub const BASELINE_DECAY: f64 = 0.99;
pub const BASELINE_UPDATE: f64 = 0.01;
pub const ADVANTAGE_EPSILON: f64 = 1e-6;

// ────────────────────────────────────────────────────────────
// Weights
// ────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Weights {
    pub w_in: Vec<Vec<f64>>,   // [hidden][in_dim]
    pub w_h: Vec<Vec<f64>>,    // [hidden][hidden]
    pub w_out: Vec<Vec<f64>>,  // [n_actions][hidden]
    pub b_out: Vec<f64>,       // [n_actions]
    pub h_prev: Vec<f64>,      // [hidden]
    pub baseline: f64,
}

// ────────────────────────────────────────────────────────────
// Sampling mode
// ────────────────────────────────────────────────────────────

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SamplingMode {
    /// Deterministic: pick the action with the highest
    /// probability. For reproducible tests and demos.
    Argmax,
    /// Sample from `softmax(logits)`. Matches Python's
    /// distribution; not its sequence.
    Softmax,
}

// ────────────────────────────────────────────────────────────
// The RNN
// ────────────────────────────────────────────────────────────

pub struct TinyRnn {
    pub n_actions: usize,
    pub hidden: usize,
    pub in_dim: usize,
    pub weights: Weights,
    // Forward-pass cache for learn().
    last_inputs: Vec<f64>,
    last_h: Vec<f64>,
    last_probs: Vec<f64>,
    last_action: usize,
    has_forward: bool,
}

impl TinyRnn {
    /// Load from a `Weights` structure. The caller is
    /// responsible for the weights' shape consistency.
    pub fn from_weights(weights: Weights) -> Self {
        let hidden = weights.w_in.len();
        let in_dim = weights.w_in[0].len();
        let n_actions = weights.w_out.len();
        Self {
            n_actions,
            hidden,
            in_dim,
            weights,
            last_inputs: Vec::new(),
            last_h: Vec::new(),
            last_probs: Vec::new(),
            last_action: 0,
            has_forward: false,
        }
    }

    /// Convenience: initialize with zeros (only used by tests
    /// that want a "blank" RNN, not production).
    pub fn zeros(n_actions: usize, hidden: usize, in_dim: usize) -> Self {
        Self::from_weights(Weights {
            w_in: vec![vec![0.0; in_dim]; hidden],
            w_h: vec![vec![0.0; hidden]; hidden],
            w_out: vec![vec![0.0; hidden]; n_actions],
            b_out: vec![0.0; n_actions],
            h_prev: vec![0.0; hidden],
            baseline: 0.0,
        })
    }

    /// Forward pass. `state` is the flat input vector
    /// (including the one-hot action prefix, `last_reward`,
    /// `x_norm`, `y_norm`). Returns the softmax probabilities.
    pub fn forward(&mut self, state: &[f64]) -> &[f64] {
        // Build the input: state already contains the one-hot
        // prefix per the Python format. in_dim = n_actions + 3.
        self.last_inputs = state.to_vec();

        // h_new = tanh(W_in·inputs + W_h·h_prev)
        let mut h_new = vec![0.0; self.hidden];
        for i in 0..self.hidden {
            let mut sum = 0.0;
            for j in 0..self.in_dim {
                sum += self.weights.w_in[i][j] * self.last_inputs[j];
            }
            for j in 0..self.hidden {
                sum += self.weights.w_h[i][j] * self.weights.h_prev[j];
            }
            h_new[i] = sum.tanh();
        }

        // logits = W_out·h_new + b_out
        let mut logits = vec![0.0; self.n_actions];
        for a in 0..self.n_actions {
            let mut sum = self.weights.b_out[a];
            for i in 0..self.hidden {
                sum += self.weights.w_out[a][i] * h_new[i];
            }
            logits[a] = sum;
        }

        // softmax
        let max = logits.iter().cloned()
            .fold(f64::NEG_INFINITY, f64::max);
        let exps: Vec<f64> = logits.iter()
            .map(|l| (l - max).exp())
            .collect();
        let sum: f64 = exps.iter().sum();
        let probs: Vec<f64> = exps.iter().map(|e| e / sum).collect();

        // Cache for learn() — mirrors Python's state update.
        self.last_h = h_new.clone();
        self.last_probs = probs.clone();
        self.weights.h_prev = h_new;  // Python: self._h_prev = h
        self.has_forward = true;

        &self.last_probs
    }

    /// Pick an action. Records the choice for `learn()`.
    /// Returns (action_idx, probs).
    pub fn act(
        &mut self,
        state: &[f64],
        mode: SamplingMode,
        rng: &mut XorShift64,
    ) -> (usize, Vec<f64>) {
        let probs = self.forward(state).to_vec();
        let action = match mode {
            SamplingMode::Argmax => {
                probs.iter().enumerate()
                    .max_by(|a, b| a.1.partial_cmp(b.1)
                        .unwrap_or(std::cmp::Ordering::Equal))
                    .map(|(i, _)| i)
                    .unwrap_or(0)
            }
            SamplingMode::Softmax => {
                let r = rng.next_f64();
                let mut cum = 0.0;
                let mut chosen = self.n_actions - 1;
                for (i, p) in probs.iter().enumerate() {
                    cum += p;
                    if r < cum {
                        chosen = i;
                        break;
                    }
                }
                chosen
            }
        };
        self.last_action = action;
        (action, probs)
    }

    /// REINFORCE update, matching Python's `learn()` exactly.
    /// `chosen_action` must be the action returned by `act()`.
    pub fn learn(&mut self, chosen_action: usize, reward: f64) {
        self.weights.baseline = BASELINE_DECAY * self.weights.baseline
            + BASELINE_UPDATE * reward;
        let advantage = reward - self.weights.baseline;
        if advantage.abs() < ADVANTAGE_EPSILON || !self.has_forward {
            return;
        }

        // grad_logits[k] = (1 - probs[k]) if k == chosen else -probs[k]
        let mut grad_logits = vec![0.0; self.n_actions];
        for k in 0..self.n_actions {
            grad_logits[k] = if k == chosen_action {
                1.0 - self.last_probs[k]
            } else {
                -self.last_probs[k]
            };
        }

        // W_out and b_out
        for k in 0..self.n_actions {
            for i in 0..self.hidden {
                self.weights.w_out[k][i] += LEARNING_RATE
                    * advantage * grad_logits[k] * self.last_h[i];
            }
            self.weights.b_out[k] += LEARNING_RATE
                * advantage * grad_logits[k];
        }

        // W_in and W_h (first-order approximation, matching
        // Python's derivation)
        for i in 0..self.hidden {
            let mut dh = 0.0;
            for k in 0..self.n_actions {
                dh += self.weights.w_out[k][i] * grad_logits[k];
            }
            let dt = dh * (1.0 - self.last_h[i] * self.last_h[i]);
            for j in 0..self.in_dim {
                self.weights.w_in[i][j] += LEARNING_RATE
                    * advantage * dt * self.last_inputs[j];
            }
            for j in 0..self.hidden {
                self.weights.w_h[i][j] += LEARNING_RATE
                    * advantage * dt * self.weights.h_prev[j];
            }
        }
    }

    pub fn serialize_weights(&self) -> Weights {
        self.weights.clone()
    }
}

// ────────────────────────────────────────────────────────────
// Deterministic RNG (matches the garden's other uses)
// ────────────────────────────────────────────────────────────

pub struct XorShift64(pub u64);

impl XorShift64 {
    pub fn new(seed: u64) -> Self { Self(seed | 1) }

    pub fn next(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.0 = x;
        x.wrapping_mul(0x2545F4914F6CDD1D)
    }

    /// Uniform [0, 1).
    pub fn next_f64(&mut self) -> f64 {
        (self.next() >> 11) as f64 * (1.0 / (1u64 << 53) as f64)
    }
}
