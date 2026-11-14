"""
forking.py — branch an individual into a new lineage.

fork_from_bundle(parent, fork_kp, fork_at_entry, world_specs)
  -> (sessions, weights_at_k, reason)
pack_fork_bundle(sessions, memory, model, parent, fork_kp,
                  fork_record, ...) -> IndividualBundle
verify_forked_basic(bundle) -> (ok, reason)
verify_forked_full(bundle)  -> (ok, reason)
verify_fork_continuity(fork, parent) -> (ok, reason)

Fork manifest adds:
  forked_from, fork_at_entry, fork_at_memory_root,
  fork_weights_hash, fork_record (parent-signed).
Fork's initial_weights = parent's weights at K.

Honest limits:
  - Single-parent fork (forking a fork is supported but
    forking a compacted parent is not).
  - Mid-world fork is supported: the fork inherits parent's
    world X up to K, then starts its own new world at K.
  - No revocation of a fork. The parent cannot "unfork" —
    it continues, and the fork is a separate entity.
"""

import json
from dataclasses import dataclass
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
from federated_bundle import (
    FederatedSession, verify_federated_full,
)
from federated_spawn import _replay_federated_to_index
from world_agent_coupling import ScriptedWorld
from coupled_learners import SIERPINSKI


def _entry_hash(rec: Dict) -> str:
    return _hash({k: v for k, v in rec.items() if k != "sig"})


def _weights_hash(weights: Dict) -> str:
    return _hash(json.dumps(weights, sort_keys=True,
                             separators=(",", ":")).encode())


# =====================================================================
# ForkRecord (signed by parent)
# =====================================================================

@dataclass(frozen=True)
class ForkRecord:
    original_id: str
    fork_id: str
    fork_at_entry: int
    fork_at_memory_root: str
    fork_weights_hash: str
    ts: str
    sig: str

    def __post_init__(self):
        if self.original_id == self.fork_id:
            raise ValueError("fork_id must differ from original_id")
        if self.fork_at_entry < 0:
            raise ValueError("fork_at_entry must be >= 0")
        if len(self.fork_at_memory_root) != 64:
            raise ValueError("fork_at_memory_root must be 64 hex")

    def body(self) -> Dict:
        return {
            "type": "fork_record",
            "original_id": self.original_id,
            "fork_id": self.fork_id,
            "fork_at_entry": int(self.fork_at_entry),
            "fork_at_memory_root": self.fork_at_memory_root,
            "fork_weights_hash": self.fork_weights_hash,
            "ts": self.ts,
        }

    def to_dict(self) -> Dict:
        return {**self.body(), "sig": self.sig}

    @classmethod
    def from_dict(cls, d: Dict) -> "ForkRecord":
        return cls(
            original_id=d["original_id"],
            fork_id=d["fork_id"],
            fork_at_entry=int(d["fork_at_entry"]),
            fork_at_memory_root=d["fork_at_memory_root"],
            fork_weights_hash=d["fork_weights_hash"],
            ts=d["ts"], sig=d["sig"],
        )


# =====================================================================
# Fork operation
# =====================================================================

def fork_from_bundle(
    parent: IndividualBundle,
    fork_kp,
    fork_at_entry: int,
    world_specs: List[Tuple[int, Tuple[int, int], int, int]],
    rule=SIERPINSKI,
) -> Tuple[Optional[List[FederatedSession]],
            Optional[Dict],
            Optional[ForkRecord],
            str]:
    """Branch the parent into a new individual.

    Returns (sessions, weights_at_k, fork_record, reason).
    Never raises for verification failures."""
    if not HAS_CRYPTO:
        return (None, None, None, "cryptography not installed")
    if not isinstance(parent, IndividualBundle):
        return (None, None, None, "not an IndividualBundle")
    if world_specs is None or len(world_specs) == 0:
        return (None, None, None,
                 "world_specs must not be empty")
    if parent.manifest.get("compacted_at"):
        return (None, None, None,
                 "forking a compacted parent is not supported "
                 "in this cycle")
    n = parent.manifest["memory_entries"]
    if not (0 <= fork_at_entry <= n):
        return (None, None, None,
                 f"fork_at_entry {fork_at_entry} out of [0, {n}]")

    # Parent must verify internally
    v_basic = verify_bundle_basic(parent)
    if not v_basic[0]:
        return (None, None, None, f"parent basic: {v_basic[1]}")
    v_full = verify_federated_full(parent)
    if not v_full[0]:
        return (None, None, None, f"parent full: {v_full[1]}")

    # Derive parent's weights at K by replaying [0:K]
    parent_model, reason = _replay_federated_to_index(
        parent, fork_at_entry)
    if parent_model is None:
        return (None, None, None,
                 f"parent replay to {fork_at_entry} failed: "
                 f"{reason}")
    weights_at_k = serialize_weights(parent_model)

    # Compute prefix Merkle root
    prefix = parent.memory[:fork_at_entry]
    prefix_root = _merkle_root([_entry_hash(r) for r in prefix])
    if prefix_root != parent.manifest["memory_root"] \
            and fork_at_entry != n:
        # n == memory_entries: prefix is full memory, root
        # equals manifest root. For K < n, prefix_root is
        # the root of the prefix, computed here.
        pass

    # Fork's new sessions start with the inherited prefix
    fork_kp_did = _did_from_kp(fork_kp)
    memory: List[Dict] = list(prefix)
    model = build_model(parent.manifest["model_config"])
    apply_weights(model, weights_at_k)

    sessions: List[FederatedSession] = []
    for idx, (n_steps, initial_point, k_b, prng_seed_b) \
            in enumerate(world_specs):
        if n_steps < 0:
            return (None, None, None,
                     f"world_specs[{idx}]: negative n_steps")
        world = ScriptedWorld(
            kp=Ed25519PrivateKey.generate(),
            initial_point_b=(800, 800),
            k_b=int(k_b),
            prng_seed_b=int(prng_seed_b),
            rule=rule,
        )
        s = FederatedSession(
            individual_kp=fork_kp,
            model=model,
            world=world,
            initial_point=tuple(initial_point),
            memory=memory,
            rule=rule,
        )
        for _ in range(n_steps):
            s.step()
        sessions.append(s)

    # Fork record (signed by parent)
    weights_hash = _weights_hash(weights_at_k)
    ts = _now()
    rec_body = {
        "type": "fork_record",
        "original_id": parent.individual_id,
        "fork_id": fork_kp_did,
        "fork_at_entry": int(fork_at_entry),
        "fork_at_memory_root": prefix_root,
        "fork_weights_hash": weights_hash,
        "ts": ts,
    }
    # Parent signs it — but we need the parent's *private* key.
    # fork_from_bundle only gets the fork's kp. The caller
    # must supply the parent's private key separately.
    return (sessions, weights_at_k, None,
             "caller must call sign_fork_record_with_parent")


def sign_fork_record_with_parent(
    parent_kp,
    parent: IndividualBundle,
    fork_id: str,
    fork_at_entry: int,
    fork_at_memory_root: str,
    fork_weights_hash: str,
) -> ForkRecord:
    """Build and sign the fork record (called by parent's key
    holder)."""
    if _did_from_kp(parent_kp) != parent.individual_id:
        raise ValueError("parent_kp does not match parent DID")
    ts = _now()
    body = {
        "type": "fork_record",
        "original_id": parent.individual_id,
        "fork_id": fork_id,
        "fork_at_entry": int(fork_at_entry),
        "fork_at_memory_root": fork_at_memory_root,
        "fork_weights_hash": fork_weights_hash,
        "ts": ts,
    }
    sig = parent_kp.sign(_canonical(body)).hex()
    return ForkRecord(
        original_id=parent.individual_id,
        fork_id=fork_id,
        fork_at_entry=fork_at_entry,
        fork_at_memory_root=fork_at_memory_root,
        fork_weights_hash=fork_weights_hash,
        ts=ts, sig=sig,
    )


# =====================================================================
# Pack
# =====================================================================

def pack_fork_bundle(
    sessions: List[FederatedSession],
    memory: List[Dict],
    model,
    parent_bundle: IndividualBundle,
    fork_kp,
    fork_record: ForkRecord,
    persona: str,
    name: str,
) -> IndividualBundle:
    if not HAS_CRYPTO:
        raise RuntimeError("cryptography not installed")
    fork_id = _did_from_kp(fork_kp)
    if fork_record.fork_id != fork_id:
        raise ValueError("fork_record.fork_id != fork kp DID")
    if fork_record.original_id != parent_bundle.individual_id:
        raise ValueError("fork_record.original_id != parent DID")

    K = fork_record.fork_at_entry
    if len(memory) < K:
        raise ValueError("memory shorter than fork_at_entry")

    # Prefix entries come from parent; verify count
    prefix = memory[:K]
    suffix = memory[K:]
    if len(prefix) != K:
        raise ValueError("prefix length mismatch")

    weights_at_k = dict(sessions[0].model.__class__.__dict__.get(
        "_fork_weights_at_k", {})) if False else None
    # Actually, reconstruct weights_at_k from initial_weights
    # of the first session's model? No — the first session's
    # model has learned further. We need to store weights_at_k
    # at fork time. Caller supplies via fork_record.fork_weights_hash.
    # But packing needs the actual weights. Let me require the
    # caller to pass them.
    return _pack_fork(
        sessions=sessions, memory=memory, model=model,
        parent_bundle=parent_bundle, fork_kp=fork_kp,
        fork_record=fork_record, persona=persona, name=name,
    )


def _pack_fork(
    sessions, memory, model, parent_bundle, fork_kp,
    fork_record, persona, name,
):
    # We need weights_at_k for the bundle's initial_weights.
    # Recompute by replaying parent to K.
    parent_model, reason = _replay_federated_to_index(
        parent_bundle, fork_record.fork_at_entry)
    if parent_model is None:
        raise RuntimeError(f"cannot reconstruct weights: {reason}")
    weights_at_k = serialize_weights(parent_model)
    if _weights_hash(weights_at_k) != \
            fork_record.fork_weights_hash:
        raise RuntimeError(
            "reconstructed weights hash != fork record's claim")

    # Merge contexts: parent's prefix + new (indices shifted)
    parent_contexts = list(
        parent_bundle.manifest.get("world_contexts", []))
    K = fork_record.fork_at_entry
    prefix_contexts = [
        dict(c) for c in parent_contexts
        if c.get("first_memory_index", 0) < K
    ]
    # Only keep contexts whose first_memory_index is < K
    # (all the fork's new contexts come from sessions)
    new_contexts = [dict(s.world_context) for s in sessions]
    all_contexts = prefix_contexts + new_contexts

    # Weights
    weights = serialize_weights(model)
    weights_hash = _hash(json.dumps(
        weights, sort_keys=True,
        separators=(",", ":")).encode())
    memory_hashes = [_entry_hash(r) for r in memory]
    memory_root = _merkle_root(memory_hashes)
    obs_hash = _hash("[]")
    initial_weights_hash = fork_record.fork_weights_hash

    fork_id = _did_from_kp(fork_kp)
    body: Dict = {
        "kind": "individual_bundle",
        "version": "1.4",
        "individual_id": fork_id,
        "name": name,
        "persona": persona,
        "created_at": _now(),
        "parent_did": None,  # fork is a new root
        "lineage_root": fork_id,  # new lineage
        "model_config": parent_bundle.manifest["model_config"],
        "model_initial_seed":
            parent_bundle.manifest["model_initial_seed"],
        "model_weights_hash": weights_hash,
        "observes": parent_bundle.manifest.get("observes", False),
        "memory_entries": len(memory),
        "memory_root": memory_root,
        "observations_hash": obs_hash,
        "world_contexts": all_contexts,
        "initial_weights_hash": initial_weights_hash,
        "forked_from": parent_bundle.individual_id,
        "fork_at_entry": K,
        "fork_at_memory_root": fork_record.fork_at_memory_root,
        "fork_record": fork_record.to_dict(),
        "ts": _now(),
    }
    sig = fork_kp.sign(_canonical(body)).hex()
    return IndividualBundle(
        manifest={**body, "sig": sig},
        memory=list(memory),
        weights=weights,
        initial_weights=dict(weights_at_k),
        observations=[],
        ancestry=[],
        checkpoint_weights=None,
    )


# =====================================================================
# Verification
# =====================================================================

def verify_forked_basic(bundle: IndividualBundle
                         ) -> Tuple[bool, str]:
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    if not isinstance(bundle, IndividualBundle):
        return (False, "not an IndividualBundle")
    if not bundle.manifest.get("forked_from"):
        # Non-fork — delegate to base
        return verify_bundle_basic(bundle)

    fork_record_dict = bundle.manifest.get("fork_record")
    if not fork_record_dict:
        return (False, "forked_from set but no fork_record")
    try:
        fork_record = ForkRecord.from_dict(fork_record_dict)
    except (KeyError, ValueError, TypeError) as e:
        return (False, f"malformed fork_record: {e}")

    # 1. Fork record fields match manifest
    if fork_record.fork_id != bundle.individual_id:
        return (False, "fork_record.fork_id != individual_id")
    if fork_record.original_id != bundle.manifest["forked_from"]:
        return (False, "fork_record.original_id != forked_from")
    if fork_record.fork_at_entry != bundle.manifest["fork_at_entry"]:
        return (False, "fork_record.fork_at_entry != "
                        "manifest.fork_at_entry")
    if fork_record.fork_at_memory_root != \
            bundle.manifest["fork_at_memory_root"]:
        return (False, "fork_record.fork_at_memory_root != "
                        "manifest.fork_at_memory_root")
    if fork_record.fork_weights_hash != \
            bundle.manifest.get("initial_weights_hash"):
        return (False, "fork_record.fork_weights_hash != "
                        "manifest.initial_weights_hash")

    # 2. Fork record signed by parent
    try:
        _pubkey_from_did(fork_record.original_id).verify(
            bytes.fromhex(fork_record.sig),
            _canonical(fork_record.body()))
    except Exception:
        return (False, "fork_record signature invalid (parent)")

    # 3. Manifest signed by fork
    body = {k: v for k, v in bundle.manifest.items() if k != "sig"}
    try:
        _pubkey_from_did(bundle.individual_id).verify(
            bytes.fromhex(bundle.manifest["sig"]),
            _canonical(body))
    except Exception:
        return (False, "manifest signature invalid (fork)")

    # 4. Memory prefix: sigs verify against parent
    K = fork_record.fork_at_entry
    if K > len(bundle.memory):
        return (False, "fork_at_entry > memory length")
    prefix = bundle.memory[:K]
    for i, rec in enumerate(prefix):
        signer = bundle.manifest["forked_from"]
        try:
            _pubkey_from_did(signer).verify(
                bytes.fromhex(rec["sig"]),
                _canonical({k: v for k, v in rec.items()
                             if k != "sig"}))
        except Exception:
            return (False,
                     f"memory[{i}]: prefix sig invalid "
                     f"(expected parent signer)")
    prefix_root = _merkle_root([_entry_hash(r) for r in prefix])
    if prefix_root != bundle.manifest["fork_at_memory_root"]:
        return (False, "prefix Merkle root mismatch")

    # 5. Memory suffix: sigs verify against fork
    suffix = bundle.memory[K:]
    for i, rec in enumerate(suffix):
        try:
            _pubkey_from_did(bundle.individual_id).verify(
                bytes.fromhex(rec["sig"]),
                _canonical({k: v for k, v in rec.items()
                             if k != "sig"}))
        except Exception:
            return (False,
                     f"memory[{K+i}]: suffix sig invalid "
                     f"(expected fork signer)")

    # 6. Memory invariants
    if len(bundle.memory) != bundle.manifest["memory_entries"]:
        return (False, "memory_entries mismatch")
    full_root = _merkle_root(
        [_entry_hash(r) for r in bundle.memory])
    if full_root != bundle.manifest["memory_root"]:
        return (False, "memory_root mismatch")

    # 7. Initial weights present and hash matches
    if bundle.initial_weights is None:
        return (False, "fork missing initial_weights")
    iw_hash = _weights_hash(bundle.initial_weights)
    if iw_hash != bundle.manifest.get("initial_weights_hash"):
        return (False, "initial_weights hash mismatch")

    # 8. Weights hash
    w_hash = _hash(json.dumps(
        bundle.weights, sort_keys=True,
        separators=(",", ":")).encode())
    if w_hash != bundle.manifest["model_weights_hash"]:
        return (False, "weights hash mismatch")

    return (True,
             f"forked basic verifies (K={K}, "
             f"suffix {len(suffix)} entries)")


def verify_forked_full(bundle: IndividualBundle
                        ) -> Tuple[bool, str]:
    """Basic + replay [K:] from initial_weights."""
    ok, reason = verify_forked_basic(bundle)
    if not ok:
        return (False, reason)
    if not bundle.manifest.get("forked_from"):
        # Non-fork — delegate
        return verify_federated_full(bundle)

    K = bundle.manifest["fork_at_entry"]
    model = build_model(bundle.manifest["model_config"])
    apply_weights(model, bundle.initial_weights)

    individual_id = bundle.manifest["individual_id"]
    import random as _rng
    rng = None
    prev_point = None
    last_action = 0
    last_reward = 0.0
    started = False
    for i, rec in enumerate(bundle.memory[K:]):
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
                     f"suffix[{i}]: agent_step without "
                     f"preceding world_entry")
        x, y = prev_point[0] / 1000, prev_point[1] / 1000
        state = (last_action, last_reward, x, y)
        expected = model.act(state, rng)
        if expected != rec["action"]:
            return (False,
                     f"suffix[{i}]: recorded {rec['action']} "
                     f"!= replayed {expected}")
        model.learn(rec["reward_micros"] / 1_000_000)
        last_action = rec["action"]
        last_reward = rec["reward_micros"] / 1_000_000
        prev_point = tuple(rec["to_point"])
    final_weights = serialize_weights(model)
    if json.dumps(final_weights, sort_keys=True) != \
            json.dumps(bundle.weights, sort_keys=True):
        return (False, "replayed weights != bundle weights")
    return (True, "forked full verifies (replay from K)")


def verify_fork_continuity(
    fork: IndividualBundle,
    parent: IndividualBundle,
) -> Tuple[bool, str]:
    """Confirm the fork is a legitimate fork of parent.

    Checks: fork basic + prefix matches parent up to K +
    parent's derived weights at K == fork's initial_weights.
    """
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    v = verify_forked_basic(fork)
    if not v[0]:
        return (False, f"forked basic: {v[1]}")
    if fork.manifest["forked_from"] != parent.individual_id:
        return (False,
                 "fork.forked_from != parent.individual_id")
    v_p = verify_bundle_basic(parent)
    if not v_p[0]:
        return (False, f"parent basic: {v_p[1]}")
    if parent.manifest.get("compacted_at"):
        return (False, "parent is compacted; continuity "
                        "verification not supported")

    K = fork.manifest["fork_at_entry"]
    if K > len(parent.memory):
        return (False,
                 f"fork_at_entry {K} > parent.memory length "
                 f"{len(parent.memory)}")

    # Prefix of fork == prefix of parent
    fork_prefix = fork.memory[:K]
    parent_prefix = parent.memory[:K]
    if fork_prefix != parent_prefix:
        return (False, "fork prefix != parent prefix")

    # Derive parent's weights at K
    parent_model, reason = _replay_federated_to_index(parent, K)
    if parent_model is None:
        return (False, f"parent replay: {reason}")
    derived_weights = serialize_weights(parent_model)
    derived_hash = _weights_hash(derived_weights)
    if derived_hash != fork.manifest["fork_weights_hash"]:
        return (False,
                 f"parent's derived weights at K "
                 f"({derived_hash[:16]}...) != fork's claim "
                 f"({fork.manifest['fork_weights_hash'][:16]}...)")
    if derived_weights != fork.initial_weights:
        return (False,
                 "derived weights != fork.initial_weights")

    return (True,
             f"fork continuity verifies (K={K})")


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir=None):
    from pathlib import Path
    from federated_bundle import (
        FederatedSession, pack_federated_bundle,
        verify_federated_full,
    )
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey)
    from coupled_learners import TinyRNN
    import json as _json

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    root = Path(artifact_dir) / "forking"
    root.mkdir(parents=True, exist_ok=True)

    def _kp():
        return Ed25519PrivateKey.generate()

    def _world(k_b, prng):
        return ScriptedWorld(
            kp=_kp(), initial_point_b=(800, 800),
            k_b=k_b, prng_seed_b=prng, rule=SIERPINSKI)

    # ---- Parent lives in two worlds ----
    parent_kp = _kp()
    parent_id = _did_from_kp(parent_kp)
    parent_model = TinyRNN(n_extra_inputs=0, seed=42)
    parent_memory: List[Dict] = []
    parent_sessions = []
    for i, (n, pt, k, prng) in enumerate([
        (25, (200, 800), 0, 0xAAAA),
        (25, (250, 750), 50, 0xBBBB),
    ]):
        s = FederatedSession(
            individual_kp=parent_kp, model=parent_model,
            world=_world(k, prng),
            initial_point=pt, memory=parent_memory,
            rule=SIERPINSKI)
        for _ in range(n):
            s.step()
        parent_sessions.append(s)
    parent_bundle = pack_federated_bundle(
        individual_kp=parent_kp, model=parent_model,
        sessions=parent_sessions, memory=parent_memory,
        persona="original", initial_seed=42, name="original")
    K = parent_bundle.manifest["memory_entries"]

    # ---- Parent signs fork record, fork inherits at tip ----
    fork_kp = _kp()
    fork_id = _did_from_kp(fork_kp)

    # Derive weights at K (K == memory_entries, so all of it)
    from federated_spawn import _replay_federated_to_index
    parent_model_at_k, reason = _replay_federated_to_index(
        parent_bundle, K)
    assert parent_model_at_k is not None, reason
    weights_at_k = serialize_weights(parent_model_at_k)

    prefix_root = _merkle_root(
        [_entry_hash(r) for r in parent_bundle.memory[:K]])

    fork_record = sign_fork_record_with_parent(
        parent_kp=parent_kp, parent=parent_bundle,
        fork_id=fork_id, fork_at_entry=K,
        fork_at_memory_root=prefix_root,
        fork_weights_hash=_weights_hash(weights_at_k),
    )

    # ---- Fork lives in two new worlds ----
    fork_sessions, fork_weights_at_k, _, reason = fork_from_bundle(
        parent=parent_bundle, fork_kp=fork_kp,
        fork_at_entry=K,
        world_specs=[
            (25, (300, 700), 25, 0xCCCC),
            (20, (350, 650), 75, 0xDDDD),
        ],
    )
    assert fork_sessions is not None, reason
    fork_bundle = pack_fork_bundle(
        sessions=fork_sessions,
        memory=fork_sessions[-1].memory,
        model=fork_sessions[-1].model,
        parent_bundle=parent_bundle,
        fork_kp=fork_kp,
        fork_record=fork_record,
        persona="forked", name="fork",
    )

    # ---- Parent continues in a third world ----
    s3 = FederatedSession(
        individual_kp=parent_kp, model=parent_model,
        world=_world(75, 0xEEEE),
        initial_point=(400, 600), memory=parent_memory,
        rule=SIERPINSKI)
    for _ in range(20):
        s3.step()
    # Re-pack parent with the new world
    parent_after = pack_federated_bundle(
        individual_kp=parent_kp, model=parent_model,
        sessions=parent_sessions + [s3],
        memory=parent_memory,
        persona="original", initial_seed=42, name="original")
    parent_after.save(root / "parent")
    fork_bundle.save(root / "fork")

    # Reload
    from individual_bundle import IndividualBundle as IB
    parent_loaded = IB.load(root / "parent")
    fork_loaded = IB.load(root / "fork")

    # ---- Verification ----
    v_parent_full = verify_federated_full(parent_loaded)
    v_fork_basic = verify_forked_basic(fork_loaded)
    v_fork_full = verify_forked_full(fork_loaded)
    v_cont = verify_fork_continuity(fork_loaded, parent_loaded)

    # ---- Tamper tests ----
    # T1: fork_at_entry points to mid-memory but prefix changed
    tampered_k = IB.load(root / "fork")
    tampered_k.manifest = dict(tampered_k.manifest)
    tampered_k.manifest["fork_at_entry"] = K - 5
    body = {k: v for k, v in tampered_k.manifest.items()
             if k != "sig"}
    tampered_k.manifest["sig"] = fork_kp.sign(
        _canonical(body)).hex()
    t1_basic, t1_reason = verify_forked_basic(tampered_k)

    # T2: fork_weights_hash points to wrong value
    tampered_w = IB.load(root / "fork")
    tampered_w.manifest = dict(tampered_w.manifest)
    tampered_w.manifest["initial_weights_hash"] = "00" * 32
    body = {k: v for k, v in tampered_w.manifest.items()
             if k != "sig"}
    tampered_w.manifest["sig"] = fork_kp.sign(
        _canonical(body)).hex()
    t2_basic, t2_reason = verify_forked_basic(tampered_w)

    # T3: fork claims wrong parent
    tampered_p = IB.load(root / "fork")
    tampered_p.manifest = dict(tampered_p.manifest)
    tampered_p.manifest["forked_from"] = "did:key:" + "00" * 32
    body = {k: v for k, v in tampered_p.manifest.items()
             if k != "sig"}
    tampered_p.manifest["sig"] = fork_kp.sign(
        _canonical(body)).hex()
    t3_cont, t3_reason = verify_fork_continuity(
        tampered_p, parent_loaded)

    # T4: parent has been altered since fork
    tampered_parent = IB.load(root / "parent")
    tampered_parent.memory = list(tampered_parent.memory)
    for i, r in enumerate(tampered_parent.memory[:K]):
        if r.get("type") == "agent_step":
            tampered_parent.memory[i] = {
                **r, "action": 99}
            break
    # Re-sign the tampered memory? Attacker can't (no parent kp).
    # But verify continuity with the ORIGINAL fork against
    # tampered parent — fork prefix won't match
    t4_cont, t4_reason = verify_fork_continuity(
        fork_loaded, tampered_parent)

    print("=" * 74)
    print("Forking — one individual becomes two")
    print("=" * 74)
    print()
    print(f"  Parent:   {parent_id[:24]}...")
    print(f"  Fork:     {fork_id[:24]}...")
    print(f"  Parent memory:  {parent_loaded.manifest['memory_entries']} "
          f"entries")
    print(f"  Fork memory:    {fork_loaded.manifest['memory_entries']} "
          f"entries")
    print(f"  Forked at:      {fork_loaded.manifest['fork_at_entry']}")
    print()
    print("  Verification:")
    print(f"    parent federated_full:   {v_parent_full[0]}  "
          f"({v_parent_full[1]})")
    print(f"    fork basic:              {v_fork_basic[0]}  "
          f"({v_fork_basic[1]})")
    print(f"    fork full:               {v_fork_full[0]}  "
          f"({v_fork_full[1]})")
    print(f"    fork continuity:         {v_cont[0]}  "
          f"({v_cont[1]})")
    print()
    print("  Tampering:")
    print(f"    fork_at_entry shifted:   {t1_basic[0]}  "
          f"({t1_basic[1]})")
    print(f"    weights_hash forged:     {t2_basic[0]}  "
          f"({t2_basic[1]})")
    print(f"    wrong parent claimed:    {t3_cont[0]}  "
          f"({t3_cont[1]})")
    print(f"    parent altered post-hoc: {t4_cont[0]}  "
          f"({t4_reason})")
    print()
    print("  What this establishes:")
    print("    - A fork is a new individual. New DID, own")
    print("      lineage_root, own bundle. The parent is")
    print("      unchanged and continues independently.")
    print("    - The fork inherits the parent's memory prefix")
    print("      (verbatim, parent's signatures intact) and")
    print("      the parent's weights at fork point (as")
    print("      initial_weights for the fork's own replay).")
    print("    - The fork record is signed by the parent. It")
    print("      attests to the fork: 'I forked at K, with")
    print("      these weights, and my fork's DID is X.'")
    print("    - Verification splits at K. Pre-K entries verify")
    print("      against parent; post-K against fork. Both must")
    print("      pass. The pattern is the same as delegation's")
    print("      split-at-boundary.")
    print("    - Continuity is proven, not trusted. A verifier")
    print("      with both bundles derives the parent's weights")
    print("      at K, compares to the fork's initial_weights,")
    print("      and confirms the prefix is a shared history —")
    print("      not a fabricated one.")
    print("    - Tampering: shifting fork_at_entry breaks the")
    print("      prefix hash; forging weights_hash breaks the")
    print("      fork record body hash; claiming a different")
    print("      parent breaks continuity; altering parent's")
    print("      past memory breaks prefix match.")
    print()
    print("  The four operations of an individual's lifecycle:")
    print("    resume           — continue me (same key)")
    print("    delegated_resume — continue me (delegated key)")
    print("    fork             — branch me (new individual)")
    print("    spawn            — beget a child (new individual,")
    print("                       no memory prefix, fresh lineage)")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'I'm Nobody! Who are you?'")
    print("    'Are you – Nobody – too?'")

    audit = {
        "parent_id": parent_id,
        "fork_id": fork_id,
        "fork_at_entry": K,
        "parent_memory_entries":
            parent_loaded.manifest["memory_entries"],
        "fork_memory_entries":
            fork_loaded.manifest["memory_entries"],
        "verification": {
            "parent_federated_full": v_parent_full[0],
            "fork_basic": v_fork_basic[0],
            "fork_full": v_fork_full[0],
            "fork_continuity": v_cont[0],
        },
        "tampering": {
            "shifted_fork_at_entry_detected":
                not t1_basic[0],
            "forged_weights_hash_detected":
                not t2_basic[0],
            "wrong_parent_detected":
                not t3_cont[0],
            "altered_parent_detected":
                not t4_cont[0],
        },
    }
    (root / "forking_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {root}/forking_demo.json")
    return audit
