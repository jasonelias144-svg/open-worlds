import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c3 import Act, Ack, Refusal
from multiverse_c42 import SignalWorld
from multiverse_c47 import (
    AutonomicUnit, AutonomicNetwork, EpochResult, demo,
)


# =====================================================================
# Unit construction and accessors
# =====================================================================

def test_unit_construction():
    print("=== AutonomicUnit: construction ===")
    u = AutonomicUnit(
        entity_id="world:u", name="U",
        target=22.0, initial_state=20.0,
        correction_strength=3.0, ambient_drift=0.5)
    assert u.state == 20.0
    assert u.target == 22.0
    assert u.correction_strength == 3.0


def test_unit_is_wcp_world():
    print("=== AutonomicUnit: WCP shape + conformance ===")
    from wcp_conformance import run_conformance
    u = AutonomicUnit("world:u", "U", 22.0, 20.0)
    assert run_conformance(u)["passed"]


# =====================================================================
# Firing behavior — own state only
# =====================================================================

def test_no_fire_below_target():
    print("=== Unit: below target → no fire ===")
    u = AutonomicUnit("world:u", "U", 22.0, 20.0)
    assert u.tick(0) is False
    assert u.state == 20.0  # unchanged


def test_fire_at_target_exactly_no_fire():
    print("=== Unit: state == target → no fire (needs >) ===")
    u = AutonomicUnit("world:u", "U", 22.0, 22.0)
    assert u.tick(0) is False


def test_fire_above_target():
    print("=== Unit: above target → fires, state -correction ===")
    u = AutonomicUnit("world:u", "U", 22.0, 23.0,
                       correction_strength=3.0)
    assert u.tick(0) is True
    assert u.state == 20.0  # 23 - 3


def test_fire_emits_log_entry():
    print("=== Unit: fire emits a log entry ===")
    u = AutonomicUnit("world:u", "U", 22.0, 23.0,
                       correction_strength=3.0)
    u.tick(0)
    fire_entries = [e for e in u.log_since(None)
                     if e.kind == "fire"]
    assert len(fire_entries) == 1
    assert fire_entries[0].data["epoch"] == 0


def test_fires_based_on_own_state_only():
    """Two units with same state/target fire identically, regardless
    of any other unit's state."""
    print("=== Unit: firing depends on own state only ===")
    u1 = AutonomicUnit("world:u1", "U1", 22.0, 23.0,
                        correction_strength=3.0)
    u2 = AutonomicUnit("world:u2", "U2", 22.0, 23.0,
                        correction_strength=3.0)
    # Fire both
    assert u1.tick(0) is True
    assert u2.tick(0) is True
    # Now change u2's state, keep u1's
    u2.apply_external_heat(5.0)  # u2 now at 25
    # u1 fires iff its own state > target — u1 at 20, no fire
    assert u1.tick(1) is False
    # u2 fires — its own state is 25 > 22
    assert u2.tick(1) is True
    # The other unit's state doesn't affect a unit's decision


def test_no_shared_stream_attr():
    print("=== Unit: no shared env stream (vs C43) ===")
    u = AutonomicUnit("world:u", "U", 22.0, 20.0)
    assert not hasattr(u, "_env_stream")
    assert not hasattr(u, "_position")


def test_no_aggregate_threshold_attr():
    print("=== Unit: no aggregate threshold (vs C42) ===")
    u = AutonomicUnit("world:u", "U", 22.0, 20.0)
    assert not hasattr(u, "_inputs")
    assert not hasattr(u, "_threshold")


def test_no_intent_queue_attr():
    print("=== Unit: no intent queue (vs C41) ===")
    u = AutonomicUnit("world:u", "U", 22.0, 20.0)
    assert not hasattr(u, "_intent_queue")
    assert not hasattr(u, "_model")


def test_has_target_and_state():
    print("=== Unit: has target and state (unique to C47) ===")
    u = AutonomicUnit("world:u", "U", 22.0, 20.0)
    assert hasattr(u, "_target")
    assert hasattr(u, "_state")
    assert hasattr(u, "_correction_strength")


# =====================================================================
# modulate act
# =====================================================================

def test_modulate_changes_target():
    print("=== modulate: changes target, logs the change ===")
    u = AutonomicUnit("world:u", "U", 22.0, 20.0)
    r = u.act(Act(
        actor_token="ext", type="modulate",
        payload={"target": 20.0}))
    assert isinstance(r, Ack)
    assert u.target == 20.0
    mod_entries = [e for e in u.log_since(None)
                    if e.kind == "modulation"]
    assert len(mod_entries) == 1
    assert mod_entries[0].data["old_target"] == 22.0
    assert mod_entries[0].data["new_target"] == 20.0


def test_modulate_rejects_bad_payload():
    print("=== modulate: bad payload → Refusal ===")
    u = AutonomicUnit("world:u", "U", 22.0, 20.0)
    for bad in (None, "not a number", [], {}, [1, 2]):
        r = u.act(Act(
            actor_token="ext", type="modulate",
            payload={"target": bad}))
        assert isinstance(r, Refusal)
    # Original target unchanged
    assert u.target == 22.0


def test_modulate_rejects_missing_target():
    print("=== modulate: missing target field → Refusal ===")
    u = AutonomicUnit("world:u", "U", 22.0, 20.0)
    r = u.act(Act(
        actor_token="ext", type="modulate",
        payload={}))
    assert isinstance(r, Refusal)


def test_unknown_act_refused():
    print("=== Unit: unknown act type → Refusal ===")
    u = AutonomicUnit("world:u", "U", 22.0, 20.0)
    for bad in ("fire", "set_state", "anything"):
        r = u.act(Act(
            actor_token="ext", type=bad, payload={}))
        assert isinstance(r, Refusal)
        assert "refuses" in r.reason.lower()


def test_act_never_raises():
    print("=== Unit: act never raises on bad payloads ===")
    u = AutonomicUnit("world:u", "U", 22.0, 20.0)
    for bad in (None, {}, [], "abc", 5):
        r = u.act(Act(
            actor_token="ext", type="modulate",
            payload={"target": bad}))
        assert isinstance(r, Refusal)


# =====================================================================
# Network — no coupling
# =====================================================================

def _make_network_no_coupling(n_units=3):
    net = AutonomicNetwork()
    net.set_coupling_heat(0.0)
    units = {}
    for i in range(n_units):
        u = AutonomicUnit(
            entity_id=f"world:u{i}", name=f"U{i}",
            target=22.0, initial_state=20.0,
            correction_strength=3.0, ambient_drift=0.5)
        units[f"U{i}"] = u
    for name, u in units.items():
        net.add_unit(name, u)
    return net, units


def test_network_uncoupled_each_holds_own_line():
    """With no coupling, each unit cycles independently."""
    print("=== Network: uncoupled units each hold their line ===")
    net, units = _make_network_no_coupling(3)
    # Run 12 ticks
    for _ in range(12):
        net.run_epoch()
    # Each unit should have similar behavior (they started
    # identically and there's no coupling)
    states = [u.state for u in units.values()]
    # They drift together, so they should be identical
    assert len(set(states)) == 1
    # All states are within [target - correction, target + drift]
    for s in states:
        assert 19.0 <= s <= 23.0


def test_network_uncoupled_fire_cycles():
    """A single unit fires periodically under ambient drift."""
    print("=== Network: uncoupled fire cycles ===")
    net = AutonomicNetwork()
    net.set_coupling_heat(0.0)
    u = AutonomicUnit(
        "world:u", "U", 22.0, 20.0,
        correction_strength=3.0, ambient_drift=0.5)
    net.add_unit("U", u)
    fires = []
    for _ in range(20):
        r = net.run_epoch()
        fires.append(r.fires["U"])
    # Fires at least twice (20 ticks with 0.5 drift + 3 correction)
    assert sum(fires) >= 2


# =====================================================================
# Network — with coupling
# =====================================================================

def _make_coupled_network():
    """Three units in a line, uniform coupling."""
    net = AutonomicNetwork()
    net.set_coupling_heat(0.3)
    units = {}
    for i, name in enumerate(("A", "B", "C")):
        u = AutonomicUnit(
            entity_id=f"world:{name.lower()}", name=name,
            target=22.0, initial_state=20.0,
            correction_strength=3.0, ambient_drift=0.5)
        units[name] = u
    net.add_unit("A", units["A"], neighbors=["B"])
    net.add_unit("B", units["B"], neighbors=["A", "C"])
    net.add_unit("C", units["C"], neighbors=["B"])
    return net, units


def test_network_coupled_all_within_tolerance():
    """Coupled units still hold their lines (homeostasis survives
    coupling)."""
    print("=== Network: coupled units all within tolerance ===")
    net, units = _make_coupled_network()
    for _ in range(20):
        net.run_epoch()
    # Each unit's state within tolerance of target
    assert net.all_within_tolerance(tolerance=4.0)


def test_coupling_transfers_heat():
    """When A fires, B gets hotter."""
    print("=== Network: coupling transfers heat ===")
    net = AutonomicNetwork()
    net.set_coupling_heat(1.0)
    ua = AutonomicUnit("world:a", "A", 22.0, 23.0,
                        correction_strength=3.0,
                        ambient_drift=0.0)
    ub = AutonomicUnit("world:b", "B", 22.0, 20.0,
                        correction_strength=3.0,
                        ambient_drift=0.0)
    net.add_unit("A", ua, neighbors=["B"])
    net.add_unit("B", ub, neighbors=["A"])
    # A is above target, will fire; B won't
    r = net.run_epoch()
    assert r.fires["A"] is True
    assert r.fires["B"] is False
    # B's state increased from coupling
    assert ub.state > 20.0


# =====================================================================
# Modulation
# =====================================================================

def test_modulate_via_network():
    print("=== Network.modulate: changes unit target ===")
    net, units = _make_coupled_network()
    r = net.modulate("B", 20.0)
    assert isinstance(r, Ack)
    assert units["B"].target == 20.0


def test_modulate_unknown_unit():
    print("=== Network.modulate: unknown unit → Refusal ===")
    net, _ = _make_coupled_network()
    r = net.modulate("Z", 20.0)
    assert isinstance(r, Refusal)


def test_modulation_changes_fire_pattern():
    """Modulating a unit to a lower target makes it fire more."""
    print("=== Modulation: lower target → more fires ===")
    net, units = _make_coupled_network()
    # Run 5 ticks to establish pattern
    for _ in range(5):
        net.run_epoch()
    fires_before = sum(
        1 for e in units["B"].log_since(None)
        if e.kind == "fire")
    # Modulate B down
    net.modulate("B", 18.0)
    # Run 10 more ticks
    for _ in range(10):
        net.run_epoch()
    fires_after = sum(
        1 for e in units["B"].log_since(None)
        if e.kind == "fire")
    assert fires_after > fires_before


def test_modulation_does_not_change_others_targets():
    print("=== Modulation: only the modulated unit's target changes ===")
    net, units = _make_coupled_network()
    net.modulate("B", 18.0)
    assert units["B"].target == 18.0
    assert units["A"].target == 22.0
    assert units["C"].target == 22.0


# =====================================================================
# Structural claims
# =====================================================================

def test_all_five_architectures_same_substrate():
    """The substrate supports all five. Conformance is
    architecture-agnostic."""
    print("=== Five architectures, one substrate ===")
    from wcp_conformance import run_conformance
    from multiverse_c1 import create_identity
    from multiverse_c13 import KeyPair
    from multiverse_c41 import Arm
    from multiverse_c42 import RelayUnit, Stream, SignalWorld
    from multiverse_c43 import SwarmUnit
    from multiverse_c44 import (
        TriumvirateMember, QuorumRule,
    )

    class StubModel:
        def generate(self, prompt): return "x"

    # C41
    arm = Arm(
        name="a", world_id="world:a", dag_id="dag:a",
        model_backend=StubModel(),
        arm_report_kp=KeyPair.generate(),
        arm_report_identity=create_identity("r"),
        arm_dag_kp=KeyPair.generate(),
        arm_dag_identity=create_identity("d"))

    # C42
    stim = SignalWorld("world:s", "S")
    neuron = RelayUnit(
        "world:n", "N", [Stream(stim)], threshold=1.0)

    # C43
    env = SignalWorld("world:e", "E")
    swarm = SwarmUnit(
        entity_id="world:u", name="U",
        env_stream=Stream(env),
        initial_position=(0, 0),
        seed=0, sample_probability=0.0)

    # C44
    member = TriumvirateMember(
        entity_id="m", name="M",
        member_kp=KeyPair.generate(),
        decision_rule=lambda p: "yea")

    # C47
    autonomic = AutonomicUnit(
        "world:auto", "Auto", target=22.0, initial_state=20.0)

    for name, e in [
        ("C41 arm (octopus)", arm),
        ("C42 relay neuron", neuron),
        ("C43 swarm unit", swarm),
        ("C44 council member", member),
        ("C47 autonomic unit", autonomic),
    ]:
        assert run_conformance(e)["passed"], name
        print(f"  ✓ {name}")


def test_all_five_units_have_distinct_attrs():
    """No two units share the same distinguishing attribute set."""
    print("=== Five architectures, five distinct attr sets ===")
    from multiverse_c1 import create_identity
    from multiverse_c13 import KeyPair
    from multiverse_c41 import Arm
    from multiverse_c42 import RelayUnit, Stream, SignalWorld
    from multiverse_c43 import SwarmUnit
    from multiverse_c44 import TriumvirateMember

    class StubModel:
        def generate(self, prompt): return "x"

    arm = Arm(
        name="a", world_id="world:a", dag_id="dag:a",
        model_backend=StubModel(),
        arm_report_kp=KeyPair.generate(),
        arm_report_identity=create_identity("r"),
        arm_dag_kp=KeyPair.generate(),
        arm_dag_identity=create_identity("d"))
    stim = SignalWorld("world:s", "S")
    neuron = RelayUnit(
        "world:n", "N", [Stream(stim)], threshold=1.0)
    env = SignalWorld("world:e", "E")
    swarm = SwarmUnit(
        entity_id="world:u", name="U",
        env_stream=Stream(env),
        initial_position=(0, 0), seed=0)
    member = TriumvirateMember(
        entity_id="m", name="M",
        member_kp=KeyPair.generate(),
        decision_rule=lambda p: "yea")
    autonomic = AutonomicUnit(
        "world:auto", "Auto", target=22.0, initial_state=20.0)

    # Each has a distinguishing attr
    assert hasattr(arm, "_model") and hasattr(arm, "_intent_queue")
    assert hasattr(neuron, "_inputs") and hasattr(neuron, "_threshold")
    assert hasattr(swarm, "_env_stream") and hasattr(swarm, "_position")
    assert hasattr(member, "_decision_rule")
    assert hasattr(autonomic, "_target") and hasattr(autonomic, "_state")
    # And NOT each other's:
    assert not hasattr(autonomic, "_model")
    assert not hasattr(autonomic, "_inputs")
    assert not hasattr(autonomic, "_env_stream")
    assert not hasattr(autonomic, "_decision_rule")


# =====================================================================
# Never raises
# =====================================================================

def test_network_never_raises_on_weird_input():
    print("=== Network: never raises on weird input ===")
    net, _ = _make_coupled_network()
    # Modulate with absurd target
    r = net.modulate("A", 1e10)
    assert isinstance(r, Ack)
    r = net.modulate("A", -1e10)
    assert isinstance(r, Ack)


# =====================================================================
# EpochResult
# =====================================================================

def test_epoch_result_format():
    print("=== EpochResult: format is readable ===")
    net, _ = _make_coupled_network()
    r = net.run_epoch()
    text = r.format()
    assert "Epoch 0" in text
    assert "A:" in text
    assert "target=" in text


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: three compartments, modulation ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert len(audit["traces"]) == 14  # 6 + 8
    assert audit["final_all_within_tolerance"] is True
    assert audit["structural"]["no_shared_stream"] is True
    assert audit["structural"]["no_aggregate_threshold"] is True
    assert audit["structural"]["no_intent_queue"] is True
    assert audit["structural"]["has_own_target_and_state"] is True
    # Modulation at epoch 6 changed B's target to 20
    epoch_7 = audit["traces"][7]
    assert epoch_7["targets"]["B"] == 20.0
    assert epoch_7["targets"]["A"] == 22.0
    assert (tmp_path / "autonomic_demo.json").exists()


if __name__ == "__main__":
    test_unit_construction()
    test_unit_is_wcp_world()
    test_no_fire_below_target()
    test_fire_at_target_exactly_no_fire()
    test_fire_above_target()
    test_fire_emits_log_entry()
    test_fires_based_on_own_state_only()
    test_no_shared_stream_attr()
    test_no_aggregate_threshold_attr()
    test_no_intent_queue_attr()
    test_has_target_and_state()
    test_modulate_changes_target()
    test_modulate_rejects_bad_payload()
    test_modulate_rejects_missing_target()
    test_unknown_act_refused()
    test_act_never_raises()
    test_network_uncoupled_each_holds_own_line()
    test_network_uncoupled_fire_cycles()
    test_network_coupled_all_within_tolerance()
    test_coupling_transfers_heat()
    test_modulate_via_network()
    test_modulate_unknown_unit()
    test_modulation_changes_fire_pattern()
    test_modulation_does_not_change_others_targets()
    test_all_five_architectures_same_substrate()
    test_all_five_units_have_distinct_attrs()
    test_network_never_raises_on_weird_input()
    test_epoch_result_format()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
