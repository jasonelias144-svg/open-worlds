"""
federated_spawn.py — a federated individual spawns an inheriting
child.

The parent lived in worlds A, B, C (own log, one DID). It spawns
a child in world C. The child inherits the parent's weights at
spawn time — weights shaped by A, B, and C — and starts its own
life in worlds D, E.

Verification composes:
  - federated basic on both bundles (identity, memory chain,
    world_contexts match world_entry records)
  - federated full on both bundles (replay respects RNG reseed
    at each world boundary)
  - lineage (parent signed spawn, child claims parent)
  - ancestry (replay parent to spawn index, confirm inherited
    weights hash matches parent's actual weights there)

The replay in ancestry must handle world_entry records: they
reseed the RNG, set the initial point, and don't advance the
model. Spawn records are skipped (they don't advance either).

Honest limits:
  - Child lives in fresh worlds. Parent and child never coexist
    in the same world instance.
  - No observation mode (bundles use no observations).
  - Ancestry is pairwise. A three-generation inherited chain
    needs pairwise verification at each link.
"""

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
    IndividualBundle, serialize_weights, build_model,
    apply_weights, model_config,
    _canonical, _hash, _now, _did_from_kp, _pubkey_from_did,
)
from individual_spawn import (
    spawn_record_hash, verify_bundle_lineage,
)
from federated_bundle import (
    FederatedSession, pack_federated_bundle,
    verify_federated_basic, verify_federated_full,
    verify_federated_with_world_logs,
    _start_model, SCALE,
)
from world_agent_coupling import ScriptedWorld
from coupled_learners import TinyRNN, TabularQ, SIERPINSKI


def _weights_hash(weights: Dict) -> str:
    return _hash(json.dumps(weights, sort_keys=True,
                             separators=(",", ":")).encode())


def _find_spawn_index(parent: IndividualBundle,
                       spawn_hash: str) -> Optional[int]:
    for i, rec in enumerate(parent.memory):
        if rec.get("type") == "spawn" \
                and spawn_record_hash(rec) == spawn_hash:
            return i
    return None


# =====================================================================
# Spawn
# =====================================================================

def spawn_federated_child(
    parent_session: FederatedSession,
    child_persona: str,
    child_initial_seed: int,
) -> Tuple[object, object, Dict, Dict]:
    """Create a child session-less: keypair, model, and the
    spawn record already appended to the parent's memory.

    Returns (child_kp, child_model, spawn_record,
    inherited_weights). The caller creates FederatedSessions
    for the child in its own worlds.
    """
    if not HAS_CRYPTO:
        raise RuntimeError("cryptography not installed")

    parent_kp = parent_session.individual_kp
    parent_id = parent_session.individual_id
    parent_config = model_config(parent_session.model)
    parent_weights = serialize_weights(parent_session.model)
    inherited_hash = _weights_hash(parent_weights)

    child_kp = Ed25519PrivateKey.generate()
    child_id = _did_from_kp(child_kp)
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

    body = {
        "type": "spawn",
        "agent_id": parent_id,
        "child_id": child_id,
        "mode": "inherit_federated",
        "world_id": parent_session.world.world_id,
        "child_persona": child_persona,
        "child_initial_seed": int(child_initial_seed),
        "inherited_weights_hash": inherited_hash,
        "ts": _now(),
    }
    sig = parent_kp.sign(_canonical(body)).hex()
    spawn_record = {**body, "sig": sig}
    parent_session.memory.append(spawn_record)
    return child_kp, child_model, spawn_record, parent_weights


# =====================================================================
# Pack
# =====================================================================

def pack_federated_child(
    child_kp,
    child_model,
    child_sessions: List[FederatedSession],
    child_memory: List[Dict],
    child_persona: str,
    child_initial_seed: int,
    parent_bundle: IndividualBundle,
    spawn_record: Dict,
    inherited_weights: Dict,
    name: str = "child",
) -> IndividualBundle:
    bundle = pack_federated_bundle(
        individual_kp=child_kp,
        model=child_model,
        sessions=child_sessions,
        memory=child_memory,
        persona=child_persona,
        initial_seed=child_initial_seed,
        initial_weights=inherited_weights,
        name=name,
    )
    # Add lineage fields to manifest, re-sign
    bundle.manifest = dict(bundle.manifest)
    bundle.manifest["parent_did"] = parent_bundle.individual_id
    bundle.manifest["parent_spawn_hash"] = \
        spawn_record_hash(spawn_record)
    bundle.manifest["inherited_from"] = parent_bundle.individual_id
    body = {k: v for k, v in bundle.manifest.items()
             if k != "sig"}
    bundle.manifest["sig"] = child_kp.sign(
        _canonical(body)).hex()
    return bundle


# =====================================================================
# Replay to spawn index (respects world_entry RNG reseeds)
# =====================================================================

def _replay_federated_to_index(
    parent_bundle: IndividualBundle, index: int,
) -> Tuple[Optional[object], str]:
    """Reconstruct the parent's model by replaying memory[0..index).
    Handles world_entry records (RNG reseed) and spawn records
    (skipped)."""
    model = _start_model(parent_bundle)
    individual_id = parent_bundle.manifest["individual_id"]
    rng = None
    prev_point = None
    last_action = 0
    last_reward = 0.0
    for i, rec in enumerate(parent_bundle.memory[:index]):
        typ = rec.get("type")
        if typ == "world_entry":
            prev_point = tuple(rec["initial_point"])
            seed_int = int(_hash(
                individual_id + rec["world_id"]).encode(),
                16) & ((1 << 32) - 1)
            rng = _rng.Random(seed_int)
            continue
        if typ != "agent_step":
            continue  # skip spawn and any future non-step types
        if prev_point is None or rng is None:
            return (None,
                     f"memory[{i}]: step with no preceding "
                     f"world_entry")
        x, y = prev_point[0] / SCALE, prev_point[1] / SCALE
        state = (last_action, last_reward, x, y)
        expected = model.act(state, rng)
        if expected != rec["action"]:
            return (None,
                     f"memory[{i}]: replay mismatch "
                     f"({expected} != {rec['action']})")
        model.learn(rec["reward_micros"] / 1_000_000)
        last_action = rec["action"]
        last_reward = rec["reward_micros"] / 1_000_000
        prev_point = tuple(rec["to_point"])
    return (model, "ok")


# =====================================================================
# Ancestry verification
# =====================================================================

def verify_federated_spawn_ancestry(
    child_bundle: IndividualBundle,
    parent_bundle: IndividualBundle,
) -> Tuple[bool, str]:
    """Lineage + replay parent to spawn index + confirm
    inherited weights hash matches parent's actual weights."""
    ok, reason = verify_federated_basic(child_bundle)
    if not ok:
        return (False, f"child basic: {reason}")
    ok, reason = verify_federated_basic(parent_bundle)
    if not ok:
        return (False, f"parent basic: {reason}")

    ok, reason = verify_bundle_lineage(child_bundle, parent_bundle)
    if not ok:
        return (False, f"lineage: {reason}")

    if not child_bundle.manifest.get("inherited_from"):
        return (True, "lineage verifies (no inheritance)")

    spawn_hash = child_bundle.manifest["parent_spawn_hash"]
    spawn_index = _find_spawn_index(parent_bundle, spawn_hash)
    if spawn_index is None:
        return (False, "spawn record not found in parent")
    spawn_rec = parent_bundle.memory[spawn_index]
    if spawn_rec.get("mode") != "inherit_federated":
        return (False,
                 f"spawn mode is {spawn_rec.get('mode')!r}, "
                 f"not 'inherit_federated'")

    claimed_hash = spawn_rec.get("inherited_weights_hash")
    if claimed_hash is None:
        return (False, "spawn record has no inherited hash")
    child_claimed = child_bundle.manifest.get(
        "initial_weights_hash")
    if child_claimed != claimed_hash:
        return (False,
                 f"child claims "
                 f"{str(child_claimed)[:16] if child_claimed else None}..., "
                 f"parent claims {claimed_hash[:16]}...")

    actual_model, reason = _replay_federated_to_index(
        parent_bundle, spawn_index)
    if actual_model is None:
        return (False, f"replay: {reason}")
    actual_weights = serialize_weights(actual_model)
    actual_hash = _weights_hash(actual_weights)
    if actual_hash != claimed_hash:
        return (False,
                 f"parent's actual weights at spawn "
                 f"({actual_hash[:16]}...) do not match "
                 f"spawn claim ({claimed_hash[:16]}...)")
    return (True,
             f"federated spawn ancestry verifies "
             f"(replayed {spawn_index} records)")


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
    root = Path(artifact_dir) / "federated_spawn"
    root.mkdir(parents=True, exist_ok=True)

    # --- Parent: lives in three worlds ---
    parent_kp = Ed25519PrivateKey.generate()
    parent_model = TinyRNN(
        n_actions=3, hidden=4, n_extra_inputs=0, seed=42)
    parent_memory: List[Dict] = []
    parent_sessions: List[FederatedSession] = []

    parent_worlds = [
        ScriptedWorld(
            kp=Ed25519PrivateKey.generate(),
            initial_point_b=(800, 800), k_b=0,
            prng_seed_b=0xAAAA, rule=SIERPINSKI),
        ScriptedWorld(
            kp=Ed25519PrivateKey.generate(),
            initial_point_b=(800, 800), k_b=50,
            prng_seed_b=0xBBBB, rule=SIERPINSKI),
        ScriptedWorld(
            kp=Ed25519PrivateKey.generate(),
            initial_point_b=(800, 800), k_b=100,
            prng_seed_b=0xCCCC, rule=SIERPINSKI),
    ]
    parent_steps = [(0, 200, (200, 800)),
                     (1, 150, (300, 700)),
                     (2, 100, (400, 600))]

    last_parent_session = None
    for widx, n_steps, init_pt in parent_steps:
        s = FederatedSession(
            individual_kp=parent_kp,
            model=parent_model,
            world=parent_worlds[widx],
            initial_point=init_pt,
            memory=parent_memory,
            rule=SIERPINSKI,
        )
        for _ in range(n_steps):
            s.step()
        parent_sessions.append(s)
        last_parent_session = s

    # --- Spawn happens at the moment above: 450 agent_steps done ---
    parent_spawn_index = len(parent_memory)
    child_kp, child_model, spawn_record, inherited_weights = \
        spawn_federated_child(
            parent_session=last_parent_session,
            child_persona="child inheriting multi-world experience",
            child_initial_seed=200,
        )
    # Parent continues in world C
    for _ in range(100):
        last_parent_session.step()

    # --- Pack parent ---
    parent_bundle = pack_federated_bundle(
        individual_kp=parent_kp, model=parent_model,
        sessions=parent_sessions, memory=parent_memory,
        persona="federated parent, lived in three worlds",
        initial_seed=42, name="federated_parent",
    )
    parent_bundle.save(root / "parent")
    parent_loaded = IndividualBundle.load(root / "parent")

    # --- Child: lives in worlds D, E ---
    child_memory: List[Dict] = []
    child_sessions: List[FederatedSession] = []
    child_worlds = [
        ScriptedWorld(
            kp=Ed25519PrivateKey.generate(),
            initial_point_b=(800, 800), k_b=25,
            prng_seed_b=0xDDDD, rule=SIERPINSKI),
        ScriptedWorld(
            kp=Ed25519PrivateKey.generate(),
            initial_point_b=(800, 800), k_b=75,
            prng_seed_b=0xEEEE, rule=SIERPINSKI),
    ]
    for widx, n_steps, init_pt in [(0, 300, (250, 750)),
                                     (1, 200, (350, 650))]:
        s = FederatedSession(
            individual_kp=child_kp,
            model=child_model,
            world=child_worlds[widx],
            initial_point=init_pt,
            memory=child_memory,
            rule=SIERPINSKI,
        )
        for _ in range(n_steps):
            s.step()
        child_sessions.append(s)

    child_bundle = pack_federated_child(
        child_kp=child_kp, child_model=child_model,
        child_sessions=child_sessions,
        child_memory=child_memory,
        child_persona="child inheriting multi-world experience",
        child_initial_seed=200,
        parent_bundle=parent_loaded,
        spawn_record=spawn_record,
        inherited_weights=inherited_weights,
        name="federated_child",
    )
    child_bundle.save(root / "child")
    child_loaded = IndividualBundle.load(root / "child")

    # --- Verification ---
    parent_basic = verify_federated_basic(parent_loaded)
    parent_full = verify_federated_full(parent_loaded)
    child_basic = verify_federated_basic(child_loaded)
    child_full = verify_federated_full(child_loaded)
    ancestry = verify_federated_spawn_ancestry(
        child_loaded, parent_loaded)

    # --- Behavioral comparison at child's world D ---
    def first_n_in_world(memory_list, world_id, n=50):
        steps = [r for r in memory_list
                  if r.get("type") == "agent_step"
                  and r["world_id"] == world_id][:n]
        counts = [0, 0, 0]
        for r in steps:
            counts[r["action"]] += 1
        total = sum(counts) or 1
        return [c / total for c in counts]

    child_initial_dist = first_n_in_world(
        child_loaded.memory, child_worlds[0].world_id)

    # Fresh control: same RNG seed as the child in world D,
    # fresh weights. Isolates the inherited-weights effect.
    child_world_d_rng = int(_hash(
        child_loaded.manifest["individual_id"]
        + child_worlds[0].world_id).encode(),
        16) & ((1 << 32) - 1)
    control_kp = Ed25519PrivateKey.generate()
    control_model = TinyRNN(
        n_actions=3, hidden=4, n_extra_inputs=0, seed=200)
    control_world = ScriptedWorld(
        kp=Ed25519PrivateKey.generate(),
        initial_point_b=(800, 800), k_b=25,
        prng_seed_b=0xDDDD, rule=SIERPINSKI,
    )
    control_memory: List[Dict] = []
    control_session = FederatedSession(
        individual_kp=control_kp,
        model=control_model,
        world=control_world,
        initial_point=(250, 750),
        memory=control_memory,
        rule=SIERPINSKI,
        rng_seed_override=child_world_d_rng,
    )
    for _ in range(50):
        control_session.step()
    control_dist = first_n_in_world(
        control_memory, control_world.world_id, n=50)

    # --- Tamper: change spawn's inherited hash ---
    tampered_parent = IndividualBundle.load(root / "parent")
    for i, rec in enumerate(tampered_parent.memory):
        if rec.get("type") == "spawn":
            body = {k: v for k, v in rec.items() if k != "sig"}
            body["inherited_weights_hash"] = "00" * 32
            sig = parent_kp.sign(_canonical(body)).hex()
            tampered_parent.memory[i] = {**body, "sig": sig}
            break
    # Recompute memory_root in manifest and re-sign
    tampered_parent.manifest = dict(tampered_parent.manifest)
    from individual_bundle import _merkle_root
    tampered_parent.manifest["memory_root"] = _merkle_root([
        _hash({k: v for k, v in r.items() if k != "sig"})
        for r in tampered_parent.memory])
    body = {k: v for k, v in tampered_parent.manifest.items()
             if k != "sig"}
    tampered_parent.manifest["sig"] = parent_kp.sign(
        _canonical(body)).hex()
    tamper_ancestry_ok, _ = verify_federated_spawn_ancestry(
        child_loaded, tampered_parent)

    # --- Print ---
    print("=" * 74)
    print("Federated spawn — an inherited child of a multi-world"
          " parent")
    print("=" * 74)
    print()
    print(f"  Parent: {parent_loaded.individual_id[:32]}...")
    print(f"    worlds: {len(parent_sessions)}  "
          f"memory: {len(parent_loaded.memory)} entries")
    print(f"    spawn at memory index: {parent_spawn_index}")
    print()
    print(f"  Child:  {child_loaded.individual_id[:32]}...")
    print(f"    worlds: {len(child_sessions)}  "
          f"memory: {len(child_loaded.memory)} entries")
    print(f"    parent_did: {child_loaded.manifest['parent_did'][:32]}...")
    print(f"    inherited weights hash: "
          f"{child_loaded.manifest['initial_weights_hash'][:16]}...")
    print()
    print("  Verification:")
    print(f"    parent federated basic: {parent_basic[0]}  "
          f"({parent_basic[1]})")
    print(f"    parent federated full:  {parent_full[0]}  "
          f"({parent_full[1]})")
    print(f"    child  federated basic: {child_basic[0]}  "
          f"({child_basic[1]})")
    print(f"    child  federated full:  {child_full[0]}  "
          f"({child_full[1]})")
    print(f"    federated ancestry:     {ancestry[0]}  "
          f"({ancestry[1]})")
    print()
    print("  Behavioral comparison (child's first 50 steps in"
          " world D,")
    print("  vs. fresh individual in same world, same RNG seed):")
    print(f"    child (inherited multi-world weights):")
    print(f"      {[round(x, 2) for x in child_initial_dist]}")
    print(f"    fresh (from seed 200):")
    print(f"      {[round(x, 2) for x in control_dist]}")
    print()
    print("  Tampering:")
    print(f"    spawn claim tampered (inherited hash → 00…):")
    print(f"      ancestry verifies: {tamper_ancestry_ok}")
    print()
    print("  What this establishes:")
    print("    - An individual whose model has been shaped by")
    print("      three worlds can spawn a child that starts")
    print("      pre-adapted to those worlds.")
    print("    - The parent's spawn record (with "
          "inherited_weights_hash)")
    print("      and the child's initial_weights_hash are mutual")
    print("      claims. The verifier confirms they match.")
    print("    - The verifier then replays the parent to the")
    print("      spawn index — respecting world_entry RNG")
    print("      reseeds — and confirms the parent's actual")
    print("      weights at that moment hash to the claimed")
    print("      value. The claim is not trusted.")
    print("    - After spawn, parent and child learn")
    print("      independently. The child's full federated")
    print("      verification works self-contained.")
    print("    - Tampering with the spawn record's inherited")
    print("      hash breaks ancestry: the replayed parent")
    print("      weights don't match.")
    print()
    print("  Honest limit: pairwise verification. A three-")
    print("  generation inherited chain needs ancestry checks at")
    print("  each link.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'I dwell in Possibility –'")
    print("    'A fairer House than Prose –'")
    print("    'More numerous of Windows –'")
    print("    'Superior – for Doors –'")

    audit = {
        "parent_id": parent_loaded.individual_id,
        "child_id": child_loaded.individual_id,
        "parent_spawn_index": parent_spawn_index,
        "verification": {
            "parent_basic": parent_basic[0],
            "parent_full": parent_full[0],
            "child_basic": child_basic[0],
            "child_full": child_full[0],
            "ancestry": ancestry[0],
        },
        "behavioral": {
            "child_first_50_world_d":
                [round(x, 3) for x in child_initial_dist],
            "fresh_first_50_world_d":
                [round(x, 3) for x in control_dist],
        },
        "tampering": {
            "tampered_spawn_detected":
                not tamper_ancestry_ok,
        },
    }
    (root / "federated_spawn_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {root}/federated_spawn_demo.json")
    return audit
