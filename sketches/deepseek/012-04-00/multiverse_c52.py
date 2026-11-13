"""
multiverse_c52.py — Component 52: The Epidemic Architecture.

Seventh architecture. Each unit has:
  - its own contact list (outgoing edges)
  - a susceptibility threshold (rumors heard N times → spread)
  - exposure tracking (rumors it's heard, and from whom)

Coordination is direct unit-to-unit transmission, delivered by
the network on the unit's behalf. No shared environment, no
aggregate threshold, no votes. The unit's decision is: "for each
rumor I've heard at least susceptibility times, tell every
contact once."

Structural differences from C41-C50:
  C41 Octopus:    model + intent queue
  C42 Relay:      input streams + aggregate threshold
  C43 Swarm:      shared env stream + position
  C44 Council:    decision_rule + votes
  C47 Autonomic:  state + target
  C50 Institution: signed policy + ruling log
  C52 Epidemic:   contacts + susceptibility + exposures

The distinguishing test: two subnets that can't reach each other
will never transmit between them, regardless of how many units
each contains or what state each is in. Transmission requires
edges. Topology is coordination.

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per behavior, plus structural tests
    (no shared medium, no aggregate, has own contacts).
  - "A world never raises on what a visitor sends" — act
    refuses bad payloads.
  - "History, not rank" — exposure logs are records.

Honest limits (documented, tested):
  - Topology is static. Contacts are set at construction and
    never changed. Dynamic topology (units adding/removing
    contacts) is future work.
  - No rumor decay. Once a unit is "spreading" a rumor, it
    spreads to each contact exactly once and stops. Old rumors
    don't get re-spread.
  - No rumor content semantics. The unit doesn't know what it's
    spreading; the network holds the canonical content for
    logging. This is the "courier, not editor" model.
  - No immunization. A unit never decides "I won't spread this."
    Once susceptible-threshold is reached, it spreads. Immunity
    would be one more rule.
  - No cycles. Because a unit spreads to each contact exactly
    once, cycles don't cause infinite loops. But a unit can
    hear the same rumor from multiple contacts (up to
    len(contacts) times).
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from multiverse_c3 import Act, Ack, Refusal
from multiverse_c42 import SignalWorld


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# =====================================================================
# EpidemicUnit
# =====================================================================

class EpidemicUnit(SignalWorld):
    """A unit with its own contact list and susceptibility threshold.

    Accepts one act type: `infect` (with payload.rumor_id and
    payload.source). Logs each exposure. On tick, decides which
    contacts to spread to (for each rumor it's spreading, once
    per contact).
    """

    def __init__(
        self,
        entity_id: str,
        name: str,
        contacts: Optional[List[str]] = None,
        susceptibility: int = 1,
    ):
        super().__init__(entity_id, name)
        if susceptibility < 1:
            raise ValueError("susceptibility must be >= 1")
        self._contacts: List[str] = list(contacts or [])
        self._susceptibility = susceptibility
        # rumor_id -> set of source unit_ids
        self._exposures: Dict[str, Set[str]] = {}
        # rumors we're currently spreading
        self._spreading: Set[str] = set()
        # rumor_id -> set of contact names we've already spread to
        self._spread_done: Dict[str, Set[str]] = {}

    @property
    def contacts(self) -> List[str]:
        return list(self._contacts)

    @property
    def susceptibility(self) -> int:
        return self._susceptibility

    def exposures(self, rumor_id: str) -> Set[str]:
        return set(self._exposures.get(rumor_id, set()))

    def is_spreading(self, rumor_id: str) -> bool:
        return rumor_id in self._spreading

    def has_heard(self, rumor_id: str) -> bool:
        return rumor_id in self._exposures

    # -- WCP act handler ----------------------------------------

    def act(self, act: Act):
        if act.type != "infect":
            return Refusal(
                reason=(f"EpidemicUnit refuses act type "
                        f"{act.type!r}; only 'infect' is accepted"))
        payload = act.payload or {}
        rumor_id = payload.get("rumor_id")
        source = payload.get("source")
        if not isinstance(rumor_id, str) or not rumor_id:
            return Refusal(reason="infect requires rumor_id string")
        if not isinstance(source, str) or not source:
            return Refusal(reason="infect requires source string")
        self._exposures.setdefault(rumor_id, set()).add(source)
        self._log.append(type(self._log[0])(**{
            "timestamp": _now(),
            "kind": "exposure",
            "actor_token": source,
            "data": {
                "rumor_id": rumor_id,
                "exposure_count":
                    len(self._exposures[rumor_id]),
                "susceptibility": self._susceptibility,
            },
        }))
        return Ack(entity_id=self._manifest.entity_id,
                   timestamp=_now())

    # -- Local dynamics ----------------------------------------

    def tick(self, epoch: int) -> List[Tuple[str, str]]:
        """Return list of (target_contact_name, rumor_id) that the
        unit wants to spread this tick. Network delivers them.

        A unit starts spreading rumor R once its exposure count
        for R >= susceptibility. Once spreading, it spreads to
        each contact exactly once. After that, it stops.
        """
        # 1. Update spreading state
        for rumor_id, sources in self._exposures.items():
            if (len(sources) >= self._susceptibility
                    and rumor_id not in self._spreading):
                self._spreading.add(rumor_id)
                self._spread_done.setdefault(rumor_id, set())
                self._log.append(type(self._log[0])(**{
                    "timestamp": _now(),
                    "kind": "spreading_start",
                    "actor_token": self._manifest.entity_id,
                    "data": {"rumor_id": rumor_id,
                              "epoch": epoch},
                }))
        # 2. Compute pending transmissions
        pending: List[Tuple[str, str]] = []
        for rumor_id in list(self._spreading):
            already_told = self._spread_done.setdefault(
                rumor_id, set())
            for contact in self._contacts:
                if contact not in already_told:
                    already_told.add(contact)
                    pending.append((contact, rumor_id))
        return pending


# =====================================================================
# EpochResult
# =====================================================================

@dataclass
class EpochResult:
    epoch: int
    transmissions: List[Tuple[str, str, str]]  # (from, to, rumor)
    exposures_by_unit: Dict[str, Dict[str, int]]
    spreading_by_unit: Dict[str, Set[str]]

    def format(self) -> str:
        lines = [f"Epoch {self.epoch}"]
        if not self.transmissions:
            lines.append("  (no transmissions)")
        else:
            for src, dst, rumor in self.transmissions:
                lines.append(f"  {src} → {dst}  [{rumor}]")
        return "\n".join(lines)


# =====================================================================
# EpidemicNetwork
# =====================================================================

class EpidemicNetwork:
    """Orchestrates epidemic units. The network:
      - delivers `infect` acts on units' behalf
      - holds canonical rumor content (for logging only)
      - collects per-tick transmissions

    Units never call each other directly. This mirrors the C41
    and C43 pattern: the network is the substrate.
    """

    def __init__(self):
        self._units: Dict[str, EpidemicUnit] = {}
        self._rumors: Dict[str, Dict] = {}
        self._epoch = 0

    def add_unit(self, name: str, unit: EpidemicUnit) -> None:
        self._units[name] = unit

    def unit_by_name(self, name: str) -> Optional[EpidemicUnit]:
        return self._units.get(name)

    def register_rumor(self, rumor_id: str, content: Dict) -> None:
        self._rumors[rumor_id] = content

    def seed(
        self, unit_name: str, rumor_id: str,
        source: str = "external",
    ) -> bool:
        """Inject a rumor into a unit. Returns True iff accepted."""
        unit = self._units.get(unit_name)
        if unit is None:
            return False
        r = unit.act(Act(
            actor_token=source, type="infect",
            payload={"rumor_id": rumor_id, "source": source}))
        return isinstance(r, Ack)

    def run_epoch(self) -> EpochResult:
        epoch = self._epoch
        self._epoch += 1
        transmissions: List[Tuple[str, str, str]] = []
        # Each unit decides its own transmissions
        for name, unit in self._units.items():
            pending = unit.tick(epoch)
            for target_name, rumor_id in pending:
                target = self._units.get(target_name)
                if target is None:
                    # Contact not in network; drop silently
                    continue
                r = target.act(Act(
                    actor_token=name, type="infect",
                    payload={"rumor_id": rumor_id,
                              "source": name}))
                if isinstance(r, Ack):
                    transmissions.append(
                        (name, target_name, rumor_id))
        return EpochResult(
            epoch=epoch,
            transmissions=transmissions,
            exposures_by_unit={
                n: {rid: len(u.exposures(rid))
                    for rid in u._exposures}
                for n, u in self._units.items()},
            spreading_by_unit={
                n: set(u._spreading)
                for n, u in self._units.items()},
        )

    def saturation(self, rumor_id: str) -> Tuple[int, int, bool]:
        """(reached, total, saturated).

        reached: how many units have heard the rumor
        total: how many units exist
        saturated: reached == total
        """
        total = len(self._units)
        reached = sum(
            1 for u in self._units.values()
            if u.has_heard(rumor_id))
        return (reached, total, reached == total)

    def reached_by(self, rumor_id: str) -> List[str]:
        return sorted(
            n for n, u in self._units.items()
            if u.has_heard(rumor_id))

    def active_spreaders(self, rumor_id: str) -> List[str]:
        return sorted(
            n for n, u in self._units.items()
            if u.is_spreading(rumor_id))

    def all_quiet(self) -> bool:
        """True iff every unit has ticked to completion (no unit is
        spreading a rumor to un-told contacts)."""
        for u in self._units.values():
            for rumor_id in u._spreading:
                already = u._spread_done.get(rumor_id, set())
                if any(c not in already for c in u._contacts):
                    return False
        return True

    def run_until_quiet(self, max_epochs: int = 100) -> List[EpochResult]:
        results: List[EpochResult] = []
        for _ in range(max_epochs):
            r = self.run_epoch()
            results.append(r)
            if self.all_quiet():
                break
        return results
