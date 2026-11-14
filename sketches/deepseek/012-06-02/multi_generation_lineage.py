"""
multi_generation_lineage.py — a chain of inheriting individuals.

Grandparent → Parent → Child, each inheriting from the previous,
each living in its own worlds. Provides:

  verify_lineage_chain_full(chain)
    Each bundle federated-basic + full verified.
    Each adjacent pair passes federated-spawn-ancestry.
    Returns (ok, reason) — the conjunction.

  lineage_report(chain)
    Structured breakdown: per-bundle, per-link, aggregate.

  render_chain(chain)
    Human-readable tree.

Honest limits:
  - O(N·M) verification cost (N generations, M max memory).
    Pairwise ancestry replays each parent to spawn index;
    each bundle full-replays its own memory.
  - Linear chains only. Branching (one parent, multiple
    children) would need a tree verifier.
  - No transitive descent proof without intermediate bundles.
    Grandchild can't prove descent from grandparent without
    the parent bundle.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from individual_bundle import (
    IndividualBundle, serialize_weights, _canonical, _hash,
    _merkle_root, _pubkey_from_did, _did_from_kp,
)
from individual_spawn import spawn_record_hash
from federated_bundle import (
    FederatedSession, pack_federated_bundle,
    verify_federated_basic, verify_federated_full,
)
from federated_spawn import (
    spawn_federated_child, pack_federated_child,
    verify_federated_spawn_ancestry,
)
from world_agent_coupling import ScriptedWorld
from coupled_learners import TinyRNN, SIERPINSKI


def _kp():
    return Ed25519PrivateKey.generate()


# =====================================================================
# Chain verification
# =====================================================================

def verify_lineage_chain_full(
    chain: List[IndividualBundle],
) -> Tuple[bool, str]:
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    if not isinstance(chain, list):
        return (False, "chain must be a list")
    if len(chain) < 1:
        return (False, "empty chain")

    # Every bundle independently
    for i, b in enumerate(chain):
        if not isinstance(b, IndividualBundle):
            return (False, f"chain[{i}] is not an IndividualBundle")
        v_basic = verify_federated_basic(b)
        if not v_basic[0]:
            return (False, f"chain[{i}] basic: {v_basic[1]}")
        v_full = verify_federated_full(b)
        if not v_full[0]:
            return (False, f"chain[{i}] full: {v_full[1]}")

    # Every adjacent pair
    for i in range(len(chain) - 1):
        ok, reason = verify_federated_spawn_ancestry(
            chain[i + 1], chain[i])
        if not ok:
            return (False, f"link {i}→{i+1}: {reason}")

    return (True, f"chain of {len(chain)} verifies")


def lineage_report(chain: List[IndividualBundle]) -> Dict:
    """Structured report — per-bundle, per-link, aggregate.
    Does not raise; reports failures as data."""
    per_bundle = []
    per_link = []
    for i, b in enumerate(chain):
        try:
            v_basic = verify_federated_basic(b)
            v_full = verify_federated_full(b)
        except Exception as e:
            v_basic = (False, f"exception: {e}")
            v_full = (False, f"exception: {e}")
        per_bundle.append({
            "index": i,
            "name": b.manifest.get("name", "?"),
            "id": b.manifest["individual_id"],
            "basic": v_basic[0],
            "full": v_full[0],
            "basic_reason": v_basic[1],
            "full_reason": v_full[1],
        })
    for i in range(len(chain) - 1):
        try:
            ok, reason = verify_federated_spawn_ancestry(
                chain[i + 1], chain[i])
        except Exception as e:
            ok, reason = (False, f"exception: {e}")
        per_link.append({
            "from": i,
            "to": i + 1,
            "verified": ok,
            "reason": reason,
        })
    aggregate = all(p["basic"] and p["full"]
                     for p in per_bundle) and \
                all(p["verified"] for p in per_link)
    return {
        "chain_length": len(chain),
        "bundles": per_bundle,
        "links": per_link,
        "aggregate": aggregate,
    }


def render_chain(chain: List[IndividualBundle]) -> str:
    lines = [f"Multi-generation lineage chain ({len(chain)} bundles)"]
    lines.append("")
    for i, b in enumerate(chain):
        m = b.manifest
        indent = "  " * i
        if i == 0:
            marker = "◆"
        elif i == len(chain) - 1:
            marker = "└─"
        else:
            marker = "├─"
        lines.append(f"{indent}{marker} Gen {i}: {m.get('name', '?')}")
        lines.append(f"{indent}    id: {m['individual_id'][:32]}...")
        lines.append(f"{indent}    worlds: {len(m['world_contexts'])}, "
                     f"memory: {m['memory_entries']}")
        if m.get("inherited_from"):
            lines.append(f"{indent}    inherited_from: "
                          f"{m['inherited_from'][:32]}...")
        else:
            lines.append(f"{indent}    inherited_from: (none — origin)")
    return "\n".join(lines)


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir=None):
    from pathlib import Path
    import json as _json

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    root = Path(artifact_dir) / "multi_generation"
    root.mkdir(parents=True, exist_ok=True)

    def make_world(k_b, prng, seed=0xCAFE):
        return ScriptedWorld(
            kp=_kp(), initial_point_b=(800, 800),
            k_b=k_b, prng_seed_b=prng, rule=SIERPINSKI)

    # ---- Gen 0: grandparent lives in three worlds ----
    gp_kp = _kp()
    gp_model = TinyRNN(n_actions=3, hidden=4,
                        n_extra_inputs=0, seed=42)
    gp_memory: List[Dict] = []
    gp_sessions: List[FederatedSession] = []
    gp_worlds = [make_world(0, 0xAAAA),
                  make_world(50, 0xBBBB),
                  make_world(100, 0xCCCC)]
    for widx, n_steps, pt in [
        (0, 200, (200, 800)),
        (1, 150, (300, 700)),
        (2, 100, (400, 600)),
    ]:
        s = FederatedSession(
            individual_kp=gp_kp, model=gp_model,
            world=gp_worlds[widx], initial_point=pt,
            memory=gp_memory, rule=SIERPINSKI)
        for _ in range(n_steps):
            s.step()
        gp_sessions.append(s)
    # GP spawns Parent, then continues in world C
    parent_kp, parent_model, gp_to_parent_spawn, gp_weights = \
        spawn_federated_child(
            parent_session=gp_sessions[-1],
            child_persona="parent: child of grandparent, "
                           "bears the weights shaped by A, B, C",
            child_initial_seed=200,
        )
    for _ in range(50):
        gp_sessions[-1].step()
    gp_bundle = pack_federated_bundle(
        individual_kp=gp_kp, model=gp_model,
        sessions=gp_sessions, memory=gp_memory,
        persona="grandparent: origin of the lineage",
        initial_seed=42, name="grandparent",
    )
    gp_bundle.save(root / "gen0_grandparent")

    # ---- Gen 1: parent lives in two worlds ----
    parent_memory: List[Dict] = []
    parent_sessions: List[FederatedSession] = []
    parent_worlds = [make_world(25, 0xDDDD),
                      make_world(75, 0xEEEE)]
    for widx, n_steps, pt in [
        (0, 150, (250, 750)),
        (1, 100, (350, 650)),
    ]:
        s = FederatedSession(
            individual_kp=parent_kp, model=parent_model,
            world=parent_worlds[widx], initial_point=pt,
            memory=parent_memory, rule=SIERPINSKI)
        for _ in range(n_steps):
            s.step()
        parent_sessions.append(s)
    # Parent spawns Child, then continues in world E
    child_kp, child_model, parent_to_child_spawn, parent_weights = \
        spawn_federated_child(
            parent_session=parent_sessions[-1],
            child_persona="child: grandchild, bears weights "
                           "shaped by A, B, C, D, E",
            child_initial_seed=300,
        )
    for _ in range(50):
        parent_sessions[-1].step()
    parent_bundle = pack_federated_child(
        child_kp=parent_kp, child_model=parent_model,
        child_sessions=parent_sessions,
        child_memory=parent_memory,
        child_persona="parent: child of grandparent, "
                       "bears the weights shaped by A, B, C",
        child_initial_seed=200,
        parent_bundle=gp_bundle,
        spawn_record=gp_to_parent_spawn,
        inherited_weights=gp_weights,
        name="parent",
    )
    parent_bundle.save(root / "gen1_parent")

    # ---- Gen 2: child lives in one world ----
    child_memory: List[Dict] = []
    child_sessions: List[FederatedSession] = []
    child_worlds = [make_world(50, 0x1234)]
    s = FederatedSession(
        individual_kp=child_kp, model=child_model,
        world=child_worlds[0], initial_point=(300, 700),
        memory=child_memory, rule=SIERPINSKI)
    for _ in range(150):
        s.step()
    child_sessions.append(s)
    child_bundle = pack_federated_child(
        child_kp=child_kp, child_model=child_model,
        child_sessions=child_sessions,
        child_memory=child_memory,
        child_persona="child: grandchild, bears weights "
                       "shaped by A, B, C, D, E",
        child_initial_seed=300,
        parent_bundle=parent_bundle,
        spawn_record=parent_to_child_spawn,
        inherited_weights=parent_weights,
        name="child",
    )
    child_bundle.save(root / "gen2_child")

    # ---- Reload from disk ----
    gp_loaded = IndividualBundle.load(root / "gen0_grandparent")
    parent_loaded = IndividualBundle.load(root / "gen1_parent")
    child_loaded = IndividualBundle.load(root / "gen2_child")
    chain = [gp_loaded, parent_loaded, child_loaded]

    # ---- Verify chain ----
    verdict = verify_lineage_chain_full(chain)
    report = lineage_report(chain)

    # ---- Tampering: parent's spawn child_id ----
    tampered_parent = IndividualBundle.load(root / "gen1_parent")
    for i, rec in enumerate(tampered_parent.memory):
        if rec.get("type") == "spawn":
            body = {k: v for k, v in rec.items() if k != "sig"}
            body["child_id"] = "did:key:" + "00" * 32
            sig = parent_kp.sign(_canonical(body)).hex()
            tampered_parent.memory[i] = {**body, "sig": sig}
            break
    tampered_parent.manifest = dict(tampered_parent.manifest)
    tampered_parent.manifest["memory_root"] = _merkle_root([
        _hash({k: v for k, v in r.items() if k != "sig"})
        for r in tampered_parent.memory])
    body = {k: v for k, v in tampered_parent.manifest.items()
             if k != "sig"}
    tampered_parent.manifest["sig"] = parent_kp.sign(
        _canonical(body)).hex()
    tamper1_chain = verify_lineage_chain_full(
        [gp_loaded, tampered_parent, child_loaded])

    # ---- Tampering: child's parent_did → grandparent ----
    tampered_child = IndividualBundle.load(root / "gen2_child")
    tampered_child.manifest = dict(tampered_child.manifest)
    tampered_child.manifest["parent_did"] = \
        gp_loaded.individual_id
    body = {k: v for k, v in tampered_child.manifest.items()
             if k != "sig"}
    tampered_child.manifest["sig"] = child_kp.sign(
        _canonical(body)).hex()
    tamper2_chain = verify_lineage_chain_full(
        [gp_loaded, parent_loaded, tampered_child])

    # ---- Behavioral evidence ----
    def action_dist_in_world(memory_list, world_id, n=50):
        steps = [r for r in memory_list
                  if r.get("type") == "agent_step"
                  and r["world_id"] == world_id][:n]
        counts = [0, 0, 0]
        for r in steps:
            counts[r["action"]] += 1
        total = sum(counts) or 1
        return [c / total for c in counts]

    child_early = action_dist_in_world(
        child_loaded.memory, child_worlds[0].world_id, n=50)

    # Fresh control in the child's world with same RNG seed
    child_rng = int(_hash(
        child_loaded.manifest["individual_id"]
        + child_worlds[0].world_id).encode(),
        16) & ((1 << 32) - 1)
    control_kp = _kp()
    control_model = TinyRNN(
        n_actions=3, hidden=4, n_extra_inputs=0, seed=300)
    control_world = make_world(50, 0x1234)
    control_memory: List[Dict] = []
    control_s = FederatedSession(
        individual_kp=control_kp, model=control_model,
        world=control_world, initial_point=(300, 700),
        memory=control_memory, rule=SIERPINSKI,
        rng_seed_override=child_rng)
    for _ in range(50):
        control_s.step()
    control_dist = action_dist_in_world(
        control_memory, control_world.world_id, n=50)

    # ---- Print ----
    print("=" * 74)
    print("Multi-generation federated lineage")
    print("=" * 74)
    print()
    print(render_chain(chain))
    print()
    print("  Verification:")
    for b in report["bundles"]:
        print(f"    bundle {b['index']} ({b['name']:12s}): "
              f"basic={b['basic']}  full={b['full']}")
    for l in report["links"]:
        print(f"    link {l['from']}→{l['to']}: "
              f"{l['verified']}  ({l['reason']})")
    print(f"    chain: {verdict[0]}  ({verdict[1]})")
    print()
    print("  Tampering (each individually re-signed, "
          "so bundles alone still verify):")
    print(f"    parent's spawn.child_id → garbage:")
    print(f"      chain: {tamper1_chain[0]}  ({tamper1_chain[1]})")
    print(f"    child's parent_did → grandparent (skipping parent):")
    print(f"      chain: {tamper2_chain[0]}  ({tamper2_chain[1]})")
    print()
    print("  Behavioral evidence (child's first 50 steps in "
          "world F,")
    print("  vs. fresh individual in same world, same RNG seed):")
    print(f"    child (3-gen inherited weights):")
    print(f"      {[round(x, 2) for x in child_early]}")
    print(f"    fresh (from seed 300):")
    print(f"      {[round(x, 2) for x in control_dist]}")
    print()
    print("  What this establishes:")
    print("    - A chain of inheriting individuals verifies as a")
    print("      whole. Each bundle is self-contained; each link")
    print("      is proven by replay.")
    print("    - The verifier replays each parent to its spawn")
    print("      index — respecting world_entry RNG reseeds —")
    print("      and confirms its weights at that moment hash")
    print("      to what the child claims to have inherited.")
    print("    - Tampering with parent or child individually")
    print("      (re-signed bundles that pass their own basic and")
    print("      full) still fails chain verification: the")
    print("      ancestry links catch inconsistent lineage.")
    print("    - The child's early behavior differs measurably")
    print("      from a fresh individual with the same seed.")
    print("      The difference is the accumulated effect of")
    print("      two generations and five worlds of learning.")
    print()
    print("  Honest limit: O(N·M) verification (N generations,")
    print("  M max memory). Pairwise ancestry replays each")
    print("  parent to spawn index. For N=3, trivial; for N=10")
    print("  with long memories, caching would be needed.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'I dwell in Possibility –'")
    print("    'A fairer House than Prose –'")
    print("    'More numerous of Windows –'")
    print("    'Superior – for Doors –'")

    audit = {
        "chain_length": len(chain),
        "verification": {
            "bundles": [
                {"index": b["index"], "name": b["name"],
                 "basic": b["basic"], "full": b["full"]}
                for b in report["bundles"]
            ],
            "links": [
                {"from": l["from"], "to": l["to"],
                 "verified": l["verified"]}
                for l in report["links"]
            ],
            "aggregate": verdict[0],
        },
        "tampering": {
            "tampered_spawn_detected": not tamper1_chain[0],
            "tampered_parent_did_detected": not tamper2_chain[0],
        },
        "behavioral": {
            "child_first_50": [round(x, 3)
                                for x in child_early],
            "fresh_first_50": [round(x, 3)
                                for x in control_dist],
        },
    }
    (root / "multi_generation_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {root}/multi_generation_demo.json")
    return audit
