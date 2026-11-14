"""
individual_spawn.py — an individual that creates an individual.

A spawn is a signed record in the parent's memory chain:

    {
      "type": "spawn",
      "agent_id": <parent>,
      "child_id": <child's new DID>,
      "child_persona": <str>,
      "child_initial_seed": <int>,
      "child_initial_point": [x, y],
      "ts": ...,
      "sig": <parent's signature>
    }

The child's manifest carries two extra fields:

    "parent_did": <parent>,
    "parent_spawn_hash": <hash of the parent's spawn record body>

verify_bundle_lineage(child, parent):
  - child.parent_did == parent.individual_id
  - parent's memory contains a record whose body-hash
    matches child.parent_spawn_hash
  - that record is type=spawn, and its child_id matches
    child.individual_id
  - both bundles pass basic verification

verify_bundle_full (updated):
  - during replay, skip records whose type != "agent_step"
    (spawns and other non-step entries don't advance the
    model; last_action/last_reward persist across them)

verify_lineage_chain([b1, b2, b3, ...]):
  - every adjacent pair passes verify_bundle_lineage

Honest limits:
  - No weight inheritance. Child starts fresh from its own
    seed. A future "inheriting spawn" would carry parent
    weights in the child's bundle; that changes what
    verify_bundle_full can do.
  - Spawn is unconditional. The world can't refuse. Future
    spawn keys would gate it.
  - The child gets its own world instance. Shared-world
    spawning would require shared world state; not built.
  - No recursive lineage proof — verify_lineage_chain
    walks the chain, but a single bundle doesn't prove
    its full ancestry without all bundles present.
"""

import hashlib
import json
from dataclasses import dataclass
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
    _merkle_root, _canonical, _hash, _now,
    _did_from_kp, _pubkey_from_did,
)
from world_agent_coupling import (
    WorldAgentSession, ScriptedWorld,
)
from coupled_learners import TinyRNN, SIERPINSKI


# =====================================================================
# Spawn
# =====================================================================

def spawn_child(
    parent_session: WorldAgentSession,
    child_persona: str,
    child_initial_seed: int,
    child_initial_point: Tuple[int, int],
    child_world_k_b: int = 100,
    child_world_prng_seed: int = 0xCAFEBABE,
) -> Tuple[WorldAgentSession, Dict]:
    """Create a child session and record the spawn in the parent's
    memory.

    The child gets:
      - fresh keypair (own DID)
      - fresh model from child_initial_seed
      - fresh world instance (own B-side identity)

    Returns (child_session, spawn_record). The spawn_record is
    already appended to parent_session.a_records.
    """
    if not HAS_CRYPTO:
        raise RuntimeError("cryptography not installed")

    child_kp = Ed25519PrivateKey.generate()
    child_world = ScriptedWorld(
        kp=Ed25519PrivateKey.generate(),
        initial_point_b=(800, 800),
        k_b=child_world_k_b,
        prng_seed_b=child_world_prng_seed,
        rule=SIERPINSKI,
    )
    n_extra = 3 if parent_session.agent_observe else 0
    child_model = TinyRNN(
        n_actions=3, hidden=4,
        n_extra_inputs=n_extra,
        seed=child_initial_seed,
    )
    child_session = WorldAgentSession(
        agent_kp=child_kp,
        agent_model=child_model,
        agent_observe=parent_session.agent_observe,
        world=child_world,
        agent_initial_point=child_initial_point,
        rule=SIERPINSKI,
        seed_a=child_initial_seed + 1000,
    )

    # Build the spawn record
    body = {
        "type": "spawn",
        "agent_id": parent_session.agent_id,
        "child_id": child_session.agent_id,
        "child_persona": child_persona,
        "child_initial_seed": int(child_initial_seed),
        "child_initial_point": list(child_initial_point),
        "ts": _now(),
    }
    sig = parent_session.agent_kp.sign(
        _canonical(body)).hex()
    spawn_record = {**body, "sig": sig}
    parent_session.a_records.append(spawn_record)
    return child_session, spawn_record


def spawn_record_hash(spawn_record: Dict) -> str:
    return _hash({k: v for k, v in spawn_record.items()
                   if k != "sig"})


# =====================================================================
# Extended pack_bundle
# =====================================================================

def pack_child_bundle(
    child_session: WorldAgentSession,
    child_name: str,
    child_persona: str,
    parent_bundle: IndividualBundle,
    spawn_record: Dict,
    child_initial_seed: int,
) -> IndividualBundle:
    """Pack a child bundle with lineage fields.

    Wraps pack_bundle with parent_did and parent_spawn_hash.
    The child's `agent_model_config_name` is set to child_name
    before packing.
    """
    child_session.agent_model_config_name = child_name
    bundle = pack_bundle(
        child_session,
        persona=child_persona,
        parent_did=parent_bundle.individual_id,
        initial_seed=child_initial_seed,
    )
    # Inject lineage fields into the manifest, re-sign
    bundle.manifest = dict(bundle.manifest)
    bundle.manifest["parent_spawn_hash"] = \
        spawn_record_hash(spawn_record)
    # Re-sign the manifest (lineage fields are part of it)
    body = {k: v for k, v in bundle.manifest.items()
             if k != "sig"}
    new_sig = child_session.agent_kp.sign(
        _canonical(body)).hex()
    bundle.manifest["sig"] = new_sig
    return bundle


# =====================================================================
# Lineage verification
# =====================================================================

def verify_bundle_lineage(
    child: IndividualBundle,
    parent: IndividualBundle,
) -> Tuple[bool, str]:
    """Verify that `parent` spawned `child`."""
    # Both bundles must pass basic verification
    ok, reason = verify_bundle_basic(child)
    if not ok:
        return (False, f"child basic: {reason}")
    ok, reason = verify_bundle_basic(parent)
    if not ok:
        return (False, f"parent basic: {reason}")
    # Child's declared parent matches
    if child.manifest.get("parent_did") != \
            parent.manifest["individual_id"]:
        return (False,
                 f"child.parent_did {child.manifest.get('parent_did')} "
                 f"!= parent.individual_id "
                 f"{parent.manifest['individual_id']}")
    # Parent's spawn record exists with matching hash
    target_hash = child.manifest.get("parent_spawn_hash")
    if not target_hash:
        return (False, "child has no parent_spawn_hash")
    found = None
    for rec in parent.memory:
        if rec.get("type") != "spawn":
            continue
        if spawn_record_hash(rec) == target_hash:
            found = rec
            break
    if found is None:
        return (False,
                 f"parent has no spawn record with hash "
                 f"{target_hash[:16]}...")
    # Spawn record's child_id matches
    if found.get("child_id") != child.manifest["individual_id"]:
        return (False,
                 f"parent's spawn.child_id {found.get('child_id')} "
                 f"!= child.individual_id "
                 f"{child.manifest['individual_id']}")
    # Spawn record is signed by parent
    try:
        _pubkey_from_did(parent.manifest["individual_id"]).verify(
            bytes.fromhex(found["sig"]),
            _canonical({k: v for k, v in found.items()
                         if k != "sig"}))
    except Exception:
        return (False, "spawn record signature invalid")
    return (True, "lineage verifies")


def verify_lineage_chain(
    chain: List[IndividualBundle],
) -> Tuple[bool, str]:
    if len(chain) < 2:
        return (False, "chain needs at least 2 bundles")
    for i in range(len(chain) - 1):
        ok, reason = verify_bundle_lineage(
            chain[i + 1], chain[i])
        if not ok:
            return (False,
                     f"lineage[{i}→{i+1}]: {reason}")
    return (True, f"lineage chain of {len(chain)} verifies")


# =====================================================================
# Extended full-verification (skip spawns)
# =====================================================================

def verify_bundle_full_with_spawn(
    bundle: IndividualBundle,
) -> Tuple[bool, str]:
    """Same as verify_bundle_full, but skips non-step records
    during replay. Spawn records and any future non-step
    entries don't advance the model."""
    ok, reason = verify_bundle_basic(bundle)
    if not ok:
        return (False, f"basic: {reason}")

    model = bundle.initial_model()
    if bundle.manifest["observes"]:
        obs_map = {o["step"]: o["freq"]
                    for o in bundle.observations}
    else:
        obs_map = {}

    import random as _rng
    rng = _rng.Random(
        bundle.manifest["model_initial_seed"] + 1)

    last_action = 0
    last_reward = 0.0
    prev_point = None
    step_index = 0
    for i, rec in enumerate(bundle.memory):
        if rec.get("type") != "agent_step":
            continue
        x, y = (prev_point[0] / 1000, prev_point[1] / 1000) \
                if prev_point else (0.2, 0.8)
        if bundle.manifest["observes"]:
            freq = tuple(obs_map.get(step_index,
                                       (0.33, 0.33, 0.34)))
            state = (last_action, last_reward, x, y, *freq)
        else:
            state = (last_action, last_reward, x, y)
        expected = model.act(state, rng)
        if expected != rec["action"]:
            return (False,
                     f"memory[{i}] step {step_index}: "
                     f"recorded action {rec['action']} "
                     f"!= replayed {expected}")
        reward = rec["reward_micros"] / 1_000_000
        model.learn(reward)
        last_action = rec["action"]
        last_reward = reward
        prev_point = tuple(rec["to_point"])
        step_index += 1
    return (True, "full replay matches (spawns skipped)")


def verify_bundle_exact_with_spawn(
    bundle: IndividualBundle,
) -> Tuple[bool, str]:
    """Full-with-spawn + final weights match."""
    ok, reason = verify_bundle_full_with_spawn(bundle)
    if not ok:
        return (False, f"full: {reason}")
    model = bundle.initial_model()
    if bundle.manifest["observes"]:
        obs_map = {o["step"]: o["freq"]
                    for o in bundle.observations}
    else:
        obs_map = {}
    import random as _rng
    rng = _rng.Random(
        bundle.manifest["model_initial_seed"] + 1)
    last_action = 0
    last_reward = 0.0
    prev_point = None
    step_index = 0
    for rec in bundle.memory:
        if rec.get("type") != "agent_step":
            continue
        x, y = (prev_point[0] / 1000, prev_point[1] / 1000) \
                if prev_point else (0.2, 0.8)
        if bundle.manifest["observes"]:
            freq = tuple(obs_map.get(step_index,
                                       (0.33, 0.33, 0.34)))
            state = (last_action, last_reward, x, y, *freq)
        else:
            state = (last_action, last_reward, x, y)
        model.act(state, rng)
        model.learn(rec["reward_micros"] / 1_000_000)
        last_action = rec["action"]
        last_reward = rec["reward_micros"] / 1_000_000
        prev_point = tuple(rec["to_point"])
        step_index += 1
    from individual_bundle import serialize_weights
    replayed_weights = serialize_weights(model)
    if json.dumps(replayed_weights, sort_keys=True) != \
            json.dumps(bundle.weights, sort_keys=True):
        return (False, "replayed weights != saved weights")
    return (True, "exact verification passes (spawns skipped)")


# =====================================================================
# Rendering
# =====================================================================

def render_lineage(chain: List[IndividualBundle]) -> str:
    lines = []
    for i, b in enumerate(chain):
        indent = "  " * i
        marker = "├─" if i < len(chain) - 1 else "└─"
        if i == 0:
            marker = "◆"
        lines.append(
            f"  {indent}{marker} "
            f"{b.manifest['name']}  "
            f"({b.manifest['individual_id'][:16]}...)")
        lines.append(
            f"  {indent}    persona: "
            f"{b.manifest['persona'][:50]}")
        lines.append(
            f"  {indent}    memory:  "
            f"{b.manifest['memory_entries']} entries")
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
    root = Path(artifact_dir) / "individual_spawn"
    root.mkdir(parents=True, exist_ok=True)

    # --- Generation 0: grandparent ---
    gp_world = ScriptedWorld(
        kp=Ed25519PrivateKey.generate(),
        initial_point_b=(800, 800), k_b=100,
        prng_seed_b=0xCAFEBABE, rule=SIERPINSKI)
    gp_model = TinyRNN(
        n_actions=3, hidden=4, n_extra_inputs=0, seed=100)
    gp_session = WorldAgentSession(
        agent_kp=Ed25519PrivateKey.generate(),
        agent_model=gp_model, agent_observe=False,
        world=gp_world,
        agent_initial_point=(200, 800),
        rule=SIERPINSKI, seed_a=1100)
    gp_session.agent_model_config_name = "grandparent"
    for _ in range(800):
        gp_session.step()

    # Grandparent spawns parent
    parent_session, gp_spawn = spawn_child(
        parent_session=gp_session,
        child_persona="a child of the grandparent, "
                       "learning in a fresh world",
        child_initial_seed=200,
        child_initial_point=(300, 700),
    )
    # Grandparent continues
    for _ in range(400):
        gp_session.step()

    # --- Generation 1: parent ---
    parent_session.agent_model_config_name = "parent"
    for _ in range(500):
        parent_session.step()

    # Parent spawns child
    child_session, parent_spawn = spawn_child(
        parent_session=parent_session,
        child_persona="a grandchild, spawned by the child",
        child_initial_seed=300,
        child_initial_point=(400, 600),
    )
    # Parent continues
    for _ in range(300):
        parent_session.step()

    # --- Generation 2: child ---
    child_session.agent_model_config_name = "child"
    for _ in range(500):
        child_session.step()

    # --- Pack bundles ---
    gp_bundle = pack_bundle(
        gp_session,
        persona="an original agent, "
                "grandparent of two descendants",
        initial_seed=100,
    )
    parent_bundle = pack_child_bundle(
        parent_session,
        child_name="parent",
        child_persona="a child of the grandparent",
        parent_bundle=gp_bundle,
        spawn_record=gp_spawn,
        child_initial_seed=200,
    )
    child_bundle = pack_child_bundle(
        child_session,
        child_name="child",
        child_persona="a grandchild of the grandparent",
        parent_bundle=parent_bundle,
        spawn_record=parent_spawn,
        child_initial_seed=300,
    )

    # --- Save ---
    for name, bundle in (
        ("grandparent", gp_bundle),
        ("parent", parent_bundle),
        ("child", child_bundle),
    ):
        bundle.save(root / name)

    # --- Reload from disk ---
    gp_loaded = IndividualBundle.load(root / "grandparent")
    parent_loaded = IndividualBundle.load(root / "parent")
    child_loaded = IndividualBundle.load(root / "child")

    # --- Verify ---
    tiers = {}
    for name, b in (
        ("grandparent", gp_loaded),
        ("parent", parent_loaded),
        ("child", child_loaded),
    ):
        basic = verify_bundle_basic(b)
        full = verify_bundle_full_with_spawn(b)
        exact = verify_bundle_exact_with_spawn(b)
        tiers[name] = {
            "basic": basic[0], "full": full[0], "exact": exact[0],
            "full_reason": full[1], "exact_reason": exact[1],
        }

    # --- Lineage ---
    pair = verify_bundle_lineage(parent_loaded, gp_loaded)
    pair2 = verify_bundle_lineage(child_loaded, parent_loaded)
    chain = verify_lineage_chain(
        [gp_loaded, parent_loaded, child_loaded])

    # --- Tamper: fake a spawn record ---
    tampered_child = IndividualBundle.load(root / "child")
    # Modify a memory entry — should fail basic
    tampered_child.memory[10]["action"] = 99
    tamper_ok, _ = verify_bundle_basic(tampered_child)

    # --- Tamper: fake lineage ---
    # Create a fake child whose parent_did points to grandparent
    # but the parent_spawn_hash is bogus
    fake_child = IndividualBundle.load(root / "child")
    fake_child.manifest = dict(fake_child.manifest)
    fake_child.manifest["parent_did"] = \
        gp_loaded.manifest["individual_id"]
    body = {k: v for k, v in fake_child.manifest.items()
             if k != "sig"}
    # Re-sign with the child's key (child can claim any parent)
    fake_child.manifest["sig"] = child_session.agent_kp.sign(
        _canonical(body)).hex()
    lineage_ok, _ = verify_bundle_lineage(fake_child, gp_loaded)

    # --- Resume grandparent from bundle ---
    resumed_gp_model = gp_loaded.reconstruct_model()
    resume_session = WorldAgentSession(
        agent_kp=gp_session.agent_kp,
        agent_model=resumed_gp_model,
        agent_observe=False,
        world=ScriptedWorld(
            kp=Ed25519PrivateKey.generate(),
            initial_point_b=(800, 800), k_b=100,
            prng_seed_b=0xCAFEBABE, rule=SIERPINSKI),
        agent_initial_point=(200, 800),
        rule=SIERPINSKI, seed_a=9999,
    )
    for _ in range(300):
        resume_session.step()

    # --- Print ---
    print("=" * 74)
    print("Individual spawn — an individual that creates an")
    print("individual")
    print("=" * 74)
    print()
    print("  Lineage:")
    print(render_lineage([gp_loaded, parent_loaded, child_loaded]))
    print()
    print("  Verification tiers:")
    for name in ("grandparent", "parent", "child"):
        t = tiers[name]
        print(f"    {name:12s}  basic={t['basic']}  "
              f"full={t['full']}  exact={t['exact']}")
    print()
    print("  Lineage verification:")
    print(f"    parent ← grandparent: "
          f"{pair[0]}  ({pair[1]})")
    print(f"    child ← parent:       "
          f"{pair2[0]}  ({pair2[1]})")
    print(f"    chain of 3:           "
          f"{chain[0]}  ({chain[1]})")
    print()
    print("  Tampering:")
    print(f"    modified memory entry:  "
          f"basic verification {tamper_ok}")
    print(f"    fake lineage (child claims grandparent): "
          f"{lineage_ok}")
    print()
    print(f"  Resume: grandparent loaded from bundle, "
          f"continued 300 more steps")
    print(f"    new memory entries: {len(resume_session.a_records)}")
    print()
    print("  What this establishes:")
    print("    - An individual can create another individual.")
    print("      The spawn is signed, recorded in the parent's")
    print("      memory, and referenced by the child's manifest.")
    print("    - The lineage is verifiable: given both bundles,")
    print("      anyone can confirm the parent spawned the child.")
    print("      The chain extends to any depth.")
    print("    - Each bundle is still self-contained for")
    print("      verification. The parent's spawn record is")
    print("      skipped during model replay, so exact")
    print("      verification still passes.")
    print("    - Tampering with memory breaks basic. Faking")
    print("      lineage fails because the parent has no")
    print("      matching spawn record.")
    print("    - A bundled individual can be resumed, spawned")
    print("      from, or verified independently.")
    print()
    print("  Honest limit: no weight inheritance. The child")
    print("  starts fresh from its own seed — it must learn")
    print("  on its own. Inheritance would be a richer mode;")
    print("  noted as future work.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'I dwell in Possibility –'")
    print("    'A fairer House than Prose –'")

    audit = {
        "chain_length": 3,
        "tiers": tiers,
        "lineage": {
            "parent_grandparent": pair[0],
            "child_parent": pair2[0],
            "chain": chain[0],
        },
        "tampering": {
            "memory_detected": not tamper_ok,
            "fake_lineage_detected": not lineage_ok,
        },
        "resume_entries": len(resume_session.a_records),
    }
    (root / "individual_spawn_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {root}/individual_spawn_demo.json")
    return audit
