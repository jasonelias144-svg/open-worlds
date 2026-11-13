"""
multiverse_c47.py — Component 47: The Autonomic Architecture.

Fifth and final value on the direction axis: local. Each unit
has its own target; each unit corrects its own state; no unit
looks at other units through the protocol. The aggregate is
stable because each unit is stable.

Structural differences from the previous four:

  C41 Octopus:  unit has a MODEL and an INTENT QUEUE
  C42 Relay:    unit has INPUT STREAMS and a THRESHOLD on aggregate
  C43 Swarm:    unit has a SHARED ENV STREAM and a POSITION
  C44 Council:  unit has a DECISION RULE and casts VOTES
  C47 Autonomic: unit has a TARGET and a STATE; fires when
                 own state exceeds own target

  Autonomic is a DYNAMICAL SYSTEM; C41-C46 are message-passing
  or counted-aggregation. The substrate supports both.

Infrastructure addition: a modulate act. The unit accepts one
act type — modulate — which changes its target. That's the
entire infrastructure delta.

The demo: three compartments, ambient heat, coupling.
Each compartment holds its target. Modulate the middle one;
all three still hold.

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per behavior, plus the "no shared stream"
    and "own-state-only" structural tests.
  - "A world never raises on what a visitor sends" — act
    refuses bad payloads.
  - "History, not rank" — state traces are records.

Honest limits (documented, tested):
  - Ambient drift is applied by the network, not the unit.
    Units don't decide their disturbance; they respond to it.
  - Coupling is symmetric and uniform. Real systems have
    asymmetric coupling (a neuron's dendrite isn't the same
    as its axon).
  - No time constants. All dynamics happen at once per tick.
    Real autonomic loops run at different speeds.
  - modulate is unconditional (any actor can modulate).
    Same as C3's act auth model everywhere.
  - Float state, no overflow handling. Production would
    normalize.
"""

import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple

from multiverse_c3 import Act, Ack, Refusal
from multiverse_c42 import SignalWorld


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# =====================================================================
# AutonomicUnit
# =====================================================================

class AutonomicUnit(SignalWorld):
    """A self-regulating unit.

    Has its own state, its own target, and its own correction
    policy. Fires when own state > own target. Adjusts own state
    downward (by `correction_strength`) when firing.

    Accepts one act type: `modulate` — adjust target.
    Refuses anything else.
    """

    def __init__(
        self,
        entity_id: str,
        name: str,
        target: float,
        initial_state: float,
        correction_strength: float = 1.0,
        ambient_drift: float = 0.0,
    ):
        super().__init__(entity_id, name)
        self._target = float(target)
        self._state = float(initial_state)
        self._correction_strength = float(correction_strength)
        self._ambient_drift = float(ambient_drift)
        self._fire_history: List[Tuple[int, float]] = []

    # -- Read-only accessors ------------------------------------

    @property
    def state(self) -> float:
        return self._state

    @property
    def target(self) -> float:
        return self._target

    @property
    def correction_strength(self) -> float:
        return self._correction_strength

    # -- WCP act handler ---------------------------------------

    def act(self, act: Act):
        if act.type == "modulate":
            new_target = act.payload.get("target")
            if not isinstance(new_target, (int, float)):
                return Refusal(
                    reason="modulate requires payload.target number")
            old = self._target
            self._target = float(new_target)
            self._log.append(type(self._log[0])(**{
                "timestamp": _now(), "kind": "modulation",
                "actor_token": act.actor_token,
                "data": {"old_target": old,
                          "new_target": float(new_target)},
            }))
            return Ack(
                entity_id=self._manifest.entity_id,
                timestamp=_now())
        return Refusal(
            reason=(f"AutonomicUnit refuses external act type "
                    f"{act.type!r}; only 'modulate' is accepted"))

    # -- Local dynamics ----------------------------------------

    def apply_ambient(self, delta: Optional[float] = None) -> None:
        """Apply ambient drift. The network or an external process
        calls this between ticks. Not part of `act` — it's the
        physics, not a command.
        """
        d = self._ambient_drift if delta is None else delta
        self._state += d

    def apply_external_heat(self, delta: float) -> None:
        """Add heat from an external source (coupling, stimulus)."""
        self._state += float(delta)

    def tick(self, epoch: int) -> bool:
        """Read own state. Fire iff state > target. Correct if
        fired. Return True iff fired.
        """
        fired = False
        if self._state > self._target:
            self._state -= self._correction_strength
            fired = True
            self._fire_history.append((epoch, self._state))
            self.emit("fire", 1.0, {
                "epoch": epoch,
                "state_before_fire":
                    self._state + self._correction_strength,
                "target": self._target,
            })
        return fired

    def state_trace(self) -> List[float]:
        """A simple observable trace — the states at each fire.
        (Prototype convenience; a production trace would be
        reconstructed from the log.)"""
        return [s for _, s in self._fire_history]


# =====================================================================
# EpochResult
# =====================================================================

@dataclass
class EpochResult:
    epoch: int
    fires: Dict[str, bool]
    states: Dict[str, float]
    targets: Dict[str, float]

    def format(self) -> str:
        lines = [f"Epoch {self.epoch}"]
        for name in self.fires:
            fired_marker = "FIRE" if self.fires[name] else "    "
            s = self.states[name]
            t = self.targets[name]
            delta = s - t
            sign = "+" if delta >= 0 else ""
            lines.append(
                f"  {fired_marker} {name}: "
                f"state={s:6.2f} target={t:6.2f} "
                f"(Δ={sign}{delta:+.2f})")
        return "\n".join(lines)


# =====================================================================
# AutonomicNetwork
# =====================================================================

class AutonomicNetwork:
    """Orchestrates N autonomic units.

    The network does three things:
      1. Apply ambient drift to each unit.
      2. Let each unit tick (self-regulate).
      3. Apply coupling: firers add heat to their neighbors.

    The units don't know about steps 1 and 3. They only know their
    own state and target. Homeostasis is their job; physics is the
    network's.
    """

    def __init__(self):
        self._units: Dict[str, AutonomicUnit] = {}
        self._neighbors: Dict[str, List[str]] = {}
        self._coupling_heat: float = 0.0
        self._epoch = 0

    def add_unit(
        self,
        name: str,
        unit: AutonomicUnit,
        neighbors: Optional[List[str]] = None,
    ) -> None:
        self._units[name] = unit
        self._neighbors[name] = list(neighbors or [])

    def set_coupling_heat(self, heat: float) -> None:
        self._coupling_heat = float(heat)

    def unit_by_name(self, name: str) -> Optional[AutonomicUnit]:
        return self._units.get(name)

    def run_epoch(self) -> EpochResult:
        epoch = self._epoch
        self._epoch += 1
        # 1. Apply ambient drift
        for unit in self._units.values():
            unit.apply_ambient()
        # 2. Each unit ticks (self-regulates)
        fires: Dict[str, bool] = {}
        for name, unit in self._units.items():
            fires[name] = unit.tick(epoch)
        # 3. Coupling: firers add heat to their neighbors
        if self._coupling_heat > 0:
            for name, fired in fires.items():
                if not fired:
                    continue
                for nb_name in self._neighbors.get(name, ()):
                    nb = self._units.get(nb_name)
                    if nb is not None:
                        nb.apply_external_heat(self._coupling_heat)
        return EpochResult(
            epoch=epoch,
            fires=dict(fires),
            states={n: u.state for n, u in self._units.items()},
            targets={n: u.target
                      for n, u in self._units.items()})

    def modulate(self, name: str, new_target: float,
                  actor: str = "external"):
        """Apply a modulate act to a unit. Returns the unit's
        response (Ack or Refusal)."""
        unit = self._units.get(name)
        if unit is None:
            return Refusal(reason=f"no unit named {name!r}")
        return unit.act(Act(
            actor_token=actor, type="modulate",
            payload={"target": new_target}))

    def all_within_tolerance(self, tolerance: float) -> bool:
        """True iff every unit's state is within `tolerance` of
        its own target. Homeostasis is per-unit, not aggregate."""
        return all(
            abs(u.state - u.target) <= tolerance
            for u in self._units.values())
