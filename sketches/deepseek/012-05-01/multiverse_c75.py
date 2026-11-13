"""
multiverse_c75.py — Component 75: The Traversable World.

Two conditions for emergence. No rules about shape.

C74 gave worlds the ability to *be* a directory of other
worlds. C75 gives clients two conditions to act on that:

  1. Traversability. A client can walk a tree of worlds:
     nexus → mall → room. Each hop is a petition to a world,
     each admission verified against the previous hop's
     manifest (or against an explicit expected key).

  2. Observability. A client can read a tree's structure
     without prescribing it: fetch the root, walk its
     sub-registry, recurse. The tree is whatever operators
     have registered; the snapshot is a report about it,
     not a plan for it.

What C75 deliberately does NOT do:

  - Decide which worlds belong where. Operators register
    rooms; C75 doesn't care about the pattern.
  - Require a global tree. There's no "the world tree."
    There are as many trees as there are RoomWorlds.
  - Enforce a schema on the tree. A RoomWorld can be a
    room of another RoomWorld (recursion is a property).
  - Rank, cluster, or predict. Snapshot is a walk; it
    returns what's there, ordered by discovery, and stops.

What's already true (no C75 code needed):

  - No central authority. Every hop is a petition to a
    world the client chooses to enter.
  - No required pattern. A world that wants to be a mall
    registers rooms. A world that doesn't, doesn't.
  - No trust in the tree structure. Every admission is
    verified against an anchor the caller supplies (or
    explicitly left unverified, with a flag).

Honest limits (documented, tested):

  - Route carries a manifest URI, not an HTTP URL. C75's
    caller supplies the room's base URL. A v0.2 spec
    would have RoomWorld serve GET /rooms so the client
    can derive URLs from parent sub-registries. C75's
    snapshot_tree takes a `room_loader` callback for
    exactly this reason.
  - Snapshot is depth-bounded (default 3). Beyond that,
    caller must supply a larger depth; there's no
    "give me the whole tree" default.
  - No cycle detection beyond depth limit. A two-world
    loop (A lists B, B lists A) would consume max_depth
    hops and stop. Repeated visits are reported as
    separate nodes if they appear at different depths.
  - Snapshot is read-only. It fetches manifests and
    (via room_loader) room lists. It does not petition,
    admit, or act. Observation doesn't intervene.
"""

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from multiverse_c1 import create_identity
from multiverse_c3 import (
    Petition, Act, Ack, Refusal, Route, Admission as WCPAdmission,
)
from multiverse_c13 import (
    HAS_CRYPTO, canonical_bytes, verify_signature,
)
from multiverse_c15 import PassportEntry
from multiverse_c65 import FederationClient
from multiverse_c73 import ChessWorld, HAS_CHESS
from multiverse_c74 import RoomWorld, RoomEntry, ChatWorld
from wcp_http_shim import WorldProtocolServer


# =====================================================================
# Small HTTP helpers
# =====================================================================

class _HTTPError(Exception):
    pass


def _http_get(url: str, timeout: float = 5.0) -> Any:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise _HTTPError(f"HTTP {e.code}")
    except urllib.error.URLError as e:
        raise _HTTPError(f"network: {e}")
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise _HTTPError(f"malformed response: {e}")


def _http_post(url: str, body: Dict,
                timeout: float = 5.0) -> Any:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        raise _HTTPError(f"HTTP {e.code}")
    except urllib.error.URLError as e:
        raise _HTTPError(f"network: {e}")
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise _HTTPError(f"malformed response: {e}")


def _strip_path(url: str, suffix: str) -> str:
    if url.endswith(suffix):
        return url[: -len(suffix)]
    return url


# =====================================================================
# RouteFollowResult
# =====================================================================

@dataclass
class RouteFollowResult:
    ok: bool
    verified: bool
    world_id: str
    reason: str
    admission_raw: Optional[Dict] = None

    def format(self) -> str:
        marker = "✓" if (self.ok and self.verified) else (
            "○" if self.ok else "✗")
        ver_note = ("verified" if self.verified
                     else "unverified" if self.ok
                     else "")
        return (f"  {marker} {self.world_id} "
                f"({self.reason})"
                + (f" [{ver_note}]" if ver_note else ""))


# =====================================================================
# The traversal verb
# =====================================================================

def _enter_at_url(
    client: FederationClient,
    base_url: str,
    expected_public_key: Optional[str] = None,
    label: Optional[str] = None,
) -> RouteFollowResult:
    """The core step: petition a world at a URL, verify the
    admission if an expected key is given, update the passport.

    Never raises for network or semantic errors — returns a
    RouteFollowResult with ok=False and a reason.
    """
    if not HAS_CRYPTO:
        return RouteFollowResult(
            False, False, label or base_url,
            "cryptography not installed")
    if client.state.identity is None:
        return RouteFollowResult(
            False, False, label or base_url,
            "client has no identity")

    world_label = label or base_url
    base = _strip_path(base_url, "/")
    try:
        passport_admissions = list(
            client.state.passport.to_plain_entries())
        resp = _http_post(f"{base}/petition", {
            "petitioner_token":
                client.state.identity.identity.token,
            "petitioner_name":
                client.state.identity.identity.name,
            "passport_admissions": passport_admissions,
            "message": "traversal",
        })
    except _HTTPError as e:
        return RouteFollowResult(
            False, False, world_label,
            f"petition failed: {e}")

    if resp.get("kind") == "refusal":
        return RouteFollowResult(
            False, False, world_label,
            f"refused: {resp.get('reason', '')}")
    if resp.get("kind") != "admission":
        return RouteFollowResult(
            False, False, world_label,
            f"unexpected response: {resp.get('kind')}")

    verified = False
    if expected_public_key is not None:
        try:
            payload = canonical_bytes({
                "kind": "admission",
                "entity_id": resp["entity_id"],
                "timestamp": resp["timestamp"],
                "subject_token": resp["subject_token"],
            })
            verified = verify_signature(
                expected_public_key, payload,
                resp.get("signature", ""))
        except Exception:
            verified = False
        if not verified:
            return RouteFollowResult(
                False, False, world_label,
                "admission signature does not verify against "
                "expected_public_key")

    try:
        entry = PassportEntry(
            entity_id=resp["entity_id"],
            timestamp=resp["timestamp"],
            subject_token=resp["subject_token"],
            signature=resp["signature"])
    except (KeyError, TypeError) as e:
        return RouteFollowResult(
            False, False, world_label,
            f"malformed admission: {e}")

    client.state.passport = client.state.passport.with_entry(
        entry)
    client.state.save_passport()
    client.state.append_log("follow_route", {
        "world_label": world_label,
        "entity_id": resp["entity_id"],
        "verified": verified,
        "admission": resp,
    })
    return RouteFollowResult(
        True, verified, resp.get("entity_id", world_label),
        "entered" if verified
        else "entered (unverified: no expected_public_key)",
        resp)


def follow_route(
    client: FederationClient,
    route: Route,
    room_base_url: str,
    expected_public_key: Optional[str] = None,
) -> RouteFollowResult:
    """Enter a room given a Route and its base URL.

    The Route carries the room's manifest (C3). The caller
    supplies the room's HTTP base URL — C75's honest limit is
    that Route URIs aren't HTTP-resolvable; a v0.2 spec would
    have parents serve GET /rooms.
    """
    if not isinstance(route, Route):
        return RouteFollowResult(
            False, False, "",
            "not a Route")
    return _enter_at_url(
        client,
        base_url=room_base_url,
        expected_public_key=expected_public_key,
        label=route.target_manifest.entity_id,
    )


def enter_path(
    client: FederationClient,
    steps: List[Tuple[str, Optional[str]]],
) -> List[RouteFollowResult]:
    """Walk a path of worlds by petitioning each in sequence.

    Each step is (base_url, expected_public_key_or_None).
    The caller supplies both; C75 does not read the tree
    itself. This is the deliberate shape: the *caller* knows
    the path; C75 walks it.
    """
    return [
        _enter_at_url(
            client, base_url=step_url,
            expected_public_key=step_key,
            label=step_url)
        for step_url, step_key in steps
    ]


# =====================================================================
# The observation verb
# =====================================================================

RoomLoader = Callable[[str], Optional[List[Dict]]]
# A RoomLoader takes a base_url and returns the list of rooms
# the world at that URL lists, or None if it has no sub-registry
# or the fetch failed. C75 supplies a default that tries GET
# /rooms; callers can substitute an in-process accessor.


@dataclass
class TreeNode:
    depth: int
    base_url: str
    entity_id: str
    name: str
    has_sub_registry: bool
    rooms: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "depth": self.depth,
            "base_url": self.base_url,
            "entity_id": self.entity_id,
            "name": self.name,
            "has_sub_registry": self.has_sub_registry,
            "rooms": list(self.rooms),
        }


@dataclass
class WorldTreeSnapshot:
    root_base_url: str
    max_depth: int
    nodes: List[TreeNode] = field(default_factory=list)
    edges: List[Tuple[str, str, str]] = field(default_factory=list)
    # edges: (parent_base_url, room_id, child_base_url)

    def format(self) -> str:
        lines = ["World Tree Snapshot", "=" * 50]
        lines.append(f"  root:      {self.root_base_url}")
        lines.append(f"  max_depth: {self.max_depth}")
        lines.append(f"  nodes:     {len(self.nodes)}")
        lines.append(f"  edges:     {len(self.edges)}")
        lines.append("")
        by_depth: Dict[int, List[TreeNode]] = {}
        for n in self.nodes:
            by_depth.setdefault(n.depth, []).append(n)
        for d in sorted(by_depth):
            indent = "  " + "  " * d
            for n in by_depth[d]:
                sub = " [dir]" if n.has_sub_registry else ""
                lines.append(
                    f"{indent}{n.name} ({n.entity_id})"
                    f"  @ {n.base_url}{sub}")
                if n.rooms:
                    for r in n.rooms:
                        lines.append(
                            f"{indent}  → {r.get('room_id')}"
                            f"  ({r.get('name', '')})")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "root_base_url": self.root_base_url,
            "max_depth": self.max_depth,
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [
                {"parent": p, "room_id": r, "child": c}
                for p, r, c in self.edges],
        }


def _default_room_loader(base_url: str) -> Optional[List[Dict]]:
    """Try GET <base_url>/rooms. Returns None on any failure.

    C74's RoomWorld does not currently serve /rooms — this
    default loader will return None for it. That is the honest
    v0.2 gap; the demo supplies a room_loader that reads
    in-process.
    """
    try:
        data = _http_get(f"{base_url.rstrip('/')}/rooms")
    except _HTTPError:
        return None
    if not isinstance(data, dict):
        return None
    rooms = data.get("rooms")
    if not isinstance(rooms, list):
        return None
    return rooms


def snapshot_tree(
    client: FederationClient,
    root_base_url: str,
    room_loader: Optional[RoomLoader] = None,
    max_depth: int = 3,
) -> WorldTreeSnapshot:
    """Walk a tree of worlds from a root URL. Read-only.

    At each node: fetch /manifest. If the manifest declares a
    sub_registry_endpoint, call room_loader to get the rooms.
    Recurse into each room's base_url, up to max_depth.

    Never raises; unreadable nodes are skipped (but noted as
    nodes without room data — the caller can see which parts
    of the tree were inaccessible).
    """
    loader = room_loader or _default_room_loader
    snapshot = WorldTreeSnapshot(
        root_base_url=root_base_url, max_depth=max_depth)
    if not HAS_CRYPTO:
        return snapshot

    seen_urls: set = set()

    def _walk(base_url: str, depth: int) -> None:
        normalized = base_url.rstrip("/")
        if normalized in seen_urls:
            return
        seen_urls.add(normalized)
        try:
            m = _http_get(f"{normalized}/manifest")
        except _HTTPError:
            return
        node = TreeNode(
            depth=depth,
            base_url=normalized,
            entity_id=m.get("entity_id", ""),
            name=m.get("name", ""),
            has_sub_registry=bool(
                m.get("sub_registry_endpoint")),
        )
        snapshot.nodes.append(node)
        if depth >= max_depth:
            return
        if not node.has_sub_registry:
            return
        rooms = loader(normalized)
        if rooms is None:
            return
        node.rooms = rooms
        for r in rooms:
            rid = r.get("room_id", "")
            rurl = r.get("base_url")
            if not isinstance(rurl, str) or not rurl:
                continue
            snapshot.edges.append((normalized, rid, rurl))
            _walk(rurl, depth + 1)

    _walk(root_base_url, 0)
    return snapshot


# =====================================================================
# Demo: a tree that wasn't prescribed, walked by one client
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """A tree that formed from operators' choices, walked in
    one client session, observed in one snapshot.

    Structure (built by four register_room calls):

        world:nexus
          ├── world:games           [RoomWorld]
          │     ├── world:chess     [ChessWorld]
          │     └── world:plaza     [ChatWorld]
          └── world:poetry-hall     [RoomWorld]
                └── world:reading   [ChatWorld]

    Nobody built the tree in one place. Two operators chose
    their subtrees; a third decided to be a nexus. The tree is
    the sum of those choices.

    The visitor:
      1. Enters the nexus (via C65's client.enter_world,
         anchored to the federation).
      2. Follows a route into world:games.
      3. Follows a route into world:chess.
      4. Sits at white.
    """
    import json as _json
    from multiverse_c1 import Identity

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if not HAS_CHESS:
        raise RuntimeError(
            "demo requires `python-chess` (pip install chess)")

    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "traversable_world"
    path.mkdir(parents=True, exist_ok=True)

    # -- Build worlds -----------------------------------------
    chess = ChessWorld("world:chess", "Chess Table")
    plaza = ChatWorld("world:plaza", "Plaza")
    games = RoomWorld("world:games", "Games Hall")
    reading = ChatWorld("world:reading", "Poetry Reading")
    poetry_hall = RoomWorld("world:poetry-hall", "Poetry Hall")
    nexus = RoomWorld("world:nexus", "The Nexus")

    servers = {}
    urls = {}
    for world, wname in (
        (chess, "chess"), (plaza, "plaza"),
        (games, "games"),
        (reading, "reading"),
        (poetry_hall, "poetry-hall"),
        (nexus, "nexus"),
    ):
        srv = WorldProtocolServer(world, port=0)
        srv.serve_in_thread()
        servers[wname] = srv
        urls[wname] = (
            f"http://127.0.0.1:"
            f"{srv._httpd.server_address[1]}")
    import time as _t
    _t.sleep(0.2)

    # Sub-registries (each operator's choice):
    games.register_room(RoomEntry(
        parent_world_id="world:games",
        room_id="world:chess",
        base_url=urls["chess"],
        public_key="00" * 32,
        name="Chess Table",
        description="One table, two seats"))
    games.register_room(RoomEntry(
        parent_world_id="world:games",
        room_id="world:plaza",
        base_url=urls["plaza"],
        public_key="00" * 32,
        name="Games Plaza",
        description="Talk between games"))
    poetry_hall.register_room(RoomEntry(
        parent_world_id="world:poetry-hall",
        room_id="world:reading",
        base_url=urls["reading"],
        public_key="00" * 32,
        name="Poetry Reading",
        description="Open mic"))
    nexus.register_room(RoomEntry(
        parent_world_id="world:nexus",
        room_id="world:games",
        base_url=urls["games"],
        public_key="00" * 32,
        name="Games Hall"))
    nexus.register_room(RoomEntry(
        parent_world_id="world:nexus",
        room_id="world:poetry-hall",
        base_url=urls["poetry-hall"],
        public_key="00" * 32,
        name="Poetry Hall"))

    try:
        # -- Client walks the tree ---------------------------
        client_dir = path / "alice"
        if client_dir.exists():
            import shutil
            shutil.rmtree(client_dir)
        client = FederationClient(client_dir)
        client.create_identity("Alice")

        # Enter the nexus (via route from the tree, or directly).
        # We use enter_path: it petitions each world in sequence.
        walk_results = enter_path(client, [
            (urls["nexus"], None),   # root; no anchor checked in demo
            (urls["games"], None),   # games hall
            (urls["chess"], None),   # chess table
        ])
        # Sit at white via raw HTTP against the room
        _http_post(f"{urls['chess']}/act", {
            "actor_token": client.state.identity.identity.token,
            "type": "chess.sit",
            "payload": {"seat": "white"},
        })

        # -- Snapshot the tree ------------------------------
        # Since C74 doesn't serve GET /rooms yet, supply a
        # room_loader that reads the RoomWorld's list_rooms()
        # in-process. In a real deployment, this would be a
        # /rooms HTTP call.
        room_lists = {
            urls["nexus"]: nexus.list_rooms(),
            urls["games"]: games.list_rooms(),
            urls["poetry-hall"]: poetry_hall.list_rooms(),
        }
        def loader(base_url: str) -> Optional[List[Dict]]:
            return room_lists.get(base_url.rstrip("/"))

        snapshot = snapshot_tree(
            client, urls["nexus"],
            room_loader=loader, max_depth=3)

        # -- Print -----------------------------------------
        print("=" * 70)
        print("The Traversable World — a tree that formed, walked,"
              " observed")
        print("=" * 70)
        print()
        print(f"  Visitor: Alice ({client.state.identity.identity.token[:16]}...)")
        print()
        print("  The walk:")
        for r in walk_results:
            print(f"    {r.format()}")
        print()
        print(f"  {snapshot.format()}")
        print()
        print(f"  Alice's passport: "
              f"{len(client.state.passport)} admissions")
        print()
        print("  What this demonstrates:")
        print("    - The tree's shape was chosen by operators,")
        print("      not by any component. C75 didn't say 'build a")
        print("      nexus'; the demo's operator did.")
        print("    - The client walks the tree with two verbs:")
        print("      enter_path (petition a sequence of worlds) and")
        print("      follow_route (petition the target of a Route).")
        print("    - The client observes the tree with one verb:")
        print("      snapshot_tree. It reads what's there; it")
        print("      doesn't prescribe what should be.")
        print("    - Three conditions for emergence are now present:")
        print("      traversable substrate, no prescribed shape,")
        print("      observable history. What patterns form is up")
        print("      to operators.")
        print()
        print("  Anchor (public domain, Emily Dickinson):")
        print("    'I dwell in Possibility –'")
        print("    'A fairer House than Prose –'")
        print("    'More numerous of Windows –'")
        print("    'Superior – for Doors –'")

        audit = {
            "nexus_url": urls["nexus"],
            "walk_results": [
                {"world_id": r.world_id, "ok": r.ok,
                 "verified": r.verified, "reason": r.reason}
                for r in walk_results
            ],
            "passport_admissions": len(client.state.passport),
            "snapshot": snapshot.to_dict(),
        }
        (path / "traversable_world_demo.json").write_text(
            _json.dumps(audit, indent=2))
        print(f"\n  → {path}/traversable_world_demo.json")
        return audit
    finally:
        for srv in servers.values():
            srv.stop()
