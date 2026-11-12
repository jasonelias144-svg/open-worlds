"""A registry of worlds: a multiverse that is itself an entity.

From the DeepSeek sketch's component 6. A registry speaks the same
protocol as any world. Its one structural difference is a
sub_registry_endpoint in its manifest. It lists manifests; it does not
route anyone anywhere. A registry can be listed in another registry,
which is how multiverses join each other. Anyone can run one, and none is
the authority (docs/MULTIVERSE.md).

Acts:
  multiverse.admit    {"entity_id": str}, with the entity attached to the
                      act: runs the conformance test, and lists the
                      entity if it passes and its id is the one signed
  multiverse.remove   {"entity_id": str}: takes down a listing; only
                      whoever listed it may

Changed from the sketch:
  - An entity whose manifest is broken is refused as failing
    conformance, with the test's own report.
  - The conformance test leaves the world it checks (conformance.py), so
    listing a world no longer takes one of its places.
  - The manifest listed is the one the conformance test checked. The
    sketch asked the entity again, so an entity could pass with one
    answer and then raise, or give another.
  - Only whoever listed an entity may take the listing down (the sketch
    recorded who listed it but let anyone remove it), and a registry
    does not list itself.

Known limit, until course step 12 (docs/COURSE.md): `multiverse.admit`
carries the entity itself, attached to the act, so it only works within
one process. Over the network it carries an address. The signature
covers the entity's id; the registry lists only an entity whose checked
manifest has that id.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .conformance import check
from .entity import Entity, now
from .protocol import Ack, Act, ActResponse, LogEntry, Manifest, Refusal


def manifest_to_dict(m: Manifest) -> Dict:
    return {"entity_id": m.entity_id, "name": m.name,
            "protocol_version": m.protocol_version, "law_url": m.law_url,
            "act_endpoint": m.act_endpoint, "log_endpoint": m.log_endpoint,
            "sub_registry_endpoint": m.sub_registry_endpoint}


def manifest_from_dict(d: Dict) -> Manifest:
    return Manifest(entity_id=d["entity_id"], name=d["name"],
                    protocol_version=d["protocol_version"],
                    law_url=d["law_url"], act_endpoint=d["act_endpoint"],
                    log_endpoint=d["log_endpoint"],
                    sub_registry_endpoint=d.get("sub_registry_endpoint"))


@dataclass(frozen=True)
class MultiverseLaw:
    admits_any_identity: bool = True
    max_admitted: Optional[int] = None

    def describe(self) -> str:
        return "\n".join([
            "# Multiverse Registry Law v0.1",
            "",
            "## Entering and leaving",
            f"- Admits any identity: {self.admits_any_identity}",
            "- Max present: "
            f"{self.max_admitted if self.max_admitted else 'unlimited'}",
            "- Anyone may leave at any time.",
            "",
            "## Acts",
            "- multiverse.admit: propose an entity for listing. It is "
            "listed if it passes the WCP/0.1 conformance test.",
            "- multiverse.remove: take down a listing you made. (Until "
            "worlds have keys, a world can't take down its own listing, and "
            "a listing whose lister has left stays up.)",
            "- A registry does not list itself.",
            "",
            "## Convergence",
            "- Never. A catalogue stays open: worlds appear and go.",
            "",
            "## Limits",
            "- Petitions and acts are not signed yet (WCP/0.1).",
            "- Conformance is checked once, at listing. Anyone who doesn't "
            "trust this registry can run the test themselves.",
        ])


class MultiverseRegistry(Entity):
    noun = "multiverse"
    scheme = "multiverse"

    def __init__(self, entity_id: str, name: str,
                 law: Optional[MultiverseLaw] = None):
        super().__init__(entity_id, name, law or MultiverseLaw(),
                         sub_registry=True)
        self._registry: Dict[str, Manifest] = {}
        self._conformance_reports: Dict[str, Dict] = {}
        self._proposed_by: Dict[str, str] = {}

    def act(self, act: Act) -> ActResponse:
        timestamp = now()
        refusal = self._actor_problem(timestamp, act)
        if refusal:
            return refusal
        if act.type == "multiverse.admit":
            return self._handle_admit(timestamp, act)
        if act.type == "multiverse.remove":
            return self._handle_remove(timestamp, act)
        return self._refuse(timestamp, act.actor_token,
                            f"Unknown act type: {act.type}", "act")

    # -- conveniences ---------------------------------------------------

    def list_sub_entities(self) -> List[Manifest]:
        return list(self._registry.values())

    def get_manifest(self, entity_id: str) -> Optional[Manifest]:
        return self._registry.get(entity_id)

    def entity_ids(self) -> List[str]:
        return list(self._registry)

    def conformance_report(self, entity_id: str) -> Optional[Dict]:
        return self._conformance_reports.get(entity_id)

    def is_converged(self) -> bool:
        return False

    def describe(self) -> str:
        return "\n".join([
            f"MultiverseRegistry: {self._manifest.name}",
            f"  entity_id:       {self._manifest.entity_id}",
            f"  present:         {len(self._admitted)}",
            f"  listed entities: {len(self._registry)}",
            f"  entity ids:      {sorted(self._registry)}",
        ])

    # -- internals ------------------------------------------------------

    def _handle_admit(self, timestamp: str, act: Act) -> ActResponse:
        entity = act.attachment
        entity_id = act.payload.get("entity_id")
        if entity is None:
            return self._refuse(timestamp, act.actor_token,
                                "No entity attached", "act")
        if type(entity_id) is not str or not entity_id:
            return self._refuse(timestamp, act.actor_token,
                                "No entity_id in payload", "act")
        if entity is self:
            return self._refuse(timestamp, act.actor_token,
                                "A registry does not list itself", "act")
        # The manifest the test checked is the one listed: an entity can't
        # pass with one manifest and be listed with another. check() only
        # returns a plain Manifest with plain-text fields, so comparing and
        # hashing its fields below can't be redefined by the entity.
        try:
            result, m = check(entity)
        except Exception:
            # check() reports what it finds rather than raising; this is
            # a last guard. (Exceptions outside Exception, like SystemExit,
            # are not contained: code run in-process is trusted, and
            # outside agents run in their own processes; DESIGN.md.)
            return self._refuse(timestamp, act.actor_token,
                                "Entity could not be checked", "act")
        if not result["passed"]:
            self._log.append(LogEntry(
                timestamp=timestamp, kind="entity_admit_refused",
                actor_token=act.actor_token,
                data={"manifest": (manifest_to_dict(m) if m is not None
                                   else None),
                      "conformance": result}))
            # Recorded above, with the full report.
            return Refusal(reason=f"Entity fails conformance: "
                                  f"{result['failures']}")
        if m.entity_id == self._manifest.entity_id:
            return self._refuse(timestamp, act.actor_token,
                                "A registry does not list itself", "act")
        if m.entity_id != entity_id:
            # The signature covers the id, not the attached object, so
            # what is listed must be what was signed for.
            return self._refuse(timestamp, act.actor_token,
                                f"The attached entity is {m.entity_id}, "
                                f"not the {entity_id} that was signed for",
                                "act")
        if m.entity_id in self._registry:
            return self._refuse(timestamp, act.actor_token,
                                f"Entity {m.entity_id} already listed", "act")
        self._registry[m.entity_id] = m
        self._conformance_reports[m.entity_id] = result
        self._proposed_by[m.entity_id] = act.actor_token
        self._log.append(LogEntry(
            timestamp=timestamp, kind="entity_admitted",
            actor_token=act.actor_token,
            data={"entity_id": m.entity_id,
                  "manifest": manifest_to_dict(m),
                  "conformance": result}))
        return Ack(entity_id=self._manifest.entity_id, timestamp=timestamp)

    def _handle_remove(self, timestamp: str, act: Act) -> ActResponse:
        entity_id = act.payload.get("entity_id")
        if type(entity_id) is not str or not entity_id:
            return self._refuse(timestamp, act.actor_token,
                                "No entity_id in payload", "act")
        if entity_id not in self._registry:
            return self._refuse(timestamp, act.actor_token,
                                f"Entity {entity_id} not in registry", "act")
        if self._proposed_by.get(entity_id) != act.actor_token:
            return self._refuse(timestamp, act.actor_token,
                                "Only whoever listed an entity may take "
                                "the listing down", "act")
        del self._registry[entity_id]
        self._conformance_reports.pop(entity_id, None)
        self._proposed_by.pop(entity_id, None)
        self._log.append(LogEntry(
            timestamp=timestamp, kind="entity_removed",
            actor_token=act.actor_token, data={"entity_id": entity_id}))
        return Ack(entity_id=self._manifest.entity_id, timestamp=timestamp)


def registry_from_log(log: List[LogEntry]) -> Dict[str, Manifest]:
    """The listings rebuilt from a registry's log, so anyone can check
    that list_sub_entities() matches the record."""
    registry: Dict[str, Manifest] = {}
    for entry in log:
        if entry.kind == "entity_admitted":
            m = manifest_from_dict(entry.data["manifest"])
            registry[m.entity_id] = m
        elif entry.kind == "entity_removed":
            registry.pop(entry.data["entity_id"], None)
    return registry
