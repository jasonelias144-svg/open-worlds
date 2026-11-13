"""
multiverse_c74.py — Component 74: The Room World.

A world that is a directory of other worlds.

The reframe: a world doesn't have to be one space. It can be a
*lobby* — a directory of rooms — where each room is itself a
full WCP world. Entering a room is a Route (C3's response type)
to that room's manifest. The parent's Law is minimal: admit,
register rooms, route. The room's Law is its own.

This is what makes a mall a mall, a park a park, and a social
space a social space:

  - Union Square is a RoomWorld.
  - Its rooms are individual spaces: a chess table, a chat
    room, a poetry reading.
  - Each room is a full WCP world with its own Law and its own
    curator.
  - Entering a room is a Route to the room's URL. The parent
    doesn't enforce the room's Law; it just points.

What C74 does NOT do (v0.1):

  - Enforce the child's Law. The parent points; the child
    enforces. That is the point.
  - Prevent a room from being a RoomWorld. Recursion is a
    property, not a bug — a mall can contain a cinema which
    contains screening rooms.
  - Track current location. The parent's log records "Alice
    entered room X". Once Alice is in room X, the room's log
    records what happens; the parent doesn't know when she
    leaves. The parent is a *directory*, not a *router*.
  - Revoke a room and kill it. Unregistering removes it from
    the directory; the room world keeps running if its
    operator wants it to.
  - Verify the room's public_key on registration (v0.1). A
    v0.2 would check the room's manifest signature at register
    time and refuse if it doesn't verify.

Composition: C3 (Route), C13 (signing where used), C73
(ChessWorld, used as one room in the demo), C68 (transport
for the room servers).

The vocabulary — mall, park, nexus, storefront — is
deliberately not baked into the code. The code uses RoomWorld
and RoomEntry because those are neutral. Which rooms a
particular RoomWorld hosts, and what it calls itself, is a
deployment concern.
"""

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from multiverse_c1 import Identity, create_identity
from multiverse_c3 import (
    Manifest, Petition, Act, LogEntry,
    Admission as WCPAdmission, Refusal, Ack, Route,
)
from multiverse_c13 import HAS_CRYPTO, KeyPair
from multiverse_c73 import ChessWorld, HAS_CHESS
from wcp_http_shim import WorldProtocolServer


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# =====================================================================
# RoomEntry — a registration
# =====================================================================

@dataclass(frozen=True)
class RoomEntry:
    parent_world_id: str
    room_id: str
    base_url: str
    public_key: str
    name: str
    description: str = ""

    def __post_init__(self):
        for f in ("parent_world_id", "room_id", "base_url",
                  "public_key", "name"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if len(self.public_key) != 64:
            raise ValueError(
                "public_key must be 64 hex chars")
        if not self.base_url.startswith(("http://", "https://")):
            raise ValueError(
                "base_url must be http:// or https://")


# =====================================================================
# RoomWorld
# =====================================================================

class RoomWorld:
    """A WCP world that is a directory of other worlds.

    Minimal Law:
      - Admit any identity.
      - Petition with target=<room_id> → Route to that room's
        manifest, fetched from the room's base_url.
      - Direct method (curator-level): register/unregister a room.
      - No acts (v0.1). The parent has no activity of its own;
        everything is in the rooms.

    The log is the directory. list_rooms() reconstructs the
    current set from room_registered / room_unregistered
    entries.
    """

    def __init__(self, entity_id: str, name: str):
        self._manifest = Manifest(
            entity_id=entity_id, name=name,
            protocol_version="WCP/0.2",
            law_url=f"roomworld://{entity_id}/law",
            act_endpoint=f"roomworld://{entity_id}/act",
            log_endpoint=f"roomworld://{entity_id}/log",
            sub_registry_endpoint=(
                f"roomworld://{entity_id}/rooms"),
        )
        self._admitted: Dict[str, str] = {}
        self._log: List[LogEntry] = []

    def manifest(self) -> Manifest:
        return self._manifest

    def petition(self, petition: Petition):
        if petition.target is not None:
            return self._route_to_room(petition)
        if petition.petitioner_token in self._admitted:
            return Refusal(reason="Already admitted")
        self._admitted[petition.petitioner_token] = \
            petition.petitioner_name
        self._append("admission", petition.petitioner_token,
                     {"name": petition.petitioner_name})
        return WCPAdmission(
            entity_id=self._manifest.entity_id,
            timestamp=_now())

    def act(self, act: Act):
        return Refusal(
            reason=(f"the lobby has no acts; petition with "
                    f"target=<room_id> to enter a room "
                    f"(got {act.type!r})"))

    def log_since(self, since: Optional[str] = None):
        if since is None:
            return list(self._log)
        return [e for e in self._log if e.timestamp > since]

    # -- Registration (direct; curator-level in a real deploy) --

    def register_room(self, entry: RoomEntry) -> None:
        if entry.parent_world_id != self._manifest.entity_id:
            raise ValueError("entry.parent_world_id mismatch")
        for existing in self.list_rooms():
            if existing["room_id"] == entry.room_id:
                raise ValueError(
                    f"room {entry.room_id!r} already registered")
        self._append("room_registered", None, {
            "room_id": entry.room_id,
            "base_url": entry.base_url,
            "public_key": entry.public_key,
            "name": entry.name,
            "description": entry.description,
        })

    def unregister_room(self, room_id: str) -> None:
        if room_id not in {r["room_id"]
                            for r in self.list_rooms()}:
            raise ValueError(
                f"room {room_id!r} not registered")
        self._append("room_unregistered", None,
                     {"room_id": room_id})

    def list_rooms(self) -> List[Dict]:
        rooms: Dict[str, Dict] = {}
        for e in self._log:
            if e.kind == "room_registered":
                rooms[e.data["room_id"]] = dict(e.data)
            elif e.kind == "room_unregistered":
                rooms.pop(e.data["room_id"], None)
        return sorted(rooms.values(), key=lambda r: r["room_id"])

    # -- Internals --------------------------------------------

    def _route_to_room(self, petition: Petition):
        if petition.petitioner_token not in self._admitted:
            return Refusal(
                reason=("petition to enter a room requires "
                        "admission to the lobby first"))
        entries = {r["room_id"]: r for r in self.list_rooms()}
        entry = entries.get(petition.target or "")
        if entry is None:
            return Refusal(
                reason=f"unknown room: {petition.target!r}")
        try:
            with urllib.request.urlopen(
                    f"{entry['base_url']}/manifest",
                    timeout=5) as r:
                m = json.loads(r.read().decode())
        except (urllib.error.URLError,
                urllib.error.HTTPError,
                json.JSONDecodeError, OSError) as e:
            return Refusal(
                reason=(f"could not fetch room manifest: "
                        f"{type(e).__name__}: {e}"))
        try:
            target_manifest = Manifest(
                entity_id=m["entity_id"],
                name=m["name"],
                protocol_version=m["protocol_version"],
                law_url=m["law_url"],
                act_endpoint=m["act_endpoint"],
                log_endpoint=m["log_endpoint"],
                sub_registry_endpoint=m.get(
                    "sub_registry_endpoint"),
            )
        except KeyError as e:
            return Refusal(
                reason=f"room manifest missing field: {e}")
        self._append("room_enter", petition.petitioner_token, {
            "room_id": petition.target,
            "target_entity_id": target_manifest.entity_id,
        })
        return Route(
            target_manifest=target_manifest,
            reason=f"entering {entry['name']}")

    def _append(self, kind: str, actor: Optional[str],
                 data: Dict) -> LogEntry:
        entry = LogEntry(
            timestamp=_now(), kind=kind,
            actor_token=actor, data=data)
        self._log.append(entry)
        return entry


# =====================================================================
# ChatWorld — a reusable room type
# =====================================================================

class ChatWorld:
    """A minimal world where residents say things to each other.

    No state beyond the log. No turn order. Any admitted
    identity can say anything, any time. This is the "plaza"
    room type: the social area the user described.
    """

    def __init__(self, entity_id: str, name: str):
        self._manifest = Manifest(
            entity_id=entity_id, name=name,
            protocol_version="WCP/0.2",
            law_url=f"chat://{entity_id}/law",
            act_endpoint=f"chat://{entity_id}/act",
            log_endpoint=f"chat://{entity_id}/log",
            sub_registry_endpoint=None,
        )
        self._admitted: Dict[str, str] = {}
        self._log: List[LogEntry] = []

    def manifest(self) -> Manifest:
        return self._manifest

    def petition(self, petition: Petition):
        if petition.petitioner_token in self._admitted:
            return Refusal(reason="Already admitted")
        self._admitted[petition.petitioner_token] = \
            petition.petitioner_name
        self._append("admission", petition.petitioner_token,
                     {"name": petition.petitioner_name})
        return WCPAdmission(
            entity_id=self._manifest.entity_id,
            timestamp=_now())

    def act(self, act: Act):
        if act.actor_token not in self._admitted:
            return Refusal(reason="Actor is not admitted")
        if act.type == "chat.say":
            text = act.payload.get("text", "")
            if not isinstance(text, str) or not text.strip():
                return Refusal(reason="text required")
            self._append("chat.say", act.actor_token,
                         {"text": text})
            return Ack(
                entity_id=self._manifest.entity_id,
                timestamp=_now())
        if act.type == "chat.join":
            self._append("chat.join", act.actor_token, {})
            return Ack(
                entity_id=self._manifest.entity_id,
                timestamp=_now())
        if act.type == "chat.leave":
            self._append("chat.leave", act.actor_token, {})
            return Ack(
                entity_id=self._manifest.entity_id,
                timestamp=_now())
        return Refusal(
            reason=f"Unknown act type: {act.type}")

    def log_since(self, since: Optional[str] = None):
        if since is None:
            return list(self._log)
        return [e for e in self._log if e.timestamp > since]

    def _append(self, kind: str, actor: Optional[str],
                 data: Dict) -> LogEntry:
        entry = LogEntry(
            timestamp=_now(), kind=kind,
            actor_token=actor, data=data)
        self._log.append(entry)
        return entry


def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Two rooms (a Chess Table, a Plaza) in one mall. Alice
    routes to chess; Carol routes to the plaza and says hello.

    Each world keeps its own log; the mall's log is the
    directory. That is what makes it a park and not one big
    room.
    """
    import json as _json
    from pathlib import Path

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if not HAS_CHESS:
        raise RuntimeError(
            "demo requires `python-chess` (pip install chess)")

    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "room_world"
    path.mkdir(parents=True, exist_ok=True)

    chess = ChessWorld("world:park-chess", "Chess Table")
    chess_srv = WorldProtocolServer(chess, port=0)
    chess_srv.serve_in_thread()
    plaza = ChatWorld("world:park-plaza", "Plaza")
    plaza_srv = WorldProtocolServer(plaza, port=0)
    plaza_srv.serve_in_thread()
    time.sleep(0.2)
    chess_url = (
        f"http://127.0.0.1:"
        f"{chess_srv._httpd.server_address[1]}")
    plaza_url = (
        f"http://127.0.0.1:"
        f"{plaza_srv._httpd.server_address[1]}")

    try:
        mall = RoomWorld("world:union-square", "Union Square")
        mall.register_room(RoomEntry(
            parent_world_id="world:union-square",
            room_id="world:park-chess",
            base_url=chess_url,
            public_key="00" * 32,
            name="Chess Table",
            description="One table, two seats, any watchers",
        ))
        mall.register_room(RoomEntry(
            parent_world_id="world:union-square",
            room_id="world:park-plaza",
            base_url=plaza_url,
            public_key="00" * 32,
            name="Plaza",
            description="Open chat; say anything",
        ))

        alice = create_identity("Alice")
        carol = create_identity("Carol")

        def _post(url, body):
            req = urllib.request.Request(
                url, data=json.dumps(body).encode(),
                headers={"Content-Type": "application/json"},
                method="POST")
            with urllib.request.urlopen(
                    req, timeout=5) as r:
                return json.loads(r.read().decode())

        # Alice: lobby → chess
        mall.petition(Petition(
            petitioner_token=alice.token,
            petitioner_name=alice.name,
            passport_admissions=(), message="hi"))
        a_route = mall.petition(Petition(
            petitioner_token=alice.token,
            petitioner_name=alice.name,
            passport_admissions=(), message="",
            target="world:park-chess"))
        _post(f"{chess_url}/petition", {
            "petitioner_token": alice.token,
            "petitioner_name": alice.name,
            "passport_admissions": [],
            "message": "from the plaza"})
        _post(f"{chess_url}/act", {
            "actor_token": alice.token,
            "type": "chess.sit",
            "payload": {"seat": "white"}})

        # Carol: lobby → plaza
        mall.petition(Petition(
            petitioner_token=carol.token,
            petitioner_name=carol.name,
            passport_admissions=(), message="hi"))
        c_route = mall.petition(Petition(
            petitioner_token=carol.token,
            petitioner_name=carol.name,
            passport_admissions=(), message="",
            target="world:park-plaza"))
        _post(f"{plaza_url}/petition", {
            "petitioner_token": carol.token,
            "petitioner_name": carol.name,
            "passport_admissions": [],
            "message": "from the plaza"})
        _post(f"{plaza_url}/act", {
            "actor_token": carol.token,
            "type": "chat.say",
            "payload": {
                "text": "Anyone up for a game after this?"}})

        # Print
        print("=" * 70)
        print("The Room World — Union Square")
        print("=" * 70)
        print()
        print(f"  Mall:  world:union-square")
        print(f"  Rooms: {[r['room_id'] for r in mall.list_rooms()]}")
        print()
        print("  Mall log (directory):")
        for e in mall.log_since(None):
            a = (e.actor_token[:8] + "..."
                 if e.actor_token else "        ")
            print(f"    [{e.kind:20s}] {a}  {e.data}")
        print()
        print("  Alice's route from the mall:")
        print(f"    {type(a_route).__name__} → "
              f"{a_route.target_manifest.entity_id}  "
              f"({a_route.reason})")
        print()
        print("  Chess world log:")
        for e in chess.log_since(None):
            a = (e.actor_token[:8] + "..."
                 if e.actor_token else "        ")
            print(f"    [{e.kind:20s}] {a}  {e.data}")
        print()
        print("  Plaza log:")
        for e in plaza.log_since(None):
            a = (e.actor_token[:8] + "..."
                 if e.actor_token else "        ")
            print(f"    [{e.kind:20s}] {a}  {e.data}")
        print()
        print("  What this demonstrates:")
        print("    - The mall is a RoomWorld; its rooms are full")
        print("      WCP worlds with their own Laws.")
        print("    - Entering a room is a Route: the mall points")
        print("      to the room's manifest; the visitor petitions")
        print("      the room directly.")
        print("    - The mall's log is a directory; each room's")
        print("      log is the room's own record. Three worlds,")
        print("      three histories.")
        print("    - Chat and chess coexist as sibling rooms.")
        print("      The mall doesn't enforce either room's Law.")
        print()
        print("  Anchor (public domain, Emily Dickinson):")
        print("    'I dwell in Possibility –'")
        print("    'A fairer House than Prose –'")

        audit = {
            "mall_id": "world:union-square",
            "rooms": [r["room_id"] for r in mall.list_rooms()],
            "mall_log_entries": len(mall.log_since(None)),
            "chess_log_entries": len(chess.log_since(None)),
            "plaza_log_entries": len(plaza.log_since(None)),
            "alice_route_type": type(a_route).__name__,
            "alice_route_target": (
                a_route.target_manifest.entity_id
                if isinstance(a_route, Route) else None),
            "carol_route_type": type(c_route).__name__,
            "carol_route_target": (
                c_route.target_manifest.entity_id
                if isinstance(c_route, Route) else None),
        }
        (path / "room_world_demo.json").write_text(
            json.dumps(audit, indent=2))
        print(f"\n  → {path}/room_world_demo.json")
        return audit
    finally:
        chess_srv.stop()
        plaza_srv.stop()
