# multiverse_c42_test.py
import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c3 import (
    Petition, Act, LogEntry, Admission, Refusal, Ack,
)
from multiverse_c42 import (
    SignalWorld, Stream, StimulusWorld,
    RelayUnit, SensoryNeuron, Interneuron, Brain, Muscle,
    RelayEpoch, RelayNetwork, demo,
)


# =====================================================================
# SignalWorld — WCP shape
# =====================================================================

def test_signalworld_manifest_shape():
    print("=== SignalWorld: WCP manifest shape ===")
    w = SignalWorld("world:sig", "Sig")
    m = w.manifest()
    assert m.entity_id == "world:sig"
    assert m.protocol_version == "WCP/0.1"
    assert m.sub_registry_endpoint is None


def test_signalworld_petition_works():
    print("=== SignalWorld: petition admitted ===")
    w = SignalWorld("world:sig", "Sig")
    r = w.petition(Petition(
        petitioner_token="reader-1", petitioner_name="Reader",
        passport_admissions=(), message="subscribe"))
    assert isinstance(r, Admission)


def test_signalworld_act_refused():
    print("=== SignalWorld: act refused (readers only) ===")
    w = SignalWorld("world:sig", "Sig")
    r = w.act(Act(
        actor_token="x", type="anything", payload={}))
    assert isinstance(r, Refusal)
    assert "do not accept" in r.reason


def test_signalworld_log_shape():
    print("=== SignalWorld: log entries well-formed ===")
    w = SignalWorld("world:sig", "Sig")
    w.petition(Petition(
        petitioner_token="r", petitioner_name="R",
        passport_admissions=(), message="sub"))
    w.emit("signal", 3.0, {"origin": "world:sig", "epoch": 0})
    log = w.log_since(None)
    assert len(log) == 2
    assert log[0].kind == "admission"
    assert log[1].kind == "signal"
    assert log[1].data["weight"] == 3.0


def test_signalworld_passes_wcp_conformance():
    print("=== SignalWorld passes WCP/0.1 conformance ===")
    from wcp_conformance import run_conformance
    w = SignalWorld("world:sig", "Sig")
    result = run_conformance(w)
    assert result["passed"], result["failures"]


# =====================================================================
# StimulusWorld
# =====================================================================

def test_stimulus_accepts_stimulus_act():
    print("=== StimulusWorld: 'stimulus' act appends entry ===")
    w = StimulusWorld("world:stim", "Stim")
    r = w.act(Act(
        actor_token="driver", type="stimulus",
        payload={"weight": 5.0}))
    assert isinstance(r, Ack)
    log = w.log_since(None)
    assert any(e.kind == "stimulus" and e.data["weight"] == 5.0
                for e in log)


def test_stimulus_refuses_unknown_act():
    print("=== StimulusWorld: unknown act refused ===")
    w = StimulusWorld("world:stim", "Stim")
    r = w.act(Act(
        actor_token="driver", type="bogus", payload={}))
    assert isinstance(r, Refusal)


# =====================================================================
# Stream
# =====================================================================

def test_stream_pull_advances_cursor():
    print("=== Stream: pull returns new entries only ===")
    w = SignalWorld("world:s", "S")
    w.emit("signal", 1.0, {"origin": "s"})
    w.emit("signal", 2.0, {"origin": "s"})
    s = Stream(w)
    first = s.pull()
    assert len(first) == 2
    second = s.pull()
    assert len(second) == 0
    w.emit("signal", 3.0, {"origin": "s"})
    third = s.pull()
    assert len(third) == 1
    assert third[0].data["weight"] == 3.0


def test_stream_pending():
    print("=== Stream.pending: count of unread entries ===")
    w = SignalWorld("world:s", "S")
    s = Stream(w)
    assert s.pending() == 0
    w.emit("signal", 1.0, {})
    w.emit("signal", 1.0, {})
    assert s.pending() == 2
    s.pull()
    assert s.pending() == 0


# =====================================================================
# SensoryNeuron / RelayUnit — threshold behavior
# =====================================================================

def _stim_with(weight: float) -> StimulusWorld:
    w = StimulusWorld("world:stim", "Stim")
    w.act(Act(actor_token="d", type="stimulus",
              payload={"weight": weight}))
    return w


def test_neuron_below_threshold_no_fire():
    print("=== Neuron: below threshold → no fire ===")
    stim = _stim_with(3.0)
    n = SensoryNeuron(
        "world:n", "N", [Stream(stim)], threshold=4.0)
    fired = n.tick(epoch=0)
    assert fired is False
    # No signal emitted
    assert not any(e.kind == "signal" for e in n.log_since(None))


def test_neuron_at_threshold_fires():
    print("=== Neuron: at threshold → fires ===")
    stim = _stim_with(4.0)
    n = SensoryNeuron(
        "world:n", "N", [Stream(stim)], threshold=4.0)
    fired = n.tick(epoch=0)
    assert fired is True
    assert any(e.kind == "signal" for e in n.log_since(None))


def test_neuron_above_threshold_fires():
    print("=== Neuron: above threshold → fires ===")
    stim = _stim_with(10.0)
    n = SensoryNeuron(
        "world:n", "N", [Stream(stim)], threshold=4.0)
    assert n.tick(epoch=0) is True


def test_neuron_adds_across_streams():
    print("=== Neuron: sums across multiple input streams ===")
    stim1 = _stim_with(2.0)
    stim2 = _stim_with(3.0)
    n = SensoryNeuron(
        "world:n", "N",
        [Stream(stim1), Stream(stim2)], threshold=5.0)
    assert n.tick(epoch=0) is True


def test_interneuron_composes():
    print("=== Interneuron: a neuron whose inputs are neurons ===")
    stim = _stim_with(4.0)
    sensory = SensoryNeuron(
        "world:s", "S", [Stream(stim)], threshold=4.0)
    inter = Interneuron(
        "world:i", "I", [Stream(sensory)], threshold=1.0)
    sensory.tick(epoch=0)
    fired = inter.tick(epoch=0)
    assert fired is True


# =====================================================================
# Brain — aggregation, origin-agnostic decision
# =====================================================================

def _neuron_fired(name: str) -> SignalWorld:
    w = SignalWorld(f"world:{name}", name)
    w.emit("signal", 1.0, {"origin": f"world:{name}"})
    return w


def test_brain_fires_when_aggregate_crosses():
    print("=== Brain: fires when aggregate crosses threshold ===")
    n1 = _neuron_fired("n1")
    n2 = _neuron_fired("n2")
    b = Brain(
        "world:brain", "B",
        [Stream(n1), Stream(n2)], threshold=2.0)
    assert b.tick(epoch=0) is True


def test_brain_does_not_fire_below_threshold():
    print("=== Brain: below threshold → no fire ===")
    n1 = _neuron_fired("n1")
    b = Brain(
        "world:brain", "B",
        [Stream(n1)], threshold=2.0)
    assert b.tick(epoch=0) is False


def test_brain_records_origins_for_audit():
    print("=== Brain: records origins for audit (not for branching) ===")
    n1 = _neuron_fired("n1")
    n2 = _neuron_fired("n2")
    b = Brain(
        "world:brain", "B",
        [Stream(n1), Stream(n2)], threshold=1.0)
    b.tick(epoch=0)
    motor = [e for e in b.log_since(None) if e.kind == "motor"][0]
    assert sorted(motor.data["origins_contributing"]) == [
        "world:n1", "world:n2"]


def test_brain_does_not_branch_on_origin():
    """The brain's decision depends only on total weight, not on
    which origins contributed. Two entries from the same origin and
    two from different origins produce the same result.
    """
    print("=== Brain: decision is origin-agnostic ===")
    e_a = LogEntry(
        timestamp="t1", kind="signal",
        actor_token="a",
        data={"weight": 1.0, "origin": "origin-a"})
    e_b = LogEntry(
        timestamp="t2", kind="signal",
        actor_token="b",
        data={"weight": 1.0, "origin": "origin-b"})
    e_a2 = LogEntry(
        timestamp="t3", kind="signal",
        actor_token="a2",
        data={"weight": 1.0, "origin": "origin-a"})
    b = Brain(
        "world:brain", "B", [], threshold=2.0)
    # Case 1: two entries, different origins
    fires_diff = b.fires_by_aggregate_only(
        epoch=0, entries=[e_a, e_b])
    # Case 2: two entries, same origin
    fires_same = b.fires_by_aggregate_only(
        epoch=0, entries=[e_a, e_a2])
    # Case 3: one entry with weight 2
    e_double = LogEntry(
        timestamp="t4", kind="signal",
        actor_token="z",
        data={"weight": 2.0, "origin": "origin-z"})
    fires_one = b.fires_by_aggregate_only(
        epoch=0, entries=[e_double])
    assert fires_diff == fires_same == fires_one is True


# =====================================================================
# Muscle
# =====================================================================

def test_muscle_contracts_on_motor():
    print("=== Muscle: contracts when motor fires ===")
    b = SignalWorld("world:brain", "B")
    b.emit("motor", 3.0, {"origin": "world:brain"})
    m = Muscle(
        "world:muscle", "M", Stream(b), threshold=1.0)
    assert m.tick(epoch=0) is True
    assert any(e.kind == "contraction"
               for e in m.log_since(None))


def test_muscle_rests_without_motor():
    print("=== Muscle: at rest when no motor ===")
    b = SignalWorld("world:brain", "B")
    m = Muscle(
        "world:muscle", "M", Stream(b), threshold=1.0)
    assert m.tick(epoch=0) is False


# =====================================================================
# RelayNetwork
# =====================================================================

def _build_simple_network():
    stim = StimulusWorld("world:stim", "Stim")
    a = SensoryNeuron(
        "world:a", "A", [Stream(stim)], threshold=4.0)
    b_brain = Brain(
        "world:brain", "B", [Stream(a)], threshold=1.0)
    m = Muscle(
        "world:muscle", "M", Stream(b_brain), threshold=1.0)
    net = RelayNetwork()
    net.add("a", a)
    net.add("brain", b_brain)
    net.add("muscle", m)
    return net, stim, a, b_brain, m


def test_network_epoch_no_stimulus():
    print("=== Network: no stimulus → muscle at rest ===")
    net, stim, a, brain, m = _build_simple_network()
    e = net.run_epoch()
    assert e.muscle_contracted is False
    assert all(f is False for f in e.fires.values())


def test_network_epoch_with_stimulus():
    print("=== Network: stimulus above threshold → muscle contracts ===")
    net, stim, a, brain, m = _build_simple_network()
    stim.act(Act(actor_token="d", type="stimulus",
                  payload={"weight": 5.0}))
    e = net.run_epoch()
    assert e.fires["a"] is True
    assert e.fires["brain"] is True
    assert e.fires["muscle"] is True
    assert e.muscle_contracted is True


def test_network_second_epoch_does_not_refire():
    """After firing, subsequent epochs with no new stimulus don't
    re-fire, because the streams have been drained."""
    print("=== Network: no re-fire without new stimulus ===")
    net, stim, a, brain, m = _build_simple_network()
    stim.act(Act(actor_token="d", type="stimulus",
                  payload={"weight": 5.0}))
    e1 = net.run_epoch()
    assert e1.muscle_contracted is True
    e2 = net.run_epoch()
    assert e2.muscle_contracted is False


def test_network_add_neuron_is_local():
    """Adding a neuron to the network only requires adding a new
    input stream to the brain. The brain's logic is unchanged."""
    print("=== Network: adding a neuron is local ===")
    net, stim, a, brain, m = _build_simple_network()
    # Add neuron B, feeding the same brain
    b = SensoryNeuron(
        "world:b", "B", [Stream(stim)], threshold=6.0)
    net.add("b", b)
    brain.add_input_stream(Stream(b))
    # Now stimulate above B's threshold, but below A's
    stim.act(Act(actor_token="d", type="stimulus",
                  payload={"weight": 5.0}))
    e = net.run_epoch()
    # A doesn't fire (5 < 4? no, 5 >= 4, A fires), B doesn't
    # (5 < 6). Brain sees A's fire → motor → muscle
    assert e.fires["a"] is True
    assert e.fires["b"] is False
    assert e.muscle_contracted is True


# =====================================================================
# The distinguishing property vs. C41 (octopus)
# =====================================================================

def test_brain_has_no_arm_list():
    """The octopus brain has a per-arm intent interface (issue_intent,
    receive_report). The relay brain has input streams. Structurally
    different; the same substrate supports both."""
    print("=== Distinguishable from octopus: no arm list ===")
    b = Brain("world:brain", "B", [], threshold=1.0)
    assert not hasattr(b, "_arms")
    assert not hasattr(b, "issue_intent")
    assert not hasattr(b, "receive_report")
    # It has input streams (a cursor list), by contrast
    assert hasattr(b, "_inputs")
    print("  relay brain: has _inputs (Stream cursors)")
    print("  relay brain: no issue_intent, no per-arm identity")


def test_octopus_and_relay_same_substrate():
    """Both the octopus (C41) and the relay (C42) use worlds that
    satisfy WCP. Neither required new primitives."""
    print("=== Same substrate: both pass WCP conformance ===")
    from wcp_conformance import run_conformance
    # SignalWorld passes (test above); but so did the C41 arms
    # and brain — same shape. Confirm by checking the WCP
    # interface.
    b = Brain("world:brain", "B", [], threshold=1.0)
    for attr in ("manifest", "petition", "act", "log_since"):
        assert hasattr(b, attr)
    result = run_conformance(b)
    assert result["passed"], result["failures"]


# =====================================================================
# Never raises
# =====================================================================

def test_tick_never_raises():
    print("=== RelayUnit.tick: never raises on bad streams ===")
    class BadWorld:
        def manifest(self):
            class M:
                entity_id = "bad"
            return M()
        def log_since(self, since):
            raise RuntimeError("boom")
    n = SensoryNeuron(
        "world:n", "N", [Stream(BadWorld())], threshold=1.0)
    # Stream.pull will propagate the exception; the unit's tick
    # propagates it. This is a prototype-level behavior — a
    # production version would catch per-stream and continue.
    # Document the honest limit; assert current behavior.
    with pytest.raises(RuntimeError):
        n.tick(epoch=0)


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: stimulus → neuron → brain → muscle ===")
    audit = demo(artifact_dir=str(tmp_path))
    # Epoch 0: no stimulus, nothing fires
    assert audit["epochs"][0]["muscle_contracted"] is False
    # Epoch 1: stimulus 5 → A fires, B not, brain, muscle
    assert audit["epochs"][1]["fires"]["neuron-a"] is True
    assert audit["epochs"][1]["fires"]["neuron-b"] is False
    assert audit["epochs"][1]["muscle_contracted"] is True
    # Epoch 2: no stimulus, nothing fires
    assert audit["epochs"][2]["muscle_contracted"] is False
    # Epoch 3: stimulus 8 → both fire, muscle contracts
    assert audit["epochs"][3]["fires"]["neuron-a"] is True
    assert audit["epochs"][3]["fires"]["neuron-b"] is True
    assert audit["epochs"][3]["muscle_contracted"] is True
    assert (tmp_path / "relay_demo.json").exists()


if __name__ == "__main__":
    test_signalworld_manifest_shape()
    test_signalworld_petition_works()
    test_signalworld_act_refused()
    test_signalworld_log_shape()
    test_signalworld_passes_wcp_conformance()
    test_stimulus_accepts_stimulus_act()
    test_stimulus_refuses_unknown_act()
    test_stream_pull_advances_cursor()
    test_stream_pending()
    test_neuron_below_threshold_no_fire()
    test_neuron_at_threshold_fires()
    test_neuron_above_threshold_fires()
    test_neuron_adds_across_streams()
    test_interneuron_composes()
    test_brain_fires_when_aggregate_crosses()
    test_brain_does_not_fire_below_threshold()
    test_brain_records_origins_for_audit()
    test_brain_does_not_branch_on_origin()
    test_muscle_contracts_on_motor()
    test_muscle_rests_without_motor()
    test_network_epoch_no_stimulus()
    test_network_epoch_with_stimulus()
    test_network_second_epoch_does_not_refire()
    test_network_add_neuron_is_local()
    test_brain_has_no_arm_list()
    test_octopus_and_relay_same_substrate()
    test_tick_never_raises()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
