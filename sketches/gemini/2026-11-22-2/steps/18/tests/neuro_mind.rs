use chat_world::error::Result;
use chat_world::neuro::{
    Channel, DelayMode, NeuralCluster, PlasticityRule, SynapseSpec, TriSignal, UnitKind, UnitSpec,
};
use chat_world::neuro_mind::{
    verify_mind_session, ActionProposal, AdaptiveArenaWorld, ArenaStepSpec, Mind, MindAction,
    MindBindings, MindSession, NeuroMind, PluginRequest, PluginResponse,
};
use chat_world::Keypair;
use std::collections::BTreeMap;

fn build_six_archetype_mind(mind_kp: Keypair, cluster_kp: Keypair) -> Result<NeuroMind> {
    let units = vec![
        UnitSpec {
            id: "rec_red".into(),
            kind: UnitKind::ReceptorBroadcast {
                affinity: [1000, 0, 0],
                sigma: 160,
                g0: 15,
                threshold: 450,
                emit_channel: Channel::Red,
            },
        },
        UnitSpec {
            id: "rec_blue".into(),
            kind: UnitKind::ReceptorBroadcast {
                affinity: [0, 1000, 0],
                sigma: 160,
                g0: 15,
                threshold: 450,
                emit_channel: Channel::Blue,
            },
        },
        UnitSpec {
            id: "rec_purple".into(),
            kind: UnitKind::ReceptorBroadcast {
                affinity: [500, 500, 0],
                sigma: 160,
                g0: 15,
                threshold: 450,
                emit_channel: Channel::Red,
            },
        },
        UnitSpec {
            id: "rec_orange".into(),
            kind: UnitKind::ReceptorBroadcast {
                affinity: [500, 0, 500],
                sigma: 160,
                g0: 15,
                threshold: 450,
                emit_channel: Channel::Red,
            },
        },
        UnitSpec {
            id: "rec_green".into(),
            kind: UnitKind::ReceptorBroadcast {
                affinity: [0, 500, 500],
                sigma: 160,
                g0: 15,
                threshold: 450,
                emit_channel: Channel::Red,
            },
        },
        // 2 micro-ticks per world tick: world lag 2 -> 4 micro-ticks; lags 3 & 5 -> 6 & 10 micro-ticks.
        UnitSpec {
            id: "jeffress".into(),
            kind: UnitKind::DelayLine {
                max_lag: 6,
                mode: DelayMode::Coincidence {
                    lag_a: 4,
                    lag_b: 0,
                    threshold: 600,
                },
            },
        },
        UnitSpec {
            id: "purkinje".into(),
            kind: UnitKind::DelayLine {
                max_lag: 12,
                mode: DelayMode::PurkinjeCancel {
                    lr_fast: 850,
                    decay_quiet: 995,
                    decay_error: 880,
                    error_threshold: 250,
                    tap_cap: 1500,
                    base_taps: vec![0; 12],
                },
            },
        },
        UnitSpec {
            id: "pyr".into(),
            kind: UnitKind::Pyramidal {
                leak_g0: 1000,
                threshold: 300,
                apical_threshold: 500,
                coincidence_boost: 500,
                yellow_decay: 0,
            },
        },
        UnitSpec {
            id: "mod_nuc".into(),
            kind: UnitKind::ModulatorNucleus {
                tonic_decay: 850,
                red_trigger_gain: 0,
                threshold: 200,
            },
        },
        UnitSpec {
            id: "shunt_inh".into(),
            kind: UnitKind::ShuntingInterneuron {
                threshold: 100,
                blue_gain: 350,
            },
        },
        UnitSpec {
            id: "act_0".into(),
            kind: UnitKind::TriChannel {
                leak_g0: 1000,
                threshold: 100,
                yellow_decay: 0,
                blue_gain: 0,
                yellow_gain: 0,
            },
        },
        UnitSpec {
            id: "act_1".into(),
            kind: UnitKind::TriChannel {
                leak_g0: 1000,
                threshold: 100,
                yellow_decay: 0,
                blue_gain: 0,
                yellow_gain: 0,
            },
        },
    ];

    let delta_syn = |from: &str, to: &str, base_r: i64| SynapseSpec {
        from: from.into(),
        to: to.into(),
        base_red: base_r,
        base_blue: 0,
        base_yellow: 0,
        decay_min: 1000,
        decay_max: 1000,
        write_deadzone: 500,
        learning_rate: 1200,
        consolidation_rate: 0,
        consolidation_threshold: 1500,
        fast_cap: 1500,
        plasticity: PlasticityRule::Delta,
    };

    let synapses = vec![
        SynapseSpec::static_channel("rec_red", "jeffress", 1000, 0, 0),
        SynapseSpec::static_channel("rec_blue", "jeffress", 0, 1000, 0),
        SynapseSpec::static_channel("rec_green", "purkinje", 1000, 0, 0),
        SynapseSpec::static_channel("pyr", "mod_nuc", 0, 0, 1000),
        SynapseSpec::static_channel("mod_nuc", "act_0", 0, 0, 400),
        SynapseSpec::static_channel("mod_nuc", "act_1", 0, 0, 400),
        // Baseline habits (Rule A): Purple -> act_0, Orange -> act_1
        delta_syn("rec_purple", "act_0", 1000),
        delta_syn("rec_purple", "act_1", 0),
        delta_syn("rec_orange", "act_0", 0),
        delta_syn("rec_orange", "act_1", 1000),
        SynapseSpec::static_channel("act_0", "shunt_inh", 1000, 0, 0),
        SynapseSpec::static_channel("act_1", "shunt_inh", 1000, 0, 0),
        SynapseSpec::static_channel("shunt_inh", "act_0", 0, 1000, 0),
        SynapseSpec::static_channel("shunt_inh", "act_1", 0, 1000, 0),
    ];

    let cluster = NeuralCluster::new("arena-micro-brain", cluster_kp, units, synapses)?;
    let bindings = MindBindings {
        sensory_receptors: vec![
            "rec_red".into(),
            "rec_blue".into(),
            "rec_purple".into(),
            "rec_orange".into(),
            "rec_green".into(),
        ],
        action_units: BTreeMap::from([
            ("act_0".into(), "act_0".into()),
            ("act_1".into(), "act_1".into()),
        ]),
        purkinje_unit: Some("purkinje".into()),
        coincidence_unit: Some("jeffress".into()),
        pyramidal_unit: Some("pyr".into()),
        modulator_unit: Some("mod_nuc".into()),
        action_threshold: 1,
        teaching_drive: 1000,
        surprise_yellow: 1000,
    };

    NeuroMind::new(mind_kp, cluster, bindings)
}

fn build_90_tick_arena_schedule() -> Vec<ArenaStepSpec> {
    let mut hues = vec!["quiet"; 90];
    let mut scales = vec![1000i64; 90];
    let mut shocks = vec![0i64; 90];

    for tc in [2usize, 10, 18] {
        hues[tc] = "green";
        shocks[tc + 3] = 1000;
    }
    for tc in [32usize, 40, 48] {
        hues[tc] = "green";
        shocks[tc + 5] = 1000;
    }
    for tc in [62usize, 70, 78] {
        hues[tc] = "green";
        shocks[tc + 3] = 1000;
    }

    // Target order event: Red (t=6) -> 2 ticks -> 5x bright Blue (t=8).
    // Reversed distractor: Blue (t=14) -> 2 ticks -> Red (t=16).
    hues[6] = "red";
    hues[8] = "blue";
    scales[8] = 5000;
    hues[14] = "blue";
    hues[16] = "red";

    for t in 0..90 {
        if hues[t] == "quiet" && t % 2 == 1 {
            hues[t] = if (t / 2) % 2 == 0 { "purple" } else { "orange" };
            scales[t] = [50, 1000, 20_000][t % 3]; // 400x intensity swing!
        }
    }

    let hue_field = |h: &str, sc: i64| match h {
        "red" => TriSignal::raw(sc, 0, 0),
        "blue" => TriSignal::raw(0, sc, 0),
        "purple" => TriSignal::raw(sc / 2, sc / 2, 0),
        "orange" => TriSignal::raw(sc / 2, 0, sc / 2),
        "green" => TriSignal::raw(0, sc / 2, sc / 2),
        _ => TriSignal::default(),
    };

    (0..90)
        .map(|t| {
            let rule_b = (30..60).contains(&t);
            let teaching_action = match hues[t] {
                "purple" => Some(if rule_b { "act_1" } else { "act_0" }.to_string()),
                "orange" => Some(if rule_b { "act_0" } else { "act_1" }.to_string()),
                _ => None,
            };
            ArenaStepSpec {
                sensory_field: hue_field(hues[t], scales[t]),
                available_actions: vec!["act_0".into(), "act_1".into()],
                teaching_action,
                shock: shocks[t],
                attention_cue: 0,
            }
        })
        .collect()
}

#[test]
fn closed_loop_neuro_mind_adapts_across_rule_flips_lag_shifts_400x_scales_and_verifies_offline()
-> Result<()> {
    let mut world = AdaptiveArenaWorld::new(Keypair::generate(), build_90_tick_arena_schedule())?;
    let mut mind = build_six_archetype_mind(Keypair::generate(), Keypair::generate())?;

    let mut phase_correct = [0usize; 3];
    let mut phase_total = [0usize; 3];
    let mut order_alert_ticks = Vec::new();
    let mut shock_braces = Vec::new();

    while !world.is_finished() {
        let obs = world.observe()?;
        let t = obs.tick as usize;
        let proposal = mind.decide(&obs)?;
        if proposal.order_alert_red > 0 {
            order_alert_ticks.push(t);
        }
        if matches!(t, 21 | 53 | 81) {
            shock_braces.push(proposal.brace_level_blue);
        }

        let outcome = world.apply_proposal(&proposal)?;
        assert!(outcome.accepted);

        if let Some(expected) = &outcome.teaching_action {
            let p = t / 30;
            phase_total[p] += 1;
            if proposal.action == (MindAction::Act { name: expected.clone() }) {
                phase_correct[p] += 1;
            }
        }
        mind.integrate_outcome(&outcome)?;
    }

    // Phase 1 (Rule A): 15/15 (100.0%).
    assert_eq!((phase_correct[0], phase_total[0]), (15, 15));
    // Phase 2 (Unannounced Rule B flip): 13/15 (86.7%, exact theoretical ceiling for 2 unseen cues!).
    assert_eq!((phase_correct[1], phase_total[1]), (13, 15));
    // Phase 3 (Unannounced Rule A return): 12/15 (80.0%), with permanent base_red completely untouched.
    assert_eq!((phase_correct[2], phase_total[2]), (12, 15));
    assert_eq!(mind.cluster().synapse_weights("rec_purple", "act_0").unwrap().base_red, 1000);
    assert_eq!(mind.cluster().synapse_weights("rec_orange", "act_1").unwrap().base_red, 1000);

    // Purkinje cancels >77% of the 3rd shock in every phase despite lag shifting 3 -> 5 -> 3.
    assert_eq!(shock_braces.len(), 3);
    for &b in &shock_braces {
        assert!(b >= 770, "expected Purkinje brace >= 770, got {b}");
    }

    // Jeffress fires ONLY on Red -> 2 ticks -> Blue (tick 8), never on reversed Blue -> Red.
    assert_eq!(order_alert_ticks, vec![8]);

    // Export complete MindSession, round-trip through JSON, and audit offline.
    let session = mind.export_session()?;
    let json = serde_json::to_string(&session).unwrap();
    let restored: MindSession = serde_json::from_str(&json).unwrap();
    verify_mind_session(&restored)?;

    // Tampering with a recorded proposal action fails offline neural-decode verification!
    let mut forged = restored;
    forged.receipts[1].proposal.action = MindAction::Wait;
    assert!(verify_mind_session(&forged).is_err());

    Ok(())
}

#[test]
fn mid_run_snapshot_restart_reproduces_identical_continuations_and_stdio_plugin_works() -> Result<()>
{
    let schedule = build_90_tick_arena_schedule();
    let mind_kp = Keypair::generate();
    let cluster_kp = Keypair::generate();
    let world_kp = Keypair::generate();

    // Run 1: Continuous uninterrupted mind over all 90 ticks.
    let mut world_cont = AdaptiveArenaWorld::new(world_kp.clone(), schedule.clone())?;
    let mut mind_cont = build_six_archetype_mind(mind_kp.clone(), cluster_kp.clone())?;
    let mut cont_actions = Vec::new();
    while !world_cont.is_finished() {
        let obs = world_cont.observe()?;
        let prop = mind_cont.decide(&obs)?;
        cont_actions.push(prop.action.clone());
        let out = world_cont.apply_proposal(&prop)?;
        mind_cont.integrate_outcome(&out)?;
    }

    // Run 2: Pause at tick 45 (mid-Phase 2!), serialize MindSession to JSON, drop NeuroMind,
    // restore in a fresh instance, and finish ticks 45..90 via the stdio JSON-lines plugin API.
    let mut world_split = AdaptiveArenaWorld::new(world_kp, schedule)?;
    let mut mind_a = build_six_archetype_mind(mind_kp.clone(), cluster_kp.clone())?;
    let mut split_actions = Vec::new();

    for _ in 0..45 {
        let obs = world_split.observe()?;
        let prop = mind_a.decide(&obs)?;
        split_actions.push(prop.action.clone());
        let out = world_split.apply_proposal(&prop)?;
        mind_a.integrate_outcome(&out)?;
    }

    let export_resp: PluginResponse = serde_json::from_str(
        &mind_a.handle_json_line(&serde_json::to_string(&PluginRequest::ExportSession).unwrap())?,
    )
    .unwrap();
    let PluginResponse::Session { session: mid_snap } = export_resp else {
        panic!("expected Session response");
    };
    drop(mind_a);

    let mut mind_b = NeuroMind::restore(mid_snap, mind_kp, cluster_kp)?;
    while !world_split.is_finished() {
        let obs = world_split.observe()?;
        let decide_line =
            serde_json::to_string(&PluginRequest::Decide { observation: obs }).unwrap();
        let resp1: PluginResponse =
            serde_json::from_str(&mind_b.handle_json_line(&decide_line)?).unwrap();
        let PluginResponse::Proposal { proposal } = resp1 else {
            panic!("expected Proposal response");
        };
        split_actions.push(proposal.action.clone());

        let outcome = world_split.apply_proposal(&proposal)?;
        let out_line = serde_json::to_string(&PluginRequest::Outcome { outcome }).unwrap();
        let resp2: PluginResponse =
            serde_json::from_str(&mind_b.handle_json_line(&out_line)?).unwrap();
        assert!(matches!(resp2, PluginResponse::Receipt { .. }));
    }

    // Bit-for-bit identical action trajectory across the mid-run restart!
    assert_eq!(cont_actions, split_actions);
    verify_mind_session(&mind_b.export_session()?)?;

    Ok(())
}

#[test]
fn world_boundary_enforces_available_actions_refusal_and_stale_world_guards() -> Result<()> {
    let schedule = vec![
        ArenaStepSpec {
            sensory_field: TriSignal::raw(500, 500, 0), // Purple -> mind normally prefers act_0
            available_actions: vec!["act_1".into()],    // act_0 temporarily unavailable!
            teaching_action: None,
            shock: 0,
            attention_cue: 0,
        },
        ArenaStepSpec {
            sensory_field: TriSignal::raw(500, 500, 0),
            available_actions: vec!["act_0".into(), "act_1".into()],
            teaching_action: Some("act_0".into()),
            shock: 0,
            attention_cue: 0,
        },
    ];
    let mut world = AdaptiveArenaWorld::new(Keypair::generate(), schedule.clone())?;
    let mut other_world = AdaptiveArenaWorld::new(Keypair::generate(), schedule)?;
    let mut mind = build_six_archetype_mind(Keypair::generate(), Keypair::generate())?;

    // Tick 0: act_0 is unavailable, so NeuroMind respects available_actions and proposes Wait.
    let obs0 = world.observe()?;
    let prop0 = mind.decide(&obs0)?;
    assert_eq!(prop0.action, MindAction::Wait);

    // Cross-world guard: submitting prop0 to a different world is refused!
    let _ = other_world.observe()?;
    assert!(other_world.apply_proposal(&prop0).is_err());

    let out0 = world.apply_proposal(&prop0)?;
    assert!(out0.accepted);
    mind.integrate_outcome(&out0)?;

    // Tick 1: Stale prop0 (tick 0) cannot be replayed on tick 1.
    let obs1 = world.observe()?;
    assert!(world.apply_proposal(&prop0).is_err());

    // Honest prop1 selects act_0; world accepts.
    let prop1 = mind.decide(&obs1)?;
    assert_eq!(prop1.action, MindAction::Act { name: "act_0".into() });

    // Direct world-law check: if an external actor forces a signed proposal for an unavailable
    // action on other_world (tick 0 where only act_1 is available), other_world returns accepted=false.
    let rogue_kp = Keypair::generate();
    let other_obs = other_world.observe()?;
    let mut rogue_prop = ActionProposal {
        mind_id: rogue_kp.did(),
        cluster_id: rogue_kp.did(),
        world_id: other_obs.world_id.clone(),
        tick: other_obs.tick,
        observation_hash: other_obs.hash()?,
        sensory_tick_hash: "00".repeat(32),
        action: MindAction::Act {
            name: "act_0".into(),
        },
        confidence_red: 1000,
        brace_level_blue: 0,
        order_alert_red: 0,
        proof: chat_world::ProofOrArray::placeholder(),
    };
    let body = chat_world::hash::body_for_signing(&rogue_prop)?;
    rogue_prop.proof = chat_world::ProofOrArray::single(chat_world::Proof::create(
        &rogue_kp,
        &rogue_kp.sign(&body),
    ));
    let refused = other_world.apply_proposal(&rogue_prop)?;
    assert!(!refused.accepted);
    assert!(refused.refusal_reason.is_some());

    // Finish mind's tick 1 cleanly and verify session.
    let out1 = world.apply_proposal(&prop1)?;
    mind.integrate_outcome(&out1)?;
    verify_mind_session(&mind.export_session()?)?;

    Ok(())
}
