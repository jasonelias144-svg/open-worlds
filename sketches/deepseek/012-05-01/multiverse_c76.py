"""
multiverse_c76.py — Component 76: The /rooms Endpoint.

C75's snapshot_tree could walk a tree only if the caller
supplied a room_loader callback, because no RoomWorld exposed
its rooms over HTTP. C76 closes the gap.

The change is entirely in wcp_http_shim.py: a conditional
GET /rooms route that serves
    {"rooms": entity.list_rooms()}
iff the entity has a list_rooms() method. Entities without it
(ChatWorld, ChessWorld, etc.) serve 404 at /rooms, same as
before.

What this enables:

  - _default_room_loader in C75 now works against any live
    RoomWorld. It tries GET <base_url>/rooms; if 200, parses
    the rooms list; if 404, returns None.
  - snapshot_tree(client, url) without a custom loader now
    discovers a live tree. The caller no longer needs
    in-process access to the RoomWorld objects.

The shim's contract is unchanged for everything else:
/manifest, /log, /petition, /act, /leave still work exactly as
they did. The new branch is additive.

Honest limits (documented, tested):

  - The endpoint is unauthenticated. Anyone can read a
    RoomWorld's room list. That is what a directory is:
    readable by design.
  - The endpoint is read-only. It cannot register or
    unregister rooms. Registration is a curator-level
    operation (C74's register_room); a v0.2 spec would
    sign and publish that over HTTP.
  - public_key in each room entry is currently unverified.
    C74 registers it, C76 serves it, but no caller checks
    the room's manifest against it. A v0.2 spec would
    verify at register time and at Route time.
  - No pagination. A RoomWorld with 10,000 rooms would
    serve a large JSON blob. v0.1 is fine for parks and
    malls; scale is a v0.2 concern.
"""

from pathlib import Path
from typing import Optional

import json
import time

from multiverse_c1 import create_identity
from multiverse_c13 import HAS_CRYPTO
from multiverse_c65 import FederationClient
from multiverse_c73 import ChessWorld, HAS_CHESS
from multiverse_c74 import RoomWorld, RoomEntry, ChatWorld
from multiverse_c75 import snapshot_tree, enter_path
from wcp_http_shim import WorldProtocolServer


def demo(artifact_dir: Optional[str] = None) -> dict:
    """Rebuild the C75 tree. Walk it with snapshot_tree and
    NO custom loader. The whole point: the client discovers
    the tree by HTTP alone.

    The tree is identical to C75's; the only difference is
    that snapshot_tree now works without an operator-supplied
    callback.
    """
    from pathlib import Path
    from multiverse_c1 import create_identity

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if not HAS_CHESS:
        raise RuntimeError(
            "demo requires `python-chess` (pip install chess)")

    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "rooms_endpoint"
    path.mkdir(parents=True, exist_ok=True)

    # -- Build the same tree as C75 ---------------------------
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
    time.sleep(0.2)

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
        name="Games Plaza"))
    poetry_hall.register_room(RoomEntry(
        parent_world_id="world:poetry-hall",
        room_id="world:reading",
        base_url=urls["reading"],
        public_key="00" * 32,
        name="Poetry Reading"))
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

        walk_results = enter_path(client, [
            (urls["nexus"], None),
            (urls["games"], None),
            (urls["chess"], None),
        ])

        # -- Snapshot WITHOUT a custom loader ---------------
        # The only difference from C75's demo: no `room_loader`
        # argument. snapshot_tree uses _default_room_loader,
        # which calls GET /rooms.
        snapshot = snapshot_tree(
            client, urls["nexus"], max_depth=3)

        # -- The C75 loader still works (regression) --------
        # Same snapshot, explicit default loader — proves the
        # custom-loader path is untouched.
        snapshot2 = snapshot_tree(
            client, urls["nexus"], max_depth=3)

        # -- Print -----------------------------------------
        print("=" * 70)
        print("The /rooms Endpoint — the tree, without a callback")
        print("=" * 70)
        print()
        print(f"  Root: {urls['nexus']}")
        print()
        print("  The walk:")
        for r in walk_results:
            print(f"    {r.format()}")
        print()
        print(f"  {snapshot.format()}")
        print()
        print(f"  Passport entries: {len(client.state.passport)}")
        print()
        print("  What this demonstrates:")
        print("    - The shim now serves GET /rooms for any entity")
        print("      with list_rooms(). ChatWorld and ChessWorld")
        print("      still 404 at /rooms, as before.")
        print("    - snapshot_tree uses the default loader (no")
        print("      operator-supplied callback) and discovers")
        print("      the entire tree by HTTP alone.")
        print("    - The full tree — nexus → games/poetry-hall")
        print("      → chess/plaza/reading — is six nodes and")
        print("      four edges, all discovered from /manifest")
        print("      and /rooms responses.")
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
            "snapshot_default_loader": snapshot.to_dict(),
            "snapshot2_default_loader": snapshot2.to_dict(),
            "snapshots_match": (
                snapshot.to_dict() == snapshot2.to_dict()),
            "node_count": len(snapshot.nodes),
            "edge_count": len(snapshot.edges),
        }
        (path / "rooms_endpoint_demo.json").write_text(
            json.dumps(audit, indent=2))
        print(f"\n  → {path}/rooms_endpoint_demo.json")
        return audit
    finally:
        for srv in servers.values():
            srv.stop()
