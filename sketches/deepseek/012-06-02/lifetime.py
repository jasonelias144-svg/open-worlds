"""
lifetime.py — verify an individual's complete verifiable history.

Given a set of IndividualBundle instances indexed by DID,
verify_individual_lifetime(bundles, individual_id) walks every
bundle carrying that DID, verifies each at its appropriate
tier, verifies every resume edge, and produces a report.

Bundles are grouped by individual_id:
  - Same individual_id → the individual's own line
    (origin → resume → resume → ...)
  - Different individual_id with forked_from == X → a branch
    of X (verified if include_branches=True)

The verifier detects:
  - Per-bundle tier failures (fork/delegated/compacted/federated)
  - Resume edge breaks (via verify_resumed_from or
    verify_delegated_continuity)
  - Gaps (resumed_from points to a memory_root not in the set)
  - Cycles (malformed chains that loop)
  - Multiple candidate origins (ambiguous start)

Composition: pure orchestrator. Delegates every cryptographic
check to the existing tier verifiers. No new record types, no
new primitives.

Honest limits:
  - Compacting an intermediate bundle invalidates any resume
    edges to its pre-compaction state. The verifier catches
    this as a gap, not as a compaction-specific error.
  - No cross-individual cycle detection (only within one
    individual's chain).
  - include_branches verifies forks against their parent, but
    does not verify the fork's own lifetime — that's a
    separate call with individual_id = fork_id.
  - Delegated forks (fork_authorized_by_delegate) not
    supported — forked bundles don't carry resumed_by.
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from individual_bundle import (
    IndividualBundle, verify_bundle_basic, _hash,
)
from federated_bundle import verify_federated_full
from compact_memory import verify_compacted_full
from delegated_resumption import verify_delegated_full
from forking import verify_forked_full, verify_fork_continuity
from resumable import verify_resumed_from


# =====================================================================
# Report
# =====================================================================

@dataclass
class LifetimeReport:
    individual_id: str
    ok: bool = False
    origin_id: Optional[str] = None
    bundles: List[Dict] = field(default_factory=list)
    edges: List[Dict] = field(default_factory=list)
    branches: List[Dict] = field(default_factory=list)
    timeline: List[Dict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def format(self) -> str:
        lines = [
            f"Lifetime report — {self.individual_id[:32]}...",
            f"  ok: {self.ok}",
        ]
        if self.origin_id:
            lines.append(
                f"  origin: {self.origin_id[:32]}...")
        lines.append(f"  bundles: {len(self.bundles)}")
        for b in self.bundles:
            marker = "✓" if b["ok"] else "✗"
            lines.append(
                f"    {marker} {b['id'][:24]}... "
                f"[{b['tier']}] {b.get('reason', '')}")
        if self.edges:
            lines.append(f"  edges: {len(self.edges)}")
            for e in self.edges:
                marker = "✓" if e["ok"] else "✗"
                marker_kind = (
                    "delegated" if e.get("delegated")
                    else "self")
                lines.append(
                    f"    {marker} {e['from'][:16]}... → "
                    f"{e['to'][:16]}... [{marker_kind}] "
                    f"{e.get('reason', '')}")
        if self.branches:
            lines.append(f"  branches: {len(self.branches)}")
            for br in self.branches:
                marker = "·" if br.get("ok") else "✗"
                lines.append(
                    f"    {marker} {br['kind']} "
                    f"{br['id'][:24]}... {br.get('reason', '')}")
        if self.timeline:
            lines.append("  timeline:")
            for ev in self.timeline:
                lines.append("    " + _format_event(ev))
        if self.errors:
            lines.append(f"  errors: {len(self.errors)}")
            for e in self.errors:
                lines.append(f"    ✗ {e}")
        if self.warnings:
            lines.append(f"  warnings: {len(self.warnings)}")
            for w in self.warnings:
                lines.append(f"    · {w}")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "individual_id": self.individual_id,
            "ok": self.ok,
            "origin_id": self.origin_id,
            "bundles": self.bundles,
            "edges": self.edges,
            "branches": self.branches,
            "timeline": self.timeline,
            "errors": self.errors,
            "warnings": self.warnings,
        }


def _format_event(ev: Dict) -> str:
    kind = ev.get("event")
    if kind == "origin":
        return (f"[{ev['index']}] origin: {ev['id'][:24]}... "
                f"({ev['memory_entries']} entries, "
                f"{ev['worlds']} worlds)")
    if kind == "resume":
        marker = "delegated" if ev.get("delegated_by") else "self"
        return (f"[{ev['index']}] resume ({marker}): "
                f"{ev['from'][:16]}... → {ev['to'][:16]}... "
                f"(K={ev['k']})")
    if kind == "compacted":
        return (f"[{ev['index']}] compacted: {ev['id'][:24]}... "
                f"(at K={ev['at_k']})")
    return f"[{ev.get('index', '?')}] {kind}"


# =====================================================================
# Tier dispatch
# =====================================================================

def _verify_bundle_at_tier(bundle: IndividualBundle) -> Dict:
    if bundle.manifest.get("forked_from"):
        ok, reason = verify_forked_full(bundle)
        return {"ok": ok, "tier": "forked", "reason": reason}
    if bundle.manifest.get("resumed_by"):
        ok, reason = verify_delegated_full(bundle)
        return {"ok": ok, "tier": "delegated", "reason": reason}
    if bundle.manifest.get("compacted_at"):
        ok, reason = verify_compacted_full(bundle)
        return {"ok": ok, "tier": "compacted", "reason": reason}
    ok, reason = verify_federated_full(bundle)
    return {"ok": ok, "tier": "federated", "reason": reason}


# =====================================================================
# Lifetime verification
# =====================================================================

def verify_individual_lifetime(
    bundles: Dict[str, IndividualBundle],
    individual_id: str,
    include_branches: bool = False,
) -> LifetimeReport:
    report = LifetimeReport(individual_id=individual_id)

    if not HAS_CRYPTO:
        report.errors.append("cryptography not installed")
        return report
    if not isinstance(bundles, dict):
        report.errors.append("bundles must be a Dict")
        return report

    # 1. Filter to this individual's own line
    own = {did: b for did, b in bundles.items()
           if b.manifest.get("individual_id") == individual_id}
    if not own:
        report.errors.append(
            f"no bundles found for {individual_id[:24]}...")
        return report

    # 2. Index by memory_root
    by_root: Dict[str, str] = {}
    for did, b in own.items():
        root = b.manifest.get("memory_root")
        if root in by_root:
            report.warnings.append(
                f"duplicate memory_root {root[:16]}... "
                f"({did[:16]}... and {by_root[root][:16]}...)")
        else:
            by_root[root] = did

    # 3. Verify each bundle at its tier
    for did, b in own.items():
        r = _verify_bundle_at_tier(b)
        report.bundles.append({
            "id": did,
            "tier": r["tier"],
            "ok": r["ok"],
            "reason": r["reason"],
            "memory_entries": b.manifest["memory_entries"],
            "worlds": len(b.manifest.get("world_contexts", [])),
            "resumed_from": b.manifest.get("resumed_from"),
            "forked_from": b.manifest.get("forked_from"),
            "resumed_by": b.manifest.get("resumed_by"),
            "compacted_at": b.manifest.get("compacted_at"),
        })
        if not r["ok"]:
            report.errors.append(
                f"{did[:24]}...: {r['tier']} verification "
                f"failed: {r['reason']}")

    # 4. Origin
    strict_origins = [
        did for did, b in own.items()
        if not b.manifest.get("resumed_from")
        and not b.manifest.get("forked_from")]
    if not strict_origins:
        strict_origins = [
            did for did, b in own.items()
            if not b.manifest.get("resumed_from")]
    if not strict_origins:
        report.errors.append("no origin bundle found")
    elif len(strict_origins) > 1:
        report.warnings.append(
            f"{len(strict_origins)} candidate origins — "
            f"individual has multiple chains")
        report.origin_id = strict_origins[0]
    else:
        report.origin_id = strict_origins[0]

    # 5. Resume edges
    for did, b in own.items():
        resumed_from = b.manifest.get("resumed_from")
        if not resumed_from:
            continue
        parent_did = by_root.get(resumed_from)
        if not parent_did:
            report.errors.append(
                f"{did[:24]}...: resumed_from "
                f"{resumed_from[:16]}... not in bundle set "
                f"(missing intermediate or compacted parent)")
            continue
        parent = own[parent_did]
        if b.manifest.get("resumed_by"):
            from delegated_resumption import (
                verify_delegated_continuity,
            )
            ok, reason = verify_delegated_continuity(b, parent)
            delegated = True
        else:
            ok, reason = verify_resumed_from(b, parent)
            delegated = False
        report.edges.append({
            "from": parent_did,
            "to": did,
            "ok": ok,
            "reason": reason,
            "delegated": delegated,
        })
        if not ok:
            report.errors.append(
                f"resume edge {parent_did[:16]}... → "
                f"{did[:16]}...: {reason}")

    # 6. Cycle detection
    for did in own:
        visited = set()
        current: Optional[str] = did
        while current:
            if current in visited:
                report.errors.append(
                    f"cycle detected: {did[:16]}... "
                    f"revisits {current[:16]}...")
                break
            visited.add(current)
            b = own[current]
            resumed_from = b.manifest.get("resumed_from")
            if not resumed_from:
                break
            current = by_root.get(resumed_from)

    # 7. Branches (forks of this individual)
    if include_branches:
        for did, b in bundles.items():
            if b.manifest.get("forked_from") == individual_id:
                parent_root = b.manifest.get(
                    "fork_at_memory_root")
                parent_did = by_root.get(parent_root)
                if parent_did:
                    ok, reason = verify_fork_continuity(
                        b, own[parent_did])
                else:
                    ok = False
                    reason = (
                        "fork parent not in bundle set")
                report.branches.append({
                    "kind": "fork",
                    "id": did,
                    "ok": ok,
                    "reason": reason,
                })

    # 8. Timeline
    report.timeline = _build_timeline(
        own, by_root, report.origin_id)

    # 9. Overall verdict
    report.ok = (
        not report.errors
        and all(b["ok"] for b in report.bundles)
    )
    return report


def _build_timeline(
    own: Dict[str, IndividualBundle],
    by_root: Dict[str, str],
    origin_id: Optional[str],
) -> List[Dict]:
    if not origin_id:
        return []
    chain: List[str] = [origin_id]
    current = origin_id
    seen = {origin_id}
    while True:
        current_root = own[current].manifest.get("memory_root")
        next_did = None
        for did, b in own.items():
            if did in seen:
                continue
            if b.manifest.get("resumed_from") == current_root:
                next_did = did
                break
        if not next_did:
            break
        chain.append(next_did)
        seen.add(next_did)
        current = next_did

    timeline: List[Dict] = []
    for i, did in enumerate(chain):
        b = own[did]
        if i == 0:
            timeline.append({
                "event": "origin",
                "index": i,
                "id": did,
                "memory_entries":
                    b.manifest["memory_entries"],
                "worlds": len(
                    b.manifest.get("world_contexts", [])),
            })
        else:
            prev_did = chain[i - 1]
            prev = own[prev_did]
            timeline.append({
                "event": "resume",
                "index": i,
                "from": prev_did,
                "to": did,
                "k": prev.manifest["memory_entries"],
                "delegated_by": b.manifest.get("resumed_by"),
            })
        if b.manifest.get("compacted_at"):
            timeline.append({
                "event": "compacted",
                "index": i,
                "id": did,
                "at_k": b.manifest["compacted_at"],
            })
    return timeline


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir=None):
    from pathlib import Path
    from world_agent_coupling import ScriptedWorld
    from coupled_learners import TinyRNN, SIERPINSKI
    from federated_bundle import (
        FederatedSession, pack_federated_bundle,
    )
    from resumable import (
        resume_from_bundle, pack_resumed_bundle,
    )
    from delegated_resumption import (
        sign_resumption_delegation, resume_with_delegation,
        pack_delegated_bundle,
    )
    from forking import (
        fork_from_bundle, sign_fork_record_with_parent,
        pack_fork_bundle,
    )
    from federated_spawn import _replay_federated_to_index
    from individual_bundle import (
        serialize_weights, _merkle_root, _hash,
    )
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey)
    import json as _json

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    root = Path(artifact_dir) / "lifetime"
    root.mkdir(parents=True, exist_ok=True)

    def _kp():
        return Ed25519PrivateKey.generate()

    def _world(k_b, prng):
        return ScriptedWorld(
            kp=_kp(), initial_point_b=(800, 800),
            k_b=k_b, prng_seed_b=prng, rule=SIERPINSKI)

    def _entry_hash(rec):
        return _hash({k: v for k, v in rec.items() if k != "sig"})

    # ---- Build origin A (2 worlds) ----
    a_kp = _kp()
    a_id = __import__("individual_bundle")._did_from_kp(a_kp)
    a_model = TinyRNN(n_extra_inputs=0, seed=42)
    a_memory: List[Dict] = []
    a_sessions = []
    for i, (n, pt, k, prng) in enumerate([
        (20, (200, 800), 0, 0xAAAA),
        (20, (250, 750), 50, 0xBBBB),
    ]):
        s = FederatedSession(
            individual_kp=a_kp, model=a_model,
            world=_world(k, prng),
            initial_point=pt, memory=a_memory,
            rule=SIERPINSKI)
        for _ in range(n):
            s.step()
        a_sessions.append(s)
    A = pack_federated_bundle(
        individual_kp=a_kp, model=a_model,
        sessions=a_sessions, memory=a_memory,
        persona="origin", initial_seed=42, name="A")

    # ---- Fork F from A at end of A's memory ----
    K_fork = A.manifest["memory_entries"]
    f_kp = _kp()
    f_id = __import__("individual_bundle")._did_from_kp(f_kp)
    a_model_at_k, _ = _replay_federated_to_index(A, K_fork)
    w_at_k = serialize_weights(a_model_at_k)
    prefix_root = _merkle_root(
        [_entry_hash(r) for r in A.memory[:K_fork]])
    fork_record = sign_fork_record_with_parent(
        parent_kp=a_kp, parent=A, fork_id=f_id,
        fork_at_entry=K_fork,
        fork_at_memory_root=prefix_root,
        fork_weights_hash=__import__(
            "forking")._weights_hash(w_at_k),
    )
    f_sessions, _, _, reason = fork_from_bundle(
        parent=A, fork_kp=f_kp, fork_at_entry=K_fork,
        world_specs=[(15, (300, 700), 75, 0xCCCC)],
    )
    assert f_sessions is not None, reason
    F = pack_fork_bundle(
        sessions=f_sessions,
        memory=f_sessions[-1].memory,
        model=f_sessions[-1].model,
        parent_bundle=A, fork_kp=f_kp,
        fork_record=fork_record,
        persona="fork", name="F")

    # ---- Self-resume B from A ----
    b_sessions, reason = resume_from_bundle(
        A, a_kp, [(15, (400, 600), 25, 0xDDDD)])
    assert b_sessions is not None, reason
    B = pack_resumed_bundle(
        sessions=b_sessions, memory=b_sessions[-1].memory,
        model=b_sessions[-1].model,
        parent_bundle=A, individual_kp=a_kp,
        persona="resumed", name="B")

    # ---- Delegated resume C from B ----
    curator_kp = _kp()
    curator_id = __import__(
        "individual_bundle")._did_from_kp(curator_kp)
    delegation = sign_resumption_delegation(
        individual_kp=a_kp, delegate_did=curator_id,
        resume_at_entry=B.manifest["memory_entries"],
        resume_at_memory_root=B.manifest["memory_root"],
        max_resumed_steps=20)
    c_sessions, reason = resume_with_delegation(
        B, curator_kp, delegation,
        [(10, (450, 550), 50, 0xEEEE)])
    assert c_sessions is not None, reason
    C = pack_delegated_bundle(
        sessions=c_sessions, memory=c_sessions[-1].memory,
        model=c_sessions[-1].model,
        parent_bundle=B, delegation=delegation,
        delegate_kp=curator_kp,
        persona="delegated resume", name="C")

    # ---- Bundle set ----
    bundles = {
        A.individual_id: A,
        B.individual_id: B,
        C.individual_id: C,
        F.individual_id: F,
    }

    # ---- Verify lifetime of A ----
    report_a = verify_individual_lifetime(
        bundles, a_id, include_branches=True)
    # ---- Verify lifetime of F ----
    report_f = verify_individual_lifetime(
        bundles, f_id, include_branches=False)

    # ---- Tampering: break a resume edge ----
    tampered_bundles = dict(bundles)
    B2 = IndividualBundle(
        manifest=dict(B.manifest),
        memory=list(B.memory),
        weights=dict(B.weights),
        initial_weights=B.initial_weights,
        observations=list(B.observations),
        ancestry=list(B.ancestry),
        checkpoint_weights=B.checkpoint_weights,
    )
    B2.manifest = dict(B2.manifest)
    B2.manifest["resumed_from"] = "00" * 32
    body = {k: v for k, v in B2.manifest.items()
             if k != "sig"}
    B2.manifest["sig"] = a_kp.sign(
        __import__("individual_bundle")._canonical(
            body)).hex()
    tampered_bundles[a_id + "-tampered"] = B2
    report_tampered_edge = verify_individual_lifetime(
        tampered_bundles, a_id, include_branches=False)

    # ---- Tampering: remove B (create a gap) ----
    missing_bundles = {k: v for k, v in bundles.items()
                        if k != B.individual_id}
    report_missing = verify_individual_lifetime(
        missing_bundles, a_id, include_branches=False)

    # ---- Print ----
    print("=" * 74)
    print("Lifetime — one individual, verified end to end")
    print("=" * 74)
    print()
    print(f"  Individual A: {a_id[:32]}...")
    print(f"  Bundles in set: {len(bundles)}")
    print(f"    A (origin)")
    print(f"    B (self-resumed from A)")
    print(f"    C (delegated resume from B)")
    print(f"    F (fork of A)")
    print()
    print("  A's lifetime report:")
    print(report_a.format())
    print()
    print("  F's lifetime report (the fork, independent):")
    print(report_f.format())
    print()
    print("  Tampering — broken resume edge (B.resumed_from → 00…):")
    print(f"    ok: {report_tampered_edge.ok}")
    print(f"    errors: {len(report_tampered_edge.errors)}")
    for e in report_tampered_edge.errors:
        print(f"      ✗ {e}")
    print()
    print("  Tampering — missing B (gap in the chain):")
    print(f"    ok: {report_missing.ok}")
    print(f"    errors: {len(report_missing.errors)}")
    for e in report_missing.errors:
        print(f"      ✗ {e}")
    print()
    print("  What this establishes:")
    print("    - A lifetime is a graph, and the verifier walks it.")
    print("      Bundles of one individual are collected by DID,")
    print("      ordered by resume edges, and each verified at")
    print("      its appropriate tier.")
    print("    - The four operations of the individual layer —")
    print("      resume, delegated resume, fork, spawn — produce")
    print("      different tiers. The lifetime verifier dispatches")
    print("      to the right check per bundle.")
    print("    - Every edge is verified, not just recorded. A")
    print("      broken resume edge, a missing intermediate, a")
    print("      cycle, or a tampered memory — all caught.")
    print("    - Branches are reported separately. F is a fork of")
    print("      A; F's own lifetime verifies independently (it's")
    print("      its own origin). A's lifetime reports F as a")
    print("      branch.")
    print("    - This is the arc's compositional endpoint at the")
    print("      individual layer: one function verifies an")
    print("      individual's complete verifiable history, and")
    print("      every primitive built in the last eight cycles")
    print("      contributes to the answer.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'Forever – is composed of Nows –'")
    print("    'Tis not a different time –'")
    print("    'Except Infinity – is composed –'")
    print("    'Of Nows – and Nowheres – now –'")

    audit = {
        "individual_id": a_id,
        "bundle_set": {
            "A": a_id, "B": B.individual_id,
            "C": C.individual_id, "F": F.individual_id,
        },
        "lifetime_a": report_a.to_dict(),
        "lifetime_f": report_f.to_dict(),
        "tampering": {
            "broken_edge_ok": report_tampered_edge.ok,
            "broken_edge_errors":
                report_tampered_edge.errors,
            "missing_b_ok": report_missing.ok,
            "missing_b_errors": report_missing.errors,
        },
    }
    (root / "lifetime_demo.json").write_text(
        _json.dumps(audit, indent=2, default=str))
    print(f"\n  → {root}/lifetime_demo.json")
    return audit
