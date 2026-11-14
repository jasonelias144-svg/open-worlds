"""
lineage_tree.py — a lineage tree verifier.

A tree is a Dict[individual_id, IndividualBundle] plus a root DID.
Every bundle's lineage_root must equal the root. Every non-root
bundle's parent_did must name a bundle in the tree.

Verification tiers:
  structure  — connectivity + chain-start invariants + root
               self-declaration. Cheap; no replay.
  full       — structure + each bundle's federated basic/full
               + each edge's federated-spawn-ancestry (replays
               parents to spawn indices)
  with_world_logs — full + each bundle cross-checked against
               its own world logs (composes existing
               verify_federated_with_world_logs)

Fork detection: a parent whose memory contains two spawn
records for the same child_id has produced a duplicate.
Detected during full verification.

Orphan detection: a child whose parent_did is not in the tree,
or whose ancestry references a spawn record not found in the
parent's memory.

Honest limits:
  - Linear-only ancestry within each bundle is assumed. A
    bundle's ancestry chain is a single path to the root.
  - The tree is provided as a Dict. Building it from disk,
    discovering parents on demand, or federating across
    multiple verifiers is out of scope.
  - Fork detection is local to each parent. Two parents
    producing consistent-looking records for the same child
    (a child with two "lineages") would not be caught
    without cross-tree consistency checks.
  - No cycle detection. A malicious tree where A.parent_did =
    B and B.parent_did = A would pass structure if both have
    valid lineage_root claims. Adding cycle detection is a
    future tightening.
"""

import json
from typing import Dict, List, Optional, Tuple

from individual_bundle import (
    IndividualBundle, verify_bundle_basic, _hash, _canonical,
)
from federated_bundle import (
    verify_federated_basic, verify_federated_full,
    verify_federated_with_world_logs,
)
from federated_spawn import verify_federated_spawn_ancestry
from lineage_root import verify_lineage_root


# =====================================================================
# Helpers
# =====================================================================

def _spawn_hash(rec: Dict) -> str:
    return _hash({k: v for k, v in rec.items() if k != "sig"})


def _find_spawn_in_memory(
    parent: IndividualBundle, spawn_hash: str,
) -> Optional[Dict]:
    for rec in parent.memory:
        if rec.get("type") != "spawn":
            continue
        if _spawn_hash(rec) == spawn_hash:
            return rec
    return None


def _detect_duplicate_spawns(
    parent: IndividualBundle,
) -> List[Dict]:
    """Spawn records in parent's memory sharing a child_id."""
    seen: Dict[str, List[Dict]] = {}
    for rec in parent.memory:
        if rec.get("type") != "spawn":
            continue
        child_id = rec.get("child_id")
        if not child_id:
            continue
        seen.setdefault(child_id, []).append({
            "record_hash": _spawn_hash(rec),
            "signed_at": rec.get("ts", ""),
        })
    return [
        {"child_id": cid, "records": recs}
        for cid, recs in seen.items() if len(recs) > 1
    ]


# =====================================================================
# Structure tier
# =====================================================================

def verify_lineage_tree_structure(
    bundles: Dict[str, IndividualBundle],
    root_did: str,
) -> Tuple[bool, str]:
    if not isinstance(bundles, dict):
        return (False, "bundles must be a Dict")
    if root_did not in bundles:
        return (False,
                 f"root {root_did[:16]}... not in bundles")
    root = bundles[root_did]
    if root.manifest.get("individual_id") != root_did:
        return (False,
                 f"root bundle's individual_id "
                 f"{root.manifest.get('individual_id', '')[:16]}... "
                 f"!= root_did")
    if root.manifest.get("lineage_root") != root_did:
        return (False,
                 f"root's lineage_root "
                 f"{root.manifest.get('lineage_root', '')[:16]}... "
                 f"!= root_did (root must be self-declared origin)")
    if root.ancestry:
        return (False,
                 "root bundle carries ancestry (should be empty)")

    for did, b in bundles.items():
        if not isinstance(b, IndividualBundle):
            return (False,
                     f"bundle {did[:16]}... is not an "
                     f"IndividualBundle")
        if b.manifest.get("individual_id") != did:
            return (False,
                     f"bundle key {did[:16]}... != "
                     f"manifest.individual_id")
        if b.manifest.get("lineage_root") != root_did:
            return (False,
                     f"bundle {did[:16]}... lineage_root "
                     f"{b.manifest.get('lineage_root', '')[:16]}... "
                     f"!= tree root")
        if did == root_did:
            continue
        parent_did = b.manifest.get("parent_did")
        if not parent_did:
            return (False,
                     f"bundle {did[:16]}... has no parent_did")
        if parent_did not in bundles:
            return (False,
                     f"bundle {did[:16]}... parent_did "
                     f"{parent_did[:16]}... not in tree")
        if not b.ancestry:
            return (False,
                     f"bundle {did[:16]}... has no ancestry")
        if b.ancestry[0].get("agent_id") != parent_did:
            return (False,
                     f"bundle {did[:16]}... ancestry[0].agent_id "
                     f"!= parent_did")
        if b.ancestry[0].get("child_id") != did:
            return (False,
                     f"bundle {did[:16]}... ancestry[0].child_id "
                     f"!= individual_id")
    return (True, f"tree structure verifies ({len(bundles)} bundles)")


# =====================================================================
# Full tier
# =====================================================================

def verify_lineage_tree(
    bundles: Dict[str, IndividualBundle],
    root_did: str,
) -> Tuple[bool, str]:
    ok, reason = verify_lineage_tree_structure(bundles, root_did)
    if not ok:
        return (False, f"structure: {reason}")

    # Each bundle independently
    for did, b in bundles.items():
        v_basic = verify_federated_basic(b)
        if not v_basic[0]:
            return (False,
                     f"bundle {did[:16]}... basic: {v_basic[1]}")
        v_full = verify_federated_full(b)
        if not v_full[0]:
            return (False,
                     f"bundle {did[:16]}... full: {v_full[1]}")
        v_root = verify_lineage_root(b)
        if not v_root[0]:
            return (False,
                     f"bundle {did[:16]}... lineage_root: {v_root[1]}")

    # Each edge
    for did, b in bundles.items():
        if did == root_did:
            continue
        parent_did = b.manifest["parent_did"]
        parent = bundles[parent_did]
        v_edge = verify_federated_spawn_ancestry(b, parent)
        if not v_edge[0]:
            return (False,
                     f"edge {parent_did[:16]}...→{did[:16]}...: "
                     f"{v_edge[1]}")

    # Duplicate spawns (fork detection)
    for did, b in bundles.items():
        dups = _detect_duplicate_spawns(b)
        if dups:
            return (False,
                     f"bundle {did[:16]}... has duplicate "
                     f"spawns for children "
                     f"{[d['child_id'][:16] for d in dups]}")

    return (True, f"tree of {len(bundles)} bundles verifies")


# =====================================================================
# With-world-logs tier
# =====================================================================

def verify_lineage_tree_with_world_logs(
    bundles: Dict[str, IndividualBundle],
    root_did: str,
    world_logs: Dict[str, Dict[str, List[Dict]]],
) -> Tuple[bool, str]:
    """world_logs: {individual_id: {world_id: [step_bodies]}}."""
    ok, reason = verify_lineage_tree(bundles, root_did)
    if not ok:
        return (False, f"full: {reason}")
    for did, b in bundles.items():
        if did not in world_logs:
            return (False,
                     f"bundle {did[:16]}... not in world_logs")
        v_wl = verify_federated_with_world_logs(
            b, world_logs[did])
        if not v_wl[0]:
            return (False,
                     f"bundle {did[:16]}... with-world-logs: "
                     f"{v_wl[1]}")
    return (True,
             f"tree of {len(bundles)} bundles with world logs verifies")


# =====================================================================
# Reports
# =====================================================================

def tree_report(
    bundles: Dict[str, IndividualBundle],
    root_did: str,
) -> Dict:
    report = {
        "root": root_did,
        "bundles": [],
        "edges": [],
        "duplicates": [],
        "verdict": False,
        "verdict_reason": "",
    }
    try:
        verdict = verify_lineage_tree(bundles, root_did)
        report["verdict"] = verdict[0]
        report["verdict_reason"] = verdict[1]
    except Exception as e:
        report["verdict_reason"] = f"exception: {e}"

    for did, b in bundles.items():
        info = {
            "individual_id": did,
            "name": b.manifest.get("name", "?"),
            "parent_did": b.manifest.get("parent_did"),
            "lineage_root": b.manifest.get("lineage_root"),
            "ancestry_length": len(b.ancestry),
        }
        try:
            v_basic = verify_federated_basic(b)
            v_full = verify_federated_full(b)
            info["basic"] = v_basic[0]
            info["full"] = v_full[0]
        except Exception as e:
            info["basic"] = False
            info["full"] = False
            info["error"] = str(e)
        report["bundles"].append(info)

        parent_did = b.manifest.get("parent_did")
        if parent_did and parent_did in bundles:
            try:
                v_edge = verify_federated_spawn_ancestry(
                    b, bundles[parent_did])
                report["edges"].append({
                    "from": parent_did,
                    "to": did,
                    "verified": v_edge[0],
                    "reason": v_edge[1],
                })
            except Exception as e:
                report["edges"].append({
                    "from": parent_did,
                    "to": did,
                    "verified": False,
                    "reason": f"exception: {e}",
                })
        dups = _detect_duplicate_spawns(b)
        if dups:
            report["duplicates"].append({
                "parent": did,
                "children": [d["child_id"] for d in dups],
            })
    return report


# =====================================================================
# Tree building and rendering
# =====================================================================

def build_tree(
    bundles: Dict[str, IndividualBundle],
    root_did: str,
) -> Dict[str, Dict]:
    tree: Dict[str, Dict] = {}
    for did, b in bundles.items():
        tree[did] = {
            "individual_id": did,
            "name": b.manifest.get("name", "?"),
            "parent_did": b.manifest.get("parent_did"),
            "children": [],
        }
    for did, node in tree.items():
        parent_did = node["parent_did"]
        if parent_did and parent_did in tree:
            tree[parent_did]["children"].append(did)
    return tree


def render_tree(
    bundles: Dict[str, IndividualBundle],
    root_did: str,
) -> str:
    tree = build_tree(bundles, root_did)
    lines = []

    def _walk(did: str, indent: int, is_last: bool):
        prefix = "  " * indent
        if indent == 0:
            marker = "◆"
        elif is_last:
            marker = "└─"
        else:
            marker = "├─"
        node = tree[did]
        lines.append(
            f"{prefix}{marker} {node['name']} "
            f"({did[:20]}...)")
        children = sorted(node["children"])
        for i, child in enumerate(children):
            _walk(child, indent + 1, i == len(children) - 1)

    if root_did in tree:
        _walk(root_did, 0, True)
    else:
        lines.append(
            f"(root {root_did[:20]}... not in bundles)")
    return "\n".join(lines)


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
    root = Path(artifact_dir) / "lineage_tree"
    root.mkdir(parents=True, exist_ok=True)

    def _kp():
        return Ed25519PrivateKey.generate()

    def _world(k_b, prng):
        return ScriptedWorld(
            kp=_kp(), initial_point_b=(800, 800),
            k_b=k_b, prng_seed_b=prng, rule=SIERPINSKI)

    def _make_individual(
        name: str, seed: int, world_specs: list,
        parent_bundle=None, spawn_record=None,
        inherited_weights=None,
    ):
        """Build a bundle with given world specs. If parent_bundle
        is given, spawns from it; otherwise origin."""
        kp = _kp()
        model = TinyRNN(n_extra_inputs=0, seed=seed)
        if inherited_weights is not None:
            from individual_bundle import apply_weights
            apply_weights(model, inherited_weights)
        memory: List[Dict] = []
        sessions = []
        for widx, (n, pt, k_b, prng) in enumerate(world_specs):
            s = FederatedSession(
                individual_kp=kp, model=model,
                world=_world(k_b, prng),
                initial_point=pt, memory=memory,
                rule=SIERPINSKI)
            for _ in range(n):
                s.step()
            sessions.append(s)
        if parent_bundle is None:
            bundle = pack_federated_bundle(
                individual_kp=kp, model=model,
                sessions=sessions, memory=memory,
                persona=f"{name} (origin)", initial_seed=seed,
                name=name,
            )
        else:
            bundle = pack_federated_child(
                child_kp=kp, child_model=model,
                child_sessions=sessions, child_memory=memory,
                child_persona=name, child_initial_seed=seed,
                parent_bundle=parent_bundle,
                spawn_record=spawn_record,
                inherited_weights=inherited_weights,
                name=name,
            )
        return kp, model, sessions, memory, bundle

    # Build tree:
    # Grandparent
    # ├── Parent1
    # │   └── Child1
    # └── Parent2
    #     ├── Child2
    #     └── Child3

    gp_kp, gp_model, gp_sessions, gp_mem, gp = _make_individual(
        "grandparent", seed=42,
        world_specs=[(80, (200, 800), 0, 0xAAAA),
                      (60, (300, 700), 50, 0xBBBB)],
    )

    # GP spawns P1, then continues
    p1_kp, p1_model, gp_to_p1, gp_weights_p1 = \
        spawn_federated_child(
            parent_session=gp_sessions[-1],
            child_persona="parent1",
            child_initial_seed=100)
    gp_sessions[-1].step()

    # GP spawns P2 (at a different point)
    p2_kp, p2_model, gp_to_p2, gp_weights_p2 = \
        spawn_federated_child(
            parent_session=gp_sessions[-1],
            child_persona="parent2",
            child_initial_seed=200)
    gp_sessions[-1].step()

    # Repack GP with both spawns in memory
    gp = pack_federated_bundle(
        individual_kp=gp_kp, model=gp_model,
        sessions=gp_sessions, memory=gp_mem,
        persona="grandparent (origin)",
        initial_seed=42, name="grandparent",
    )

    # Build P1 (inherits from GP)
    p1_kp, p1_model, p1_sessions, p1_mem, p1 = \
        _make_individual(
            "parent1", seed=100,
            world_specs=[(60, (250, 750), 25, 0xDDDD)],
            parent_bundle=gp, spawn_record=gp_to_p1,
            inherited_weights=gp_weights_p1,
        )
    # P1 spawns C1
    c1_kp, c1_model, p1_to_c1, p1_weights_c1 = \
        spawn_federated_child(
            parent_session=p1_sessions[-1],
            child_persona="child1",
            child_initial_seed=101)
    p1_sessions[-1].step()
    # Repack P1
    p1 = pack_federated_child(
        child_kp=p1_kp, child_model=p1_model,
        child_sessions=p1_sessions, child_memory=p1_mem,
        child_persona="parent1", child_initial_seed=100,
        parent_bundle=gp, spawn_record=gp_to_p1,
        inherited_weights=gp_weights_p1, name="parent1",
    )

    # C1 (inherits from P1)
    c1_kp, c1_model, c1_sessions, c1_mem, c1 = \
        _make_individual(
            "child1", seed=101,
            world_specs=[(40, (300, 700), 30, 0x1234)],
            parent_bundle=p1, spawn_record=p1_to_c1,
            inherited_weights=p1_weights_c1,
        )

    # Build P2 (inherits from GP)
    p2_kp, p2_model, p2_sessions, p2_mem, p2 = \
        _make_individual(
            "parent2", seed=200,
            world_specs=[(60, (250, 750), 40, 0xEEEE)],
            parent_bundle=gp, spawn_record=gp_to_p2,
            inherited_weights=gp_weights_p2,
        )
    # P2 spawns C2 and C3
    c2_kp, c2_model, p2_to_c2, p2_weights_c2 = \
        spawn_federated_child(
            parent_session=p2_sessions[-1],
            child_persona="child2",
            child_initial_seed=201)
    p2_sessions[-1].step()
    c3_kp, c3_model, p2_to_c3, p2_weights_c3 = \
        spawn_federated_child(
            parent_session=p2_sessions[-1],
            child_persona="child3",
            child_initial_seed=202)
    p2_sessions[-1].step()
    # Repack P2 with both spawns
    p2 = pack_federated_child(
        child_kp=p2_kp, child_model=p2_model,
        child_sessions=p2_sessions, child_memory=p2_mem,
        child_persona="parent2", child_initial_seed=200,
        parent_bundle=gp, spawn_record=gp_to_p2,
        inherited_weights=gp_weights_p2, name="parent2",
    )

    # Build C2, C3
    _, _, _, _, c2 = _make_individual(
        "child2", seed=201,
        world_specs=[(30, (300, 700), 55, 0x5555)],
        parent_bundle=p2, spawn_record=p2_to_c2,
        inherited_weights=p2_weights_c2,
    )
    _, _, _, _, c3 = _make_individual(
        "child3", seed=202,
        world_specs=[(30, (300, 700), 65, 0x6666)],
        parent_bundle=p2, spawn_record=p2_to_c3,
        inherited_weights=p2_weights_c3,
    )

    bundles = {
        gp.individual_id: gp,
        p1.individual_id: p1,
        p2.individual_id: p2,
        c1.individual_id: c1,
        c2.individual_id: c2,
        c3.individual_id: c3,
    }
    root_did = gp.individual_id

    # Save to disk
    for name, b in (
        ("grandparent", gp), ("parent1", p1), ("parent2", p2),
        ("child1", c1), ("child2", c2), ("child3", c3),
    ):
        b.save(root / name)

    # Verify tree
    verdict = verify_lineage_tree(bundles, root_did)
    report = tree_report(bundles, root_did)

    # Tamper 1: remove child1 from the tree
    smaller = {did: b for did, b in bundles.items()
                if did != c1.individual_id}
    tamper1 = verify_lineage_tree(smaller, root_did)

    # Tamper 2: change child2's parent_did (re-signed)
    tampered_c2 = IndividualBundle.load(root / "child2")
    tampered_c2.manifest = dict(tampered_c2.manifest)
    tampered_c2.manifest["parent_did"] = gp.individual_id
    from individual_bundle import _canonical as _canon
    body = {k: v for k, v in tampered_c2.manifest.items()
             if k != "sig"}
    tampered_c2.manifest["sig"] = c2_kp.sign(
        _canon(body)).hex()
    tamper2_bundles = dict(bundles)
    tamper2_bundles[c2.individual_id] = tampered_c2
    tamper2 = verify_lineage_tree(tamper2_bundles, root_did)

    # Tamper 3: inject a duplicate spawn into parent2's memory
    tampered_p2 = IndividualBundle.load(root / "parent2")
    tampered_p2.memory = list(tampered_p2.memory)
    # Find the spawn record for child2
    spawn_rec_for_c2 = None
    for rec in tampered_p2.memory:
        if rec.get("type") == "spawn" \
                and rec.get("child_id") == c2.individual_id:
            spawn_rec_for_c2 = dict(rec)
            break
    if spawn_rec_for_c2:
        dup = {**spawn_rec_for_c2, "ts": "2026-11-15T99:99:99Z"}
        body = {k: v for k, v in dup.items() if k != "sig"}
        dup["sig"] = p2_kp.sign(_canon(body)).hex()
        tampered_p2.memory.append(dup)
        # Recompute memory_root and re-sign manifest
        from individual_bundle import _merkle_root, _hash
        tampered_p2.manifest = dict(tampered_p2.manifest)
        tampered_p2.manifest["memory_entries"] = len(
            tampered_p2.memory)
        tampered_p2.manifest["memory_root"] = _merkle_root([
            _hash({k: v for k, v in r.items() if k != "sig"})
            for r in tampered_p2.memory
        ])
        body = {k: v for k, v in tampered_p2.manifest.items()
                 if k != "sig"}
        tampered_p2.manifest["sig"] = p2_kp.sign(
            _canon(body)).hex()
        tamper3_bundles = dict(bundles)
        tamper3_bundles[p2.individual_id] = tampered_p2
        tamper3 = verify_lineage_tree(tamper3_bundles, root_did)
    else:
        tamper3 = (None, "could not find spawn for c2")

    # Print
    print("=" * 74)
    print("Lineage tree — a branching family of individuals")
    print("=" * 74)
    print()
    print(render_tree(bundles, root_did))
    print()
    print(f"  Tree: {len(bundles)} bundles, {len(report['edges'])} edges")
    print()
    print("  Verification:")
    print(f"    full: {verdict[0]}  ({verdict[1]})")
    print(f"    tree_report aggregate: {report['verdict']}")
    print()
    print("  Tampering:")
    print(f"    remove child1 from tree → "
          f"structure: {tamper1[0]}")
    if not tamper1[0]:
        print(f"      reason: {tamper1[1]}")
    print(f"    change child2's parent_did to grandparent → "
          f"structure: {tamper2[0]}")
    if not tamper2[0]:
        print(f"      reason: {tamper2[1]}")
    print(f"    inject duplicate spawn for child2 in parent2 → "
          f"full: {tamper3[0]}")
    if tamper3[0] is False:
        print(f"      reason: {tamper3[1]}")
    print()
    print("  What this establishes:")
    print("    - A lineage is a tree, not a chain. Parent2 spawns")
    print("      both child2 and child3; both descend from the same")
    print("      grandparent, but through different paths.")
    print("    - verify_lineage_tree walks the whole structure:")
    print("      connectivity, each bundle's independent verification,")
    print("      each edge's spawn-ancestry replay, and each parent's")
    print("      spawn-record integrity.")
    print("    - Forks are detected: a parent with two spawn records")
    print("      for the same child_id is caught, even though each")
    print("      record individually verifies.")
    print("    - Orphans are detected: a removed bundle breaks")
    print("      structure because a child's parent_did no longer")
    print("      resolves.")
    print("    - Tampering with a child's parent_did breaks structure")
    print("      because ancestry[0].agent_id no longer matches.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'The Brain – is wider than the Sky –'")
    print("    'For – put them side by side –'")
    print("    'The one the other will contain'")
    print("    'With ease – and You – beside –'")

    audit = {
        "tree_root": root_did,
        "tree_size": len(bundles),
        "edge_count": len(report["edges"]),
        "verification": {
            "full": verdict[0],
            "report_aggregate": report["verdict"],
        },
        "tampering": {
            "remove_child_detected": not tamper1[0],
            "wrong_parent_detected": not tamper2[0],
            "duplicate_spawn_detected": (
                tamper3[0] is False),
        },
    }
    (root / "lineage_tree_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {root}/lineage_tree_demo.json")
    return audit


HAS_CRYPTO = True
try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey)
except ImportError:
    HAS_CRYPTO = False
