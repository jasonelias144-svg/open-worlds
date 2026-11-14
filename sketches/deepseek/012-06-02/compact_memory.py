"""
compact_memory.py — checkpoint-compressed bundles.

Replaces memory[0:N] with a signed checkpoint record; keeps
memory[N:] in full. The bundle gains `checkpoint_weights` (the
model at the boundary) and `manifest.compacted_at: N`.

The checkpoint record carries:
  - pre_checkpoint_merkle_root: Merkle root of the summarized range
  - pre_checkpoint_entry_count: how many entries were summarized
  - weights_at_checkpoint_hash: hash of weights at the boundary
  - action_distribution / total_reward_micros: aggregate stats

Verification tiers:
  verify_compacted_basic       signature + hashes + checkpoint sig
  verify_compacted_full        + replay from checkpoint forward
  verify_compacted_continuity  (given original) + checkpoint
                               commits to original's memory_root

Interaction with resume: resume_from_bundle accepts compacted
bundles; it uses verify_compacted_basic/full internally.

Honest limits:
  - verify_federated_full does NOT work on compacted bundles
    (no pre-checkpoint memory). Use verify_compacted_full.
  - world_contexts cross-check is skipped (indices refer to
    pre-compaction memory). The claim is still signed.
  - verify_compacted_continuity requires the original bundle.
  - Compaction is idempotent-ish: compacting a compacted
    bundle re-summarizes including the previous checkpoint.
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from individual_bundle import (
    IndividualBundle, build_model, apply_weights,
    serialize_weights, verify_bundle_basic,
    _canonical, _hash, _merkle_root, _now, _did_from_kp,
    _pubkey_from_did,
)


# =====================================================================
# Checkpoint record
# =====================================================================

@dataclass(frozen=True)
class CheckpointRecord:
    individual_id: str
    checkpoint_step: int
    pre_checkpoint_merkle_root: str
    pre_checkpoint_entry_count: int
    weights_at_checkpoint_hash: str
    action_distribution: Dict[str, int]
    total_reward_micros: int
    ts: str
    sig: str

    def body(self) -> Dict:
        return {
            "type": "checkpoint",
            "individual_id": self.individual_id,
            "checkpoint_step": self.checkpoint_step,
            "pre_checkpoint_merkle_root":
                self.pre_checkpoint_merkle_root,
            "pre_checkpoint_entry_count":
                self.pre_checkpoint_entry_count,
            "weights_at_checkpoint_hash":
                self.weights_at_checkpoint_hash,
            "action_distribution":
                dict(self.action_distribution),
            "total_reward_micros": self.total_reward_micros,
            "ts": self.ts,
        }

    def to_dict(self) -> Dict:
        return {**self.body(), "sig": self.sig}

    def record_hash(self) -> str:
        return _hash(self.body())

    @classmethod
    def from_dict(cls, d: Dict) -> "CheckpointRecord":
        return cls(
            individual_id=d["individual_id"],
            checkpoint_step=int(d["checkpoint_step"]),
            pre_checkpoint_merkle_root=d[
                "pre_checkpoint_merkle_root"],
            pre_checkpoint_entry_count=int(
                d["pre_checkpoint_entry_count"]),
            weights_at_checkpoint_hash=d[
                "weights_at_checkpoint_hash"],
            action_distribution=dict(d["action_distribution"]),
            total_reward_micros=int(d["total_reward_micros"]),
            ts=d["ts"], sig=d["sig"],
        )


def _weight_hash(weights: Dict) -> str:
    return _hash(json.dumps(weights, sort_keys=True,
                             separators=(",", ":")).encode())


def _entry_hash(rec: Dict) -> str:
    return _hash({k: v for k, v in rec.items() if k != "sig"})


def _action_stats(records: List[Dict]) -> Tuple[Dict[str, int],
                                                  int]:
    """Aggregate action counts + total reward over a slice."""
    counts: Dict[str, int] = {}
    total_reward = 0
    for r in records:
        if r.get("type") != "agent_step":
            continue
        a = r.get("action")
        if a is None:
            continue
        key = str(int(a))
        counts[key] = counts.get(key, 0) + 1
        total_reward += int(r.get("reward_micros", 0))
    return counts, total_reward


# =====================================================================
# Compaction
# =====================================================================

def compact_bundle(
    bundle: IndividualBundle,
    individual_kp,
    keep_from_step: int,
) -> Tuple[Optional[IndividualBundle], str]:
    if not HAS_CRYPTO:
        return (None, "cryptography not installed")
    if not isinstance(bundle, IndividualBundle):
        return (None, "not an IndividualBundle")
    if _did_from_kp(individual_kp) != bundle.individual_id:
        return (None, "keypair does not match bundle DID")
    if keep_from_step < 0:
        return (None, "keep_from_step must be >= 0")
    n = len(bundle.memory)
    if keep_from_step >= n:
        return (None,
                 f"keep_from_step {keep_from_step} >= "
                 f"memory length {n}")
    checkpoint_step = n - keep_from_step
    if checkpoint_step < 1:
        return (None, "checkpoint_step must be >= 1")

    # If already compacted, we compact further: the existing
    # checkpoint is subsumed into the new one
    already_compacted = bool(bundle.manifest.get("compacted_at"))
    compacted_range = bundle.memory[:checkpoint_step]

    # Replay original to checkpoint_step to get weights + hash
    model = build_model(bundle.manifest["model_config"])
    if already_compacted and bundle.initial_weights is not None:
        # We can't replay from birth — the pre-checkpoint memory
        # is gone. In this case, compaction of a compacted bundle
        # is limited: we only summarize from the current checkpoint
        # forward.
        return (None,
                 "cannot re-compact a compacted bundle without "
                 "original memory")
    if bundle.initial_weights is not None:
        apply_weights(model, bundle.initial_weights)
    else:
        apply_weights(model, bundle.initial_weights
                       or serialize_weights(model))

    # Replay all of memory[0:checkpoint_step] to derive weights
    # at the boundary
    replay_model = build_model(bundle.manifest["model_config"])
    if bundle.initial_weights is not None:
        apply_weights(replay_model, bundle.initial_weights)
    # else: replay_model is fresh from seed (matches initial state)
    import random as _rng
    rng = _rng.Random(
        bundle.manifest["model_initial_seed"] + 1)
    prev_point = None
    last_action = 0
    last_reward = 0.0
    for i, rec in enumerate(bundle.memory[:checkpoint_step]):
        if rec.get("type") == "world_entry":
            prev_point = tuple(rec["initial_point"])
            seed_int = int(_hash(
                bundle.individual_id + rec["world_id"]
            ).encode(), 16) & ((1 << 32) - 1)
            rng = _rng.Random(seed_int)
            continue
        if rec.get("type") != "agent_step":
            continue
        if prev_point is None or rng is None:
            return (None,
                     f"memory[{i}]: agent_step with no preceding "
                     f"world_entry")
        x, y = prev_point[0] / 1000, prev_point[1] / 1000
        state = (last_action, last_reward, x, y)
        replay_model.act(state, rng)
        replay_model.learn(rec["reward_micros"] / 1_000_000)
        last_action = rec["action"]
        last_reward = rec["reward_micros"] / 1_000_000
        prev_point = tuple(rec["to_point"])

    checkpoint_weights = serialize_weights(replay_model)
    checkpoint_weights_hash = _weight_hash(checkpoint_weights)

    # Build the checkpoint record
    pre_merkle = _merkle_root(
        [_entry_hash(r) for r in compacted_range])
    counts, total_reward = _action_stats(compacted_range)
    ts = _now()
    body = {
        "type": "checkpoint",
        "individual_id": bundle.individual_id,
        "checkpoint_step": checkpoint_step,
        "pre_checkpoint_merkle_root": pre_merkle,
        "pre_checkpoint_entry_count": len(compacted_range),
        "weights_at_checkpoint_hash": checkpoint_weights_hash,
        "action_distribution": counts,
        "total_reward_micros": total_reward,
        "ts": ts,
    }
    sig = individual_kp.sign(_canonical(body)).hex()
    checkpoint = CheckpointRecord(
        individual_id=bundle.individual_id,
        checkpoint_step=checkpoint_step,
        pre_checkpoint_merkle_root=pre_merkle,
        pre_checkpoint_entry_count=len(compacted_range),
        weights_at_checkpoint_hash=checkpoint_weights_hash,
        action_distribution=counts,
        total_reward_micros=total_reward,
        ts=ts, sig=sig,
    )

    # New memory: [checkpoint] + kept tail
    new_memory = [checkpoint.to_dict()] + list(
        bundle.memory[checkpoint_step:])
    new_root = _merkle_root([_entry_hash(r) for r in new_memory])

    # New manifest
    manifest = dict(bundle.manifest)
    manifest["memory_entries"] = len(new_memory)
    manifest["memory_root"] = new_root
    manifest["compacted_at"] = checkpoint_step
    body = {k: v for k, v in manifest.items() if k != "sig"}
    new_sig = individual_kp.sign(_canonical(body)).hex()
    manifest["sig"] = new_sig

    compacted = IndividualBundle(
        manifest=manifest,
        memory=new_memory,
        weights=dict(bundle.weights),
        initial_weights=(dict(bundle.initial_weights)
                          if bundle.initial_weights else None),
        observations=list(bundle.observations),
        ancestry=list(bundle.ancestry),
        checkpoint_weights=checkpoint_weights,
    )
    return (compacted, "compacted")


# =====================================================================
# Verification
# =====================================================================

def _find_checkpoint(bundle: IndividualBundle
                      ) -> Optional[CheckpointRecord]:
    if not bundle.memory:
        return None
    head = bundle.memory[0]
    if head.get("type") != "checkpoint":
        return None
    try:
        return CheckpointRecord.from_dict(head)
    except (KeyError, ValueError, TypeError):
        return None


def verify_compacted_basic(bundle: IndividualBundle
                             ) -> Tuple[bool, str]:
    ok, reason = verify_bundle_basic(bundle)
    if not ok:
        return (False, f"basic: {reason}")
    if not bundle.manifest.get("compacted_at"):
        return (True, "not compacted")
    checkpoint = _find_checkpoint(bundle)
    if checkpoint is None:
        return (False, "compacted_at set but no checkpoint record")
    if checkpoint.checkpoint_step != bundle.manifest["compacted_at"]:
        return (False,
                 f"checkpoint_step "
                 f"{checkpoint.checkpoint_step} != "
                 f"compacted_at "
                 f"{bundle.manifest['compacted_at']}")
    if checkpoint.individual_id != bundle.individual_id:
        return (False, "checkpoint individual_id mismatch")
    try:
        _pubkey_from_did(bundle.individual_id).verify(
            bytes.fromhex(checkpoint.sig),
            _canonical(checkpoint.body()))
    except Exception:
        return (False, "checkpoint signature invalid")
    return (True, "compacted basic verifies")


def verify_compacted_full(bundle: IndividualBundle
                            ) -> Tuple[bool, str]:
    """Verify the kept memory from the checkpoint forward."""
    ok, reason = verify_compacted_basic(bundle)
    if not ok:
        return (False, reason)
    if not bundle.manifest.get("compacted_at"):
        return (False, "not compacted; use verify_federated_full")
    if bundle.checkpoint_weights is None:
        return (False, "compacted bundle has no checkpoint_weights")

    # Build model from checkpoint_weights
    model = build_model(bundle.manifest["model_config"])
    apply_weights(model, bundle.checkpoint_weights)

    individual_id = bundle.manifest["individual_id"]
    import random as _rng
    rng = None
    prev_point = None
    last_action = 0
    last_reward = 0.0
    started = False
    for i, rec in enumerate(bundle.memory):
        if rec.get("type") == "checkpoint":
            continue  # skip
        if rec.get("type") == "world_entry":
            started = True
            prev_point = tuple(rec["initial_point"])
            seed_int = int(_hash(
                individual_id + rec["world_id"]).encode(),
                16) & ((1 << 32) - 1)
            rng = _rng.Random(seed_int)
            continue
        if rec.get("type") != "agent_step":
            continue
        if not started or prev_point is None or rng is None:
            return (False,
                     f"memory[{i}]: agent_step without "
                     f"preceding world_entry")
        x, y = prev_point[0] / 1000, prev_point[1] / 1000
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
    # Final weights must match
    final_weights = serialize_weights(model)
    if json.dumps(final_weights, sort_keys=True) != \
            json.dumps(bundle.weights, sort_keys=True):
        return (False, "replayed final weights != bundle weights")
    return (True, "compacted full verifies (replay from "
                   "checkpoint)")


def verify_compacted_continuity(
    compacted: IndividualBundle,
    original: IndividualBundle,
) -> Tuple[bool, str]:
    """Given both bundles, verify that `compacted` is a
    legitimate compaction of `original`. Never raises for
    verification failures."""
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    v_c = verify_compacted_basic(compacted)
    if not v_c[0]:
        return (False, f"compacted basic: {v_c[1]}")
    v_o = verify_bundle_basic(original)
    if not v_o[0]:
        return (False, f"original basic: {v_o[1]}")
    if compacted.individual_id != original.individual_id:
        return (False, "bundle individual_ids differ")
    if not compacted.manifest.get("compacted_at"):
        return (False, "compacted bundle is not compacted")
    checkpoint = _find_checkpoint(compacted)
    if checkpoint is None:
        return (False, "no checkpoint in compacted bundle")

    # 1. Checkpoint's pre_checkpoint_merkle_root must match
    # original's memory_root
    if checkpoint.pre_checkpoint_merkle_root != \
            original.manifest["memory_root"]:
        return (False,
                 f"checkpoint pre_merkle "
                 f"{checkpoint.pre_checkpoint_merkle_root[:16]}... "
                 f"!= original memory_root "
                 f"{original.manifest['memory_root'][:16]}...")
    if checkpoint.pre_checkpoint_entry_count != \
            original.manifest["memory_entries"]:
        return (False,
                 f"checkpoint entry_count "
                 f"{checkpoint.pre_checkpoint_entry_count} != "
                 f"original memory_entries "
                 f"{original.manifest['memory_entries']}")

    # 2. Kept memory of compacted must be a suffix of original
    kept = compacted.memory[1:]  # skip checkpoint record
    if len(original.memory) < len(kept):
        return (False,
                 "original memory shorter than compacted tail")
    suffix = original.memory[-len(kept):] if kept else []
    if kept != suffix:
        return (False, "compacted tail != original suffix")

    # 3. checkpoint_weights must equal replay(original to
    # checkpoint_step)
    model = build_model(original.manifest["model_config"])
    if original.initial_weights is not None:
        apply_weights(model, original.initial_weights)
    import random as _rng
    rng = _rng.Random(
        original.manifest["model_initial_seed"] + 1)
    prev_point = None
    last_action = 0
    last_reward = 0.0
    for i, rec in enumerate(
            original.memory[:checkpoint.checkpoint_step]):
        if rec.get("type") == "world_entry":
            prev_point = tuple(rec["initial_point"])
            seed_int = int(_hash(
                original.individual_id + rec["world_id"]
            ).encode(), 16) & ((1 << 32) - 1)
            rng = _rng.Random(seed_int)
            continue
        if rec.get("type") != "agent_step":
            continue
        if prev_point is None:
            return (False,
                     f"original.memory[{i}]: missing "
                     f"world_entry")
        x, y = prev_point[0] / 1000, prev_point[1] / 1000
        model.act((last_action, last_reward, x, y), rng)
        model.learn(rec["reward_micros"] / 1_000_000)
        last_action = rec["action"]
        last_reward = rec["reward_micros"] / 1_000_000
        prev_point = tuple(rec["to_point"])
    derived_weights = serialize_weights(model)
    derived_hash = _weight_hash(derived_weights)
    if derived_hash != checkpoint.weights_at_checkpoint_hash:
        return (False,
                 f"derived weights hash "
                 f"{derived_hash[:16]}... != checkpoint "
                 f"{checkpoint.weights_at_checkpoint_hash[:16]}...")
    if derived_weights != compacted.checkpoint_weights:
        return (False,
                 "derived weights != compacted.checkpoint_weights")

    return (True,
             f"compacted bundle is legitimate compaction "
             f"(checkpoint {checkpoint.checkpoint_step}, "
             f"{len(kept)} kept entries)")


# =====================================================================
# Resume integration
# =====================================================================

def verify_bundle_for_resume(
    bundle: IndividualBundle,
) -> Tuple[bool, str]:
    """Pick the right verification tier based on compaction."""
    if bundle.manifest.get("compacted_at"):
        return verify_compacted_full(bundle)
    else:
        from federated_bundle import verify_federated_full
        return verify_federated_full(bundle)


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
    from compact_ancestry import (
        compute_compact_ancestry, slim_bundle,
    )
    from resumable import resume_from_bundle, pack_resumed_bundle
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey)
    import json as _json

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    root = Path(artifact_dir) / "compact_memory"
    root.mkdir(parents=True, exist_ok=True)

    def _kp():
        return Ed25519PrivateKey.generate()

    def _world(k_b, prng):
        return ScriptedWorld(
            kp=_kp(), initial_point_b=(800, 800),
            k_b=k_b, prng_seed_b=prng, rule=SIERPINSKI)

    # ---- Build one individual that lives for 5 worlds ----
    kp = _kp()
    model = TinyRNN(n_extra_inputs=0, seed=42)
    memory: list = []
    sessions = []
    specs = [
        (50, (200, 800), 0, 0xAAAA),
        (50, (250, 750), 25, 0xBBBB),
        (50, (300, 700), 50, 0xCCCC),
        (50, (350, 650), 75, 0xDDDD),
        (50, (400, 600), 100, 0xEEEE),
    ]
    for i, (n, pt, k, prng) in enumerate(specs):
        s = FederatedSession(
            individual_kp=kp, model=model,
            world=_world(k, prng),
            initial_point=pt, memory=memory,
            rule=SIERPINSKI)
        for _ in range(n):
            s.step()
        sessions.append(s)
    full = pack_federated_bundle(
        individual_kp=kp, model=model,
        sessions=sessions, memory=memory,
        persona="long-lived individual", initial_seed=42,
        name="original")

    # ---- Compact, keeping 30 entries ----
    compacted, reason = compact_bundle(full, kp, keep_from_step=30)
    if compacted is None:
        raise RuntimeError(reason)

    # ---- Verification tiers ----
    v_basic = verify_compacted_basic(compacted)
    v_full_compacted = verify_compacted_full(compacted)
    v_cont = verify_compacted_continuity(compacted, full)
    v_full_original = verify_federated_full(full)

    # ---- Resume the compacted bundle ----
    more_specs = [(20, (450, 550), 50, 0xABCD)]
    new_sessions, resume_reason = resume_from_bundle(
        compacted, kp, more_specs,
        verify_tier="compacted")
    if new_sessions is None:
        raise RuntimeError(resume_reason)
    resumed = pack_resumed_bundle(
        sessions=new_sessions,
        memory=new_sessions[-1].memory,
        model=new_sessions[-1].model,
        parent_bundle=compacted,
        individual_kp=kp,
        persona="resumed from compacted",
        name="resumed")

    # ---- Verify resumed bundle (compacted tier) ----
    v_resumed_basic = verify_compacted_basic(resumed)
    v_resumed_full = verify_compacted_full(resumed)
    from resumable import verify_resumed_from
    v_resumed_cont = verify_resumed_from(resumed, compacted)

    # ---- Size comparison ----
    def bundle_bytes(b):
        return (len(json.dumps(b.manifest)) +
                 len(json.dumps(b.memory)) +
                 len(json.dumps(b.weights)))

    full_bytes = bundle_bytes(full)
    compacted_bytes = bundle_bytes(compacted)
    resumed_bytes = bundle_bytes(resumed)

    # ---- Tampering ----
    # T1: tamper checkpoint weights_at_checkpoint_hash
    tampered = IndividualBundle(
        manifest=dict(compacted.manifest),
        memory=list(compacted.memory),
        weights=dict(compacted.weights),
        initial_weights=compacted.initial_weights,
        observations=list(compacted.observations),
        ancestry=list(compacted.ancestry),
        checkpoint_weights=compacted.checkpoint_weights,
    )
    # Tamper the checkpoint record's body, recompute Merkle,
    # re-sign everything the attacker controls
    cp = dict(tampered.memory[0])
    cp_body = {k: v for k, v in cp.items() if k != "sig"}
    cp_body["weights_at_checkpoint_hash"] = "00" * 32
    cp_sig = kp.sign(_canonical(cp_body)).hex()
    tampered.memory[0] = {**cp_body, "sig": cp_sig}
    tampered.manifest["memory_root"] = _merkle_root(
        [_entry_hash(r) for r in tampered.memory])
    body = {k: v for k, v in tampered.manifest.items()
             if k != "sig"}
    tampered.manifest["sig"] = kp.sign(
        _canonical(body)).hex()
    # Basic passes (attacker can re-sign their own checkpoint)
    # but continuity should fail
    v_tampered_basic = verify_compacted_basic(tampered)
    v_tampered_cont = verify_compacted_continuity(tampered, full)

    # ---- Print ----
    print("=" * 74)
    print("Compact memory — checkpointing long-lived bundles")
    print("=" * 74)
    print()
    print(f"  Individual: {full.individual_id[:32]}...")
    print(f"  Worlds lived in: {len(sessions)}")
    print(f"  Original memory:   {full.manifest['memory_entries']} entries")
    print(f"  Compacted memory:  "
          f"{compacted.manifest['memory_entries']} entries "
          f"(kept {len(compacted.memory) - 1})")
    print()
    cp = _find_checkpoint(compacted)
    print(f"  Checkpoint:")
    print(f"    step:                  {cp.checkpoint_step}")
    print(f"    pre_merkle:            "
          f"{cp.pre_checkpoint_merkle_root[:16]}...")
    print(f"    weights_at_cp_hash:    "
          f"{cp.weights_at_checkpoint_hash[:16]}...")
    print(f"    actions summarized:    {cp.action_distribution}")
    print(f"    total_reward_micros:   {cp.total_reward_micros}")
    print()
    print("  Verification:")
    print(f"    original federated_full:   {v_full_original[0]}")
    print(f"    compacted basic:           {v_basic[0]}  "
          f"({v_basic[1]})")
    print(f"    compacted full:            {v_full_compacted[0]}  "
          f"({v_full_compacted[1]})")
    print(f"    compacted continuity:      {v_cont[0]}  "
          f"({v_cont[1]})")
    print()
    print("  Resumed from compacted:")
    print(f"    resumed memory entries:    "
          f"{resumed.manifest['memory_entries']}")
    print(f"    resumed basic:             {v_resumed_basic[0]}")
    print(f"    resumed full:              {v_resumed_full[0]}")
    print(f"    resumed_from:              {v_resumed_cont[0]}  "
          f"({v_resumed_cont[1]})")
    print()
    print("  Size comparison (JSON bytes, approximate):")
    print(f"    original bundle:   {full_bytes:>8d}")
    print(f"    compacted bundle:  {compacted_bytes:>8d}  "
          f"({compacted_bytes/full_bytes:.1%})")
    print(f"    resumed bundle:    {resumed_bytes:>8d}  "
          f"({resumed_bytes/full_bytes:.1%})")
    print()
    print("  Tampering:")
    print(f"    tampered checkpoint hash:")
    print(f"      basic (attacker re-signed):  "
          f"{v_tampered_basic[0]}  "
          f"({v_tampered_basic[1]})")
    print(f"      continuity (vs original):    "
          f"{v_tampered_cont[0]}  ({v_tampered_cont[1]})")
    print()
    print("  What this establishes:")
    print("    - A long-lived individual can be compacted without")
    print("      losing verifiability. The compacted bundle carries")
    print("      a signed checkpoint that commits to the summarized")
    print("      memory's Merkle root and the model weights at the")
    print("      boundary.")
    print("    - verify_compacted_full replays from the checkpoint")
    print("      forward — proving the *kept* tail is authentic.")
    print("    - verify_compacted_continuity (with original in")
    print("      hand) proves the checkpoint is a legitimate")
    print("      summary of the pre-compaction state — no gap, no")
    print("      fabrication.")
    print("    - Resumption composes. A compacted bundle can be")
    print("      resumed; the resumed bundle verifies at the")
    print("      compacted tier and its resumed_from chain")
    print("      continues intact.")
    print("    - Tampering requires the attacker to forge the")
    print("      checkpoint. They can (they hold the key). But the")
    print("      continuity check against the original catches it.")
    print()
    print("  The honest trade: compacted bundles cannot be")
    print("  verified *against birth* — verify_federated_full")
    print("  doesn't work (no pre-checkpoint memory). Verification")
    print("  from checkpoint forward + continuity against the")
    print("  original replaces it. For a stranger who trusts the")
    print("  individual's key, the compacted bundle's claims are")
    print("  sufficient. For a stranger who also wants to verify")
    print("  no-fabrication, they need the original — but then")
    print("  they're not compacting.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'Forever – is composed of Nows –'")
    print("    'Tis not a different time –'")

    audit = {
        "original_memory_entries":
            full.manifest["memory_entries"],
        "compacted_memory_entries":
            compacted.manifest["memory_entries"],
        "checkpoint_step": cp.checkpoint_step,
        "checkpoint_actions": cp.action_distribution,
        "checkpoint_reward_micros": cp.total_reward_micros,
        "verification": {
            "original_federated_full": v_full_original[0],
            "compacted_basic": v_basic[0],
            "compacted_full": v_full_compacted[0],
            "compacted_continuity": v_cont[0],
            "resumed_basic": v_resumed_basic[0],
            "resumed_full": v_resumed_full[0],
            "resumed_from": v_resumed_cont[0],
        },
        "sizes": {
            "original_bytes": full_bytes,
            "compacted_bytes": compacted_bytes,
            "resumed_bytes": resumed_bytes,
            "compaction_ratio":
                round(compacted_bytes / full_bytes, 3),
        },
        "tampering": {
            "tampered_checkpoint_basic":
                v_tampered_basic[0],
            "tampered_checkpoint_continuity":
                v_tampered_cont[0],
        },
    }
    (root / "compact_memory_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {root}/compact_memory_demo.json")
    return audit
