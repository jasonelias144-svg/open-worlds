"""
delegated_resumption.py — resume an individual on their behalf.

Two-key model:
  - The individual's key signs a ResumptionDelegation
    authorising a delegate.
  - The delegate's key signs the resumed bundle and all new
    memory entries.

Verification splits the bundle at the delegation's resume
boundary: pre-boundary entries against the individual,
post-boundary entries against the delegate. Both must pass.

Scope fields on the delegation:
  max_resumed_steps : int          total new agent_steps allowed
  allowed_world_ids : List[str]    (empty = any)
  valid_from        : str          delegation not valid before
  valid_until       : Optional[str] (None = no expiry)
  scopes            : List[str]    currently only ["resume"]

Verification tiers:
  verify_delegation(rec, expected_individual)
  verify_delegated_basic     sig chain + per-entry signers +
                             scope + Merkle invariants
  verify_delegated_full      basic + replay from initial_weights
  verify_delegated_continuity(basic + parent.memory_entries
                             == delegation.resume_at_entry AND
                             parent.memory_root
                             == delegation.resume_at_memory_root)

Interaction with compaction:
  Delegation over a compacted parent works — resume_at_entry
  and resume_at_memory_root reference the compacted bundle's
  current state. Compacting a delegated bundle is out of scope
  (the checkpoint would need both signatures — future work).

Honest limits:
  - Single delegate. Multi-delegate requires N signed
    delegations, one per delegate, and a verifier that
    matches on resumed_by. Not built.
  - No delegation revocation. A future
    `ResumptionDelegationRevoked` record would parallel
    tree_recognition's derecognition. Not built.
  - No nested delegation. A → B → C needs new records and
    new verification. Not built.
  - scopes is currently ["resume"] only. Future values
    ("compact", "spawn") would need verifier support.
"""

import json
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from individual_bundle import (
    IndividualBundle, build_model, apply_weights,
    serialize_weights,
    _canonical, _hash, _merkle_root, _now, _did_from_kp,
    _pubkey_from_did,
)
from federated_bundle import (
    FederatedSession, verify_federated_full,
)
from resumable import (
    resume_from_bundle, pack_resumed_bundle,
    verify_resumed_from,
)
from world_agent_coupling import ScriptedWorld
from coupled_learners import SIERPINSKI


VALID_SCOPES = frozenset({"resume"})
DEFAULT_REQUIRED_SCOPES = frozenset({"resume"})


def _entry_hash(rec: Dict) -> str:
    return _hash({k: v for k, v in rec.items() if k != "sig"})


# =====================================================================
# Delegation record
# =====================================================================

@dataclass(frozen=True)
class ResumptionDelegation:
    individual_id: str
    delegate_did: str
    resume_at_entry: int
    resume_at_memory_root: str
    max_resumed_steps: int
    allowed_world_ids: Tuple[str, ...]
    valid_from: str
    valid_until: Optional[str]
    scopes: Tuple[str, ...]
    ts: str
    sig: str

    def __post_init__(self):
        if not self.individual_id or not self.delegate_did:
            raise ValueError("individual_id and delegate_did required")
        if self.individual_id == self.delegate_did:
            raise ValueError("cannot delegate to self")
        if self.resume_at_entry < 0:
            raise ValueError("resume_at_entry must be >= 0")
        if len(self.resume_at_memory_root) != 64:
            raise ValueError("resume_at_memory_root must be 64 hex")
        if self.max_resumed_steps < 1:
            raise ValueError("max_resumed_steps must be >= 1")
        if not self.scopes:
            raise ValueError("scopes must not be empty")
        for s in self.scopes:
            if s not in VALID_SCOPES:
                raise ValueError(f"unknown scope {s!r}")
        if not self.valid_from:
            raise ValueError("valid_from required")
        if self.valid_until is not None \
                and self.valid_until <= self.valid_from:
            raise ValueError("valid_until must be > valid_from")

    def body(self) -> Dict:
        return {
            "type": "resumption_delegation",
            "individual_id": self.individual_id,
            "delegate_did": self.delegate_did,
            "resume_at_entry": int(self.resume_at_entry),
            "resume_at_memory_root":
                self.resume_at_memory_root,
            "max_resumed_steps": int(self.max_resumed_steps),
            "allowed_world_ids": list(self.allowed_world_ids),
            "valid_from": self.valid_from,
            "valid_until": self.valid_until,
            "scopes": sorted(self.scopes),
            "ts": self.ts,
        }

    def to_dict(self) -> Dict:
        return {**self.body(), "sig": self.sig}

    def record_hash(self) -> str:
        return _hash(self.body())

    @classmethod
    def from_dict(cls, d: Dict) -> "ResumptionDelegation":
        return cls(
            individual_id=d["individual_id"],
            delegate_did=d["delegate_did"],
            resume_at_entry=int(d["resume_at_entry"]),
            resume_at_memory_root=d["resume_at_memory_root"],
            max_resumed_steps=int(d["max_resumed_steps"]),
            allowed_world_ids=tuple(d["allowed_world_ids"]),
            valid_from=d["valid_from"],
            valid_until=d.get("valid_until"),
            scopes=tuple(sorted(d["scopes"])),
            ts=d["ts"], sig=d["sig"],
        )


def sign_resumption_delegation(
    individual_kp,
    delegate_did: str,
    resume_at_entry: int,
    resume_at_memory_root: str,
    max_resumed_steps: int,
    allowed_world_ids: Optional[List[str]] = None,
    valid_from: Optional[str] = None,
    valid_until: Optional[str] = None,
    scopes: Optional[List[str]] = None,
) -> ResumptionDelegation:
    individual_id = _did_from_kp(individual_kp)
    ts = _now()
    vf = valid_from or ts
    scopes = scopes or ["resume"]
    awids = tuple(sorted(allowed_world_ids or []))
    body = {
        "type": "resumption_delegation",
        "individual_id": individual_id,
        "delegate_did": delegate_did,
        "resume_at_entry": int(resume_at_entry),
        "resume_at_memory_root": resume_at_memory_root,
        "max_resumed_steps": int(max_resumed_steps),
        "allowed_world_ids": list(awids),
        "valid_from": vf,
        "valid_until": valid_until,
        "scopes": sorted(scopes),
        "ts": ts,
    }
    sig = individual_kp.sign(_canonical(body)).hex()
    return ResumptionDelegation(
        individual_id=individual_id,
        delegate_did=delegate_did,
        resume_at_entry=int(resume_at_entry),
        resume_at_memory_root=resume_at_memory_root,
        max_resumed_steps=int(max_resumed_steps),
        allowed_world_ids=awids,
        valid_from=vf,
        valid_until=valid_until,
        scopes=tuple(sorted(scopes)),
        ts=ts, sig=sig,
    )


def verify_delegation(
    rec: ResumptionDelegation,
    expected_individual: Optional[str] = None,
    required_scopes: Optional[set] = None,
) -> Tuple[bool, str]:
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    if not isinstance(rec, ResumptionDelegation):
        return (False, "not a ResumptionDelegation")
    if expected_individual is not None \
            and rec.individual_id != expected_individual:
        return (False,
                 f"individual_id {rec.individual_id[:16]}... "
                 f"!= expected {expected_individual[:16]}...")
    try:
        _pubkey_from_did(rec.individual_id).verify(
            bytes.fromhex(rec.sig),
            _canonical(rec.body()))
    except Exception:
        return (False, "delegation signature invalid")
    if required_scopes is not None:
        missing = set(required_scopes) - set(rec.scopes)
        if missing:
            return (False,
                     f"scopes {sorted(missing)} not covered")
    return (True, "delegation verifies")


# =====================================================================
# Resume + pack
# =====================================================================

def resume_with_delegation(
    bundle: IndividualBundle,
    delegate_kp,
    delegation: ResumptionDelegation,
    world_specs: List[Tuple[int, Tuple[int, int], int, int]],
) -> Tuple[Optional[List[FederatedSession]], str]:
    if not HAS_CRYPTO:
        return (None, "cryptography not installed")
    delegate_did = _did_from_kp(delegate_kp)
    if delegate_did != delegation.delegate_did:
        return (None,
                 f"delegate key {delegate_did[:16]}... does not "
                 f"match delegation.delegate_did "
                 f"{delegation.delegate_did[:16]}...")
    if delegation.individual_id != bundle.individual_id:
        return (None,
                 "delegation.individual_id != "
                 "bundle.individual_id")
    ok, reason = verify_delegation(
        delegation,
        expected_individual=bundle.individual_id)
    if not ok:
        return (None, f"delegation: {reason}")
    if delegation.resume_at_entry != \
            bundle.manifest["memory_entries"]:
        return (None,
                 f"delegation.resume_at_entry "
                 f"{delegation.resume_at_entry} != "
                 f"bundle.memory_entries "
                 f"{bundle.manifest['memory_entries']}")
    if delegation.resume_at_memory_root != \
            bundle.manifest["memory_root"]:
        return (None,
                 "delegation.resume_at_memory_root != "
                 "bundle.memory_root")

    sessions, reason = resume_from_bundle(
        bundle, delegate_kp, world_specs,
        individual_id_override=bundle.individual_id,
    )
    if sessions is None:
        return (None, reason)
    return (sessions, "delegated resume")


def pack_delegated_bundle(
    sessions: List[FederatedSession],
    memory: List[Dict],
    model,
    parent_bundle: IndividualBundle,
    delegation: ResumptionDelegation,
    delegate_kp,
    persona: str,
    name: str,
) -> IndividualBundle:
    """Pack the resumed bundle with delegation fields, signed
    by the delegate."""
    if not HAS_CRYPTO:
        raise RuntimeError("cryptography not installed")
    if not sessions:
        raise ValueError("sessions must not be empty")
    delegate_did = _did_from_kp(delegate_kp)
    if delegate_did != delegation.delegate_did:
        raise ValueError("delegate key does not match "
                          "delegation.delegate_did")

    # Build base bundle via the normal mechanism, but signed by
    # the delegate with the original individual_id.
    resumed = pack_resumed_bundle(
        sessions=sessions, memory=memory, model=model,
        parent_bundle=parent_bundle,
        individual_kp=delegate_kp,  # signs with delegate key
        persona=persona, name=name,
    )
    # pack_resumed_bundle checked kp_did == parent.individual_id
    # and would have raised. Work around by re-signing directly:
    # (In practice pack_resumed_bundle should accept
    # individual_id_override. Documented as coupling.)
    return _repackage_with_delegation(
        resumed, parent_bundle, delegation, delegate_kp)


def _repackage_with_delegation(
    partial: IndividualBundle,
    parent_bundle: IndividualBundle,
    delegation: ResumptionDelegation,
    delegate_kp,
) -> IndividualBundle:
    """Reassemble the manifest with delegation fields and
    correct signer (delegate)."""
    # Merge contexts: parent's + new
    old_contexts = list(
        parent_bundle.manifest.get("world_contexts", []))
    # Determine new contexts from partial's last N entries
    # (partial already merged them in pack_resumed_bundle)
    all_contexts = list(partial.manifest.get("world_contexts", []))

    weights = partial.weights
    weights_hash = _hash(json.dumps(
        weights, sort_keys=True,
        separators=(",", ":")).encode())
    memory_hashes = [_entry_hash(r) for r in partial.memory]
    memory_root = _merkle_root(memory_hashes)
    obs_hash = _hash("[]")

    body: Dict = {
        "kind": "individual_bundle",
        "version": "1.3",
        "individual_id": parent_bundle.individual_id,
        "name": partial.manifest.get("name", "delegated"),
        "persona": partial.manifest.get("persona", ""),
        "created_at": _now(),
        "parent_did": parent_bundle.manifest.get("parent_did"),
        "model_config": parent_bundle.manifest["model_config"],
        "model_initial_seed":
            parent_bundle.manifest["model_initial_seed"],
        "model_weights_hash": weights_hash,
        "observes": parent_bundle.manifest.get("observes", False),
        "memory_entries": len(partial.memory),
        "memory_root": memory_root,
        "observations_hash": obs_hash,
        "world_contexts": all_contexts,
        "resumed_from":
            parent_bundle.manifest.get("memory_root"),
        "resumed_by": _did_from_kp(delegate_kp),
        "resumption_delegation": delegation.to_dict(),
        "lineage_root": parent_bundle.manifest.get("lineage_root"),
        "compact_ancestry":
            parent_bundle.manifest.get("compact_ancestry"),
        "parent_spawn_hash":
            parent_bundle.manifest.get("parent_spawn_hash"),
        "inherited_from":
            parent_bundle.manifest.get("inherited_from"),
        "ts": _now(),
    }
    if "initial_weights_hash" in parent_bundle.manifest:
        body["initial_weights_hash"] = \
            parent_bundle.manifest["initial_weights_hash"]
    if "compacted_at" in parent_bundle.manifest:
        body["compacted_at"] = parent_bundle.manifest["compacted_at"]
    body = {k: v for k, v in body.items() if v is not None}

    sig = delegate_kp.sign(_canonical(body)).hex()
    return IndividualBundle(
        manifest={**body, "sig": sig},
        memory=list(partial.memory),
        weights=dict(weights),
        initial_weights=(dict(parent_bundle.initial_weights)
                          if parent_bundle.initial_weights else None),
        observations=list(parent_bundle.observations),
        ancestry=list(parent_bundle.ancestry),
        checkpoint_weights=(
            dict(parent_bundle.checkpoint_weights)
            if parent_bundle.checkpoint_weights else None),
    )


# =====================================================================
# Verification
# =====================================================================

def _split_memory(bundle: IndividualBundle) -> Tuple[
    int, str, Optional[str]]:
    """Return (K, individual_id, delegate_did). K is the resume
    boundary; delegate_did is None for non-delegated bundles."""
    if not bundle.manifest.get("resumed_by"):
        return (len(bundle.memory), bundle.individual_id, None)
    delegation_dict = bundle.manifest.get("resumption_delegation")
    if not delegation_dict:
        return (-1, bundle.individual_id, None)
    K = int(delegation_dict["resume_at_entry"])
    return (K, bundle.individual_id,
             bundle.manifest["resumed_by"])


def _verify_invariants(bundle: IndividualBundle
                        ) -> Tuple[bool, str]:
    """Merkle, weights, observations — everything except sigs."""
    m = bundle.manifest
    if len(bundle.memory) != m.get("memory_entries"):
        return (False,
                 f"memory_entries mismatch: "
                 f"{len(bundle.memory)} != {m.get('memory_entries')}")
    root = _merkle_root([_entry_hash(r) for r in bundle.memory])
    if root != m.get("memory_root"):
        return (False, "memory_root mismatch")
    w_hash = _hash(json.dumps(
        bundle.weights, sort_keys=True,
        separators=(",", ":")).encode())
    if w_hash != m.get("model_weights_hash"):
        return (False, "weights_hash mismatch")
    return (True, "invariants ok")


def verify_delegated_basic(bundle: IndividualBundle
                             ) -> Tuple[bool, str]:
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    if not isinstance(bundle, IndividualBundle):
        return (False, "not an IndividualBundle")

    resumed_by = bundle.manifest.get("resumed_by")
    if resumed_by is None:
        # Non-delegated
        from individual_bundle import verify_bundle_basic
        return verify_bundle_basic(bundle)

    delegation_dict = bundle.manifest.get("resumption_delegation")
    if not delegation_dict:
        return (False, "resumed_by set but no resumption_delegation")
    try:
        delegation = ResumptionDelegation.from_dict(delegation_dict)
    except (KeyError, ValueError, TypeError) as e:
        return (False, f"malformed delegation: {e}")

    # 1. Delegation structure
    if delegation.individual_id != bundle.individual_id:
        return (False, "delegation.individual_id mismatch")
    if delegation.delegate_did != resumed_by:
        return (False, "delegation.delegate_did != resumed_by")

    # 2. Delegation signature (individual signed it)
    ok, reason = verify_delegation(
        delegation,
        expected_individual=bundle.individual_id)
    if not ok:
        return (False, f"delegation: {reason}")

    # 3. Manifest signed by delegate
    body = {k: v for k, v in bundle.manifest.items() if k != "sig"}
    try:
        _pubkey_from_did(resumed_by).verify(
            bytes.fromhex(bundle.manifest["sig"]),
            _canonical(body))
    except Exception:
        return (False, "manifest signature invalid (delegate)")

    # 4. resume boundary
    K = delegation.resume_at_entry
    if K >= len(bundle.memory):
        return (False,
                 "resume_at_entry >= memory length "
                 "(no post-resume entries)")
    if delegation.resume_at_memory_root != bundle.manifest.get(
            "resumed_from"):
        return (False,
                 "delegation.resume_at_memory_root != "
                 "resumed_from")

    # 5. Per-entry signers by position
    for i, rec in enumerate(bundle.memory):
        signer = (bundle.individual_id if i < K
                   else resumed_by)
        try:
            _pubkey_from_did(signer).verify(
                bytes.fromhex(rec["sig"]),
                _canonical({k: v for k, v in rec.items()
                             if k != "sig"}))
        except Exception:
            return (False,
                     f"memory[{i}]: signature invalid "
                     f"(expected signer {signer[:16]}...)")

    # 6. Scope: new agent steps
    new_steps = sum(
        1 for r in bundle.memory[K:]
        if r.get("type") == "agent_step")
    if new_steps > delegation.max_resumed_steps:
        return (False,
                 f"new agent_steps {new_steps} > "
                 f"max_resumed_steps {delegation.max_resumed_steps}")

    # 7. Scope: world_ids (only new contexts)
    if delegation.allowed_world_ids:
        allowed = set(delegation.allowed_world_ids)
        for ctx in bundle.manifest.get("world_contexts", []):
            if ctx.get("first_memory_index", 0) >= K:
                if ctx["world_id"] not in allowed:
                    return (False,
                             f"new world {ctx['world_id'][:16]}... "
                             f"not in allowed_world_ids")

    # 8. Scope: time
    created = bundle.manifest.get("created_at")
    if not created:
        return (False, "manifest.created_at missing")
    if delegation.valid_from > created:
        return (False,
                 f"delegation not valid until "
                 f"{delegation.valid_from} (created {created})")
    if delegation.valid_until \
            and delegation.valid_until < created:
        return (False,
                 f"delegation expired "
                 f"{delegation.valid_until} (created {created})")

    # 9. Invariants (Merkle, weights)
    ok, reason = _verify_invariants(bundle)
    if not ok:
        return (False, reason)

    return (True,
             f"delegated basic verifies (K={K}, "
             f"new_steps={new_steps})")


def verify_delegated_full(bundle: IndividualBundle
                            ) -> Tuple[bool, str]:
    """Basic + replay from initial_weights (model actual act()
    calls, ignoring sig positions — replay is position-agnostic)."""
    ok, reason = verify_delegated_basic(bundle)
    if not ok:
        return (False, reason)

    K, individual_id, delegate_did = _split_memory(bundle)

    # Build model at start (initial or checkpoint weights)
    if bundle.manifest.get("compacted_at") \
            and bundle.checkpoint_weights is not None:
        model = build_model(bundle.manifest["model_config"])
        apply_weights(model, bundle.checkpoint_weights)
        start_index = 0  # checkpoint is at position 0
    elif bundle.initial_weights is not None:
        model = build_model(bundle.manifest["model_config"])
        apply_weights(model, bundle.initial_weights)
        start_index = 0
    else:
        model = build_model(bundle.manifest["model_config"])
        start_index = 0

    import random as _rng
    rng = None
    prev_point = None
    last_action = 0
    last_reward = 0.0
    started = False
    for i, rec in enumerate(bundle.memory):
        if rec.get("type") == "checkpoint":
            continue
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
                     f"memory[{i}]: agent_step with no "
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
    final_weights = serialize_weights(model)
    if json.dumps(final_weights, sort_keys=True) != \
            json.dumps(bundle.weights, sort_keys=True):
        return (False, "replayed final weights != bundle weights")
    return (True, "delegated full verifies")


def verify_delegated_continuity(
    delegated: IndividualBundle,
    parent: IndividualBundle,
) -> Tuple[bool, str]:
    """Delegated basic + confirm the delegation references
    parent's actual state (entry count and memory_root)."""
    ok, reason = verify_delegated_basic(delegated)
    if not ok:
        return (False, f"delegated basic: {reason}")

    delegation = ResumptionDelegation.from_dict(
        delegated.manifest["resumption_delegation"])

    if delegation.resume_at_entry != \
            parent.manifest["memory_entries"]:
        return (False,
                 f"delegation.resume_at_entry "
                 f"{delegation.resume_at_entry} != "
                 f"parent.memory_entries "
                 f"{parent.manifest['memory_entries']}")
    if delegation.resume_at_memory_root != \
            parent.manifest["memory_root"]:
        return (False,
                 "delegation.resume_at_memory_root != "
                 "parent.memory_root")

    # Verify prefix of delegated memory hashes to parent's
    # memory_root
    prefix = delegated.memory[:delegation.resume_at_entry]
    prefix_root = _merkle_root([_entry_hash(r) for r in prefix])
    if prefix_root != delegation.resume_at_memory_root:
        return (False,
                 "delegated memory prefix does not hash to "
                 "delegation.resume_at_memory_root")

    return (True,
             f"delegated continuity verifies (K="
             f"{delegation.resume_at_entry})")


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir=None):
    from pathlib import Path
    from federated_bundle import pack_federated_bundle
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey)
    import json as _json

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    root = Path(artifact_dir) / "delegated_resumption"
    root.mkdir(parents=True, exist_ok=True)

    def _kp():
        return Ed25519PrivateKey.generate()

    def _world(k_b, prng):
        return ScriptedWorld(
            kp=_kp(), initial_point_b=(800, 800),
            k_b=k_b, prng_seed_b=prng, rule=SIERPINSKI)

    # ---- The individual (artist) lives for two worlds ----
    artist_kp = _kp()
    artist_id = _did_from_kp(artist_kp)
    model = TinyRNN_lazy(seed=42)
    memory: List[Dict] = []
    sessions = []
    for i, (n, pt, k, prng) in enumerate([
        (30, (200, 800), 0, 0xAAAA),
        (30, (250, 750), 50, 0xBBBB),
    ]):
        s = FederatedSession(
            individual_kp=artist_kp, model=model,
            world=_world(k, prng),
            initial_point=pt, memory=memory,
            rule=SIERPINSKI)
        for _ in range(n):
            s.step()
        sessions.append(s)
    parent = pack_federated_bundle(
        individual_kp=artist_kp, model=model,
        sessions=sessions, memory=memory,
        persona="artist's resident", initial_seed=42,
        name="artist")

    # ---- Artist signs a delegation to a curator ----
    curator_kp = _kp()
    curator_id = _did_from_kp(curator_kp)
    delegation = sign_resumption_delegation(
        individual_kp=artist_kp,
        delegate_did=curator_id,
        resume_at_entry=parent.manifest["memory_entries"],
        resume_at_memory_root=parent.manifest["memory_root"],
        max_resumed_steps=30,
        allowed_world_ids=None,  # any world
        valid_until=None,        # no expiry
    )

    # ---- Curator resumes into two new worlds ----
    new_specs = [
        (15, (300, 700), 75, 0xCCCC),
        (10, (350, 650), 25, 0xDDDD),
    ]
    new_sessions, reason = resume_with_delegation(
        parent, curator_kp, delegation, new_specs)
    if new_sessions is None:
        raise RuntimeError(f"resume failed: {reason}")

    delegated = pack_delegated_bundle(
        sessions=new_sessions,
        memory=new_sessions[-1].memory,
        model=new_sessions[-1].model,
        parent_bundle=parent,
        delegation=delegation,
        delegate_kp=curator_kp,
        persona="artist's resident, resumed by curator",
        name="delegated",
    )
    delegated.save(root / "delegated")
    parent.save(root / "parent")

    # Reload
    from individual_bundle import IndividualBundle as IB
    delegated_loaded = IB.load(root / "delegated")
    parent_loaded = IB.load(root / "parent")

    # ---- Verification tiers ----
    v_basic = verify_delegated_basic(delegated_loaded)
    v_full = verify_delegated_full(delegated_loaded)
    v_cont = verify_delegated_continuity(
        delegated_loaded, parent_loaded)

    # ---- Tamper cases ----
    # T1: another delegate's key tried to sign (not curator)
    other_kp = _kp()
    t1_sessions, t1_reason = resume_with_delegation(
        parent, other_kp, delegation, new_specs)

    # T2: curator exceeded max steps
    over_specs = [(40, (400, 600), 50, 0xEEEE)]  # 40 > 30
    # (resume succeeds; verification catches it)
    t2_sessions, t2_reason = resume_with_delegation(
        parent, curator_kp, delegation, over_specs)
    if t2_sessions is not None:
        t2_delegated = pack_delegated_bundle(
            sessions=t2_sessions,
            memory=t2_sessions[-1].memory,
            model=t2_sessions[-1].model,
            parent_bundle=parent,
            delegation=delegation,
            delegate_kp=curator_kp,
            persona="over", name="over")
        t2_verify = verify_delegated_basic(t2_delegated)
    else:
        t2_verify = (False, t2_reason)

    # T3: delegation references wrong memory_root
    bad_delegation = sign_resumption_delegation(
        individual_kp=artist_kp,
        delegate_did=curator_id,
        resume_at_entry=parent.manifest["memory_entries"],
        resume_at_memory_root="00" * 32,  # wrong
        max_resumed_steps=30,
    )
    t3_sessions, t3_reason = resume_with_delegation(
        parent, curator_kp, bad_delegation, new_specs)

    # T4: expired delegation
    expired_delegation = sign_resumption_delegation(
        individual_kp=artist_kp,
        delegate_did=curator_id,
        resume_at_entry=parent.manifest["memory_entries"],
        resume_at_memory_root=parent.manifest["memory_root"],
        max_resumed_steps=30,
        valid_from="2020-01-01T00:00:00+00:00",
        valid_until="2020-12-31T23:59:59+00:00",
    )
    t4_sessions, t4_reason = resume_with_delegation(
        parent, curator_kp, expired_delegation, new_specs)
    # If resume passed, verify catches it (created_at > valid_until)
    if t4_sessions is not None:
        t4_delegated = pack_delegated_bundle(
            sessions=t4_sessions,
            memory=t4_sessions[-1].memory,
            model=t4_sessions[-1].model,
            parent_bundle=parent,
            delegation=expired_delegation,
            delegate_kp=curator_kp,
            persona="expired", name="expired")
        t4_verify = verify_delegated_basic(t4_delegated)
    else:
        t4_verify = (False, t4_reason)

    # ---- Print ----
    print("=" * 74)
    print("Delegated resumption — the individual extends past the key")
    print("=" * 74)
    print()
    print(f"  Artist:   {artist_id[:24]}...")
    print(f"  Delegate: {curator_id[:24]}...")
    print(f"  Parent:   {parent.manifest['memory_entries']} "
          f"memory entries, "
          f"{len(parent.manifest['world_contexts'])} worlds")
    print(f"  Delegated: {delegated.manifest['memory_entries']} "
          f"memory entries, "
          f"{len(delegated.manifest['world_contexts'])} worlds")
    print()
    print(f"  Delegation scope:")
    print(f"    max_resumed_steps:    {delegation.max_resumed_steps}")
    print(f"    allowed_world_ids:    "
          f"{list(delegation.allowed_world_ids) or '(any)'}")
    print(f"    valid_until:          {delegation.valid_until or '(never)'}")
    print(f"    scopes:               {list(delegation.scopes)}")
    print()
    print("  Verification:")
    print(f"    delegated basic:      {v_basic[0]}  ({v_basic[1]})")
    print(f"    delegated full:       {v_full[0]}  ({v_full[1]})")
    print(f"    delegated continuity: {v_cont[0]}  ({v_cont[1]})")
    print()
    print("  Tampering:")
    print(f"    wrong delegate key:   "
          f"{t1_sessions is None}  ({t1_reason})")
    print(f"    exceeded max steps:   {t2_verify[0]}  "
          f"({t2_verify[1]})")
    print(f"    stale delegation:     "
          f"{t3_sessions is None}  ({t3_reason})")
    print(f"    expired delegation:   {t4_verify[0]}  "
          f"({t4_verify[1]})")
    print()
    print("  What this establishes:")
    print("    - An individual can be resumed by someone other")
    print("      than their key holder, under signed, scoped")
    print("      authorization from the individual themselves.")
    print("    - Two signatures per delegated bundle: the")
    print("      individual's on the delegation, the delegate's")
    print("      on the manifest. Memory entries split at the")
    print("      resume boundary — pre-boundary verified against")
    print("      the individual, post-boundary against the")
    print("      delegate.")
    print("    - Scope is enforced. Exceeding max steps, using a")
    print("      disallowed world, or resuming after expiry all")
    print("      fail. The verifier catches each.")
    print("    - Continuity is preserved. The delegation pins")
    print("      the parent's exact state (memory_root and")
    print("      entry count). A stale delegation against a")
    print("      changed parent fails immediately.")
    print("    - The individual's identity doesn't fork. The")
    print("      delegate acts on behalf of one continuous")
    print("      individual, not as a new entity.")
    print()
    print("  Honest limit: single delegate, no revocation, no")
    print("  nesting. Each is a natural next step but not this")
    print("  cycle.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'The Soul selects her own Society –'")
    print("    'Then – shuts the Door –'")

    audit = {
        "individual_id": artist_id,
        "delegate_did": curator_id,
        "parent_entries": parent.manifest["memory_entries"],
        "delegated_entries":
            delegated.manifest["memory_entries"],
        "verification": {
            "basic": v_basic[0],
            "full": v_full[0],
            "continuity": v_cont[0],
        },
        "tampering": {
            "wrong_delegate_refused":
                t1_sessions is None,
            "over_scope_detected":
                not t2_verify[0],
            "stale_delegation_refused":
                t3_sessions is None,
            "expired_delegation_detected":
                not t4_verify[0],
        },
    }
    (root / "delegated_resumption_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {root}/delegated_resumption_demo.json")
    return audit


def TinyRNN_lazy(seed):
    from coupled_learners import TinyRNN
    return TinyRNN(n_extra_inputs=0, seed=seed)
