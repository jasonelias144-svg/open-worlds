use chat_world::error::Result;
use chat_world::hash::body_for_signing;
use chat_world::observe::{
    suggest_discriminating_probe, verify_observation_log, CandidateModel, HiddenSecret, ModelRule,
    ObservationLaw, ObservationLog, ObservationRecord, ObservationWorld, ProbeReading,
    ProbeRecorded, ReadoutKind, ReadoutSpec, SecretRevealed,
};
use chat_world::{Keypair, Proof, ProofOrArray};

#[test]
fn finite_agreement_at_zero_and_one_fails_to_identify_quadratic_until_input_two() -> Result<()> {
    let alice = Keypair::generate();
    let world_kp = Keypair::generate();

    // Chapter 119.7: f(x) = x and g(x) = x^2 agree at 0 and 1, and diverge at 2.
    let law = ObservationLaw {
        topic: "Distinguish f(x) = x from g(x) = x^2".into(),
        candidates: vec![
            CandidateModel {
                name: "linear".into(),
                rule: ModelRule::Affine {
                    slope: 1,
                    intercept: 0,
                },
            },
            CandidateModel {
                name: "quadratic".into(),
                rule: ModelRule::Quadratic { a: 1, b: 0, c: 0 },
            },
        ],
        admitted_readouts: vec![ReadoutSpec {
            name: "exact".into(),
            kind: ReadoutKind::Exact,
            cost: 1,
        }],
        probe_budget: 5,
        input_min: 0,
        input_max: 5,
    };

    let mut world = ObservationWorld::open(law, 1, "salt-ch119-01", world_kp, &alice, 100)?;

    // Probing 0 and 1 yields exact agreement between both candidates.
    let p0 = world.probe(&alice, 0, "exact", 101)?;
    let p1 = world.probe(&alice, 1, "exact", 102)?;
    assert_eq!(p0.reading, ProbeReading::Exact { value: 0 });
    assert_eq!(p1.reading, ProbeReading::Exact { value: 1 });
    assert_eq!(
        world.compatible_candidates()?,
        vec!["linear".to_string(), "quadratic".to_string()]
    );

    // Alice commits to a prediction under the mistaken "linear" hypothesis at x = 2.
    world.predict(
        &alice,
        2,
        "exact",
        ProbeReading::Exact { value: 2 },
        "linear",
        103,
    )?;
    let p2 = world.probe(&alice, 2, "exact", 104)?;
    assert_eq!(p2.reading, ProbeReading::Exact { value: 4 });
    assert_eq!(p2.prediction_matched, Some(false));

    // Only quadratic remains compatible.
    assert_eq!(world.compatible_candidates()?, vec!["quadratic".to_string()]);
    assert_eq!(world.remaining_budget(), 2);

    // Log verifies both before reveal and after reveal.
    verify_observation_log(&world.log())?;
    let revealed = world.reveal(110)?;
    assert_eq!(revealed.model_name, "quadratic");

    let json = serde_json::to_string(&world.log()).unwrap();
    let restored: ObservationLog = serde_json::from_str(&json).unwrap();
    verify_observation_log(&restored)?;

    Ok(())
}

#[test]
fn sign_only_hides_diverging_gain_until_bounded_error_resolution_splits_candidates() -> Result<()> {
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let world_kp = Keypair::generate();

    // Chapter 119.5–119.6: e_n = (-a)^n * 1 for a = 1 vs a = 4.
    // Both alternate +1, -1, +1, -1 forever under SignOnly.
    // At step 1: -1 vs -4 (distance 3).
    //   coarse_radius_2: 2*2 = 4 >= 3 (cannot guarantee separation at step 1)
    //   fine_radius_1:   2*1 = 2 < 3  (guarantees separation at step 1!)
    let law = ObservationLaw {
        topic: "Separating persistent alternation from growing oscillation".into(),
        candidates: vec![
            CandidateModel {
                name: "unit_gain".into(),
                rule: ModelRule::AlternatingPower {
                    gain: 1,
                    initial: 1,
                },
            },
            CandidateModel {
                name: "diverging_gain".into(),
                rule: ModelRule::AlternatingPower {
                    gain: 4,
                    initial: 1,
                },
            },
        ],
        admitted_readouts: vec![
            ReadoutSpec {
                name: "sign".into(),
                kind: ReadoutKind::SignOnly,
                cost: 1,
            },
            ReadoutSpec {
                name: "coarse_r2".into(),
                kind: ReadoutKind::BoundedError { radius: 2 },
                cost: 2,
            },
            ReadoutSpec {
                name: "fine_r1".into(),
                kind: ReadoutKind::BoundedError { radius: 1 },
                cost: 3,
            },
        ],
        probe_budget: 10,
        input_min: 0,
        input_max: 4,
    };

    let mut world = ObservationWorld::open(law, 1, "salt-ch119-02", world_kp, &alice, 200)?;
    world.join(&bob, 201)?;

    // Four sign-only probes never separate the two models.
    for step in 0..=3 {
        let p = world.probe(&alice, step, "sign", 210 + step as u64)?;
        let expected_sign = if step % 2 == 0 { 1 } else { -1 };
        assert_eq!(p.reading, ProbeReading::Sign { sign: expected_sign });
    }
    assert_eq!(world.compatible_candidates()?.len(), 2);
    assert_eq!(world.remaining_budget(), 6);

    // Asking for a discriminating probe on step 1 skips sign (fails) and coarse_r2 (3 <= 4),
    // selecting fine_r1 (3 > 2).
    let suggestion =
        suggest_discriminating_probe(world.law(), &world.probes(), world.remaining_budget(), &[1])?
            .expect("fine_r1 should split candidates at step 1");
    assert_eq!(suggestion.readout_name, "fine_r1");
    assert_eq!(suggestion.input, 1);

    // Bob runs fine_r1 at step 1 with worst-case +1 error offset (true -4 reported as -3).
    let p_fine = world.probe_with_offset(&bob, 1, "fine_r1", 1, 220)?;
    assert_eq!(
        p_fine.reading,
        ProbeReading::Bounded {
            reported: -3,
            radius: 1
        }
    );
    // Even with +1 error, |-1 - (-3)| = 2 > 1 rules out unit_gain!
    assert_eq!(
        world.compatible_candidates()?,
        vec!["diverging_gain".to_string()]
    );

    world.reveal(230)?;
    verify_observation_log(&world.log())?;
    Ok(())
}

#[test]
fn budget_limits_dishonest_host_probes_and_swapped_secrets_are_refused() -> Result<()> {
    let alice = Keypair::generate();
    let world_kp = Keypair::generate();

    let law = ObservationLaw {
        topic: "Threshold check".into(),
        candidates: vec![
            CandidateModel {
                name: "cut_at_3".into(),
                rule: ModelRule::PiecewiseThreshold {
                    threshold: 3,
                    low_value: 0,
                    high_value: 10,
                },
            },
            CandidateModel {
                name: "cut_at_5".into(),
                rule: ModelRule::PiecewiseThreshold {
                    threshold: 5,
                    low_value: 0,
                    high_value: 10,
                },
            },
        ],
        admitted_readouts: vec![ReadoutSpec {
            name: "exact".into(),
            kind: ReadoutKind::Exact,
            cost: 2,
        }],
        probe_budget: 2,
        input_min: 0,
        input_max: 10,
    };

    let mut world = ObservationWorld::open(law, 0, "salt-honest", world_kp.clone(), &alice, 10)?;

    // Out-of-range input is refused.
    assert!(world.probe(&alice, 11, "exact", 11).is_err());

    // First probe uses the full budget (2); a second probe is refused.
    world.probe(&alice, 4, "exact", 12)?;
    assert_eq!(world.remaining_budget(), 0);
    assert!(world.probe(&alice, 2, "exact", 13).is_err());

    // Attack 1: Host attempts to swap to cut_at_5 at reveal time -> commitment mismatch!
    let mut bad_reveal_log = world.log();
    let prev = bad_reveal_log.records.last().unwrap().hash()?;
    let mut forged_reveal = SecretRevealed {
        world_id: world.world_id().clone(),
        seq: bad_reveal_log.records.len() as u64,
        prev,
        secret: HiddenSecret {
            model_index: 1,
            model_name: "cut_at_5".into(),
            rule: world.law().candidates[1].rule.clone(),
            salt: "salt-honest".into(),
        },
        ts: 20,
        proof: ProofOrArray::placeholder(),
    };
    let body = body_for_signing(&ObservationRecord::SecretRevealed(forged_reveal.clone()))?;
    forged_reveal.proof = ProofOrArray::single(Proof::create(&world_kp, &world_kp.sign(&body)));
    bad_reveal_log
        .records
        .push(ObservationRecord::SecretRevealed(forged_reveal));
    assert!(verify_observation_log(&bad_reveal_log).is_err());

    // Attack 2: Dishonest host reports a lying probe reading (0 instead of 10 at x = 4)
    // and then reveals the true committed secret cut_at_3 -> caught retroactively on reveal!
    let mut lying_log = ObservationLog {
        world_id: world.world_id().clone(),
        law: world.law().clone(),
        hidden_commitment: world.log().hidden_commitment,
        records: vec![world.log().records[0].clone()],
    };
    let seed_hash = lying_log.records[0].hash()?;
    let mut lying_probe = ProbeRecorded {
        world_id: world.world_id().clone(),
        seq: 1,
        prev: seed_hash,
        actor_id: alice.did(),
        input: 4,
        readout_name: "exact".into(),
        cost: 2,
        remaining_budget: 0,
        reading: ProbeReading::Exact { value: 0 }, // lie! cut_at_3 gives 10 at x = 4
        prediction_matched: None,
        ts: 12,
        proof: ProofOrArray::placeholder(),
    };
    let p_body = body_for_signing(&ObservationRecord::ProbeRecorded(lying_probe.clone()))?;
    lying_probe.proof = ProofOrArray::array(vec![
        Proof::create(&alice, &alice.sign(&p_body)),
        Proof::create(&world_kp, &world_kp.sign(&p_body)),
    ]);
    let probe_hash = ObservationRecord::ProbeRecorded(lying_probe.clone()).hash()?;
    lying_log
        .records
        .push(ObservationRecord::ProbeRecorded(lying_probe));

    // Before reveal, the lying probe is indistinguishable from an honest cut_at_5 world.
    verify_observation_log(&lying_log)?;

    // Once the committed secret (cut_at_3) is revealed, verification catches the lie!
    let mut true_reveal = SecretRevealed {
        world_id: world.world_id().clone(),
        seq: 2,
        prev: probe_hash,
        secret: HiddenSecret {
            model_index: 0,
            model_name: "cut_at_3".into(),
            rule: world.law().candidates[0].rule.clone(),
            salt: "salt-honest".into(),
        },
        ts: 25,
        proof: ProofOrArray::placeholder(),
    };
    let r_body = body_for_signing(&ObservationRecord::SecretRevealed(true_reveal.clone()))?;
    true_reveal.proof = ProofOrArray::single(Proof::create(&world_kp, &world_kp.sign(&r_body)));
    lying_log
        .records
        .push(ObservationRecord::SecretRevealed(true_reveal));
    assert!(verify_observation_log(&lying_log).is_err());

    // Attack 3: Unknown JSON field injected into ObservationLog is refused.
    let mut val = serde_json::to_value(&world.log()).unwrap();
    val["leaked_secret"] = serde_json::json!("cut_at_3");
    assert!(serde_json::from_value::<ObservationLog>(val).is_err());

    Ok(())
}
