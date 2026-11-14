"""
resumable.py — continue an individual's life from a bundle.

resume_from_bundle(bundle, individual_kp, world_specs)
  -> (sessions, "resumed") or (None, reason)

pack_resumed_bundle(sessions, memory, model, parent_bundle,
                     individual_kp, persona, name)
  -> IndividualBundle

verify_resumed_from(resumed, parent)
  -> (ok, reason)

Design commitments:
  - The bundle authenticates the individual; the private key
    authorises the resumption. A verifier can only resume an
    individual whose key it holds.
  - Memory continues the chain. The resumed bundle's memory
    is [parent.memory] ++ [new world_entries and steps]. The
    `resumed_from` field pins the parent's memory_root at
    resume time.
  - Weights continue the learning. The resumed model is
    build_model + apply_weights(bundle.weights), then learns
    new steps. initial_weights and model_initial_seed are
    preserved so verify_federated_full can replay from birth.
  - world_contexts is merged. The resumed manifest lists
    every world the individual has ever lived in.
  - Lineage is preserved. compact_ancestry / full ancestry /
    lineage_root / inherited_from all copied unchanged — the
    individual's descent didn't change by resuming.

Honest limits:
  - Resume verifies the bundle internally (basic + full). It
    does NOT verify lineage (compact_ancestry_with_inheritance)
    because that requires parent bundles via fetcher. Callers
    who want the full tier run it after resuming.
  - One individual per bundle. Forking a bundle into a new
    individual is a distinct operation (a `spawn` from
    itself) not built here.
  - Determinism: same bundle + same kp + same world_specs
    produces the same resumed bundle. Different world_specs
    (different world keypairs → different world_ids → different
    RNG seeds) produce different behaviour, which is correct.
"""

import json
from typing import Dict, List, Optional, Tuple

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from individual_bundle import (
    IndividualBundle, build_model, apply_weights, serialize_weights,
    verify_bundle_basic, _canonical, _hash, _merkle_root, _now,
    _did_from_kp,
)
from federated_bundle import (
    FederatedSession, verify_federated_full,
)
from world_agent_coupling import ScriptedWorld
from coupled_learners import SIERPINSKI


WorldSpec = Tuple[int, Tuple[int, int], int, int]
# (n_steps, initial_point, k_b, prng_seed_b)


def resume_from_bundle(
    bundle: IndividualBundle,
    individual_kp,
    world_specs: List[WorldSpec],
    rule=SIERPINSKI,
    rng_seed_override: Optional[int] = None,
) -> Tuple[Optional[List[FederatedSession]], str]:
    """Continue a bundled individual into new worlds.

    Returns (sessions, "resumed") on success, (None, reason) on
    failure. Never raises for verification failures.
    """
    if not HAS_CRYPTO:
        return (None, "cryptography not installed")
    if not isinstance(bundle, IndividualBundle):
        return (None, "not an IndividualBundle")
    if not world_specs:
        return (None, "world_specs must not be empty")

    # 1. Keypair must match bundle's DID
    kp_did = _did_from_kp(individual_kp)
    if kp_did != bundle.individual_id:
        return (None,
                 f"keypair DID {kp_did[:16]}... does not match "
                 f"bundle {bundle.individual_id[:16]}...")

    # 2. Bundle must verify internally
    v_basic = verify_bundle_basic(bundle)
    if not v_basic[0]:
        return (None, f"bundle basic: {v_basic[1]}")
    v_full = verify_federated_full(bundle)
    if not v_full[0]:
        return (None, f"bundle full: {v_full[1]}")

    # 3. Reconstruct model from final weights
    cfg = bundle.manifest["model_config"]
    model = build_model(cfg)
    apply_weights(model, bundle.weights)

    # 4. Shared memory across sessions
    memory: List[Dict] = list(bundle.memory)

    # 5. Create and step sessions
    sessions: List[FederatedSession] = []
    for idx, (n_steps, initial_point, k_b, prng_seed_b) in enumerate(
            world_specs):
        if n_steps < 0:
            return (None, f"world_specs[{idx}]: negative n_steps")
        world = ScriptedWorld(
            kp=Ed25519PrivateKey.generate(),
            initial_point_b=(800, 800),
            k_b=int(k_b),
            prng_seed_b=int(prng_seed_b),
            rule=rule,
        )
        s = FederatedSession(
            individual_kp=individual_kp,
            model=model,
            world=world,
            initial_point=tuple(initial_point),
            memory=memory,
            rule=rule,
            rng_seed_override=rng_seed_override,
        )
        for _ in range(n_steps):
            s.step()
        sessions.append(s)

    return (sessions, "resumed")


def pack_resumed_bundle(
    sessions: List[FederatedSession],
    memory: List[Dict],
    model,
    parent_bundle: IndividualBundle,
    individual_kp,
    persona: str,
    name: str,
) -> IndividualBundle:
    """Assemble the resumed bundle. Merges parent's
    world_contexts with the new sessions', pins the parent's
    memory_root as `resumed_from`, preserves initial_weights
    and model_initial_seed for replay-from-birth."""
    if not HAS_CRYPTO:
        raise RuntimeError("cryptography not installed")
    if not sessions:
        raise ValueError("sessions must not be empty")

    individual_id = _did_from_kp(individual_kp)
    if individual_id != parent_bundle.individual_id:
        raise ValueError(
            f"keypair DID {individual_id[:16]}... does not match "
            f"parent_bundle {parent_bundle.individual_id[:16]}...")

    # Merge world_contexts
    old_contexts = list(
        parent_bundle.manifest.get("world_contexts", []))
    new_contexts = [dict(s.world_context) for s in sessions]
    all_contexts = old_contexts + new_contexts

    # Weights
    weights = serialize_weights(model)
    weights_hash = _hash(json.dumps(
        weights, sort_keys=True,
        separators=(",", ":")).encode())

    # Memory
    memory_hashes = [
        _hash({k: v for k, v in rec.items() if k != "sig"})
        for rec in memory
    ]
    memory_root = _merkle_root(memory_hashes)

    # Observations
    obs_canon = json.dumps(
        [], sort_keys=True,
        separators=(",", ":")).encode()
    observations_hash = _hash(obs_canon)

    # Manifest body — start from parent's lineage claims,
    # override the fields that changed
    body: Dict = {
        "kind": "individual_bundle",
        "version": "1.2",
        "individual_id": individual_id,
        "name": name,
        "persona": persona,
        "created_at": _now(),
        "parent_did": parent_bundle.manifest.get("parent_did"),
        "model_config": parent_bundle.manifest["model_config"],
        "model_initial_seed":
            parent_bundle.manifest["model_initial_seed"],
        "model_weights_hash": weights_hash,
        "observes": parent_bundle.manifest.get("observes", False),
        "memory_entries": len(memory),
        "memory_root": memory_root,
        "observations_hash": observations_hash,
        "world_contexts": all_contexts,
        "resumed_from": parent_bundle.manifest.get("memory_root"),
        "lineage_root": parent_bundle.manifest.get("lineage_root"),
        "compact_ancestry":
            parent_bundle.manifest.get("compact_ancestry"),
        "parent_spawn_hash":
            parent_bundle.manifest.get("parent_spawn_hash"),
        "inherited_from":
            parent_bundle.manifest.get("inherited_from"),
        "ts": _now(),
    }
    # Preserve initial_weights_hash if parent had it
    if "initial_weights_hash" in parent_bundle.manifest:
        body["initial_weights_hash"] = \
            parent_bundle.manifest["initial_weights_hash"]
    # Preserve ancestry_hash if parent had it (full-ancestry mode)
    if "ancestry_hash" in parent_bundle.manifest:
        body["ancestry_hash"] = \
            parent_bundle.manifest["ancestry_hash"]

    # Drop None fields so signature is clean
    body = {k: v for k, v in body.items() if v is not None}

    sig = individual_kp.sign(_canonical(body)).hex()
    return IndividualBundle(
        manifest={**body, "sig": sig},
        memory=list(memory),
        weights=weights,
        initial_weights=(dict(parent_bundle.initial_weights)
                          if parent_bundle.initial_weights
                          else None),
        observations=list(parent_bundle.observations),
        ancestry=list(parent_bundle.ancestry),
    )


def verify_resumed_from(
    resumed: IndividualBundle,
    parent: IndividualBundle,
) -> Tuple[bool, str]:
    """Verify that `resumed` is a legitimate continuation of
    `parent`: the resumed memory's prefix hashes to parent's
    memory_root, and the claimed prefix length matches."""
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    resumed_from = resumed.manifest.get("resumed_from")
    if resumed_from is None:
        return (True, "not a resumed bundle")

    parent_root = parent.manifest.get("memory_root")
    if resumed_from != parent_root:
        return (False,
                 f"resumed.resumed_from "
                 f"{resumed_from[:16]}... != "
                 f"parent.memory_root "
                 f"{parent_root[:16] if parent_root else None}")

    n = parent.manifest.get("memory_entries")
    if n is None or n < 0:
        return (False, "parent.memory_entries missing or invalid")
    if len(resumed.memory) < n:
        return (False,
                 f"resumed memory ({len(resumed.memory)} entries) "
                 f"shorter than parent ({n} entries)")
    prefix = resumed.memory[:n]
    prefix_hashes = [
        _hash({k: v for k, v in r.items() if k != "sig"})
        for r in prefix
    ]
    prefix_root = _merkle_root(prefix_hashes)
    if prefix_root != resumed_from:
        return (False,
                 f"resumed memory prefix does not hash to "
                 f"resumed_from "
                 f"(prefix={prefix_root[:16]}..., "
                 f"claimed={resumed_from[:16]}...)")
    return (True,
             f"resumed from {resumed_from[:16]}... verified "
             f"(prefix of {n} memory entries)")


def verify_resumed_bundle(
    resumed: IndividualBundle,
    parent: IndividualBundle,
) -> Tuple[bool, str]:
    """Composite: basic + full + resumed_from.
    Does not run compact_ancestry_with_inheritance (that
    requires parent bundles via fetcher)."""
    v_basic = verify_bundle_basic(resumed)
    if not v_basic[0]:
        return (False, f"basic: {v_basic[1]}")
    v_full = verify_federated_full(resumed)
    if not v_full[0]:
        return (False, f"federated_full: {v_full[1]}")
    v_cont = verify_resumed_from(resumed, parent)
    if not v_cont[0]:
        return (False, f"resumed_from: {v_cont[1]}")
    return (True,
             f"resumed bundle verifies (memory: "
             f"{len(resumed.memory)} entries, "
             f"worlds: {len(resumed.manifest['world_contexts'])})")


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir=None):
    from pathlib import Path
    import json as _json
    from federated_spawn import (
        spawn_federated_child, pack_federated_child,
    )
    from compact_ancestry import (
        compute_compact_ancestry, slim_bundle,
        verify_compact_ancestry,
    )
    from compact_inheritance import (
        verify_compact_ancestry_with_inheritance,
    )
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey)

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    root = Path(artifact_dir) / "resumable"
    root.mkdir(parents=True, exist_ok=True)

    def _kp():
        return Ed25519PrivateKey.generate()

    def _world(k_b, prng):
        return ScriptedWorld(
            kp=_kp(), initial_point_b=(800, 800),
            k_b=k_b, prng_seed_b=prng, rule=SIERPINSKI)

    # ---- Build 3-gen chain (as before) ----
    DEPTH = 3
    STEPS = 8

    kps = []
    models = []
    memories = []
    sessions_list = []
    spawns = []
    inherited = []

    kp0 = _kp()
    m0 = TinyRNN_safe(100)
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
                child_initial_seed=100 + i * 100)
        parent_sessions[-1].step()
        kps.append(child_kp); models.append(child_model)
        spawns.append(spawn_rec)
        inherited.append(inherited_w)
        mem_i: list = []
        s_i = FederatedSession(
            individual_kp=child_kp, model=child_model,
            world=_world(i * 10, 0xAAAA + i * 0x1111),
            initial_point=(200 + i * 10, 800),
            memory=mem_i, rule=SIERPINSKI)
        for _ in range(STEPS):
            s_i.step()
        memories.append(mem_i)
        sessions_list.append([s_i])

    full = [pack_federated_bundle_safe(
        kps[0], models[0], sessions_list[0], memories[0],
        persona="origin", initial_seed=100, name="gen0")]
    for i in range(1, DEPTH + 1):
        full.append(pack_federated_child(
            child_kp=kps[i], child_model=models[i],
            child_sessions=sessions_list[i],
            child_memory=memories[i],
            child_persona=f"gen{i}",
            child_initial_seed=100 + i * 100,
            parent_bundle=full[i - 1],
            spawn_record=spawns[i - 1],
            inherited_weights=inherited[i - 1],
            name=f"gen{i}"))

    # Slim all
    slim = [full[0]]
    for i in range(1, DEPTH + 1):
        compact = compute_compact_ancestry(
            full[i].individual_id, slim[i - 1],
            spawns[i - 1])
        slim.append(slim_bundle(full[i], compact, kps[i]))

    full_by_id = {b.individual_id: b for b in full}
    def fetcher(did):
        return full_by_id.get(did)

    # Pick the deepest: gen3
    target = slim[-1]
    target_full = full[-1]
    target_kp = kps[-1]
    target_slim = target

    # Verify baseline
    baseline_fed = verify_federated_full(target_slim)
    baseline_compact = verify_compact_ancestry_with_inheritance(
        target_slim, fetcher)

    # ---- Resume ----
    new_specs: List[WorldSpec] = [
        (30, (250, 750), 25, 0x1111),
        (25, (350, 650), 75, 0x2222),
    ]
    sessions, reason = resume_from_bundle(
        target_slim, target_kp, new_specs)
    if sessions is None:
        raise RuntimeError(f"resume failed: {reason}")

    # Shared memory now extends
    resumed_memory = sessions[-1].memory
    resumed_model = sessions[-1].model

    resumed_bundle = pack_resumed_bundle(
        sessions=sessions,
        memory=resumed_memory,
        model=resumed_model,
        parent_bundle=target_slim,
        individual_kp=target_kp,
        persona="gen3, resumed in two new worlds",
        name="gen3-resumed",
    )

    # Save
    resumed_bundle.save(root / "resumed")
    target_slim.save(root / "parent")

    # Reload
    resumed_loaded = IndividualBundle.load(root / "resumed")
    parent_loaded = IndividualBundle.load(root / "parent")

    # ---- Verification tiers ----
    v_basic = verify_bundle_basic(resumed_loaded)
    v_full = verify_federated_full(resumed_loaded)
    v_cont = verify_resumed_from(resumed_loaded, parent_loaded)
    v_comp = verify_compact_ancestry_with_inheritance(
        resumed_loaded, fetcher)
    v_all = verify_resumed_bundle(resumed_loaded, parent_loaded)

    # ---- Continuity assertions ----
    n_parent = parent_loaded.manifest["memory_entries"]
    prefix_of_resumed = resumed_loaded.memory[:n_parent]
    prefix_matches_parent = (
        prefix_of_resumed == parent_loaded.memory)

    # ---- Tampering ----
    # Wrong keypair
    wrong_kp = _kp()
    bad_resume_sessions, bad_resume_reason = resume_from_bundle(
        parent_loaded, wrong_kp, new_specs)

    # Tampered parent bundle
    tampered_parent = IndividualBundle.load(root / "parent")
    tampered_parent.memory = list(tampered_parent.memory)
    for i, r in enumerate(tampered_parent.memory):
        if r.get("type") == "agent_step":
            tampered_parent.memory[i] = {**r, "action": 99}
            break
    tampered_sessions, tampered_reason = resume_from_bundle(
        tampered_parent, target_kp, new_specs)

    # Tampered resumed_from (fabricated continuation)
    tampered_resumed = IndividualBundle.load(root / "resumed")
    tampered_resumed.manifest = dict(tampered_resumed.manifest)
    tampered_resumed.manifest["resumed_from"] = "00" * 32
    body = {k: v for k, v in tampered_resumed.manifest.items()
             if k != "sig"}
    tampered_resumed.manifest["sig"] = target_kp.sign(
        _canonical(body)).hex()
    tamper_cont_ok, tamper_cont_reason = verify_resumed_from(
        tampered_resumed, parent_loaded)

    # ---- Print ----
    print("=" * 74)
    print("Resumable individual — continue a bundle's life")
    print("=" * 74)
    print()
    print(f"  Individual: {target_slim.individual_id[:32]}...")
    print(f"  Parent: {n_parent} memory entries, "
          f"{len(parent_loaded.manifest['world_contexts'])} worlds")
    print(f"  Resumed: {len(resumed_loaded.memory)} memory entries, "
          f"{len(resumed_loaded.manifest['world_contexts'])} worlds")
    print()
    print(f"  New worlds:")
    for ctx in resumed_loaded.manifest["world_contexts"][-2:]:
        print(f"    {ctx['world_id'][:24]}...  "
              f"steps={ctx['steps_in_world']}  "
              f"first_index={ctx['first_memory_index']}")
    print()
    print("  Baseline (before resume):")
    print(f"    federated_full:            {baseline_fed[0]}")
    print(f"    compact_ancestry_with_inh: {baseline_compact[0]}")
    print()
    print("  Resumed bundle verification:")
    print(f"    basic:                     {v_basic[0]}  "
          f"({v_basic[1]})")
    print(f"    federated_full:            {v_full[0]}  "
          f"({v_full[1]})")
    print(f"    resumed_from:              {v_cont[0]}  "
          f"({v_cont[1]})")
    print(f"    compact_ancestry_with_inh: {v_comp[0]}  "
          f"({v_comp[1]})")
    print(f"    composite:                 {v_all[0]}  "
          f"({v_all[1]})")
    print()
    print("  Continuity:")
    print(f"    resumed memory prefix == parent memory: "
          f"{prefix_matches_parent}")
    print(f"    parent's memory_root == resumed_from:   "
          f"{parent_loaded.manifest['memory_root'] == resumed_loaded.manifest['resumed_from']}")
    print()
    print("  Tampering:")
    print(f"    wrong keypair:          "
          f"{bad_resume_sessions is None}  ({bad_resume_reason})")
    print(f"    tampered parent:        "
          f"{tampered_sessions is None}  ({tampered_reason})")
    print(f"    tampered resumed_from:  "
          f"{not tamper_cont_ok}  ({tamper_cont_reason})")
    print()
    print("  What this establishes:")
    print("    - A bundle is a runnable artifact. With the key in")
    print("      hand, an individual can be resumed from its saved")
    print("      state — model weights, memory, lineage all")
    print("      preserved — into new worlds.")
    print("    - The resumed bundle is itself verifiable at every")
    print("      tier. Its memory replays to the same weights")
    print("      (federated_full). Its lineage walks to the same")
    print("      root (compact_ancestry_with_inheritance). Its")
    print("      memory continues the parent (resumed_from).")
    print("    - Continuity is proven, not trusted: the resumed")
    print("      memory's first N entries hash to the parent's")
    print("      memory_root. A stranger can verify: this exact")
    print("      state was legitimately continued.")
    print("    - The key authorizes continuation. A wrong key")
    print("      fails immediately; a tampered bundle fails at")
    print("      basic verification before resume even starts.")
    print("    - Forking an individual (making a new entity from")
    print("      its bundle) is a distinct operation, not built")
    print("      here. The model insists: resumption is one")
    print("      individual's life continuing, not two.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'Forever – is composed of Nows –'")
    print("    'Tis not a different time –'")

    audit = {
        "individual_id": target_slim.individual_id,
        "parent_memory_entries": n_parent,
        "resumed_memory_entries": len(resumed_loaded.memory),
        "new_worlds_added": 2,
        "verification": {
            "basic": v_basic[0],
            "federated_full": v_full[0],
            "resumed_from": v_cont[0],
            "compact_ancestry_with_inheritance": v_comp[0],
            "composite": v_all[0],
        },
        "continuity": {
            "prefix_matches_parent": prefix_matches_parent,
            "resumed_from_equals_parent_root": (
                parent_loaded.manifest["memory_root"]
                == resumed_loaded.manifest["resumed_from"]),
        },
        "tampering": {
            "wrong_keypair_refused":
                bad_resume_sessions is None,
            "tampered_parent_refused":
                tampered_sessions is None,
            "tampered_resumed_from_detected":
                not tamper_cont_ok,
        },
    }
    (root / "resumable_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {root}/resumable_demo.json")
    return audit


def TinyRNN_safe(seed):
    from coupled_learners import TinyRNN
    return TinyRNN(n_extra_inputs=0, seed=seed)


def pack_federated_bundle_safe(kp, model, sessions, memory,
                                persona, initial_seed, name):
    from federated_bundle import pack_federated_bundle
    return pack_federated_bundle(
        individual_kp=kp, model=model,
        sessions=sessions, memory=memory,
        persona=persona, initial_seed=initial_seed,
        name=name)
