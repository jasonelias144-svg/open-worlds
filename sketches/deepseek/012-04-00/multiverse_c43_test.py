import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c3 import Act, Ack, Refusal
from multiverse_c42 import SignalWorld, Stream, RelayUnit
from multiverse_c43 import SwarmUnit, SwarmNetwork, EpochResult, demo


# =====================================================================
# Helpers
# =====================================================================

def _make_environment():
    env = SignalWorld("world:env", "Env")
    return env, Stream(env, "env")


def _make_unit(name="ant-0", seed=42, position=(0, 0),
                env_stream=None, sample_probability=1.0):
    if env_stream is None:
        _, env_stream = _make_environment()
    return SwarmUnit(
        entity_id=f"world:{name}", name=name,
        env_stream=env_stream, initial_position=position,
        seed=seed, sample_probability=sample_probability,
        window_size=8)


def _make_network(n=5, food_target=(10, 10)):
    net = SwarmNetwork(food_target=food_target, max_epochs=30)
    for i in range(n):
        net.add_unit(f"ant-{i}", SwarmUnit(
            entity_id=f"world:ant-{i}", name=f"ant-{i}",
            env_stream=net.stream, initial_position=(i, i),
            seed=42 + i, sample_probability=1.0,
            window_size=8))
    return net


# =====================================================================
# Stream.window
# =====================================================================

def test_window_returns_last_n():
    print("=== Stream.window: last n entries ===")
    env, s = _make_environment()
    for i in range(5):
        env.emit("signal", float(i), {"i": i})
    assert [e.data["i"] for e in s.window(3)] == [2, 3, 4]


def test_window_order_preserved():
    print("=== Stream.window: order preserved ===")
    env, s = _make_environment()
    for i in range(4):
        env.emit("signal", 0.0, {"i": i})
    assert [e.data["i"] for e in s.window(2)] == [2, 3]


def test_window_does_not_advance_cursor():
    print("=== Stream.window: cursor unaffected ===")
    env, s = _make_environment()
    env.emit("signal", 1.0, {})
    env.emit("signal", 2.0, {})
    s.window(5)
    assert s.pending() == 2
    assert len(s.pull()) == 2


def test_window_larger_than_log():
    print("=== Stream.window: n > log size → whole log ===")
    env, s = _make_environment()
    env.emit("signal", 1.0, {})
    assert len(s.window(10)) == 1


def test_window_zero_or_negative():
    print("=== Stream.window: n<=0 → empty ===")
    env, s = _make_environment()
    env.emit("signal", 1.0, {})
    assert s.window(0) == []
    assert s.window(-1) == []


# =====================================================================
# SwarmUnit — shape and act handling
# =====================================================================

def test_unit_is_wcp_world():
    print("=== SwarmUnit: WCP shape + conformance ===")
    unit = _make_unit()
    for attr in ("manifest", "petition", "act", "log_since"):
        assert hasattr(unit, attr)
    from wcp_conformance import run_conformance
    assert run_conformance(unit)["passed"]


def test_unit_accepts_find_food():
    print("=== SwarmUnit: accepts 'find_food' ===")
    unit = _make_unit()
    r = unit.act(Act(
        actor_token="ext", type="find_food",
        payload={"location": [10, 10]}))
    assert isinstance(r, Ack)
    assert unit.known_food == (10, 10)


def test_unit_refuses_bad_find_food_payload():
    print("=== SwarmUnit: refuses bad find_food payload ===")
    unit = _make_unit()
    for bad in (None, [], [1], [1, 2, 3],
                ["a", "b"], 5, "abc", [None, None]):
        r = unit.act(Act(
            actor_token="ext", type="find_food",
            payload={"location": bad}))
        assert isinstance(r, Refusal)
    assert unit.known_food is None


def test_unit_refuses_unknown_act():
    print("=== SwarmUnit: refuses unknown act types ===")
    unit = _make_unit()
    r = unit.act(Act(
        actor_token="ext", type="bogus", payload={}))
    assert isinstance(r, Refusal)
    assert "refuses" in r.reason.lower()


# =====================================================================
# SwarmUnit — local behavior
# =====================================================================

def test_wander_without_food():
    print("=== Unit: wanders with no food signal ===")
    unit = _make_unit(position=(5, 5))
    unit.tick(0)
    assert unit.position != (5, 5)


def test_no_food_emission_when_wandering():
    print("=== Unit: no food trace when wandering ===")
    unit = _make_unit()
    unit.tick(0)
    assert not any(e.kind == "food-pheromone"
                    for e in unit.log_since(None))


def test_follows_food_trace():
    print("=== Unit: follows food trace in environment ===")
    env, s = _make_environment()
    env.emit("food-pheromone", 1.0,
             {"location": [10, 10], "origin": "world:other"})
    unit = _make_unit(env_stream=s)
    unit.tick(0)
    assert unit.position == (10, 10)


def test_emits_own_trace_when_following():
    print("=== Unit: emits own trace when following ===")
    env, s = _make_environment()
    env.emit("food-pheromone", 1.0,
             {"location": [10, 10], "origin": "world:other"})
    unit = _make_unit(env_stream=s)
    unit.tick(0)
    own = [e for e in unit.log_since(None)
           if e.kind == "food-pheromone"]
    assert len(own) == 1
    assert own[0].data["location"] == [10, 10]


def test_follows_most_recent_trace():
    print("=== Unit: follows most recent trace in window ===")
    env, s = _make_environment()
    env.emit("food-pheromone", 1.0,
             {"location": [5, 5], "origin": "world:a"})
    env.emit("food-pheromone", 1.0,
             {"location": [10, 10], "origin": "world:b"})
    unit = _make_unit(env_stream=s)
    unit.tick(0)
    assert unit.position == (10, 10)


def test_stays_at_food():
    print("=== Unit: stays at food once there ===")
    env, s = _make_environment()
    env.emit("food-pheromone", 1.0,
             {"location": [10, 10], "origin": "world:x"})
    unit = _make_unit(env_stream=s)
    unit.tick(0)
    unit.tick(1)
    assert unit.position == (10, 10)


def test_known_food_overrides_wandering():
    print("=== Unit: known_food → moves there without any trace ===")
    unit = _make_unit()
    unit.act(Act(
        actor_token="ext", type="find_food",
        payload={"location": [20, 20]}))
    unit.tick(0)
    assert unit.position == (20, 20)


# =====================================================================
# Anti-property: no privileged unit
# =====================================================================

def test_no_c41_brain_attrs():
    print("=== No C41 brain attrs on swarm unit ===")
    unit = _make_unit()
    for attr in ("_arms", "issue_intent", "receive_report"):
        assert not hasattr(unit, attr), attr


def test_no_c42_brain_attrs():
    print("=== No C42 brain attrs on swarm unit ===")
    unit = _make_unit()
    for attr in ("_inputs", "_threshold", "fires_by_aggregate_only"):
        assert not hasattr(unit, attr), attr


def test_no_muscle_attrs():
    print("=== No muscle attrs on swarm unit ===")
    unit = _make_unit()
    assert not hasattr(unit, "_out_kind")


def test_all_units_same_interface():
    print("=== All units have the same attribute set ===")
    net = _make_network()
    sets = set()
    for unit in net._units.values():
        sets.add(frozenset(
            a for a in dir(unit) if not a.startswith("__")))
    assert len(sets) == 1


# =====================================================================
# Convergence — the emergent property
# =====================================================================

def test_converges_from_one_find():
    print("=== Network: converges from one find_food ===")
    net = _make_network(n=5, food_target=(10, 10))
    net.unit_by_name("ant-0").act(Act(
        actor_token="ext", type="find_food",
        payload={"location": [10, 10]}))
    for _ in range(15):
        net.run_epoch()
        if net.converged():
            break
    assert net.converged()
    assert net.statistics()["units_at_food"] == 5


def test_no_find_no_food_trace():
    """Without a find_food act, no unit ever emits a food trace."""
    print("=== Network: no find_food → no food trace anywhere ===")
    net = _make_network(n=5, food_target=(10, 10))
    for _ in range(10):
        net.run_epoch()
    for unit in net._units.values():
        food = [e for e in unit.log_since(None)
                if e.kind == "food-pheromone"]
        assert food == []


def test_convergence_is_statistical():
    """Mid-run, some units at food, some not. No unit decides
    'converged' — it's an aggregate property."""
    print("=== Convergence is statistical (partial mid-run) ===")
    net = SwarmNetwork(food_target=(10, 10), max_epochs=30)
    for i in range(5):
        net.add_unit(f"ant-{i}", SwarmUnit(
            entity_id=f"world:ant-{i}", name=f"ant-{i}",
            env_stream=net.stream, initial_position=(i, i),
            seed=42 + i, sample_probability=0.5,
            window_size=8))
    net.unit_by_name("ant-0").act(Act(
        actor_token="ext", type="find_food",
        payload={"location": [10, 10]}))
    net.run_epoch()
    s = net.statistics()
    assert 1 <= s["units_at_food"] < 5
    assert not s["converged"]


def test_any_finder_works():
    """No unit is structurally privileged: any unit can be told
    about food, and the colony converges either way."""
    print("=== Any unit can be the finder ===")
    for finder_idx in range(5):
        name = f"ant-{finder_idx}"
        net = _make_network(n=5)
        net.unit_by_name(name).act(Act(
            actor_token="ext", type="find_food",
            payload={"location": [10, 10]}))
        for _ in range(15):
            net.run_epoch()
            if net.converged():
                break
        assert net.converged(), f"failed with finder={name}"


def test_removing_non_finder_still_converges():
    print("=== Removing a non-finder still converges ===")
    for removed in ("ant-1", "ant-2", "ant-3", "ant-4"):
        net = _make_network(n=5)
        net.remove_unit(removed)
        net.unit_by_name("ant-0").act(Act(
            actor_token="ext", type="find_food",
            payload={"location": [10, 10]}))
        for _ in range(15):
            net.run_epoch()
            if net.converged():
                break
        assert net.converged(), f"failed after removing {removed}"
        assert net.statistics()["total_units"] == 4


# =====================================================================
# Contrast with C41 / C42: structural differences
# =====================================================================

def test_vs_octopus_different_interface():
    print("=== Vs octopus: different interface ===")
    from multiverse_c41 import Arm
    from multiverse_c13 import KeyPair
    from multiverse_c1 import create_identity

    class StubModel:
        def generate(self, prompt): return "x"

    arm = Arm(
        name="a", world_id="world:a", dag_id="dag:a",
        model_backend=StubModel(),
        arm_report_kp=KeyPair.generate(),
        arm_report_identity=create_identity("r"),
        arm_dag_kp=KeyPair.generate(),
        arm_dag_identity=create_identity("d"))
    unit = _make_unit()
    # Octopus arm: model + intent queue
    assert hasattr(arm, "_model")
    assert hasattr(arm, "_intent_queue")
    # Swarm unit: neither; has shared env stream
    assert not hasattr(unit, "_model")
    assert not hasattr(unit, "_intent_queue")
    assert hasattr(unit, "_env_stream")
    assert not hasattr(arm, "_env_stream")


def test_vs_relay_shared_vs_private_stream():
    print("=== Vs relay: shared vs private stream ===")
    env, s = _make_environment()
    u1 = _make_unit(name="u1", env_stream=s)
    u2 = _make_unit(name="u2", env_stream=s)
    # Swarm: same stream object
    assert u1._env_stream is u2._env_stream

    from multiverse_c42 import SensoryNeuron
    stim = SignalWorld("world:stim", "Stim")
    r1 = SensoryNeuron("world:r1", "r1",
                        [Stream(stim)], threshold=1.0)
    r2 = SensoryNeuron("world:r2", "r2",
                        [Stream(stim)], threshold=1.0)
    # Relay: private input lists; the streams are distinct cursors
    assert r1._inputs is not r2._inputs
    assert r1._inputs[0] is not r2._inputs[0]


def test_three_architectures_same_substrate():
    """The substrate doesn't know which architecture is being built.
    All three pass the same WCP conformance test."""
    print("=== Same substrate: all three architectures conform ===")
    from wcp_conformance import run_conformance
    from multiverse_c41 import Arm
    from multiverse_c13 import KeyPair
    from multiverse_c1 import create_identity

    class StubModel:
        def generate(self, prompt): return "x"

    arm = Arm(
        name="a", world_id="world:a", dag_id="dag:a",
        model_backend=StubModel(),
        arm_report_kp=KeyPair.generate(),
        arm_report_identity=create_identity("r"),
        arm_dag_kp=KeyPair.generate(),
        arm_dag_identity=create_identity("d"))

    stim = SignalWorld("world:stim", "Stim")
    relay = RelayUnit(
        "world:relay", "Relay", [Stream(stim)], threshold=1.0)

    swarm = _make_unit()

    for name, e in [("arm", arm), ("relay", relay),
                    ("swarm", swarm)]:
        assert run_conformance(e)["passed"], name
    print("  ✓ arm (octopus, C41)")
    print("  ✓ relay neuron (C42)")
    print("  ✓ swarm unit (C43)")


# =====================================================================
# Honest limits
# =====================================================================

def test_no_pheromone_decay():
    """Old traces persist forever; a unit follows them regardless
    of age."""
    print("=== Honest limit: no pheromone decay ===")
    env, s = _make_environment()
    env.emit("food-pheromone", 1.0,
             {"location": [10, 10], "origin": "world:old"})
    unit = _make_unit(env_stream=s)
    unit.tick(0)
    assert unit.position == (10, 10)


def test_own_trace_keeps_unit_stable():
    """A unit that laid a food trace sees its own trace and stays
    put. This is what makes convergence stable."""
    print("=== Own trace → stability at food ===")
    net = _make_network(n=2, food_target=(10, 10))
    net.unit_by_name("ant-0").act(Act(
        actor_token="ext", type="find_food",
        payload={"location": [10, 10]}))
    for _ in range(10):
        net.run_epoch()
    assert net.converged()
    net.run_epoch()
    net.run_epoch()
    assert net.converged()


# =====================================================================
# Never raises
# =====================================================================

def test_act_never_raises():
    print("=== SwarmUnit.act: never raises ===")
    unit = _make_unit()
    for bad in (None, {}, [], "abc", 5, [None, None]):
        r = unit.act(Act(
            actor_token="ext", type="find_food",
            payload={"location": bad}))
        assert isinstance(r, Refusal)


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: 5 ants, one finder, converges ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["finder"] == "ant-0"
    assert audit["target"] == [10, 10]
    assert audit["final_statistics"]["converged"] is True
    assert (tmp_path / "swarm_demo.json").exists()


def test_demo_with_different_finder(tmp_path):
    print("=== Demo: finder=ant-3 (any unit can be finder) ===")
    audit = demo(
        artifact_dir=str(tmp_path),
        finder_name="ant-3")
    assert audit["finder"] == "ant-3"
    assert audit["final_statistics"]["converged"] is True


if __name__ == "__main__":
    test_window_returns_last_n()
    test_window_order_preserved()
    test_window_does_not_advance_cursor()
    test_window_larger_than_log()
    test_window_zero_or_negative()
    test_unit_is_wcp_world()
    test_unit_accepts_find_food()
    test_unit_refuses_bad_find_food_payload()
    test_unit_refuses_unknown_act()
    test_wander_without_food()
    test_no_food_emission_when_wandering()
    test_follows_food_trace()
    test_emits_own_trace_when_following()
    test_follows_most_recent_trace()
    test_stays_at_food()
    test_known_food_overrides_wandering()
    test_no_c41_brain_attrs()
    test_no_c42_brain_attrs()
    test_no_muscle_attrs()
    test_all_units_same_interface()
    test_converges_from_one_find()
    test_no_find_no_food_trace()
    test_convergence_is_statistical()
    test_any_finder_works()
    test_removing_non_finder_still_converges()
    test_vs_octopus_different_interface()
    test_vs_relay_shared_vs_private_stream()
    test_three_architectures_same_substrate()
    test_no_pheromone_decay()
    test_own_trace_keeps_unit_stable()
    test_act_never_raises()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_demo_with_different_finder(Path(tmp))
