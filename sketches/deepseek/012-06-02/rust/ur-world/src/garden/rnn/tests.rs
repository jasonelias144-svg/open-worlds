#[cfg(test)]
mod tests {
    use super::*;
    use crate::garden::rnn::{SamplingMode, TinyRnn, Weights};
    use std::fs;
    use std::path::PathBuf;

    fn load_vector() -> serde_json::Value {
        let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .join("..").join("..").join("vectors")
            .join("garden_reference.json");
        serde_json::from_str(
            &fs::read_to_string(&path).unwrap_or_else(|_|
                panic!("run gen_garden_reference.py first")),
        ).unwrap()
    }

    fn load_weights(v: &serde_json::Value) -> Weights {
        serde_json::from_value(v["rnn"]["initial_weights"].clone())
            .expect("weights shape mismatch")
    }

    fn quantize_weights(w: &Weights) -> serde_json::Value {
        let q = |x: f64| (x * 1e9).round() as i64;
        serde_json::json!({
            "w_in": w.w_in.iter().map(|r| r.iter().map(|&v| q(v)).collect::<Vec<_>>()).collect::<Vec<_>>(),
            "w_h": w.w_h.iter().map(|r| r.iter().map(|&v| q(v)).collect::<Vec<_>>()).collect::<Vec<_>>(),
            "w_out": w.w_out.iter().map(|r| r.iter().map(|&v| q(v)).collect::<Vec<_>>()).collect::<Vec<_>>(),
            "b_out": w.b_out.iter().map(|&v| q(v)).collect::<Vec<_>>(),
            "h_prev": w.h_prev.iter().map(|&v| q(v)).collect::<Vec<_>>(),
            "baseline": q(w.baseline),
        })
    }

    #[test]
    fn rnn_forward_and_learn_match_vector() {
        let v = load_vector();
        let mut rnn = TinyRnn::from_weights(load_weights(&v));
        let tol_prob = 1e-6;
        let tol_baseline = 1e-9;

        for (i, tc) in v["rnn"]["test_cases"].as_array()
            .unwrap().iter().enumerate()
        {
            let state: Vec<f64> = serde_json::from_value(
                tc["state"].clone()).unwrap();
            let expected_probs: Vec<f64> = serde_json::from_value(
                tc["expected_probs"].clone()).unwrap();
            let chosen = tc["chosen_action"].as_u64().unwrap() as usize;
            let reward = tc["reward"].as_f64().unwrap();
            let expected_baseline =
                tc["expected_baseline_after"].as_f64().unwrap();

            let probs = rnn.forward(&state).to_vec();
            for k in 0..probs.len() {
                assert!(
                    (probs[k] - expected_probs[k]).abs() < tol_prob,
                    "case {}: probs[{}] = {}, expected {}, delta {}",
                    i, k, probs[k], expected_probs[k],
                    (probs[k] - expected_probs[k]).abs()
                );
            }

            rnn.learn(chosen, reward);
            assert!(
                (rnn.weights.baseline - expected_baseline).abs()
                    < tol_baseline,
                "case {}: baseline = {}, expected {}",
                i, rnn.weights.baseline, expected_baseline
            );

            let quantized = quantize_weights(&rnn.serialize_weights());
            let actual_hash = sha256_hex(
                &serde_jcs::to_vec(&quantized).unwrap());
            let expected_hash = tc["expected_weights_after_hash"]
                .as_str().unwrap();
            assert_eq!(
                actual_hash, expected_hash,
                "case {}: weights-after hash mismatch", i
            );
        }
    }

    #[test]
    fn argmax_picks_highest_prob() {
        let v = load_vector();
        let mut rnn = TinyRnn::from_weights(load_weights(&v));
        let state: Vec<f64> = serde_json::from_value(
            v["rnn"]["test_cases"][0]["state"].clone()).unwrap();
        let mut rng = XorShift64::new(0);
        let (action, probs) = rnn.act(&state,
            SamplingMode::Argmax, &mut rng);
        let max_idx = probs.iter().enumerate()
            .max_by(|a, b| a.1.partial_cmp(b.1).unwrap())
            .map(|(i, _)| i).unwrap();
        assert_eq!(action, max_idx);
    }

    #[test]
    fn softmax_sampling_matches_distribution() {
        // Draw 1000 samples; check frequencies are close to
        // the probabilities.
        let v = load_vector();
        let mut rng = XorShift64::new(7);
        let state: Vec<f64> = serde_json::from_value(
            v["rnn"]["test_cases"][0]["state"].clone()).unwrap();
        let weights = load_weights(&v);
        let mut counts = [0usize; 3];
        const N: usize = 1000;
        for _ in 0..N {
            let mut rnn = TinyRnn::from_weights(weights.clone());
            let (a, _) = rnn.act(&state,
                SamplingMode::Softmax, &mut rng);
            counts[a] += 1;
        }
        // Loose check: each frequency within 5% of expected.
        let expected = [0.333, 0.333, 0.334];
        for k in 0..3 {
            let freq = counts[k] as f64 / N as f64;
            assert!(
                (freq - expected[k]).abs() < 0.05,
                "freq[{}] = {}, expected ≈ {}", k, freq, expected[k]
            );
        }
    }

    fn sha256_hex(bytes: &[u8]) -> String {
        use sha2::{Digest, Sha256};
        let mut h = Sha256::new();
        h.update(bytes);
        hex::encode(h.finalize())
    }
}
