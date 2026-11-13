"""
multiverse_c79.py — Component 79: The Reference LTS Implementation.

C78 specified LTS/0.1. C79 implements it.

What it delivers:

  - RoomLifecycleEvent: the atom. Signed by the parent's
    curator key, chained via prior_event_hash per
    (parent, room) pair. Three event types: registered,
    retired, updated.

  - TreeSubscription: a client's signed claim it wants to
    receive tree events from a root. Depth-limited,
    resume-capable via since_event_hash.

  - TreeEventNotification: an event delivered to a
    subscriber, carrying a relay chain (each hop signed).

  - LivingRoomWorld: a RoomWorld whose directory is
    reconstructed from the signed event chain rather than
    from a mutable map. It fires signed events on
    register/unregister/update and delivers them to
    subscribers.

  - LivingRoomWorldServer: a WCP server that adds
    GET /events, GET /events/since/<hash>, POST /subscribe.

  - TreeSubscriber: a client-side daemon that runs an HTTP
    callback, receives notifications, verifies them against
    the parent's key and the chain, and maintains a local
    event log.

  - verify_lifecycle_chain: a third party's verification
    of a full event log.

  - reconstruct_rooms_from_events: historical state
    reconstruction from the chain.

Composition: C3 (Manifest, Route), C13 (sign/verify),
C55 (curator keys), C56 (relay chain pattern), C74
(RoomWorld), C77 (UrlResolvingRoomWorld). No new
primitives.

Honest limits (documented, tested):
  - No fork resolution. A parent producing two events
    with the same prior_event_hash is detected by
    verify_lifecycle_chain as a fork; C79 reports it but
    does not resolve it. LTS/0.1 §11.
  - No signed subscription withdrawal. A subscriber
    stops receiving events by not answering its
    callback; there is no signed "I withdraw" artifact.
  - Callback endpoints are HTTP, not HTTPS. Production
    must use TLS.
  - Subscription is push-based. A subscriber must be
    reachable at callback_url. NAT'd subscribers can't
    easily receive events; a pull-based alternative is
    future work.
  - Backfill fetches all events from the parent; a real
    deployment would index by event hash server-side.
  - No relay beyond the parent itself. The relay_chain
    in TreeEventNotification has one entry (the parent
    as direct deliverer). Multi-hop relaying — a
    subscriber forwarding to its own subscribers — is
    structurally supported by the format but not
    implemented.
"""

import json
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from multiverse_c3 import (
    Manifest, Petition, Act, LogEntry, Route, Ack, Refusal,
)
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c74 import RoomEntry
from multiverse_c77 import (
    UrlResolvingRoomWorld, resolve_manifest_urls,
)
from wcp_http_shim import WorldProtocolServer


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_payload(p: bytes) -> str:
    import hashlib
    return hashlib.sha256(p).hexdigest()


LIFECYCLE_EVENT_TYPES = frozenset({
    "registered", "retired", "updated"})


# =====================================================================
# RoomLifecycleEvent
# =====================================================================

@dataclass(frozen=True)
class RoomLifecycleEvent:
    event_type: str
    parent_id: str
    room_id: str
    room_url: str
    room_public_key: str
    room_name: str
    room_description: str
    prior_event_hash: Optional[str]
    timestamp: str
    signer_id: str
    signer_public_key: str
    signature: str

    def __post_init__(self):
        if self.event_type not in LIFECYCLE_EVENT_TYPES:
            raise ValueError(
                f"event_type must be one of "
                f"{sorted(LIFECYCLE_EVENT_TYPES)}; "
                f"got {self.event_type!r}")
        for f in ("parent_id", "room_id", "timestamp",
                  "signer_id", "signer_public_key",
                  "signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if len(self.signer_public_key) != 64:
            raise ValueError(
                "signer_public_key must be 64 hex chars")
        if self.prior_event_hash is not None \
                and len(self.prior_event_hash) != 64:
            raise ValueError(
                "prior_event_hash must be 64 hex chars or None")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "room_lifecycle_event",
            "event_type": self.event_type,
            "parent_id": self.parent_id,
            "room_id": self.room_id,
            "room_url": self.room_url,
            "room_public_key": self.room_public_key,
            "room_name": self.room_name,
            "room_description": self.room_description,
            "prior_event_hash": self.prior_event_hash,
            "timestamp": self.timestamp,
            "signer_id": self.signer_id,
            "signer_public_key": self.signer_public_key,
        })

    def event_hash(self) -> str:
        return _hash_payload(self.canonical_payload())

    def to_dict(self) -> Dict:
        d = json.loads(self.canonical_payload().decode())
        d["signature"] = self.signature
        return d

    @classmethod
    def from_dict(cls, d: Dict) -> "RoomLifecycleEvent":
        return cls(
            event_type=d["event_type"],
            parent_id=d["parent_id"],
            room_id=d["room_id"],
            room_url=d.get("room_url", ""),
            room_public_key=d.get("room_public_key", ""),
            room_name=d.get("room_name", ""),
            room_description=d.get("room_description", ""),
            prior_event_hash=d.get("prior_event_hash"),
            timestamp=d["timestamp"],
            signer_id=d["signer_id"],
            signer_public_key=d["signer_public_key"],
            signature=d["signature"],
        )


def sign_lifecycle_event(
    event_type: str,
    parent_id: str,
    signer_id: str,
    signer_kp: KeyPair,
    room_id: str,
    room_url: str = "",
    room_public_key: str = "",
    room_name: str = "",
    room_description: str = "",
    prior_event_hash: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> RoomLifecycleEvent:
    if not HAS_CRYPTO:
        raise RuntimeError(
            "sign_lifecycle_event requires cryptography")
    if timestamp is None:
        timestamp = _now()
    payload = canonical_bytes({
        "kind": "room_lifecycle_event",
        "event_type": event_type,
        "parent_id": parent_id,
        "room_id": room_id,
        "room_url": room_url,
        "room_public_key": room_public_key,
        "room_name": room_name,
        "room_description": room_description,
        "prior_event_hash": prior_event_hash,
        "timestamp": timestamp,
        "signer_id": signer_id,
        "signer_public_key": signer_kp.public_key_hex(),
    })
    return RoomLifecycleEvent(
        event_type=event_type,
        parent_id=parent_id,
        room_id=room_id,
        room_url=room_url,
        room_public_key=room_public_key,
        room_name=room_name,
        room_description=room_description,
        prior_event_hash=prior_event_hash,
        timestamp=timestamp,
        signer_id=signer_id,
        signer_public_key=signer_kp.public_key_hex(),
        signature=signer_kp.sign(payload).hex(),
    )


def verify_lifecycle_event(
    event: RoomLifecycleEvent,
    expected_parent_key: Optional[str] = None,
) -> bool:
    if not HAS_CRYPTO:
        return False
    try:
        if not isinstance(event, RoomLifecycleEvent):
            return False
        key = expected_parent_key or event.signer_public_key
        return verify_signature(
            key, event.canonical_payload(), event.signature)
    except Exception:
        return False


# =====================================================================
# TreeSubscription
# =====================================================================

@dataclass(frozen=True)
class TreeSubscription:
    subscriber_id: str
    subscriber_public_key: str
    root_id: str
    root_url: str
    depth: int
    callback_url: str
    since_event_hash: Optional[str]
    timestamp: str
    signer_id: str
    signer_public_key: str
    signature: str

    def __post_init__(self):
        for f in ("subscriber_id", "subscriber_public_key",
                  "root_id", "root_url", "callback_url",
                  "timestamp", "signer_id",
                  "signer_public_key", "signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if len(self.subscriber_public_key) != 64:
            raise ValueError(
                "subscriber_public_key must be 64 hex chars")
        if len(self.signer_public_key) != 64:
            raise ValueError(
                "signer_public_key must be 64 hex chars")
        if not (1 <= self.depth <= 8):
            raise ValueError("depth must be in [1, 8]")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "tree_subscription",
            "subscriber_id": self.subscriber_id,
            "subscriber_public_key": self.subscriber_public_key,
            "root_id": self.root_id,
            "root_url": self.root_url,
            "depth": self.depth,
            "callback_url": self.callback_url,
            "since_event_hash": self.since_event_hash,
            "timestamp": self.timestamp,
            "signer_id": self.signer_id,
            "signer_public_key": self.signer_public_key,
        })

    def subscription_hash(self) -> str:
        return _hash_payload(self.canonical_payload())

    def to_dict(self) -> Dict:
        d = json.loads(self.canonical_payload().decode())
        d["signature"] = self.signature
        return d

    @classmethod
    def from_dict(cls, d: Dict) -> "TreeSubscription":
        return cls(
            subscriber_id=d["subscriber_id"],
            subscriber_public_key=d["subscriber_public_key"],
            root_id=d["root_id"],
            root_url=d["root_url"],
            depth=int(d["depth"]),
            callback_url=d["callback_url"],
            since_event_hash=d.get("since_event_hash"),
            timestamp=d["timestamp"],
            signer_id=d["signer_id"],
            signer_public_key=d["signer_public_key"],
            signature=d["signature"],
        )


def sign_tree_subscription(
    subscriber_id: str,
    subscriber_kp: KeyPair,
    signer_id: str,
    signer_kp: KeyPair,
    root_id: str,
    root_url: str,
    callback_url: str,
    depth: int = 3,
    since_event_hash: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> TreeSubscription:
    if not HAS_CRYPTO:
        raise RuntimeError(
            "sign_tree_subscription requires cryptography")
    if timestamp is None:
        timestamp = _now()
    payload = canonical_bytes({
        "kind": "tree_subscription",
        "subscriber_id": subscriber_id,
        "subscriber_public_key":
            subscriber_kp.public_key_hex(),
        "root_id": root_id,
        "root_url": root_url,
        "depth": depth,
        "callback_url": callback_url,
        "since_event_hash": since_event_hash,
        "timestamp": timestamp,
        "signer_id": signer_id,
        "signer_public_key": signer_kp.public_key_hex(),
    })
    return TreeSubscription(
        subscriber_id=subscriber_id,
        subscriber_public_key=subscriber_kp.public_key_hex(),
        root_id=root_id,
        root_url=root_url,
        depth=depth,
        callback_url=callback_url,
        since_event_hash=since_event_hash,
        timestamp=timestamp,
        signer_id=signer_id,
        signer_public_key=signer_kp.public_key_hex(),
        signature=signer_kp.sign(payload).hex(),
    )


def verify_tree_subscription(
    sub: TreeSubscription,
    expected_subscriber_key: Optional[str] = None,
) -> bool:
    if not HAS_CRYPTO:
        return False
    try:
        if not isinstance(sub, TreeSubscription):
            return False
        key = (expected_subscriber_key
               or sub.subscriber_public_key)
        return verify_signature(
            key, sub.canonical_payload(), sub.signature)
    except Exception:
        return False


# =====================================================================
# TreeEventNotification
# =====================================================================

@dataclass(frozen=True)
class RelayHop:
    relayer_id: str
    relayer_public_key: str
    received_at: str
    prior_relay_hash: Optional[str]
    signature: str

    def canonical_payload(
        self, subscription_hash: str, event_hash: str,
    ) -> bytes:
        return canonical_bytes({
            "kind": "tree_event_relay",
            "subscription_hash": subscription_hash,
            "event_hash": event_hash,
            "relayer_id": self.relayer_id,
            "relayer_public_key": self.relayer_public_key,
            "received_at": self.received_at,
            "prior_relay_hash": self.prior_relay_hash,
        })

    def relay_hash(
        self, subscription_hash: str, event_hash: str,
    ) -> str:
        return _hash_payload(
            self.canonical_payload(subscription_hash, event_hash))

    def to_dict(self) -> Dict:
        return {
            "relayer_id": self.relayer_id,
            "relayer_public_key": self.relayer_public_key,
            "received_at": self.received_at,
            "prior_relay_hash": self.prior_relay_hash,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "RelayHop":
        return cls(
            relayer_id=d["relayer_id"],
            relayer_public_key=d["relayer_public_key"],
            received_at=d["received_at"],
            prior_relay_hash=d.get("prior_relay_hash"),
            signature=d["signature"],
        )


@dataclass(frozen=True)
class TreeEventNotification:
    subscription_hash: str
    event: RoomLifecycleEvent
    delivered_at: str
    relay_chain: Tuple[RelayHop, ...]

    def to_dict(self) -> Dict:
        return {
            "kind": "tree_event_notification",
            "subscription_hash": self.subscription_hash,
            "event": self.event.to_dict(),
            "delivered_at": self.delivered_at,
            "relay_chain": [h.to_dict()
                             for h in self.relay_chain],
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "TreeEventNotification":
        return cls(
            subscription_hash=d["subscription_hash"],
            event=RoomLifecycleEvent.from_dict(d["event"]),
            delivered_at=d["delivered_at"],
            relay_chain=tuple(
                RelayHop.from_dict(h)
                for h in d.get("relay_chain", [])),
        )


def verify_tree_event_notification(
    notification: TreeEventNotification,
    expected_parent_key: Optional[str] = None,
) -> Tuple[bool, str]:
    """Verify the notification. Never raises.

    Checks:
      1. The event is signed by the parent (expected_parent_key).
      2. The relay chain is non-empty.
      3. Each hop's signature verifies.
      4. Each hop's prior_relay_hash matches the previous hop's
         hash (None for the first).
      5. The first hop is the parent itself (relayer_id ==
         event.signer_id).
    """
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    if not isinstance(notification, TreeEventNotification):
        return (False, "not a TreeEventNotification")
    if not verify_lifecycle_event(
            notification.event, expected_parent_key):
        return (False, "event signature INVALID")
    if not notification.relay_chain:
        return (False, "empty relay chain")
    prev_hash: Optional[str] = None
    for i, hop in enumerate(notification.relay_chain):
        expected = hop.relayer_public_key
        if i == 0:
            if hop.relayer_id != notification.event.signer_id:
                return (False,
                         "first hop is not the parent")
            if hop.prior_relay_hash is not None:
                return (False,
                         "first hop has prior_relay_hash")
        else:
            if hop.prior_relay_hash != prev_hash:
                return (False,
                         f"hop {i} prior_relay_hash mismatch")
        try:
            ok = verify_signature(
                expected,
                hop.canonical_payload(
                    notification.subscription_hash,
                    notification.event.event_hash()),
                hop.signature)
        except Exception:
            ok = False
        if not ok:
            return (False, f"hop {i} signature INVALID")
        prev_hash = hop.relay_hash(
            notification.subscription_hash,
            notification.event.event_hash())
    return (True, "verified")


def build_direct_notification(
    subscription: TreeSubscription,
    event: RoomLifecycleEvent,
    deliverer_id: str,
    deliverer_kp: KeyPair,
) -> TreeEventNotification:
    """Build a single-hop notification: the parent delivers
    directly. The relay chain has one entry: the parent."""
    if not HAS_CRYPTO:
        raise RuntimeError(
            "build_direct_notification requires cryptography")
    delivered_at = _now()
    hop_payload = canonical_bytes({
        "kind": "tree_event_relay",
        "subscription_hash": subscription.subscription_hash(),
        "event_hash": event.event_hash(),
        "relayer_id": deliverer_id,
        "relayer_public_key": deliverer_kp.public_key_hex(),
        "received_at": delivered_at,
        "prior_relay_hash": None,
    })
    hop = RelayHop(
        relayer_id=deliverer_id,
        relayer_public_key=deliverer_kp.public_key_hex(),
        received_at=delivered_at,
        prior_relay_hash=None,
        signature=deliverer_kp.sign(hop_payload).hex(),
    )
    return TreeEventNotification(
        subscription_hash=subscription.subscription_hash(),
        event=event,
        delivered_at=delivered_at,
        relay_chain=(hop,),
    )


# =====================================================================
# Chain verification and reconstruction
# =====================================================================

@dataclass
class ChainVerdict:
    valid: bool
    reason: str
    forks: List[Tuple[str, str]] = field(default_factory=list)
    # forks: (room_id, prior_event_hash shared by >= 2 events)

    def format(self) -> str:
        lines = ["Lifecycle Chain Verification", "=" * 50]
        lines.append(f"  valid: {self.valid}")
        lines.append(f"  reason: {self.reason}")
        if self.forks:
            lines.append("  forks:")
            for rid, ph in self.forks:
                lines.append(f"    {rid} @ {ph[:16]}...")
        return "\n".join(lines)


def verify_lifecycle_chain(
    events: List[RoomLifecycleEvent],
    expected_parent_key: Optional[str] = None,
) -> ChainVerdict:
    """Verify a list of lifecycle events. Never raises.

    Checks, per room_id chain (ordered by emission):
      1. Each event's signature verifies against the
         parent's key (or the declared signer key).
      2. The first event has prior_event_hash == None.
      3. Each subsequent event's prior_event_hash matches
         the previous event's event_hash().
      4. No two events for the same room share a
         prior_event_hash (fork detection).

    A fork makes the chain INVALID — the parent's Law
    was broken. The spec documents this as a fork; C79
    reports it but does not resolve it.
    """
    if not HAS_CRYPTO:
        return ChainVerdict(False, "cryptography not installed")
    if not isinstance(events, list):
        return ChainVerdict(False, "events must be a list")

    # 1. Verify all signatures first
    for i, ev in enumerate(events):
        if not isinstance(ev, RoomLifecycleEvent):
            return ChainVerdict(
                False, f"entry {i} is not a RoomLifecycleEvent")
        if not verify_lifecycle_event(ev, expected_parent_key):
            return ChainVerdict(
                False, f"entry {i} signature INVALID")

    # 2. Group by room and chain-verify
    by_room: Dict[str, List[RoomLifecycleEvent]] = {}
    for ev in events:
        by_room.setdefault(ev.room_id, []).append(ev)

    forks: List[Tuple[str, str]] = []
    for room_id, chain in by_room.items():
        prior_map: Dict[str, int] = {}
        prev_hash: Optional[str] = "UNSET"
        for ev in chain:
            if ev.event_type == "registered" and \
                    ev.prior_event_hash is None:
                # Fresh chain
                if prior_map:
                    return ChainVerdict(
                        False,
                        f"room {room_id!r} has two "
                        f"first-registrations")
                prior_map[ev.event_hash()] = 1
                prev_hash = ev.event_hash()
                continue
            if ev.prior_event_hash is None:
                return ChainVerdict(
                    False,
                    f"room {room_id!r} has non-initial event "
                    f"with prior_event_hash=None")
            if prev_hash == "UNSET":
                return ChainVerdict(
                    False,
                    f"room {room_id!r} chain starts with "
                    f"non-null prior_event_hash")
            if ev.prior_event_hash != prev_hash:
                return ChainVerdict(
                    False,
                    f"room {room_id!r} chain broken at "
                    f"{ev.event_hash()[:16]}...")
            prior_map[ev.prior_event_hash] = (
                prior_map.get(ev.prior_event_hash, 0) + 1)
            prev_hash = ev.event_hash()
        # Detect fork: any prior_event_hash with count > 1
        for prior, count in prior_map.items():
            if count > 1:
                forks.append((room_id, prior))
    if forks:
        return ChainVerdict(
            False,
            f"fork detected in {len(forks)} room(s)",
            forks=forks)
    return ChainVerdict(True, "chain verifies")


def reconstruct_rooms_from_events(
    events: List[RoomLifecycleEvent],
) -> Dict[str, Dict]:
    """Reconstruct the current room state from a list of events.

    Applies events in order:
      - registered → add
      - updated    → replace
      - retired    → remove
    Returns {room_id: {base_url, public_key, name, description}}.
    """
    state: Dict[str, Dict] = {}
    for ev in events:
        if ev.event_type == "retired":
            state.pop(ev.room_id, None)
        else:  # registered or updated
            state[ev.room_id] = {
                "room_id": ev.room_id,
                "base_url": ev.room_url,
                "public_key": ev.room_public_key,
                "name": ev.room_name,
                "description": ev.room_description,
            }
    return state


def reconstruct_at(
    events: List[RoomLifecycleEvent],
    at_event_hash: str,
) -> Dict[str, Dict]:
    """Reconstruct state as of a specific event.

    Events at or before the target are applied; later events
    are ignored. Used for historical reconstruction.
    """
    target_index = None
    for i, ev in enumerate(events):
        if ev.event_hash() == at_event_hash:
            target_index = i
            break
    if target_index is None:
        return {}
    return reconstruct_rooms_from_events(
        events[:target_index + 1])


# =====================================================================
# LivingRoomWorld
# =====================================================================

class LivingRoomWorld(UrlResolvingRoomWorld):
    """A RoomWorld whose directory is reconstructed from signed
    lifecycle events. Signs each event with its curator key and
    delivers notifications to subscribers.
    """

    def __init__(
        self, entity_id: str, name: str, curator_kp: KeyPair,
    ):
        if not HAS_CRYPTO:
            raise RuntimeError(
                "LivingRoomWorld requires cryptography")
        super().__init__(entity_id, name)
        self._curator_kp = curator_kp
        self._subscribers: List[TreeSubscription] = []

    @property
    def curator_public_key(self) -> str:
        return self._curator_kp.public_key_hex()

    # -- Lifecycle events ---------------------------------------

    def _last_event_for(self, room_id: str
                        ) -> Optional[RoomLifecycleEvent]:
        for entry in reversed(self._log):
            if entry.kind == "room_lifecycle_event":
                if entry.data.get("room_id") == room_id:
                    return RoomLifecycleEvent.from_dict(
                        entry.data)
        return None

    def _emit(self, event: RoomLifecycleEvent) -> None:
        self._log.append(LogEntry(
            timestamp=event.timestamp,
            kind="room_lifecycle_event",
            actor_token=event.signer_id,
            data=event.to_dict()))
        self._notify_subscribers(event)

    def register_room(
        self, entry: RoomEntry,
    ) -> RoomLifecycleEvent:
        if entry.parent_world_id != self._manifest.entity_id:
            raise ValueError("entry.parent_world_id mismatch")
        # Check "already registered" via current state
        current = self._current_state()
        if entry.room_id in current:
            raise ValueError(
                f"room {entry.room_id!r} already registered")
        prior = self._last_event_for(entry.room_id)
        prior_hash = prior.event_hash() if prior else None
        event = sign_lifecycle_event(
            event_type="registered",
            parent_id=self._manifest.entity_id,
            signer_id=self._manifest.entity_id,
            signer_kp=self._curator_kp,
            room_id=entry.room_id,
            room_url=entry.base_url,
            room_public_key=entry.public_key,
            room_name=entry.name,
            room_description=entry.description,
            prior_event_hash=prior_hash,
        )
        self._emit(event)
        return event

    def unregister_room(
        self, room_id: str,
    ) -> RoomLifecycleEvent:
        current = self._current_state()
        if room_id not in current:
            raise ValueError(
                f"room {room_id!r} not registered")
        prior = self._last_event_for(room_id)
        prior_hash = prior.event_hash() if prior else None
        event = sign_lifecycle_event(
            event_type="retired",
            parent_id=self._manifest.entity_id,
            signer_id=self._manifest.entity_id,
            signer_kp=self._curator_kp,
            room_id=room_id,
            prior_event_hash=prior_hash,
        )
        self._emit(event)
        return event

    def update_room(
        self, room_id: str, **changes,
    ) -> RoomLifecycleEvent:
        current = self._current_state()
        if room_id not in current:
            raise ValueError(
                f"room {room_id!r} not registered")
        cur = current[room_id]
        prior = self._last_event_for(room_id)
        prior_hash = prior.event_hash() if prior else None
        event = sign_lifecycle_event(
            event_type="updated",
            parent_id=self._manifest.entity_id,
            signer_id=self._manifest.entity_id,
            signer_kp=self._curator_kp,
            room_id=room_id,
            room_url=changes.get("base_url",
                                  cur["base_url"]),
            room_public_key=changes.get("public_key",
                                         cur["public_key"]),
            room_name=changes.get("name", cur["name"]),
            room_description=changes.get(
                "description", cur["description"]),
            prior_event_hash=prior_hash,
        )
        self._emit(event)
        return event

    # -- Reconstruction (overrides C74's list_rooms) ----------

    def _current_state(self) -> Dict[str, Dict]:
        events = [
            RoomLifecycleEvent.from_dict(e.data)
            for e in self._log
            if e.kind == "room_lifecycle_event"
        ]
        return reconstruct_rooms_from_events(events)

    def list_rooms(self) -> List[Dict]:
        state = self._current_state()
        return sorted(state.values(),
                      key=lambda r: r["room_id"])

    # -- Event access ----------------------------------------

    def events(self) -> List[RoomLifecycleEvent]:
        return [
            RoomLifecycleEvent.from_dict(e.data)
            for e in self._log
            if e.kind == "room_lifecycle_event"
        ]

    def events_since(
        self, since_hash: Optional[str],
    ) -> List[RoomLifecycleEvent]:
        events = self.events()
        if since_hash is None:
            return events
        idx = next(
            (i for i, e in enumerate(events)
             if e.event_hash() == since_hash), None)
        if idx is None:
            return events
        return events[idx + 1:]

    # -- Subscriptions ---------------------------------------

    def add_subscription(self, sub: TreeSubscription) -> None:
        if sub.root_id != self._manifest.entity_id:
            raise ValueError("root_id mismatch")
        # Replace if already subscribed (same subscriber_id)
        self._subscribers = [
            s for s in self._subscribers
            if s.subscriber_id != sub.subscriber_id
        ]
        self._subscribers.append(sub)

    def subscribers(self) -> List[TreeSubscription]:
        return list(self._subscribers)

    def _notify_subscribers(
        self, event: RoomLifecycleEvent,
    ) -> List[Tuple[str, bool, str]]:
        results: List[Tuple[str, bool, str]] = []
        for sub in self._subscribers:
            notification = build_direct_notification(
                sub, event,
                deliverer_id=self._manifest.entity_id,
                deliverer_kp=self._curator_kp)
            ok, reason = _post_notification(
                sub.callback_url, notification)
            results.append((sub.subscriber_id, ok, reason))
        return results


def _post_notification(
    callback_url: str, notification: TreeEventNotification,
) -> Tuple[bool, str]:
    url = f"{callback_url.rstrip('/')}/callback"
    body = json.dumps(notification.to_dict()).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            resp = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return (False, f"HTTP {e.code}")
    except urllib.error.URLError as e:
        return (False, f"network: {e}")
    except (json.JSONDecodeError,
            UnicodeDecodeError) as e:
        return (False, f"malformed response: {e}")
    if resp.get("kind") == "ack":
        return (True, "delivered")
    if resp.get("kind") == "refusal":
        return (False, resp.get("reason", "refused"))
    return (False, f"unexpected: {resp.get('kind')}")


# =====================================================================
# LivingRoomWorldServer
# =====================================================================

class LivingRoomWorldServer(WorldProtocolServer):
    """A WorldProtocolServer that adds /events, /events/since,
    and /subscribe to a LivingRoomWorld."""

    def __init__(self, living: LivingRoomWorld,
                 host: str = "127.0.0.1", port: int = 0):
        self._living = living
        super().__init__(living, host=host, port=port)

    def _make_handler(self):
        BaseHandler = super()._make_handler()
        living = self._living
        server = self

        class Handler(BaseHandler):
            def do_GET(self):
                from urllib.parse import urlparse, parse_qs
                url = urlparse(self.path)
                if url.path == "/events":
                    qs = parse_qs(url.query)
                    since = qs.get("since", [None])[0]
                    events = living.events_since(since)
                    server._send(self, 200, {
                        "events": [e.to_dict()
                                    for e in events]})
                    return
                if url.path.startswith("/events/since/"):
                    since = url.path[
                        len("/events/since/"):]
                    events = living.events_since(since)
                    server._send(self, 200, {
                        "events": [e.to_dict()
                                    for e in events]})
                    return
                super().do_GET()

            def do_POST(self):
                if self.path == "/subscribe":
                    try:
                        length = int(self.headers.get(
                            "Content-Length", 0))
                        body = json.loads(
                            self.rfile.read(length).decode())
                        sub = TreeSubscription.from_dict(body)
                    except (json.JSONDecodeError, KeyError,
                            ValueError, TypeError) as e:
                        server._send(self, 400, {
                            "error": f"malformed: {e}"})
                        return
                    if not verify_tree_subscription(sub):
                        server._send(self, 400, {
                            "error": "signature invalid"})
                        return
                    if sub.root_id != \
                            living.manifest().entity_id:
                        server._send(self, 400, {
                            "error": "root_id mismatch"})
                        return
                    living.add_subscription(sub)
                    server._send(self, 200, {
                        "kind": "ack"})
                    return
                super().do_POST()

        return Handler


# =====================================================================
# TreeSubscriber
# =====================================================================

class TreeSubscriber:
    """A client-side daemon that receives, verifies, and stores
    tree event notifications."""

    def __init__(
        self,
        subscriber_id: str,
        subscriber_kp: KeyPair,
        host: str = "127.0.0.1",
        port: int = 0,
    ):
        if not HAS_CRYPTO:
            raise RuntimeError(
                "TreeSubscriber requires cryptography")
        self._subscriber_id = subscriber_id
        self._subscriber_kp = subscriber_kp
        self._host = host
        self._port = port
        self._httpd: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._subscriptions: List[TreeSubscription] = []
        self._parent_keys: Dict[str, str] = {}
        # Canonical event log (ordered by receipt)
        self._events: List[RoomLifecycleEvent] = []
        # Per-room: prior_event_hash we've verified up to
        self._last_hash: Dict[str, str] = {}
        self._notifications: List[TreeEventNotification] = []

    @property
    def url(self) -> str:
        return f"http://{self._host}:{self._port}"

    @property
    def subscriber_id(self) -> str:
        return self._subscriber_id

    @property
    def subscriber_public_key(self) -> str:
        return self._subscriber_kp.public_key_hex()

    # -- Lifecycle -------------------------------------------

    def start(self) -> None:
        self._httpd = HTTPServer(
            (self._host, self._port),
            self._make_handler())
        self._port = self._httpd.server_address[1]
        self._thread = threading.Thread(
            target=self._httpd.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _make_handler(self):
        subscriber = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, status, payload):
                body = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header(
                    "Content-Type", "application/json")
                self.send_header("Content-Length",
                                  str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                if self.path != "/callback":
                    self._send(404, {"error": "not found"})
                    return
                try:
                    length = int(self.headers.get(
                        "Content-Length", 0))
                    body = json.loads(
                        self.rfile.read(length).decode())
                    notification = \
                        TreeEventNotification.from_dict(body)
                except (json.JSONDecodeError, KeyError,
                        ValueError, TypeError) as e:
                    self._send(400, {
                        "kind": "refusal",
                        "reason": f"malformed: {e}"})
                    return
                ok, reason = subscriber._handle_notification(
                    notification)
                if ok:
                    self._send(200, {"kind": "ack"})
                else:
                    self._send(200, {
                        "kind": "refusal",
                        "reason": reason})

        return Handler

    # -- Subscription ---------------------------------------

    def subscribe_to(
        self,
        root_id: str,
        root_url: str,
        parent_public_key: str,
        depth: int = 3,
        since_event_hash: Optional[str] = None,
    ) -> Tuple[bool, str]:
        self._parent_keys[root_id] = parent_public_key
        sub = sign_tree_subscription(
            subscriber_id=self._subscriber_id,
            subscriber_kp=self._subscriber_kp,
            signer_id=self._subscriber_id,
            signer_kp=self._subscriber_kp,
            root_id=root_id,
            root_url=root_url,
            callback_url=self.url,
            depth=depth,
            since_event_hash=since_event_hash,
        )
        body = json.dumps(sub.to_dict()).encode()
        try:
            req = urllib.request.Request(
                f"{root_url.rstrip('/')}/subscribe",
                data=body,
                headers={"Content-Type":
                          "application/json"},
                method="POST")
            with urllib.request.urlopen(req, timeout=10) as r:
                resp = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return (False, f"HTTP {e.code}")
        except urllib.error.URLError as e:
            return (False, f"network: {e}")
        except (json.JSONDecodeError,
                UnicodeDecodeError) as e:
            return (False, f"malformed response: {e}")
        if resp.get("kind") != "ack":
            return (False, resp.get("error", "refused"))
        self._subscriptions.append(sub)
        # Backfill: fetch events since
        ok, reason = self._backfill(sub)
        if not ok:
            return (False, f"backfill failed: {reason}")
        return (True, "subscribed")

    def _backfill(self, sub: TreeSubscription) -> Tuple[bool, str]:
        url = f"{sub.root_url.rstrip('/')}/events"
        if sub.since_event_hash is not None:
            url += f"?since={sub.since_event_hash}"
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                data = json.loads(r.read().decode())
        except (urllib.error.URLError,
                urllib.error.HTTPError,
                json.JSONDecodeError) as e:
            return (False, f"fetch: {e}")
        for ev_dict in data.get("events", []):
            try:
                ev = RoomLifecycleEvent.from_dict(ev_dict)
            except (KeyError, ValueError, TypeError):
                continue
            self._apply_event(ev)
        return (True, "backfilled")

    # -- Event handling --------------------------------------

    def _handle_notification(
        self, notification: TreeEventNotification,
    ) -> Tuple[bool, str]:
        parent_key = self._parent_keys.get(
            notification.event.parent_id)
        ok, reason = verify_tree_event_notification(
            notification, parent_key)
        if not ok:
            return (False, reason)
        self._notifications.append(notification)
        self._apply_event(notification.event)
        return (True, "ok")

    def _apply_event(
        self, event: RoomLifecycleEvent,
    ) -> Tuple[bool, str]:
        expected_prior = self._last_hash.get(event.room_id)
        if event.prior_event_hash != expected_prior:
            # Mismatch: either a duplicate or a gap.
            # Duplicate (already applied) → ack
            if any(e.event_hash() == event.event_hash()
                    for e in self._events):
                return (True, "duplicate")
            return (False,
                     f"prior_event_hash mismatch for "
                     f"{event.room_id!r}")
        self._events.append(event)
        self._last_hash[event.room_id] = event.event_hash()
        return (True, "applied")

    # -- Read model ------------------------------------------

    def received_events(self) -> List[RoomLifecycleEvent]:
        return list(self._events)

    def notifications(self) -> List[TreeEventNotification]:
        return list(self._notifications)

    def current_state(self) -> Dict[str, Dict]:
        return reconstruct_rooms_from_events(self._events)

    def state_at(self, event_hash: str) -> Dict[str, Dict]:
        return reconstruct_at(self._events, event_hash)

    def last_event_hash(self, room_id: str
                        ) -> Optional[str]:
        return self._last_hash.get(room_id)


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Living tree lifecycle:

    1. Build LivingRoomWorld('world:games').
    2. Register A, B, C.
    3. Start subscriber, subscribe.
    4. Retire B; register D; update A's name.
    5. Subscriber receives all 3 events.
    6. Third party fetches parent /events, verifies chain,
       reconstructs state at multiple points.
    """
    import json as _json
    from pathlib import Path

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "living_tree"
    path.mkdir(parents=True, exist_ok=True)

    parent_kp = KeyPair.generate()
    parent = LivingRoomWorld(
        "world:games", "Games Hall", parent_kp)
    parent_server = LivingRoomWorldServer(parent, port=0)
    parent_server.serve_in_thread()
    time.sleep(0.2)
    parent_url = (
        f"http://127.0.0.1:"
        f"{parent_server._httpd.server_address[1]}")

    sub_kp = KeyPair.generate()
    subscriber = TreeSubscriber(
        "sub:observer", sub_kp, port=0)
    subscriber.start()
    time.sleep(0.1)

    try:
        # 1. Initial registrations (before subscription)
        e_a = parent.register_room(RoomEntry(
            parent_world_id="world:games",
            room_id="world:chess",
            base_url="http://chess.example",
            public_key="aa" * 32,
            name="Chess Table"))
        e_b = parent.register_room(RoomEntry(
            parent_world_id="world:games",
            room_id="world:plaza",
            base_url="http://plaza.example",
            public_key="bb" * 32,
            name="Plaza"))
        e_c = parent.register_room(RoomEntry(
            parent_world_id="world:games",
            room_id="world:reading",
            base_url="http://reading.example",
            public_key="cc" * 32,
            name="Reading Room"))

        # 2. Subscriber arrives
        sub_ok, sub_reason = subscriber.subscribe_to(
            root_id="world:games",
            root_url=parent_url,
            parent_public_key=parent.curator_public_key,
            depth=1)
        assert sub_ok, sub_reason
        events_after_subscribe = len(
            subscriber.received_events())

        # 3. Live changes
        e_retire = parent.unregister_room("world:plaza")
        e_add = parent.register_room(RoomEntry(
            parent_world_id="world:games",
            room_id="world:music",
            base_url="http://music.example",
            public_key="dd" * 32,
            name="Music Room"))
        e_update = parent.update_room(
            "world:chess", name="The Main Chess Table")
        time.sleep(0.1)  # let deliveries complete

        # 4. Subscriber sees all 3 live changes
        received = subscriber.received_events()
        state = subscriber.current_state()

        # 5. Third-party verification (offline)
        # Fetch events directly from parent
        try:
            with urllib.request.urlopen(
                    f"{parent_url}/events", timeout=5) as r:
                fetched = json.loads(r.read().decode())
        except (urllib.error.URLError,
                json.JSONDecodeError) as e:
            raise RuntimeError(
                f"could not fetch /events: {e}")
        all_events = [
            RoomLifecycleEvent.from_dict(d)
            for d in fetched.get("events", [])]
        verdict = verify_lifecycle_chain(
            all_events, parent.curator_public_key)
        reconstructed = reconstruct_rooms_from_events(
            all_events)
        # Reconstruct at the moment of the update
        update_state = reconstruct_at(
            all_events, e_update.event_hash())

        # 6. Compare subscriber's log to parent's /events
        sub_hashes = [e.event_hash()
                       for e in subscriber.received_events()]
        parent_hashes = [e.event_hash() for e in all_events]
        logs_match = sub_hashes == parent_hashes

        # Print
        print("=" * 70)
        print("Living Tree — changes signed, delivered,"
              " verified offline")
        print("=" * 70)
        print()
        print(f"  Parent:     world:games")
        print(f"  Key:        {parent.curator_public_key[:16]}...")
        print(f"  Subscriber: {subscriber.subscriber_id}"
              f" @ {subscriber.url}")
        print()
        print(f"  Lifecycle events (in emission order):")
        for ev in all_events:
            print(f"    [{ev.event_type:10s}] "
                  f"{ev.room_id:20s}  "
                  f"prior={ev.prior_event_hash[:16] if ev.prior_event_hash else 'None'}...")
        print()
        print(f"  Current rooms (reconstructed):")
        for rid in sorted(reconstructed):
            r = reconstructed[rid]
            print(f"    {rid}: {r['name']!r} @ {r['base_url']}")
        print()
        print(f"  Chain verification: {verdict.valid}"
              f" ({verdict.reason})")
        print()
        print(f"  Subscriber state:")
        print(f"    Events received:     "
              f"{len(subscriber.received_events())}")
        print(f"    Notifications:       "
              f"{len(subscriber.notifications())}")
        print(f"    Rooms in state:      {sorted(state)}")
        print(f"    Matches parent log:  {logs_match}")
        print()
        print(f"  Historical reconstruction:")
        print(f"    State at last event "
              f"(after update): {sorted(update_state)}")
        print()
        print("  What this demonstrates:")
        print("    - Every directory change is a signed")
        print("      RoomLifecycleEvent, chained via")
        print("      prior_event_hash.")
        print("    - A subscriber receives notifications,")
        print("      verifies them against the parent's key,")
        print("      and maintains a chain-verified log.")
        print("    - A third party can fetch /events, verify")
        print("      the chain against the parent's key, and")
        print("      reconstruct state at any point without")
        print("      trusting the subscriber.")
        print("    - Retired is distinguishable from never-there:")
        print("      the retired event is in the chain, signed.")
        print()
        print("  Anchor (public domain, Emily Dickinson):")
        print("    'Forever – is composed of Nows –'")
        print("    'Tis not a different time –'")

        audit = {
            "parent_id": "world:games",
            "parent_public_key": parent.curator_public_key,
            "event_count": len(all_events),
            "events": [
                {"event_type": ev.event_type,
                 "room_id": ev.room_id,
                 "prior_event_hash": ev.prior_event_hash,
                 "event_hash": ev.event_hash()}
                for ev in all_events
            ],
            "chain_valid": verdict.valid,
            "chain_reason": verdict.reason,
            "current_rooms": sorted(reconstructed.keys()),
            "subscriber": {
                "id": subscriber.subscriber_id,
                "events_received":
                    len(subscriber.received_events()),
                "notifications_received":
                    len(subscriber.notifications()),
                "rooms_in_state": sorted(state.keys()),
                "logs_match_parent": logs_match,
            },
            "historical_reconstruction": {
                "at_update": sorted(update_state.keys()),
            },
        }
        (path / "living_tree_demo.json").write_text(
            _json.dumps(audit, indent=2))
        print(f"\n  → {path}/living_tree_demo.json")
        return audit
    finally:
        subscriber.stop()
        parent_server.stop()
