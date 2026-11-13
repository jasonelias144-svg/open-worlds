import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c3 import Act, Ack, Refusal
from multiverse_c42 import SignalWorld
from multiverse_c52 import (
    EpidemicUnit, EpidemicNetwork, EpochResult, demo,
)


# =====================================================================
# Unit construction and accessors
# =====================================================================

def test_unit_construction():
    print("=== EpidemicUnit: construction ===")
    u = EpidemicUnit(
        "world:u", "U",
        contacts=["A", "B"], susceptibility=2)
    assert u.contacts == ["A", "B"]
    assert u.susceptibility == 2
    assert not u.has_heard("r1")
    assert not u.is_spreading("r1")


def test_unit_rejects_bad_susceptibility():
    print("=== EpidemicUnit: susceptibility must be >= 1 ===")
    with pytest.raises(ValueError):
        EpidemicUnit("world:u", "U", susceptibility=0)


def test_unit_is_wcp_world():
    print("=== EpidemicUnit: WCP shape + conformance ===")
    from wcp_conformance import run_conformance
    u = EpidemicUnit("world:u", "U")
    assert run_conformance(u)["passed"]


# =====================================================================
# Act handling
# =====================================================================

def test_act_infect_records_exposure():
    print("=== act('infect'): records exposure ===")
    u = EpidemicUnit("world:u", "U")
    r = u.act(Act(
        actor_token="src", type="infect",
        payload={"rumor_id": "r1", "source": "src"}))
    assert isinstance(r, Ack)
    assert u.has_heard("r1")
    assert u.exposures("r1") == {"src"}


def test_act_infect_multiple_sources_deduplicated():
    print("=== act('infect'): same source doesn't double-count ===")
    u = EpidemicUnit("world:u", "U")
    for _ in range(3):
        u.act(Act(actor_token="src", type="infect",
                  payload={"rumor_id": "r1",
                           "source": "src"}))
    assert u.exposures("r1") == {"src"}
    # But different sources count separately
    u.act(Act(actor_token="src2", type="infect",
              payload={"rumor_id": "r1", "source": "src2"}))
    assert u.exposures("r1") == {"src", "src2"}


def test_act_infect_rejects_bad_payload():
    print("=== act('infect'): bad payload → Refusal ===")
    u = EpidemicUnit("world:u", "U")
    for bad in (
        {"rumor_id": "", "source": "x"},
        {"rumor_id": "r1", "source": ""},
        {"rumor_id": "r1"},  # no source
        {"source": "x"},     # no rumor
        {},                  # empty
    ):
        r = u.act(Act(actor_token="src", type="infect",
                      payload=bad))
        assert isinstance(r, Refusal)


def test_act_unknown_type_refused():
    print("=== act: unknown type → Refusal ===")
    u = EpidemicUnit("world:u", "U")
    for t in ("fire", "spread", "expose", "bogus"):
        r = u.act(Act(actor_token="src", type=t, payload={}))
        assert isinstance(r, Refusal)


def test_act_never_raises():
    print("=== act: never raises ===")
    u = EpidemicUnit("world:u", "U")
    for bad in (None, "str", 5, [], {"x": 1}):
        r = u.act(Act(actor_token="src", type="infect",
                      payload=bad or {}))
        assert isinstance(r, Refusal)


# =====================================================================
# Tick — susceptibility behavior
# =====================================================================

def test_tick_below_susceptibility_no_spread():
    print("=== tick: below susceptibility → no spread ===")
    u = EpidemicUnit(
        "world:u", "U", contacts=["A", "B"], susceptibility=2)
    u.act(Act(actor_token="src", type="infect",
              payload={"rumor_id": "r1", "source": "src"}))
    # Only 1 exposure, susc=2 → no spreading
    pending = u.tick(0)
    assert pending == []
    assert not u.is_spreading("r1")


def test_tick_at_susceptibility_starts_spreading():
    print("=== tick: at susceptibility → starts spreading ===")
    u = EpidemicUnit(
        "world:u", "U", contacts=["A", "B"], susceptibility=2)
    u.act(Act(actor_token="s1", type="infect",
              payload={"rumor_id": "r1", "source": "s1"}))
    u.act(Act(actor_token="s2", type="infect",
              payload={"rumor_id": "r1", "source": "s2"}))
    pending = u.tick(0)
    assert u.is_spreading("r1")
    assert len(pending) == 2
    targets = {t for t, _ in pending}
    assert targets == {"A", "B"}


def test_tick_spreads_to_each_contact_once():
    print("=== tick: each contact told once ===")
    u = EpidemicUnit(
        "world:u", "U", contacts=["A", "B"], susceptibility=1)
    u.act(Act(actor_token="src", type="infect",
              payload={"rumor_id": "r1", "source": "src"}))
    first = u.tick(0)
    assert len(first) == 2  # A and B
    second = u.tick(1)
    assert second == []  # already told them
    third = u.tick(2)
    assert third == []


def test_tick_ignores_contacts_we_have_not_heard():
    """A unit with no exposures ticks to nothing."""
    print("=== tick: no exposures → no spread ===")
    u = EpidemicUnit(
        "world:u", "U", contacts=["A", "B"], susceptibility=1)
    assert u.tick(0) == []


def test_tick_handles_multiple_rumors_independently():
    print("=== tick: multiple rumors independent ===")
    u = EpidemicUnit(
        "world:u", "U", contacts=["A"], susceptibility=1)
    u.act(Act(actor_token="s", type="infect",
              payload={"rumor_id": "r1", "source": "s"}))
    u.act(Act(actor_token="s", type="infect",
              payload={"rumor_id": "r2", "source": "s"}))
    pending = u.tick(0)
    rumors = {rid for _, rid in pending}
    assert rumors == {"r1", "r2"}


# =====================================================================
# Network
# =====================================================================

def _build_chain(names, suscept=None):
    suscept = suscept or {n: 1 for n in names}
    net = EpidemicNetwork()
    for i, name in enumerate(names):
        contacts = []
        if i > 0:
            contacts.append(names[i - 1])
        if i < len(names) - 1:
            contacts.append(names[i + 1])
        net.add_unit(name, EpidemicUnit(
            entity_id=f"world:{name}", name=name,
            contacts=contacts,
            susceptibility=suscept.get(name, 1)))
    return net


def test_network_seed():
    print("=== Network: seed infects a unit ===")
    net = _build_chain(["A", "B", "C"])
    assert net.seed("A", "r1")
    assert net.unit_by_name("A").has_heard("r1")


def test_network_seed_unknown_unit():
    print("=== Network: seed unknown unit → False ===")
    net = _build_chain(["A"])
    assert not net.seed("Z", "r1")


def test_network_run_epoch_delivers():
    print("=== Network.run_epoch: delivers transmissions ===")
    net = _build_chain(["A", "B", "C"])
    net.seed("A", "r1")
    r = net.run_epoch()
    # A spreads to B; B isn't yet spreading (just got exposed)
    assert len(r.transmissions) == 1
    assert r.transmissions[0] == ("A", "B", "r1")


def test_network_run_until_quiet_full_chain():
    print("=== Network: full chain saturates ===")
    net = _build_chain(["A", "B", "C", "D", "E", "F"])
    net.seed("A", "r1")
    trace = net.run_until_quiet()
    reached, total, sat = net.saturation("r1")
    assert sat
    assert reached == 6


def test_network_broken_edge_stops_spread():
    print("=== Network: broken edge stops spread ===")
    net = EpidemicNetwork()
    # Chain with no D—E edge
    layout = {
        "A": ["B"], "B": ["A", "C"], "C": ["B", "D"],
        "D": ["C"],  # no E
        "E": ["F"], "F": ["E"],
    }
    for name, contacts in layout.items():
        net.add_unit(name, EpidemicUnit(
            entity_id=f"world:{name}", name=name,
            contacts=contacts, susceptibility=1))
    net.seed("A", "r1")
    net.run_until_quiet()
    reached, total, sat = net.saturation("r1")
    assert not sat
    assert "E" not in net.reached_by("r1")
    assert "F" not in net.reached_by("r1")


def test_network_skeptic_blocks():
    print("=== Network: skeptic at C blocks spread ===")
    # Chain A—B—C—D—E; C has susc=2 but only hears from B
    net = _build_chain(
        ["A", "B", "C", "D", "E"],
        suscept={"A": 1, "B": 1, "C": 2, "D": 1, "E": 1})
    net.seed("A", "r1")
    net.run_until_quiet()
    reached, total, sat = net.saturation("r1")
    assert not sat
    # C, D, E never hear the rumor
    reached_units = net.reached_by("r1")
    assert "C" not in reached_units
    assert "D" not in reached_units
    assert "E" not in reached_units
    # Only A and B heard it
    assert reached_units == ["A", "B"]


def test_network_isolated_subnets():
    print("=== Network: two isolated triangles never cross ===")
    net = EpidemicNetwork()
    for name, contacts in [
        ("A", ["B", "C"]), ("B", ["A", "C"]), ("C", ["A", "B"]),
        ("D", ["E", "F"]), ("E", ["D", "F"]), ("F", ["D", "E"]),
    ]:
        net.add_unit(name, EpidemicUnit(
            entity_id=f"world:{name}", name=name,
            contacts=contacts, susceptibility=1))
    net.seed("A", "r1")
    net.run_until_quiet()
    reached = net.reached_by("r1")
    # ABC heard it; DEF didn't
    assert set(reached) == {"A", "B", "C"}
    assert "D" not in reached
    assert "E" not in reached
    assert "F" not in reached


def test_network_terminates():
    """Every topology terminates (no infinite loops)."""
    print("=== Network: terminates even with cycles ===")
    net = EpidemicNetwork()
    # Complete graph on 4 nodes: A→B→A cycle
    names = ["A", "B", "C", "D"]
    for name in names:
        others = [n for n in names if n != name]
        net.add_unit(name, EpidemicUnit(
            entity_id=f"world:{name}", name=name,
            contacts=others, susceptibility=1))
    net.seed("A", "r1")
    trace = net.run_until_quiet(max_epochs=20)
    # Should terminate quickly (each unit tells each other once)
    assert len(trace) < 10
    reached, total, sat = net.saturation("r1")
    assert sat


# =====================================================================
# Structural distinctions from other architectures
# =====================================================================

def test_unit_has_contacts_not_streams():
    print("=== Unit: has contacts, not streams (vs C42) ===")
    u = EpidemicUnit(
        "world:u", "U", contacts=["A", "B"])
    assert hasattr(u, "_contacts")
    assert not hasattr(u, "_inputs")
    assert not hasattr(u, "_threshold")


def test_unit_has_no_shared_environment():
    print("=== Unit: no shared env (vs C43) ===")
    u = EpidemicUnit("world:u", "U", contacts=["A"])
    assert not hasattr(u, "_env_stream")
    assert not hasattr(u, "_position")


def test_unit_has_no_brain_attrs():
    print("=== Unit: no brain attrs (vs C41) ===")
    u = EpidemicUnit("world:u", "U", contacts=["A"])
    assert not hasattr(u, "_model")
    assert not hasattr(u, "_intent_queue")


def test_unit_has_no_vote_attrs():
    print("=== Unit: no vote attrs (vs C44) ===")
    u = EpidemicUnit("world:u", "U", contacts=["A"])
    assert not hasattr(u, "_decision_rule")


def test_unit_has_no_policy_attrs():
    print("=== Unit: no policy attrs (vs C50) ===")
    u = EpidemicUnit("world:u", "U", contacts=["A"])
    assert not hasattr(u, "_current_policy")
    assert not hasattr(u, "_policy_history")


def test_seven_architectures_same_substrate():
    print("=== Seven architectures, one substrate ===")
    from wcp_conformance import run_conformance
    from multiverse_c1 import create_identity
    from multiverse_c13 import KeyPair
    from multiverse_c41 import Arm
    from multiverse_c42 import (
        RelayUnit, Stream, SignalWorld,
    )
    from multiverse_c43 import SwarmUnit
    from multiverse_c44 import TriumvirateMember
    from multiverse_c47 import AutonomicUnit
    from multiverse_c50 import InstitutionalUnit, sign_policy, Clause

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
        initial_position=(0, 0), seed=0,
        sample_probability=0.0)
    member = TriumvirateMember(
        entity_id="m", name="M",
        member_kp=KeyPair.generate(),
        decision_rule=lambda p: "yea")
    autonomic = AutonomicUnit(
        "world:auto", "Auto", target=22.0,
        initial_state=20.0)
    author = create_identity("A")
    author_kp = KeyPair.generate()
    policy = sign_policy(
        "p", 1,
        [Clause("c1", {"field": "x", "op": "eq", "value": 1},
                "accept")],
        "reject", author, author_kp)
    institutional = InstitutionalUnit(
        "world:inst", "Inst", KeyPair.generate(), policy)
    epidemic = EpidemicUnit(
        "world:epi", "Epi", contacts=["A"], susceptibility=1)

    for name, e in [
        ("C41 arm", arm),
        ("C42 relay", neuron),
        ("C43 swarm", swarm),
        ("C44 council member", member),
        ("C47 autonomic", autonomic),
        ("C50 institutional", institutional),
        ("C52 epidemic", epidemic),
    ]:
        assert run_conformance(e)["passed"], name
        print(f"  ✓ {name}")


# =====================================================================
# EpochResult
# =====================================================================

def test_epoch_result_format():
    print("=== EpochResult: readable format ===")
    net = _build_chain(["A", "B", "C"])
    net.seed("A", "r1")
    r = net.run_epoch()
    text = r.format()
    assert "Epoch 0" in text
    assert "A → B" in text


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: four scenarios ===")
    audit = demo(artifact_dir=str(tmp_path))
    scenarios = {s["name"]: s for s in audit["scenarios"]}
    # A: full chain saturates
    assert scenarios["A_full_chain"]["saturated"] is True
    assert scenarios["A_full_chain"]["reached"] == 6
    # B: broken edge — E,F unreachable
    assert scenarios["B_broken_edge"]["saturated"] is False
    assert "E" not in scenarios["B_broken_edge"]["reached_units"]
    assert "F" not in scenarios["B_broken_edge"]["reached_units"]
    # C: skeptic blocks
    assert scenarios["C_skeptic"]["saturated"] is False
    assert "C" not in scenarios["C_skeptic"]["reached_units"]
    assert "D" not in scenarios["C_skeptic"]["reached_units"]
    # D: isolated subnets
    assert scenarios["D_isolated_subnets"]["saturated"] is False
    assert set(scenarios["D_isolated_subnets"]["reached_units"]) == {
        "A", "B", "C"}
    assert (tmp_path / "epidemic_demo.json").exists()


if __name__ == "__main__":
    test_unit_construction()
    test_unit_rejects_bad_susceptibility()
    test_unit_is_wcp_world()
    test_act_infect_records_exposure()
    test_act_infect_multiple_sources_deduplicated()
    test_act_infect_rejects_bad_payload()
    test_act_unknown_type_refused()
    test_act_never_raises()
    test_tick_below_susceptibility_no_spread()
    test_tick_at_susceptibility_starts_spreading()
    test_tick_spreads_to_each_contact_once()
    test_tick_ignores_contacts_we_have_not_heard()
    test_tick_handles_multiple_rumors_independently()
    test_network_seed()
    test_network_seed_unknown_unit()
    test_network_run_epoch_delivers()
    test_network_run_until_quiet_full_chain()
    test_network_broken_edge_stops_spread()
    test_network_skeptic_blocks()
    test_network_isolated_subnets()
    test_network_terminates()
    test_unit_has_contacts_not_streams()
    test_unit_has_no_shared_environment()
    test_unit_has_no_brain_attrs()
    test_unit_has_no_vote_attrs()
    test_unit_has_no_policy_attrs()
    test_seven_architectures_same_substrate()
    test_epoch_result_format()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
