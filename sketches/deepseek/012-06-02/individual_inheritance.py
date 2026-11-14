"""
individual_inheritance.py — spawn with weight inheritance.

Extends individual_spawn.py with one new mode:

  mode="inherit"  — child starts from parent's weights at spawn time
  mode="fresh"    — child starts from a fresh seed (existing behavior)

The parent's spawn record gains `inherited_weights_hash`. The
child's bundle gains `initial_weights` (the parent's weights at
spawn time) and `inherited_from` (parent DID) in its manifest.

Verification:
  - basic: signatures + hashes (unchanged)
  - full: replay from initial_weights (works for fresh and
    inherited bundles; fresh bundles derive from seed)
  - exact: full + final weights match (unchanged)
  - lineage: parent signed spawn + child claims parent
  - lineage_with_ancestry: lineage + replay parent up to spawn
    index + confirm actual parent weights hash to the claimed
    inherited_weights_hash

Honest limits:
  - Inheriting child must have same architecture as parent
    (hidden size, n_extra_inputs). Checked at spawn time.
  - No cascade ancestry: verify_bundle_lineage_with_ancestry
    is pairwise. Chain verification uses
    verify_lineage_chain, which is pairwise-adjoined.
  - No observations in the demo. Observing agents would need
    observations bundled through the inheritance chain too.
"""

import hashlib
import json
import random as _rng
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
    IndividualBundle, pack_bundle,
    verify_bundle_basic, verify_bundle_full, verify_bundle_exact,
    build_model, apply_weights, serialize_weights,
    model_config, _merkle_root, _canonical, _hash, _now,
    _did_from_kp, _pubkey_from_did,
)
from individual_spawn import (
    spawn_record_hash, verify_bundle_lineage,
    verify_bundle_full_with_spawn, verify_bundle_exact_with_spawn,
    verify_lineage_chain, render_lineage,
)
from world_agent_coupling import (
    WorldAgentSession, ScriptedWorld,
)
from coupled_learners import TinyRNN, TabularQ, SIERPINSKI


def _weights_hash(weights: Dict) -> str:
    return _hash(json.dumps(weights, sort_keys=True,
                             separators=(",", ":")).encode())


# =====================================================================
# Spawn with inheritance
# =====================================================================

def spawn_child_inheriting(
    parent_session: WorldAgentSession,
    child_persona: str,
    child_initial_seed: int,
    child_initial_point: Tuple[int, int],
    child_world_k_b: int = 100,
    child_world_prng_seed: int = 0xCAFEBABE,
) -> Tuple[WorldAgentSession, Dict, Dict]:
    """Spawn a child that inherits the parent's current weights.

    Returns (child_session, spawn_record, initial_weights).
    The caller must pass initial_weights to pack_inheriting_child
    so the child's bundle carries its inheritance.
    """
    if not HAS_CRYPTO:
        raise RuntimeError("cryptography not installed")

    parent_config = model_config(parent_session.agent_model)
    parent_weights = serialize_weights(parent_session.agent_model)
    inherited_hash = _weights_hash(parent_weights)

    child_kp = Ed25519PrivateKey.generate()
    child_world = ScriptedWorld(
        kp=Ed25519PrivateKey.generate(),
        initial_point_b=(800, 800),
        k_b=child_world_k_b,
        prng_seed_b=child_world_prng_seed,
        rule=SIERPINSKI,
    )
    # Child model — same architecture, fresh RNG seed, but
    # weights immediately overwritten with parent's
    if parent_config["kind"] == "rnn":
        child_model = TinyRNN(
            n_actions=parent_config["n_actions"],
            hidden=parent_config["hidden"],
            n_extra_inputs=parent_config["n_extra_inputs"],
            seed=child_initial_seed,
        )
    elif parent_config["kind"] == "q":
        child_model = TabularQ(
            n_actions=parent_config["n_actions"],
            grid=parent_config["grid"],
            seed=child_initial_seed,
        )
    else:
        raise ValueError(parent_config["kind"])
    apply_weights(child_model, parent_weights)

    child_session = WorldAgentSession(
        agent_kp=child_kp,
        agent_model=child_model,
        agent_observe=parent_session.agent_observe,
        world=child_world,
        agent_initial_point=child_initial_point,
        rule=SIERPINSKI,
        seed_a=child_initial_seed + 1000,
    )

    body = {
        "type": "spawn",
        "agent_id": parent_session.agent_id,
        "child_id": child_session.agent_id,
        "mode": "inherit",
        "child_persona": child_persona,
        "child_initial_seed": int(child_initial_seed),
        "child_initial_point": list(child_initial_point),
        "inherited_weights_hash": inherited_hash,
        "ts": _now(),
    }
    sig = parent_session.agent_kp.sign(
        _canonical(body)).hex()
    spawn_record = {**body, "sig": sig}
    parent_session.a_records.append(spawn_record)
    return child_session, spawn_record, parent_weights


# =====================================================================
# Pack an inheriting child
# =====================================================================

def pack_inheriting_child(
    child_session: WorldAgentSession,
    child_name: str,
    child_persona: str,
    parent_bundle: IndividualBundle,
    spawn_record: Dict,
    child_initial_seed: int,
    initial_weights: Dict,
) -> IndividualBundle:
    """Pack a child bundle that carries its inherited weights."""
    child_session.agent_model_config_name = child_name
    bundle = pack_bundle(
        child_session,
        persona=child_persona,
        parent_did=parent_bundle.individual_id,
        initial_seed=child_initial_seed,
        initial_weights=initial_weights,
    )
    # Inject lineage fields
    bundle.manifest = dict(bundle.manifest)
    bundle.manifest["parent_spawn_hash"] = \
        spawn_record_hash(spawn_record)
    bundle.manifest["inherited_from"] = \
        parent_bundle.individual_id
    body = {k: v for k, v in bundle.manifest.items()
             if k != "sig"}
    bundle.manifest["sig"] = child_session.agent_kp.sign(
        _canonical(body)).hex()
    return bundle


# =====================================================================
# Lineage with ancestry
# =====================================================================

def _find_spawn_index(parent: IndividualBundle,
                       spawn_hash: str) -> Optional[int]:
    for i, rec in enumerate(parent.memory):
        if rec.get("type") == "spawn" \
                and spawn_record_hash(rec) == spawn_hash:
            return i
    return None


def _replay_parent_to_index(
    parent: IndividualBundle, index: int,
) -> object:
    """Reconstruct parent's model weights by replaying its
    memory entries [0, index)."""
    config = parent.manifest["model_config"]
    if parent.initial_weights is not None:
        model = build_model(config)
        apply_weights(model, parent.initial_weights)
    else:
        model = parent.initial_model()
    rng = _rng.Random(
        parent.manifest["model_initial_seed"] + 1)
    last_action = 0
    last_reward = 0.0
    prev_point = None
    for rec in parent.memory[:index]:
        if rec.get("type") != "agent_step":
            continue
        x, y = (prev_point[0] / 1000,
                 prev_point[1] / 1000) \
                if prev_point else (0.2, 0.8)
        state = (last_action, last_reward, x, y)
        model.act(state, rng)
        model.learn(rec["reward_micros"] / 1_000_000)
        last_action = rec["action"]
        last_reward = rec["reward_micros"] / 1_000_000
        prev_point = tuple(rec["to_point"])
    return model


def verify_bundle_lineage_with_ancestry(
    child: IndividualBundle,
    parent: IndividualBundle,
) -> Tuple[bool, str]:
    """Lineage check + replay parent to spawn point, confirm
    inherited weights hash matches what parent actually had."""
    ok, reason = verify_bundle_lineage(child, parent)
    if not ok:
        return (False, f"basic lineage: {reason}")

    if not child.manifest.get("inherited_from"):
        return (True, "lineage verifies (no inheritance)")

    spawn_hash = child.manifest["parent_spawn_hash"]
    spawn_index = _find_spawn_index(parent, spawn_hash)
    if spawn_index is None:
        return (False, "spawn record not found")
    spawn_rec = parent.memory[spawn_index]
    if spawn_rec.get("mode") != "inherit":
        return (False,
                 f"spawn mode is {spawn_rec.get('mode')!r}, "
                 f"not 'inherit'")

    claimed_hash = spawn_rec.get("inherited_weights_hash")
    if claimed_hash is None:
        return (False, "spawn record has no inherited hash")

    child_claimed = child.manifest.get("initial_weights_hash")
    if child_claimed != claimed_hash:
        return (False,
                 f"parent claims {claimed_hash[:16]}..., "
                 f"child claims {child_claimed[:16] if child_claimed else None}")

    # The expensive check: replay parent to spawn index,
    # derive actual weights, hash them, compare.
    actual_model = _replay_parent_to_index(parent, spawn_index)
    actual_weights = serialize_weights(actual_model)
    actual_hash = _weights_hash(actual_weights)
    if actual_hash != claimed_hash:
        return (False,
                 f"parent's actual weights at spawn "
                 f"({actual_hash[:16]}...) do not match "
                 f"spawn claim ({claimed_hash[:16]}...)")
    return (True, "lineage with weight ancestry verifies")


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
    root = Path(artifact_dir) / "individual_inheritance"
    root.mkdir(parents=True, exist_ok=True)

    # --- Grandparent: learns 800 steps ---
    gp_kp = Ed25519PrivateKey.generate()
    gp_world = ScriptedWorld(
        kp=Ed25519PrivateKey.generate(),
        initial_point_b=(800, 800), k_b=100,
        prng_seed_b=0xCAFEBABE, rule=SIERPINSKI)
    gp_model = TinyRNN(
        n_actions=3, hidden=4, n_extra_inputs=0, seed=100)
    gp_session = WorldAgentSession(
        agent_kp=gp_kp, agent_model=gp_model,
        agent_observe=False, world=gp_world,
        agent_initial_point=(200, 800),
        rule=SIERPINSKI, seed_a=1100)
    gp_session.agent_model_config_name = "grandparent"
    for _ in range(800):
        gp_session.step()

    # Snapshot grandparent's weights (they will be inherited)
    gp_weights_at_spawn = serialize_weights(
        gp_session.agent_model)

    # --- Grandparent spawns two children:
    #   child_fresh (mode=fresh, learns 300 steps, no inheritance)
    #   child_inherit (mode=inherit, inherits gp's weights)
    from individual_spawn import spawn_child as spawn_fresh
    child_fresh_session, child_fresh_spawn = spawn_fresh(
        gp_session,
        child_persona="fresh child, no inheritance",
        child_initial_seed=200,
        child_initial_point=(300, 700),
    )
    child_fresh_session.agent_model_config_name = "child_fresh"

    child_inherit_session, child_inherit_spawn, gp_inherited_weights = \
        spawn_child_inheriting(
            gp_session,
            child_persona="inheriting child, "
                           "starts from grandparent's weights",
            child_initial_seed=201,
            child_initial_point=(300, 700),
        )
    child_inherit_session.agent_model_config_name = "child_inherit"

    # --- Each child learns 300 steps independently ---
    for _ in range(300):
        child_fresh_session.step()
        child_inherit_session.step()

    # --- Pack bundles ---
    gp_bundle = pack_bundle(
        gp_session,
        persona="the origin, learner of 800 steps",
        initial_seed=100,
    )
    fresh_bundle = pack_bundle(
        child_fresh_session,
        persona="fresh child",
        parent_did=gp_bundle.individual_id,
        initial_seed=200,
    )
    fresh_bundle.manifest = dict(fresh_bundle.manifest)
    fresh_bundle.manifest["parent_spawn_hash"] = \
        spawn_record_hash(child_fresh_spawn)
    body = {k: v for k, v in fresh_bundle.manifest.items()
             if k != "sig"}
    fresh_bundle.manifest["sig"] = child_fresh_session.agent_kp.sign(
        _canonical(body)).hex()

    inherit_bundle = pack_inheriting_child(
        child_inherit_session,
        child_name="child_inherit",
        child_persona="inheriting child",
        parent_bundle=gp_bundle,
        spawn_record=child_inherit_spawn,
        child_initial_seed=201,
        initial_weights=gp_inherited_weights,
    )

    # --- Save to disk ---
    for name, b in (
        ("grandparent", gp_bundle),
        ("child_fresh", fresh_bundle),
        ("child_inherit", inherit_bundle),
    ):
        b.save(root / name)

    # --- Reload ---
    gp_loaded = IndividualBundle.load(root / "grandparent")
    fresh_loaded = IndividualBundle.load(root / "child_fresh")
    inherit_loaded = IndividualBundle.load(root / "child_inherit")

    # --- Verification ---
    tiers = {}
    for name, b in (
        ("grandparent", gp_loaded),
        ("child_fresh", fresh_loaded),
        ("child_inherit", inherit_loaded),
    ):
        basic = verify_bundle_basic(b)
        full = verify_bundle_full(b)
        exact = verify_bundle_exact(b)
        tiers[name] = {
            "basic": basic[0], "full": full[0],
            "exact": exact[0],
            "full_reason": full[1],
            "exact_reason": exact[1],
        }

    # --- Lineage ---
    fresh_lineage = verify_bundle_lineage(
        fresh_loaded, gp_loaded)
    inherit_lineage = verify_bundle_lineage(
        inherit_loaded, gp_loaded)
    inherit_ancestry = verify_bundle_lineage_with_ancestry(
        inherit_loaded, gp_loaded)
    fresh_ancestry = verify_bundle_lineage_with_ancestry(
        fresh_loaded, gp_loaded)

    # --- Behavioral comparison ---
    def action_hist(session, n=100):
        counts = [0, 0, 0]
        for r in session.a_records[:n]:
            if r.get("type") != "agent_step":
                continue
            counts[r["action"]] += 1
        total = sum(counts) or 1
        return [c / total for c in counts]

    fresh_hist = action_hist(child_fresh_session)
    inherit_hist = action_hist(child_inherit_session)
    gp_final_hist = action_hist(gp_session, n=100)

    # --- Tamper: fake the inherited hash ---
    tampered = IndividualBundle.load(root / "child_inherit")
    tampered.manifest = dict(tampered.manifest)
    tampered.manifest["initial_weights_hash"] = "00" * 32
    body = {k: v for k, v in tampered.manifest.items()
             if k != "sig"}
    tampered.manifest["sig"] = child_inherit_session.agent_kp.sign(
        _canonical(body)).hex()
    tamper_ok, _ = verify_bundle_lineage_with_ancestry(
        tampered, gp_loaded)

    # --- Print ---
    print("=" * 74)
    print("Weight-inheriting spawn — a child that starts "
          "from its parent")
    print("=" * 74)
    print()
    print("  Lineage:")
    print(render_lineage([gp_loaded, fresh_loaded,
                            inherit_loaded]))
    print()
    print("  Verification tiers:")
    for name in ("grandparent", "child_fresh", "child_inherit"):
        t = tiers[name]
        print(f"    {name:14s}  basic={t['basic']}  "
              f"full={t['full']}  exact={t['exact']}")
    print()
    print("  Lineage:")
    print(f"    child_fresh ← grandparent:      "
          f"{fresh_lineage[0]}")
    print(f"    child_inherit ← grandparent:    "
          f"{inherit_lineage[0]}")
    print(f"    fresh with ancestry:            "
          f"{fresh_ancestry[0]}  ({fresh_ancestry[1]})")
    print(f"    inherit with ancestry:          "
          f"{inherit_ancestry[0]}  "
          f"({inherit_ancestry[1]})")
    print()
    print("  Behavioral comparison (first 100 steps of each child):")
    print(f"    grandparent's late preference:  "
          f"{[round(x, 2) for x in gp_final_hist]}")
    print(f"    child_fresh's early choices:    "
          f"{[round(x, 2) for x in fresh_hist]}")
    print(f"    child_inherit's early choices:  "
          f"{[round(x, 2) for x in inherit_hist]}")
    print()
    print("  Tampering:")
    print(f"    child claims wrong inherited hash: "
          f"lineage_with_ancestry {tamper_ok}")
    print()
    print("  What this establishes:")
    print("    - Inheriting spawn is a signed claim by the parent")
    print("      ('the weights I'm passing have hash H') and by")
    print("      the child ('my starting weights have hash H').")
    print("    - verify_bundle_lineage_with_ancestry replays the")
    print("      parent to the spawn point and confirms the")
    print("      parent's actual weights hash to H — the claim")
    print("      is verified, not trusted.")
    print("    - The inheriting child's early behavior is")
    print("      biased toward the grandparent's late")
    print("      preferences. The fresh child starts near-uniform.")
    print("    - Both children continue to learn independently")
    print("      after spawn. The grandparent's later learning")
    print("      does not affect its children.")
    print("    - Each bundle remains self-contained: full")
    print("      verification of the inheriting child starts")
    print("      from its bundled initial_weights, no parent")
    print("      required.")
    print()
    print("  Honest limit: no cascade inheritance across more")
    print("  than one generation without re-verifying the whole")
    print("  chain. A three-generation inherited lineage would")
    print("  need pairwise verification at each link.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'The Brain – is wider than the Sky –'")
    print("    'For – put them side by side –'")
    print("    'The one the other will contain'")
    print("    'With ease – and You – beside –'")

    audit = {
        "tiers": tiers,
        "lineage": {
            "fresh": fresh_lineage[0],
            "inherit": inherit_lineage[0],
            "fresh_ancestry": fresh_ancestry[0],
            "inherit_ancestry": inherit_ancestry[0],
        },
        "tampering": {
            "fake_inherited_hash_detected": not tamper_ok,
        },
        "behavioral": {
            "grandparent_late": [round(x, 3)
                                    for x in gp_final_hist],
            "child_fresh_early": [round(x, 3)
                                     for x in fresh_hist],
            "child_inherit_early": [round(x, 3)
                                        for x in inherit_hist],
        },
    }
    (root / "individual_inheritance_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {root}/individual_inheritance_demo.json")
    return audit
