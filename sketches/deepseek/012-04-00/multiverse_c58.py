"""
multiverse_c58.py — Component 58: Contract-Aware Acts.

C57 made contracts verifiable, but no world enforced them. C58
adds the enforcement policy: a world can check, at act time,
whether the contract a resident cites is real, established, and
in force.

Design:
  - ContractAwareMixin: mixin providing _init_contract_aware,
    act() override, and _check_citation.
  - ContractAwarePoetryWorld(ContractAwareMixin, PoetryWorld)
  - ContractAwareChemistryWorld(ContractAwareMixin, ChemistryWorld)

  The base classes are UNCHANGED. A world that doesn't want
  contract enforcement doesn't subclass.

Check ordering (matters for information leak prevention):
  1. Admission: if actor not admitted, delegate to parent
     — unadmitted actors never learn contract state.
  2. Citation presence: if `cites_contract` is absent and
     `require_citation=False`, proceed (no contract claimed).
  3. Citation validity: look up record in registry; require
     is_established (not pending, not rejected, not revoked).
  4. Counterparty: contract must involve this world; if
     `cites_world` is provided, contract must be specifically
     with that world.

The registry is SHARED with the world's ContractNegotiator (C57).
When the negotiator establishes or revokes a contract, the world
sees it immediately. This is the wiring: one ContractRegistry
object, held by both.

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: valid citation, pending, rejected,
    revoked, not found, wrong counterparty, missing when
    required, invalid format, unadmitted actor, still works
    without citation, ChemistryWorld subclass.
  - "A world never raises on what a visitor sends" — act
    refuses with reason; never raises.
  - "History, not rank" — citations logged, refusals logged.

Honest limits (documented, tested):
  - Enforcement is LOCAL. The world checks against its own
    registry. If the counterparty revokes a contract but the
    world's registry doesn't learn of it, the check passes.
    Sync is the demo's job (shared registry); a production
    system would sync via the negotiators.
  - No per-act-type policy. `require_citation` is a single
    bool. A world that requires citations for some act types
    but not others would need a per-type policy — future work.
  - Same-terms collision. C57 noted that identical terms
    produce identical IDs. A world enforcing citations gets
    whichever record the registry returns by terms_hash. The
    `cites_world` field disambiguates when needed.
  - Contract records are not signed at the world level. The
    registry trusts the negotiator (C57) to have registered
    verified artifacts. If a bad actor injected a fake
    ContractRecord into the registry, the world would trust
    it. Production would require register_* to verify before
    storing.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set

from multiverse_c3 import Act, Ack, Refusal, LogEntry
from multiverse_c4 import PoetryWorld
from multiverse_c5 import ChemistryWorld
from multiverse_c57 import (
    ContractRegistry, ContractOffer, ContractAcceptance,
    ContractRejection, BilateralRevocation,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# =====================================================================
# ContractAwareMixin
# =====================================================================

class ContractAwareMixin:
    """Mixin providing contract-aware act() to any PoetryWorld or
    ChemistryWorld subclass.

    Prerequisites (satisfied by PoetryWorld, ChemistryWorld):
      - self._admitted: dict of token -> admission
      - self._log: list of LogEntry
      - self._manifest.entity_id: str
      - parent act(act) -> Ack | Refusal
      - parent _refuse(ts, actor, reason, kind) -> Refusal
    """

    def _init_contract_aware(
        self,
        registry: Optional[ContractRegistry] = None,
        require_citation: bool = False,
    ) -> None:
        self._contract_registry: ContractRegistry = (
            registry if registry is not None else ContractRegistry())
        self._require_citation = require_citation

    # -- Public accessors -------------------------------------------

    @property
    def contract_registry(self) -> ContractRegistry:
        return self._contract_registry

    @property
    def require_citation(self) -> bool:
        return self._require_citation

    def set_require_citation(self, required: bool) -> None:
        self._require_citation = required

    # -- Registry wiring (convenience) ------------------------------

    def register_contract_offer(self, offer: ContractOffer) -> None:
        self._contract_registry.register_offer(offer)

    def register_contract_acceptance(
        self, acceptance: ContractAcceptance,
    ) -> None:
        self._contract_registry.register_acceptance(acceptance)

    def register_contract_rejection(
        self, rejection: ContractRejection,
    ) -> None:
        self._contract_registry.register_rejection(rejection)

    def register_contract_revocation(
        self, revocation: BilateralRevocation,
    ) -> None:
        self._contract_registry.register_revocation(revocation)

    # -- act() override ---------------------------------------------

    def act(self, act: Act):
        # 1. Admission gate first — unadmitted actors must not
        #    learn contract state.
        if act.actor_token not in self._admitted:
            return super().act(act)
        # 2. Citation check (only for admitted actors)
        payload = act.payload or {}
        cites = payload.get("cites_contract")
        if cites or self._require_citation:
            reason = self._check_citation(act)
            if reason is not None:
                ts = _now()
                return self._refuse(
                    ts, act.actor_token, reason,
                    "contract_citation")
        # 3. Delegate to parent
        result = super().act(act)
        # 4. If accepted with a citation, log the citation
        if isinstance(result, Ack) and cites:
            self._log.append(LogEntry(
                timestamp=_now(),
                kind="contract_cited",
                actor_token=act.actor_token,
                data={
                    "cites_contract": cites,
                    "cites_world": payload.get("cites_world"),
                    "act_type": act.type,
                },
            ))
        return result

    # -- Citation check ---------------------------------------------

    def _check_citation(self, act: Act) -> Optional[str]:
        """Return None if citation OK, else a refusal reason."""
        payload = act.payload or {}
        cites = payload.get("cites_contract")
        if not cites:
            if self._require_citation:
                return "act must cite a contract"
            return None
        if not isinstance(cites, str) or len(cites) != 64:
            return "cites_contract must be 64 hex chars"
        record = self._contract_registry.get(cites)
        if record is None:
            return (f"cited contract not found: "
                    f"{cites[:16]}...")
        if record.is_revoked():
            return "cited contract is revoked"
        if record.is_rejected():
            return "cited contract was rejected"
        if record.is_pending():
            return "cited contract is still pending"
        if not record.is_established():
            return "cited contract is not established"
        world_id = self._manifest.entity_id
        if (record.world_a_id != world_id
                and record.world_b_id != world_id):
            return "cited contract does not involve this world"
        cites_world = payload.get("cites_world")
        if cites_world is not None:
            expected_pair = (world_id, cites_world)
            actual_pair = (record.world_a_id,
                            record.world_b_id)
            if not (
                actual_pair == expected_pair
                or actual_pair == expected_pair[::-1]
            ):
                return ("cited contract does not match "
                         "cites_world")
        return None


# =====================================================================
# Concrete subclasses
# =====================================================================

class ContractAwarePoetryWorld(ContractAwareMixin, PoetryWorld):
    """A Poetry World that checks contract citations.

    The base PoetryWorld is unchanged. This subclass adds the
    contract check as a policy.
    """

    def __init__(
        self,
        entity_id: str,
        name: str,
        *args,
        registry: Optional[ContractRegistry] = None,
        require_citation: bool = False,
        **kwargs,
    ):
        super().__init__(entity_id, name, *args, **kwargs)
        self._init_contract_aware(registry, require_citation)


class ContractAwareChemistryWorld(ContractAwareMixin, ChemistryWorld):
    """A Chemistry World that checks contract citations."""

    def __init__(
        self,
        entity_id: str,
        name: str,
        *args,
        registry: Optional[ContractRegistry] = None,
        require_citation: bool = False,
        **kwargs,
    ):
        super().__init__(entity_id, name, *args, **kwargs)
        self._init_contract_aware(registry, require_citation)
