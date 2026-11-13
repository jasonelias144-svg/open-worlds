"""The World Connection Protocol (WCP/0.4): what every entity speaks.

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
can't be sent to a world with another id, and can't be replayed. A world
checks the signature before anything else.

WCP/0.3 (course step 3): a world is a key too. Its manifest names its
key (`world_key`) and is signed by it, and every request's document
names the world's key as well as its id, so a world that copies another
world's id can't pass that world's requests on to it. A world signs a
stamp for each arrival and departure, and for what was made inside it
(passport.py); an individual's passport is the stamps it has been given,
and anyone can check it offline, without asking any world. A world keeps
the numbers it has seen in memory, and across a restart only if they are
saved and restored (keys.py, course step 6).

WCP/0.4 (course step 6): a key can be signed over to a new one, by a
succession both keys sign (succession.py). A passport carries the
successions that link its stamps to the keys they were given to: its
holder's own, and those of worlds that signed over since they stamped
it. A world refuses requests signed by a key it knows was signed over,
except a leave.

Changed from the sketch: `leave` is new. The sketch had no way to go,
and principle 3 of open-worlds is exit at any time. A world's law can
refuse a petition or an act, but never a leave. Leaving when not present
answers already_left, and changes nothing. The departure of someone who
was present is recorded in the log, kind "departure", with their token.
The only leaves a world refuses are ones that aren't the leaver's own
(not signed by them, or a replay of an old one) and ones that aren't
leaves at all (not plain values, as below). The leaver's own, well
formed, always succeeds.

`type` and `payload` of an act are opaque to the protocol: each world's
law decides what they mean.

Plain values only: what crosses the protocol (tokens, names, act types,
payloads all the way down, manifest fields) must be plain built-in values
(str, int, float, bool, list, dict with text keys, None), not subclasses
of them, which could redefine how they compare or hash (`is_plain`).
Worlds refuse anything else. This is the same rule JSON
over the network enforces by itself (course step 13).
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional, Protocol, Tuple, Union

from .identity import Signer, signature_valid, token_problem

PROTOCOL_VERSION = "WCP/0.4"

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
    sub_registry_endpoint; a multiverse has one. `world_key` is the
    entity's public key, and `signature` its signature of the manifest
    (`manifest_document`): an entity is its key, as an individual is
    (`signed_manifest` builds one)."""
    entity_id: str
    name: str
    protocol_version: str
    law_url: str
    act_endpoint: str
    log_endpoint: str
    sub_registry_endpoint: Optional[str] = None
    world_key: str = ""
    signature: str = ""

    def __post_init__(self):
        for name in ("entity_id", "name", "protocol_version",
                     "law_url", "act_endpoint", "log_endpoint"):
            value = getattr(self, name)
            if type(value) is not str or not value:
                raise ValueError(f"{name} must be non-empty plain text")
        if (self.sub_registry_endpoint is not None
                and type(self.sub_registry_endpoint) is not str):
            raise ValueError("sub_registry_endpoint must be plain text")
        if type(self.world_key) is not str or type(self.signature) is not str:
            raise ValueError("world_key and signature must be plain text")

    def has_sub_registry(self) -> bool:
        return self.sub_registry_endpoint is not None


def manifest_document(m: Manifest) -> Dict:
    """What an entity signs to say: this is me."""
    return {"wcp": PROTOCOL_VERSION, "kind": "manifest",
            "entity_id": m.entity_id, "name": m.name,
            "protocol_version": m.protocol_version, "law_url": m.law_url,
            "act_endpoint": m.act_endpoint, "log_endpoint": m.log_endpoint,
            "sub_registry_endpoint": m.sub_registry_endpoint,
            "world_key": m.world_key}


def signed_manifest(signer: Signer, **fields) -> Manifest:
    """A manifest naming `signer`'s key, signed by it."""
    unsigned = Manifest(world_key=signer.token, **fields)
    return replace(unsigned,
                   signature=signer.sign(manifest_document(unsigned)))


def manifest_problem(m: object) -> str:
    """Why a manifest isn't a usable one, or "": it must name a usable
    key and be signed by it. A good signature proves the manifest came
    from whoever holds the key; which world a key belongs to is for a
    reader to decide (by the key it was given, or a registry's listing)."""
    if type(m) is not Manifest:
        return "not a manifest"
    problem = token_problem(m.world_key)
    if problem:
        return f"its world_key is not a usable key: {problem}"
    if not signature_valid(m.world_key, manifest_document(m), m.signature):
        return "its signature does not verify against its world_key"
    return ""


@dataclass(frozen=True)
class Petition:
    """A request to enter. `passport` is the petitioner's passport, as
    plain entries: the stamps worlds have signed for it, and its own
    signed leaves (passport.Passport.entries). `target` names a
    sub-entity when the entity has a sub-registry. Signed by the
    petitioner over `petition_document` (Individual.petition builds
    one)."""
    petitioner_token: str
    petitioner_name: str
    passport: Tuple[Dict, ...]
    message: str
    target: Optional[str] = None
    seq: int = 0
    signature: str = ""


@dataclass(frozen=True)
class Admission:
    """`stamp` is the world's signed arrival stamp (passport.Stamp, as a
    plain mapping)."""
    entity_id: str
    timestamp: str
    stamp: Optional[Dict] = None


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
    when the protocol goes over the network (course step 13)."""
    actor_token: str
    type: str
    payload: Dict
    seq: int = 0
    signature: str = ""
    attachment: object = None


@dataclass(frozen=True)
class Ack:
    """`stamp`, when the act made something, is the world's signed stamp
    for it (passport.Stamp, kind "made")."""
    entity_id: str
    timestamp: str
    stamp: Optional[Dict] = None


ActResponse = Union[Ack, Refusal]


# The documents that are signed. Each names the protocol, the kind of
# request, the world it is for (by id and by key), and the request's
# number.

def petition_document(world_id: str, world_key: str, p: "Petition") -> Dict:
    return {"wcp": PROTOCOL_VERSION, "kind": "petition", "world": world_id,
            "world_key": world_key, "token": p.petitioner_token,
            "name": p.petitioner_name,
            "passport": [dict(entry) for entry in p.passport],
            "message": p.message, "target": p.target, "seq": p.seq}


def act_document(world_id: str, world_key: str, a: "Act") -> Dict:
    return {"wcp": PROTOCOL_VERSION, "kind": "act", "world": world_id,
            "world_key": world_key, "token": a.actor_token, "type": a.type,
            "payload": a.payload, "seq": a.seq}


def leave_document(world_id: str, world_key: str, request: "Leave") -> Dict:
    return {"wcp": PROTOCOL_VERSION, "kind": "leave", "world": world_id,
            "world_key": world_key, "token": request.token,
            "closes": request.closes, "seq": request.seq}


@dataclass(frozen=True)
class Leave:
    """A request to go. Signed by the one leaving over `leave_document`
    (Individual.leave builds one), so nobody can make someone else
    leave. `closes` is the fingerprint of the arrival stamp the leave
    ends, or "": signed by the leaver, the leave is its own record of
    having gone, whether or not the world stamps the departure."""
    token: str
    seq: int = 0
    signature: str = ""
    closes: str = ""


@dataclass(frozen=True)
class Departure:
    """The individual has gone. already_left is True when it wasn't
    present (it never entered, or had left before). `stamp` is the
    world's signed departure stamp, when it gives one."""
    entity_id: str
    timestamp: str
    already_left: bool = False
    stamp: Optional[Dict] = None


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
        self._key = Signer()
        self._manifest = signed_manifest(
            self._key, entity_id=entity_id, name=name,
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
        if type(leave.closes) is not str:
            return Refusal(reason="Not a leave")
        problem = request_problem(
            leave.token, leave.seq, leave.signature,
            leave_document(self._manifest.entity_id,
                           self._manifest.world_key, leave), self._last_seq)
        if problem:
            return Refusal(reason=problem)
        return Departure(entity_id=self._manifest.entity_id,
                         timestamp="(null)", already_left=True)

    def log_since(self, timestamp: Optional[str] = None) -> List[LogEntry]:
        return list(self._log)
