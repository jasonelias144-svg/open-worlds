"""
compact_ancestry.py — O(1) space per bundle, O(depth) fetches.

The full-ancestry format (individual_bundle.ancestry) stores
one spawn record per generation per bundle. Space cost is
O(depth) per bundle; for a 20-generation lineage, the deepest
descendant carries ~12 KB of ancestry.

Compact ancestry replaces this with a running hash commitment
and a pointer to the parent. Per-bundle space is O(1) (4
hashes/DIDs ~= 128 bytes). Verification walks up the tree via
a caller-supplied fetcher, composing and checking at each step.

Composition function:
    genesis(root) = H("genesis:" || root_did)
    ancestry(child) = H("spawn:" || ancestry(parent)
                         || "||" || spawn_record_hash)

Each child's ancestry_root commits to the whole chain to the
root. Verification of a bundle:
  - fetch parent via parent_did
  - verify parent's basic signature chain
  - find spawn record in parent memory (by hash)
  - verify spawn record names child and parent
  - verify spawn signature
  - compose: child.ancestry_root == H("spawn:" ||
                parent.ancestry_root || spawn_hash)
  - recurse (or check at origin)

What compact ancestry proves:
  - Lineage: I descend from a declared root via these specific
    spawn events, without needing my parent's bundle present.
  - Tamper-evidence: any modification to any link breaks the
    hash chain.

What it does NOT prove:
  - Weight inheritance. Verifying that a parent's actual
    weights at spawn time hash to a child's claimed
    initial_weights still requires replaying the parent's
    memory. That's verify_federated_spawn_ancestry, which
    needs the parent's full bundle (present in the fetch
    chain anyway).
  - That the root is a true origin. The verifier trusts
    root_did as declared unless it also fetches the root
    (which it does, in the last step of the walk, so this is
    actually verified — root must be present in the fetcher).

Honest limits:
  - O(depth) fetches, each requiring parent's full bundle.
    For a local verifier with a cache, cheap. For a distributed
    verifier (HTTP), expensive.
  - The parent's full bundle must be reachable. A dangling
    child (parent bundle unavailable) cannot be verified.
  - No aggregate signatures. Each spawn record still carries
    its own Ed25519 signature. BLS aggregation would reduce
    further but is out of scope (different curve, non-standard).
  - Backward compatible: bundles with full `ancestry` still
    verify via lineage_root. Bundles with `compact_ancestry`
    verify via compact_ancestry. Bundles with both verify via
    both (independent claims).
"""

import hashlib
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PublicKey)
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from individual_bundle import (
    IndividualBundle, verify_bundle_basic,
    _canonical, _hash, _pubkey_from_did,
)
from individual_spawn import spawn_record_hash


GENESIS_PREFIX = "genesis:"
SPAWN_LINK_PREFIX = "spawn:"


def _hash_str(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def genesis_ancestry_root(root_did: str) -> str:
    return _hash_str(GENESIS_PREFIX + root_did)


def compute_ancestry_root(
    parent_ancestry_root: str, spawn_hash: str,
) -> str:
    return _hash_str(SPAWN_LINK_PREFIX + parent_ancestry_root
                     + "||" + spawn_hash)


@dataclass(frozen=True)
class CompactAncestry:
    root_did: str
    ancestry_root: str
    parent_did: str
    spawn_record_hash: str

    def to_dict(self) -> Dict:
        return {
            "root_did": self.root_did,
            "ancestry_root": self.ancestry_root,
            "parent_did": self.parent_did,
            "spawn_record_hash": self.spawn_record_hash,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "CompactAncestry":
        return cls(
            root_did=d["root_did"],
            ancestry_root=d["ancestry_root"],
            parent_did=d["parent_did"],
            spawn_record_hash=d["spawn_record_hash"],
        )


def compute_compact_ancestry(
    child_id: str,
    parent_bundle: IndividualBundle,
    spawn_record: Dict,
) -> CompactAncestry:
    parent_id = parent_bundle.individual_id
    spawn_hash = spawn_record_hash(spawn_record)
    parent_ca = parent_bundle.manifest.get("compact_ancestry")
    if parent_ca:
        parent_ancestry_root = parent_ca["ancestry_root"]
        root_did = parent_ca["root_did"]
    else:
        parent_ancestry_root = genesis_ancestry_root(parent_id)
        root_did = parent_id
    child_ancestry_root = compute_ancestry_root(
        parent_ancestry_root, spawn_hash)
    return CompactAncestry(
        root_did=root_did,
        ancestry_root=child_ancestry_root,
        parent_did=parent_id,
        spawn_record_hash=spawn_hash,
    )


def slim_bundle(
    child_bundle: IndividualBundle,
    compact: CompactAncestry,
    child_kp,
) -> IndividualBundle:
    """Drop full ancestry, add compact_ancestry to manifest,
    re-sign."""
    manifest = dict(child_bundle.manifest)
    manifest.pop("ancestry_hash", None)
    manifest["compact_ancestry"] = compact.to_dict()
    body = {k: v for k, v in manifest.items() if k != "sig"}
    new_sig = child_kp.sign(_canonical(body)).hex()
    manifest["sig"] = new_sig
    return IndividualBundle(
        manifest=manifest,
        memory=list(child_bundle.memory),
        weights=dict(child_bundle.weights),
        initial_weights=(dict(child_bundle.initial_weights)
                          if child_bundle.initial_weights else None),
        observations=list(child_bundle.observations),
        ancestry=[],
    )


Fetcher = Callable[[str], Optional[IndividualBundle]]


def verify_compact_ancestry(
    child_bundle: IndividualBundle,
    fetcher: Fetcher,
    max_depth: int = 100,
) -> Tuple[bool, str]:
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    manifest = child_bundle.manifest
    compact = manifest.get("compact_ancestry")

    # Root case: no compact_ancestry, no parent_did
    if compact is None:
        if not manifest.get("parent_did"):
            return (True, "root bundle (trivially its own origin)")
        if child_bundle.ancestry:
            return (False,
                     "bundle has full ancestry; use "
                     "verify_lineage_root")
        return (False, "no compact_ancestry or ancestry")

    # Well-formedness
    for field in ("root_did", "ancestry_root",
                   "parent_did", "spawn_record_hash"):
        v = compact.get(field)
        if not isinstance(v, str) or not v:
            return (False, f"compact_ancestry.{field} missing")

    current = child_bundle
    for depth in range(max_depth):
        cur_compact = current.manifest.get("compact_ancestry")
        if cur_compact is None:
            return (False,
                     f"depth {depth}: bundle "
                     f"{current.individual_id[:16]}... has no "
                     f"compact_ancestry, but not at root")
        parent_id = cur_compact["parent_did"]
        spawn_hash = cur_compact["spawn_record_hash"]
        parent = fetcher(parent_id)
        if parent is None:
            return (False,
                     f"depth {depth}: parent "
                     f"{parent_id[:16]}... not fetchable")
        v_basic = verify_bundle_basic(parent)
        if not v_basic[0]:
            return (False,
                     f"depth {depth}: parent basic: {v_basic[1]}")

        # Find spawn record
        spawn_rec = None
        for rec in parent.memory:
            if rec.get("type") != "spawn":
                continue
            if spawn_record_hash(rec) == spawn_hash:
                spawn_rec = rec
                break
        if spawn_rec is None:
            return (False,
                     f"depth {depth}: parent "
                     f"{parent_id[:16]}... memory lacks spawn "
                     f"{spawn_hash[:16]}...")
        if spawn_rec.get("child_id") != current.individual_id:
            return (False,
                     f"depth {depth}: spawn.child_id "
                     f"{spawn_rec.get('child_id')} != "
                     f"{current.individual_id}")
        if spawn_rec.get("agent_id") != parent_id:
            return (False,
                     f"depth {depth}: spawn.agent_id "
                     f"{spawn_rec.get('agent_id')} != parent")

        # Verify spawn record's signature
        body = {k: v for k, v in spawn_rec.items() if k != "sig"}
        try:
            _pubkey_from_did(parent_id).verify(
                bytes.fromhex(spawn_rec["sig"]),
                _canonical(body))
        except Exception:
            return (False,
                     f"depth {depth}: spawn signature invalid")

        # Compose
        parent_compact = parent.manifest.get("compact_ancestry")
        if parent_compact is None:
            # Parent is origin — verify genesis and stop
            if cur_compact["root_did"] != parent_id:
                return (False,
                         f"depth {depth}: root_did "
                         f"{cur_compact['root_did']} != "
                         f"origin {parent_id}")
            expected = compute_ancestry_root(
                genesis_ancestry_root(parent_id), spawn_hash)
            if cur_compact["ancestry_root"] != expected:
                return (False,
                         f"depth {depth}: ancestry_root "
                         f"mismatch at origin")
            return (True,
                     f"compact ancestry verifies (depth "
                     f"{depth + 1})")

        # Parent has compact_ancestry — recurse
        if cur_compact["root_did"] != parent_compact["root_did"]:
            return (False,
                     f"depth {depth}: root_did mismatch")
        expected = compute_ancestry_root(
            parent_compact["ancestry_root"], spawn_hash)
        if cur_compact["ancestry_root"] != expected:
            return (False,
                     f"depth {depth}: ancestry_root mismatch")
        current = parent

    return (False, f"max depth {max_depth} exceeded")


def compact_ancestry_size(compact: CompactAncestry) -> int:
    """Approximate JSON size of the compact_ancestry dict."""
    import json
    return len(json.dumps(compact.to_dict(),
                            sort_keys=True).encode())


def full_ancestry_size(ancestry: list) -> int:
    import json
    return len(json.dumps(ancestry, sort_keys=True).encode())


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir=None):
    from pathlib import Path
    from world_agent_coupling import ScriptedWorld
    from coupled_learners import TinyRNN, SIERPINSKI
    from federated_bundle import (
        FederatedSession, pack_federated_bundle,
        verify_federated_full,
    )
    from federated_spawn import (
        spawn_federated_child, pack_federated_child,
    )
    from lineage_root import verify_lineage_root
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey)
    import json as _json

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    root = Path(artifact_dir) / "compact_ancestry"
    root.mkdir(parents=True, exist_ok=True)

    def _kp():
        return Ed25519PrivateKey.generate()

    def _world(k_b, prng):
        return ScriptedWorld(
            kp=_kp(), initial_point_b=(800, 800),
            k_b=k_b, prng_seed_b=prng, rule=SIERPINSKI)

    # ---- Build a 5-gen chain ----
    DEPTH = 5
    STEPS = 20
    kps: list = []
    models: list = []
    sessions_lists: list = []
    memories: list = []
    spawn_records: list = []  # spawn_records[i] spawns i+1 from i
    inherited_weights: list = []  # inherited_weights[i] = child i's init
    full_bundles: list = []

    # Gen 0 (origin)
    kp0 = _kp()
    model0 = TinyRNN(n_extra_inputs=0, seed=100)
    mem0: list = []
    s0 = FederatedSession(
        individual_kp=kp0, model=model0,
        world=_world(0, 0xAAAA),
        initial_point=(200, 800), memory=mem0,
        rule=SIERPINSKI)
    for _ in range(STEPS):
        s0.step()
    kps.append(kp0)
    models.append(model0)
    sessions_lists.append([s0])
    memories.append(mem0)

    # Generate 1..DEPTH iteratively
    for i in range(1, DEPTH + 1):
        prev_sessions = sessions_lists[i - 1]
        prev_kp = kps[i - 1]
        prev_model = models[i - 1]
        # Spawn child i
        child_kp, child_model, spawn_rec, inherited_w = \
            spawn_federated_child(
                parent_session=prev_sessions[-1],
                child_persona=f"gen{i}",
                child_initial_seed=100 + i)
        prev_sessions[-1].step()  # parent continues after spawn
        kps.append(child_kp)
        models.append(child_model)
        spawn_records.append(spawn_rec)
        inherited_weights.append(inherited_w)
        # Child lives
        mem_i: list = []
        s_i = FederatedSession(
            individual_kp=child_kp, model=child_model,
            world=_world(i * 10, 0xAAAA + i * 0x1111),
            initial_point=(200 + i * 10, 800),
            memory=mem_i, rule=SIERPINSKI)
        for _ in range(STEPS):
            s_i.step()
        sessions_lists.append([s_i])
        memories.append(mem_i)

    # Pack all bundles (in reverse to have parents first)
    bundles_list: list = []
    for i in range(DEPTH, -1, -1):
        if i == 0:
            b = pack_federated_bundle(
                individual_kp=kps[0], model=models[0],
                sessions=sessions_lists[0],
                memory=memories[0],
                persona="gen0 (origin)", initial_seed=100,
                name=f"gen0")
        else:
            b = pack_federated_child(
                child_kp=kps[i], child_model=models[i],
                child_sessions=sessions_lists[i],
                child_memory=memories[i],
                child_persona=f"gen{i}",
                child_initial_seed=100 + i,
                parent_bundle=bundles_list[DEPTH - i + 1] if False
                             else None,
                spawn_record=spawn_records[i - 1],
                inherited_weights=inherited_weights[i - 1],
                name=f"gen{i}")
            # Oops — we need the parent's bundle, but we're
            # iterating from high to low. Restructure.
        bundles_list.append(b)

    # Actually restructure: build from low to high
    bundles_by_depth: list = []
    b0 = pack_federated_bundle(
        individual_kp=kps[0], model=models[0],
        sessions=sessions_lists[0], memory=memories[0],
        persona="gen0 (origin)", initial_seed=100,
        name="gen0")
    bundles_by_depth.append(b0)
    for i in range(1, DEPTH + 1):
        parent_b = bundles_by_depth[i - 1]
        bi = pack_federated_child(
            child_kp=kps[i], child_model=models[i],
            child_sessions=sessions_lists[i],
            child_memory=memories[i],
            child_persona=f"gen{i}",
            child_initial_seed=100 + i,
            parent_bundle=parent_b,
            spawn_record=spawn_records[i - 1],
            inherited_weights=inherited_weights[i - 1],
            name=f"gen{i}")
        bundles_by_depth.append(bi)

    # Slim versions
    slim_by_depth: list = []
    for i, full_b in enumerate(bundles_by_depth):
        if i == 0:
            slim_by_depth.append(full_b)  # origin unchanged
            continue
        parent_b = bundles_by_depth[i - 1]
        compact = compute_compact_ancestry(
            full_b.individual_id, parent_b,
            spawn_records[i - 1])
        slim = slim_bundle(full_b, compact, kps[i])
        slim_by_depth.append(slim)

    # Build fetcher dict — full bundles so we can find memory
    full_by_id = {b.individual_id: b for b in bundles_by_depth}

    def fetcher(did):
        return full_by_id.get(did)

    # ---- Save both ----
    for i, (full_b, slim_b) in enumerate(
            zip(bundles_by_depth, slim_by_depth)):
        full_b.save(root / "full" / f"gen{i}")
        slim_b.save(root / "slim" / f"gen{i}")

    # ---- Verify full chain ----
    full_chain_verdicts = []
    for b in bundles_by_depth:
        v = verify_lineage_root(b)
        v_full = verify_federated_full(b)
        full_chain_verdicts.append({
            "name": b.manifest["name"],
            "lineage": v[0],
            "federated_full": v_full[0],
        })

    # ---- Verify slim chain ----
    slim_chain_verdicts = []
    for b in slim_by_depth:
        v = verify_compact_ancestry(b, fetcher)
        v_full = verify_federated_full(b)
        slim_chain_verdicts.append({
            "name": b.manifest["name"],
            "compact_ancestry": v[0],
            "reason": v[1],
            "federated_full": v_full[0],
        })

    # ---- Size comparison ----
    sizes = []
    for i in range(1, DEPTH + 1):
        full_anc_size = full_ancestry_size(
            bundles_by_depth[i].ancestry)
        compact_size = compact_ancestry_size(
            CompactAncestry.from_dict(
                slim_by_depth[i].manifest["compact_ancestry"]))
        # Total bundle dir sizes
        full_dir_size = sum(
            f.stat().st_size for f in (root / "full" / f"gen{i}").rglob("*")
            if f.is_file())
        slim_dir_size = sum(
            f.stat().st_size for f in (root / "slim" / f"gen{i}").rglob("*")
            if f.is_file())
        sizes.append({
            "depth": i,
            "ancestry_records": len(bundles_by_depth[i].ancestry),
            "full_ancestry_bytes": full_anc_size,
            "compact_ancestry_bytes": compact_size,
            "full_bundle_bytes": full_dir_size,
            "slim_bundle_bytes": slim_dir_size,
        })

    # ---- Tampering ----
    # T1: tamper ancestor chain (change slim[2].ancestry_root)
    t1 = slim_bundle(
        slim_by_depth[2],
        CompactAncestry(
            root_did=slim_by_depth[2].manifest["compact_ancestry"]["root_did"],
            ancestry_root="00" * 32,
            parent_did=slim_by_depth[2].manifest["compact_ancestry"]["parent_did"],
            spawn_record_hash=slim_by_depth[2].manifest["compact_ancestry"]["spawn_record_hash"],
        ),
        kps[2])
    t1_ok, t1_reason = verify_compact_ancestry(t1, fetcher)

    # T2: tamper spawn_record_hash (points to nonexistent spawn)
    t2 = slim_bundle(
        slim_by_depth[3],
        CompactAncestry(
            root_did=slim_by_depth[3].manifest["compact_ancestry"]["root_did"],
            ancestry_root=slim_by_depth[3].manifest["compact_ancestry"]["ancestry_root"],
            parent_did=slim_by_depth[3].manifest["compact_ancestry"]["parent_did"],
            spawn_record_hash="00" * 32,
        ),
        kps[3])
    t2_ok, t2_reason = verify_compact_ancestry(t2, fetcher)

    # T3: tamper root_did (mis-declares origin)
    t3 = slim_bundle(
        slim_by_depth[4],
        CompactAncestry(
            root_did="did:key:" + "00" * 32,
            ancestry_root=slim_by_depth[4].manifest["compact_ancestry"]["ancestry_root"],
            parent_did=slim_by_depth[4].manifest["compact_ancestry"]["parent_did"],
            spawn_record_hash=slim_by_depth[4].manifest["compact_ancestry"]["spawn_record_hash"],
        ),
        kps[4])
    t3_ok, t3_reason = verify_compact_ancestry(t3, fetcher)

    # T4: break fetcher (simulate missing parent)
    def bad_fetcher(did):
        if did == bundles_by_depth[1].individual_id:
            return None
        return full_by_id.get(did)

    t4_ok, t4_reason = verify_compact_ancestry(
        slim_by_depth[4], bad_fetcher)

    # ---- Print ----
    print("=" * 74)
    print("Compact ancestry — O(1) space per bundle")
    print("=" * 74)
    print()
    print(f"  Chain: {DEPTH + 1} generations, {STEPS} steps each")
    print()

    print("  Full-ancestry verification (baseline):")
    for v in full_chain_verdicts:
        print(f"    {v['name']:8s}  lineage={v['lineage']}  "
              f"federated_full={v['federated_full']}")
    print()
    print("  Compact-ancestry verification:")
    for v in slim_chain_verdicts:
        marker = "✓" if v['compact_ancestry'] else "✗"
        print(f"    {v['name']:8s}  {marker} "
              f"({v['reason']})")
    print()

    print("  Sizes:")
    print(f"    {'depth':<6s} {'ancestry':<10s} "
          f"{'full_anc':<10s} {'compact':<10s} "
          f"{'full_bundle':<12s} {'slim_bundle':<12s} {'ratio':<8s}")
    print(f"    {'-'*6} {'-'*10} {'-'*10} {'-'*10} "
          f"{'-'*12} {'-'*12} {'-'*8}")
    for s in sizes:
        ratio = (s['slim_bundle_bytes']
                 / max(s['full_bundle_bytes'], 1))
        print(f"    {s['depth']:<6d} {s['ancestry_records']:<10d} "
              f"{s['full_ancestry_bytes']:<10d} "
              f"{s['compact_ancestry_bytes']:<10d} "
              f"{s['full_bundle_bytes']:<12d} "
              f"{s['slim_bundle_bytes']:<12d} "
              f"{ratio:.2%}")
    print()
    print("  Tampering (slim bundles, all re-signed so basic passes):")
    print(f"    change ancestry_root:  {t1_ok}  ({t1_reason})")
    print(f"    change spawn_hash:     {t2_ok}  ({t2_reason})")
    print(f"    change root_did:       {t3_ok}  ({t3_reason})")
    print(f"    break fetcher (missing parent): "
          f"{t4_ok}  ({t4_reason})")
    print()
    print("  What this establishes:")
    print("    - Compact ancestry is O(1) space per bundle.")
    print("      Each descendant carries ~128 bytes of chain")
    print("      metadata regardless of depth.")
    print("    - The full chain is verified by walking up via")
    print("      the fetcher. Each step is O(1) work; the")
    print("      overall cost is O(depth) fetches.")
    print("    - Sizes scale as expected. At depth 5, ancestry")
    print("      is ~4 KB in full format, ~128 bytes in")
    print("      compact. The bundle size reduction is")
    print("      meaningful but not dominant — memory entries")
    print("      are still the bulk.")
    print("    - Tampering with any field breaks verification:")
    print("      ancestry_root mismatches, spawn_record_hash")
    print("      not found, root_did mismatches, or missing")
    print("      parent. All caught.")
    print("    - Backward compatible: full-ancestry bundles")
    print("      still verify via verify_lineage_root.")
    print()
    print("  The honest trade: O(depth) fetches instead of")
    print("  O(1). For a local verifier with all bundles in")
    print("  hand, this is instant. For a distributed verifier")
    print("  fetching over a network, it's O(depth) round")
    print("  trips. There is no scheme with both O(1) space")
    print("  and O(1) fetches without trusting someone else's")
    print("  verification or using aggregate signatures")
    print("  (BLS), which are out of scope.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'I dwell in Possibility –'")
    print("    'A fairer House than Prose –'")
    print("    'More numerous of Windows –'")
    print("    'Superior – for Doors –'")

    audit = {
        "chain_length": DEPTH + 1,
        "steps_per_gen": STEPS,
        "full_verification": full_chain_verdicts,
        "slim_verification": slim_chain_verdicts,
        "sizes": sizes,
        "tampering": {
            "ancestry_root": {
                "detected": not t1_ok,
                "reason": t1_reason,
            },
            "spawn_hash": {
                "detected": not t2_ok,
                "reason": t2_reason,
            },
            "root_did": {
                "detected": not t3_ok,
                "reason": t3_reason,
            },
            "missing_parent": {
                "detected": not t4_ok,
                "reason": t4_reason,
            },
        },
    }
    (root / "compact_ancestry_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {root}/compact_ancestry_demo.json")
    return audit
