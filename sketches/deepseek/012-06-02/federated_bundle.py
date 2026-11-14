"""
federated_bundle.py — the individual across worlds.

An individual enters world A, lives for a while, moves to
world B, lives, moves to world C. Its identity is the same
DID; its model is continuous — weights carry over; its memory
is one chain with world boundaries marked.

The bundle gains `world_contexts` in its manifest: an ordered
list of {world_id, seed_hash, initial_point, steps_in_world,
first_memory_index}. Memory gains `world_entry` records at
world boundaries, each signed by the individual.

Three verification tiers:
  basic          — signatures + hashes + world_contexts
                   matches world_entry records
  full           — basic + full model replay, using each
                   world's initial_point at its world_entry
  with_world_logs — full + cross-check every agent_step's
                   world_step_hash against the actual world
                   log

Honest limits:
  - The bundle carries world seed hashes but not world logs.
    Full verification is self-contained; with_world_logs
    requires the logs to be supplied separately.
  - RNG is reseeded per world (derived from individual DID +
    world id). Deterministic without carrying RNG state.
  - Observations not exercised. Non-observing agents only.
  - No world switching mid-step. Worlds are entered, lived
    in for >=1 step, and exited via world_entry records.
"""

import hashlib
import json
import random as _rng
from collections import deque
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
    verify_bundle_basic, serialize_weights, build_model,
    apply_weights, model_config,
    _canonical, _hash, _now, _did_from_kp, _pubkey_from_did,
)
from world_agent_coupling import ScriptedWorld, WorldStepRecord
from coupled_learners import TinyRNN, TabularQ, SIERPINSKI


SCALE = 1000
NOVELTY_RADIUS = 50
SHARED_HISTORY_LEN = 200


# =====================================================================
# FederatedSession
# =====================================================================

class FederatedSession:
    """One world's slice of the individual's life. Multiple
    sessions share the same keypair, model, and memory."""

    def __init__(
        self,
        individual_kp,
        model,
        world: ScriptedWorld,
        initial_point: Tuple[int, int],
        memory: List[Dict],
        rule=SIERPINSKI,
        rng_seed_override: Optional[int] = None,
    ):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        self.individual_kp = individual_kp
        self.individual_id = _did_from_kp(individual_kp)
        self.model = model
        self.world = world
        self.rule = rule
        self.initial_point = tuple(initial_point)
        self.a_point = tuple(initial_point)
        self.a_last_action = 0
        self.a_last_reward = 0.0
        self.shared: deque = deque(maxlen=SHARED_HISTORY_LEN)
        # RNG: override or derived from (individual, world)
        if rng_seed_override is not None:
            self._rng_seed = int(rng_seed_override)
        else:
            h = _hash(self.individual_id + world.world_id).encode()
            self._rng_seed = int(h, 16) & ((1 << 32) - 1)
        self._rng = _rng.Random(self._rng_seed)
        self.memory = memory
        self._world_step = 0
        seed_hash = _hash(world.seed_record.body())
        self.world_context = {
            "world_id": world.world_id,
            "seed_hash": seed_hash,
            "initial_point": list(self.initial_point),
            "first_memory_index": len(memory),
            "steps_in_world": 0,
        }
        body = {
            "type": "world_entry",
            "agent_id": self.individual_id,
            "world_id": world.world_id,
            "world_seed_hash": seed_hash,
            "initial_point": list(self.initial_point),
            "ts": _now(),
        }
        sig = individual_kp.sign(_canonical(body)).hex()
        memory.append({**body, "sig": sig})

    def _novelty(self, point):
        near = sum(1 for (px, py) in self.shared
                    if abs(px - point[0]) < NOVELTY_RADIUS
                    and abs(py - point[1]) < NOVELTY_RADIUS)
        return 1.0 / (1.0 + near)

    def step(self):
        state = (self.a_last_action, self.a_last_reward,
                  self.a_point[0] / SCALE,
                  self.a_point[1] / SCALE)
        a_pick = self.model.act(state, self._rng)
        b_pick, b_new = self.world.step()
        a_new = self.rule[a_pick].apply(*self.a_point)
        reward = self._novelty(a_new)
        self.model.learn(reward)
        self.shared.append(a_new)
        self.shared.append(b_new)
        world_step_record = self.world.records[-1]
        body = {
            "type": "agent_step",
            "agent_id": self.individual_id,
            "world_id": self.world.world_id,
            "step_in_world": self._world_step,
            "action": a_pick,
            "from_point": list(self.a_point),
            "to_point": list(a_new),
            "reward_micros": int(reward * 1_000_000),
            "world_step_hash": world_step_record.record_hash(),
            "ts": _now(),
        }
        sig = self.individual_kp.sign(_canonical(body)).hex()
        self.memory.append({**body, "sig": sig})
        self.a_point = a_new
        self.a_last_action = a_pick
        self.a_last_reward = reward
        self.world.append_a_pick(a_pick)
        self._world_step += 1
        self.world_context["steps_in_world"] += 1


# =====================================================================
# Pack
# =====================================================================

def _merkle_root(hashes: List[str]) -> str:
    if not hashes:
        return _hash("")
    level = list(hashes)
    while len(level) > 1:
        if len(level) % 2 == 1:
            level.append(level[-1])
        level = [_hash((level[i] + level[i + 1]).encode())
                 for i in range(0, len(level), 2)]
    return level[0]


def pack_federated_bundle(
    individual_kp,
    model,
    sessions: List[FederatedSession],
    memory: List[Dict],
    persona: str,
    initial_seed: int,
    initial_weights: Optional[Dict] = None,
    name: str = "individual",
) -> IndividualBundle:
    individual_id = _did_from_kp(individual_kp)
    world_contexts = [dict(s.world_context) for s in sessions]
    weights = serialize_weights(model)
    weights_hash = _hash(json.dumps(
        weights, sort_keys=True,
        separators=(",", ":")).encode())
    memory_hashes = [
        _hash({k: v for k, v in rec.items() if k != "sig"})
        for rec in memory
    ]
    memory_root = _merkle_root(memory_hashes)
    obs_hash = _hash("[]")
    body = {
        "kind": "individual_bundle",
        "version": "1.1",
        "individual_id": individual_id,
        "name": name,
        "persona": persona,
        "created_at": _now(),
        "parent_did": None,
        "model_config": model_config(model),
        "model_initial_seed": int(initial_seed),
        "model_weights_hash": weights_hash,
        "observes": False,
        "memory_entries": len(memory),
        "memory_root": memory_root,
        "observations_hash": obs_hash,
        "world_contexts": world_contexts,
        "ts": _now(),
    }
    if initial_weights is not None:
        iw_canon = json.dumps(initial_weights,
                                sort_keys=True,
                                separators=(",", ":")).encode()
        body["initial_weights_hash"] = _hash(iw_canon)
    sig = individual_kp.sign(_canonical(body)).hex()
    return IndividualBundle(
        manifest={**body, "sig": sig},
        memory=memory,
        weights=weights,
        initial_weights=initial_weights,
        observations=[],
    )


# =====================================================================
# Verification
# =====================================================================

def _start_model(bundle):
    cfg = bundle.manifest["model_config"]
    if bundle.initial_weights is not None:
        model = build_model(cfg)
        apply_weights(model, bundle.initial_weights)
        return model
    seed = bundle.manifest["model_initial_seed"]
    if cfg["kind"] == "rnn":
        return TinyRNN(n_actions=cfg["n_actions"],
                        hidden=cfg["hidden"],
                        n_extra_inputs=cfg["n_extra_inputs"],
                        seed=seed)
    if cfg["kind"] == "q":
        return TabularQ(n_actions=cfg["n_actions"],
                         grid=cfg["grid"], seed=seed)
    raise ValueError(cfg["kind"])


def verify_federated_basic(bundle: IndividualBundle) -> Tuple[bool, str]:
    ok, reason = verify_bundle_basic(bundle)
    if not ok:
        return (False, f"base: {reason}")
    contexts = bundle.manifest.get("world_contexts")
    if not isinstance(contexts, list):
        return (False, "world_contexts missing")
    entry_indices = [
        i for i, rec in enumerate(bundle.memory)
        if rec.get("type") == "world_entry"
    ]
    if len(entry_indices) != len(contexts):
        return (False,
                 f"world_entry count {len(entry_indices)} "
                 f"!= world_contexts count {len(contexts)}")
    for j, idx in enumerate(entry_indices):
        rec = bundle.memory[idx]
        ctx = contexts[j]
        if rec["world_id"] != ctx["world_id"]:
            return (False,
                     f"world_entry {j}: world_id mismatch")
        if rec["world_seed_hash"] != ctx["seed_hash"]:
            return (False,
                     f"world_entry {j}: seed_hash mismatch")
        if tuple(rec["initial_point"]) != \
                tuple(ctx["initial_point"]):
            return (False,
                     f"world_entry {j}: initial_point mismatch")
        if idx != ctx["first_memory_index"]:
            return (False,
                     f"world_entry {j}: index {idx} != "
                     f"context {ctx['first_memory_index']}")
        next_idx = (entry_indices[j + 1]
                    if j + 1 < len(entry_indices)
                    else len(bundle.memory))
        steps_in_world = sum(
            1 for rec2 in bundle.memory[idx + 1:next_idx]
            if rec2.get("type") == "agent_step")
        if steps_in_world != ctx["steps_in_world"]:
            return (False,
                     f"world_entry {j}: steps_in_world "
                     f"{steps_in_world} != context "
                     f"{ctx['steps_in_world']}")
    return (True, "federated basic verifies")


def verify_federated_full(bundle: IndividualBundle) -> Tuple[bool, str]:
    ok, reason = verify_federated_basic(bundle)
    if not ok:
        return (False, f"basic: {reason}")
    model = _start_model(bundle)
    individual_id = bundle.manifest["individual_id"]
    last_action = 0
    last_reward = 0.0
    prev_point = None
    rng = None
    for i, rec in enumerate(bundle.memory):
        if rec.get("type") == "world_entry":
            prev_point = tuple(rec["initial_point"])
            seed_int = int(_hash(
                individual_id + rec["world_id"]).encode(),
                16) & ((1 << 32) - 1)
            rng = _rng.Random(seed_int)
            continue
        if rec.get("type") != "agent_step":
            continue
        if prev_point is None:
            return (False,
                     f"memory[{i}]: agent_step with no "
                     f"preceding world_entry")
        x, y = prev_point[0] / SCALE, prev_point[1] / SCALE
        state = (last_action, last_reward, x, y)
        expected = model.act(state, rng)
        if expected != rec["action"]:
            return (False,
                     f"memory[{i}]: recorded {rec['action']} "
                     f"!= replayed {expected}")
        model.learn(rec["reward_micros"] / 1_000_000)
        last_action = rec["action"]
        last_reward = rec["reward_micros"] / 1_000_000
        prev_point = tuple(rec["to_point"])
    return (True, "federated full verifies")


def verify_federated_with_world_logs(
    bundle: IndividualBundle,
    world_logs: Dict[str, List[Dict]],
) -> Tuple[bool, str]:
    ok, reason = verify_federated_full(bundle)
    if not ok:
        return (False, f"full: {reason}")
    for ctx in bundle.manifest["world_contexts"]:
        wid = ctx["world_id"]
        if wid not in world_logs:
            return (False,
                     f"world {wid[:16]}... not in world_logs")
    world_step_indices: Dict[str, int] = {}
    for i, rec in enumerate(bundle.memory):
        if rec.get("type") == "world_entry":
            world_step_indices[rec["world_id"]] = 0
            continue
        if rec.get("type") != "agent_step":
            continue
        wid = rec["world_id"]
        idx = world_step_indices.get(wid)
        if idx is None:
            return (False,
                     f"memory[{i}]: step in unentered world")
        if idx >= len(world_logs[wid]):
            return (False,
                     f"memory[{i}]: world log exhausted")
        expected_hash = _hash(world_logs[wid][idx])
        if expected_hash != rec["world_step_hash"]:
            return (False,
                     f"memory[{i}]: world_step_hash mismatch "
                     f"at world step {idx}")
        world_step_indices[wid] = idx + 1
    return (True, "federated with world logs verifies")


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
    root = Path(artifact_dir) / "federated_bundle"
    root.mkdir(parents=True, exist_ok=True)

    individual_kp = Ed25519PrivateKey.generate()
    individual_id = _did_from_kp(individual_kp)
    model = TinyRNN(
        n_actions=3, hidden=4, n_extra_inputs=0, seed=42)

    world_specs = [
        (0,   0xAAAA),   # world 1: uniform B
        (50,  0xBBBB),   # world 2: mild B
        (100, 0xCCCC),   # world 3: strong B
    ]
    worlds = [ScriptedWorld(
        kp=Ed25519PrivateKey.generate(),
        initial_point_b=(800, 800),
        k_b=k_b, prng_seed_b=prng,
        rule=SIERPINSKI) for k_b, prng in world_specs]

    memory: List[Dict] = []
    sessions: List[FederatedSession] = []
    steps_per_world = [500, 300, 200]
    initial_points = [(200, 800), (300, 700), (400, 600)]

    # Pre-compute the RNG seed that world 3 will use, so we
    # can give the fresh control individual the same seed.
    world3_rng_seed = int(_hash(
        individual_id + worlds[2].world_id).encode(),
        16) & ((1 << 32) - 1)

    for idx, (world, n_steps, init_pt) in enumerate(
            zip(worlds, steps_per_world, initial_points)):
        s = FederatedSession(
            individual_kp=individual_kp,
            model=model, world=world,
            initial_point=init_pt,
            memory=memory, rule=SIERPINSKI,
        )
        for _ in range(n_steps):
            s.step()
        sessions.append(s)

    bundle = pack_federated_bundle(
        individual_kp=individual_kp,
        model=model,
        sessions=sessions,
        memory=memory,
        persona="an individual who lived in three worlds",
        initial_seed=42,
        name="federated",
    )
    bundle.save(root / "federated")
    bundle_loaded = IndividualBundle.load(root / "federated")

    basic = verify_federated_basic(bundle_loaded)
    full = verify_federated_full(bundle_loaded)
    world_logs = {
        w.world_id: [r.body() for r in w.records
                      if isinstance(r, WorldStepRecord)]
        for w in worlds
    }
    with_logs = verify_federated_with_world_logs(
        bundle_loaded, world_logs)

    # Behavioral comparison in world 3, same RNG seed.
    def first_100_in_world(memory_list, world_id):
        steps = [r for r in memory_list
                  if r.get("type") == "agent_step"
                  and r["world_id"] == world_id][:100]
        counts = [0, 0, 0]
        for r in steps:
            counts[r["action"]] += 1
        total = sum(counts) or 1
        return [c / total for c in counts]

    federated_dist = first_100_in_world(
        bundle_loaded.memory, worlds[2].world_id)

    # Control: fresh individual, same initial seed, same RNG
    # seed at world 3, only world 3 — RNG seed override makes
    # the comparison isolate the effect of learning.
    control_kp = Ed25519PrivateKey.generate()
    control_model = TinyRNN(
        n_actions=3, hidden=4, n_extra_inputs=0, seed=42)
    control_world = ScriptedWorld(
        kp=Ed25519PrivateKey.generate(),
        initial_point_b=(800, 800),
        k_b=100, prng_seed_b=0xCCCC,
        rule=SIERPINSKI,
    )
    control_memory: List[Dict] = []
    control_session = FederatedSession(
        individual_kp=control_kp,
        model=control_model,
        world=control_world,
        initial_point=(400, 600),
        memory=control_memory,
        rule=SIERPINSKI,
        rng_seed_override=world3_rng_seed,
    )
    for _ in range(200):
        control_session.step()
    control_dist = first_100_in_world(
        control_memory, control_world.world_id)

    print("=" * 74)
    print("Federated bundles — one individual, three worlds")
    print("=" * 74)
    print()
    print(f"  Individual: {individual_id}")
    print(f"  Journeys: {len(sessions)} worlds")
    print()
    for i, (world, n_steps) in enumerate(
            zip(worlds, steps_per_world), 1):
        ctx = bundle_loaded.manifest["world_contexts"][i - 1]
        print(f"  World {i}: {world.world_id[:24]}...")
        print(f"    k_b={world.k_b}, steps={n_steps}, "
              f"first_memory_index={ctx['first_memory_index']}")
    print()
    print(f"  Bundle memory: {len(bundle_loaded.memory)} entries")
    print(f"  Bundle weights: "
          f"{bundle_loaded.manifest['model_weights_hash'][:16]}...")
    print()
    print("  Verification:")
    print(f"    basic:           {basic[0]}  ({basic[1]})")
    print(f"    full:            {full[0]}  ({full[1]})")
    print(f"    with world logs: {with_logs[0]}  ({with_logs[1]})")
    print()
    print("  Behavioral comparison, world 3 first 100 steps:")
    print(f"    (same RNG seed — the difference is weights only)")
    print(f"    Federated individual (learned in A, B, C):")
    print(f"      {[round(x, 2) for x in federated_dist]}")
    print(f"    Fresh individual (learned in C only):")
    print(f"      {[round(x, 2) for x in control_dist]}")
    print()
    print("  What this establishes:")
    print("    - An individual's identity is independent of any")
    print("      world. The same DID lives in three worlds; its")
    print("      memory is one continuous chain with world")
    print("      boundaries marked.")
    print("    - The model is continuous: weights carry over")
    print("      between worlds. The individual enters world 3")
    print("      with a policy shaped by worlds 1 and 2.")
    print("    - world_contexts is a signed, ordered claim about")
    print("      which worlds the individual entered and when.")
    print("      Basic verification confirms the claim matches")
    print("      the memory's world_entry records.")
    print("    - Full verification replays the model across all")
    print("      worlds. With-world-logs cross-checks every")
    print("      memory entry against the actual world event.")
    print("    - The behavioral comparison isolates the weight")
    print("      effect: same RNG seed, different distributions")
    print("      — the difference is learning carried over.")
    print()
    print("  Honest limit: the bundle carries world seed hashes")
    print("  but not world logs. Full verification is")
    print("  self-contained; world-log cross-check requires the")
    print("  world logs to be supplied separately.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'I dwell in Possibility –'")
    print("    'A fairer House than Prose –'")
    print("    'More numerous of Windows –'")
    print("    'Superior – for Doors –'")

    audit = {
        "individual_id": individual_id,
        "worlds_visited": [w.world_id for w in worlds],
        "memory_entries": len(bundle_loaded.memory),
        "verification": {
            "basic": basic[0],
            "full": full[0],
            "with_world_logs": with_logs[0],
        },
        "behavioral": {
            "federated_world3_first_100":
                [round(x, 3) for x in federated_dist],
            "fresh_world3_first_100":
                [round(x, 3) for x in control_dist],
        },
    }
    (root / "federated_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {root}/federated_demo.json")
    return audit
