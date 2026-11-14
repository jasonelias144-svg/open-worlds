"""
lineage_root.py — single-bundle proof of descent.

verify_lineage_root(bundle) proves descent from a claimed
root using only the bundle itself. The chain of ancestry
records (signed by each parent at spawn time) forms the
evidence; the manifest's ancestry_hash binds the list.

What this proves:
  - I descend from the root I claim, via these specific
    spawn records.
  - Each link was signed by the parent at spawn time.
  - The chain has no gaps and no reordering.

What this does NOT prove:
  - That the root is the *true* origin. My bundle declares
    it as the root; my root's bundle might declare an
    earlier root. To verify the root is truly the origin,
    fetch root's bundle and check
    root.manifest.lineage_root == root.individual_id.
  - That weights were actually inherited. Lineage and
    weight inheritance are separate claims. Lineage
    proves descent; verify_federated_spawn_ancestry
    proves inheritance.

The space cost is O(depth): each generation's bundle
carries one more ancestry record than its parent's.

Honest limits:
  - Single-bundle verification of *weight inheritance*
    is impossible without replaying parent memories.
    Lineage_root only proves the descent relationship,
    not the arithmetic of what was passed.
  - The root bundle's own verification (that it's truly
    the origin) requires fetching one more bundle.
  - Ancestry is linear. Branching lineage (one parent,
    multiple children) works per-child — each child
    carries its own ancestry list — but a *tree*
    verifier that walks all descendants from a root is
    not built.
"""

import json
from typing import Dict, List, Tuple

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PublicKey)
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from individual_bundle import (
    IndividualBundle, _canonical, _hash, _pubkey_from_did,
    _merkle_root, verify_bundle_basic,
)
from federated_bundle import verify_federated_basic


def verify_lineage_root(bundle: IndividualBundle) -> Tuple[bool, str]:
    """Prove descent from bundle.manifest['lineage_root'] using
    only the bundle. Never raises."""
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    if not isinstance(bundle, IndividualBundle):
        return (False, "not an IndividualBundle")
    manifest = bundle.manifest
    root = manifest.get("lineage_root")
    if root is None:
        return (False, "no lineage_root declared")
    ind_id = manifest.get("individual_id")
    if not isinstance(ind_id, str) or not ind_id:
        return (False, "missing individual_id")
    ancestry = bundle.ancestry or []

    # Self-root case
    if root == ind_id:
        if ancestry:
            return (False,
                     "root bundle carries ancestry (should be empty)")
        return (True, "bundle is its own lineage root")

    # Descendant case
    if not ancestry:
        return (False, "descendant has no ancestry chain")
    first = ancestry[0]
    if first.get("child_id") != ind_id:
        return (False,
                 f"ancestry[0].child_id {first.get('child_id')} "
                 f"!= individual_id {ind_id}")

    # Verify each record's signature and chain links
    for i, rec in enumerate(ancestry):
        agent = rec.get("agent_id")
        child = rec.get("child_id")
        sig = rec.get("sig")
        if not agent or not child or not sig:
            return (False,
                     f"ancestry[{i}]: missing agent_id / "
                     f"child_id / sig")
        if i > 0:
            prev = ancestry[i - 1]
            if prev.get("agent_id") != child:
                return (False,
                         f"ancestry[{i}]: parent "
                         f"{prev.get('agent_id')} of ancestry["
                         f"{i-1}] != child {child} of "
                         f"ancestry[{i}]")
        # Signature: parent (agent_id) signs the spawn record
        body = {k: v for k, v in rec.items() if k != "sig"}
        try:
            _pubkey_from_did(agent).verify(
                bytes.fromhex(sig), _canonical(body))
        except Exception:
            return (False,
                     f"ancestry[{i}]: signature invalid "
                     f"(signed by {agent})")

    # Chain ends at the claimed root
    last_agent = ancestry[-1].get("agent_id")
    if last_agent != root:
        return (False,
                 f"ancestry[-1].agent_id {last_agent} != "
                 f"lineage_root {root}")

    return (True,
             f"descends from {root} via {len(ancestry)} "
             f"signed spawn record(s)")


def verify_lineage_root_is_origin(
    descendant: IndividualBundle,
    root_bundle: IndividualBundle,
) -> Tuple[bool, str]:
    """Stronger: proves descendant descends from root, and
    root is truly the origin (root's own lineage_root =
    root's own did)."""
    ok, reason = verify_lineage_root(descendant)
    if not ok:
        return (False, f"descendant lineage_root: {reason}")
    root_did = descendant.manifest["lineage_root"]
    if root_bundle.manifest.get("individual_id") != root_did:
        return (False,
                 f"root_bundle id "
                 f"{root_bundle.manifest.get('individual_id')} "
                 f"!= claimed root {root_did}")
    if root_bundle.manifest.get("lineage_root") != root_did:
        return (False,
                 f"root_bundle.lineage_root "
                 f"{root_bundle.manifest.get('lineage_root')} "
                 f"!= root's own id — root is not "
                 f"self-declared origin")
    return (True,
             f"descends from verified origin {root_did}")


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
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey)
    import json as _json

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    root = Path(artifact_dir) / "lineage_root"
    root.mkdir(parents=True, exist_ok=True)

    def _kp():
        return Ed25519PrivateKey.generate()

    def _world(k_b, prng):
        return ScriptedWorld(
            kp=_kp(), initial_point_b=(800, 800),
            k_b=k_b, prng_seed_b=prng, rule=SIERPINSKI)

    # --- Generation 0: grandparent lives in three worlds ---
    gp_kp = _kp()
    gp_model = TinyRNN(n_extra_inputs=0, seed=42)
    gp_mem: List[Dict] = []
    gp_sessions = []
    for widx, n, pt in [(0, 100, (200, 800)),
                          (1, 80, (300, 700)),
                          (2, 60, (400, 600))]:
        s = FederatedSession(
            individual_kp=gp_kp, model=gp_model,
            world=_world(0 if widx == 0 else 50 if widx == 1 else 100,
                          0xAAAA + widx * 0x1111),
            initial_point=pt, memory=gp_mem,
            rule=SIERPINSKI)
        for _ in range(n):
            s.step()
        gp_sessions.append(s)
    # Grandparent spawns parent
    p_kp, p_model, gp_to_p_spawn, gp_weights = \
        spawn_federated_child(
            parent_session=gp_sessions[-1],
            child_persona="parent",
            child_initial_seed=200)
    for _ in range(20):
        gp_sessions[-1].step()
    gp_bundle = pack_federated_bundle(
        individual_kp=gp_kp, model=gp_model,
        sessions=gp_sessions, memory=gp_mem,
        persona="grandparent (origin)",
        initial_seed=42, name="grandparent",
        # No lineage_root passed → self-root (default)
    )

    # --- Generation 1: parent lives in two worlds ---
    p_mem: List[Dict] = []
    p_sessions = []
    for widx, n, pt in [(0, 80, (250, 750)),
                          (1, 60, (350, 650))]:
        s = FederatedSession(
            individual_kp=p_kp, model=p_model,
            world=_world(25, 0xDDDD + widx),
            initial_point=pt, memory=p_mem,
            rule=SIERPINSKI)
        for _ in range(n):
            s.step()
        p_sessions.append(s)
    # Parent spawns child
    c_kp, c_model, p_to_c_spawn, p_weights = \
        spawn_federated_child(
            parent_session=p_sessions[-1],
            child_persona="child",
            child_initial_seed=300)
    for _ in range(20):
        p_sessions[-1].step()
    p_bundle = pack_federated_child(
        child_kp=p_kp, child_model=p_model,
        child_sessions=p_sessions, child_memory=p_mem,
        child_persona="parent", child_initial_seed=200,
        parent_bundle=gp_bundle, spawn_record=gp_to_p_spawn,
        inherited_weights=gp_weights, name="parent")

    # --- Generation 2: child lives in one world ---
    c_mem: List[Dict] = []
    c_world = _world(75, 0x1234)
    s = FederatedSession(
        individual_kp=c_kp, model=c_model,
        world=c_world, initial_point=(300, 700),
        memory=c_mem, rule=SIERPINSKI)
    for _ in range(100):
        s.step()
    c_sessions = [s]
    c_bundle = pack_federated_child(
        child_kp=c_kp, child_model=c_model,
        child_sessions=c_sessions, child_memory=c_mem,
        child_persona="child", child_initial_seed=300,
        parent_bundle=p_bundle, spawn_record=p_to_c_spawn,
        inherited_weights=p_weights, name="child")

    # --- Save all three ---
    for name, b in (("gen0_grandparent", gp_bundle),
                     ("gen1_parent", p_bundle),
                     ("gen2_child", c_bundle)):
        b.save(root / name)

    # --- Reload and verify ---
    gp = IndividualBundle.load(root / "gen0_grandparent")
    p = IndividualBundle.load(root / "gen1_parent")
    c = IndividualBundle.load(root / "gen2_child")

    # The key demonstration: child's bundle alone proves descent
    # to grandparent
    child_root_verdict = verify_lineage_root(c)
    child_root_verdict_with_origin = verify_lineage_root_is_origin(
        c, gp)
    # And parent, being a descendant, also proves descent
    parent_root_verdict = verify_lineage_root(p)
    # Grandparent is self-root
    gp_root_verdict = verify_lineage_root(gp)

    # Federated full still works for each bundle independently
    fed_full = {
        "gp": verify_federated_full(gp)[0],
        "p":  verify_federated_full(p)[0],
        "c":  verify_federated_full(c)[0],
    }

    # --- Tampering: remove ancestry from child bundle ---
    tampered_c = IndividualBundle.load(root / "gen2_child")
    tampered_c.ancestry = []
    # ancestry_hash in manifest won't match anymore
    tampered_basic = verify_bundle_basic(tampered_c)
    tampered_root = verify_lineage_root(tampered_c)

    # --- Tampering: alter one ancestry record's sig ---
    tampered_c2 = IndividualBundle.load(root / "gen2_child")
    tampered_c2.ancestry = [dict(r) for r in tampered_c2.ancestry]
    tampered_c2.ancestry[1]["sig"] = "00" * 64
    tampered_c2_basic = verify_bundle_basic(tampered_c2)
    tampered_c2_root = verify_lineage_root(tampered_c2)

    # --- Print ---
    print("=" * 74)
    print("Lineage root — single-bundle proof of descent")
    print("=" * 74)
    print()
    print(f"  Grandparent (origin): {gp.individual_id[:40]}...")
    print(f"  Parent:               {p.individual_id[:40]}...")
    print(f"  Child:                {c.individual_id[:40]}...")
    print()
    print("  All three bundles declare the same root:")
    print(f"    grandparent.lineage_root = "
          f"{gp.manifest['lineage_root'][:40]}...")
    print(f"    parent.lineage_root      = "
          f"{p.manifest['lineage_root'][:40]}...")
    print(f"    child.lineage_root       = "
          f"{c.manifest['lineage_root'][:40]}...")
    print()
    print("  Ancestry chain sizes:")
    print(f"    grandparent: {len(gp.ancestry)} records")
    print(f"    parent:      {len(p.ancestry)} records")
    print(f"    child:       {len(c.ancestry)} records")
    print()
    print("  Single-bundle lineage verification (no parent bundles):")
    print(f"    grandparent:  {gp_root_verdict[0]}  "
          f"({gp_root_verdict[1]})")
    print(f"    parent:       {parent_root_verdict[0]}  "
          f"({parent_root_verdict[1]})")
    print(f"    child:        {child_root_verdict[0]}  "
          f"({child_root_verdict[1]})")
    print(f"    child → origin: {child_root_verdict_with_origin[0]}  "
          f"({child_root_verdict_with_origin[1]})")
    print()
    print("  Federated full (independent of lineage):")
    print(f"    grandparent: {fed_full['gp']}, "
          f"parent: {fed_full['p']}, "
          f"child: {fed_full['c']}")
    print()
    print("  Tampering (each child bundle loaded from disk, "
          "then tampered):")
    print(f"    remove all ancestry records:")
    print(f"      basic verification: {tampered_basic[0]}  "
          f"({tampered_basic[1]})")
    print(f"      lineage_root:       {tampered_root[0]}  "
          f"({tampered_root[1]})")
    print(f"    alter one ancestry record's signature:")
    print(f"      basic verification: {tampered_c2_basic[0]}  "
          f"({tampered_c2_basic[1]})")
    print(f"      lineage_root:       {tampered_c2_root[0]}  "
          f"({tampered_c2_root[1]})")
    print()
    print("  What this establishes:")
    print("    - A single descendant bundle proves descent from")
    print("      a specific root. Given only the child's bundle,")
    print("      a stranger verifies the ancestry chain: each")
    print("      link was signed by the parent at spawn time,")
    print("      the chain has no gaps, and it ends at the")
    print("      declared root.")
    print("    - The child doesn't need the parent's or")
    print("      grandparent's bundles for this proof.")
    print("    - To additionally verify the root is truly the")
    print("      origin (not itself a descendant), one more")
    print("      bundle is needed — the root's. That's")
    print("      verify_lineage_root_is_origin.")
    print("    - Tampering with ancestry (removing records,")
    print("      corrupting signatures) fails at basic")
    print("      verification (ancestry_hash mismatch) or at")
    print("      the lineage_root check (signature invalid).")
    print("    - Federated full verification is unchanged;")
    print("      lineage_root is an additional claim that")
    print("      composes with the existing tiers.")
    print()
    print("  Honest limit: lineage_root proves *descent*, not")
    print("  *weight inheritance*. Proving the parent's actual")
    print("  weights match the child's claimed initial_weights")
    print("  still requires replaying the parent's log — which")
    print("  means having the parent's bundle. Lineage and")
    print("  inheritance are separate claims at separate tiers.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'I dwell in Possibility –'")
    print("    'A fairer House than Prose –'")
    print("    'More numerous of Windows –'")
    print("    'Superior – for Doors –'")

    audit = {
        "grandparent_id": gp.individual_id,
        "parent_id": p.individual_id,
        "child_id": c.individual_id,
        "lineage_root": gp.individual_id,
        "ancestry_lengths": {
            "grandparent": len(gp.ancestry),
            "parent": len(p.ancestry),
            "child": len(c.ancestry),
        },
        "verification": {
            "gp_root": gp_root_verdict[0],
            "parent_root": parent_root_verdict[0],
            "child_root": child_root_verdict[0],
            "child_root_is_origin": child_root_verdict_with_origin[0],
            "federated_full": fed_full,
        },
        "tampering": {
            "removed_ancestry_detected": not tampered_basic[0],
            "corrupt_sig_detected_basic": not tampered_c2_basic[0],
            "corrupt_sig_detected_root": not tampered_c2_root[0],
        },
    }
    (root / "lineage_root_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {root}/lineage_root_demo.json")
    return audit
