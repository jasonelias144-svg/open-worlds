use chat_world::circuit::{
    verify_circuit_trace, ExternalInput, Route, SignalValue, WorldCircuit, WorldRule, WorldState,
};
use chat_world::error::Result;
use chat_world::Keypair;
use std::collections::BTreeMap;

fn build_three_world_feedback_loop(
    initial_plant: i64,
    target: i64,
    gain_num: i64,
    gain_den: i64,
) -> Result<(WorldCircuit, chat_world::DidKey)> {
    let mut circuit = WorldCircuit::new();
    let plant_id = circuit.add_world(
        "plant",
        Keypair::generate(),
        WorldRule::Plant {
            initial: initial_plant,
        },
    )?;
    let comp_id = circuit.add_world(
        "comparator",
        Keypair::generate(),
        WorldRule::Comparator { target },
    )?;
    let ctrl_id = circuit.add_world(
        "controller",
        Keypair::generate(),
        WorldRule::FeedbackController {
            gain_num,
            gain_den,
            max_out: 10_000,
        },
    )?;

    // Ring topology: plant -> comparator -> controller -> plant (3-tick round-trip delay)
    circuit.add_route(Route {
        from_world: plant_id.clone(),
        from_port: "state".into(),
        to_world: comp_id.clone(),
        to_port: "reading".into(),
        delay: 1,
    })?;
    circuit.add_route(Route {
        from_world: comp_id.clone(),
        from_port: "error".into(),
        to_world: ctrl_id.clone(),
        to_port: "error".into(),
        delay: 1,
    })?;
    circuit.add_route(Route {
        from_world: ctrl_id,
        from_port: "control".into(),
        to_world: plant_id.clone(),
        to_port: "drive".into(),
        delay: 1,
    })?;

    Ok((circuit, plant_id))
}

#[test]
fn three_world_feedback_loop_converges_at_low_gain_and_oscillates_at_high_gain() -> Result<()> {
    // 1. Gain 1/4 (< golden stability limit ~0.618 for a 3-hop delayed ring) settles to 0.
    let (mut stable, plant_stable) = build_three_world_feedback_loop(100, 0, 1, 4)?;
    for _ in 0..20 {
        stable.step(Vec::new())?;
    }
    assert_eq!(
        stable.state(&plant_stable),
        Some(&WorldState::Plant { value: 0 })
    );
    verify_circuit_trace(&stable.trace())?;

    // 2. Exact same three worlds and topology, gain raised to 1/1 (> 0.618) -> growing oscillation.
    let (mut unstable, plant_unstable) = build_three_world_feedback_loop(100, 0, 1, 1)?;
    for _ in 0..15 {
        unstable.step(Vec::new())?;
    }
    let WorldState::Plant { value } = unstable.state(&plant_unstable).unwrap() else {
        panic!("expected Plant state");
    };
    assert!(
        value.abs() > 500,
        "high-gain 3-hop delayed ring should diverge in amplitude, got {value}"
    );
    verify_circuit_trace(&unstable.trace())?;

    Ok(())
}

#[test]
fn neuron_world_integrates_weighted_inputs_and_latches_persistent_memory() -> Result<()> {
    let mut circuit = WorldCircuit::new();
    let reg_a = circuit.add_world("sensor_a", Keypair::generate(), WorldRule::Register { initial: 0 })?;
    let reg_b = circuit.add_world("sensor_b", Keypair::generate(), WorldRule::Register { initial: 0 })?;

    let mut weights = BTreeMap::new();
    weights.insert("a".into(), 2);
    weights.insert("b".into(), 2);
    let neuron = circuit.add_world(
        "neuron",
        Keypair::generate(),
        WorldRule::Neuron {
            threshold: 5,
            leak: 1,
            refractory_ticks: 2,
            weights,
        },
    )?;
    let latch = circuit.add_world(
        "memory_latch",
        Keypair::generate(),
        WorldRule::MemoryLatch { initial: false },
    )?;

    circuit.add_route(Route {
        from_world: reg_a.clone(),
        from_port: "value".into(),
        to_world: neuron.clone(),
        to_port: "a".into(),
        delay: 1,
    })?;
    circuit.add_route(Route {
        from_world: reg_b.clone(),
        from_port: "value".into(),
        to_world: neuron.clone(),
        to_port: "b".into(),
        delay: 1,
    })?;
    circuit.add_route(Route {
        from_world: neuron.clone(),
        from_port: "spike".into(),
        to_world: latch.clone(),
        to_port: "set".into(),
        delay: 1,
    })?;

    // Tick 0: drive both sensors to 1.
    circuit.step(vec![
        ExternalInput {
            to_world: reg_a.clone(),
            to_port: "write".into(),
            value: SignalValue::Int(1),
        },
        ExternalInput {
            to_world: reg_b.clone(),
            to_port: "write".into(),
            value: SignalValue::Int(1),
        },
    ])?;

    // Tick 1: neuron accumulates 2*1 + 2*1 = 4 (< threshold 5); latch still false.
    circuit.step(Vec::new())?;
    assert_eq!(
        circuit.state(&neuron),
        Some(&WorldState::Neuron {
            potential: 4,
            refractory_left: 0,
            fired_count: 0,
        })
    );
    assert_eq!(
        circuit.state(&latch),
        Some(&WorldState::MemoryLatch { stored: false })
    );

    // Tick 2: neuron leaks 4 -> 3, integrates +4 -> 7 >= 5 -> FIRES! Enters 2-tick refractory.
    circuit.step(Vec::new())?;
    assert_eq!(
        circuit.state(&neuron),
        Some(&WorldState::Neuron {
            potential: 0,
            refractory_left: 2,
            fired_count: 1,
        })
    );

    // Tick 3: spike arrives at latch -> stored becomes true; neuron decrements refractory to 1.
    circuit.step(Vec::new())?;
    assert_eq!(
        circuit.state(&latch),
        Some(&WorldState::MemoryLatch { stored: true })
    );
    assert_eq!(
        circuit.state(&neuron),
        Some(&WorldState::Neuron {
            potential: 0,
            refractory_left: 1,
            fired_count: 1,
        })
    );

    // Tick 4: clear both sensors to 0.
    circuit.step(vec![
        ExternalInput {
            to_world: reg_a,
            to_port: "clear".into(),
            value: SignalValue::Bool(true),
        },
        ExternalInput {
            to_world: reg_b,
            to_port: "clear".into(),
            value: SignalValue::Bool(true),
        },
    ])?;

    // Tick 5: inputs are silent and neuron is quiet, yet latch retains stored = true.
    circuit.step(Vec::new())?;
    assert_eq!(
        circuit.state(&latch),
        Some(&WorldState::MemoryLatch { stored: true })
    );

    // Tick 6: explicit reset clears the latch back to false.
    circuit.step(vec![ExternalInput {
        to_world: latch.clone(),
        to_port: "reset".into(),
        value: SignalValue::Bool(true),
    }])?;
    assert_eq!(
        circuit.state(&latch),
        Some(&WorldState::MemoryLatch { stored: false })
    );

    verify_circuit_trace(&circuit.trace())?;
    Ok(())
}

#[test]
fn port_type_mismatch_zero_delay_and_forged_traces_are_refused() -> Result<()> {
    let mut circuit = WorldCircuit::new();
    let reg = circuit.add_world("reg", Keypair::generate(), WorldRule::Register { initial: 7 })?;
    let latch = circuit.add_world(
        "latch",
        Keypair::generate(),
        WorldRule::MemoryLatch { initial: false },
    )?;

    // Connecting Int output to Bool input -> refused.
    assert!(circuit
        .add_route(Route {
            from_world: reg.clone(),
            from_port: "value".into(),
            to_world: latch.clone(),
            to_port: "set".into(),
            delay: 1,
        })
        .is_err());

    // Zero-delay route -> refused.
    assert!(circuit
        .add_route(Route {
            from_world: reg.clone(),
            from_port: "value".into(),
            to_world: reg.clone(),
            to_port: "write".into(),
            delay: 0,
        })
        .is_err());

    // Build a valid trace, round-trip through JSON, and verify tampering is caught.
    let (mut valid, _) = build_three_world_feedback_loop(40, 0, 1, 4)?;
    for _ in 0..5 {
        valid.step(Vec::new())?;
    }
    let trace = valid.trace();
    let json = serde_json::to_string(&trace).unwrap();
    let roundtrip: chat_world::circuit::CircuitTrace = serde_json::from_str(&json).unwrap();
    verify_circuit_trace(&roundtrip)?;

    // Attack 1: tamper with an emitted signal payload.
    let mut tampered_sig = roundtrip.clone();
    tampered_sig.ticks[0].emitted_signals[0].payload = SignalValue::Int(999);
    assert!(verify_circuit_trace(&tampered_sig).is_err());

    // Attack 2: drop a scheduled signal from delivered_signals at tick 1.
    let mut dropped_delivery = roundtrip.clone();
    dropped_delivery.ticks[1].delivered_signals.clear();
    assert!(verify_circuit_trace(&dropped_delivery).is_err());

    // Attack 3: forge a node's next_state_hash.
    let mut forged_state = roundtrip;
    forged_state.ticks[0].node_records[0].next_state_hash = "00".repeat(32);
    assert!(verify_circuit_trace(&forged_state).is_err());

    Ok(())
}
