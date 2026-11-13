"""
multiverse_c6.py — Component 6: The Multiverse Registry.

The keystone. A multiverse is a WCP-conforming entity whose
sub_registry_endpoint lists other entities. It proves the fractal
property by being itself listable in another multiverse.

Depends on Components 1, 2, 3.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union

from multiverse_c1 import Identity
from multiverse_c2 import Passport, Admission as PassportAdmission
from multiverse_c3 import (
    Manifest, Petition, Act, LogEntry,
    Admission as WCPAdmission, Refusal, Route, Ack,
    WorldProtocol,
)
from multiverse_c3_conformance import run_conformance


# =====================================================================
# Serialization helpers
# =====================================================================

def manifest_to_dict(m: Manifest) -> Dict:
    return {
        "entity_id": m.entity_id,
        "name": m.name,
        "protocol_version": m.protocol_version,
        "law_url": m.law_url,
        "act_endpoint": m.act_endpoint,
        "log_endpoint": m.log_endpoint,
        "sub_registry_endpoint": m.sub_registry_endpoint,
    }


def manifest_from_dict(d: Dict) -> Manifest:
    return Manifest(
        entity_id=d["entity_id"],
        name=d["name"],
        protocol_version=d["protocol_version"],
        law_url=d["law_url"],
        act_endpoint=d["act_endpoint"],
        log_endpoint=d["log_endpoint"],
        sub_registry_endpoint=d.get("sub_registry_endpoint"),
    )


# =====================================================================
# The Law
# =====================================================================

@dataclass(frozen=True)
class MultiverseLaw:
    """The published Law of the Multiverse."""
    admits_any_identity: bool = True
    max_admitted: Optional[int] = None

    def describe(self) -> str:
        return "\n".join([
            "# Multiverse Registry Law v0.1",
            "",
            "## Petition",
            f"- Admits any identity: {self.admits_any_identity}",
            f"- Max admitted: "
            f"{self.max_admitted if self.max_admitted else 'unlimited'}",
            "",
            "## Acts",
            "- `multiverse.admit`: propose an entity for listing.",
            "  payload: {entity: WorldProtocol instance}",
            "  verifies: entity's conformance to WCP/0.1",
            "  on success: adds entity.manifest() to the sub-registry",
            "- `multiverse.remove`: remove an entity from listing.",
            "  payload: {entity_id: str}",
            "",
            "## Convergence",
            "- NEVER. The multiverse remains open indefinitely.",
            "- A catalog is a living thing. New worlds appear. Old",
            "  worlds disappear. The multiverse is the record of what",
            "  exists, and what exists is always changing.",
            "",
            "## Limits",
            "- Petitions are not signed (WCP/0.1).",
            "- Conformance is verified ONCE at admission. Clients",
            "  who trust the multiverse trust its log entry; clients",
            "  who do not trust it can run their own conformance test",
            "  against the listed entities.",
        ])


# =====================================================================
# The Multiverse
# =====================================================================

class MultiverseRegistry:
    """A WCP-conforming multiverse.

    Same protocol as any world. Distinctive property: its manifest
    has a sub_registry_endpoint. That is the *only* structural
    difference.

    The multiverse is a catalog. It lists manifests. It does not
    route. Clients that want to use a listed entity use the
    entity's own endpoints (given by the manifest).
    """

    def __init__(self, entity_id: str, name: str,
                 law: Optional[MultiverseLaw] = None):
        self._law = law or MultiverseLaw()
        self._manifest = Manifest(
            entity_id=entity_id,
            name=name,
            protocol_version="WCP/0.1",
            law_url=f"multiverse://{entity_id}/law",
            act_endpoint=f"multiverse://{entity_id}/act",
            log_endpoint=f"multiverse://{entity_id}/log",
            sub_registry_endpoint=f"multiverse://{entity_id}/worlds",
        )
        self._log: List[LogEntry] = []
        self._admitted: Dict[str, WCPAdmission] = {}
        self._passports: Dict[str, Passport] = {}
        self._registry: Dict[str, Manifest] = {}
        self._conformance_reports: Dict[str, Dict] = {}
        self._proposed_by: Dict[str, str] = {}

    # -- WCP interface ---------------------------------------------

    def manifest(self) -> Manifest:
        return self._manifest

    def petition(self, petition: Petition) -> Union[
            WCPAdmission, Refusal, Route]:
        timestamp = datetime.now(timezone.utc).isoformat()

        if not self._law.admits_any_identity:
            return self._refuse(timestamp, petition.petitioner_token,
                                 "This multiverse does not admit strangers",
                                 "petition")
        if (self._law.max_admitted is not None
                and len(self._admitted) >= self._law.max_admitted):
            return self._refuse(timestamp, petition.petitioner_token,
                                 "The multiverse is full", "petition")
        if petition.petitioner_token in self._admitted:
            return self._refuse(timestamp, petition.petitioner_token,
                                 "Already admitted", "petition")

        admission = WCPAdmission(
            entity_id=self._manifest.entity_id, timestamp=timestamp)
        self._admitted[petition.petitioner_token] = admission

        passport = Passport(
            identity=Identity(
                token=petition.petitioner_token,
                name=petition.petitioner_name,
            ),
            admissions=tuple(
                PassportAdmission(world_id=w, timestamp=t)
                for w, t in petition.passport_admissions
            ),
        ).with_admission(PassportAdmission(
            world_id=self._manifest.entity_id, timestamp=timestamp,
        ))
        self._passports[petition.petitioner_token] = passport

        self._log.append(LogEntry(
            timestamp=timestamp, kind="admission",
            actor_token=petition.petitioner_token,
            data={"name": petition.petitioner_name},
        ))
        return admission

    def act(self, act: Act) -> Union[Ack, Refusal]:
        timestamp = datetime.now(timezone.utc).isoformat()

        if act.actor_token not in self._admitted:
            return self._refuse(timestamp, act.actor_token,
                                 "Actor is not admitted", "act")

        if act.type == "multiverse.admit":
            return self._handle_admit(timestamp, act)
        if act.type == "multiverse.remove":
            return self._handle_remove(timestamp, act)
        return self._refuse(timestamp, act.actor_token,
                             f"Unknown act type: {act.type}", "act")

    def log_since(self, timestamp: Optional[str] = None) -> List[LogEntry]:
        if timestamp is None:
            return list(self._log)
        return [e for e in self._log if e.timestamp > timestamp]

    # -- convenience -----------------------------------------------

    def list_sub_entities(self) -> List[Manifest]:
        """The sub-registry. Every client can call this."""
        return list(self._registry.values())

    def get_manifest(self, entity_id: str) -> Optional[Manifest]:
        return self._registry.get(entity_id)

    def entity_ids(self) -> List[str]:
        return list(self._registry.keys())

    def is_converged(self) -> bool:
        """Never converges. A catalog is a living thing."""
        return False

    def law(self) -> MultiverseLaw:
        return self._law

    def describe(self) -> str:
        return "\n".join([
            f"MultiverseRegistry: {self._manifest.name}",
            f"  entity_id:      {self._manifest.entity_id}",
            f"  admitted:       {len(self._admitted)}",
            f"  listed entities: {len(self._registry)}",
            f"  entity ids:     {sorted(self._registry.keys())}",
        ])

    # -- internals -------------------------------------------------

    def _handle_admit(self, timestamp: str, act: Act) -> Union[Ack, Refusal]:
        entity = act.payload.get("entity")
        if entity is None:
            return self._refuse(timestamp, act.actor_token,
                                 "No entity in payload", "act")
        try:
            m = entity.manifest()
        except Exception as e:
            return self._refuse(timestamp, act.actor_token,
                                 f"Proposed entity has no manifest: {e}",
                                 "act")

        if not isinstance(m, Manifest):
            return self._refuse(timestamp, act.actor_token,
                                 "Proposed entity's manifest is not a Manifest",
                                 "act")
        if m.entity_id in self._registry:
            return self._refuse(timestamp, act.actor_token,
                                 f"Entity {m.entity_id} already listed",
                                 "act")

        # Run the conformance test against the entity
        result = run_conformance(entity)
        if not result["passed"]:
            self._log.append(LogEntry(
                timestamp=timestamp, kind="entity_admit_refused",
                actor_token=act.actor_token,
                data={
                    "entity_id": m.entity_id,
                    "manifest": manifest_to_dict(m),
                    "conformance": result,
                },
            ))
            return Refusal(reason=(
                f"Entity {m.entity_id} fails conformance: "
                f"{result['failures']}"
            ))

        # Admit
        self._registry[m.entity_id] = m
        self._conformance_reports[m.entity_id] = result
        self._proposed_by[m.entity_id] = act.actor_token

        self._log.append(LogEntry(
            timestamp=timestamp, kind="entity_admitted",
            actor_token=act.actor_token,
            data={
                "entity_id": m.entity_id,
                "manifest": manifest_to_dict(m),
                "conformance": result,
            },
        ))
        return Ack(entity_id=self._manifest.entity_id,
                   timestamp=timestamp)

    def _handle_remove(self, timestamp: str,
                       act: Act) -> Union[Ack, Refusal]:
        entity_id = act.payload.get("entity_id")
        if not entity_id:
            return self._refuse(timestamp, act.actor_token,
                                 "No entity_id in payload", "act")
        if entity_id not in self._registry:
            return self._refuse(timestamp, act.actor_token,
                                 f"Entity {entity_id} not in registry",
                                 "act")
        del self._registry[entity_id]
        self._conformance_reports.pop(entity_id, None)
        self._proposed_by.pop(entity_id, None)
        self._log.append(LogEntry(
            timestamp=timestamp, kind="entity_removed",
            actor_token=act.actor_token,
            data={"entity_id": entity_id},
        ))
        return Ack(entity_id=self._manifest.entity_id,
                   timestamp=timestamp)

    def _refuse(self, timestamp: str, actor: str, reason: str,
                 kind: str) -> Refusal:
        self._log.append(LogEntry(
            timestamp=timestamp, kind=f"{kind}_refused",
            actor_token=actor, data={"reason": reason},
        ))
        return Refusal(reason=reason)


# =====================================================================
# Reconstruct the registry from the log
# =====================================================================

def registry_from_log(log: List[LogEntry]) -> Dict[str, Manifest]:
    """Reconstruct the multiverse's sub-registry from its log.

    The log is canonical. Any client can call this to verify that
    the multiverse's list_sub_entities() matches what the log says.
    """
    registry: Dict[str, Manifest] = {}
    for entry in log:
        if entry.kind == "entity_admitted":
            m = manifest_from_dict(entry.data["manifest"])
            registry[m.entity_id] = m
        elif entry.kind == "entity_removed":
            registry.pop(entry.data["entity_id"], None)
    return registry
