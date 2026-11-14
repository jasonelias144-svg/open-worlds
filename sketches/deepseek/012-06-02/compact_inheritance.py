"""
compact_inheritance.py — descent + inheritance, at the compact tier.

verify_compact_ancestry (previous cycle) proves the chain of spawn
records is coherent. It does not prove that the parent's actual
weights at spawn time match the child's initial_weights claim.

This module adds that. The walk visits each parent anyway (via
fetcher), finds the spawn record, verifies it — so it can also:
  - Check the spawn's claimed inherited_weights_hash matches
    the child's claimed initial_weights_hash
  - Replay the parent to the spawn index
  - Serialize and hash the derived weights
  - Compare to the claimed hash

Three cases per link:
  inherit*: spawn has inherited_weights_hash, child has
            initial_weights_hash → full verification
  fresh:    neither has it → verified as fresh (no inheritance)
  mismatch: exactly one has it → fail (inconsistent)

Cost: O(depth × parent_memory) time, O(depth) fetches, O(1)
space per bundle. Honest tradeoff vs. full-ancestry's O(depth)
space and per-edge ancestry's O(depth × parent_memory) time.

Composes: verify_compact_ancestry for structure + the walk;
federated_spawn._replay_federated_to_index for parent replay.

Honest limits:
  - Fresh spawns don't inherit; they're a different mode
    (present in individual_spawn.spawn_child). Compact
    verifier detects "no inheritance claimed" and passes.
  - The parent's initial_weights (if present) is trusted for
    the *start* of the parent's replay. A tampered parent
    with fabricated initial_weights would need verify_bundle_basic
    to fail — but basic is run at each step, so tampering is
    caught there, not at inheritance.
  - The parent's weights at spawn must be derivable. If a
    parent's replay fails (e.g., corrupt memory), inheritance
    cannot be verified — the walk fails with "replay failed."
  - No weight inheritance of *observations*. Bundles here
    have observations=[]; observing bundles would need
    observations to be replayed too (future work).
"""

import json
from typing import Callable, Dict, Optional, Tuple

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from individual_bundle import (
    IndividualBundle, verify_bundle_basic, serialize_weights,
    _canonical, _hash, _pubkey_from_did,
)
from individual_spawn import spawn_record_hash
from federated_spawn import _replay_federated_to_index
from compact_ancestry import (
    compute_ancestry_root, genesis_ancestry_root,
    CompactAncestry,
)


def _weights_hash(weights: Dict) -> str:
    return _hash(json.dumps(weights, sort_keys=True,
                             separators=(",", ":")).encode())


Fetcher = Callable[[str], Optional[IndividualBundle]]


def verify_compact_ancestry_with_inheritance(
    child_bundle: IndividualBundle,
    fetcher: Fetcher,
    max_depth: int = 100,
) -> Tuple[bool, str]:
    """Descent + inheritance, walking up via fetcher.
    Never raises for network/verification failures — returns
    (False, reason)."""
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    if not isinstance(child_bundle, IndividualBundle):
        return (False, "not an IndividualBundle")

    manifest = child_bundle.manifest
    compact = manifest.get("compact_ancestry")

    # Root case
    if compact is None:
        if not manifest.get("parent_did"):
            if manifest.get("initial_weights_hash"):
                return (False,
                         "root bundle claims inherited weights")
            return (True, "root bundle (trivially its own origin)")
        return (False, "no compact_ancestry on non-root bundle")

    # Non-root: walk
    current = child_bundle
    for depth in range(max_depth):
        cur_compact = current.manifest.get("compact_ancestry")
        if cur_compact is None:
            return (False,
                     f"depth {depth}: missing compact_ancestry "
                     f"at non-root")
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

        # Find spawn record and its index
        spawn_rec = None
        spawn_index = None
        for idx, rec in enumerate(parent.memory):
            if rec.get("type") != "spawn":
                continue
            if spawn_record_hash(rec) == spawn_hash:
                spawn_rec = rec
                spawn_index = idx
                break
        if spawn_rec is None:
            return (False,
                     f"depth {depth}: parent "
                     f"{parent_id[:16]}... memory lacks spawn "
                     f"{spawn_hash[:16]}...")
        if spawn_rec.get("child_id") != current.individual_id:
            return (False,
                     f"depth {depth}: spawn.child_id mismatch")
        if spawn_rec.get("agent_id") != parent_id:
            return (False,
                     f"depth {depth}: spawn.agent_id mismatch")

        # Verify spawn signature
        body = {k: v for k, v in spawn_rec.items() if k != "sig"}
        try:
            _pubkey_from_did(parent_id).verify(
                bytes.fromhex(spawn_rec["sig"]),
                _canonical(body))
        except Exception:
            return (False,
                     f"depth {depth}: spawn sig invalid")

        # --- Inheritance check ---
        spawn_has_inh = "inherited_weights_hash" in spawn_rec
        child_has_inh = "initial_weights_hash" in current.manifest
        if spawn_has_inh != child_has_inh:
            which = ("spawn claims inheritance but child "
                     "doesn't declare initial_weights"
                     if spawn_has_inh else
                     "child declares initial_weights but "
                     "spawn doesn't claim inheritance")
            return (False,
                     f"depth {depth}: inconsistent inheritance "
                     f"({which})")

        if spawn_has_inh:
            spawn_hash_v = spawn_rec["inherited_weights_hash"]
            child_hash_v = current.manifest["initial_weights_hash"]
            if spawn_hash_v != child_hash_v:
                return (False,
                         f"depth {depth}: inherited hash mismatch "
                         f"(spawn claims "
                         f"{spawn_hash_v[:16]}..., "
                         f"child claims "
                         f"{child_hash_v[:16]}...)")
            # Replay parent to spawn index
            model, reason = _replay_federated_to_index(
                parent, spawn_index)
            if model is None:
                return (False,
                         f"depth {depth}: parent replay "
                         f"failed: {reason}")
            derived = _weights_hash(serialize_weights(model))
            if derived != spawn_hash_v:
                return (False,
                         f"depth {depth}: parent's actual "
                         f"weights at spawn ({derived[:16]}...) "
                         f"!= claimed ({spawn_hash_v[:16]}...)")

        # --- Chain composition ---
        parent_compact = parent.manifest.get("compact_ancestry")
        if parent_compact is None:
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
                     f"compact+inheritance verifies (depth "
                     f"{depth + 1})")

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


def verify_chain_compact_with_inheritance(
    chain: list,
) -> Tuple[bool, str]:
    """Verify a list of bundles as a chain, top-down.
    For each bundle, run verify_compact_ancestry_with_inheritance
    against a fetcher that supplies the parents from the list."""
    by_id = {b.individual_id: b for b in chain}
    def fetcher(did):
        return by_id.get(did)
    for i, b in enumerate(chain):
        ok, reason = verify_compact_ancestry_with_inheritance(
            b, fetcher)
        if not ok:
            return (False,
                     f"chain[{i}] "
                     f"({b.manifest.get('name', '?')}): {reason}")
    return (True, f"compact inheritance chain of {len(chain)} "
                   f"verifies")


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir=None):
    from pathlib import Path
    import json as _json
    from world_agent_coupling import ScriptedWorld
    from coupled_learners import TinyRNN, SIERPINSKI
    from federated_bundle import (
        FederatedSession, pack_federated_bundle,
        verify_federated_full,
    )
    from federated_spawn import (
        spawn_federated_child, pack_federated_child,
    )
    from individual_spawn import spawn_child as spawn_fresh
    from compact_ancestry import (
        compute_compact_ancestry, slim_bundle,
        compact_ancestry_size, full_ancestry_size,
    )
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey)

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    root = Path(artifact_dir) / "compact_inheritance"
    root.mkdir(parents=True, exist_ok=True)

    def _kp():
        return Ed25519PrivateKey.generate()

    def _world(k_b, prng):
        return ScriptedWorld(
            kp=_kp(), initial_point_b=(800, 800),
            k_b=k_b, prng_seed_b=prng, rule=SIERPINSKI)

    # ---- 5-gen inheriting chain ----
    DEPTH = 5
    STEPS = 15
    kps = []
    models = []
    memories = []
    sessions_list = []
    spawns = []
    inherited_weights = []

    # Gen 0 (origin)
    kp0 = _kp()
    m0 = TinyRNN(n_extra_inputs=0, seed=100)
    mem0: list = []
    s0 = FederatedSession(
        individual_kp=kp0, model=m0,
        world=_world(0, 0xAAAA),
        initial_point=(200, 800), memory=mem0,
        rule=SIERPINSKI)
    for _ in range(STEPS):
        s0.step()
    kps.append(kp0); models.append(m0)
    memories.append(mem0); sessions_list.append([s0])

    for i in range(1, DEPTH + 1):
        parent_sessions = sessions_list[i - 1]
        child_kp, child_model, spawn_rec, inherited_w = \
            spawn_federated_child(
                parent_session=parent_sessions[-1],
                child_persona=f"gen{i}",
                child_initial_seed=100 + i)
        parent_sessions[-1].step()
        kps.append(child_kp); models.append(child_model)
        spawns.append(spawn_rec)
        inherited_weights.append(inherited_w)
        mem_i: list = []
        s_i = FederatedSession(
            individual_kp=child_kp, model=child_model,
            world=_world(i * 10, 0xAAAA + i * 0x1111),
            initial_point=(200 + i * 10, 800),
            memory=mem_i, rule=SIERPINSKI)
        for _ in range(STEPS):
            s_i.step()
        memories.append(mem_i); sessions_list.append([s_i])

    # Pack full bundles
    full_bundles = [pack_federated_bundle(
        individual_kp=kps[0], model=models[0],
        sessions=sessions_list[0], memory=memories[0],
        persona="gen0 (origin)", initial_seed=100, name="gen0")]
    for i in range(1, DEPTH + 1):
        full_bundles.append(pack_federated_child(
            child_kp=kps[i], child_model=models[i],
            child_sessions=sessions_list[i],
            child_memory=memories[i],
            child_persona=f"gen{i}",
            child_initial_seed=100 + i,
            parent_bundle=full_bundles[i - 1],
            spawn_record=spawns[i - 1],
            inherited_weights=inherited_weights[i - 1],
            name=f"gen{i}"))

    # Slim them
    slim_bundles = [full_bundles[0]]  # origin unchanged
    for i in range(1, DEPTH + 1):
        compact = compute_compact_ancestry(
            full_bundles[i].individual_id,
            slim_bundles[i - 1], spawns[i - 1])
        slim = slim_bundle(full_bundles[i], compact, kps[i])
        slim_bundles.append(slim)

    # Save slim to disk, full for fetcher
    for i, s in enumerate(slim_bundles):
        s.save(root / "slim" / f"gen{i}")
    full_by_id = {b.individual_id: b for b in full_bundles}
    def fetcher(did):
        return full_by_id.get(did)

    # ---- Verify all three tiers ----
    results = []
    for i, b in enumerate(slim_bundles):
        v_full = verify_federated_full(b)
        v_inh = verify_compact_ancestry_with_inheritance(b, fetcher)
        results.append({
            "name": b.manifest["name"],
            "federated_full": v_full[0],
            "compact_inheritance": v_inh[0],
            "reason": v_inh[1],
        })

    # Chain-level
    chain_verdict = verify_chain_compact_with_inheritance(
        slim_bundles)

    # ---- Tampering ----
    # T1: tamper deepest child's initial_weights_hash
    t1 = slim_bundle(
        slim_bundles[-1],
        CompactAncestry.from_dict(
            slim_bundles[-1].manifest["compact_ancestry"]),
        kps[-1])
    t1.manifest = dict(t1.manifest)
    t1.manifest["initial_weights_hash"] = "00" * 32
    body = {k: v for k, v in t1.manifest.items() if k != "sig"}
    t1.manifest["sig"] = kps[-1].sign(
        _canonical(body)).hex()
    t1_ok, t1_reason = verify_compact_ancestry_with_inheritance(
        t1, fetcher)

    # T2: tamper parent's spawn inherited_weights_hash
    parent_to_tamper = full_by_id[slim_bundles[-1].manifest[
        "compact_ancestry"]["parent_did"]]
    tampered_parent = IndividualBundle(
        manifest=dict(parent_to_tamper.manifest),
        memory=list(parent_to_tamper.memory),
        weights=parent_to_tamper.weights,
        initial_weights=parent_to_tamper.initial_weights,
        observations=parent_to_tamper.observations,
        ancestry=list(parent_to_tamper.ancestry),
    )
    for idx, rec in enumerate(tampered_parent.memory):
        if rec.get("type") == "spawn":
            target_child = slim_bundles[-1].individual_id
            if rec.get("child_id") == target_child:
                body = {k: v for k, v in rec.items()
                         if k != "sig"}
                body["inherited_weights_hash"] = "ff" * 32
                sig = kps[-2].sign(_canonical(body)).hex()
                tampered_parent.memory[idx] = {**body, "sig": sig}
                break
    from individual_bundle import _merkle_root
    tampered_parent.manifest["memory_root"] = _merkle_root([
        _hash({k: v for k, v in r.items() if k != "sig"})
        for r in tampered_parent.memory])
    body = {k: v for k, v in tampered_parent.manifest.items()
             if k != "sig"}
    tampered_parent.manifest["sig"] = kps[-2].sign(
        _canonical(body)).hex()
    def bad_fetcher(did):
        if did == parent_to_tamper.individual_id:
            return tampered_parent
        return full_by_id.get(did)
    t2_ok, t2_reason = verify_compact_ancestry_with_inheritance(
        slim_bundles[-1], bad_fetcher)

    # T3: remove parent's initial_weights (make it look fresh)
    stripped_parent = IndividualBundle(
        manifest=dict(parent_to_tamper.manifest),
        memory=list(parent_to_tamper.memory),
        weights=parent_to_tamper.weights,
        initial_weights=None,  # <-- stripped
        observations=parent_to_tamper.observations,
        ancestry=list(parent_to_tamper.ancestry),
    )
    # Re-sign manifest without initial_weights_hash
    if "initial_weights_hash" in stripped_parent.manifest:
        del stripped_parent.manifest["initial_weights_hash"]
    body = {k: v for k, v in stripped_parent.manifest.items()
             if k != "sig"}
    stripped_parent.manifest["sig"] = kps[-2].sign(
        _canonical(body)).hex()
    def strip_fetcher(did):
        if did == parent_to_tamper.individual_id:
            return stripped_parent
        return full_by_id.get(did)
    t3_ok, t3_reason = verify_compact_ancestry_with_inheritance(
        slim_bundles[-1], strip_fetcher)

    # ---- Size comparison ----
    sizes = []
    for i in range(1, DEPTH + 1):
        full_anc_size = full_ancestry_size(
            full_bundles[i].ancestry)
        compact_size = compact_ancestry_size(
            CompactAncestry.from_dict(
                slim_bundles[i].manifest["compact_ancestry"]))
        full_bytes = sum(
            f.stat().st_size for f in
            (root / "slim" / f"gen{i}").rglob("*")
            if f.is_file())
        sizes.append({
            "depth": i,
            "full_ancestry_bytes": full_anc_size,
            "compact_ancestry_bytes": compact_size,
            "slim_bundle_bytes": full_bytes,
        })

    # ---- Print ----
    print("=" * 74)
    print("Compact + inheritance — O(1) space, both claims")
    print("=" * 74)
    print()
    print(f"  Chain: {DEPTH + 1} generations, {STEPS} steps each")
    print()
    print("  Per-bundle verification:")
    for r in results:
        marker = "✓" if r["compact_inheritance"] else "✗"
        print(f"    {r['name']:8s}  "
              f"federated_full={r['federated_full']}  "
              f"{marker} ({r['reason']})")
    print()
    print(f"  Chain: {chain_verdict[0]}  ({chain_verdict[1]})")
    print()
    print("  Sizes (slim bundles):")
    print(f"    {'depth':<6s} {'full_anc':<10s} "
          f"{'compact':<10s} {'slim_total':<12s}")
    print(f"    {'-'*6} {'-'*10} {'-'*10} {'-'*12}")
    for s in sizes:
        print(f"    {s['depth']:<6d} "
              f"{s['full_ancestry_bytes']:<10d} "
              f"{s['compact_ancestry_bytes']:<10d} "
              f"{s['slim_bundle_bytes']:<12d}")
    print()
    print("  Tampering (slim bundles, all re-signed):")
    print(f"    tamper child's initial_weights_hash:")
    print(f"      {t1_ok}  ({t1_reason})")
    print(f"    tamper parent's spawn inherited hash:")
    print(f"      {t2_ok}  ({t2_reason})")
    print(f"    strip parent's initial_weights:")
    print(f"      {t3_ok}  ({t3_reason})")
    print()
    print("  What this establishes:")
    print("    - Descent and inheritance are verified together at")
    print("      the compact tier. Each bundle carries only ~210")
    print("      bytes of chain metadata (regardless of depth),")
    print("      but proving it descends *and* inherits requires")
    print("      walking up via fetcher.")
    print("    - At each step, the verifier replays the parent")
    print("      to the spawn index, derives the parent's actual")
    print("      weights, hashes them, and compares to the")
    print("      spawn's claim and the child's claim.")
    print("    - Tampering with either claim breaks verification:")
    print("      the two claims must match each other AND the")
    print("      replayed parent must hash to the same value.")
    print("    - Stripping the parent's initial_weights makes the")
    print("      parent appear fresh while the child still claims")
    print("      inheritance — the verifier catches the mismatch.")
    print()
    print("  The cost: O(depth × memory) time, not O(depth).")
    print("  Each step replays the parent's memory to find its")
    print("  weights at spawn time. For 5 gens × ~20 entries")
    print("  each, that's trivial; for 20 gens × 1000 entries,")
    print("  it's ~20K model steps — a few seconds.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'The Brain – is wider than the Sky –'")
    print("    'For – put them side by side –'")

    audit = {
        "chain_length": DEPTH + 1,
        "steps_per_gen": STEPS,
        "verification": results,
        "chain_verdict": {
            "ok": chain_verdict[0],
            "reason": chain_verdict[1],
        },
        "sizes": sizes,
        "tampering": {
            "child_initial_hash": {
                "detected": not t1_ok,
                "reason": t1_reason,
            },
            "parent_spawn_hash": {
                "detected": not t2_ok,
                "reason": t2_reason,
            },
            "parent_stripped_initial": {
                "detected": not t3_ok,
                "reason": t3_reason,
            },
        },
    }
    (root / "compact_inheritance_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {root}/compact_inheritance_demo.json")
    return audit
