"""
multiverse_c34.py — Component 34: Cross-DAG Composition.

C27's DAG is self-contained. C34 adds a link type that can
reference links in OTHER DAGs, enabling federations to attest to
each other.

Design (the honest kind):
  - DAGLink (C27) is UNCHANGED. C27's verify_dag works as before.
  - ExtendingDAGLink is NEW: DAGLink's fields plus
    external_references — a tuple of (dag_id, link_hash).
  - verify_dag_extended verifies a DAG that may contain either
    type, resolving external references via a DAGResolver.
  - FederatedDAGVerdict names both each DAG's local validity and
    the cross-DAG resolution outcome.

Semantics:
  - An extension link attests to *witnessing* a link in another
    DAG, not to *owning* it. Dave in DAG-B referencing Bob in
    DAG-A is "Dave has seen Bob's attestation."
  - An extension link is valid iff every external reference
    resolves to a link in a resolvable DAG, AND that DAG is
    itself valid. Referencing a broken DAG breaks the extension.
  - No cascade: revoking Bob in DAG-A does not revoke Dave in
    DAG-B (Bob's retraction is in DAG-A; Dave's witness is in
    DAG-B). Dave's link remains valid; the reference is
    annotated (see C26's revocation model).

Composes with C27 (DAG), C26 (revocation), C25 (chain).

House rules honored:
  - "A world never raises on what a visitor sends" — verify
    functions return verdicts, never raise. Tested.
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one test per: valid extension, missing external
    DAG, missing external link, invalid external DAG, cycle
    detection, wrong key, JSON roundtrip.
  - "History, not rank" — the extension is a record of what
    was witnessed. No ranking; no scoring.

Honest limits (documented, tested):
  - One extension layer at a time for the demo, but the design
    supports multi-hop (A ← B ← C) via recursive resolution.
    A depth limit prevents unbounded recursion in a hostile
    federation.
  - Cycles are IMPOSSIBLE to construct (a link's hash depends
    on its references, which depend on hashes — you'd need to
    know a hash before computing it). The cycle detector is
    defensive; it catches hand-crafted invalid input.
  - Resolver trust is external. The caller decides which DAGs
    the resolver returns. Same trust model as C16/C29.
  - No timestamp verification. Same as C24/C25/C26/C27.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple, Union

from multiverse_c1 import Identity
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c24 import SignedProvenanceReport, verify_signed_report
from multiverse_c27 import (
    DAGLink, AttestedDAG, DAGVerdict, verify_dag,
    _hash_payload, _canonical_link_payload,
)


# =====================================================================
# ExtendingDAGLink — a link with cross-DAG references
# =====================================================================

@dataclass(frozen=True)
class ExtendingDAGLink:
    """A DAGLink that additionally references links in other DAGs.

    Same fields as DAGLink, plus `external_references` — a tuple
    of (dag_id, link_hash) pairs. The external references are
    included in the canonical payload, so tampering with any of
    them changes the link's hash and breaks any dependents.
    """
    signer_id: str
    signer_name: str
    previous_link_hashes: Tuple[str, ...]
    report_hash: Optional[str]
    timestamp: str
    external_references: Tuple[Tuple[str, str], ...]
    signature: str

    def __post_init__(self):
        if not self.signer_id:
            raise ValueError("signer_id required")
        if not self.signer_name:
            raise ValueError("signer_name required")
        if not self.timestamp:
            raise ValueError("timestamp required")
        if not self.signature:
            raise ValueError("signature required")
        if self.report_hash is None:
            if not self.previous_link_hashes:
                raise ValueError(
                    "non-root link must have at least one previous link")
        else:
            if self.previous_link_hashes:
                raise ValueError(
                    "root link must not have previous links")
        if not self.external_references:
            raise ValueError(
                "ExtendingDAGLink must have at least one external "
                "reference (use DAGLink for plain links)")
        if len(self.external_references) != len(
                set(self.external_references)):
            raise ValueError(
                "external_references must not contain duplicates")
        for dag_id, link_hash in self.external_references:
            if not isinstance(dag_id, str) or not dag_id:
                raise ValueError(
                    "external dag_id must be non-empty string")
            if not isinstance(link_hash, str) or len(link_hash) != 64:
                raise ValueError(
                    "external link_hash must be 64 hex chars")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "attestation_extending_dag_link",
            "signer_id": self.signer_id,
            "signer_name": self.signer_name,
            "previous_link_hashes": sorted(self.previous_link_hashes),
            "report_hash": self.report_hash,
            "timestamp": self.timestamp,
            "external_references": [
                [dag_id, link_hash]
                for (dag_id, link_hash)
                in sorted(self.external_references)
            ],
        })

    def link_hash(self) -> str:
        return _hash_payload(self.canonical_payload())

    def to_dict(self) -> Dict:
        return {
            "kind": "extending",
            "signer_id": self.signer_id,
            "signer_name": self.signer_name,
            "previous_link_hashes": list(self.previous_link_hashes),
            "report_hash": self.report_hash,
            "timestamp": self.timestamp,
            "external_references": [
                list(ref) for ref in self.external_references],
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "ExtendingDAGLink":
        return cls(
            signer_id=d["signer_id"],
            signer_name=d["signer_name"],
            previous_link_hashes=tuple(
                d.get("previous_link_hashes", [])),
            report_hash=d.get("report_hash"),
            timestamp=d["timestamp"],
            external_references=tuple(
                (ref[0], ref[1])
                for ref in d.get("external_references", [])),
            signature=d["signature"],
        )


Link = Union[DAGLink, ExtendingDAGLink]


# =====================================================================
# FederatedDAG — a set of DAGs plus a resolver
# =====================================================================

DAGResolver = Callable[[str], Optional[AttestedDAG]]


class DictDAGResolver:
    """A resolver backed by a dict of {dag_id → AttestedDAG}."""

    def __init__(self, dags: Optional[Dict[str, AttestedDAG]] = None):
        self._dags: Dict[str, AttestedDAG] = dict(dags) if dags else {}

    def register(self, dag_id: str, dag: AttestedDAG) -> None:
        self._dags[dag_id] = dag

    def __call__(self, dag_id: str) -> Optional[AttestedDAG]:
        return self._dags.get(dag_id)


# =====================================================================
# Verdicts
# =====================================================================

@dataclass(frozen=True)
class ExtensionReferenceResult:
    dag_id: str
    link_hash: str
    resolved: bool
    external_dag_valid: bool
    external_link_found: bool
    external_link_valid: bool
    reason: str

    @property
    def ok(self) -> bool:
        return (self.resolved
                and self.external_dag_valid
                and self.external_link_found
                and self.external_link_valid)


@dataclass
class FederatedDAGVerdict:
    valid: bool
    reason: str
    dag_verdict: DAGVerdict
    extension_results: Dict[str, List[ExtensionReferenceResult]]
    # extension_results maps the *extending link's hash* to a list
    # of per-reference resolution results.

    def format(self) -> str:
        lines = ["=" * 70,
                 "Federated DAG Verification",
                 "=" * 70,
                 self.dag_verdict.format(), ""]
        if not self.extension_results:
            lines.append("  (no external references)")
        else:
            lines.append("  External references:")
            for link_hash, results in self.extension_results.items():
                lines.append(f"    link {link_hash[:16]}...")
                for r in results:
                    marker = "✓" if r.ok else "✗"
                    lines.append(
                        f"      {marker} {r.dag_id}::"
                        f"{r.link_hash[:16]}... "
                        f"({r.reason})")
        lines.append("")
        lines.append(f"  Result: "
                     f"{'✓ VALID' if self.valid else '✗ INVALID'}")
        if not self.valid:
            lines.append(f"  Reason: {self.reason}")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "valid": self.valid,
            "reason": self.reason,
            "dag_verdict": self.dag_verdict.to_dict(),
            "extension_results": {
                lh: [
                    {
                        "dag_id": r.dag_id,
                        "link_hash": r.link_hash,
                        "resolved": r.resolved,
                        "external_dag_valid": r.external_dag_valid,
                        "external_link_found": r.external_link_found,
                        "external_link_valid": r.external_link_valid,
                        "reason": r.reason,
                        "ok": r.ok,
                    }
                    for r in results
                ]
                for lh, results in self.extension_results.items()
            },
        }


# =====================================================================
# Builder — DAGBuilder that can emit extending links
# =====================================================================

class ExtendedDAGBuilder:
    """Builder that supports both plain and extending links.

    First call is the root (plain). Subsequent calls can be plain
    or extending, and extending links can reference external DAGs
    by (dag_id, link_hash).
    """

    def __init__(self, report: SignedProvenanceReport):
        if not HAS_CRYPTO:
            raise RuntimeError(
                "ExtendedDAGBuilder requires `cryptography`. "
                "Install with: pip install cryptography")
        self._report = report
        self._links: List[Link] = []
        self._known_hashes: set = set()

    def attest(
        self,
        keypair: KeyPair,
        signer: Identity,
        previous_link_hashes: Tuple[str, ...] = (),
        external_references: Tuple[Tuple[str, str], ...] = (),
        timestamp: Optional[str] = None,
    ) -> Link:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()

        if not self._links:
            if previous_link_hashes:
                raise ValueError(
                    "first link must be root (no previous hashes)")
            if external_references:
                raise ValueError(
                    "root cannot have external references")
            report_hash = _hash_payload(self._report.canonical_payload())
            prev = ()
        else:
            if not previous_link_hashes:
                raise ValueError(
                    "non-root link requires at least one previous hash")
            prev_set = set(previous_link_hashes)
            for ph in prev_set:
                if ph not in self._known_hashes:
                    raise ValueError(
                        f"unknown previous hash: {ph[:16]}...")
            report_hash = None
            prev = tuple(sorted(prev_set))

        if external_references:
            payload = canonical_bytes({
                "kind": "attestation_extending_dag_link",
                "signer_id": signer.token,
                "signer_name": signer.name,
                "previous_link_hashes": sorted(prev),
                "report_hash": report_hash,
                "timestamp": timestamp,
                "external_references": [
                    [d, h] for (d, h)
                    in sorted(external_references)
                ],
            })
            sig = keypair.sign(payload).hex()
            link = ExtendingDAGLink(
                signer_id=signer.token,
                signer_name=signer.name,
                previous_link_hashes=prev,
                report_hash=report_hash,
                timestamp=timestamp,
                external_references=tuple(
                    sorted(external_references)),
                signature=sig,
            )
        else:
            payload = _canonical_link_payload(
                signer.token, signer.name, prev, report_hash, timestamp,
            )
            sig = keypair.sign(payload).hex()
            link = DAGLink(
                signer_id=signer.token,
                signer_name=signer.name,
                previous_link_hashes=prev,
                report_hash=report_hash,
                timestamp=timestamp,
                signature=sig,
            )
        self._links.append(link)
        self._known_hashes.add(link.link_hash())
        return link

    def build(self) -> AttestedDAG:
        return AttestedDAG(report=self._report, links=self._links)

    def __len__(self) -> int:
        return len(self._links)


# =====================================================================
# Verification
# =====================================================================

def verify_dag_extended(
    dag: AttestedDAG,
    key_resolver: Callable[[str], Optional[str]],
    dag_resolver: DAGResolver,
    report_verifier: Optional[
        Callable[[SignedProvenanceReport], bool]] = None,
    max_depth: int = 8,
    _visited: Optional[set] = None,
) -> FederatedDAGVerdict:
    """Verify a DAG that may contain extending links. Never raises.

    Steps:
      1. Run C27's verify_dag on the local DAG. Fails fast if local
         structure is broken.
      2. For each ExtendingDAGLink, resolve each external reference
         via dag_resolver and verify the referenced DAG recursively.
      3. A DAG is valid iff local verification passes AND every
         external reference resolves to a valid link in a valid DAG.
    """
    if not HAS_CRYPTO:
        return FederatedDAGVerdict(
            valid=False, reason="cryptography not installed",
            dag_verdict=DAGVerdict(False, "cryptography",
                                     [], []),
            extension_results={})
    if _visited is None:
        _visited = set()
    if max_depth <= 0:
        return FederatedDAGVerdict(
            valid=False, reason="max_depth exceeded",
            dag_verdict=DAGVerdict(False, "max_depth", [], []),
            extension_results={})

    # Compute a stable identity for this DAG (root hash + report)
    try:
        dag_identity = _dag_identity(dag)
    except Exception as e:
        return FederatedDAGVerdict(
            valid=False, reason=f"could not identify DAG: {e}",
            dag_verdict=DAGVerdict(False, "bad DAG", [], []),
            extension_results={})
    if dag_identity in _visited:
        return FederatedDAGVerdict(
            valid=False, reason="cycle detected",
            dag_verdict=DAGVerdict(False, "cycle", [], []),
            extension_results={})
    _visited = _visited | {dag_identity}

    # Step 1: C27 verification (local structure). Requires every
    # link to be a DAGLink — but our DAG might contain extending
    # links, which C27's verifier doesn't know about. So we run a
    # *local* structural check that understands both link types,
    # reusing C27's DAGVerdict shape for the result.
    local_verdict = _verify_dag_local_extended(dag, key_resolver,
                                                report_verifier)
    if not local_verdict.valid:
        return FederatedDAGVerdict(
            valid=False,
            reason=f"local verification failed: {local_verdict.reason}",
            dag_verdict=local_verdict,
            extension_results={})

    # Step 2: resolve each extension's external references
    extension_results: Dict[str, List[ExtensionReferenceResult]] = {}
    all_ok = True
    for link in dag.links:
        if not isinstance(link, ExtendingDAGLink):
            continue
        results: List[ExtensionReferenceResult] = []
        for ext_dag_id, ext_link_hash in link.external_references:
            result = _resolve_external_reference(
                ext_dag_id, ext_link_hash,
                key_resolver, dag_resolver, report_verifier,
                max_depth - 1, _visited,
            )
            results.append(result)
            if not result.ok:
                all_ok = False
        extension_results[link.link_hash()] = results

    if not all_ok:
        return FederatedDAGVerdict(
            valid=False,
            reason="one or more external references failed",
            dag_verdict=local_verdict,
            extension_results=extension_results)

    return FederatedDAGVerdict(
        valid=True,
        reason="local verified, all external references verified",
        dag_verdict=local_verdict,
        extension_results=extension_results)


def _dag_identity(dag: AttestedDAG) -> str:
    """A stable identifier for a DAG: root hash + report hash."""
    for link in dag.links:
        if link.report_hash is not None:
            return f"{link.report_hash}::{link.link_hash()}"
    return f"no_root::{_hash_payload(dag.report.canonical_payload())}"


def _verify_dag_local_extended(
    dag: AttestedDAG,
    key_resolver: Callable[[str], Optional[str]],
    report_verifier: Optional[
        Callable[[SignedProvenanceReport], bool]],
) -> DAGVerdict:
    """Like C27's verify_dag, but accepts ExtendingDAGLink too.

    The only structural difference: extending links are valid,
    and their external_references are not checked here (checked
    by the caller). Everything else — exactly one root, root's
    report_hash matches, every previous_link_hash resolves,
    topological order, signatures verify — is identical to C27.
    """
    if not dag.links:
        return DAGVerdict(False, "empty DAG", [], [])

    by_hash: Dict[str, Link] = {}
    for link in dag.links:
        h = link.link_hash()
        if h in by_hash:
            return DAGVerdict(
                False, f"duplicate link hash {h[:16]}...", [], [])
        by_hash[h] = link

    roots = [h for h, l in by_hash.items()
             if l.report_hash is not None]
    if len(roots) == 0:
        return DAGVerdict(False, "no root", [], [])
    if len(roots) > 1:
        return DAGVerdict(
            False, f"{len(roots)} roots, expected 1", [], [])
    root_hash = roots[0]

    try:
        expected = _hash_payload(dag.report.canonical_payload())
    except Exception as e:
        return DAGVerdict(
            False, f"could not hash report: {e}", [], [])
    if by_hash[root_hash].report_hash != expected:
        return DAGVerdict(
            False, "root report_hash mismatch", [], [])

    for link in dag.links:
        for ph in link.previous_link_hashes:
            if ph not in by_hash:
                return DAGVerdict(
                    False,
                    f"link {link.signer_name!r} references unknown "
                    f"hash {ph[:16]}...",
                    [], [])

    in_degree = {h: len(l.previous_link_hashes)
                 for h, l in by_hash.items()}
    dependents: Dict[str, List[str]] = {h: [] for h in by_hash}
    for h, link in by_hash.items():
        for ph in link.previous_link_hashes:
            dependents[ph].append(h)

    queue = sorted(h for h, d in in_degree.items() if d == 0)
    topo: List[str] = []
    while queue:
        h = queue.pop(0)
        topo.append(h)
        for dep in dependents[h]:
            in_degree[dep] -= 1
            if in_degree[dep] == 0:
                queue.append(dep)
        queue.sort()
    if len(topo) != len(by_hash):
        return DAGVerdict(False, "cycle in local DAG", [], [])

    verified: List[str] = []
    for h in topo:
        link = by_hash[h]
        try:
            pk = key_resolver(link.signer_id)
        except Exception as e:
            return DAGVerdict(
                False, f"key_resolver raised: {e}", verified, [])
        if pk is None:
            return DAGVerdict(
                False, f"no key for {link.signer_id!r}", verified, [])
        try:
            ok = verify_signature(pk, link.canonical_payload(),
                                    link.signature)
        except Exception as e:
            return DAGVerdict(
                False, f"verify raised: {e}", verified, [])
        if not ok:
            return DAGVerdict(
                False, f"signature INVALID for "
                        f"{link.signer_name!r}", verified, [])
        verified.append(link.signer_name)

    if report_verifier is not None:
        try:
            if not report_verifier(dag.report):
                return DAGVerdict(
                    False, "report signature failed", verified, [])
        except Exception as e:
            return DAGVerdict(
                False, f"report_verifier raised: {e}", verified, [])

    referenced = set()
    for link in dag.links:
        referenced.update(link.previous_link_hashes)
    leaves = [
        by_hash[h].signer_name for h in by_hash if h not in referenced
    ]

    return DAGVerdict(True, "local verified", verified, leaves)


def _resolve_external_reference(
    ext_dag_id: str,
    ext_link_hash: str,
    key_resolver: Callable[[str], Optional[str]],
    dag_resolver: DAGResolver,
    report_verifier: Optional[
        Callable[[SignedProvenanceReport], bool]],
    max_depth: int,
    _visited: set,
) -> ExtensionReferenceResult:
    """Resolve one (dag_id, link_hash) reference. Never raises."""

    def fail(reason: str, *, resolved=False,
             dag_valid=False, link_found=False, link_valid=False):
        return ExtensionReferenceResult(
            dag_id=ext_dag_id, link_hash=ext_link_hash,
            resolved=resolved, external_dag_valid=dag_valid,
            external_link_found=link_found,
            external_link_valid=link_valid, reason=reason)

    try:
        ext_dag = dag_resolver(ext_dag_id)
    except Exception as e:
        return fail(f"dag_resolver raised: {e}")
    if ext_dag is None:
        return fail("no such DAG in resolver")

    ext_verdict = verify_dag_extended(
        ext_dag, key_resolver, dag_resolver,
        report_verifier, max_depth, _visited)
    if not ext_verdict.valid:
        return fail(
            f"external DAG failed verification: {ext_verdict.reason}",
            resolved=True)

    # Find the referenced link
    found_link: Optional[Link] = None
    for link in ext_dag.links:
        if link.link_hash() == ext_link_hash:
            found_link = link
            break
    if found_link is None:
        return fail("external DAG does not contain the link",
                    resolved=True, dag_valid=True)

    # The link was already verified as part of ext_verdict; but we
    # re-check that it's in the verified signers list as a
    # belt-and-braces measure
    if found_link.signer_name not in ext_verdict.dag_verdict.\
            verified_signers:
        return fail("external link was not in ext DAG's "
                    "verified set",
                    resolved=True, dag_valid=True, link_found=True)
    return fail("external reference verified",
                resolved=True, dag_valid=True,
                link_found=True, link_valid=True)


# =====================================================================
# Demo: two DAGs, extension across the boundary
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Two federations attest to each other.

    DAG-A: Alice anchors report A; Bob witnesses.
    DAG-B: Carol anchors report B; Dave witnesses Carol AND
           references Bob's link in DAG-A.

    Dave's link in DAG-B is only valid if DAG-A is valid and
    Bob's link is in it. Dave's witness says "I have seen Bob's
    attestation."

    Anchor: Emily Dickinson, 'Forever – is composed of Nows –',
    public domain.
    """
    import json
    from pathlib import Path
    from multiverse_c1 import create_identity
    from multiverse_c15 import PassportEntry
    from multiverse_c21 import ProvenanceReport, EntryProvenance
    from multiverse_c24 import sign_report

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    def _build_report(name, entity_id):
        kp = KeyPair.generate()
        who = create_identity(name)
        rep = ProvenanceReport(
            passport_token=f"{name.lower()}-token",
            passport_name=name,
            registry_url="http://demo/registry",
        )
        entry = PassportEntry(
            entity_id=entity_id,
            timestamp="2024-01-01T00:00:00+00:00",
            subject_token=f"{name.lower()}-token",
            signature="cc" * 64,
        )
        ep = EntryProvenance(entry=entry)
        ep.verdict = "verified"
        ep.reason = "stub"
        rep.entries.append(ep)
        return sign_report(rep, kp, who), kp, who

    # DAG-A
    report_a, alice_kp, alice = _build_report("Alice", "world:a")
    bob_kp = KeyPair.generate()
    bob = create_identity("Bob")
    a_builder = ExtendedDAGBuilder(report_a)
    a_root = a_builder.attest(alice_kp, alice)
    a_bob = a_builder.attest(
        bob_kp, bob,
        previous_link_hashes=(a_root.link_hash(),))
    dag_a = a_builder.build()

    # DAG-B
    report_b, carol_kp, carol = _build_report("Carol", "world:b")
    dave_kp = KeyPair.generate()
    dave = create_identity("Dave")
    b_builder = ExtendedDAGBuilder(report_b)
    b_root = b_builder.attest(carol_kp, carol)
    b_dave = b_builder.attest(
        dave_kp, dave,
        previous_link_hashes=(b_root.link_hash(),),
        external_references=(("dag-a", a_bob.link_hash()),),
    )
    dag_b = b_builder.build()

    # Resolver
    resolver = DictDAGResolver({
        "dag-a": dag_a,
        "dag-b": dag_b,
    })

    # Keys
    keys = {
        alice.token: alice_kp.public_key_hex(),
        bob.token: bob_kp.public_key_hex(),
        carol.token: carol_kp.public_key_hex(),
        dave.token: dave_kp.public_key_hex(),
    }
    key_resolver = lambda sid: keys.get(sid)
    report_verifier = lambda r: True  # stub reports

    # Verify both DAGs (B's extension requires A)
    verdict_a = verify_dag_extended(
        dag_a, key_resolver, resolver, report_verifier)
    verdict_b = verify_dag_extended(
        dag_b, key_resolver, resolver, report_verifier)

    print("=" * 70)
    print("Cross-DAG Composition — demo")
    print("=" * 70)
    print()
    print("  DAG-A (Alice anchors, Bob witnesses):")
    print(verdict_a.format())
    print()
    print("  DAG-B (Carol anchors, Dave witnesses Carol")
    print("        AND references Bob's link in DAG-A):")
    print(verdict_b.format())
    print()
    print("  What Dave's link in DAG-B means:")
    print("    'I have seen Bob's attestation in DAG-A,'")
    print("    'and I extend my own witness to include it.'")
    print("    Dave's link is valid only if DAG-A is valid")
    print("    and Bob's link is in it.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'Forever – is composed of Nows –'")
    print("    'Tis not a different time –'")

    audit = {
        "dag_a_valid": verdict_a.valid,
        "dag_b_valid": verdict_b.valid,
        "dag_b_extends_dag_a": True,
    }
    if artifact_dir:
        path = Path(artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "cross_dag_demo.json").write_text(
            json.dumps(audit, indent=2))
        print(f"\n  → {path}/cross_dag_demo.json")
    return audit
