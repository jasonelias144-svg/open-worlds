//! Two RNN-driven residents in the Ur-garden.

use ur_world::garden::{
    Garden, GardenAction, PlantKind,
};
use ur_world::garden::rnn::{
    SamplingMode, TinyRnn, Weights, XorShift64,
};
use ur_world::garden::rnn_mind::TinyRnnMind;
use ur_world::world::{Cell, Mind, World};
use formats::proof::SigningKey;

fn random_weights(rng: &mut XorShift64, n: usize, h: usize,
                   i: usize) -> Weights {
    let g = |rng: &mut XorShift64| (rng.next_f64() - 0.5) * 0.5;
    Weights {
        w_in: (0..h).map(|_| (0..i).map(|_| g(rng)).collect())
            .collect(),
        w_h: (0..h).map(|_| (0..h).map(|_| g(rng)).collect())
            .collect(),
        w_out: (0..n).map(|_| (0..h).map(|_| g(rng)).collect())
            .collect(),
        b_out: vec![0.0; n],
        h_prev: vec![0.0; h],
        baseline: 0.0,
    }
}

fn main() {
    let mut g_rng = XorShift64::new(1234);
    let mut g = Garden::new(
        World::new("garden:demo".to_string(), 0),
        "demo garden".to_string(),
        SigningKey::generate(),
        9, 8, 1,
    );
    g.add_plant("fern".into(), PlantKind::Fern,
        Cell { x: 2, y: 2, z: 0 }, 0xAAAA).unwrap();
    g.add_plant("vine".into(), PlantKind::Vine,
        Cell { x: 4, y: 6, z: 0 }, 0xBBBB).unwrap();

    let alice_key = SigningKey::generate();
    let alice_did = alice_key.did();
    g.admit(&alice_did, "ALICE").unwrap();
    g.apply_action(&alice_did, GardenAction::Enter {
        at: Cell { x: 0, y: 4, z: 0 },
    }).unwrap();

    let mut alice = TinyRnnMind::new(
        TinyRnn::from_weights(random_weights(&mut g_rng, 3, 4, 7)),
        111, SamplingMode::Softmax);

    for _ in 0..20 {
        let obs = ur_world::garden::rnn_mind::Observation {
            position: *g.agent_positions.get(&alice_did).unwrap(),
            last_action: 0,
            last_reward_micros: 0,
            plants: g.plants_active.iter()
                .map(|(k, v)| (k.clone(), v.position)).collect(),
            nearby_agents: vec![],
            garden_size: [g.width, g.height, g.depth],
        };
        let action = alice.observe(obs);
        if let Err(e) = g.apply_action(&alice_did, action) {
            eprintln!("action refused: {:?}", e);
        }
        alice.receive(ur_world::garden::rnn_mind::Outcome {
            accepted: true,
            reward_micros: 50_000,
        });
        g.advance_cycle(1).unwrap();
    }

    g.verify_log().expect("log must verify");
    g.verify_cross_references().expect("cross-refs must verify");
    println!("final log length: {}", g.log.len());
    println!("verify: OK");
}
