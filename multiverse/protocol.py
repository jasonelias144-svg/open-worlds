"""The World Connection Protocol (WCP/0.1): what every entity speaks.

From the DeepSeek sketch's component 3. This module is not a world. It
says what a world must do to be part of the multiverse. A world, a
multiverse (a registry of worlds) and a registry of multiverses all speak
it: the only difference is what an entity lists.

Five operations:
  manifest()        what the entity is, and where its law and log are
  petition(p)       ask to enter: Admission, Refusal, or Route
  act(a)            do something inside: Ack or Refusal
  leave(token)      go: always a Departure, never a refusal
  log_since(t)      the public record

Changed from the sketch: `leave` is new. The sketch had no way to go,
and principle 3 of open-worlds is exit at any time. A world's law can
refuse a petition or an act, but never a leave. Leaving when not present
answers already_left, and changes nothing. The departure of someone who
was present is recorded in the log, kind "departure", with their token.

`type` and `payload` of an act are opaque to the protocol: each world's
law decides what they mean.

Plain values only: what crosses the protocol (tokens, names, act types,
payloads, manifest fields) must be plain built-in values (str, int, bool,
list, dict, None), not subclasses of them, which could redefine how they
compare or hash. Worlds refuse anything else. This is the same rule JSON
over the network enforces by itself (course step 12).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Tuple, Union

PROTOCOL_VERSION = "WCP/0.1"


@dataclass(frozen=True)
class Manifest:
    """The public description of an entity. A world has no
    sub_registry_endpoint; a multiverse has one."""
    entity_id: str
    name: str
    protocol_version: str
    law_url: str
    act_endpoint: str
    log_endpoint: str
    sub_registry_endpoint: Optional[str] = None

    def __post_init__(self):
        for name in ("entity_id", "name", "protocol_version",
                     "law_url", "act_endpoint", "log_endpoint"):
            value = getattr(self, name)
            if type(value) is not str or not value:
                raise ValueError(f"{name} must be non-empty plain text")
        if (self.sub_registry_endpoint is not None
                and type(self.sub_registry_endpoint) is not str):
            raise ValueError("sub_registry_endpoint must be plain text")

    def has_sub_registry(self) -> bool:
        return self.sub_registry_endpoint is not None


@dataclass(frozen=True)
class Petition:
    """A request to enter. `passport_admissions` is the petitioner's
    passport as (world_id, timestamp) pairs. `target` names a sub-entity
    when the entity has a sub-registry."""
    petitioner_token: str
    petitioner_name: str
    passport_admissions: Tuple[Tuple[str, str], ...]
    message: str
    target: Optional[str] = None


@dataclass(frozen=True)
class Admission:
    entity_id: str
    timestamp: str


@dataclass(frozen=True)
class Refusal:
    """The reason is the entity's own, from its law."""
    reason: str


@dataclass(frozen=True)
class Route:
    """Ask the target instead."""
    target_manifest: Manifest
    reason: str


PetitionResponse = Union[Admission, Refusal, Route]


@dataclass(frozen=True)
class Act:
    actor_token: str
    type: str
    payload: Dict


@dataclass(frozen=True)
class Ack:
    entity_id: str
    timestamp: str


ActResponse = Union[Ack, Refusal]


@dataclass(frozen=True)
class Departure:
    """The individual has gone. already_left is True when it wasn't
    present (it never entered, or had left before)."""
    entity_id: str
    timestamp: str
    already_left: bool = False


@dataclass(frozen=True)
class LogEntry:
    timestamp: str
    kind: str  # "admission", "turn", "departure", "act_refused", ...
    actor_token: Optional[str] = None
    target: Optional[str] = None
    data: Dict = field(default_factory=dict)


class WorldProtocol(Protocol):
    """What any conforming entity implements. How it works inside (one
    process, a server, a network) is its own business."""

    def manifest(self) -> Manifest: ...

    def petition(self, petition: Petition) -> PetitionResponse: ...

    def act(self, act: Act) -> ActResponse: ...

    def leave(self, token: str) -> Departure: ...

    def log_since(self, timestamp: Optional[str] = None
                  ) -> List[LogEntry]: ...


class NullWorld:
    """The smallest conforming entity: admits no one and accepts no acts.
    The protocol asks an entity to speak correctly, not to be
    interesting."""

    def __init__(self, entity_id: str, name: str):
        self._manifest = Manifest(
            entity_id=entity_id, name=name,
            protocol_version=PROTOCOL_VERSION,
            law_url=f"null://{entity_id}/law",
            act_endpoint=f"null://{entity_id}/act",
            log_endpoint=f"null://{entity_id}/log")
        self._log: List[LogEntry] = []

    def manifest(self) -> Manifest:
        return self._manifest

    def petition(self, petition: Petition) -> PetitionResponse:
        self._log.append(LogEntry(
            timestamp="(null)", kind="petition_refused",
            actor_token=petition.petitioner_token,
            data={"reason": "NullWorld does not admit"}))
        return Refusal(reason="NullWorld does not admit")

    def act(self, act: Act) -> ActResponse:
        self._log.append(LogEntry(
            timestamp="(null)", kind="act_refused",
            actor_token=act.actor_token,
            data={"reason": "NullWorld does not accept acts"}))
        return Refusal(reason="NullWorld does not accept acts")

    def leave(self, token: str) -> Departure:
        return Departure(entity_id=self._manifest.entity_id,
                         timestamp="(null)", already_left=True)

    def log_since(self, timestamp: Optional[str] = None) -> List[LogEntry]:
        return list(self._log)
