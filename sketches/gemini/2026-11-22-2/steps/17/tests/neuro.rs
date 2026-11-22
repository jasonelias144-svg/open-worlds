use chat_world::error::Result;
use chat_world::neuro::{
    update_synapse, verify_cluster_trace, Channel, ClusterTrace, DelayMode, NeuralCluster,
    PlasticityRule, SynapseSpec, SynapseWeights, TriSignal, UnitKind, UnitSpec, UnitState,
};
use chat_world::Keypair;
use std::collections::BTreeMap;

fn make_working_memory_cluster() -> Result<NeuralCluster> {
    let units = vec![
        UnitSpec {
            id: "cue".into(),
            kind: UnitKind::TriChannel {
                leak_g0: 1000,
                threshold: 0,
                yellow_decay: 0,
                blue_gain: 0,
                yellow_gain: 0,
            },
        },
        UnitSpec {
            id: "mem".into(),
            kind: UnitKind::TriChannel {
                leak_g0: 1000,
                threshold: 300,
                yellow_decay: 500,
                blue_gain: 0,
                yellow_gain: 0,
            },
        },
    ];
    let synapses = vec![SynapseSpec {
        from: "cue".into(),
        to: "mem".into(),
        base_red: 0,
        base_blue: 0,
        base_yellow: 0,
        decay_min: 500,
        decay_max: 950,
        write_deadzone: 0,
        learning_rate: 1000,
        consolidation_rate: 100,
        consolidation_threshold: 1300,
        fast_cap: 1500,
        plasticity: PlasticityRule::Hebbian,
    }];
    NeuralCluster::new("working-memory", Keypair::generate(), units, synapses)
}

#[test]
fn activity_silent_working_memory_dissolves_if_ignored_and_survives_with_yellow_attention()
-> Result<()> {
    // Branch A: Encode temporary binding, then leave unattended during a 4-tick quiet delay.
    let mut unattended = make_working_memory_cluster()?;
    unattended.step(BTreeMap::from([("cue".into(), TriSignal::red_only(1000))]))?;
    unattended.step(BTreeMap::from([(
        "mem".into(),
        TriSignal::new(1000, 0, 1000),
    )]))?;

    let w_after_encode = unattended.synapse_weights("cue", "mem").unwrap();
    assert_eq!(w_after_encode.fast_red, 1200);
    assert_eq!(w_after_encode.base_red, 0);

    for _ in 0..4 {
        unattended.step(BTreeMap::new())?;
        assert_eq!(unattended.unit_state("cue").unwrap().output.red, 0);
        assert_eq!(unattended.unit_state("mem").unwrap().output.red, 0);
    }
    assert!(unattended.synapse_weights("cue", "mem").unwrap().fast_red < 200);

    unattended.step(BTreeMap::from([("cue".into(), TriSignal::red_only(1000))]))?;
    unattended.step(BTreeMap::new())?;
    assert_eq!(unattended.unit_state("mem").unwrap().output.red, 0);
    verify_cluster_trace(&unattended.trace())?;

    // Branch B: Identical encode and 4-tick quiet delay, refreshed ONLY by Yellow attention.
    let mut attended = make_working_memory_cluster()?;
    attended.step(BTreeMap::from([("cue".into(), TriSignal::red_only(1000))]))?;
    attended.step(BTreeMap::from([(
        "mem".into(),
        TriSignal::new(1000, 0, 1000),
    )]))?;

    for _ in 0..4 {
        attended.step(BTreeMap::from([(
            "mem".into(),
            TriSignal::yellow_only(600),
        )]))?;
        assert_eq!(attended.unit_state("cue").unwrap().output.red, 0);
        assert_eq!(attended.unit_state("mem").unwrap().output.red, 0);
    }
    let w_kept = attended.synapse_weights("cue", "mem").unwrap();
    assert!(w_kept.fast_red > 900);
    assert_eq!(w_kept.base_red, 0);

    attended.step(BTreeMap::from([("cue".into(), TriSignal::red_only(1000))]))?;
    attended.step(BTreeMap::new())?;
    assert!(attended.unit_state("mem").unwrap().output.red > 500);
    verify_cluster_trace(&attended.trace())?;
    Ok(())
}

#[test]
fn divisive_shunting_scales_proportionally_and_repeated_rehearsal_consolidates_baseline()
-> Result<()> {
    let unit = UnitKind::TriChannel {
        leak_g0: 1000,
        threshold: 0,
        yellow_decay: 0,
        blue_gain: 0,
        yellow_gain: 0,
    };
    let st = UnitState::default();
    assert_eq!(unit.step(&st, TriSignal::new(1000, 0, 0)).output.red, 1000);
    assert_eq!(unit.step(&st, TriSignal::new(1000, 1000, 0)).output.red, 500);
    assert_eq!(unit.step(&st, TriSignal::new(2000, 1000, 0)).output.red, 1000);
    assert_eq!(unit.step(&st, TriSignal::new(200, 1000, 0)).output.red, 100);

    let mut cluster = make_working_memory_cluster()?;
    cluster.step(BTreeMap::from([("cue".into(), TriSignal::red_only(1000))]))?;
    for _ in 0..4 {
        cluster.step(BTreeMap::from([
            ("cue".into(), TriSignal::red_only(1000)),
            ("mem".into(), TriSignal::new(1000, 0, 1000)),
        ]))?;
    }
    assert_eq!(cluster.synapse_weights("cue", "mem").unwrap().fast_red, 1500);
    assert!(cluster.synapse_weights("cue", "mem").unwrap().base_red >= 450);

    for _ in 0..12 {
        cluster.step(BTreeMap::new())?;
    }
    assert_eq!(cluster.synapse_weights("cue", "mem").unwrap().fast_red, 0);
    assert!(cluster.synapse_weights("cue", "mem").unwrap().base_red >= 450);

    cluster.step(BTreeMap::from([("cue".into(), TriSignal::red_only(1000))]))?;
    cluster.step(BTreeMap::new())?;
    assert!(cluster.unit_state("mem").unwrap().output.red > 100);
    verify_cluster_trace(&cluster.trace())?;
    Ok(())
}

#[test]
fn receptor_broadcast_decodes_composite_hues_across_400x_intensity_shifts() -> Result<()> {
    let rec_red = UnitKind::ReceptorBroadcast {
        affinity: [1000, 0, 0],
        sigma: 160,
        g0: 15,
        threshold: 450,
        emit_channel: Channel::Red,
    };
    let rec_blue = UnitKind::ReceptorBroadcast {
        affinity: [0, 1000, 0],
        sigma: 160,
        g0: 15,
        threshold: 450,
        emit_channel: Channel::Blue,
    };
    let rec_purple = UnitKind::ReceptorBroadcast {
        affinity: [500, 500, 0],
        sigma: 160,
        g0: 15,
        threshold: 450,
        emit_channel: Channel::Red,
    };
    let st = UnitState::default();

    // Purple across 400x intensity shift (0.05x -> 1x -> 20x) fires ONLY rec_purple.
    for sig in [
        TriSignal::raw(25, 25, 0),
        TriSignal::raw(500, 500, 0),
        TriSignal::raw(10_000, 10_000, 0),
    ] {
        assert!(rec_purple.step(&st, sig).output.red >= 580);
        assert_eq!(rec_red.step(&st, sig).output.red, 0);
        assert_eq!(rec_blue.step(&st, sig).output.blue, 0);
    }

    // Pure Red and Pure Blue fire only their own channels.
    assert_eq!(rec_red.step(&st, TriSignal::raw(1000, 0, 0)).output.red, 972);
    assert_eq!(rec_purple.step(&st, TriSignal::raw(1000, 0, 0)).output.red, 0);
    assert_eq!(
        rec_blue.step(&st, TriSignal::raw(0, 1000, 0)).output.blue,
        972
    );
    assert_eq!(rec_purple.step(&st, TriSignal::raw(0, 1000, 0)).output.red, 0);

    // Equal White/Mud mutes all three selective receptors.
    let mud = TriSignal::raw(1000, 1000, 1000);
    assert_eq!(rec_red.step(&st, mud).output.red, 0);
    assert_eq!(rec_blue.step(&st, mud).output.blue, 0);
    assert_eq!(rec_purple.step(&st, mud).output.red, 0);

    Ok(())
}

#[test]
fn delay_line_enforces_exact_order_and_adapts_purkinje_cancellation_across_lag_shifts() -> Result<()>
{
    // 1. Jeffress coincidence: fire ONLY when Red precedes Blue by exactly 2 ticks.
    let jeffress = UnitKind::DelayLine {
        max_lag: 4,
        mode: DelayMode::Coincidence {
            lag_a: 2,
            lag_b: 0,
            threshold: 600,
        },
    };
    let run_seq = |seq: &[TriSignal]| -> Vec<i64> {
        let mut st = UnitState::for_kind(&jeffress);
        seq.iter()
            .map(|&s| {
                st = jeffress.step(&st, s);
                st.output.red
            })
            .collect()
    };

    assert_eq!(
        run_seq(&[
            TriSignal::red_only(1000),
            TriSignal::default(),
            TriSignal::blue_only(1000),
            TriSignal::default(),
        ]),
        vec![0, 0, 1000, 0]
    );
    // Reversed order (Blue -> 2 -> Red) and wrong lag (Red -> 1 -> Blue) stay completely silent.
    assert_eq!(
        run_seq(&[
            TriSignal::blue_only(1000),
            TriSignal::default(),
            TriSignal::red_only(1000),
            TriSignal::default(),
        ]),
        vec![0, 0, 0, 0]
    );
    assert_eq!(
        run_seq(&[
            TriSignal::red_only(1000),
            TriSignal::blue_only(1000),
            TriSignal::default(),
        ]),
        vec![0, 0, 0]
    );

    // 2. Purkinje shifting-lag cancellation: Phase 1 lag = 3 -> unannounced shift to lag = 5.
    let purkinje = UnitKind::DelayLine {
        max_lag: 6,
        mode: DelayMode::PurkinjeCancel {
            lr_fast: 850,
            decay_quiet: 995,
            decay_error: 880,
            error_threshold: 250,
            tap_cap: 1500,
            base_taps: vec![0; 6],
        },
    };
    let mut cues = vec![0i64; 120];
    let mut shocks = vec![0i64; 120];
    for tc in (2..60).step_by(10) {
        cues[tc] = 1000;
        shocks[tc + 3] = 1000;
    }
    for tc in (62..114).step_by(10) {
        cues[tc] = 1000;
        shocks[tc + 5] = 1000;
    }

    let mut st = UnitState::for_kind(&purkinje);
    let mut p1_err_sum = 0i64;
    let mut p2_err_sum = 0i64;
    for t in 0..120 {
        st = purkinje.step(&st, TriSignal::raw(cues[t], 0, shocks[t]));
        let err = (shocks[t] - st.output.blue).abs();
        if (30..60).contains(&t) {
            p1_err_sum += err;
        }
        if (90..120).contains(&t) {
            p2_err_sum += err;
        }
    }
    // Post-adaptation MAE <= 10/1000 (1.0%) in BOTH phases, and old lag-3 tap self-zeroes!
    assert!(p1_err_sum / 30 <= 10);
    assert!(p2_err_sum / 30 <= 10);
    assert_eq!(st.fast_taps[2], 0); // old lag 3 cleanly dissolved
    assert!(st.fast_taps[4] >= 950); // new lag 5 locked cleanly

    Ok(())
}

#[test]
fn sparse_deadzone_write_gate_blocks_50_distractors_and_supports_one_shot_delta_rebind() {
    let spec = SynapseSpec {
        from: "cue".into(),
        to: "act".into(),
        base_red: 0,
        base_blue: 0,
        base_yellow: 0,
        decay_min: 1000,
        decay_max: 1000,
        write_deadzone: 300,
        learning_rate: 1000,
        consolidation_rate: 0,
        consolidation_threshold: 1500,
        fast_cap: 1500,
        plasticity: PlasticityRule::Delta,
    };

    // 1. Bind cue -> act_0 under full Yellow attention (1000).
    let mut w0 = update_synapse(
        &spec,
        SynapseWeights {
            base_red: 0,
            fast_red: 0,
        },
        1000,
        1000,
        1000,
        0,
        1000,
    );
    let mut w1 = update_synapse(
        &spec,
        SynapseWeights {
            base_red: 0,
            fast_red: 0,
        },
        1000,
        0,
        0,
        0,
        1000,
    );
    assert_eq!(w0.fast_red, 1000);
    assert_eq!(w1.fast_red, 0);

    // 2. 50 distractor ticks with stray Yellow = 250 (<= deadzone 300) cause EXACT ZERO BLEED.
    for _ in 0..50 {
        w0 = update_synapse(&spec, w0, 1000, 0, 0, w0.fast_red, 250);
        w1 = update_synapse(&spec, w1, 1000, 1000, 1000, w1.fast_red, 250);
    }
    assert_eq!(w0.fast_red, 1000);
    assert_eq!(w1.fast_red, 0);

    // 3. One-shot Delta REBIND to act_1 under Yellow = 1000 cleanly erases w0 and writes w1.
    w0 = update_synapse(&spec, w0, 1000, 0, 0, w0.fast_red, 1000);
    w1 = update_synapse(&spec, w1, 1000, 1000, 1000, w1.fast_red, 1000);
    assert_eq!(w0.fast_red, 0);
    assert_eq!(w1.fast_red, 1000);
}

#[test]
fn full_six_archetype_micro_brain_runs_all_modules_and_verifies_offline() -> Result<()> {
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
            id: "rec_green".into(),
            kind: UnitKind::ReceptorBroadcast {
                affinity: [0, 500, 500],
                sigma: 160,
                g0: 15,
                threshold: 450,
                emit_channel: Channel::Red,
            },
        },
        UnitSpec {
            id: "jeffress".into(),
            kind: UnitKind::DelayLine {
                max_lag: 4,
                mode: DelayMode::Coincidence {
                    lag_a: 2,
                    lag_b: 0,
                    threshold: 600,
                },
            },
        },
        UnitSpec {
            id: "purkinje".into(),
            kind: UnitKind::DelayLine {
                max_lag: 6,
                mode: DelayMode::PurkinjeCancel {
                    lr_fast: 850,
                    decay_quiet: 995,
                    decay_error: 880,
                    error_threshold: 250,
                    tap_cap: 1500,
                    base_taps: vec![0; 6],
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
                tonic_decay: 800,
                red_trigger_gain: 0,
                threshold: 200,
            },
        },
        UnitSpec {
            id: "shunt_inh".into(),
            kind: UnitKind::ShuntingInterneuron {
                threshold: 100,
                blue_gain: 500,
            },
        },
        UnitSpec {
            id: "act_0".into(),
            kind: UnitKind::TriChannel {
                leak_g0: 1000,
                threshold: 250,
                yellow_decay: 0,
                blue_gain: 0,
                yellow_gain: 0,
            },
        },
        UnitSpec {
            id: "act_1".into(),
            kind: UnitKind::TriChannel {
                leak_g0: 1000,
                threshold: 250,
                yellow_decay: 0,
                blue_gain: 0,
                yellow_gain: 0,
            },
        },
    ];

    let delta_syn = |from: &str, to: &str| SynapseSpec {
        from: from.into(),
        to: to.into(),
        base_red: 0,
        base_blue: 0,
        base_yellow: 0,
        decay_min: 1000,
        decay_max: 1000,
        write_deadzone: 300,
        learning_rate: 1000,
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
        SynapseSpec::static_channel("mod_nuc", "act_0", 0, 0, 1000),
        SynapseSpec::static_channel("mod_nuc", "act_1", 0, 0, 1000),
        delta_syn("rec_purple", "act_0"),
        delta_syn("rec_purple", "act_1"),
        SynapseSpec::static_channel("act_0", "shunt_inh", 1000, 0, 0),
        SynapseSpec::static_channel("act_1", "shunt_inh", 1000, 0, 0),
        SynapseSpec::static_channel("shunt_inh", "act_0", 0, 1000, 0),
        SynapseSpec::static_channel("shunt_inh", "act_1", 0, 1000, 0),
    ];

    let mut brain = NeuralCluster::new("six-archetype-micro-brain", Keypair::generate(), units, synapses)?;

    // 1. Unexpected event triggers Pyramidal surprise -> ModulatorNucleus tonic Yellow wave.
    brain.step(BTreeMap::from([("pyr".into(), TriSignal::red_only(1000))]))?;
    // 2. While mod_nuc broadcasts Yellow, present 20x bright Purple (10_000, 10_000, 0).
    brain.step(BTreeMap::from([(
        "rec_purple".into(),
        TriSignal::raw(10_000, 10_000, 0),
    )]))?;
    // 3. Teach act_0 while Yellow attention is open -> binds rec_purple -> act_0 (998).
    brain.step(BTreeMap::from([("act_0".into(), TriSignal::red_only(1000))]))?;
    assert_eq!(brain.synapse_weights("rec_purple", "act_0").unwrap().fast_red, 998);
    assert_eq!(brain.synapse_weights("rec_purple", "act_1").unwrap().fast_red, 0);

    // 4. Wait until ModulatorNucleus tonic Yellow decays below the sparse dead-zone (<= 300).
    for _ in 0..9 {
        brain.step(BTreeMap::new())?;
    }
    assert!(brain.unit_state("mod_nuc").unwrap().yellow_level <= 300);

    // 5. Inject 10 ticks of distractor noise on rec_purple + act_1 -> ZERO write bleed!
    for _ in 0..10 {
        brain.step(BTreeMap::from([
            ("rec_purple".into(), TriSignal::raw(500, 500, 0)),
            ("act_1".into(), TriSignal::red_only(1000)),
        ]))?;
    }
    assert_eq!(brain.synapse_weights("rec_purple", "act_0").unwrap().fast_red, 998);
    assert_eq!(brain.synapse_weights("rec_purple", "act_1").unwrap().fast_red, 0);

    // 6. Query with 400x DIMMER Purple (25, 25, 0) -> recalls act_0 cleanly while act_1 stays 0!
    brain.step(BTreeMap::from([(
        "rec_purple".into(),
        TriSignal::raw(25, 25, 0),
    )]))?;
    brain.step(BTreeMap::new())?;
    assert_eq!(brain.unit_state("act_0").unwrap().output.red, 157);
    assert_eq!(brain.unit_state("act_1").unwrap().output.red, 0);

    // 7. Spatiotemporal order detection through receptors: Red -> 2 ticks -> 5x bright Blue.
    brain.step(BTreeMap::from([(
        "rec_red".into(),
        TriSignal::raw(1000, 0, 0),
    )]))?;
    brain.step(BTreeMap::new())?;
    brain.step(BTreeMap::from([(
        "rec_blue".into(),
        TriSignal::raw(0, 5000, 0),
    )]))?;
    brain.step(BTreeMap::new())?;
    assert_eq!(brain.unit_state("jeffress").unwrap().output.red, 982);

    // 8. Round-trip the entire signed ClusterTrace through JSON and verify offline.
    let json = serde_json::to_string(&brain.trace()).unwrap();
    let restored: ClusterTrace = serde_json::from_str(&json).unwrap();
    verify_cluster_trace(&restored)?;

    // 9. Tampering with a fast synapse weight or a DelayLine buffer fails offline verification.
    let mut forged_w = restored.clone();
    forged_w.ticks[2].synapse_weights[6].fast_red = 0;
    assert!(verify_cluster_trace(&forged_w).is_err());

    let mut forged_buf = restored;
    forged_buf.ticks.last_mut().unwrap().unit_states.get_mut("jeffress").unwrap().delay_buf_a[2] = 0;
    assert!(verify_cluster_trace(&forged_buf).is_err());

    Ok(())
}
