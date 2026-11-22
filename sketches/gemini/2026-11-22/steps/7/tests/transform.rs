use chat_world::error::Result;
use chat_world::hash::body_for_signing;
use chat_world::transform::{
    apply_sequence, evaluate_claim, invert_sequence, partition_orbits, shortest_path,
    verify_transform_log, HexWord, InvariantClaim, MoveApplied, Op, TransformLaw, TransformLog,
    TransformRecord, TransformationWorld,
};
use chat_world::{Keypair, Proof, ProofOrArray};

#[test]
fn chapter_26_hexagram_operations_noncommutativity_and_exact_orbit_counts() -> Result<()> {
    // Section 26.2 worked word: 101100
    let x = HexWord::parse("101100")?;
    assert_eq!(Op::Complement.apply(x).as_bit_string(), "010011");
    assert_eq!(Op::Reverse.apply(x).as_bit_string(), "001101");
    assert_eq!(Op::SwapTrigrams.apply(x).as_bit_string(), "100101");
    assert_eq!(Op::Rotate.apply(x).as_bit_string(), "010110");
    assert_eq!(
        apply_sequence(x, &[Op::Reverse, Op::Complement]).as_bit_string(),
        "110010"
    );
    assert_eq!(
        apply_sequence(x, &[Op::SwapTrigrams, Op::Complement]).as_bit_string(),
        "011010"
    );

    // Section 26.3: R and T fail to commute on 100000, and R T R = T^-1, S = T^3.
    let single_one = HexWord::parse("100000")?;
    assert_eq!(
        apply_sequence(single_one, &[Op::Rotate, Op::Reverse]).as_bit_string(),
        "000010"
    );
    assert_eq!(
        apply_sequence(single_one, &[Op::Reverse, Op::Rotate]).as_bit_string(),
        "100000"
    );
    for w in HexWord::all() {
        assert_eq!(
            apply_sequence(w, &[Op::Reverse, Op::Rotate, Op::Reverse]),
            Op::RotateInverse.apply(w)
        );
        assert_eq!(
            apply_sequence(w, &[Op::Rotate, Op::Rotate, Op::Rotate]),
            Op::SwapTrigrams.apply(w)
        );
    }

    // Section 26.6–26.9: Exact orbit partitions across all 64 words.
    let c6_orbits = partition_orbits(&[Op::Rotate]);
    assert_eq!(c6_orbits.len(), 14);

    let k_orbits = partition_orbits(&[Op::Complement, Op::Reverse, Op::SwapTrigrams]);
    assert_eq!(k_orbits.len(), 14);

    let g_orbits = partition_orbits(&[Op::Complement, Op::Reverse, Op::Rotate]);
    assert_eq!(g_orbits.len(), 8);
    let reps_and_sizes: Vec<(String, usize)> = g_orbits
        .iter()
        .map(|orb| (orb.iter().next().unwrap().as_bit_string(), orb.len()))
        .collect();
    assert_eq!(
        reps_and_sizes,
        vec![
            ("000000".into(), 2),
            ("000001".into(), 12),
            ("000011".into(), 12),
            ("000101".into(), 12),
            ("000111".into(), 6),
            ("001001".into(), 6),
            ("001011".into(), 12),
            ("010101".into(), 2),
        ]
    );

    // Section 26.10: Weight pair {n(x), 6 - n(x)} is invariant under G,
    // yet does NOT classify G-orbits (counterexample: 000011 vs 000101).
    let g_ops = [Op::Complement, Op::Reverse, Op::Rotate, Op::RotateInverse];
    assert!(evaluate_claim(&InvariantClaim::PreservesWeightPair { op: Op::Complement }, &g_ops).holds);
    assert!(
        evaluate_claim(
            &InvariantClaim::PreservesHammingDistance { op: Op::Complement },
            &g_ops
        )
        .holds
    );
    let classify = evaluate_claim(&InvariantClaim::WeightPairClassifiesOrbits, &g_ops);
    assert!(!classify.holds);
    assert!(classify.witness.contains("000011"));
    assert!(classify.witness.contains("000101"));

    Ok(())
}

#[test]
fn collaborative_transformation_session_undo_conjectures_and_portable_challenge() -> Result<()> {
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let world_kp = Keypair::generate();

    let start = HexWord::parse("101100")?;
    let target = HexWord::parse("001101")?;
    let law = TransformLaw {
        topic: "What can change while remaining in the same orbit?".into(),
        admitted_ops: vec![
            Op::Complement,
            Op::Reverse,
            Op::Rotate,
            Op::RotateInverse,
        ],
        initial_word: start,
        target_word: Some(target),
    };

    let mut world = TransformationWorld::open(law, world_kp, &alice, 100)?;
    world.join(&bob, 101)?;

    // Alice applies Rotate, then Bob applies Complement -> non-trivial sequence.
    world.apply_move(&alice, Op::Rotate, Some("shift positions once".into()), 110)?;
    world.apply_move(&bob, Op::Complement, Some("flip every line".into()), 112)?;
    assert_eq!(world.current_word(), HexWord::parse("101001")?);

    // Bob undoes both steps in exact reverse order: (C ∘ T)^-1 = T^-1 ∘ C.
    world.undo_last(&bob, 2, 115)?;
    assert_eq!(world.current_word(), start);

    // Alice tests a conjecture that fails (000011 vs 000101 are NOT in the same G-orbit).
    let eval_false = world.check_claim(
        &alice,
        InvariantClaim::SameOrbit {
            a: HexWord::parse("000011")?,
            b: HexWord::parse("000101")?,
        },
        120,
    )?;
    assert!(!eval_false.holds);

    // Bob applies Reverse to reach the world's target word and leaves a portable challenge.
    world.apply_move(&bob, Op::Reverse, Some("reach target".into()), 125)?;
    assert!(world.target_reached());

    let artifact = world.leave_challenge(
        &alice,
        "Find another sequence reaching 001101 without using Reverse directly.",
        130,
    )?;
    assert_eq!(artifact.start_word, start);
    assert_eq!(artifact.end_word, target);
    assert_eq!(apply_sequence(artifact.start_word, &artifact.sequence), target);

    // Round-trip the entire TransformLog through JSON and verify offline.
    let json = serde_json::to_string(&world.log()).unwrap();
    let restored: TransformLog = serde_json::from_str(&json).unwrap();
    verify_transform_log(&restored)?;

    Ok(())
}

#[test]
fn mathematical_inverse_without_admitted_action_is_refused_and_forgeries_fail() -> Result<()> {
    let alice = Keypair::generate();
    let world_kp = Keypair::generate();

    // A world that admits ONLY forward Rotate (not RotateInverse).
    let start = HexWord::parse("100000")?;
    let law = TransformLaw {
        topic: "Forward rotation only".into(),
        admitted_ops: vec![Op::Rotate],
        initial_word: start,
        target_word: None,
    };

    let mut world = TransformationWorld::open(law, world_kp.clone(), &alice, 10)?;
    world.apply_move(&alice, Op::Rotate, None, 11)?;
    assert_eq!(world.current_word(), HexWord::parse("010000")?);

    // Chapter 21.8: Rotate has a mathematical inverse (RotateInverse),
    // but this world's law does not admit it -> undo_last must refuse!
    assert!(world.undo_last(&alice, 1, 12).is_err());

    // Yet returning to start is still reachable in 5 forward rotations.
    let return_path = shortest_path(world.current_word(), start, &world.law().admitted_ops).unwrap();
    assert_eq!(return_path.len(), 5);
    assert_eq!(invert_sequence(&[Op::Rotate]), vec![Op::RotateInverse]);

    // Forgery 1: tamper with a move's next_word in the log -> refused.
    let mut bad_next = world.log();
    if let TransformRecord::MoveApplied(m) = &mut bad_next.records[1] {
        m.next_word = HexWord::parse("111111")?;
    }
    assert!(verify_transform_log(&bad_next).is_err());

    // Forgery 2: properly dual-sign a disallowed Complement move -> refused by law check.
    let mut bad_op_log = world.log();
    let prev = bad_op_log.records.last().unwrap().hash()?;
    let cur = world.current_word();
    let mut illegal = MoveApplied {
        world_id: world.world_id().clone(),
        seq: bad_op_log.records.len() as u64,
        prev,
        actor_id: alice.did(),
        op: Op::Complement,
        prev_word: cur,
        next_word: Op::Complement.apply(cur),
        note: None,
        ts: 20,
        proof: ProofOrArray::placeholder(),
    };
    let body = body_for_signing(&TransformRecord::MoveApplied(illegal.clone()))?;
    illegal.proof = ProofOrArray::array(vec![
        Proof::create(&alice, &alice.sign(&body)),
        Proof::create(&world_kp, &world_kp.sign(&body)),
    ]);
    bad_op_log.records.push(TransformRecord::MoveApplied(illegal));
    assert!(verify_transform_log(&bad_op_log).is_err());

    // Forgery 3: invalid HexWord in JSON is rejected on deserialization.
    let mut val = serde_json::to_value(&world.log()).unwrap();
    val["law"]["initial_word"] = serde_json::json!("102000");
    assert!(serde_json::from_value::<TransformLog>(val).is_err());

    Ok(())
}
