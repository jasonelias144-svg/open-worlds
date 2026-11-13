"""
multiverse_c82.py — Component 82: The Observing Curator.

The composition:

  GrowthObservation   — what the curator sees: plot count,
      area distribution, owner diversity, purpose
      distribution, refusal counts by category.

  GrowthModelBackend  — pluggable; MockGrowthModel is
      deterministic and triggers on thresholds. A real HF
      backend would fit the same protocol.

  RuleProposal        — a signed artifact. Recorded in the
      world's log. NEVER auto-applied.

  ObservingGrowingWorld(GrowingWorld) — adds record_proposal
      and proposals(). Two small additions.

  GrowingWorldCurator(WorldCurator) — inherits C55's
      curator identity and signing; adds observe_growth()
      and observe_and_propose_growth().

  verify_rule_proposal, fetch_rule_proposals — offline
      and HTTP verification helpers.

Composition: C3 (world/act), C13 (signatures), C55
(curator identity), C81 (GrowingWorld). No new primitives.

Honest limits (documented, tested):
  - Proposals are recommendations. C82 does not apply them.
    Applying a proposal is a separate act (a v0.3 concern).
  - Acceptance is out of scope. A world with a governance
    layer (C44-style) would vote on proposals; C82 stops at
    the proposal.
  - The mock triggers on three thresholds (size_limit
    refusal, overlap refusal, fragmentation). It doesn't
    reflect a nuanced model.
  - Proposals are logged in the world's log; no separate
    proposal index. A large world would need indexing.
  - The proposal does not specify when it was generated
    relative to the observation — same timestamp.
  - Rule proposals are not verified by the world on record;
    the world trusts its own curator (which holds the
    world's key) — same discipline as C55.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple

import hashlib
import json
import time
import urllib.error
import urllib.request

from multiverse_c3 import (
    Act, Ack, Refusal, LogEntry, Petition,
)
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c55 import WorldCurator
from multiverse_c81 import GrowingWorld
from wcp_http_shim import WorldProtocolServer


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_payload(p: bytes) -> str:
    return hashlib.sha256(p).hexdigest()


REFUSAL_KINDS = frozenset({
    "size_limit", "overlap", "contiguity", "owner", "other",
})


def _classify_refusal(reason: str) -> str:
    r = reason.lower()
    if "width must be" in r or "height must be" in r:
        return "size_limit"
    if "overlaps" in r:
        return "overlap"
    if "contiguous" in r:
        return "contiguity"
    if "owner" in r:
        return "owner"
    return "other"


# =====================================================================
# GrowthObservation
# =====================================================================

@dataclass(frozen=True)
class GrowthObservation:
    world_id: str
    growth_event_count: int
    plot_count: int
    total_area: int
    mean_area: float
    max_area: int
    min_area: int
    owner_count: int
    purpose_count: int
    purposes: Dict[str, int]
    extent_bbox: Optional[Tuple[int, int, int, int]]
    refusals_total: int
    refusals_by_kind: Dict[str, int]

    def summary(self) -> Dict:
        return {
            "world_id": self.world_id,
            "growth_event_count": self.growth_event_count,
            "plot_count": self.plot_count,
            "total_area": self.total_area,
            "mean_area": self.mean_area,
            "max_area": self.max_area,
            "min_area": self.min_area,
            "owner_count": self.owner_count,
            "purpose_count": self.purpose_count,
            "purposes": dict(self.purposes),
            "extent": (list(self.extent_bbox)
                       if self.extent_bbox else None),
            "refusals_total": self.refusals_total,
            "refusals_by_kind": dict(self.refusals_by_kind),
        }


# =====================================================================
# GrowthModelBackend
# =====================================================================

class GrowthModelBackend(Protocol):
    def generate_growth(self, summary: Dict) -> Optional[Dict]:
        ...

    def model_id(self) -> str:
        ...


class MockGrowthModel:
    """Deterministic mock that triggers on summary thresholds."""

    def model_id(self) -> str:
        return "mock:growth-v0"

    def generate_growth(self, summary: Dict) -> Optional[Dict]:
        refusals = summary.get("refusals_by_kind", {})
        if refusals.get("size_limit", 0) >= 1:
            n = refusals["size_limit"]
            return {
                "proposal_type": "raise_size_limit",
                "title": (
                    f"Raise per-plot size limit "
                    f"(triggered by {n} refusal(s))"),
                "rationale": (
                    f"{n} claim(s) refused for exceeding the "
                    f"20-cell limit. Evidence of unmet demand."),
                "suggested_rule": {
                    "max_width": 40, "max_height": 40},
            }
        if refusals.get("overlap", 0) >= 2:
            n = refusals["overlap"]
            return {
                "proposal_type": "zoning_assistance",
                "title": (
                    f"Add claim-assistance "
                    f"(triggered by {n} refusal(s))"),
                "rationale": (
                    f"{n} claims refused for overlapping "
                    f"existing plots. A suggestion service "
                    f"would reduce wasted attempts."),
                "suggested_rule": {
                    "type": "assistive_suggest"},
            }
        if (summary.get("plot_count", 0) >= 4
                and 0 < summary.get("mean_area", 0) < 6):
            return {
                "proposal_type": "growth_incentive",
                "title": "Encourage larger contiguous claims",
                "rationale": (
                    f"Mean area is {summary['mean_area']:.1f} "
                    f"across {summary['plot_count']} plots; "
                    f"the canvas is fragmenting."),
                "suggested_rule": {"min_claim_area": 9},
            }
        return None


# =====================================================================
# RuleProposal
# =====================================================================

@dataclass(frozen=True)
class RuleProposal:
    proposal_id: str
    timestamp: str
    world_id: str
    observation_summary: Dict
    proposal_type: str
    title: str
    rationale: str
    suggested_rule: Dict
    signer_id: str
    signer_public_key: str
    signature: str

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "rule_proposal",
            "proposal_id": self.proposal_id,
            "timestamp": self.timestamp,
            "world_id": self.world_id,
            "observation_summary": self.observation_summary,
            "proposal_type": self.proposal_type,
            "title": self.title,
            "rationale": self.rationale,
            "suggested_rule": self.suggested_rule,
            "signer_id": self.signer_id,
            "signer_public_key": self.signer_public_key,
        })

    def to_dict(self) -> Dict:
        d = json.loads(self.canonical_payload().decode())
        d["signature"] = self.signature
        return d

    @classmethod
    def from_dict(cls, d: Dict) -> "RuleProposal":
        return cls(
            proposal_id=d["proposal_id"],
            timestamp=d["timestamp"],
            world_id=d["world_id"],
            observation_summary=d["observation_summary"],
            proposal_type=d["proposal_type"],
            title=d["title"],
            rationale=d["rationale"],
            suggested_rule=d["suggested_rule"],
            signer_id=d["signer_id"],
            signer_public_key=d["signer_public_key"],
            signature=d["signature"],
        )


def verify_rule_proposal(
    proposal: RuleProposal,
    expected_curator_key: Optional[str] = None,
) -> bool:
    if not HAS_CRYPTO:
        return False
    try:
        if not isinstance(proposal, RuleProposal):
            return False
        key = expected_curator_key or proposal.signer_public_key
        return verify_signature(
            key, proposal.canonical_payload(),
            proposal.signature)
    except Exception:
        return False


# =====================================================================
# ObservingGrowingWorld
# =====================================================================

class ObservingGrowingWorld(GrowingWorld):
    """A GrowingWorld that accepts signed rule proposals."""

    def record_proposal(self, proposal_dict: Dict) -> None:
        self._log.append(LogEntry(
            timestamp=proposal_dict["timestamp"],
            kind="rule_proposal",
            actor_token=proposal_dict["signer_id"],
            data=proposal_dict,
        ))

    def proposals(self) -> List[Dict]:
        return [dict(e.data) for e in self._log
                if e.kind == "rule_proposal"]


# =====================================================================
# GrowingWorldCurator
# =====================================================================

class GrowingWorldCurator(WorldCurator):
    """A C55 curator specialized for GrowingWorld observation."""

    def __init__(
        self,
        world: ObservingGrowingWorld,
        world_kp: KeyPair,
        model_backend,
    ):
        super().__init__(world, world_kp,
                          model_backend=model_backend)

    def observe_growth(self) -> GrowthObservation:
        world: ObservingGrowingWorld = self._world
        events = world.events()
        active = world.current_plots()
        log = world.log_since(None)
        refusals = [e for e in log if e.kind == "act_refused"]
        purposes: Dict[str, int] = {}
        areas: List[int] = []
        owners = set()
        for p in active.values():
            purposes[p["purpose"]] = (
                purposes.get(p["purpose"], 0) + 1)
            areas.append(p["width"] * p["height"])
            owners.add(p["owner_token"])
        refusals_by_kind: Dict[str, int] = {
            k: 0 for k in REFUSAL_KINDS}
        for e in refusals:
            reason = (e.data or {}).get("reason", "")
            kind = _classify_refusal(reason)
            refusals_by_kind[kind] = (
                refusals_by_kind.get(kind, 0) + 1)
        plot_count = len(active)
        total_area = sum(areas) if areas else 0
        mean_area = (total_area / plot_count) if plot_count else 0.0
        return GrowthObservation(
            world_id=world.manifest().entity_id,
            growth_event_count=len(events),
            plot_count=plot_count,
            total_area=total_area,
            mean_area=mean_area,
            max_area=max(areas) if areas else 0,
            min_area=min(areas) if areas else 0,
            owner_count=len(owners),
            purpose_count=len(purposes),
            purposes=purposes,
            extent_bbox=world.current_extent_bbox(),
            refusals_total=len(refusals),
            refusals_by_kind=refusals_by_kind,
        )

    def observe_and_propose_growth(
        self,
    ) -> Optional[RuleProposal]:
        obs = self.observe_growth()
        if not hasattr(self._model, "generate_growth"):
            return None
        try:
            proposal_dict = self._model.generate_growth(
                obs.summary())
        except Exception:
            return None
        if not isinstance(proposal_dict, dict):
            return None
        required = ("proposal_type", "title", "rationale",
                    "suggested_rule")
        if not all(k in proposal_dict for k in required):
            return None
        return self._sign_and_record(proposal_dict, obs)

    def _sign_and_record(
        self, proposal_dict: Dict, obs: GrowthObservation,
    ) -> RuleProposal:
        world: ObservingGrowingWorld = self._world
        timestamp = _now()
        world_id = world.manifest().entity_id
        pk_hex = self._world_kp.public_key_hex()
        proposal_id = _hash_payload(canonical_bytes({
            "world_id": world_id,
            "timestamp": timestamp,
            "proposal_type": proposal_dict["proposal_type"],
            "title": proposal_dict["title"],
        }))[:16]
        payload = canonical_bytes({
            "kind": "rule_proposal",
            "proposal_id": proposal_id,
            "timestamp": timestamp,
            "world_id": world_id,
            "observation_summary": obs.summary(),
            "proposal_type": proposal_dict["proposal_type"],
            "title": proposal_dict["title"],
            "rationale": proposal_dict["rationale"],
            "suggested_rule": proposal_dict["suggested_rule"],
            "signer_id": world_id,
            "signer_public_key": pk_hex,
        })
        sig = self._world_kp.sign(payload).hex()
        proposal = RuleProposal(
            proposal_id=proposal_id,
            timestamp=timestamp,
            world_id=world_id,
            observation_summary=obs.summary(),
            proposal_type=proposal_dict["proposal_type"],
            title=proposal_dict["title"],
            rationale=proposal_dict["rationale"],
            suggested_rule=proposal_dict["suggested_rule"],
            signer_id=world_id,
            signer_public_key=pk_hex,
            signature=sig,
        )
        world.record_proposal(proposal.to_dict())
        return proposal


# =====================================================================
# Third-party fetch
# =====================================================================

def fetch_rule_proposals(
    base_url: str,
) -> List[RuleProposal]:
    """Fetch a world's /log and extract rule proposals.
    Never raises — [] on any failure."""
    url = f"{base_url.rstrip('/')}/log"
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read().decode())
    except (urllib.error.URLError, urllib.error.HTTPError,
            json.JSONDecodeError, OSError):
        return []
    out: List[RuleProposal] = []
    for e in data.get("entries", []):
        if e.get("kind") == "rule_proposal":
            try:
                out.append(
                    RuleProposal.from_dict(e["data"]))
            except (KeyError, ValueError, TypeError):
                continue
    return out


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Three scenarios, one demo, one third-party check."""
    from multiverse_c1 import create_identity

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "observing_curator"
    path.mkdir(parents=True, exist_ok=True)

    # ---- Scenario A: empty canvas -----------------------------
    kp_a = KeyPair.generate()
    canvas_a = ObservingGrowingWorld(
        "world:canvas-a", "Empty Canvas", kp_a)
    curator_a = GrowingWorldCurator(
        canvas_a, kp_a, MockGrowthModel())
    proposal_a = curator_a.observe_and_propose_growth()

    # ---- Scenario B: size_limit refusals ----------------------
    kp_b = KeyPair.generate()
    canvas_b = ObservingGrowingWorld(
        "world:canvas-b", "Growing Canvas", kp_b)
    server_b = WorldProtocolServer(canvas_b, port=0)
    server_b.serve_in_thread()
    time.sleep(0.2)
    url_b = (
        f"http://127.0.0.1:"
        f"{server_b._httpd.server_address[1]}")

    alice = create_identity("Alice")
    bob = create_identity("Bob")
    carol = create_identity("Carol")
    for who in (alice, bob, carol):
        canvas_b.petition(Petition(
            petitioner_token=who.token,
            petitioner_name=who.name,
            passport_admissions=(),
            message=f"{who.name} enters"))

    def claim(who, x, y, w, h, purpose):
        return canvas_b.act(Act(
            actor_token=who.token, type="canvas.claim",
            payload={"x": x, "y": y, "width": w,
                     "height": h, "purpose": purpose}))

    claim(alice, 4, 0, 3, 3, "studio")
    claim(bob, 4, 3, 3, 3, "gallery")
    # Two too-large claims, both refused at size check
    claim(carol, 0, 0, 30, 30, "mural")
    claim(carol, 100, 100, 25, 25, "annex")

    try:
        curator_b = GrowingWorldCurator(
            canvas_b, kp_b, MockGrowthModel())
        ext_before = canvas_b.current_extent_bbox()
        obs_b = curator_b.observe_growth()
        proposal_b = curator_b.observe_and_propose_growth()
        ext_after = canvas_b.current_extent_bbox()
        # KEY INVARIANT: proposal does not change the world
        no_auto_apply = (ext_before == ext_after)

        # ---- Scenario C: overlap refusals --------------------
        kp_c = KeyPair.generate()
        canvas_c = ObservingGrowingWorld(
            "world:canvas-c", "Overlap Canvas", kp_c)
        for who in (alice, bob):
            canvas_c.petition(Petition(
                petitioner_token=who.token,
                petitioner_name=who.name,
                passport_admissions=(),
                message=f"{who.name} enters"))
        canvas_c.act(Act(
            actor_token=alice.token, type="canvas.claim",
            payload={"x": 4, "y": 0, "width": 3,
                     "height": 3, "purpose": "studio"}))
        for _ in range(3):
            canvas_c.act(Act(
                actor_token=bob.token, type="canvas.claim",
                payload={"x": 5, "y": 0, "width": 2,
                         "height": 2, "purpose": "gallery"}))
        curator_c = GrowingWorldCurator(
            canvas_c, kp_c, MockGrowthModel())
        obs_c = curator_c.observe_growth()
        proposal_c = curator_c.observe_and_propose_growth()

        # ---- Scenario D: third-party fetch + verify ----------
        fetched = fetch_rule_proposals(url_b)
        verified = [p for p in fetched
                    if verify_rule_proposal(
                        p, kp_b.public_key_hex())]
        # Also verify in-process via world.proposals()
        in_process = canvas_b.proposals()
        in_process_verified = [
            p for p in in_process
            if verify_rule_proposal(
                RuleProposal.from_dict(p),
                kp_b.public_key_hex())]

        # --- Print ----------------------------------------
        print("=" * 70)
        print("The Observing Curator — world watches, curator"
              " proposes")
        print("=" * 70)
        print()
        print("  Scenario A: empty canvas")
        print(f"    plot_count:   0")
        print(f"    proposal:     "
              f"{'None' if proposal_a is None else 'present'}")
        print()
        print("  Scenario B: size_limit refusals")
        print(f"    plot_count:       {obs_b.plot_count}")
        print(f"    refusals_by_kind: {obs_b.refusals_by_kind}")
        if proposal_b is not None:
            print(f"    proposal:         {proposal_b.title!r}")
            print(f"    rationale:        "
                  f"{proposal_b.rationale[:70]}...")
            print(f"    suggested_rule:   "
                  f"{proposal_b.suggested_rule}")
            print(f"    signed_by:        "
                  f"{proposal_b.signer_public_key[:16]}...")
        else:
            print(f"    proposal:         None")
        print(f"    extent unchanged: {no_auto_apply}")
        print()
        print("  Scenario C: overlap refusals")
        print(f"    refusals_by_kind: {obs_c.refusals_by_kind}")
        print(f"    proposal:         "
              f"{proposal_c.title if proposal_c else 'None'}")
        print()
        print("  Scenario D: third-party verification")
        print(f"    fetched from /log: {len(fetched)}")
        print(f"    verified:          {len(verified)}")
        print(f"    in-process verify: {len(in_process_verified)}")
        print()
        print("  What this demonstrates:")
        print("    - The curator observes the world's growth state,")
        print("      not just its protocol traffic.")
        print("    - Observations drive signed rule proposals —")
        print("      recommendations, never auto-applied (extent")
        print("      unchanged before and after).")
        print("    - Proposals are in the world's /log, discoverable")
        print("      and verifiable offline.")
        print("    - This is 'learn from outside' complementing")
        print("      C81's 'grow from inside'.")
        print()
        print("  Anchor (public domain, Emily Dickinson):")
        print("    'The Soul selects her own Society –'")
        print("    'Then – shuts the Door –'")

        audit = {
            "scenario_a": {
                "plot_count": 0,
                "proposal_generated": proposal_a is not None,
            },
            "scenario_b": {
                "plot_count": obs_b.plot_count,
                "refusals_by_kind": obs_b.refusals_by_kind,
                "proposal_generated": proposal_b is not None,
                "proposal_title": (
                    proposal_b.title if proposal_b else None),
                "no_auto_apply": no_auto_apply,
            },
            "scenario_c": {
                "refusals_by_kind": obs_c.refusals_by_kind,
                "proposal_generated": proposal_c is not None,
                "proposal_title": (
                    proposal_c.title if proposal_c else None),
            },
            "scenario_d": {
                "fetched_count": len(fetched),
                "verified_count": len(verified),
                "in_process_count":
                    len(in_process_verified),
            },
        }
        (path / "observing_curator_demo.json").write_text(
            json.dumps(audit, indent=2))
        print(f"\n  → {path}/observing_curator_demo.json")
        return audit
    finally:
        server_b.stop()
