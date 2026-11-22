use chat_world::error::Result;
use chat_world::hash::{body_for_signing, sha256_hex};
use chat_world::retelling::{
    verify_retelling_log, ComparisonDraft, ComparisonRecorded, Medium, MediumPolicy,
    RetellingDraft, RetellingLaw, RetellingLog, RetellingRecord, RetellingWorld, SeedDraft,
    SourceOrigin, TransformationAccount,
};
use chat_world::{Keypair, Proof, ProofOrArray};

#[test]
fn midday_retelling_chain_branching_comparison_and_bidirectional_lineage() -> Result<()> {
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let morning_transform_world = Keypair::generate().did();
    let world_kp = Keypair::generate();

    let law = RetellingLaw {
        topic: "Carry one small pattern across media and track what each choice adds".into(),
        medium_policy: MediumPolicy::Any,
        require_explicit_losses: true,
        allow_external_imports: true,
    };

    let mut world = RetellingWorld::open(law, world_kp, &alice, 100)?;
    world.join(&bob, 101)?;

    // 1. Import the morning visual pattern as the root seed.
    let seed_hash = world.add_seed(
        &alice,
        SeedDraft {
            node_id: "seed/morning-pattern".into(),
            origin: SourceOrigin::ImportedArtifact {
                source_world_id: morning_transform_world,
                artifact_hash: sha256_hex(b"morning-transform-sequence"),
                label: "Interrupted symmetry motif".into(),
            },
            medium: Medium::VisualPattern,
            title: "Morning Symmetry with One Interruption".into(),
            audience: "explorers".into(),
            content: "A B A C A -> interrupted repetition on step 4".into(),
        },
        110,
    )?;

    // 2. Bob retells the visual pattern as a MusicalScore.
    let score_hash = world.add_retelling(
        &bob,
        RetellingDraft {
            node_id: "retell/phrased-score".into(),
            parent_node_hashes: vec![seed_hash.clone()],
            medium: Medium::MusicalScore,
            title: "Two-Voice Phrased Score".into(),
            audience: "performers".into(),
            content: "Voice 1: D5-C5-D5-rest-D5 | Voice 2 answers on the rest.".into(),
            account: TransformationAccount {
                preserved: vec!["single structural interruption at beat 4".into()],
                changed: vec!["spatial repetition mapped to temporal rhythm".into()],
                hard_to_express: vec!["simultaneous visual symmetry across the whole grid".into()],
                added_by_interpreter: vec!["second answering voice entering on the pause".into()],
            },
        },
        120,
    )?;

    // 3. Branch A (Bob): retells the visual pattern directly into a ProseScene.
    let scene_hash = world.add_retelling(
        &bob,
        RetellingDraft {
            node_id: "retell/arrival-scene".into(),
            parent_node_hashes: vec![seed_hash.clone()],
            medium: Medium::ProseScene,
            title: "The Fourth Arrival".into(),
            audience: "storytellers".into(),
            content: "Three familiar guests greet in turn; a fourth enters and changes the rules.".into(),
            account: TransformationAccount {
                preserved: vec!["recurring baseline broken once".into()],
                changed: vec!["abstract motif translated into characters and arrival".into()],
                hard_to_express: vec!["exact reversible group symmetry".into()],
                added_by_interpreter: vec!["narrative tension around an unexpected arrival".into()],
            },
        },
        125,
    )?;

    // 4. Branch B (Alice): retells the MusicalScore into a RelationDiagram.
    let diagram_hash = world.add_retelling(
        &alice,
        RetellingDraft {
            node_id: "retell/mode-boundary-diagram".into(),
            parent_node_hashes: vec![score_hash.clone()],
            medium: Medium::RelationDiagram,
            title: "Boundary Between Two Modes".into(),
            audience: "analysts".into(),
            content: "[Mode I: Periodic] --(interruption)--> [Mode II: Responsive]".into(),
            account: TransformationAccount {
                preserved: vec!["the pause acting as a pivot between voices".into()],
                changed: vec!["performed duration collapsed into state-transition arrows".into()],
                hard_to_express: vec!["audible tension and tempo before the pause".into()],
                added_by_interpreter: vec!["explicit classification into two operating modes".into()],
            },
        },
        130,
    )?;

    // 5. Compare Branch A and Branch B while citing their shared root ancestor.
    let shared = world.shared_ancestors(&scene_hash, &diagram_hash)?;
    assert_eq!(shared, vec![seed_hash.clone()]);

    world.record_comparison(
        &alice,
        ComparisonDraft {
            left_node_hash: scene_hash.clone(),
            right_node_hash: diagram_hash.clone(),
            common_ancestor_hash: Some(seed_hash.clone()),
            shared_elements: vec!["both treat the fourth beat as a structural turning point".into()],
            divergences: vec![
                "scene treats interruption as an arrival of a new agent; diagram treats it as a mode boundary"
                    .into(),
            ],
        },
        135,
    )?;

    // 6. Multi-parent synthesis combining both branches into a mini-festival WorldTemplate.
    let festival_hash = world.add_retelling(
        &bob,
        RetellingDraft {
            node_id: "retell/evening-festival-script".into(),
            parent_node_hashes: vec![scene_hash.clone(), diagram_hash.clone()],
            medium: Medium::WorldTemplate,
            title: "Evening Mini-Festival Score & Stage".into(),
            audience: "visitors".into(),
            content: "Stage cycles Mode I until a visitor enters, triggering the answering voice.".into(),
            account: TransformationAccount {
                preserved: vec![
                    "narrative arrival from scene".into(),
                    "two-mode transition boundary from diagram".into(),
                ],
                changed: vec!["static text and diagram turned into interactive stage rules".into()],
                hard_to_express: vec!["fixed single authorial ending".into()],
                added_by_interpreter: vec!["open slot for a live visitor gesture".into()],
            },
        },
        140,
    )?;

    // 7. Leave an open invitation for later visitors.
    world.leave_invitation(
        &alice,
        vec![seed_hash.clone(), festival_hash.clone()],
        "Make another transformation of this motif, and say what you chose to preserve.",
        vec![Medium::Poem, Medium::Custom { name: "choreography".into() }],
        145,
    )?;

    // 8. Verify bidirectional lineage queries.
    let forward = world.descendants(&seed_hash)?;
    assert_eq!(forward.len(), 4);
    assert!(forward.contains(&score_hash));
    assert!(forward.contains(&scene_hash));
    assert!(forward.contains(&diagram_hash));
    assert!(forward.contains(&festival_hash));

    let trace = world.trace_attribution(&festival_hash)?;
    assert_eq!(trace.root_seeds.len(), 1);
    assert_eq!(trace.root_seeds[0].node_id, "seed/morning-pattern");
    assert_eq!(trace.transformation_steps.len(), 4);
    assert_eq!(
        trace.transformation_steps.last().unwrap().node_id,
        "retell/evening-festival-script"
    );

    // 9. JSON round-trip and offline verification.
    let json = serde_json::to_string(&world.log()).unwrap();
    let restored: RetellingLog = serde_json::from_str(&json).unwrap();
    verify_retelling_log(&restored)?;

    Ok(())
}

#[test]
fn law_constraints_fake_ancestor_and_log_forgeries_are_refused() -> Result<()> {
    let alice = Keypair::generate();
    let world_kp = Keypair::generate();

    let law = RetellingLaw {
        topic: "Text-only strict retelling workshop".into(),
        medium_policy: MediumPolicy::Restricted {
            allowed: vec![Medium::Poem, Medium::ProseScene],
        },
        require_explicit_losses: true,
        allow_external_imports: false,
    };

    let mut world = RetellingWorld::open(law, world_kp.clone(), &alice, 10)?;

    // External import blocked by law.
    assert!(world
        .add_seed(
            &alice,
            SeedDraft {
                node_id: "seed/ext".into(),
                origin: SourceOrigin::ImportedArtifact {
                    source_world_id: Keypair::generate().did(),
                    artifact_hash: sha256_hex(b"ext"),
                    label: "external".into(),
                },
                medium: Medium::Poem,
                title: "Imported".into(),
                audience: "all".into(),
                content: "Line one".into(),
            },
            11,
        )
        .is_err());

    // Disallowed medium blocked by law.
    assert!(world
        .add_seed(
            &alice,
            SeedDraft {
                node_id: "seed/score".into(),
                origin: SourceOrigin::NativeSeed,
                medium: Medium::MusicalScore,
                title: "Score".into(),
                audience: "all".into(),
                content: "C4 D4 E4".into(),
            },
            12,
        )
        .is_err());

    // Two unrelated native seeds.
    let s1 = world.add_seed(
        &alice,
        SeedDraft {
            node_id: "seed/one".into(),
            origin: SourceOrigin::NativeSeed,
            medium: Medium::Poem,
            title: "First Poem".into(),
            audience: "all".into(),
            content: "Two roads in quiet rain.".into(),
        },
        13,
    )?;
    let s2 = world.add_seed(
        &alice,
        SeedDraft {
            node_id: "seed/two".into(),
            origin: SourceOrigin::NativeSeed,
            medium: Medium::ProseScene,
            title: "Unrelated Scene".into(),
            audience: "all".into(),
            content: "A clock stops at noon.".into(),
        },
        14,
    )?;

    // Duplicate node_id refused.
    assert!(world
        .add_seed(
            &alice,
            SeedDraft {
                node_id: "seed/one".into(),
                origin: SourceOrigin::NativeSeed,
                medium: Medium::Poem,
                title: "Duplicate".into(),
                audience: "all".into(),
                content: "Another poem.".into(),
            },
            15,
        )
        .is_err());

    // Empty hard_to_express refused when require_explicit_losses = true.
    assert!(world
        .add_retelling(
            &alice,
            RetellingDraft {
                node_id: "retell/lossless-claim".into(),
                parent_node_hashes: vec![s1.clone()],
                medium: Medium::ProseScene,
                title: "Claimed Lossless".into(),
                audience: "all".into(),
                content: "He stood in the rain where the road split.".into(),
                account: TransformationAccount {
                    preserved: vec!["rain and split road".into()],
                    changed: vec!["verse to prose".into()],
                    hard_to_express: vec![],
                    added_by_interpreter: vec!["named traveler".into()],
                },
            },
            16,
        )
        .is_err());

    // Live check refuses a comparison claiming s1 is a common ancestor of s1 and unrelated s2.
    assert!(world
        .record_comparison(
            &alice,
            ComparisonDraft {
                left_node_hash: s1.clone(),
                right_node_hash: s2.clone(),
                common_ancestor_hash: Some(s1.clone()),
                shared_elements: vec!["short length".into()],
                divergences: vec!["unrelated topics".into()],
            },
            17,
        )
        .is_err());

    // Forgery 1: properly dual-signed ComparisonRecorded with false common_ancestor_hash -> refused!
    let mut forged_anc_log = world.log();
    let prev = forged_anc_log.records.last().unwrap().hash()?;
    let mut bad_cmp = ComparisonRecorded {
        world_id: world.world_id().clone(),
        seq: forged_anc_log.records.len() as u64,
        prev,
        left_node_hash: s1.clone(),
        right_node_hash: s2.clone(),
        common_ancestor_hash: Some(s1),
        shared_elements: vec!["short".into()],
        divergences: vec!["unrelated".into()],
        author_id: alice.did(),
        ts: 18,
        proof: ProofOrArray::placeholder(),
    };
    let body = body_for_signing(&RetellingRecord::ComparisonRecorded(bad_cmp.clone()))?;
    bad_cmp.proof = ProofOrArray::array(vec![
        Proof::create(&alice, &alice.sign(&body)),
        Proof::create(&world_kp, &world_kp.sign(&body)),
    ]);
    forged_anc_log
        .records
        .push(RetellingRecord::ComparisonRecorded(bad_cmp));
    assert!(verify_retelling_log(&forged_anc_log).is_err());

    // Forgery 2: tamper with seed content in log -> refused!
    let mut tampered = world.log();
    if let RetellingRecord::SeedAdded(s) = &mut tampered.records[1] {
        s.content = "Altered poem text.".into();
    }
    assert!(verify_retelling_log(&tampered).is_err());

    // Forgery 3: unknown JSON field injected into RetellingLog -> refused!
    let mut val = serde_json::to_value(&world.log()).unwrap();
    val["hidden_rating"] = serde_json::json!(5);
    assert!(serde_json::from_value::<RetellingLog>(val).is_err());

    Ok(())
}
