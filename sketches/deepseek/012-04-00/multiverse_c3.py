"""
multiverse_c3.py — Component 3: The World Connection Protocol (WCP/0.1).

This module is *not* a world. It is the *specification* of what a world
must do to be part of the federation. Every entity at every level speaks
this protocol:
  - A **world** is an entity with no sub-registry.
  - A **multiverse** is an entity with a sub-registry of worlds.
  - A **federation** is an entity with a sub-registry of multiverses.

The protocol is fractal: the distinction between a world, a multiverse,
and a federation is *not* structural. It is *only* about what is listed
in the sub-registry.

Depends on Components 1 and 2 (Identity, Passport).
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Tuple, Union


# =====================================================================
# The Manifest: what every conforming entity publishes
# =====================================================================

@dataclass(frozen=True)
class Manifest:
    """The public description of a conforming entity.

    Required:
      entity_id            — the entity's stable token (like an identity)
      name                 — display label
      protocol_version     — "WCP/0.1" for this version
      law_url              — where to read the Law document
      act_endpoint         — where to submit acts
      log_endpoint         — where to read the log

    Optional:
      sub_registry_endpoint — if present, this entity has sub-entities
    """
    entity_id: str
    name: str
    protocol_version: str
    law_url: str
    act_endpoint: str
    log_endpoint: str
    sub_registry_endpoint: Optional[str] = None

    def has_sub_registry(self) -> bool:
        """A world has no sub-registry. A multiverse or federation does."""
        return self.sub_registry_endpoint is not None

    def __post_init__(self):
        for field_name in ("entity_id", "name", "protocol_version",
                            "law_url", "act_endpoint", "log_endpoint"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value:
                raise ValueError(f"{field_name} must be non-empty")


# =====================================================================
# The four messages
# =====================================================================

@dataclass(frozen=True)
class Petition:
    """A request from an individual to be admitted.

    Any individual can petition any entity. The entity's Law decides
    whether to admit.

    `target` — if the entity has a sub-registry, the petitioner may
    name a sub-entity to be routed to. If the entity has no
    sub-registry, target must be None.
    """
    petitioner_token: str          # token only, not the full Identity
    petitioner_name: str           # for display on the entity's side
    passport_admissions: Tuple[Tuple[str, str], ...]  # frozen passport
    message: str
    target: Optional[str] = None


@dataclass(frozen=True)
class Admission:
    """The entity admitted the petitioner. The passport is extended."""
    entity_id: str
    timestamp: str


@dataclass(frozen=True)
class Refusal:
    """The entity refused. The reason is *the entity's*, not the
    protocol's — it is Law-specific."""
    reason: str


@dataclass(frozen=True)
class Route:
    """The petition is routed to a sub-entity. The petitioner should
    re-petition the target."""
    target_manifest: Manifest
    reason: str


PetitionResponse = Union[Admission, Refusal, Route]


@dataclass(frozen=True)
class Act:
    """An action inside an entity. The actor must be admitted.

    `type` and `payload` are *opaque to WCP*. The entity's Law decides
    what types and payloads are valid.
    """
    actor_token: str
    type: str
    payload: Dict


@dataclass(frozen=True)
class Ack:
    """The entity accepted the act."""
    entity_id: str
    timestamp: str


ActResponse = Union[Ack, Refusal]


@dataclass(frozen=True)
class LogEntry:
    """One entry in the entity's log."""
    timestamp: str
    kind: str  # "petition" | "admission" | "refusal" | "act" | "ack" | ...
    actor_token: Optional[str] = None
    target: Optional[str] = None
    data: Dict = field(default_factory=dict)


# =====================================================================
# The interface: what any conforming entity must implement
# =====================================================================

class WorldProtocol(Protocol):
    """The four operations any entity must support.

    *A developer implementing a world only needs to implement this
    interface.* The protocol is otherwise silent on how the world
    works. The world can be a single-process in-memory object, a
    remote HTTP service, a distributed network — WCP doesn't care.
    """

    def manifest(self) -> Manifest:
        """Return this entity's public manifest."""
        ...

    def petition(self, petition: Petition) -> PetitionResponse:
        """Handle a petition. Return Admission, Refusal, or Route."""
        ...

    def act(self, act: Act) -> ActResponse:
        """Handle an act. Return Ack or Refusal. The actor must be
        admitted to this entity (checked by the entity's Law)."""
        ...

    def log_since(self, timestamp: Optional[str] = None) -> List[LogEntry]:
        """Return log entries since the given timestamp (or from the
        beginning if None)."""
        ...


# =====================================================================
# NullWorld: the minimal conforming implementation
# =====================================================================

class NullWorld:
    """A minimal conforming entity.

    NullWorld does *not* admit anyone, does *not* accept acts. It
    exists only to be a *structurally valid* implementation — to
    demonstrate that WCP is implementable and to be a template that
    real worlds can extend.

    Real worlds (Component 4+) will have real Laws, real admissions,
    real acts. NullWorld has none. But NullWorld passes the
    conformance test, because WCP does not require a world to be
    *interesting* — only to be *conforming*.
    """

    def __init__(self, entity_id: str, name: str):
        self._manifest = Manifest(
            entity_id=entity_id,
            name=name,
            protocol_version="WCP/0.1",
            law_url=f"null://{entity_id}/law",
            act_endpoint=f"null://{entity_id}/act",
            log_endpoint=f"null://{entity_id}/log",
            sub_registry_endpoint=None,
        )
        self._log: List[LogEntry] = []

    def manifest(self) -> Manifest:
        return self._manifest

    def petition(self, petition: Petition) -> PetitionResponse:
        # NullWorld refuses all petitions, with a clear reason
        self._log.append(LogEntry(
            timestamp="(null)",
            kind="refusal",
            actor_token=petition.petitioner_token,
            data={"reason": "NullWorld does not admit"},
        ))
        return Refusal(reason="NullWorld does not admit")

    def act(self, act: Act) -> ActResponse:
        # NullWorld accepts no acts
        self._log.append(LogEntry(
            timestamp="(null)",
            kind="refusal",
            actor_token=act.actor_token,
            data={"reason": "NullWorld does not accept acts"},
        ))
        return Refusal(reason="NullWorld does not accept acts")

    def log_since(self, timestamp: Optional[str] = None) -> List[LogEntry]:
        return list(self._log)
