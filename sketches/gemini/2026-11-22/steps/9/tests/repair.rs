use chat_world::error::Result;
use chat_world::hash::body_for_signing;
use chat_world::repair::{
    apply_adjustment, simulate, verify_repair_log, Adjustment, AdjustmentCommitted, GateSpec,
    LinkSpec, MechanismConfig, RepairLaw, RepairLog, RepairRecord, RepairTestCase, RepairWorld,
    StationRole, StationView,
};
use chat_world::{Keypair, Proof, ProofOrArray};

fn sample_repair_law() -> RepairLaw {
    // Source -> Relay (link_a: 4, min 3) -> Sink (link_b: 6, min 5)
    // Relay gate: [2..=5] (max_close 5)
    // Sink gate:  [5..=8] (max_close 9)
    // Declared suite: input_time 0 and input_time 1, both must deliver by t <= 12.
    // Neither station can pass both cases alone under its physical limits!
    RepairLaw {
        topic: "Restore pulse delivery across relay and sink gates".into(),
        initial_config: MechanismConfig {
            source_node: "source".into(),
            sink_node: "sink".into(),
            links: vec![
                LinkSpec {
                    link_id: "link_a".into(),
                    from: "source".into(),
                    to: "relay".into(),
                    delay: 4,
                    min_delay: 3,
                    max_delay: 10,
                    enabled: true,
                },
                LinkSpec {
                    link_id: "link_b".into(),
                    from: "relay".into(),
                    to: "sink".into(),
                    delay: 6,
                    min_delay: 5,
                    max_delay: 10,
                    enabled: true,
                },
            ],
            gates: vec![
                GateSpec {
                    gate_id: "relay".into(),
                    open_at: 2,
                    close_at: 5,
                    max_close_at: 5,
                },
                GateSpec {
                    gate_id: "sink".into(),
                    open_at: 5,
                    close_at: 8,
                    max_close_at: 9,
                },
            ],
        },
        declared_suite: vec![
            RepairTestCase {
                name: "nominal_pulse".into(),
                input_time: 0,
                max_delivery_time: 12,
            },
            RepairTestCase {
                name: "shifted_pulse".into(),
                input_time: 1,
                max_delivery_time: 12,
            },
        ],
        horizon: 15,
        material_budget: 4,
        max_trials: 4,
    }
}

#[test]
fn cooperative_two_station_diagnosis_trial_branches_swap_and_honest_report() -> Result<()> {
    let alice = Keypair::generate();
    let bob = Keypair::generate();
    let world_kp = Keypair::generate();

    let mut world = RepairWorld::open(sample_repair_law(), world_kp, &alice, 100)?;
    world.join(&bob, 101)?;

    // 1. Alice takes RoutingStation; Bob takes TimingStation.
    world.assign_station(&alice, StationRole::RoutingStation, 102)?;
    world.assign_station(&bob, StationRole::TimingStation, 103)?;

    // 2. Asymmetric partial views on input_time = 0:
    //    Alice sees links delivering a pulse to `sink` at t = 10, with no gate info.
    //    Bob sees `gate_sink` closing at t = 8 before the pulse arrives at t = 10, with no link info.
    let alice_view = world.inspect_station(&alice.did(), 0)?;
    let bob_view = world.inspect_station(&bob.did(), 0)?;

    let alice_json = serde_json::to_string(&alice_view).unwrap();
    let bob_json = serde_json::to_string(&bob_view).unwrap();
    assert!(!alice_json.contains("open_at"));
    assert!(!alice_json.contains("close_at"));
    assert!(!bob_json.contains("link_a"));
    assert!(!bob_json.contains("link_b"));

    match alice_view {
        StationView::Routing {
            link_events,
            delivered_at,
            ..
        } => {
            assert_eq!(delivered_at, None);
            assert_eq!(link_events.last().unwrap().arrived_at, 10);
        }
        _ => panic!("expected Routing view"),
    }
    match bob_view {
        StationView::Timing {
            gate_events,
            delivered_at,
            ..
        } => {
            assert_eq!(delivered_at, None);
            let sink_ev = gate_events.iter().find(|g| g.gate_id == "sink").unwrap();
            assert_eq!(sink_ev.arrival_time, 10);
            assert_eq!(sink_ev.close_at, 8);
            assert!(!sink_ev.passed);
        }
        _ => panic!("expected Timing view"),
    }

    // 3. Trial 1 (Routing adjustments alone): improves nominal_pulse (passes at t = 8),
    //    but shifted_pulse still arrives at t = 9 and fails [5..=8]!
    let trial1 = world.test_trial_branch(
        &alice,
        "trial-routing-only",
        vec![
            Adjustment::SetLinkDelay {
                link_id: "link_a".into(),
                new_delay: 3,
            },
            Adjustment::SetLinkDelay {
                link_id: "link_b".into(),
                new_delay: 5,
            },
        ],
        110,
    )?;
    assert!(!trial1.all_passed);
    assert!(trial1.cases[0].passed); // nominal_pulse passes
    assert!(!trial1.cases[1].passed); // shifted_pulse still fails
    // Trial branch did not mutate live_config or spend material.
    assert_eq!(world.remaining_material(), 4);
    assert_eq!(world.remaining_trials(), 3);

    // 4. Trial 2 (Timing adjustment alone): still fails both cases.
    let trial2 = world.test_trial_branch(
        &bob,
        "trial-timing-only",
        vec![Adjustment::SetGateWindow {
            gate_id: "sink".into(),
            open_at: 5,
            close_at: 9,
        }],
        112,
    )?;
    assert!(!trial2.all_passed);
    assert!(!trial2.cases[0].passed);
    assert!(!trial2.cases[1].passed);

    // 5. Trial 3 (Coordinated cross-station repair): passes full declared suite!
    let trial3 = world.test_trial_branch(
        &alice,
        "trial-coordinated",
        vec![
            Adjustment::SetLinkDelay {
                link_id: "link_a".into(),
                new_delay: 3,
            },
            Adjustment::SetLinkDelay {
                link_id: "link_b".into(),
                new_delay: 5,
            },
            Adjustment::SetGateWindow {
                gate_id: "sink".into(),
                open_at: 5,
                close_at: 9,
            },
        ],
        115,
    )?;
    assert!(trial3.all_passed);

    // 6. Each collaborator commits the adjustments owned by their own station.
    //    Alice cannot commit Bob's gate change from RoutingStation.
    assert!(world
        .commit_adjustment(
            &alice,
            Adjustment::SetGateWindow {
                gate_id: "sink".into(),
                open_at: 5,
                close_at: 9,
            },
            118,
        )
        .is_err());

    world.commit_adjustment(
        &alice,
        Adjustment::SetLinkDelay {
            link_id: "link_a".into(),
            new_delay: 3,
        },
        120,
    )?;
    world.commit_adjustment(
        &alice,
        Adjustment::SetLinkDelay {
            link_id: "link_b".into(),
            new_delay: 5,
        },
        121,
    )?;
    world.commit_adjustment(
        &bob,
        Adjustment::SetGateWindow {
            gate_id: "sink".into(),
            open_at: 5,
            close_at: 9,
        },
        122,
    )?;
    assert_eq!(world.remaining_material(), 1);

    // 7. Run official check suite on live_config -> passes!
    let live_suite = world.run_check_suite(&bob, 125)?;
    assert!(live_suite.all_passed);

    // 8. Check an untested case outside declared_suite: input_time = 2 still misses sink gate (t = 10 > 9).
    let untested = simulate(world.live_config(), 2, world.law().horizon);
    assert_eq!(untested.delivered_at, None);

    // 9. Swap stations so Alice inspects Bob's Timing view and Bob inspects Alice's Routing view.
    world.assign_station(&alice, StationRole::TimingStation, 130)?;
    world.assign_station(&bob, StationRole::RoutingStation, 131)?;
    assert!(matches!(
        world.inspect_station(&alice.did(), 0)?,
        StationView::Timing {
            delivered_at: Some(8),
            ..
        }
    ));
    assert!(matches!(
        world.inspect_station(&bob.did(), 1)?,
        StationView::Routing {
            delivered_at: Some(9),
            ..
        }
    ));

    // 10. Export honest RepairReport noting the unresolved edge case and collaborative lesson.
    let report = world.export_report(
        &alice,
        vec!["input_time=2 still arrives at sink at t=10 after gate_sink closes at t=9".into()],
        "When collaborators disagree, examine how their station observations differ.".into(),
        140,
    )?;
    assert!(report.checked_suite.all_passed);
    assert_eq!(report.committed_adjustments.len(), 3);
    assert_eq!(report.unresolved_cases.len(), 1);

    // Round-trip RepairLog through JSON and verify offline.
    let json = serde_json::to_string(&world.log()).unwrap();
    let restored: RepairLog = serde_json::from_str(&json).unwrap();
    verify_repair_log(&restored)?;

    Ok(())
}

#[test]
fn physical_bounds_material_budget_and_log_forgeries_are_refused() -> Result<()> {
    let alice = Keypair::generate();
    let world_kp = Keypair::generate();
    let mut law = sample_repair_law();
    law.material_budget = 1;
    law.max_trials = 1;

    let mut world = RepairWorld::open(law, world_kp.clone(), &alice, 10)?;
    world.assign_station(&alice, StationRole::RoutingStation, 11)?;

    // Physical lower bound violation: link_b min_delay is 5, so setting 4 is refused.
    assert!(world
        .commit_adjustment(
            &alice,
            Adjustment::SetLinkDelay {
                link_id: "link_b".into(),
                new_delay: 4,
            },
            12,
        )
        .is_err());

    // Spending the single material unit succeeds; a second commit is refused.
    world.commit_adjustment(
        &alice,
        Adjustment::SetLinkDelay {
            link_id: "link_a".into(),
            new_delay: 3,
        },
        13,
    )?;
    assert!(world
        .commit_adjustment(
            &alice,
            Adjustment::SetLinkDelay {
                link_id: "link_b".into(),
                new_delay: 5,
            },
            14,
        )
        .is_err());

    // Forgery 1: tamper with a trial branch's suite_result to claim all_passed = true.
    world.test_trial_branch(
        &alice,
        "honest-failing-trial",
        vec![Adjustment::SetLinkDelay {
            link_id: "link_b".into(),
            new_delay: 5,
        }],
        15,
    )?;
    let mut forged_trial = world.log();
    if let RepairRecord::TrialBranchTested(t) = forged_trial.records.last_mut().unwrap() {
        t.suite_result.all_passed = true;
    }
    assert!(verify_repair_log(&forged_trial).is_err());

    // Forgery 2: properly dual-sign a station-unauthorized commit in the log -> refused.
    let mut forged_commit_log = world.log();
    let prev = forged_commit_log.records.last().unwrap().hash()?;
    let illegal_adj = Adjustment::SetGateWindow {
        gate_id: "sink".into(),
        open_at: 5,
        close_at: 9,
    };
    let next_cfg = apply_adjustment(world.live_config(), &illegal_adj)?;
    let mut forged_rec = AdjustmentCommitted {
        world_id: world.world_id().clone(),
        seq: forged_commit_log.records.len() as u64,
        prev,
        actor_id: alice.did(),
        station: StationRole::RoutingStation, // wrong station for SetGateWindow!
        adjustment: illegal_adj,
        remaining_material: 0,
        config_hash: next_cfg.hash()?,
        ts: 20,
        proof: ProofOrArray::placeholder(),
    };
    let body = body_for_signing(&RepairRecord::AdjustmentCommitted(forged_rec.clone()))?;
    forged_rec.proof = ProofOrArray::array(vec![
        Proof::create(&alice, &alice.sign(&body)),
        Proof::create(&world_kp, &world_kp.sign(&body)),
    ]);
    forged_commit_log
        .records
        .push(RepairRecord::AdjustmentCommitted(forged_rec));
    assert!(verify_repair_log(&forged_commit_log).is_err());

    // Forgery 3: unknown JSON field injected into RepairLog is rejected.
    let mut val = serde_json::to_value(&world.log()).unwrap();
    val["hidden_answer"] = serde_json::json!("link_a=3");
    assert!(serde_json::from_value::<RepairLog>(val).is_err());

    Ok(())
}
