use chat_world::error::Result;
use chat_world::neuro::{
    verify_cluster_trace, ClusterTrace, NeuralCluster, SynapseSpec, TriSignal, UnitKind, UnitSpec,
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
        learning_rate: 1000,
        consolidation_rate: 100,
        consolidation_threshold: 1300, // above single-shot encode (1200)
        fast_cap: 1500,
    }];
    NeuralCluster::new("working-memory", Keypair::generate(), units, synapses)
}

#[test]
fn activity_silent_working_memory_dissolves_if_ignored_and_survives_with_yellow_attention()
-> Result<()> {
    // Branch A: Encode temporary binding, then leave unattended during a 4-tick quiet delay.
    let mut unattended = make_working_memory_cluster()?;
    unattended.step(BTreeMap::from([("cue".into(), TriSignal::red_only(1000))]))?;
    unattended.step(BTreeMap::from([("mem".into(), TriSignal::new(1000, 0, 1000))]))?;

    let w_after_encode = unattended.synapse_weights("cue", "mem").unwrap();
    assert_eq!(w_after_encode.fast_red, 1200);
    assert_eq!(w_after_encode.base_red, 0); // fleeting single-shot does not alter permanent weight

    for _ in 0..4 {
        unattended.step(BTreeMap::new())?;
        // Activity-silent: both units have zero Red firing during the delay!
        assert_eq!(unattended.unit_state("cue").unwrap().output.red, 0);
        assert_eq!(unattended.unit_state("mem").unwrap().output.red, 0);
    }
    assert!(unattended.synapse_weights("cue", "mem").unwrap().fast_red < 200);

    // Probe cue alone -> binding dissolved, so mem stays silent.
    unattended.step(BTreeMap::from([("cue".into(), TriSignal::red_only(1000))]))?;
    unattended.step(BTreeMap::new())?;
    assert_eq!(unattended.unit_state("mem").unwrap().output.red, 0);
    verify_cluster_trace(&unattended.trace())?;

    // Branch B: Identical encode and identical 4-tick quiet delay, refreshed ONLY by Yellow attention.
    let mut attended = make_working_memory_cluster()?;
    attended.step(BTreeMap::from([("cue".into(), TriSignal::red_only(1000))]))?;
    attended.step(BTreeMap::from([("mem".into(), TriSignal::new(1000, 0, 1000))]))?;

    for _ in 0..4 {
        attended.step(BTreeMap::from([("mem".into(), TriSignal::yellow_only(600))]))?;
        // Still activity-silent: zero Red firing on every unit!
        assert_eq!(attended.unit_state("cue").unwrap().output.red, 0);
        assert_eq!(attended.unit_state("mem").unwrap().output.red, 0);
    }
    let w_kept = attended.synapse_weights("cue", "mem").unwrap();
    assert!(w_kept.fast_red > 900);
    assert_eq!(w_kept.base_red, 0); // still purely short-term memory

    // Probe cue alone -> mem recalls strongly from the silent fast-weight trace!
    attended.step(BTreeMap::from([("cue".into(), TriSignal::red_only(1000))]))?;
    attended.step(BTreeMap::new())?;
    assert!(attended.unit_state("mem").unwrap().output.red > 500);

    // JSON round-trip & offline verification.
    let json = serde_json::to_string(&attended.trace()).unwrap();
    let restored: ClusterTrace = serde_json::from_str(&json).unwrap();
    verify_cluster_trace(&restored)?;

    Ok(())
}

#[test]
fn divisive_shunting_scales_proportionally_and_repeated_rehearsal_consolidates_baseline()
-> Result<()> {
    // 1. Verify divisive shunting vs linear subtraction on a TriChannelUnit.
    let unit = UnitKind::TriChannel {
        leak_g0: 1000,
        threshold: 0,
        yellow_decay: 0,
        blue_gain: 0,
        yellow_gain: 0,
    };
    // With blue = 1000 and leak_g0 = 1000, shunting divides every Red input cleanly by 2.
    assert_eq!(unit.step(0, TriSignal::new(1000, 0, 0)).1.red, 1000);
    assert_eq!(unit.step(0, TriSignal::new(1000, 1000, 0)).1.red, 500);
    assert_eq!(unit.step(0, TriSignal::new(2000, 1000, 0)).1.red, 1000);
    assert_eq!(unit.step(0, TriSignal::new(200, 1000, 0)).1.red, 100);

    // 2. Repeated attended rehearsal crosses consolidation_threshold (1300) and hardens base_red.
    let mut cluster = make_working_memory_cluster()?;
    cluster.step(BTreeMap::from([("cue".into(), TriSignal::red_only(1000))]))?;
    for _ in 0..4 {
        cluster.step(BTreeMap::from([
            ("cue".into(), TriSignal::red_only(1000)),
            ("mem".into(), TriSignal::new(1000, 0, 1000)),
        ]))?;
    }
    let w_rehearsed = cluster.synapse_weights("cue", "mem").unwrap();
    assert_eq!(w_rehearsed.fast_red, 1500);
    assert!(w_rehearsed.base_red >= 450);

    // Even after 12 unattended ticks dissolve fast_red to near zero, base_red survives!
    for _ in 0..12 {
        cluster.step(BTreeMap::new())?;
    }
    let w_long_term = cluster.synapse_weights("cue", "mem").unwrap();
    assert_eq!(w_long_term.fast_red, 0);
    assert!(w_long_term.base_red >= 450);

    // Probing cue alone now activates mem via long-term consolidated base_red!
    cluster.step(BTreeMap::from([("cue".into(), TriSignal::red_only(1000))]))?;
    cluster.step(BTreeMap::new())?;
    assert!(cluster.unit_state("mem").unwrap().output.red > 100);
    verify_cluster_trace(&cluster.trace())?;

    Ok(())
}

#[test]
fn heterogeneous_four_unit_module_connects_pyramidal_surprise_modulator_shunting_and_memory()
-> Result<()> {
    let units = vec![
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
            id: "mod".into(),
            kind: UnitKind::ModulatorNucleus {
                tonic_decay: 850,
                red_trigger_gain: 0,
                threshold: 200,
            },
        },
        UnitSpec {
            id: "inh".into(),
            kind: UnitKind::ShuntingInterneuron {
                threshold: 200,
                blue_gain: 1000,
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
    let synapses = vec![
        SynapseSpec::static_channel("pyr", "mod", 0, 0, 1000),
        SynapseSpec::static_channel("mod", "mem", 0, 0, 1000),
        SynapseSpec::static_channel("pyr", "inh", 1000, 0, 0),
        SynapseSpec::static_channel("inh", "mem", 0, 1000, 0),
    ];

    let mut cluster = NeuralCluster::new("cortical-microcircuit", Keypair::generate(), units, synapses)?;

    // 1. Top-down expectation alone on pyramidal unit produces zero output (no hallucination).
    cluster.step(BTreeMap::from([("pyr".into(), TriSignal::yellow_only(800))]))?;
    assert_eq!(cluster.unit_state("pyr").unwrap().output, TriSignal::default());

    // 2. Coincidence (basal 800 + apical 600) produces a boosted Red burst and ZERO surprise.
    cluster.step(BTreeMap::from([("pyr".into(), TriSignal::new(800, 0, 600))]))?;
    let pyr_coinc = cluster.unit_state("pyr").unwrap().output;
    assert_eq!(pyr_coinc.red, 800);
    assert_eq!(pyr_coinc.yellow, 0);

    // 3. Unexpected sensory input (basal 1000, apical 0) emits Yellow surprise = 1000!
    cluster.step(BTreeMap::from([("pyr".into(), TriSignal::red_only(1000))]))?;
    let pyr_surp = cluster.unit_state("pyr").unwrap().output;
    assert_eq!(pyr_surp.red, 700);
    assert_eq!(pyr_surp.yellow, 1000);

    // 4. Next tick: ModulatorNucleus catches surprise and emits tonic Yellow = 1000;
    //    ShuntingInterneuron catches pyr's Red (700) and emits Blue shunt = 500.
    cluster.step(BTreeMap::new())?;
    assert_eq!(cluster.unit_state("mod").unwrap().output.yellow, 1000);
    assert_eq!(cluster.unit_state("inh").unwrap().output.blue, 500);

    // 5. Next tick: mem simultaneously receives ModulatorNucleus's Yellow attention wave
    //    AND ShuntingInterneuron's Blue gain control, while mod's tonic wave lingers at 850.
    cluster.step(BTreeMap::from([("mem".into(), TriSignal::red_only(1000))]))?;
    assert_eq!(cluster.unit_state("mem").unwrap().yellow_level, 1000);
    assert_eq!(cluster.unit_state("mem").unwrap().output.red, 699);
    assert_eq!(cluster.unit_state("mod").unwrap().output.yellow, 850);

    let trace = cluster.trace();
    verify_cluster_trace(&trace)?;

    // Tampering with any recorded synapse weight or output fails offline verification.
    let mut forged = trace;
    forged.ticks[3].unit_states.get_mut("mod").unwrap().output.yellow = 0;
    assert!(verify_cluster_trace(&forged).is_err());

    Ok(())
}
