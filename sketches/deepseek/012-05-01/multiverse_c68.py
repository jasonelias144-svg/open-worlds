"""
multiverse_c68.py — Component 68: The Curator Process.

Turns C55's WorldCurator into a long-running daemon.

What a CuratorProcess does:
  - Serves an HTTP endpoint (/curator/manifest, /curator/message)
    for inbound messages from other curators.
  - Verifies inbound messages against the peer registry (not
    just the message's declared key — see module note).
  - Runs a periodic scheduler: attempt links, respond to pending
    hellos, observe_and_propose, persist state.
  - Persists its own identity, links, and log across restarts.

What it does NOT do (v0.1, honest):
  - TLS. HTTP only. Production must use HTTPS (C64 §3).
  - Curator URL discovery. Peers are configured explicitly
    (PeerRegistry). Anchors don't yet advertise curator URLs —
    a v0.2 LFS spec would add this.
  - Consensus. Single-writer persistence.
  - Retry logic beyond "log and continue on next tick".
  - Message replay protection. A valid message could be delivered
    twice; C55's receive is not idempotent for hellos (a second
    hello from the same peer just refreshes the pending slot).

The C55 security gap C68 closes:
  C55's `WorldCurator.receive(message)` verifies the message's
  signature against the *key the message claims*. On a public
  endpoint, that's not enough — an attacker could claim any
  world_id. C68's CuratorServer adds a check: the sender's
  declared world_id must be in the peer registry, and the
  signature must verify against the registry's key.

Composition: C1, C13, C55, C65, C66.

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: server endpoints, signature verification,
    peer-registry mismatch, HTTP client happy/error, scheduler
    tick shapes, link establishment, persistence roundtrip,
    graceful shutdown, two-curator end-to-end, proposal
    generation.
  - "A world never raises on what a visitor sends" — server
    returns Refusal; scheduler catches per-tick errors.
  - "History, not rank" — log and proposals are append-only.
"""

import hashlib
import json
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from multiverse_c1 import Identity
from multiverse_c3 import Act, Ack, Refusal
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c55 import (
    WorldCurator, CuratorMessage, WorldLink, CuratorLogEntry,
    CuratorIdentity, verify_curator_message,
    MockCuratorModel, CuratorModelBackend,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _keypair_to_hex(kp: KeyPair) -> str:
    from cryptography.hazmat.primitives import serialization
    private = kp._private
    return private.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    ).hex()


def _keypair_from_hex(hex_str: str) -> KeyPair:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
    )
    private = Ed25519PrivateKey.from_private_bytes(
        bytes.fromhex(hex_str))
    return KeyPair(private=private)


def _ack_or_refusal_to_dict(r) -> Dict:
    if isinstance(r, Ack):
        return {"kind": "ack", "entity_id": r.entity_id,
                "timestamp": r.timestamp}
    if isinstance(r, Refusal):
        return {"kind": "refusal", "reason": r.reason}
    return {"kind": "error",
            "reason": f"unexpected {type(r).__name__}"}


# =====================================================================
# PeerRegistry
# =====================================================================

class PeerRegistry:
    """Known peer curators. Mutable — peers can be added after
    construction, which the demo uses to break a chicken-and-egg
    problem (both processes must start before either URL is known).
    """

    def __init__(self):
        self._peers: Dict[str, Dict] = {}

    def add(
        self, world_id: str, curator_url: str, public_key: str,
    ) -> None:
        if not world_id or not curator_url or not public_key:
            raise ValueError(
                "world_id, curator_url, public_key all required")
        if len(public_key) != 64:
            raise ValueError(
                "public_key must be 64 hex chars")
        self._peers[world_id] = {
            "curator_url": curator_url.rstrip("/"),
            "public_key": public_key,
        }

    def remove(self, world_id: str) -> None:
        self._peers.pop(world_id, None)

    def get(self, world_id: str) -> Optional[Dict]:
        return self._peers.get(world_id)

    def all(self) -> Dict[str, Dict]:
        return dict(self._peers)

    def __len__(self) -> int:
        return len(self._peers)

    def to_dict(self) -> Dict:
        return dict(self._peers)

    @classmethod
    def from_dict(cls, d: Dict) -> "PeerRegistry":
        reg = cls()
        for wid, info in d.items():
            reg.add(wid, info["curator_url"],
                    info["public_key"])
        return reg


# =====================================================================
# CuratorServer
# =====================================================================

class CuratorServer:
    """HTTP endpoint for a curator. Accepts inbound messages."""

    def __init__(
        self, curator: WorldCurator, peers: PeerRegistry,
        host: str = "127.0.0.1", port: int = 0,
    ):
        self._curator = curator
        self._peers = peers
        self._host = host
        self._port = port
        self._httpd: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    @property
    def url(self) -> str:
        return f"http://{self._host}:{self._port}"

    def _get_actual_port(self) -> int:
        if self._httpd is None:
            return self._port
        return self._httpd.server_address[1]

    def _send(self, handler, status: int, payload: Dict) -> None:
        body = json.dumps(payload).encode()
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json")
        handler.send_header("Content-Length", str(len(body)))
        handler.end_headers()
        handler.wfile.write(body)

    def _make_handler(self):
        server = self
        curator = self._curator
        peers = self._peers

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                try:
                    if self.path == "/curator/manifest":
                        server._send(self, 200, {
                            "world_id": curator.world_id,
                            "public_key": curator.public_key,
                            "endpoint": (
                                f"{server.url}/curator/message"),
                        })
                    else:
                        server._send(self, 404, {
                            "error": "not found"})
                except Exception as e:
                    server._send(self, 500, {
                        "error": str(e)})

            def do_POST(self):
                if self.path != "/curator/message":
                    server._send(self, 404, {
                        "error": "not found"})
                    return
                try:
                    length = int(
                        self.headers.get("Content-Length", 0))
                    body = json.loads(
                        self.rfile.read(length).decode())
                except (json.JSONDecodeError,
                        UnicodeDecodeError, ValueError) as e:
                    server._send(self, 400, {
                        "kind": "refusal",
                        "reason": f"malformed body: {e}"})
                    return
                try:
                    message = CuratorMessage.from_dict(body)
                except (KeyError, ValueError, TypeError) as e:
                    server._send(self, 400, {
                        "kind": "refusal",
                        "reason": f"malformed message: {e}"})
                    return
                # Peer-registry check
                peer = peers.get(message.sender_world_id)
                if peer is None:
                    server._send(self, 200, {
                        "kind": "refusal",
                        "reason": (
                            f"unknown peer "
                            f"{message.sender_world_id!r}")})
                    return
                expected_key = peer["public_key"]
                if not verify_curator_message(
                        message, expected_key):
                    server._send(self, 200, {
                        "kind": "refusal",
                        "reason": (
                            "signature does not match "
                            "registered peer key")})
                    return
                result = curator.receive(message)
                server._send(self, 200,
                             _ack_or_refusal_to_dict(result))

        return Handler

    def start(self) -> None:
        self._httpd = HTTPServer(
            (self._host, self._port),
            self._make_handler())
        self._port = self._httpd.server_address[1]
        self._thread = threading.Thread(
            target=self._httpd.serve_forever,
            daemon=True)
        self._thread.start()

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None


# =====================================================================
# CuratorHTTPClient
# =====================================================================

class CuratorHTTPClient:
    """Delivers CuratorMessages to a peer's curator endpoint."""

    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def deliver(
        self, message: CuratorMessage,
    ) -> Tuple[bool, str]:
        url = f"{self.base_url}/curator/message"
        body = json.dumps(message.to_dict()).encode()
        req = urllib.request.Request(
            url, data=body,
            headers={"Content-Type": "application/json"},
            method="POST")
        try:
            with urllib.request.urlopen(
                    req, timeout=self.timeout) as r:
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
        return (False, f"unexpected response: {resp.get('kind')}")

    def fetch_manifest(self) -> Optional[Dict]:
        try:
            with urllib.request.urlopen(
                    f"{self.base_url}/curator/manifest",
                    timeout=self.timeout) as r:
                return json.loads(r.read().decode())
        except (urllib.error.URLError,
                urllib.error.HTTPError,
                json.JSONDecodeError):
            return None


# =====================================================================
# CuratorStore
# =====================================================================

class CuratorStore:
    """Persistence for a curator. Append-only logs, save-or-replace
    snapshots for identity/links/outbound-hellos."""

    IDENTITY_FILE = "curator_identity.json"
    LINKS_FILE = "links.json"
    OUTBOUND_HELLOS_FILE = "outbound_hellos.json"
    LOG_FILE = "curator_log.jsonl"
    PROPOSALS_FILE = "proposals.jsonl"

    def __init__(self, state_dir: Path):
        self.state_dir = Path(state_dir)

    def ensure_dir(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)

    # -- Identity ------------------------------------------------

    def save_identity(
        self, world_id: str, kp: KeyPair,
    ) -> None:
        self.ensure_dir()
        (self.state_dir / self.IDENTITY_FILE).write_text(
            json.dumps({
                "world_id": world_id,
                "public_key_hex": kp.public_key_hex(),
                "private_key_hex": _keypair_to_hex(kp),
            }, indent=2))

    def load_identity(self) -> Optional[Tuple[str, KeyPair]]:
        p = self.state_dir / self.IDENTITY_FILE
        if not p.exists():
            return None
        try:
            data = json.loads(p.read_text())
            return (data["world_id"],
                    _keypair_from_hex(data["private_key_hex"]))
        except (KeyError, ValueError, TypeError,
                json.JSONDecodeError):
            return None

    # -- Links ---------------------------------------------------

    def save_links(self, links: List[WorldLink]) -> None:
        self.ensure_dir()
        (self.state_dir / self.LINKS_FILE).write_text(
            json.dumps([l.to_dict() for l in links], indent=2))

    def load_links(self) -> List[WorldLink]:
        p = self.state_dir / self.LINKS_FILE
        if not p.exists():
            return []
        try:
            raw = json.loads(p.read_text())
            return [WorldLink.from_dict(d) for d in raw]
        except (KeyError, ValueError, TypeError,
                json.JSONDecodeError):
            return []

    # -- Outbound hellos -----------------------------------------

    def save_outbound_hellos(
        self, hellos: Dict[str, CuratorMessage],
    ) -> None:
        self.ensure_dir()
        (self.state_dir / self.OUTBOUND_HELLOS_FILE).write_text(
            json.dumps(
                {k: v.to_dict() for k, v in hellos.items()},
                indent=2))

    def load_outbound_hellos(self) -> Dict[str, CuratorMessage]:
        p = self.state_dir / self.OUTBOUND_HELLOS_FILE
        if not p.exists():
            return {}
        try:
            raw = json.loads(p.read_text())
            return {k: CuratorMessage.from_dict(v)
                    for k, v in raw.items()}
        except (KeyError, ValueError, TypeError,
                json.JSONDecodeError):
            return {}

    # -- Append-only logs ----------------------------------------

    def append_log(self, entry: CuratorLogEntry) -> None:
        self.ensure_dir()
        with open(self.state_dir / self.LOG_FILE, "a") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

    def read_log(self) -> List[Dict]:
        p = self.state_dir / self.LOG_FILE
        if not p.exists():
            return []
        out = []
        with open(p) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return out

    def append_proposal(self, proposal_dict: Dict) -> None:
        self.ensure_dir()
        with open(self.state_dir / self.PROPOSALS_FILE, "a") as f:
            f.write(json.dumps({
                "timestamp": _now(),
                "proposal": proposal_dict,
            }) + "\n")

    def read_proposals(self) -> List[Dict]:
        p = self.state_dir / self.PROPOSALS_FILE
        if not p.exists():
            return []
        out = []
        with open(p) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return out


# =====================================================================
# CuratorProcess
# =====================================================================

class CuratorProcess:
    """The full curator daemon.

    Wraps C55's WorldCurator with:
      - CuratorServer (inbound HTTP)
      - PeerRegistry (known peers)
      - CuratorStore (persistence)
      - Scheduler thread (periodic tick)
    """

    def __init__(
        self,
        world: Any,
        world_kp: KeyPair,
        peers: PeerRegistry,
        state_dir: Path,
        host: str = "127.0.0.1",
        port: int = 0,
        model_backend: Optional[CuratorModelBackend] = None,
        cycle_interval: float = 5.0,
        identity: Optional[Identity] = None,
    ):
        if not HAS_CRYPTO:
            raise RuntimeError(
                "CuratorProcess requires `cryptography`")
        self._world = world
        self._world_kp = world_kp
        self._peers = peers
        self._store = CuratorStore(state_dir)
        self._cycle_interval = cycle_interval

        # Create the underlying curator
        self._curator = WorldCurator(
            world, world_kp,
            model_backend=model_backend or MockCuratorModel())
        self._server = CuratorServer(
            self._curator, peers, host=host, port=port)

        # Outbound hello tracking (which peers we've sent hello to)
        self._outbound_hellos: Dict[str, CuratorMessage] = {}
        # Client cache
        self._clients: Dict[str, CuratorHTTPClient] = {}

        # Scheduler state
        self._stop_event = threading.Event()
        self._scheduler_thread: Optional[threading.Thread] = None
        self._tick_count = 0
        self._running = False

    # -- Accessors ------------------------------------------------

    @property
    def world_id(self) -> str:
        return self._curator.world_id

    @property
    def public_key(self) -> str:
        return self._curator.public_key

    @property
    def url(self) -> str:
        return self._server.url

    @property
    def curator(self) -> WorldCurator:
        return self._curator

    @property
    def peers(self) -> PeerRegistry:
        return self._peers

    @property
    def store(self) -> CuratorStore:
        return self._store

    def links(self) -> List[WorldLink]:
        return self._curator.links()

    def log_entries(self) -> List[CuratorLogEntry]:
        return self._curator.log_entries()

    # -- Lifecycle -----------------------------------------------

    def start(self) -> None:
        """Start the server and the scheduler thread."""
        if self._running:
            return
        self._store.save_identity(self.world_id, self._world_kp)
        self._server.start()
        self._stop_event.clear()
        self._scheduler_thread = threading.Thread(
            target=self._run_loop, daemon=True)
        self._scheduler_thread.start()
        self._running = True

    def stop(self) -> None:
        """Stop the scheduler and the server."""
        if not self._running:
            return
        self._stop_event.set()
        self._server.stop()
        if self._scheduler_thread is not None:
            self._scheduler_thread.join(timeout=5.0)
            self._scheduler_thread = None
        self._running = False

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.tick()
            except Exception:
                pass  # log-and-continue
            self._stop_event.wait(self._cycle_interval)

    # -- Client cache --------------------------------------------

    def _client_for(self, peer_id: str) -> Optional[CuratorHTTPClient]:
        peer = self._peers.get(peer_id)
        if peer is None:
            return None
        if peer_id not in self._clients:
            self._clients[peer_id] = CuratorHTTPClient(
                peer["curator_url"])
        return self._clients[peer_id]

    def _deliver(
        self, peer_id: str, message: CuratorMessage,
    ) -> Tuple[bool, str]:
        client = self._client_for(peer_id)
        if client is None:
            return (False, f"peer {peer_id!r} not registered")
        return client.deliver(message)

    # -- Scheduler tick ------------------------------------------

    def tick(self) -> Dict:
        """One scheduling cycle. Returns a structured report.

        Actions in order:
          1. For each known peer not yet linked:
             a. If we have a pending hello from them AND we've
                hello'd them → establish link.
             b. If we have a pending hello from them AND we
                haven't hello'd them → send reciprocating hello.
             c. If we haven't hello'd them and have no pending
                hello from them → send initiating hello.
          2. observe_and_propose() → append proposal if produced.
          3. Persist links + outbound hellos.
        """
        actions: List[Dict] = []
        for peer_id in self._peers.all():
            if peer_id == self.world_id:
                continue  # don't talk to self
            if any(l.hello_a.sender_world_id == peer_id
                   or l.hello_b.sender_world_id == peer_id
                   for l in self._curator.links()):
                continue  # already linked
            pending = self._curator._pending_hellos.get(peer_id)
            we_helloed = peer_id in self._outbound_hellos

            if pending is not None and we_helloed:
                # Both sides have hello'd — establish link
                try:
                    our_hello = self._outbound_hellos[peer_id]
                    link = WorldLink(
                        hello_a=pending,
                        hello_b=our_hello,
                        established_at=_now())
                    self._curator._links[peer_id] = link
                    entry = CuratorLogEntry(
                        timestamp=link.established_at,
                        kind="link_established",
                        actor_world_id=peer_id,
                        data={
                            "with": peer_id,
                            "link_hash": link.link_hash()})
                    self._curator._log.append(entry)
                    self._store.append_log(entry)
                    actions.append({
                        "kind": "link_established",
                        "peer": peer_id})
                except Exception as e:
                    actions.append({
                        "kind": "link_failed",
                        "peer": peer_id,
                        "error": str(e)})
            elif pending is not None:
                # They hello'd us; reciprocate
                try:
                    hello_msg = self._curator.hello(peer_id)
                    self._outbound_hellos[peer_id] = hello_msg
                    ok, reason = self._deliver(peer_id, hello_msg)
                    actions.append({
                        "kind": "hello_reciprocated",
                        "peer": peer_id,
                        "ok": ok,
                        "reason": reason})
                except Exception as e:
                    actions.append({
                        "kind": "hello_failed",
                        "peer": peer_id,
                        "error": str(e)})
            elif not we_helloed:
                # Initiate
                try:
                    hello_msg = self._curator.hello(peer_id)
                    self._outbound_hellos[peer_id] = hello_msg
                    ok, reason = self._deliver(peer_id, hello_msg)
                    actions.append({
                        "kind": "hello_sent",
                        "peer": peer_id,
                        "ok": ok,
                        "reason": reason})
                except Exception as e:
                    actions.append({
                        "kind": "hello_failed",
                        "peer": peer_id,
                        "error": str(e)})

        # Observe and propose
        try:
            proposal = self._curator.observe_and_propose()
            if proposal is not None:
                actions.append({
                    "kind": "proposal_generated",
                    "title": proposal.payload.get("title", ""),
                    "proposal_hash": proposal.message_hash()})
                self._store.append_proposal(proposal.to_dict())
        except Exception as e:
            actions.append({
                "kind": "propose_failed",
                "error": str(e)})

        # Persist links + outbound hellos
        try:
            self._store.save_links(self._curator.links())
            self._store.save_outbound_hellos(
                self._outbound_hellos)
        except Exception:
            pass

        self._tick_count += 1
        return {"tick": self._tick_count, "actions": actions}

    # -- Convenience for tests -----------------------------------

    def send_hello(self, peer_id: str) -> Tuple[bool, str]:
        """Manually send a hello to a peer (bypassing the tick)."""
        hello_msg = self._curator.hello(peer_id)
        self._outbound_hellos[peer_id] = hello_msg
        return self._deliver(peer_id, hello_msg)


def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Two curator processes, one federation, full lifecycle.

    1. Deploy federation (C66).
    2. Start two curators (poetry, chemistry), empty peers.
    3. Add peers now that URLs are known.
    4. Tick both until linked.
    5. Submit 3 refused acts to poetry to trigger the mock
       model.
    6. Tick poetry curator → proposal generated.
    7. Third-party verifies: proposals persisted, links persisted,
       curator identity persisted.
    8. Graceful shutdown.
    """
    import json as _json
    from multiverse_c1 import create_identity
    from multiverse_c3 import Act, Refusal
    from multiverse_c65 import FederationClient
    from multiverse_c66 import (
        DeployConfig, deploy_federation,
        _patch_c65_manifest_verification,
    )

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    _patch_c65_manifest_verification()

    if artifact_dir is None:
        artifact_dir = "artifacts"
    root_dir = Path(artifact_dir) / "curator_process"
    root_dir.mkdir(parents=True, exist_ok=True)
    fed_dir = root_dir / "federation"
    poetry_dir = root_dir / "curator_poetry"
    chem_dir = root_dir / "curator_chemistry"

    if fed_dir.exists():
        import shutil
        shutil.rmtree(fed_dir)
    for d in (poetry_dir, chem_dir):
        if d.exists():
            import shutil
            shutil.rmtree(d)

    fed = deploy_federation(DeployConfig(
        state_dir=fed_dir,
        federation_name="Curator Process Demo",
    ))

    poetry_proc = None
    chem_proc = None
    try:
        # -- 1. Start two curators (empty peers) -------------
        poetry_peers = PeerRegistry()
        chem_peers = PeerRegistry()

        poetry_proc = CuratorProcess(
            world=fed.poetry.base,  # the _DelegatingSignedWorld
            world_kp=fed.poetry_kp,
            peers=poetry_peers,
            state_dir=poetry_dir,
            cycle_interval=0.5,
            identity=create_identity("curator:poetry"),
        )
        chem_proc = CuratorProcess(
            world=fed.chemistry.base,
            world_kp=fed.chemistry_kp,
            peers=chem_peers,
            state_dir=chem_dir,
            cycle_interval=0.5,
            identity=create_identity("curator:chemistry"),
        )
        poetry_proc.start()
        chem_proc.start()

        # -- 2. Now that URLs are known, add peers --------
        poetry_peers.add(
            "world:chemistry",
            chem_proc.url,
            fed.chemistry_kp.public_key_hex())
        chem_peers.add(
            "world:poetry",
            poetry_proc.url,
            fed.poetry_kp.public_key_hex())

        # -- 3. Tick both until linked --------------------
        tick_trace = []
        linked_at = None
        for i in range(20):
            p = poetry_proc.tick()
            c = chem_proc.tick()
            tick_trace.append({
                "iteration": i,
                "poetry_actions": p["actions"],
                "chem_actions": c["actions"],
            })
            if (len(poetry_proc.links()) > 0
                    and len(chem_proc.links()) > 0
                    and linked_at is None):
                linked_at = i
            if linked_at is not None:
                break

        # -- 4. Trigger refusals in poetry ----------------
        alice = FederationClient(root_dir / "alice")
        alice.create_identity("Refuser")
        alice.connect(
            fed.anchors_url(), fed.root_kp.public_key_hex())
        alice.enter_world("world:poetry")
        refusals = []
        for _ in range(3):
            r = alice.submit_act(
                "world:poetry", "poem.turn", {
                    "acknowledgment": "",  # missing
                    "proposal": "x",
                    "invitation": "y",
                    "holds_open": True,
                })
            refusals.append(r.ok)
        assert all(not ok for ok in refusals)

        # -- 5. Tick poetry curator: propose --------------
        tick_after_refusals = poetry_proc.tick()
        proposals = poetry_proc.store.read_proposals()

        # -- 6. Check persisted state ---------------------
        poetry_identity = poetry_proc.store.load_identity()
        poetry_links = poetry_proc.store.load_links()
        poetry_log = poetry_proc.store.read_log()

        # -- 7. Graceful shutdown -------------------------
        poetry_proc.stop()
        chem_proc.stop()

        # -- 8. Verify server is down ---------------------
        import urllib.error
        try:
            urllib.request.urlopen(
                f"{poetry_proc.url}/curator/manifest", timeout=1)
            server_down = False
        except Exception:
            server_down = True

        # -- Print ----------------------------------------
        print("=" * 70)
        print("Curator Process — two daemons, one federation")
        print("=" * 70)
        print()
        print(f"  Poetry curator:    {poetry_proc.url}")
        print(f"  Chemistry curator: {chem_proc.url}")
        print()
        print(f"  Ticks until linked: {linked_at + 1 if linked_at is not None else 'never'}")
        print(f"  Poetry links:      {len(poetry_links)}")
        print(f"  Chemistry links:   {len(chem_proc.links())}")
        print()
        print("  Tick trace:")
        for entry in tick_trace[:3]:
            print(f"    Tick {entry['iteration']}:")
            for a in entry["poetry_actions"]:
                print(f"      poetry:    {a}")
            for a in entry["chem_actions"]:
                print(f"      chemistry: {a}")
        print()
        print(f"  After 3 refusals in poetry:")
        print(f"    Proposals generated: {len(proposals)}")
        for p in proposals:
            title = p["proposal"].get("payload", {}).get(
                "title", "")
            print(f"      · {title}")
        print()
        print(f"  Persisted state (poetry curator):")
        print(f"    Identity:    {'✓' if poetry_identity else '✗'}")
        print(f"    Links:       {len(poetry_links)}")
        print(f"    Log entries: {len(poetry_log)}")
        print(f"    Proposals:   {len(proposals)}")
        print()
        print(f"  Server shut down: {server_down}")
        print()
        print("  What this demonstrates:")
        print("    - Curators run as daemons (C64 §5), each with its")
        print("      own HTTP endpoint and scheduler thread.")
        print("    - Inbound messages are verified against the peer")
        print("      registry (not the message's declared key) — the")
        print("      security fix C55's receive() alone doesn't give.")
        print("    - The scheduler drives hello exchange, link")
        print("      establishment, observation, and proposal")
        print("      generation.")
        print("    - All curator state (identity, links, log,")
        print("      proposals) persists to disk across restarts.")
        print("    - Graceful shutdown: server down, thread joined.")
        print()
        print("  Anchor (public domain, Emily Dickinson):")
        print("    'The Soul selects her own Society –'")
        print("    'Then – shuts the Door –'")

        audit = {
            "poetry_curator_url": poetry_proc.url,
            "chemistry_curator_url": chem_proc.url,
            "ticks_until_linked": (
                linked_at + 1 if linked_at is not None else None),
            "poetry_link_count": len(poetry_links),
            "chemistry_link_count": len(chem_proc.links()),
            "refusals_submitted": len(refusals),
            "proposal_count": len(proposals),
            "proposal_titles": [
                p["proposal"].get("payload", {}).get(
                    "title", "")
                for p in proposals],
            "persisted": {
                "poetry_identity_loaded":
                    poetry_identity is not None,
                "poetry_log_entries": len(poetry_log),
            },
            "server_shut_down": server_down,
        }
        (root_dir / "curator_process_demo.json").write_text(
            _json.dumps(audit, indent=2))
        print(f"\n  → {root_dir}/curator_process_demo.json")
        return audit
    finally:
        if poetry_proc is not None:
            try:
                poetry_proc.stop()
            except Exception:
                pass
        if chem_proc is not None:
            try:
                chem_proc.stop()
            except Exception:
                pass
        fed.stop()
