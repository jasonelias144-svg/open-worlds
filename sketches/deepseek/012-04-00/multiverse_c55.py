"""
multiverse_c55.py — Component 55: The World Curator.

A meta-architecture layer: each world has a curator — its
representative to the outside, and the entity that proposes its
own development.

The curator IS the world's voice: it holds the world's signing
key (C13, C28), observes the world's state (C3's log_since),
and signs messages on the world's behalf. Residents (C1
identities) are unchanged. The world's Law is unchanged. What's
new is a first-class agent whose job is to maintain the world's
relationship to other worlds and to propose its evolution.

What the curator can do:
  - observe()          read-only snapshot of its own world
  - hello()            advertise itself to another world
  - status_report()    summarize recent activity
  - propose_law_change()   sign a proposal (does not auto-apply)
  - request_link()     request a formal link with another world
  - receive()          process an incoming message
  - observe_and_propose()  use an optional model to generate a proposal

What the curator CANNOT do:
  - Change the world's Law unilaterally. It proposes; the world's
    own mechanism (or external authority) applies.
  - Read any other world's state. Each curator sees only its own.
  - Act as a resident. Residents are C1 identities; the curator
    is the world's voice, not a resident.

What "learning" means here, honestly:
  The curator has a policy (a model backend) that maps an
  observation to a proposal. The prototype's mock backend
  produces fixed proposals based on triggers (many refusals,
  slow convergence, epoch growth). A real model would produce
  semantically meaningful proposals. The proposals are signed
  and inspectable, so a third party can judge them regardless
  of how they were generated.

Composition:
  - C1 Identity, C13 KeyPair, C28 signed manifest.
  - C3 log_since for observation.
  - CuratorMessages wrap as C48 FederationAttestations.
  - CuratorLog is bundleable via C49-style persistence.

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per behavior, plus structural tests
    (curator has no C41-C52 unit attrs; is not a world).
  - "A world never raises on what a visitor sends" — receive()
    returns Refusal; verifiers return verdicts.
  - "History, not rank" — the curator log is a record.

Honest limits (documented, tested):
  - Learning is minimal. The mock backend is deterministic.
    A real backend's proposals are only as good as the model.
  - Law proposals do not auto-apply. The prototype has no Law
    amendment mechanism; a proposal is a signed artifact, not
    a change to any world.
  - Manifest changes are not coupled to proposals. A world's
    manifest can be updated (C28), and separately a curator
    can propose something. The two are not linked.
  - Links bind to the world IDs and establishment time, not to
    manifests. A world's manifest rotation does not invalidate
    a link; future messages verify against the world's current
    manifest.
  - No link revocation. Once established, stands.
  - No content verification of status reports or proposals.
    The message is signed; whether it's accurate is the
    recipient's to judge.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from multiverse_c1 import Identity, create_identity
from multiverse_c3 import Act, Ack, Refusal
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_payload(p: bytes) -> str:
    return hashlib.sha256(p).hexdigest()


CURATOR_MESSAGE_TYPES = frozenset({
    "hello",
    "status_report",
    "law_proposal",
    "link_request",
})


# =====================================================================
# CuratorIdentity
# =====================================================================

@dataclass(frozen=True)
class CuratorIdentity:
    """The curator's identity, bound to its world."""
    world_id: str
    world_name: str
    world_public_key: str

    def __post_init__(self):
        for f in ("world_id", "world_name", "world_public_key"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if len(self.world_public_key) != 64:
            raise ValueError(
                "world_public_key must be 64 hex chars")

    def to_dict(self) -> Dict:
        return {
            "world_id": self.world_id,
            "world_name": self.world_name,
            "world_public_key": self.world_public_key,
        }


# =====================================================================
# WorldObservation
# =====================================================================

@dataclass(frozen=True)
class WorldObservation:
    """A read-only snapshot of a world. This is what the curator
    sees and what its model reasons about."""
    world_id: str
    manifest: Dict
    manifest_hash: str
    recent_entries: Tuple[Dict, ...]
    epoch: Optional[int]
    stats: Dict

    def summary(self) -> Dict:
        """The subset a model backend sees. Kept small and
        structured so the model's behavior is inspectable."""
        return {
            "world_id": self.world_id,
            "epoch": self.epoch,
            "recent_entry_count": len(self.recent_entries),
            "stats": dict(self.stats),
        }

    def to_dict(self) -> Dict:
        return {
            "world_id": self.world_id,
            "manifest": self.manifest,
            "manifest_hash": self.manifest_hash,
            "recent_entries": [
                e if isinstance(e, dict) else e for e in
                self.recent_entries],
            "epoch": self.epoch,
            "stats": dict(self.stats),
        }


# =====================================================================
# CuratorMessage
# =====================================================================

@dataclass(frozen=True)
class CuratorMessage:
    """A signed message from one world's curator.

    Signed by the world's key, so it is a statement the world
    itself makes. Verifiable by anyone with the world's public key.
    """
    sender_world_id: str
    sender_public_key: str
    sender_manifest_hash: str
    message_type: str
    payload: Dict
    timestamp: str
    signature: str

    def __post_init__(self):
        if not self.sender_world_id:
            raise ValueError("sender_world_id required")
        if len(self.sender_public_key) != 64:
            raise ValueError(
                "sender_public_key must be 64 hex chars")
        if len(self.sender_manifest_hash) != 64:
            raise ValueError(
                "sender_manifest_hash must be 64 hex chars")
        if self.message_type not in CURATOR_MESSAGE_TYPES:
            raise ValueError(
                f"message_type must be one of "
                f"{sorted(CURATOR_MESSAGE_TYPES)}")
        if not isinstance(self.payload, dict):
            raise ValueError("payload must be a dict")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "curator_message",
            "sender_world_id": self.sender_world_id,
            "sender_public_key": self.sender_public_key,
            "sender_manifest_hash": self.sender_manifest_hash,
            "message_type": self.message_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
        })

    def message_hash(self) -> str:
        return _hash_payload(self.canonical_payload())

    def to_dict(self) -> Dict:
        return {
            "sender_world_id": self.sender_world_id,
            "sender_public_key": self.sender_public_key,
            "sender_manifest_hash": self.sender_manifest_hash,
            "message_type": self.message_type,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "CuratorMessage":
        return cls(
            sender_world_id=d["sender_world_id"],
            sender_public_key=d["sender_public_key"],
            sender_manifest_hash=d["sender_manifest_hash"],
            message_type=d["message_type"],
            payload=d["payload"],
            timestamp=d["timestamp"],
            signature=d["signature"],
        )


def verify_curator_message(
    message: CuratorMessage,
    expected_public_key: Optional[str] = None,
) -> bool:
    """True iff the message's signature verifies. Never raises."""
    if not HAS_CRYPTO:
        return False
    try:
        if not isinstance(message, CuratorMessage):
            return False
        key = expected_public_key or message.sender_public_key
        return verify_signature(
            key, message.canonical_payload(),
            message.signature)
    except Exception:
        return False


# =====================================================================
# WorldLink
# =====================================================================

@dataclass(frozen=True)
class WorldLink:
    """A formal link between two worlds. Established when both
    worlds' curators have produced a hello addressed to each
    other. The link is the pair, not a new signature kind."""
    hello_a: CuratorMessage
    hello_b: CuratorMessage
    established_at: str

    def __post_init__(self):
        if self.hello_a.message_type != "hello":
            raise ValueError("hello_a must be a hello")
        if self.hello_b.message_type != "hello":
            raise ValueError("hello_b must be a hello")
        a_target = self.hello_a.payload.get("target_world_id")
        b_target = self.hello_b.payload.get("target_world_id")
        if a_target != self.hello_b.sender_world_id:
            raise ValueError(
                "hello_a does not target hello_b's sender")
        if b_target != self.hello_a.sender_world_id:
            raise ValueError(
                "hello_b does not target hello_a's sender")

    def world_a_id(self) -> str:
        return self.hello_a.sender_world_id

    def world_b_id(self) -> str:
        return self.hello_b.sender_world_id

    def link_hash(self) -> str:
        return _hash_payload(canonical_bytes({
            "kind": "world_link",
            "hello_a_hash": self.hello_a.message_hash(),
            "hello_b_hash": self.hello_b.message_hash(),
            "established_at": self.established_at,
        }))

    def to_dict(self) -> Dict:
        return {
            "hello_a": self.hello_a.to_dict(),
            "hello_b": self.hello_b.to_dict(),
            "established_at": self.established_at,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "WorldLink":
        return cls(
            hello_a=CuratorMessage.from_dict(d["hello_a"]),
            hello_b=CuratorMessage.from_dict(d["hello_b"]),
            established_at=d["established_at"],
        )


def verify_world_link(
    link: WorldLink,
    world_a_public_key: Optional[str] = None,
    world_b_public_key: Optional[str] = None,
) -> bool:
    """Verify both hellos in the link. Never raises."""
    if not HAS_CRYPTO:
        return False
    try:
        if not isinstance(link, WorldLink):
            return False
        key_a = (world_a_public_key
                  or link.hello_a.sender_public_key)
        key_b = (world_b_public_key
                  or link.hello_b.sender_public_key)
        return (
            verify_curator_message(link.hello_a, key_a)
            and verify_curator_message(link.hello_b, key_b)
        )
    except Exception:
        return False


# =====================================================================
# CuratorLogEntry
# =====================================================================

@dataclass(frozen=True)
class CuratorLogEntry:
    timestamp: str
    kind: str
    actor_world_id: str
    data: Dict

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "kind": self.kind,
            "actor_world_id": self.actor_world_id,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "CuratorLogEntry":
        return cls(
            timestamp=d["timestamp"],
            kind=d["kind"],
            actor_world_id=d["actor_world_id"],
            data=d.get("data", {}),
        )


# =====================================================================
# Model backend
# =====================================================================

class CuratorModelBackend:
    """Anything that can produce a proposal from an observation
    summary. Return None to mean "no proposal warranted"."""
    def generate(self, summary: Dict) -> Optional[Dict]:
        raise NotImplementedError

    def model_id(self) -> str:
        raise NotImplementedError


class MockCuratorModel(CuratorModelBackend):
    """A deterministic mock: fixed proposals based on observation
    triggers. Honest about being a mock — a real model would
    produce semantically meaningful proposals."""
    def __init__(self):
        self._calls = 0

    def model_id(self) -> str:
        return "mock:curator-v0"

    def generate(self, summary: Dict) -> Optional[Dict]:
        self._calls += 1
        stats = summary.get("stats", {})
        refusals = stats.get("refusals", 0)
        converged = stats.get("convergences", 0)
        epoch = summary.get("epoch")
        if refusals >= 3 and converged == 0:
            return {
                "title": "Relax rule acceptance",
                "rationale": (
                    f"{refusals} refusals and 0 convergences "
                    f"suggests rules are too strict"),
                "body": {"suggested_change":
                          "expand accepted act types"},
            }
        if epoch is not None and epoch > 50 and converged == 0:
            return {
                "title": "Adjust convergence window",
                "rationale": (
                    f"epoch {epoch} with no convergence; "
                    "window may be too wide"),
                "body": {"suggested_change":
                          "reduce convergence_window"},
            }
        return None


# =====================================================================
# WorldCurator
# =====================================================================

class WorldCurator:
    """The world's representative. Holds the world's signing key,
    observes its state, signs messages, establishes links."""

    def __init__(
        self,
        world: Any,
        world_kp: KeyPair,
        model_backend: Optional[CuratorModelBackend] = None,
    ):
        if not HAS_CRYPTO:
            raise RuntimeError(
                "WorldCurator requires `cryptography`")
        self._world = world
        self._world_kp = world_kp
        self._model = model_backend or MockCuratorModel()
        self._log: List[CuratorLogEntry] = []
        self._links: Dict[str, WorldLink] = {}
        self._pending_hellos: Dict[str, CuratorMessage] = {}

    @property
    def world_id(self) -> str:
        return self._world.manifest().entity_id

    @property
    def public_key(self) -> str:
        return self._world_kp.public_key_hex()

    @property
    def identity(self) -> CuratorIdentity:
        m = self._world.manifest()
        return CuratorIdentity(
            world_id=m.entity_id,
            world_name=m.name,
            world_public_key=self.public_key,
        )

    def links(self) -> List[WorldLink]:
        return list(self._links.values())

    def log_entries(self) -> List[CuratorLogEntry]:
        return list(self._log)

    # -- Observation -------------------------------------------

    def observe(self) -> WorldObservation:
        manifest = self._world.manifest()
        manifest_dict = {
            "entity_id": manifest.entity_id,
            "name": manifest.name,
            "protocol_version": manifest.protocol_version,
            "law_url": manifest.law_url,
            "act_endpoint": manifest.act_endpoint,
            "log_endpoint": manifest.log_endpoint,
            "sub_registry_endpoint":
                manifest.sub_registry_endpoint,
        }
        manifest_hash = _hash_payload(canonical_bytes(
            manifest_dict))
        recent = self._world.log_since(None)[-100:]
        recent_dicts = tuple(
            {"timestamp": e.timestamp,
             "kind": e.kind,
             "actor_token": e.actor_token,
             "data": dict(e.data)}
            for e in recent)
        # Compute stats from the log
        stats = {
            "admissions": sum(
                1 for e in recent if e.kind == "admission"),
            "refusals": sum(
                1 for e in recent if "refused" in e.kind),
            "turns": sum(
                1 for e in recent
                if e.kind in ("turn", "reaction", "contraction",
                              "fire", "signal", "ruling",
                              "exposure")),
            "convergences": sum(
                1 for e in recent if e.kind == "convergence"),
        }
        epoch = getattr(self._world, "_epoch", None)
        return WorldObservation(
            world_id=manifest.entity_id,
            manifest=manifest_dict,
            manifest_hash=manifest_hash,
            recent_entries=recent_dicts,
            epoch=epoch,
            stats=stats,
        )

    # -- Message construction ---------------------------------

    def _sign_message(
        self, message_type: str, payload: Dict,
    ) -> CuratorMessage:
        if message_type not in CURATOR_MESSAGE_TYPES:
            raise ValueError(
                f"unknown message_type {message_type!r}")
        ts = _now()
        obs = self.observe()
        body = canonical_bytes({
            "kind": "curator_message",
            "sender_world_id": self.world_id,
            "sender_public_key": self.public_key,
            "sender_manifest_hash": obs.manifest_hash,
            "message_type": message_type,
            "payload": payload,
            "timestamp": ts,
        })
        sig = self._world_kp.sign(body).hex()
        return CuratorMessage(
            sender_world_id=self.world_id,
            sender_public_key=self.public_key,
            sender_manifest_hash=obs.manifest_hash,
            message_type=message_type,
            payload=payload,
            timestamp=ts,
            signature=sig,
        )

    def hello(self, target_world_id: str) -> CuratorMessage:
        """A hello addressed to a target world."""
        msg = self._sign_message(
            "hello", {"target_world_id": target_world_id})
        self._log.append(CuratorLogEntry(
            timestamp=msg.timestamp,
            kind="message_sent",
            actor_world_id=self.world_id,
            data={"message_type": "hello",
                   "target": target_world_id,
                   "message_hash": msg.message_hash()},
        ))
        return msg

    def status_report(self) -> CuratorMessage:
        obs = self.observe()
        payload = {
            "epoch": obs.epoch,
            "manifest_hash": obs.manifest_hash,
            "stats": dict(obs.stats),
            "recent_kinds": sorted(set(
                e["kind"] for e in obs.recent_entries)),
        }
        msg = self._sign_message("status_report", payload)
        self._log.append(CuratorLogEntry(
            timestamp=msg.timestamp,
            kind="message_sent",
            actor_world_id=self.world_id,
            data={"message_type": "status_report",
                   "message_hash": msg.message_hash()},
        ))
        return msg

    def propose_law_change(
        self, title: str, rationale: str, body: Dict,
    ) -> CuratorMessage:
        payload = {
            "title": title,
            "rationale": rationale,
            "body": body,
        }
        msg = self._sign_message("law_proposal", payload)
        self._log.append(CuratorLogEntry(
            timestamp=msg.timestamp,
            kind="proposal_generated",
            actor_world_id=self.world_id,
            data={"title": title,
                   "message_hash": msg.message_hash()},
        ))
        return msg

    def request_link(
        self, target_world_id: str,
    ) -> CuratorMessage:
        """A link request is a hello addressed to target. When
        target sends a hello back, both curators hold a link."""
        msg = self._sign_message(
            "link_request",
            {"target_world_id": target_world_id})
        self._log.append(CuratorLogEntry(
            timestamp=msg.timestamp,
            kind="message_sent",
            actor_world_id=self.world_id,
            data={"message_type": "link_request",
                   "target": target_world_id,
                   "message_hash": msg.message_hash()},
        ))
        return msg

    # -- Receiving --------------------------------------------

    def receive(self, message: CuratorMessage):
        """Process an incoming message. Returns Ack (accepted) or
        Refusal (rejected). Never raises for bad input."""
        if not isinstance(message, CuratorMessage):
            return Refusal(reason="not a CuratorMessage")
        if not verify_curator_message(
                message, message.sender_public_key):
            self._log.append(CuratorLogEntry(
                timestamp=_now(),
                kind="message_refused",
                actor_world_id=message.sender_world_id,
                data={"reason": "signature invalid",
                       "message_type": message.message_type},
            ))
            return Refusal(reason="signature invalid")
        if message.sender_world_id == self.world_id:
            return Refusal(reason="cannot receive own message")

        self._log.append(CuratorLogEntry(
            timestamp=_now(),
            kind="message_received",
            actor_world_id=message.sender_world_id,
            data={"message_type": message.message_type,
                   "message_hash": message.message_hash()},
        ))
        if message.message_type == "hello":
            self._pending_hellos[message.sender_world_id] = message
        elif message.message_type == "link_request":
            self._pending_hellos[message.sender_world_id] = message
        # Other types are just logged
        return Ack(
            entity_id=self.world_id, timestamp=_now())

    def respond_hello(
        self, received: CuratorMessage,
    ) -> Tuple[Ack, Optional[WorldLink]]:
        """Respond to a hello or link_request with a hello.
        If the sender already had a pending hello with us (both
        sides have now hello'd), establish a link.

        Returns (Ack_or_Refusal, link_or_None)."""
        if not isinstance(received, CuratorMessage):
            return (Refusal(reason="not a message"), None)
        if received.message_type not in (
                "hello", "link_request"):
            return (Refusal(
                reason="respond_hello requires hello or "
                        "link_request"), None)
        if not verify_curator_message(received):
            return (Refusal(reason="invalid hello signature"),
                     None)
        sender_id = received.sender_world_id
        # Reply with our own hello
        reply = self.hello(sender_id)
        # If we already have a pending hello from this sender,
        # a link is established
        other = self._pending_hellos.get(sender_id)
        if other is not None:
            link = WorldLink(
                hello_a=other,  # their hello to us
                hello_b=reply,  # our hello to them
                established_at=_now(),
            )
            self._links[sender_id] = link
            self._log.append(CuratorLogEntry(
                timestamp=link.established_at,
                kind="link_established",
                actor_world_id=sender_id,
                data={"with": sender_id,
                       "link_hash": link.link_hash()},
            ))
            return (Ack(entity_id=self.world_id,
                          timestamp=_now()), link)
        return (Ack(entity_id=self.world_id,
                     timestamp=_now()), None)

    # -- Observation-driven proposal --------------------------

    def observe_and_propose(self) -> Optional[CuratorMessage]:
        """Let the model see a summary of our world and, if it
        proposes something, sign and return it."""
        obs = self.observe()
        try:
            proposal = self._model.generate(obs.summary())
        except Exception as e:
            self._log.append(CuratorLogEntry(
                timestamp=_now(),
                kind="model_error",
                actor_world_id=self.world_id,
                data={"error": str(e)},
            ))
            return None
        if not isinstance(proposal, dict):
            return None
        return self.propose_law_change(
            title=proposal.get("title", "(untitled)"),
            rationale=proposal.get("rationale", ""),
            body=proposal.get("body", {}),
        )


def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Two worlds, A and B. Their curators establish a link,
    exchange hellos, status reports, and law proposals. A's
    curator uses its mock model to generate a proposal based on
    its own observation. B's curator logs it.

    Anchor: Dickinson, 'The Brain – is wider than the Sky –'
    (the curator is the world's representative to the outside;
    the sky is the space between worlds).
    """
    import json
    from pathlib import Path
    from multiverse_c4 import PoetryWorld
    from multiverse_c5 import ChemistryWorld

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir)
    path.mkdir(parents=True, exist_ok=True)

    # Two worlds
    world_a = PoetryWorld("world:poetry", "Poetry")
    world_b = ChemistryWorld("world:chemistry", "Chemistry")
    # Some activity in A so its stats are non-trivial
    from multiverse_c3 import Act
    world_a._log.append(type(world_a._log[0])(**{
        "timestamp": _now(), "kind": "turn",
        "actor_token": "x", "data": {}}))
    for _ in range(3):
        world_a._log.append(type(world_a._log[0])(**{
            "timestamp": _now(), "kind": "act_refused",
            "actor_token": "y", "data": {"reason": "test"}}))

    kp_a = KeyPair.generate()
    kp_b = KeyPair.generate()
    curator_a = WorldCurator(
        world_a, kp_a, model_backend=MockCuratorModel())
    curator_b = WorldCurator(
        world_b, kp_b, model_backend=MockCuratorModel())

    # Step 1: A requests a link with B
    link_req = curator_a.request_link(curator_b.world_id)

    # Step 2: B receives and responds
    ack, link_from_b = curator_b.receive(link_req)
    assert isinstance(ack, Ack)
    ack2, link_from_b2 = curator_b.respond_hello(link_req)
    assert isinstance(ack2, Ack)

    # Step 3: A receives B's hello, establishing the link on A's side
    b_hello = curator_b.hello(curator_a.world_id)
    ack3, link_from_a = curator_a.respond_hello(link_req)
    # Actually: A received no hello yet; let's simulate the flow
    # properly. A requested link; B received and produced a link
    # (link_from_b2). A needs to receive B's hello to complete.
    ack_a = curator_a.receive(curator_b.hello(curator_a.world_id))
    assert isinstance(ack_a, Ack)
    ack_a2, link_from_a2 = curator_a.respond_hello(link_req)

    # Now both should have links
    links_a = curator_a.links()
    links_b = curator_b.links()
    assert len(links_a) == 1
    assert len(links_b) == 1
    link_a = links_a[0]
    link_b = links_b[0]

    # Step 4: A sends a status report to B
    status = curator_a.status_report()
    ack_status = curator_b.receive(status)

    # Step 5: A uses its model to observe and propose
    proposal = curator_a.observe_and_propose()

    # Step 6: B receives A's proposal
    ack_proposal = None
    if proposal is not None:
        ack_proposal = curator_b.receive(proposal)

    # Verification
    link_ok = verify_world_link(
        link_a, kp_a.public_key_hex(), kp_b.public_key_hex())
    msg_ok = verify_curator_message(proposal) if proposal else True

    print("=" * 70)
    print("World Curator — two worlds' representatives")
    print("=" * 70)
    print()
    print(f"  Curator A: {curator_a.world_id} ({curator_a.public_key[:16]}...)")
    print(f"  Curator B: {curator_b.world_id} ({curator_b.public_key[:16]}...)")
    print()
    print(f"  Link established: {link_ok}")
    print(f"    A → B hello hash: {link_a.hello_a.message_hash()[:16]}...")
    print(f"    B → A hello hash: {link_a.hello_b.message_hash()[:16]}...")
    print()
    print(f"  A sent status_report: "
          f"{isinstance(ack_status, Ack) and 'received' or 'refused'}")
    if proposal is not None:
        print(f"  A's model proposed: {proposal.payload.get('title')!r}")
        print(f"    rationale: {proposal.payload.get('rationale')}")
        print(f"    signature verifies: {msg_ok}")
        print(f"    B received: "
              f"{isinstance(ack_proposal, Ack) and 'yes' or 'no'}")
    else:
        print("  A's model: no proposal warranted")
    print()
    print(f"  A's log: {len(curator_a.log_entries())} entries")
    print(f"  B's log: {len(curator_b.log_entries())} entries")
    print()
    print("  What this demonstrates:")
    print("    - Each world has a curator — its voice to the outside.")
    print("    - Curator messages are signed by the world's own key.")
    print("    - A link is a pair of hellos, both signed, verified.")
    print("    - The curator observes its world's state and, using")
    print("      an optional model, proposes changes (never applies them).")
    print("    - Every step is a signed artifact; no new primitive")
    print("      beyond what C1, C3, C13, C28 already provide.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'The Brain – is wider than the Sky –'")
    print("    'For – put them side by side –'")

    audit = {
        "curator_a": curator_a.identity.to_dict(),
        "curator_b": curator_b.identity.to_dict(),
        "link_established": link_ok,
        "link_hash": link_a.link_hash(),
        "status_report_ok": isinstance(ack_status, Ack),
        "proposal_generated": proposal is not None,
        "proposal_title":
            proposal.payload.get("title") if proposal else None,
        "proposal_verified": msg_ok,
        "proposal_received": isinstance(ack_proposal, Ack)
            if proposal else None,
        "curator_a_log_count": len(curator_a.log_entries()),
        "curator_b_log_count": len(curator_b.log_entries()),
    }
    (path / "curator_demo.json").write_text(
        json.dumps(audit, indent=2))
    print(f"\n  → {path}/curator_demo.json")
    return audit
