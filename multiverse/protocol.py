"""The World Connection Protocol (WCP/0.2): what every entity speaks.

From the DeepSeek sketch's component 3. This module is not a world. It
says what a world must do to be part of the multiverse. A world, a
multiverse (a registry of worlds) and a registry of multiverses all speak
it: the only difference is what an entity lists.

Five operations:
  manifest()        what the entity is, and where its law and log are
  petition(p)       ask to enter: Admission, Refusal, or Route
  act(a)            do something inside: Ack or Refusal
  leave(l)          go: a Departure; refused only if not the leaver's own
  log_since(t)      the public record

WCP/0.2 (course step 2): an individual is a key (identity.py). Every
petition, act and leave is signed by the individual it names, over a
document that names the world it is sent to and a number, `seq`, that
grows with every request to that world. So a request can't be forged,
can't be sent to another world, and can't be replayed. A world checks
the signature before anything else.

Changed from the sketch: `leave` is new. The sketch had no way to go,
and principle 3 of open-worlds is exit at any time. A world's law can
refuse a petition or an act, but never a leave. Leaving when not present
answers already_left, and changes nothing. The departure of someone who
was present is recorded in the log, kind "departure", with their token.
The one leave a world refuses is a leave that isn't the leaver's own: not
signed by them, or a replay of an old one. Theirs always succeeds.

`type` and `payload` of an act are opaque to the protocol: each world's
law decides what they mean.

Plain values only: what crosses the protocol (tokens, names, act types,
payloads all the way down, manifest fields) must be plain built-in values
(str, int, float, bool, list, dict with text keys, None), not subclasses
of them, which could redefine how they compare or hash (`is_plain`).
Worlds refuse anything else. This is the same rule JSON
over the network enforces by itself (course step 12).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol, Tuple, Union

from .identity import signature_valid

PROTOCOL_VERSION = "WCP/0.2"

MAX_PLAIN_DEPTH = 32


def is_plain(value, depth: int = 0) -> bool:
    """True if `value` is plain data all the way down: None, or exactly a
    str, int, float or bool, or a list of plain values, or a dict whose
    keys are exactly str and whose values are plain. Subclasses are not
    plain: they could redefine how they compare or hash. Nesting deeper
    than MAX_PLAIN_DEPTH (or a list that contains itself) is not plain."""
    if depth > MAX_PLAIN_DEPTH:
        return False
    kind = type(value)
    if value is None or kind in (str, int, float, bool):
        return True
    if kind is list:
        return all(is_plain(v, depth + 1) for v in value)
    if kind is dict:
        return all(type(k) is str and is_plain(v, depth + 1)
                   for k, v in value.items())
    return False


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
    when the entity has a sub-registry. Signed by the petitioner over
    `petition_document` (Individual.petition builds one)."""
    petitioner_token: str
    petitioner_name: str
    passport_admissions: Tuple[Tuple[str, str], ...]
    message: str
    target: Optional[str] = None
    seq: int = 0
    signature: str = ""


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
    """Something to do inside a world. Signed by the actor over
    `act_document` (Individual.act builds one). `attachment` is carried
    but not signed: an object only meaningful within one process (the
    registry's listing act attaches the world to list). It disappears
    when the protocol goes over the network (course step 12)."""
    actor_token: str
    type: str
    payload: Dict
    seq: int = 0
    signature: str = ""
    attachment: object = None


@dataclass(frozen=True)
class Ack:
    entity_id: str
    timestamp: str


ActResponse = Union[Ack, Refusal]


# The documents that are signed. Each names the protocol, the kind of
# request, the world it is for, and the request's number.

def petition_document(world_id: str, p: "Petition") -> Dict:
    return {"wcp": PROTOCOL_VERSION, "kind": "petition", "world": world_id,
            "token": p.petitioner_token, "name": p.petitioner_name,
            "passport": [list(pair) for pair in p.passport_admissions],
            "message": p.message, "target": p.target, "seq": p.seq}


def act_document(world_id: str, a: "Act") -> Dict:
    return {"wcp": PROTOCOL_VERSION, "kind": "act", "world": world_id,
            "token": a.actor_token, "type": a.type, "payload": a.payload,
            "seq": a.seq}


def leave_document(world_id: str, request: "Leave") -> Dict:
    return {"wcp": PROTOCOL_VERSION, "kind": "leave", "world": world_id,
            "token": request.token, "seq": request.seq}


@dataclass(frozen=True)
class Leave:
    """A request to go. Signed by the one leaving over `leave_document`
    (Individual.leave builds one), so nobody can make someone else
    leave."""
    token: str
    seq: int = 0
    signature: str = ""


@dataclass(frozen=True)
class Departure:
    """The individual has gone. already_left is True when it wasn't
    present (it never entered, or had left before)."""
    entity_id: str
    timestamp: str
    already_left: bool = False


LeaveResponse = Union[Departure, Refusal]


def request_problem(token: str, seq: object, signature: object,
                    document: Dict, last_seq: Dict[str, int]) -> str:
    """Why a signed request can't be accepted, or "" if it can. Checks
    the signature, then that `seq` is larger than any this world has seen
    from the token; records it when both hold. The caller has already
    checked that the token and the document are plain."""
    if type(seq) is not int or seq < 1:
        return "seq must be a whole number of at least 1"
    if not signature_valid(token, document, signature):
        return "The signature does not verify"
    last = last_seq.get(token, 0)
    if seq <= last:
        return (f"Out of order: this world has seen request {last} from "
                "this key; send a larger seq")
    last_seq[token] = seq
    return ""


@dataclass(frozen=True)
class LogEntry:
    """One entry in a world's public record. `actor_token` names the key
    that signed the request, or is None: a refusal of a request whose
    signature never verified names nobody, since anyone can write any
    token into a request."""
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

    def leave(self, leave: Leave) -> LeaveResponse: ...

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
        self._last_seq: Dict[str, int] = {}

    def manifest(self) -> Manifest:
        return self._manifest

    # NullWorld verifies no petitions or acts, so its log names nobody.

    def petition(self, petition: Petition) -> PetitionResponse:
        self._log.append(LogEntry(
            timestamp="(null)", kind="petition_refused", actor_token=None,
            data={"reason": "NullWorld does not admit"}))
        return Refusal(reason="NullWorld does not admit")

    def act(self, act: Act) -> ActResponse:
        self._log.append(LogEntry(
            timestamp="(null)", kind="act_refused", actor_token=None,
            data={"reason": "NullWorld does not accept acts"}))
        return Refusal(reason="NullWorld does not accept acts")

    def leave(self, leave: Leave) -> LeaveResponse:
        if type(leave) is not Leave or type(leave.token) is not str:
            return Refusal(reason="Not a leave")
        problem = request_problem(
            leave.token, leave.seq, leave.signature,
            leave_document(self._manifest.entity_id, leave), self._last_seq)
        if problem:
            return Refusal(reason=problem)
        return Departure(entity_id=self._manifest.entity_id,
                         timestamp="(null)", already_left=True)

    def log_since(self, timestamp: Optional[str] = None) -> List[LogEntry]:
        return list(self._log)
