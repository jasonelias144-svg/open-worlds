"""
multiverse_c77.py — Component 77: The Route URL Extension.

Closes C75's last gap. Before C77, walking a tree required
the caller to know each room's HTTP base URL. After C77:

  - UrlResolvingRoomWorld builds Routes whose
    target_manifest endpoints are HTTP URLs.
  - follow_route can derive base_url from the Route itself
    (backward-compatible: caller-supplied base_url still wins).
  - walk_to(client, root_url, path) walks a chain of room
    ids from any root URL, needing nothing else.

The nested C74/C75/C76 worlds are unchanged; only Route
construction and follow_route's defaults differ. The client
is now self-sufficient against any tree whose parents use
UrlResolvingRoomWorld.

Composition: C3 (Manifest, Route), C74 (RoomWorld), C75
(follow_route, snapshot_tree), C76 (/rooms endpoint). No
new artifacts, no protocol change.

Honest limits (documented, tested):
  - A Route from a plain C74 RoomWorld still needs a
    caller-supplied base_url. C77 doesn't retrofit C74 —
    it provides a subclass. Deployments choose.
  - URL substitution happens per-Route, not on the
    published manifest. GET /manifest still returns
    URI-scheme endpoints for a UrlResolvingRoomWorld.
    That's correct: the world *is* located at a URI;
    the Route is a pointer to its HTTP location.
  - walk_to assumes the root world admits on first
    petition (as C74 worlds do). A world with a stricter
    Law would refuse, and walk_to would stop there.
  - walk_to uses raw HTTP against each world's /petition,
    not C65's anchor-anchored client, because the target
    worlds may not be in the client's anchors. Verifying
    each hop's admission is the caller's job (via
    expected_public_key when they know the key).
"""

from dataclasses import replace
from typing import Any, Dict, List, Optional

from multiverse_c3 import Manifest, Petition, Route, Act, Ack, Refusal
from multiverse_c65 import FederationClient
from multiverse_c74 import RoomWorld, RoomEntry
from multiverse_c75 import (
    RouteFollowResult, _enter_at_url, _http_post, _HTTPError,
    follow_route as _follow_route_c75,
)


# =====================================================================
# resolve_manifest_urls
# =====================================================================

def resolve_manifest_urls(
    manifest: Manifest, base_url: str,
) -> Manifest:
    base = base_url.rstrip("/")
    def resolve(uri: str, path: str) -> str:
        if uri.startswith(("http://", "https://")):
            return uri
        return f"{base}/{path}"
    return replace(
        manifest,
        law_url=resolve(manifest.law_url, "law"),
        act_endpoint=resolve(manifest.act_endpoint, "act"),
        log_endpoint=resolve(manifest.log_endpoint, "log"),
    )


# =====================================================================
# UrlResolvingRoomWorld
# =====================================================================

class UrlResolvingRoomWorld(RoomWorld):
    """A RoomWorld whose Routes carry HTTP URLs."""

    def _route_to_room(self, petition: Petition):
        result = super()._route_to_room(petition)
        if not isinstance(result, Route):
            return result
        entry = next(
            (r for r in self.list_rooms()
             if r["room_id"] == petition.target), None)
        if entry is None:
            return result
        return Route(
            target_manifest=resolve_manifest_urls(
                result.target_manifest, entry["base_url"]),
            reason=result.reason,
        )


# =====================================================================
# follow_route — optional base_url, derived from Route
# =====================================================================

def follow_route(
    client: FederationClient,
    route: Route,
    room_base_url: Optional[str] = None,
    expected_public_key: Optional[str] = None,
) -> RouteFollowResult:
    """C77 supersedes C75's follow_route: `room_base_url` is
    now optional. If omitted, it is derived from
    route.target_manifest.act_endpoint.

    Backward compatible: callers that pass room_base_url
    positionally (C75's signature) still work.
    """
    if not isinstance(route, Route):
        return RouteFollowResult(
            False, False, "", "not a Route")
    if room_base_url is None:
        uri = route.target_manifest.act_endpoint
        if not uri.startswith(("http://", "https://")):
            return RouteFollowResult(
                False, False, route.target_manifest.entity_id,
                ("route has no HTTP URL; caller must supply "
                 "room_base_url (this Route may come from a "
                 "plain C74 RoomWorld, not a UrlResolving "
                 "one)"))
        room_base_url = uri[:-len("/act")] if uri.endswith("/act") else uri
    return _enter_at_url(
        client,
        base_url=room_base_url,
        expected_public_key=expected_public_key,
        label=route.target_manifest.entity_id,
    )


# =====================================================================
# walk_to — the payoff
# =====================================================================

def walk_to(
    client: FederationClient,
    root_url: str,
    path: List[str],
    expected_public_key: Optional[str] = None,
) -> List[RouteFollowResult]:
    """Walk from root_url through a chain of room IDs.

    The client is given:
      - the root's HTTP URL,
      - a list of room IDs (as they appear in each parent's
        /rooms listing or register_room call),
      - optionally a public key to verify each hop.

    The client is NOT given:
      - intermediate rooms' URLs,
      - their manifests,
      - their public keys.

    walk_to uses the Route each parent returns to discover the
    next URL. If every parent is a UrlResolvingRoomWorld, no
    caller-supplied URL is needed past the root.

    Returns a list of RouteFollowResults — one for the root
    entry, one per room entered. Stops on first failure.
    """
    results: List[RouteFollowResult] = []

    # 1. Enter the root
    r = _enter_at_url(
        client, base_url=root_url,
        expected_public_key=expected_public_key,
        label=root_url)
    results.append(r)
    if not r.ok:
        return results
    current_url = r.base_url or root_url

    # 2. Walk the path
    for room_id in path:
        try:
            resp = _http_post(f"{current_url}/petition", {
                "petitioner_token":
                    client.state.identity.identity.token,
                "petitioner_name":
                    client.state.identity.identity.name,
                "passport_admissions": list(
                    client.state.passport.to_plain_entries()),
                "message": "walk",
                "target": room_id,
            })
        except _HTTPError as e:
            results.append(RouteFollowResult(
                False, False, room_id,
                f"petition failed: {e}"))
            return results
        if resp.get("kind") != "route":
            results.append(RouteFollowResult(
                False, False, room_id,
                f"expected route, got {resp.get('kind')!r}: "
                f"{resp.get('reason', '')}"))
            return results
        try:
            m = resp["target_manifest"]
            target_manifest = Manifest(
                entity_id=m["entity_id"],
                name=m["name"],
                protocol_version=m["protocol_version"],
                law_url=m["law_url"],
                act_endpoint=m["act_endpoint"],
                log_endpoint=m["log_endpoint"],
                sub_registry_endpoint=m.get(
                    "sub_registry_endpoint"))
        except (KeyError, TypeError) as e:
            results.append(RouteFollowResult(
                False, False, room_id,
                f"malformed route manifest: {e}"))
            return results
        route = Route(
            target_manifest=target_manifest,
            reason=resp.get("reason", ""))
        fr = follow_route(
            client, route,
            expected_public_key=expected_public_key)
        results.append(fr)
        if not fr.ok:
            return results
        if fr.base_url is None:
            results.append(RouteFollowResult(
                False, False, room_id,
                "follow_route returned no base_url"))
            return results
        current_url = fr.base_url

    return results


def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Walk the tree from the nexus URL alone.

    The client is given:
      - world:nexus's URL,
      - the path ["world:games", "world:chess"].

    It is NOT given the URLs of world:games or world:chess.
    It discovers both from the Route each parent returns.
    """
    import json as _json
    import time
    from pathlib import Path
    from multiverse_c1 import create_identity
    from multiverse_c13 import HAS_CRYPTO
    from multiverse_c73 import ChessWorld, HAS_CHESS
    from multiverse_c74 import RoomEntry
    from multiverse_c75 import _http_post
    from wcp_http_shim import WorldProtocolServer

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if not HAS_CHESS:
        raise RuntimeError(
            "demo requires `python-chess` (pip install chess)")

    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "route_urls"
    path.mkdir(parents=True, exist_ok=True)

    # Build a UrlResolvingRoomWorld tree
    chess = ChessWorld("world:chess", "Chess Table")
    plaza = ChatWorld("world:plaza", "Plaza")
    games = UrlResolvingRoomWorld("world:games", "Games Hall")
    nexus = UrlResolvingRoomWorld("world:nexus", "The Nexus")

    servers = {}
    urls = {}
    for world, wname in (
        (chess, "chess"), (plaza, "plaza"),
        (games, "games"), (nexus, "nexus"),
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
        name="Chess Table"))
    games.register_room(RoomEntry(
        parent_world_id="world:games",
        room_id="world:plaza",
        base_url=urls["plaza"],
        public_key="00" * 32,
        name="Games Plaza"))
    nexus.register_room(RoomEntry(
        parent_world_id="world:nexus",
        room_id="world:games",
        base_url=urls["games"],
        public_key="00" * 32,
        name="Games Hall"))

    try:
        client_dir = path / "alice"
        if client_dir.exists():
            import shutil
            shutil.rmtree(client_dir)
        client = FederationClient(client_dir)
        client.create_identity("Alice")

        # The client knows ONLY the nexus URL and the path.
        # It does NOT know world:games's URL or world:chess's URL.
        walk = walk_to(
            client,
            root_url=urls["nexus"],
            path=["world:games", "world:chess"],
        )

        # If we made it, sit at chess. We get chess's URL from
        # the last walk result — but the walk itself never needed
        # to know it.
        chess_url_from_walk = walk[-1].base_url if walk[-1].ok else None
        if chess_url_from_walk is not None:
            _http_post(f"{chess_url_from_walk}/act", {
                "actor_token":
                    client.state.identity.identity.token,
                "type": "chess.sit",
                "payload": {"seat": "white"},
            })

        # Print
        print("=" * 70)
        print("Route URL Extension — the tree, walked by URL alone")
        print("=" * 70)
        print()
        print(f"  Nexus URL (the only URL given): {urls['nexus']}")
        print(f"  Requested path: {['world:games', 'world:chess']}")
        print()
        print(f"  Intermediate URLs the client did NOT know:")
        print(f"    world:games  at  {urls['games']}")
        print(f"    world:chess  at  {urls['chess']}")
        print()
        print("  The walk:")
        for r in walk:
            marker = "✓" if (r.ok and r.verified) else (
                "○" if r.ok else "✗")
            base = r.base_url or "(no url)"
            print(f"    {marker} {r.world_id}")
            print(f"        entered at {base}")
            print(f"        {r.reason}")
        print()
        print(f"  Passport entries: {len(client.state.passport)}")
        print()
        print("  What this demonstrates:")
        print("    - A UrlResolvingRoomWorld returns Routes whose")
        print("      target manifests carry HTTP URLs. The room's")
        print("      own published manifest keeps its URI-scheme")
        print("      endpoints — the Route is a pointer that")
        print("      resolves them.")
        print("    - follow_route's base_url parameter is now")
        print("      optional. When omitted, it derives from the")
        print("      Route. Backward compatible.")
        print("    - walk_to(client, nexus_url, [games, chess])")
        print("      reaches a leaf without any external URL")
        print("      knowledge. The tree is fully navigable by a")
        print("      client that knows only the root.")
        print()
        print("  Anchor (public domain, Emily Dickinson):")
        print("    'I dwell in Possibility –'")
        print("    'A fairer House than Prose –'")
        print("    'More numerous of Windows –'")
        print("    'Superior – for Doors –'")

        audit = {
            "nexus_url": urls["nexus"],
            "hidden_urls": {
                "world:games": urls["games"],
                "world:chess": urls["chess"],
            },
            "walk": [
                {"world_id": r.world_id, "ok": r.ok,
                 "verified": r.verified,
                 "base_url": r.base_url, "reason": r.reason}
                for r in walk
            ],
            "passport_entries": len(client.state.passport),
            "reached_chess": (
                walk and walk[-1].ok
                and walk[-1].world_id == "world:chess"),
        }
        (path / "route_urls_demo.json").write_text(
            _json.dumps(audit, indent=2))
        print(f"\n  → {path}/route_urls_demo.json")
        return audit
    finally:
        for srv in servers.values():
            srv.stop()
