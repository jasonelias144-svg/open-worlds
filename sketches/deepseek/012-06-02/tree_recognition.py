"""
tree_recognition.py — cross-tree federation of individual lineages.

Two lineage trees (distinct roots, distinct individuals) can recognize
each other via signed records. The observer carries a set of trusted
roots. Any bundle whose lineage_root is trusted, or recognized by a
trusted root with sufficient scope, verifies against that trust.

Verification:
  1. Local: compact ancestry + inheritance (or full ancestry —
     both tiers supported, delegated to existing verifiers)
  2. Trust: bundle.lineage_root must be in trusted_roots, OR
     some trusted_root has a live recognition of lineage_root
     whose scopes cover the required scopes

Composition with earlier cycles:
  - Local tier: verify_compact_ancestry_with_inheritance or
    verify_lineage_root (full ancestry). Both work.
  - Trust tier: sign_recognition, RecognitionStore, and the
    "derecognition" record type.

Honest limits:
  - No transitive recognition. If B trusts A and C trusts B,
    C does NOT trust A. Transitivity must be explicit
    (C signs its own recognition of A).
  - No expiry. Recognitions live until explicitly reversed
    via derecognition.
  - Scopes are coarse. "lineage" covers all descent claims;
    "inheritance" covers all weight-inheritance claims.
    Finer scopes (e.g., specific individual sets) are future
    work.
  - RecognitionStore is in-memory. Persistence is a
    deployment concern (a well-known URL serving recognition
    records).
  - No recognition of *specific bundles* — only of roots.
    Signing individual bundles is not supported; roots cover
    all descendants.
"""

import json
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Set, Tuple

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from individual_bundle import (
    IndividualBundle, verify_bundle_basic,
    _canonical, _hash, _now, _pubkey_from_did, _did_from_kp,
)
from compact_ancestry import verify_compact_ancestry
from compact_inheritance import (
    verify_compact_ancestry_with_inheritance,
)
from lineage_root import verify_lineage_root


VALID_SCOPES = frozenset({"lineage", "inheritance"})
DEFAULT_REQUIRED_SCOPES = frozenset({"lineage"})


# =====================================================================
# Records
# =====================================================================

@dataclass(frozen=True)
class TreeRecognition:
    record_type: str          # "recognition" | "derecognition"
    recognizer_did: str
    recognized_did: str
    scopes: Tuple[str, ...]   # empty for derecognition
    ts: str
    sig: str

    def __post_init__(self):
        if self.record_type not in ("recognition", "derecognition"):
            raise ValueError(
                f"bad record_type {self.record_type!r}")
        if not self.recognizer_did or not self.recognized_did:
            raise ValueError("recognizer/recognized required")
        if self.record_type == "recognition":
            if not self.scopes:
                raise ValueError(
                    "recognition needs at least one scope")
            for s in self.scopes:
                if s not in VALID_SCOPES:
                    raise ValueError(f"bad scope {s!r}")
        else:
            if self.scopes:
                raise ValueError(
                    "derecognition must have empty scopes")
        if self.recognizer_did == self.recognized_did:
            raise ValueError(
                "cannot recognize self")

    def body(self) -> Dict:
        return {
            "type": "tree_" + self.record_type,
            "recognizer_did": self.recognizer_did,
            "recognized_did": self.recognized_did,
            "scopes": list(self.scopes),
            "ts": self.ts,
        }

    def to_dict(self) -> Dict:
        return {**self.body(), "sig": self.sig}

    def record_hash(self) -> str:
        return _hash(self.body())


def sign_recognition(
    recognizer_kp,
    recognized_did: str,
    scopes: List[str],
) -> TreeRecognition:
    recognizer_did = _did_from_kp(recognizer_kp)
    ts = _now()
    body = {
        "type": "tree_recognition",
        "recognizer_did": recognizer_did,
        "recognized_did": recognized_did,
        "scopes": sorted(scopes),
        "ts": ts,
    }
    sig = recognizer_kp.sign(_canonical(body)).hex()
    return TreeRecognition(
        record_type="recognition",
        recognizer_did=recognizer_did,
        recognized_did=recognized_did,
        scopes=tuple(sorted(scopes)),
        ts=ts, sig=sig,
    )


def sign_derecognition(
    recognizer_kp,
    recognized_did: str,
) -> TreeRecognition:
    recognizer_did = _did_from_kp(recognizer_kp)
    ts = _now()
    body = {
        "type": "tree_derecognition",
        "recognizer_did": recognizer_did,
        "recognized_did": recognized_did,
        "scopes": [],
        "ts": ts,
    }
    sig = recognizer_kp.sign(_canonical(body)).hex()
    return TreeRecognition(
        record_type="derecognition",
        recognizer_did=recognizer_did,
        recognized_did=recognized_did,
        scopes=(),
        ts=ts, sig=sig,
    )


def verify_recognition(
    rec: TreeRecognition,
    expected_recognizer: Optional[str] = None,
) -> Tuple[bool, str]:
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    if not isinstance(rec, TreeRecognition):
        return (False, "not a TreeRecognition")
    if expected_recognizer is not None \
            and rec.recognizer_did != expected_recognizer:
        return (False,
                 f"recognizer {rec.recognizer_did[:16]}... "
                 f"!= {expected_recognizer[:16]}...")
    try:
        _pubkey_from_did(rec.recognizer_did).verify(
            bytes.fromhex(rec.sig),
            _canonical(rec.body()))
    except Exception:
        return (False, "signature invalid")
    return (True, "recognition verifies")


# =====================================================================
# Store
# =====================================================================

class RecognitionStore:
    """In-memory store of recognition/derecognition records.
    Tracks the latest record per (recognizer, recognized) pair.
    Never raises for lookups."""

    def __init__(self):
        self._by_pair: Dict[Tuple[str, str], List[TreeRecognition]] = {}

    def add(self, rec: TreeRecognition) -> None:
        if not isinstance(rec, TreeRecognition):
            raise TypeError("expected TreeRecognition")
        key = (rec.recognizer_did, rec.recognized_did)
        self._by_pair.setdefault(key, []).append(rec)

    def current(
        self, recognizer_did: str, recognized_did: str,
    ) -> Optional[TreeRecognition]:
        records = self._by_pair.get(
            (recognizer_did, recognized_did))
        if not records:
            return None
        return records[-1]  # insertion order: latest wins

    def is_recognized(
        self,
        recognizer_did: str,
        recognized_did: str,
        required_scopes: Set[str],
    ) -> Tuple[bool, str]:
        rec = self.current(recognizer_did, recognized_did)
        if rec is None:
            return (False,
                     f"{recognizer_did[:16]}... does not "
                     f"recognize {recognized_did[:16]}...")
        if rec.record_type == "derecognition":
            return (False,
                     f"{recognizer_did[:16]}... revoked "
                     f"recognition of {recognized_did[:16]}...")
        missing = required_scopes - set(rec.scopes)
        if missing:
            return (False,
                     f"scopes {sorted(missing)} not covered "
                     f"(recognized for {sorted(rec.scopes)})")
        return (True, "recognized")


# =====================================================================
# Cross-tree verification
# =====================================================================

Fetcher = Callable[[str], Optional[IndividualBundle]]


def _bundle_root(bundle: IndividualBundle) -> str:
    """The root the bundle claims descent from. Defaults to
    individual_id for roots that don't declare lineage_root."""
    return (bundle.manifest.get("lineage_root")
            or bundle.individual_id)


def _verify_local(
    bundle: IndividualBundle,
    bundle_fetcher: Fetcher,
    local_mode: str,
) -> Tuple[bool, str]:
    if local_mode == "compact_inheritance":
        return verify_compact_ancestry_with_inheritance(
            bundle, bundle_fetcher)
    if local_mode == "compact":
        return verify_compact_ancestry(bundle, bundle_fetcher)
    if local_mode == "full":
        return verify_lineage_root(bundle)
    return (False, f"unknown local_mode {local_mode!r}")


def verify_cross_tree_bundle(
    bundle: IndividualBundle,
    trusted_roots: Set[str],
    bundle_fetcher: Fetcher,
    recognition_store: RecognitionStore,
    required_scopes: Set[str] = None,
    local_mode: str = "compact_inheritance",
) -> Tuple[bool, str]:
    """Verify an individual from any tree, given a set of trusted
    roots and a recognition store.

    Returns (ok, reason). Never raises for verification failures.
    """
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    if required_scopes is None:
        required_scopes = DEFAULT_REQUIRED_SCOPES
    for s in required_scopes:
        if s not in VALID_SCOPES:
            return (False, f"invalid required scope {s!r}")
    if not isinstance(bundle, IndividualBundle):
        return (False, "not an IndividualBundle")

    # 1. Local verification (walk to root)
    ok, reason = _verify_local(bundle, bundle_fetcher, local_mode)
    if not ok:
        return (False, f"local: {reason}")

    # 2. Trust path
    root = _bundle_root(bundle)
    if root in trusted_roots:
        return (True,
                 f"trusted: root {root[:16]}... is directly "
                 f"trusted (local: {reason})")

    # Try each trusted root's recognition of `root`
    failures: List[str] = []
    for trusted in trusted_roots:
        if trusted == root:
            continue
        ok, rec_reason = recognition_store.is_recognized(
            trusted, root, required_scopes)
        if ok:
            return (True,
                     f"trusted: {trusted[:16]}... recognizes "
                     f"{root[:16]}... with scopes "
                     f"{sorted(required_scopes)} "
                     f"(local: {reason})")
        failures.append(f"{trusted[:16]}...: {rec_reason}")

    if not failures:
        return (False,
                 f"no trusted roots and root {root[:16]}... "
                 f"is not directly trusted")

    return (False,
             f"no trust path to root {root[:16]}...: "
             + "; ".join(failures))


def verify_cross_tree_chain(
    chain: List[IndividualBundle],
    trusted_roots: Set[str],
    recognition_store: RecognitionStore,
    required_scopes: Set[str] = None,
    local_mode: str = "compact_inheritance",
) -> Tuple[bool, str]:
    """Verify every bundle in a chain against the same trust set.
    Uses a local fetcher built from the chain itself."""
    by_id = {b.individual_id: b for b in chain}
    def fetcher(did: str) -> Optional[IndividualBundle]:
        return by_id.get(did)
    for i, b in enumerate(chain):
        ok, reason = verify_cross_tree_bundle(
            b, trusted_roots, fetcher, recognition_store,
            required_scopes=required_scopes,
            local_mode=local_mode)
        if not ok:
            return (False,
                     f"bundle {i} "
                     f"({b.manifest.get('name', '?')}): {reason}")
    return (True, f"cross-tree chain of {len(chain)} verifies")


# =====================================================================
# Rendering
# =====================================================================

def render_trust_graph(
    trusted_roots: Set[str],
    recognition_store: RecognitionStore,
    targets: List[str],
) -> str:
    lines = ["Trust graph:"]
    for t in sorted(trusted_roots):
        lines.append(f"  trusted root: {t[:24]}...")
        for target in targets:
            if target == t:
                continue
            rec = recognition_store.current(t, target)
            if rec is None:
                status = "(no record)"
            elif rec.record_type == "derecognition":
                status = "REVOKED"
            else:
                status = f"scopes={sorted(rec.scopes)}"
            lines.append(
                f"    → {target[:24]}...: {status}")
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
        verify_federated_full,
    )
    from federated_spawn import (
        spawn_federated_child, pack_federated_child,
    )
    from compact_ancestry import (
        compute_compact_ancestry, slim_bundle,
    )
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey)
    import json as _json

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    root = Path(artifact_dir) / "tree_recognition"
    root.mkdir(parents=True, exist_ok=True)

    def _kp():
        return Ed25519PrivateKey.generate()

    def _world(k_b, prng):
        return ScriptedWorld(
            kp=_kp(), initial_point_b=(800, 800),
            k_b=k_b, prng_seed_b=prng, rule=SIERPINSKI)

    def _build_tree(depth, steps, base_seed):
        kps = []
        models = []
        memories = []
        sessions_list = []
        spawns = []
        inherited = []

        kp0 = _kp()
        m0 = TinyRNN(n_extra_inputs=0, seed=base_seed)
        mem0: list = []
        s0 = FederatedSession(
            individual_kp=kp0, model=m0,
            world=_world(0, 0xAAAA + base_seed),
            initial_point=(200, 800), memory=mem0,
            rule=SIERPINSKI)
        for _ in range(steps):
            s0.step()
        kps.append(kp0); models.append(m0)
        memories.append(mem0); sessions_list.append([s0])

        for i in range(1, depth + 1):
            parent_sessions = sessions_list[i - 1]
            child_kp, child_model, spawn_rec, inherited_w = \
                spawn_federated_child(
                    parent_session=parent_sessions[-1],
                    child_persona=f"g{i}",
                    child_initial_seed=base_seed + i * 100)
            parent_sessions[-1].step()
            kps.append(child_kp); models.append(child_model)
            spawns.append(spawn_rec)
            inherited.append(inherited_w)
            mem_i: list = []
            s_i = FederatedSession(
                individual_kp=child_kp, model=child_model,
                world=_world(i * 10 + base_seed,
                             0xAAAA + i * 0x1111 + base_seed),
                initial_point=(200 + i * 10, 800),
                memory=mem_i, rule=SIERPINSKI)
            for _ in range(steps):
                s_i.step()
            memories.append(mem_i)
            sessions_list.append([s_i])

        full = [pack_federated_bundle(
            individual_kp=kps[0], model=models[0],
            sessions=sessions_list[0], memory=memories[0],
            persona=f"origin-{base_seed}",
            initial_seed=base_seed, name=f"g0")]
        for i in range(1, depth + 1):
            full.append(pack_federated_child(
                child_kp=kps[i], child_model=models[i],
                child_sessions=sessions_list[i],
                child_memory=memories[i],
                child_persona=f"g{i}",
                child_initial_seed=base_seed + i * 100,
                parent_bundle=full[i - 1],
                spawn_record=spawns[i - 1],
                inherited_weights=inherited[i - 1],
                name=f"g{i}"))

        slim = [full[0]]
        for i in range(1, depth + 1):
            compact = compute_compact_ancestry(
                full[i].individual_id, slim[i - 1],
                spawns[i - 1])
            slim.append(slim_bundle(full[i], compact, kps[i]))

        full_by_id = {b.individual_id: b for b in full}
        def fetcher(did):
            return full_by_id.get(did)
        return {
            "kps": kps, "full": full, "slim": slim,
            "fetcher": fetcher, "root_kp": kps[0],
            "root_did": full[0].individual_id,
        }

    # ---- Build two trees ----
    tree_a = _build_tree(depth=3, steps=8, base_seed=100)
    tree_b = _build_tree(depth=3, steps=8, base_seed=200)
    tree_c = _build_tree(depth=2, steps=6, base_seed=300)

    # ---- Recognitions ----
    store = RecognitionStore()
    rec_b_of_a = sign_recognition(
        tree_b["root_kp"], tree_a["root_did"],
        scopes=["lineage", "inheritance"])
    store.add(rec_b_of_a)

    # Observer scenarios
    observer_trusts_b = {tree_b["root_did"]}
    observer_trusts_b_and_c = {
        tree_b["root_did"], tree_c["root_did"]}
    observer_trusts_a_directly = {tree_a["root_did"]}

    # ---- Positive verifications ----
    a_deepest = tree_a["slim"][-1]
    verify_via_b = verify_cross_tree_bundle(
        a_deepest, observer_trusts_b,
        tree_a["fetcher"], store,
        required_scopes={"lineage"})
    verify_via_b_inh = verify_cross_tree_bundle(
        a_deepest, observer_trusts_b,
        tree_a["fetcher"], store,
        required_scopes={"lineage", "inheritance"})
    verify_via_a_direct = verify_cross_tree_bundle(
        a_deepest, observer_trusts_a_directly,
        tree_a["fetcher"], store)
    verify_chain = verify_cross_tree_chain(
        tree_a["slim"], observer_trusts_b, store)

    # ---- Tampering scenarios ----
    # 1. Tampered B's recognition sig
    tampered_b_rec_sig = TreeRecognition(
        record_type="recognition",
        recognizer_did=rec_b_of_a.recognizer_did,
        recognized_did=rec_b_of_a.recognized_did,
        scopes=rec_b_of_a.scopes,
        ts=rec_b_of_a.ts,
        sig="00" * 64,
    )
    store_t1 = RecognitionStore()
    store_t1.add(tampered_b_rec_sig)
    t1_ok, t1_reason = verify_cross_tree_bundle(
        a_deepest, observer_trusts_b,
        tree_a["fetcher"], store_t1)

    # 2. Recognition without "inheritance" scope
    rec_narrow = sign_recognition(
        tree_b["root_kp"], tree_a["root_did"],
        scopes=["lineage"])
    store_t2 = RecognitionStore()
    store_t2.add(rec_narrow)
    t2_ok, t2_reason = verify_cross_tree_bundle(
        a_deepest, observer_trusts_b,
        tree_a["fetcher"], store_t2,
        required_scopes={"lineage", "inheritance"})

    # 3. Derecognition
    derec = sign_derecognition(
        tree_b["root_kp"], tree_a["root_did"])
    store_t3 = RecognitionStore()
    store_t3.add(rec_b_of_a)
    store_t3.add(derec)
    t3_ok, t3_reason = verify_cross_tree_bundle(
        a_deepest, observer_trusts_b,
        tree_a["fetcher"], store_t3)

    # 4. Bundle from tree C — B doesn't recognize C
    t4_ok, t4_reason = verify_cross_tree_bundle(
        tree_c["slim"][-1], observer_trusts_b,
        tree_c["fetcher"], store)

    # 5. Bundle from tree C — trusted roots include C directly
    t5_ok, t5_reason = verify_cross_tree_bundle(
        tree_c["slim"][-1], observer_trusts_b_and_c,
        tree_c["fetcher"], store)

    # ---- Print ----
    print("=" * 74)
    print("Cross-tree federation — two lineages, one trust graph")
    print("=" * 74)
    print()
    print(f"  Tree A root: {tree_a['root_did'][:24]}...")
    print(f"  Tree B root: {tree_b['root_did'][:24]}...")
    print(f"  Tree C root: {tree_c['root_did'][:24]}...")
    print()
    print(f"  B recognizes A: "
          f"scopes={sorted(rec_b_of_a.scopes)}")
    print()
    print("  Positive verifications:")
    print(f"    A[deep] via trust=B (lineage):       "
          f"{verify_via_b[0]}")
    if verify_via_b[0]:
        print(f"      {verify_via_b[1]}")
    print(f"    A[deep] via trust=B (lineage+inh):   "
          f"{verify_via_b_inh[0]}")
    print(f"    A[deep] via trust=A (direct):        "
          f"{verify_via_a_direct[0]}")
    print(f"    A chain (all bundles) via trust=B:   "
          f"{verify_chain[0]}")
    print()
    print("  Tampering:")
    print(f"    B's recognition sig tampered:        "
          f"{t1_ok}  ({t1_reason})")
    print(f"    B recognizes only lineage, observer")
    print(f"      requires inheritance:              "
          f"{t2_ok}  ({t2_reason})")
    print(f"    B derecognized A:                    "
          f"{t3_ok}  ({t3_reason})")
    print(f"    C bundle via trust={B} (no recog):   "
          f"{t4_ok}  ({t4_reason})")
    print(f"    C bundle via trust={B,C}:            "
          f"{t5_ok}")
    print()
    print("  What this establishes:")
    print("    - A lineage can be trusted across trees without")
    print("      the observer knowing the origin's DID directly.")
    print("    - B's signed recognition of A's root is the")
    print("      trust anchor. Anyone who trusts B inherits")
    print("      B's trust in A — scoped by what B signed.")
    print("    - Recognition is scoped. B can recognize A's")
    print("      descent without recognizing its inheritance;")
    print("      an observer requiring inheritance needs a")
    print("      recognition with that scope, or direct trust.")
    print("    - Derecognition works. B can revoke its")
    print("      recognition, and the observer's next")
    print("      verification fails.")
    print("    - Multiple trust roots compose. C is trusted")
    print("      directly; A is trusted via B. Both work;")
    print("      the verifier tries all trust paths.")
    print("    - No transitive trust. C being trusted via B")
    print("      does not mean C is trusted via A, or vice")
    print("      versa. Each path is explicit.")
    print()
    print("  Honest limit: this is one-directional, "
          "non-transitive trust.")
    print("  If a federation of trees is needed, each pair "
          "must sign its")
    print("  own recognition. Transitivity, scope delegation, "
          "and expiry")
    print("  are all future work.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'The Brain – is wider than the Sky –'")
    print("    'For – put them side by side –'")
    print("    'The one the other will contain'")
    print("    'With ease – and You – beside –'")

    audit = {
        "tree_a_root": tree_a["root_did"],
        "tree_b_root": tree_b["root_did"],
        "tree_c_root": tree_c["root_did"],
        "b_recognizes_a": {
            "scopes": list(rec_b_of_a.scopes),
            "sig": rec_b_of_a.sig[:16] + "...",
        },
        "positive": {
            "via_b_lineage": verify_via_b[0],
            "via_b_lineage_inheritance": verify_via_b_inh[0],
            "via_a_direct": verify_via_a_direct[0],
            "chain_via_b": verify_chain[0],
        },
        "tampering": {
            "bad_recognition_sig": {
                "detected": not t1_ok,
                "reason": t1_reason,
            },
            "narrow_scope": {
                "detected": not t2_ok,
                "reason": t2_reason,
            },
            "derecognized": {
                "detected": not t3_ok,
                "reason": t3_reason,
            },
            "unrelated_c": {
                "detected": not t4_ok,
                "reason": t4_reason,
            },
            "c_via_multiple_roots": {
                "ok": t5_ok,
            },
        },
    }
    (root / "tree_recognition_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {root}/tree_recognition_demo.json")
    return audit
