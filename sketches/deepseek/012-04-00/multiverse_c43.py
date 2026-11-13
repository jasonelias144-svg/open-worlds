"""
multiverse_c43.py — Component 43: The Swarm Architecture.

Third architecture on the same substrate. Contrast:

  Octopus (C41):  one brain, N executor arms,
                  brain PUSHES intents to specific arms
  Relay (C42):    one brain, N relay neurons,
                  brain PULLS from specific private streams
  Swarm (C43):    NO brain, N peer units,
                  all units share ONE environment stream

Structural differences:
  - No privileged unit. Every unit is identical in role.
  - Shared environment. Units don't message each other;
    they read and write to one shared log (stigmergy).
  - Stateful agents. Units have evolving state (position);
    C41/C42 units were stateless.
  - Statistical convergence. The colony reaches a threshold
    statistically; no unit "decides" the colony converged.

Infrastructure additions:
  - Stream.window(n): last n entries, cursor-unaffected.
    That's it. Everything else is C42's primitives.

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per behavior, plus anti-property tests
    (no C41/C42 brain attrs on swarm units) and structural
    tests (three architectures same substrate).
  - "A world never raises on what a visitor sends" — SwarmUnit
    refuses unknown acts; verifiers return refusals.
  - "History, not rank" — traces are records, not scores.

Honest limits (documented, tested):
  - No pheromone decay. Old traces persist forever; units
    follow them regardless of age.
  - Units see their own traces. Following one's own trace is
    a no-op (stays put), but it's why convergence is stable.
  - The demo's finder is a client input, not a privileged
    role. Any unit can be told "food here"; the protocol
    doesn't care.
  - Wander is deterministic via seed. Real swarms are noisy;
    this is a prototype with reproducible behavior.
"""

import json
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from multiverse_c3 import Act, Ack, Refusal
from multiverse_c42 import SignalWorld, Stream


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# =====================================================================
# Extend Stream with window()
#
# The only new primitive in C43. Composition, not new class.
# =====================================================================

def _stream_window(self, n: int) -> List:
    """Return the last n entries. Does not advance the cursor.

    pull() gives "new entries since last read"; window() gives
    "recent entries regardless of what I've read". Both are
    natural over log_since(); window() is the stigmergy primitive
    (a unit reads the *environment's recent state*, not a
    private input queue).
    """
    all_entries = self._world.log_since(None)
    return all_entries[-n:] if n > 0 else []


Stream.window = _stream_window


# =====================================================================
# SwarmUnit
# =====================================================================

class SwarmUnit(SignalWorld):
    """One unit of a swarm. Stateful, autonomous, peer of all
    others. Reads from the shared environment; writes traces.
    """

    def __init__(
        self,
        entity_id: str,
        name: str,
        env_stream: Stream,
        initial_position: Tuple[int, int],
        seed: int = 0,
        sample_probability: float = 0.5,
        window_size: int = 8,
    ):
        super().__init__(entity_id, name)
        self._env_stream = env_stream
        self._position = tuple(initial_position)
        self._known_food: Optional[Tuple[int, int]] = None
        self._rng = random.Random(seed)
        self._sample_probability = sample_probability
        self._window_size = window_size

    @property
    def position(self) -> Tuple[int, int]:
        return self._position

    @property
    def known_food(self) -> Optional[Tuple[int, int]]:
        return self._known_food

    def act(self, act: Act):
        """Swarm units accept one act type: 'find_food'. Anything
        else is refused."""
        if act.type == "find_food":
            loc = act.payload.get("location")
            if (isinstance(loc, (list, tuple)) and len(loc) == 2
                    and all(isinstance(v, int) for v in loc)):
                self._known_food = (loc[0], loc[1])
                return Ack(
                    entity_id=self._manifest.entity_id,
                    timestamp=_now())
            return Refusal(
                reason="find_food requires payload.location=[x, y]")
        return Refusal(
            reason=(f"SwarmUnit refuses external act type "
                    f"{act.type!r}; only 'find_food' is accepted"))

    def tick(self, epoch: int) -> bool:
        """One tick. Return True iff unit is at a food location."""
        # 1. Sample the environment (probabilistically)
        if self._rng.random() < self._sample_probability:
            recent = self._env_stream.window(self._window_size)
            food_loc = self._find_food_in(recent)
            if food_loc is not None:
                self._position = food_loc
                self._emit_food(epoch)
                return True

        # 2. Follow known food (external discovery)
        if self._known_food is not None:
            self._position = self._known_food
            self._emit_food(epoch)
            return True

        # 3. Wander deterministically
        dx = self._rng.randint(-1, 1)
        dy = self._rng.randint(-1, 1)
        self._position = (self._position[0] + dx,
                          self._position[1] + dy)
        return False

    def _find_food_in(self, entries) -> Optional[Tuple[int, int]]:
        for e in reversed(entries):
            if e.kind == "food-pheromone":
                loc = e.data.get("location")
                if (isinstance(loc, (list, tuple))
                        and len(loc) == 2):
                    return (int(loc[0]), int(loc[1]))
        return None

    def _emit_food(self, epoch: int) -> None:
        self.emit(
            "food-pheromone", 1.0, {
                "location": list(self._position),
                "origin": self._manifest.entity_id,
                "epoch": epoch,
            })


# =====================================================================
# EpochResult
# =====================================================================

@dataclass
class EpochResult:
    epoch: int
    actions: Dict[str, bool]
    positions: Dict[str, Tuple[int, int]]
    statistics: Dict

    def format(self) -> str:
        at = self.statistics["units_at_food"]
        total = self.statistics["total_units"]
        return "\n".join([
            f"Epoch {self.epoch}",
            f"  at food:    {at} / {total}",
            f"  converged:  {self.statistics['converged']}",
        ])


# =====================================================================
# SwarmNetwork
# =====================================================================

class SwarmNetwork:
    """A swarm of units sharing one environment. No brain, no
    privileged unit. Runs epochs serially (same as C41/C42)."""

    def __init__(
        self,
        food_target: Tuple[int, int],
        tolerance: float = 0.5,
        max_epochs: int = 30,
    ):
        self._environment = SignalWorld(
            "world:swarm-environment", "Swarm Environment")
        self._stream = Stream(self._environment,
                               "shared-environment")
        self._units: Dict[str, SwarmUnit] = {}
        self._epoch = 0
        self._food_target = tuple(food_target)
        self._tolerance = tolerance
        self._max_epochs = max_epochs

    @property
    def environment(self) -> SignalWorld:
        return self._environment

    @property
    def stream(self) -> Stream:
        return self._stream

    def add_unit(self, name: str, unit: SwarmUnit) -> None:
        self._units[name] = unit

    def remove_unit(self, name: str) -> None:
        self._units.pop(name, None)

    def unit_by_name(self, name: str) -> Optional[SwarmUnit]:
        return self._units.get(name)

    def run_epoch(self) -> EpochResult:
        epoch = self._epoch
        self._epoch += 1
        actions: Dict[str, bool] = {}
        positions: Dict[str, Tuple[int, int]] = {}
        for name, unit in self._units.items():
            actions[name] = unit.tick(epoch)
            positions[name] = unit.position
        return EpochResult(
            epoch=epoch, actions=actions, positions=positions,
            statistics=self.statistics())

    def statistics(self) -> Dict:
        at_food = 0
        for unit in self._units.values():
            d2 = ((unit.position[0] - self._food_target[0]) ** 2
                  + (unit.position[1] - self._food_target[1]) ** 2)
            if d2 <= self._tolerance ** 2:
                at_food += 1
        total = len(self._units)
        return {
            "units_at_food": at_food,
            "total_units": total,
            "converged": total > 0 and at_food == total,
            "epoch": self._epoch,
        }

    def converged(self) -> bool:
        return self.statistics()["converged"]

    def run_until_converged(self) -> List[EpochResult]:
        results = []
        for _ in range(self._max_epochs):
            r = self.run_epoch()
            results.append(r)
            if r.statistics["converged"]:
                return results
        return results


# =====================================================================
# Demo
# =====================================================================

def demo(
    artifact_dir: Optional[str] = None,
    finder_name: str = "ant-0",
    food_target: Tuple[int, int] = (10, 10),
) -> Dict:
    """Five ants, one finder, colony converges by stigmergy.

    Anchor: Emily Dickinson, 'The Brain – is wider than the Sky –'
    (same poem as C41 and C42; different architecture).
    """
    net = SwarmNetwork(food_target=food_target, max_epochs=20)
    for i in range(5):
        net.add_unit(f"ant-{i}", SwarmUnit(
            entity_id=f"world:ant-{i}",
            name=f"ant-{i}",
            env_stream=net.stream,
            initial_position=(i, i),
            seed=42 + i,
            sample_probability=0.5,
            window_size=8,
        ))

    finder = net.unit_by_name(finder_name)
    if finder is None:
        raise ValueError(f"finder {finder_name!r} not in network")
    finder.act(Act(
        actor_token="external", type="find_food",
        payload={"location": list(food_target)}))

    results = net.run_until_converged()

    print("=" * 70)
    print("Swarm Architecture — demo")
    print("=" * 70)
    print()
    print(f"  finder:  {finder_name}  (received find_food act)")
    print(f"  target:  {food_target}")
    print(f"  units:   {len(net._units)}")
    print()
    for r in results:
        for line in r.format().split("\n"):
            print(f"  {line}")
        print()
    final = results[-1].statistics
    print(f"  Final: {final['units_at_food']} / "
          f"{final['total_units']} at food "
          f"in {len(results)} epoch(s)")
    print()
    print("  What this demonstrates:")
    print("    - No unit is privileged. Any unit can be the")
    print("      finder; the protocol doesn't care who.")
    print("    - All units read from ONE shared stream. That")
    print("      is stigmergy: the environment is the")
    print("      coordination.")
    print("    - Convergence is statistical. No unit")
    print("      'decided' the colony converged; the")
    print("      aggregate did.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'The Brain – is wider than the Sky –'")
    print("    'For – put them side by side –'")
    print("    (same line as C41 and C42;")
    print("     no brain in this architecture)")

    audit = {
        "finder": finder_name,
        "target": list(food_target),
        "epochs_run": len(results),
        "final_statistics": final,
        "epochs": [
            {"epoch": r.epoch,
             "units_at_food": r.statistics["units_at_food"],
             "converged": r.statistics["converged"]}
            for r in results
        ],
    }
    if artifact_dir:
        path = Path(artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "swarm_demo.json").write_text(
            json.dumps(audit, indent=2))
        print(f"\n  → {path}/swarm_demo.json")
    return audit
