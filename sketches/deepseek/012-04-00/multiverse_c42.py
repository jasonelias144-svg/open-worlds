"""
multiverse_c42.py — Component 42: The Relay Pattern.

CNS/PNS as a demonstration that the substrate supports a
fundamentally different unit type than the octopus:

  Octopus unit:      Executor  — has a model, produces output,
                                 pushed by brain intent
  Relay unit:        Relay     — has thresholds, fires on input
                                 aggregate, pulled by a reader

The infrastructure provides:
  - SignalWorld: a WCP entity that logs signals (subclass of nothing
                 — just a small base)
  - Stream: a cursor over any world's log

Everything else — SensoryNeuron, Brain, Muscle, Interneuron — is
built by composing those two. The user writes the neurons; the
infrastructure supplies the primitives.

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: stream cursor, threshold fire/not-fire,
    brain origin-agnostic decision, muscle causal chain,
    end-to-end, conformance.
  - "A world never raises on what a visitor sends" — SignalWorld
    refuses acts; verifiers return verdicts.
  - "History, not rank" — signals are records, not scores.
  - "Infrastructure open enough to accommodate architectures
    we cannot imagine yet" — the pattern is user-supplied, not
    infrastructure-supplied.

Honest limits (documented, tested):
  - Stream pull is O(total log). Production would use a
    sequence-number cursor; the prototype uses index cursors
    over log_since(None).
  - No concurrency: epoch is serial. Same as C41.
  - SignalWorld admits readers without verifying their key.
    Reading a log is free — same as any observability pattern.
  - The Brain's aggregation is trivial (sum, threshold). The
    pattern is what's demonstrated, not the rule.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from multiverse_c3 import (
    Manifest, Petition, Act, LogEntry,
    Admission as WCPAdmission, Refusal, Ack,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# =====================================================================
# SignalWorld — a WCP entity whose log holds signals
# =====================================================================

class SignalWorld:
    """A WCP entity whose log carries signals.

    Satisfies WCP: manifest, petition, act, log_since.
    Refuses external acts — signals are produced by tick(), not
    by external command. (Being a world doesn't require accepting
    acts; a world that says "no" is still a world.)

    Petitions are accepted so a reader can be logged as having
    subscribed. Reading the log itself requires no petition —
    same as any observability pattern.
    """

    def __init__(self, entity_id: str, name: str):
        self._manifest = Manifest(
            entity_id=entity_id, name=name,
            protocol_version="WCP/0.1",
            law_url=f"signal://{entity_id}/law",
            act_endpoint=f"signal://{entity_id}/act",
            log_endpoint=f"signal://{entity_id}/log",
            sub_registry_endpoint=None,
        )
        self._log: List[LogEntry] = []

    def manifest(self) -> Manifest:
        return self._manifest

    def petition(self, petition: Petition):
        ts = _now()
        self._log.append(LogEntry(
            timestamp=ts, kind="admission",
            actor_token=petition.petitioner_token,
            data={"name": petition.petitioner_name},
        ))
        return WCPAdmission(
            entity_id=self._manifest.entity_id, timestamp=ts)

    def act(self, act: Act):
        return Refusal(
            reason="signal worlds do not accept external acts")

    def log_since(self, since: Optional[str] = None):
        if since is None:
            return list(self._log)
        return [e for e in self._log if e.timestamp > since]

    def emit(self, kind: str, weight: float,
             content: Dict) -> LogEntry:
        entry = LogEntry(
            timestamp=_now(), kind=kind,
            actor_token=self._manifest.entity_id,
            data={"weight": weight, **content},
        )
        self._log.append(entry)
        return entry


# =====================================================================
# Stream — a cursor over any world's log
# =====================================================================

class Stream:
    """A cursor over a world's log. Pull returns new entries."""

    def __init__(self, world, name: str = ""):
        self._world = world
        self._name = name or world.manifest().entity_id
        self._last_index = 0

    @property
    def name(self) -> str:
        return self._name

    def pull(self) -> List[LogEntry]:
        all_entries = self._world.log_since(None)
        new = all_entries[self._last_index:]
        self._last_index = len(all_entries)
        return new

    def pending(self) -> int:
        return len(self._world.log_since(None)) - self._last_index


# =====================================================================
# Stimulus — external input source
# =====================================================================

class StimulusWorld(SignalWorld):
    """A source of external stimuli. Accepts 'stimulus' acts."""

    def act(self, act: Act):
        if act.type != "stimulus":
            return Refusal(reason=f"Unknown act type: {act.type}")
        ts = _now()
        weight = act.payload.get("weight", 1)
        origin = act.payload.get("origin", self._manifest.entity_id)
        self._log.append(LogEntry(
            timestamp=ts, kind="stimulus",
            actor_token=act.actor_token,
            data={"weight": weight,
                  "origin": origin,
                  "kind": act.payload.get("kind", "generic")},
        ))
        return Ack(entity_id=self._manifest.entity_id, timestamp=ts)


# =====================================================================
# Neurons, Brain, Muscle — user-supplied composition
# =====================================================================

class RelayUnit(SignalWorld):
    """A unit with input streams and a threshold.

    Fires (emits a signal) if the sum of new input weights since
    last tick >= threshold. Never raises.
    """

    def __init__(self, entity_id: str, name: str,
                 input_streams: List[Stream], threshold: float,
                 out_kind: str = "signal"):
        super().__init__(entity_id, name)
        self._inputs = list(input_streams)
        self._threshold = threshold
        self._out_kind = out_kind

    def add_input_stream(self, stream: Stream) -> None:
        self._inputs.append(stream)

    def tick(self, epoch: int) -> bool:
        total = 0.0
        origins = set()
        for s in self._inputs:
            for e in s.pull():
                total += float(e.data.get("weight", 0))
                o = e.data.get("origin")
                if o:
                    origins.add(o)
        if total >= self._threshold:
            self.emit(self._out_kind, total, {
                "origin": self._manifest.entity_id,
                "origins_contributing": sorted(origins),
                "epoch": epoch,
            })
            return True
        return False


class SensoryNeuron(RelayUnit):
    """A sensory neuron: input streams are stimuli; fires a signal."""
    pass


class Interneuron(RelayUnit):
    """An interneuron: input streams are neuron signals; fires a signal."""
    pass


class Brain(RelayUnit):
    """A brain: aggregator over neuron signals; fires motor."""

    def __init__(self, entity_id: str, name: str,
                 input_streams: List[Stream], threshold: float):
        super().__init__(
            entity_id, name, input_streams, threshold,
            out_kind="motor")

    def fires_by_aggregate_only(self, epoch: int,
                                 entries: List[LogEntry]) -> bool:
        """A read-only variant of tick() used by tests to show
        the brain's decision depends only on aggregate weight,
        not on which origin contributed.
        """
        total = sum(float(e.data.get("weight", 0)) for e in entries)
        return total >= self._threshold


class Muscle(RelayUnit):
    """A muscle: contracts when the motor aggregate crosses threshold."""

    def __init__(self, entity_id: str, name: str,
                 brain_stream: Stream, threshold: float):
        super().__init__(
            entity_id, name, [brain_stream], threshold,
            out_kind="contraction")


# =====================================================================
# RelayNetwork — wires it together
# =====================================================================

@dataclass
class RelayEpoch:
    epoch: int
    fires: Dict[str, bool]
    muscle_contracted: bool

    def format(self) -> str:
        fired = [name for name, f in self.fires.items() if f]
        quiet = [name for name, f in self.fires.items() if not f]
        lines = [f"Epoch {self.epoch}"]
        if fired:
            lines.append(f"  fired:      {', '.join(fired)}")
        if quiet:
            lines.append(f"  quiet:      {', '.join(quiet)}")
        lines.append(
            f"  muscle:     "
            f"{'contracted' if self.muscle_contracted else 'at rest'}")
        return "\n".join(lines)


class RelayNetwork:
    """A network of relay units. Runs epochs serially."""

    def __init__(self):
        self._units: Dict[str, RelayUnit] = {}
        self._order: List[str] = []
        self._epoch = 0

    def add(self, name: str, unit: RelayUnit) -> None:
        """Register a unit. `name` is for the network's bookkeeping
        — units do not receive it in tick() and cannot branch on
        it, by design."""
        self._units[name] = unit
        self._order.append(name)

    def remove(self, name: str) -> None:
        self._units.pop(name, None)
        self._order = [n for n in self._order if n != name]

    def run_epoch(self) -> RelayEpoch:
        epoch = self._epoch
        self._epoch += 1
        fires: Dict[str, bool] = {}
        muscle_contracted = False
        # Order matters for causality within an epoch (neurons
        # before brain before muscle); see demo for wiring.
        for name in self._order:
            unit = self._units[name]
            fired = unit.tick(epoch)
            fires[name] = fired
            if isinstance(unit, Muscle) and fired:
                muscle_contracted = True
        return RelayEpoch(
            epoch=epoch, fires=fires,
            muscle_contracted=muscle_contracted)


# =====================================================================
# Demo — stimulus → sensory → brain → muscle
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Two sensory neurons (thresholds 4 and 6), one brain
    (threshold 1), one muscle (threshold 1). Stimulus weights
    drive the chain.

    Epoch 0: no stimulus → nothing fires
    Epoch 1: stimulus 5   → neuron-A fires, neuron-B not, brain
                             fires, muscle contracts
    Epoch 2: no stimulus  → nothing fires
    Epoch 3: stimulus 8   → both fire, brain fires, muscle contracts

    Anchor: Emily Dickinson, 'The Brain – is wider than the Sky –'
    (continues the C41 anchor — same poem, different architecture
    of the same line).
    """
    import json
    from pathlib import Path
    from multiverse_c3 import Act

    # Infrastructure: SignalWorlds that will hold the chain
    stimulus = StimulusWorld("world:stimulus", "Stimulus")
    neuron_a = SensoryNeuron(
        "world:neuron-a", "Sensory-A",
        input_streams=[Stream(stimulus, "stim→a")],
        threshold=4.0)
    neuron_b = SensoryNeuron(
        "world:neuron-b", "Sensory-B",
        input_streams=[Stream(stimulus, "stim→b")],
        threshold=6.0)
    brain = Brain(
        "world:brain", "Brain",
        input_streams=[
            Stream(neuron_a, "a→brain"),
            Stream(neuron_b, "b→brain"),
        ],
        threshold=1.0)
    muscle = Muscle(
        "world:muscle", "Muscle",
        brain_stream=Stream(brain, "brain→muscle"),
        threshold=1.0)

    net = RelayNetwork()
    net.add("neuron-a", neuron_a)
    net.add("neuron-b", neuron_b)
    net.add("brain", brain)
    net.add("muscle", muscle)

    # External driver — same Act mechanism as any world
    def stimulate(weight: float):
        stimulus.act(Act(
            actor_token="external",
            type="stimulus",
            payload={"weight": weight, "kind": "environmental"}))

    # Epoch 0: no stimulus
    e0 = net.run_epoch()

    # Epoch 1: stimulus 5
    stimulate(5.0)
    e1 = net.run_epoch()

    # Epoch 2: no stimulus
    e2 = net.run_epoch()

    # Epoch 3: stimulus 8
    stimulate(8.0)
    e3 = net.run_epoch()

    epochs = [e0, e1, e2, e3]

    print("=" * 70)
    print("Relay Pattern — CNS/PNS as a WCP composition")
    print("=" * 70)
    print()
    print("  Wiring:")
    print("    Stimulus → [Sensory-A (thresh 4)] ─┐")
    print("    Stimulus → [Sensory-B (thresh 6)] ─┴→")
    print("              Brain (thresh 1) → Muscle (thresh 1)")
    print()
    for e in epochs:
        for line in e.format().split("\n"):
            print(f"  {line}")
        print()
    print("  What this demonstrates:")
    print("    - Every unit is an ordinary WCP entity")
    print("      (conformance-passing, petition/act/log_since).")
    print("    - No unit receives a brain command. Everything")
    print("      flows through streams (log cursors).")
    print("    - The brain's decision depends on aggregate")
    print("      weight only; it never branches on which neuron")
    print("      fired. That's what 'stream-mediated' means.")
    print("    - Adding a neuron = adding a unit + a new input")
    print("      stream to the brain. Brain's logic unchanged.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'The Brain – is wider than the Sky –'")
    print("    'For – put them side by side –'")
    print("    (same line as C41; different architecture)")

    audit = {
        "epochs": [
            {"epoch": e.epoch,
             "fires": dict(e.fires),
             "muscle_contracted": e.muscle_contracted}
            for e in epochs
        ],
    }
    if artifact_dir:
        path = Path(artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "relay_demo.json").write_text(
            json.dumps(audit, indent=2))
        print(f"\n  → {path}/relay_demo.json")
    return audit
