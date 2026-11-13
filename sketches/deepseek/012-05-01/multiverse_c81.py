"""
multiverse_c81.py — Component 81: The Growing World.

A world whose extent grows as participants claim plots.

Initial state: a seed plot at (0, 0, 4, 4), owned by the world
itself and auto-registered as the first growth event. Every
subsequent claim extends the canvas outward from there.

The Law (published; enforced by the kernel):

  1. A claim must be contiguous with the current extent.
     "Contiguous" = shares at least one cell edge with an
     active plot. Corner-touching is not contiguous.
  2. A claim must not overlap an active plot.
  3. Width and height must be in [1, 20].
  4. A purpose string is required (non-empty).
  5. The seed plot cannot be retired.

Retirement:
  - Only the owner can retire their plot.
  - Retirement is permitted unconditionally in v0.1; the
    current extent may become disconnected. A v0.2 policy
    would preserve connectivity.

What grows and how it is verified:
  - Every claim and every retirement is a signed GrowthEvent,
    chained per plot via prior_event_hash, signed by the
    world's curator key.
  - A third party with the world's public key can verify the
    chain offline and reconstruct state at any historical
    point.

Composition: C3 (Manifest, acts, log_since), C13 (signatures),
C55 (curator-key pattern), C79 (per-plot lifecycle chain). No
new primitives.

Honest limits (documented, tested):
  - Refusals are logged but only by the world; a third party
    cannot independently verify that a refused claim was
    actually made. Accepted claims are fully verifiable.
  - Retirement is unconditional. The extent may disconnect.
    A v0.2 policy would preserve connectivity.
  - No curator-side learning. "Growing from the outside" is
    C55's territory (observe_and_propose). C81 is growth from
    the inside only.
  - No updates to a plot after claim (no resize, rename). Only
    claim and retire in v0.1.
  - No cross-world plot sharing. Two GrowingWorlds are
    independent extents.
  - Plots are 2D integer rectangles. A 3D/voxel version is the
    same discipline with a different geometry module.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import hashlib
import json
import threading
import time
import urllib.error
import urllib.request

from multiverse_c3 import (
    Manifest, Petition, Act, LogEntry,
    Admission as WCPAdmission, Refusal, Ack,
)
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c79 import ChainVerdict
from wcp_http_shim import WorldProtocolServer


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_payload(p: bytes) -> str:
    return hashlib.sha256(p).hexdigest()


GROWTH_EVENT_TYPES = frozenset({"claimed", "retired"})


# =====================================================================
# GrowthEvent
# =====================================================================

@dataclass(frozen=True)
class GrowthEvent:
    event_type: str
    plot_id: str
    owner_token: str
    owner_name: str
    x: int
    y: int
    width: int
    height: int
    purpose: str
    prior_event_hash: Optional[str]
    timestamp: str
    signer_id: str
    signer_public_key: str
    signature: str

    def __post_init__(self):
        if self.event_type not in GROWTH_EVENT_TYPES:
            raise ValueError(
                f"event_type must be one of "
                f"{sorted(GROWTH_EVENT_TYPES)}; "
                f"got {self.event_type!r}")
        for f in ("plot_id", "owner_token", "owner_name",
                  "purpose", "timestamp", "signer_id",
                  "signer_public_key", "signature"):
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
        if not (1 <= self.width <= 20):
            raise ValueError("width must be in [1, 20]")
        if not (1 <= self.height <= 20):
            raise ValueError("height must be in [1, 20]")

    def geometry(self) -> Tuple[int, int, int, int]:
        return (self.x, self.y, self.width, self.height)

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "growth_event",
            "event_type": self.event_type,
            "plot_id": self.plot_id,
            "owner_token": self.owner_token,
            "owner_name": self.owner_name,
            "x": self.x, "y": self.y,
            "width": self.width, "height": self.height,
            "purpose": self.purpose,
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
    def from_dict(cls, d: Dict) -> "GrowthEvent":
        return cls(
            event_type=d["event_type"],
            plot_id=d["plot_id"],
            owner_token=d["owner_token"],
            owner_name=d["owner_name"],
            x=int(d["x"]), y=int(d["y"]),
            width=int(d["width"]), height=int(d["height"]),
            purpose=d["purpose"],
            prior_event_hash=d.get("prior_event_hash"),
            timestamp=d["timestamp"],
            signer_id=d["signer_id"],
            signer_public_key=d["signer_public_key"],
            signature=d["signature"],
        )


def sign_growth_event(
    event_type: str,
    plot_id: str,
    owner_token: str,
    owner_name: str,
    x: int, y: int, width: int, height: int,
    purpose: str,
    prior_event_hash: Optional[str],
    signer_id: str,
    signer_kp: KeyPair,
    timestamp: Optional[str] = None,
) -> GrowthEvent:
    if not HAS_CRYPTO:
        raise RuntimeError(
            "sign_growth_event requires cryptography")
    if timestamp is None:
        timestamp = _now()
    payload = canonical_bytes({
        "kind": "growth_event",
        "event_type": event_type,
        "plot_id": plot_id,
        "owner_token": owner_token,
        "owner_name": owner_name,
        "x": x, "y": y,
        "width": width, "height": height,
        "purpose": purpose,
        "prior_event_hash": prior_event_hash,
        "timestamp": timestamp,
        "signer_id": signer_id,
        "signer_public_key": signer_kp.public_key_hex(),
    })
    return GrowthEvent(
        event_type=event_type,
        plot_id=plot_id,
        owner_token=owner_token,
        owner_name=owner_name,
        x=x, y=y, width=width, height=height,
        purpose=purpose,
        prior_event_hash=prior_event_hash,
        timestamp=timestamp,
        signer_id=signer_id,
        signer_public_key=signer_kp.public_key_hex(),
        signature=signer_kp.sign(payload).hex(),
    )


def verify_growth_event(
    event: GrowthEvent,
    expected_world_key: Optional[str] = None,
) -> bool:
    if not HAS_CRYPTO:
        return False
    try:
        if not isinstance(event, GrowthEvent):
            return False
        key = expected_world_key or event.signer_public_key
        return verify_signature(
            key, event.canonical_payload(), event.signature)
    except Exception:
        return False


# =====================================================================
# Geometry
# =====================================================================

def _plots_overlap(
    a: Tuple[int, int, int, int],
    b: Tuple[int, int, int, int],
) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return not (ax + aw <= bx or bx + bw <= ax or
                ay + ah <= by or by + bh <= ay)


def _plots_edge_adjacent(
    a: Tuple[int, int, int, int],
    b: Tuple[int, int, int, int],
) -> bool:
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    # Vertical edge shared (one is right of the other)
    if ax + aw == bx and max(ay, by) < min(ay + ah, by + bh):
        return True
    if bx + bw == ax and max(ay, by) < min(ay + ah, by + bh):
        return True
    # Horizontal edge shared (one is above the other)
    if ay + ah == by and max(ax, bx) < min(ax + aw, bx + bw):
        return True
    if by + bh == ay and max(ax, bx) < min(ax + aw, bx + bw):
        return True
    return False


# =====================================================================
# Reconstruction
# =====================================================================

def reconstruct_plots_from_events(
    events: List[GrowthEvent],
) -> Dict[str, Dict]:
    """Reconstruct the current active plot map from a list of
    growth events, applied in order.
    """
    active: Dict[str, Dict] = {}
    for ev in events:
        if ev.event_type == "claimed":
            active[ev.plot_id] = {
                "plot_id": ev.plot_id,
                "owner_token": ev.owner_token,
                "owner_name": ev.owner_name,
                "x": ev.x, "y": ev.y,
                "width": ev.width, "height": ev.height,
                "purpose": ev.purpose,
            }
        elif ev.event_type == "retired":
            active.pop(ev.plot_id, None)
    return active


def reconstruct_at(
    events: List[GrowthEvent], at_event_hash: str,
) -> Dict[str, Dict]:
    """Reconstruct state as of the given event (inclusive)."""
    target_index = None
    for i, ev in enumerate(events):
        if ev.event_hash() == at_event_hash:
            target_index = i
            break
    if target_index is None:
        return {}
    return reconstruct_plots_from_events(events[:target_index + 1])


def extent_bbox(
    active: Dict[str, Dict],
) -> Optional[Tuple[int, int, int, int]]:
    if not active:
        return None
    x_min = min(p["x"] for p in active.values())
    y_min = min(p["y"] for p in active.values())
    x_max = max(p["x"] + p["width"] for p in active.values())
    y_max = max(p["y"] + p["height"] for p in active.values())
    return (x_min, y_min, x_max - x_min, y_max - y_min)


def extent_area(active: Dict[str, Dict]) -> int:
    return sum(p["width"] * p["height"] for p in active.values())


def render_map(
    active: Dict[str, Dict],
    symbols: Optional[Dict[str, str]] = None,
) -> str:
    """Render a compact ASCII map. Seed = 'S'; other plots use
    the numeric suffix of their plot_id (or a provided symbol
    mapping keyed by plot_id)."""
    symbols = symbols or {}
    bbox = extent_bbox(active)
    if bbox is None:
        return "(empty canvas)"
    x0, y0, w, h = bbox
    grid: Dict[Tuple[int, int], str] = {}
    for pid, p in active.items():
        sym = symbols.get(pid)
        if sym is None:
            if pid == "plot:seed":
                sym = "S"
            elif pid.startswith("plot:"):
                num = pid[len("plot:"):].lstrip("0") or "0"
                sym = num[-1] if len(num) > 1 else num
            else:
                sym = "?"
        for dx in range(p["width"]):
            for dy in range(p["height"]):
                grid[(p["x"] + dx, p["y"] + dy)] = sym
    rows = []
    for yy in range(y0, y0 + h):
        row = [grid.get((xx, yy), ".") for xx in range(x0, x0 + w)]
        rows.append(" ".join(row))
    return "\n".join(rows)


# =====================================================================
# Chain verification
# =====================================================================

def verify_growth_chain(
    events: List[GrowthEvent],
    expected_world_key: Optional[str] = None,
) -> ChainVerdict:
    """Verify a growth event log. Never raises.

    Checks:
      1. Every event signature verifies.
      2. Every plot's chain starts with a 'claimed' event
         whose prior_event_hash is None.
      3. Every subsequent event references the prior
         event's hash.
      4. Every plot has at most 2 events in v0.1
         (claimed + retired).
      5. No two active plots overlap.
    """
    if not HAS_CRYPTO:
        return ChainVerdict(False, "cryptography not installed")
    if not isinstance(events, list):
        return ChainVerdict(False, "events must be a list")

    for i, ev in enumerate(events):
        if not isinstance(ev, GrowthEvent):
            return ChainVerdict(
                False, f"entry {i} is not a GrowthEvent")
        if not verify_growth_event(ev, expected_world_key):
            return ChainVerdict(
                False, f"entry {i} signature INVALID")

    by_plot: Dict[str, List[GrowthEvent]] = {}
    for ev in events:
        by_plot.setdefault(ev.plot_id, []).append(ev)

    for pid, chain in by_plot.items():
        if chain[0].event_type != "claimed":
            return ChainVerdict(
                False, f"plot {pid}: first event is not "
                       f"'claimed'")
        if chain[0].prior_event_hash is not None:
            return ChainVerdict(
                False, f"plot {pid}: first event has "
                       f"prior_event_hash")
        prev_hash = chain[0].event_hash()
        for ev in chain[1:]:
            if ev.prior_event_hash != prev_hash:
                return ChainVerdict(
                    False, f"plot {pid}: chain broken at "
                           f"{ev.event_hash()[:16]}...")
            if ev.event_type != "retired":
                return ChainVerdict(
                    False, f"plot {pid}: unexpected event_type "
                           f"{ev.event_type!r} after claim")
            prev_hash = ev.event_hash()
        if len(chain) > 2:
            return ChainVerdict(
                False, f"plot {pid}: {len(chain)} events "
                       f"(max 2 in v0.1)")

    active = reconstruct_plots_from_events(events)
    plots = list(active.values())
    for i in range(len(plots)):
        for j in range(i + 1, len(plots)):
            if _plots_overlap(plots[i]["plot_id"] and
                              (plots[i]["x"], plots[i]["y"],
                               plots[i]["width"], plots[i]["height"])
                              or (plots[i]["x"], plots[i]["y"],
                                  plots[i]["width"], plots[i]["height"]),
                              (plots[j]["x"], plots[j]["y"],
                               plots[j]["width"], plots[j]["height"])):
                return ChainVerdict(
                    False,
                    f"active plots {plots[i]['plot_id']} and "
                    f"{plots[j]['plot_id']} overlap")
    return ChainVerdict(True, "chain verifies")


# =====================================================================
# GrowingWorld
# =====================================================================

class GrowingWorld:
    """A WCP world whose extent grows as participants claim plots."""

    ACT_CLAIM = "canvas.claim"
    ACT_RETIRE = "canvas.retire"

    def __init__(
        self, entity_id: str, name: str, curator_kp: KeyPair,
        seed_extent: Tuple[int, int, int, int] = (0, 0, 4, 4),
    ):
        if not HAS_CRYPTO:
            raise RuntimeError(
                "GrowingWorld requires cryptography")
        self._manifest = Manifest(
            entity_id=entity_id, name=name,
            protocol_version="WCP/0.2",
            law_url=f"canvas://{entity_id}/law",
            act_endpoint=f"canvas://{entity_id}/act",
            log_endpoint=f"canvas://{entity_id}/log",
            sub_registry_endpoint=None,
        )
        self._curator_kp = curator_kp
        self._admitted: Dict[str, str] = {}
        self._log: List[LogEntry] = []
        self._plot_counter = 0
        # Auto-register the seed
        sx, sy, sw, sh = seed_extent
        seed_event = sign_growth_event(
            event_type="claimed",
            plot_id="plot:seed",
            owner_token=entity_id,
            owner_name=name,
            x=sx, y=sy, width=sw, height=sh,
            purpose="seed",
            prior_event_hash=None,
            signer_id=entity_id,
            signer_kp=curator_kp,
        )
        self._append_event(seed_event)

    @property
    def curator_public_key(self) -> str:
        return self._curator_kp.public_key_hex()

    # -- WCP interface ------------------------------------------

    def manifest(self) -> Manifest:
        return self._manifest

    def petition(self, petition: Petition):
        if petition.petitioner_token in self._admitted:
            return Refusal(reason="Already admitted")
        self._admitted[petition.petitioner_token] = \
            petition.petitioner_name
        self._log.append(LogEntry(
            timestamp=_now(), kind="admission",
            actor_token=petition.petitioner_token,
            data={"name": petition.petitioner_name}))
        return WCPAdmission(
            entity_id=self._manifest.entity_id,
            timestamp=_now())

    def act(self, act: Act):
        if act.actor_token not in self._admitted:
            return self._refuse(
                act.actor_token, "Actor is not admitted")
        if act.type == self.ACT_CLAIM:
            return self._handle_claim(act)
        if act.type == self.ACT_RETIRE:
            return self._handle_retire(act)
        return self._refuse(
            act.actor_token, f"Unknown act type: {act.type}")

    def log_since(self, since: Optional[str] = None):
        if since is None:
            return list(self._log)
        return [e for e in self._log if e.timestamp > since]

    # -- Read model --------------------------------------------

    def events(self) -> List[GrowthEvent]:
        return [
            GrowthEvent.from_dict(e.data)
            for e in self._log
            if e.kind == "growth_event"
        ]

    def current_plots(self) -> Dict[str, Dict]:
        return reconstruct_plots_from_events(self.events())

    def current_extent_bbox(self) -> Optional[Tuple[int, int, int, int]]:
        return extent_bbox(self.current_plots())

    def current_extent_area(self) -> int:
        return extent_area(self.current_plots())

    # -- Internals --------------------------------------------

    def _append_event(self, event: GrowthEvent) -> None:
        self._log.append(LogEntry(
            timestamp=event.timestamp, kind="growth_event",
            actor_token=event.signer_id,
            data=event.to_dict()))

    def _refuse(self, actor: str, reason: str) -> Refusal:
        self._log.append(LogEntry(
            timestamp=_now(), kind="act_refused",
            actor_token=actor,
            data={"reason": reason}))
        return Refusal(reason=reason)

    def _ack(self) -> Ack:
        return Ack(entity_id=self._manifest.entity_id,
                   timestamp=_now())

    def _next_plot_id(self) -> str:
        self._plot_counter += 1
        return f"plot:{self._plot_counter:04d}"

    def _last_event_hash_for(self, plot_id: str) -> Optional[str]:
        for ev in reversed(self.events()):
            if ev.plot_id == plot_id:
                return ev.event_hash()
        return None

    def _handle_claim(self, act: Act):
        payload = act.payload or {}
        try:
            x = int(payload["x"])
            y = int(payload["y"])
            w = int(payload["width"])
            h = int(payload["height"])
        except (KeyError, ValueError, TypeError):
            return self._refuse(
                act.actor_token,
                "claim requires integer x, y, width, height")
        purpose = payload.get("purpose", "")
        if not isinstance(purpose, str) or not purpose.strip():
            return self._refuse(
                act.actor_token, "purpose required")
        if not (1 <= w <= 20):
            return self._refuse(
                act.actor_token, "width must be in [1, 20]")
        if not (1 <= h <= 20):
            return self._refuse(
                act.actor_token, "height must be in [1, 20]")
        new_rect = (x, y, w, h)
        current = self.current_plots()
        # Overlap check
        for p in current.values():
            old_rect = (p["x"], p["y"],
                        p["width"], p["height"])
            if _plots_overlap(new_rect, old_rect):
                return self._refuse(
                    act.actor_token,
                    f"overlaps plot {p['plot_id']}")
        # Contiguity check
        if not any(
            _plots_edge_adjacent(
                new_rect,
                (p["x"], p["y"], p["width"], p["height"]))
            for p in current.values()
        ):
            return self._refuse(
                act.actor_token,
                "not contiguous with the current extent")
        # Accept
        plot_id = self._next_plot_id()
        event = sign_growth_event(
            event_type="claimed",
            plot_id=plot_id,
            owner_token=act.actor_token,
            owner_name=self._admitted[act.actor_token],
            x=x, y=y, width=w, height=h,
            purpose=purpose,
            prior_event_hash=None,
            signer_id=self._manifest.entity_id,
            signer_kp=self._curator_kp,
        )
        self._append_event(event)
        return self._ack()

    def _handle_retire(self, act: Act):
        payload = act.payload or {}
        plot_id = payload.get("plot_id")
        if not isinstance(plot_id, str) or not plot_id:
            return self._refuse(
                act.actor_token, "plot_id required")
        if plot_id == "plot:seed":
            return self._refuse(
                act.actor_token, "cannot retire the seed")
        current = self.current_plots()
        p = current.get(plot_id)
        if p is None:
            return self._refuse(
                act.actor_token,
                f"no active plot {plot_id}")
        if p["owner_token"] != act.actor_token:
            return self._refuse(
                act.actor_token,
                "only the owner can retire")
        prior_hash = self._last_event_hash_for(plot_id)
        event = sign_growth_event(
            event_type="retired",
            plot_id=plot_id,
            owner_token=p["owner_token"],
            owner_name=p["owner_name"],
            x=p["x"], y=p["y"],
            width=p["width"], height=p["height"],
            purpose=p["purpose"],
            prior_event_hash=prior_hash,
            signer_id=self._manifest.entity_id,
            signer_kp=self._curator_kp,
        )
        self._append_event(event)
        return self._ack()


# =====================================================================
# Third-party fetch helper
# =====================================================================

def fetch_growth_events(
    base_url: str, since: Optional[str] = None,
) -> List[GrowthEvent]:
    """Fetch a world's log over HTTP and extract growth events.
    Never raises — returns [] on any failure."""
    url = f"{base_url.rstrip('/')}/log"
    if since:
        url += f"?since={since}"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError,
            json.JSONDecodeError, OSError):
        return []
    events: List[GrowthEvent] = []
    for e in data.get("entries", []):
        if e.get("kind") == "growth_event":
            try:
                events.append(GrowthEvent.from_dict(e["data"]))
            except (KeyError, ValueError, TypeError):
                continue
    return events


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Three artists grow a canvas. One retires. Third party
    verifies offline."""
    from multiverse_c1 import create_identity

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "growing_world"
    path.mkdir(parents=True, exist_ok=True)

    curator_kp = KeyPair.generate()
    canvas = GrowingWorld(
        "world:canvas", "The Open Canvas", curator_kp,
        seed_extent=(0, 0, 4, 4))
    server = WorldProtocolServer(canvas, port=0)
    server.serve_in_thread()
    time.sleep(0.2)
    canvas_url = (
        f"http://127.0.0.1:"
        f"{server._httpd.server_address[1]}")

    alice = create_identity("Alice")
    bob = create_identity("Bob")
    carol = create_identity("Carol")
    for who in (alice, bob, carol):
        canvas.petition(Petition(
            petitioner_token=who.token,
            petitioner_name=who.name,
            passport_admissions=(),
            message=f"{who.name} enters the canvas"))

    def claim(who, x, y, w, h, purpose):
        return canvas.act(Act(
            actor_token=who.token, type="canvas.claim",
            payload={"x": x, "y": y, "width": w, "height": h,
                     "purpose": purpose}))

    def retire(who, plot_id):
        return canvas.act(Act(
            actor_token=who.token, type="canvas.retire",
            payload={"plot_id": plot_id}))

    try:
        # Claims
        r1 = claim(alice, 4, 0, 3, 3, "studio")
        r2 = claim(bob, 7, 0, 3, 3, "gallery")
        r3 = claim(carol, 100, 100, 3, 3, "gallery")
        r4 = claim(carol, 5, 0, 2, 2, "mural")
        r5 = claim(carol, 0, 4, 3, 3, "poetry-shrine")

        # Historical snapshot before retirement
        events_before = canvas.events()
        map_before = render_map(canvas.current_plots())
        area_before = canvas.current_extent_area()

        # Retire
        r_retire = retire(alice, "plot:0001")

        # Snapshot after
        current = canvas.current_plots()
        map_after = render_map(current)
        area_after = canvas.current_extent_area()

        # Third-party verification: fetch log over HTTP
        fetched = fetch_growth_events(canvas_url)
        verdict = verify_growth_chain(
            fetched, canvas.curator_public_key)
        reconstructed = reconstruct_plots_from_events(fetched)
        # Historical: reconstruct state at the event before retire
        last_claim_event = next(
            ev for ev in reversed(fetched)
            if ev.event_type == "claimed")
        historical = reconstruct_at(
            fetched, last_claim_event.event_hash())

        # Print
        print("=" * 70)
        print("The Growing World — a canvas grows as artists claim plots")
        print("=" * 70)
        print()
        print(f"  World:  world:canvas (The Open Canvas)")
        print(f"  Seed:   (0, 0, 4, 4)")
        print(f"  Key:    {canvas.curator_public_key[:16]}...")
        print()
        print("  The claims:")
        results = [
            ("Alice", "studio", (4, 0, 3, 3), r1),
            ("Bob", "gallery", (7, 0, 3, 3), r2),
            ("Carol", "gallery", (100, 100, 3, 3), r3),
            ("Carol", "mural", (5, 0, 2, 2), r4),
            ("Carol", "poetry-shrine", (0, 4, 3, 3), r5),
        ]
        for i, (who, purpose, coords, result) in enumerate(results, 1):
            marker = "✓" if isinstance(result, Ack) else "✗"
            note = ""
            if isinstance(result, Refusal):
                note = f"  — {result.reason}"
            print(f"    [{i}] {marker} {who} claims {coords} "
                  f"{purpose!r}{note}")
        print()
        marker = "✓" if isinstance(r_retire, Ack) else "✗"
        note = (f"  — {r_retire.reason}"
                if isinstance(r_retire, Refusal) else "")
        print(f"    [6] {marker} Alice retires plot:0001{note}")
        print()
        print("  The canvas (before retirement):")
        for ln in map_before.split("\n"):
            print(f"    {ln}")
        print(f"    area: {area_before} cells")
        print()
        print("  The canvas (after retirement):")
        for ln in map_after.split("\n"):
            print(f"    {ln}")
        print(f"    area: {area_after} cells")
        print()
        print("  Third-party verification (fetched from /log):")
        print(f"    Events:                 {len(fetched)}")
        print(f"    Chain verdict:          {verdict.valid} "
              f"({verdict.reason})")
        print(f"    Active plots:           {sorted(reconstructed)}")
        print(f"    Historical (pre-retire): "
              f"{sorted(historical)}")
        print()
        print("  What this demonstrates:")
        print("    - The canvas grew from inside: participants claimed")
        print("      plots, and the world enforced the Law (contiguity,")
        print("      no overlap, size limits) at act time.")
        print("    - Each claim and each retirement is a signed")
        print("      GrowthEvent, chained per plot, verified offline")
        print("      against the world's curator key.")
        print("    - A third party can reconstruct state at any")
        print("      historical point (pre-retirement or post-)")
        print("      purely from the log.")
        print("    - The world's shape was chosen by participants.")
        print("      No component decided what the canvas should be.")
        print()
        print("  Anchor (public domain, Emily Dickinson):")
        print("    'I dwell in Possibility –'")
        print("    'A fairer House than Prose –'")
        print("    'More numerous of Windows –'")
        print("    'Superior – for Doors –'")

        audit = {
            "world_id": "world:canvas",
            "curator_public_key": canvas.curator_public_key,
            "seed_extent": (0, 0, 4, 4),
            "claims": [
                {"who": who, "purpose": purpose,
                 "coords": coords,
                 "ok": isinstance(result, Ack),
                 "reason": (result.reason
                             if isinstance(result, Refusal)
                             else None)}
                for (who, purpose, coords, result) in results
            ],
            "retire_ok": isinstance(r_retire, Ack),
            "event_count": len(fetched),
            "chain_valid": verdict.valid,
            "current_plots": sorted(reconstructed),
            "current_area": area_after,
            "historical_plots": sorted(historical),
            "historical_area": area_before,
        }
        (path / "growing_world_demo.json").write_text(
            json.dumps(audit, indent=2))
        print(f"\n  → {path}/growing_world_demo.json")
        return audit
    finally:
        server.stop()
