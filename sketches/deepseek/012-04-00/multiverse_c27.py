"""
multiverse_c27.py — Component 27: Chain Forking (DAG).

C25 made chains. C26 made them retractable. C27 makes them forkable.

A DAGLink references a SET of previous links (by hash). Multiple
links can reference the same previous link — a fork. A link can
reference multiple previous links — a merge.

    root: Alice      (report_hash)
    Bob  ← Alice
    Carol← Alice     (fork: Bob and Carol both witness Alice)
    Dave ← Bob, Carol (merge: Dave witnesses both branches)

Verification walks topologically. Each link's references must be
in the DAG (except the root, which has none); each link's signature
must verify; exactly one link must carry report_hash (the root);
the root's report_hash must match the report.

Composes with C26 (revocation) without changing it: revocations
target link hashes, and link hashes are present in both chain and
DAG. Revocation is per-link, not per-branch. No cascade.

House rules honored:
  - "A world never raises on what a visitor sends" — verify_dag
    returns a DAGVerdict on any input, never raises. Tested.
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one test per failure mode: no root, two roots,
    bad report_hash, unknown previous, forged signature,
    wrong key, duplicate hash, JSON roundtrip, revocation,
    non-cascade.
  - "History, not rank" — the DAG is a record of who attested
    to what. Effective signers are derived by removing directly
    revoked links; no ranking, no scoring.

Honest limits (documented):
  - Cycles are impossible by construction (a link's hash depends
    on its previous hashes). The verifier's cycle check is
    redundant safety, not a load-bearing feature. Test it with
    hand-crafted invalid inputs, not by building a real cycle.
  - No deduplication of semantically redundant links. If Bob
    creates two links both referencing Alice's hash with
    different timestamps, both are in the DAG and both verify.
    Semantically one witness said the same thing twice;
    structurally there are two links.
  - No consensus ordering. Ties in topological order are
    broken by hash (deterministic for reproducibility). A real
    federation might use timestamps or consensus — out of scope.
  - No transient (dangling) references. Every previous hash
    must point to a link in the same DAG. Adding a link that
    references an external chain is not supported.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple

from multiverse_c1 import Identity
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c24 import SignedProvenanceReport, verify_signed_report
from multiverse_c26 import Revocation, RevocationSet


# =====================================================================
# Hashing
# =====================================================================

def _hash_payload(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_link_payload(
    signer_id: str,
    signer_name: str,
    previous_link_hashes: Tuple[str, ...],
    report_hash: Optional[str],
    timestamp: str,
) -> bytes:
    """Build the canonical bytes for a link's signature.

    previous_link_hashes sorted (order-independent), duplicates
    forbidden at construction.
    """
    return canonical_bytes({
        "kind": "attestation_dag_link",
        "signer_id": signer_id,
        "signer_name": signer_name,
        "previous_link_hashes": list(sorted(previous_link_hashes)),
        "report_hash": report_hash,
        "timestamp": timestamp,
    })


# =====================================================================
# DAGLink
# =====================================================================

@dataclass(frozen=True)
class DAGLink:
    """One link in the DAG.

    Root: report_hash set, previous_link_hashes empty.
    Non-root: report_hash None, previous_link_hashes non-empty.
    """
    signer_id: str
    signer_name: str
    previous_link_hashes: Tuple[str, ...]
    report_hash: Optional[str]
    timestamp: str
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
        if len(self.previous_link_hashes) != len(set(self.previous_link_hashes)):
            raise ValueError(
                "previous_link_hashes must not contain duplicates")
        for ph in self.previous_link_hashes:
            if not isinstance(ph, str) or len(ph) != 64:
                raise ValueError(
                    f"previous_link_hash must be 64 hex chars: {ph!r}")

    def canonical_payload(self) -> bytes:
        return _canonical_link_payload(
            self.signer_id, self.signer_name,
            self.previous_link_hashes, self.report_hash,
            self.timestamp,
        )

    def link_hash(self) -> str:
        return _hash_payload(self.canonical_payload())

    def to_dict(self) -> Dict:
        return {
            "signer_id": self.signer_id,
            "signer_name": self.signer_name,
            "previous_link_hashes": list(self.previous_link_hashes),
            "report_hash": self.report_hash,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "DAGLink":
        return cls(
            signer_id=d["signer_id"],
            signer_name=d["signer_name"],
            previous_link_hashes=tuple(d.get("previous_link_hashes", [])),
            report_hash=d.get("report_hash"),
            timestamp=d["timestamp"],
            signature=d["signature"],
        )


# =====================================================================
# AttestedDAG
# =====================================================================

@dataclass
class AttestedDAG:
    report: SignedProvenanceReport
    links: List[DAGLink]

    def to_dict(self) -> Dict:
        return {
            "kind": "attested_dag",
            "report": self.report.to_dict(),
            "links": [link.to_dict() for link in self.links],
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "AttestedDAG":
        return cls(
            report=SignedProvenanceReport.from_dict(d["report"]),
            links=[DAGLink.from_dict(l) for l in d["links"]],
        )

    def verify(
        self,
        key_resolver: Callable[[str], Optional[str]],
        report_verifier: Optional[Callable[[SignedProvenanceReport], bool]] = None,
    ) -> "DAGVerdict":
        return verify_dag(self, key_resolver, report_verifier)

    def verify_with_revocations(
        self,
        revocations: RevocationSet,
        key_resolver: Callable[[str], Optional[str]],
        report_verifier: Optional[Callable[[SignedProvenanceReport], bool]] = None,
    ) -> "DAGCombinedVerdict":
        return verify_dag_with_revocations(
            self, revocations, key_resolver, report_verifier)

    def format(self) -> str:
        lines = [
            "=" * 70,
            "Attested DAG",
            "=" * 70,
            f"  Report signer: {self.report.signer_name}",
            f"  Report type:   {self.report.report_type}",
            f"  Links:         {len(self.links)}",
            "",
        ]
        for link in self.links:
            if link.report_hash is not None:
                refs = f"report_hash={link.report_hash[:16]}..."
            else:
                refs = " ← " + ", ".join(
                    h[:8] for h in link.previous_link_hashes)
            lines.append(f"  {link.signer_name}: {refs}")
        return "\n".join(lines)


# =====================================================================
# DAGVerdict
# =====================================================================

@dataclass(frozen=True)
class DAGVerdict:
    valid: bool
    reason: str
    verified_signers: List[str]   # topological order
    leaf_signers: List[str]       # signers whose link has no dependents

    def to_dict(self) -> Dict:
        return {
            "valid": self.valid,
            "reason": self.reason,
            "verified_signers": list(self.verified_signers),
            "leaf_signers": list(self.leaf_signers),
        }

    def format(self) -> str:
        lines = ["DAG Verification", "=" * 50]
        if self.valid:
            lines.append("  Result:  ✓ VALID")
            lines.append(
                f"  Signers (topo): {' → '.join(self.verified_signers)}")
            lines.append(
                f"  Leaves:         "
                f"{', '.join(self.leaf_signers) or '(none)'}")
        else:
            lines.append("  Result:  ✗ INVALID")
            lines.append(f"  Reason:  {self.reason}")
            if self.verified_signers:
                lines.append(
                    f"  Verified up to: "
                    f"{' → '.join(self.verified_signers)}")
        return "\n".join(lines)


# =====================================================================
# Builder
# =====================================================================

class DAGBuilder:
    """Build a DAG link by link.

    First call: creates the root (must have no previous hashes).
    Subsequent calls: must pass at least one previous hash, all of
    which must already be in the builder.
    """

    def __init__(self, report: SignedProvenanceReport):
        if not HAS_CRYPTO:
            raise RuntimeError(
                "DAGBuilder requires `cryptography`. "
                "Install with: pip install cryptography")
        self._report = report
        self._links: List[DAGLink] = []
        self._known_hashes: set = set()

    def attest(
        self,
        keypair: KeyPair,
        signer: Identity,
        previous_link_hashes: Tuple[str, ...] = (),
        timestamp: Optional[str] = None,
    ) -> DAGLink:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()

        if not self._links:
            if previous_link_hashes:
                raise ValueError(
                    "first link must be root (no previous hashes)")
            report_hash = _hash_payload(self._report.canonical_payload())
            prev = ()
        else:
            if not previous_link_hashes:
                raise ValueError(
                    "non-root link requires at least one previous hash")
            # Dedupe and sort; validate existence
            prev_set = set(previous_link_hashes)
            for ph in prev_set:
                if ph not in self._known_hashes:
                    raise ValueError(
                        f"unknown previous hash: {ph[:16]}...")
            report_hash = None
            prev = tuple(sorted(prev_set))

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
        return AttestedDAG(report=self._report,
                            links=list(self._links))

    def __len__(self) -> int:
        return len(self._links)


# =====================================================================
# Verification
# =====================================================================

def verify_dag(
    dag: AttestedDAG,
    key_resolver: Callable[[str], Optional[str]],
    report_verifier: Optional[Callable[[SignedProvenanceReport], bool]] = None,
) -> DAGVerdict:
    """Verify a DAG. Never raises."""
    if not HAS_CRYPTO:
        return DAGVerdict(False, "cryptography not installed", [], [])
    if not isinstance(dag, AttestedDAG):
        return DAGVerdict(False, "not an AttestedDAG", [], [])
    if not dag.links:
        return DAGVerdict(False, "empty DAG", [], [])

    # -- Build hash map, reject duplicates --
    by_hash: Dict[str, DAGLink] = {}
    for link in dag.links:
        h = link.link_hash()
        if h in by_hash:
            return DAGVerdict(
                False, f"duplicate link hash {h[:16]}...", [], [])
        by_hash[h] = link

    # -- Exactly one root --
    roots = [h for h, l in by_hash.items()
             if l.report_hash is not None]
    if len(roots) == 0:
        return DAGVerdict(False, "no root (no link has report_hash)",
                          [], [])
    if len(roots) > 1:
        return DAGVerdict(
            False, f"{len(roots)} roots found, expected 1", [], [])
    root_hash = roots[0]

    # -- Root report_hash matches report --
    try:
        expected_report_hash = _hash_payload(
            dag.report.canonical_payload())
    except Exception as e:
        return DAGVerdict(
            False, f"could not hash report: {e}", [], [])
    if by_hash[root_hash].report_hash != expected_report_hash:
        return DAGVerdict(
            False, "root report_hash does not match report", [], [])

    # -- Every previous hash references an existing link --
    for link in dag.links:
        for ph in link.previous_link_hashes:
            if ph not in by_hash:
                return DAGVerdict(
                    False,
                    f"link {link.signer_name!r} references unknown "
                    f"hash {ph[:16]}...",
                    [], [])

    # -- Topological sort (Kahn's); detects cycles --
    in_degree: Dict[str, int] = {
        h: len(link.previous_link_hashes)
        for h, link in by_hash.items()
    }
    dependents: Dict[str, List[str]] = {h: [] for h in by_hash}
    for h, link in by_hash.items():
        for ph in link.previous_link_hashes:
            dependents[ph].append(h)

    queue = sorted(h for h, d in in_degree.items() if d == 0)
    topo_order: List[str] = []
    while queue:
        h = queue.pop(0)
        topo_order.append(h)
        for dep in dependents[h]:
            in_degree[dep] -= 1
            if in_degree[dep] == 0:
                queue.append(dep)
        queue.sort()
    if len(topo_order) != len(by_hash):
        return DAGVerdict(False, "cycle detected in DAG", [], [])

    # -- Verify signatures in topological order --
    verified_signers: List[str] = []
    for h in topo_order:
        link = by_hash[h]
        try:
            pk = key_resolver(link.signer_id)
        except Exception as e:
            return DAGVerdict(
                False, f"key_resolver raised: {e}",
                verified_signers, [])
        if pk is None:
            return DAGVerdict(
                False,
                f"no public key for {link.signer_id!r}",
                verified_signers, [])
        try:
            ok = verify_signature(
                pk, link.canonical_payload(), link.signature)
        except Exception as e:
            return DAGVerdict(
                False, f"signature verification raised: {e}",
                verified_signers, [])
        if not ok:
            return DAGVerdict(
                False,
                f"signature INVALID for {link.signer_name!r}",
                verified_signers, [])
        verified_signers.append(link.signer_name)

    # -- Optional report verification --
    if report_verifier is not None:
        try:
            if not report_verifier(dag.report):
                return DAGVerdict(
                    False, "report signature failed",
                    verified_signers, [])
        except Exception as e:
            return DAGVerdict(
                False, f"report_verifier raised: {e}",
                verified_signers, [])

    # -- Leaf signers: whose link no other link references --
    referenced = set()
    for link in dag.links:
        referenced.update(link.previous_link_hashes)
    leaf_signers = [
        by_hash[h].signer_name for h in by_hash if h not in referenced
    ]

    return DAGVerdict(
        True, "all links verified", verified_signers, leaf_signers)


# =====================================================================
# Composition with C26 revocations
# =====================================================================

@dataclass(frozen=True)
class DAGCombinedVerdict:
    dag_verdict: DAGVerdict
    accepted_revocations: List[Revocation]
    rejected_revocations: List[Tuple[Revocation, str]]
    revoked_link_hashes: Dict[str, List[Revocation]]
    effective_signers: List[str]
    revoked_signers: List[str]

    @property
    def valid(self) -> bool:
        return (self.dag_verdict.valid
                and not self.rejected_revocations)

    def format(self) -> str:
        lines = [
            "=" * 70,
            "DAG + Revocations",
            "=" * 70,
            self.dag_verdict.format(),
            "",
            f"  Accepted revocations: "
            f"{len(self.accepted_revocations)}",
            f"  Rejected revocations: "
            f"{len(self.rejected_revocations)}",
        ]
        if self.revoked_signers:
            lines.append(
                f"  Revoked signers:      "
                f"{', '.join(self.revoked_signers)}")
        lines.append(
            f"  Effective signers:    "
            f"{' → '.join(self.effective_signers) or '(none)'}")
        lines.append(f"  Overall valid:        {self.valid}")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "dag_verdict": self.dag_verdict.to_dict(),
            "accepted_count": len(self.accepted_revocations),
            "rejected_count": len(self.rejected_revocations),
            "rejected": [
                {"revoker": r.revoker_name, "reason": reason}
                for (r, reason) in self.rejected_revocations
            ],
            "revoked_signers": list(self.revoked_signers),
            "effective_signers": list(self.effective_signers),
            "valid": self.valid,
        }


def verify_dag_with_revocations(
    dag: AttestedDAG,
    revocations: RevocationSet,
    key_resolver: Callable[[str], Optional[str]],
    report_verifier: Optional[Callable[[SignedProvenanceReport], bool]] = None,
) -> DAGCombinedVerdict:
    """Verify the DAG, then overlay revocations.

    Never raises. Chain failures and revocation failures both
    surface as verdicts.
    """
    dag_verdict = verify_dag(dag, key_resolver, report_verifier)

    accepted: List[Revocation] = []
    rejected: List[Tuple[Revocation, str]] = []
    revoked_by_hash: Dict[str, List[Revocation]] = {}

    if dag_verdict.valid and isinstance(dag, AttestedDAG):
        # Build hash set for target lookups
        existing_hashes: Dict[str, DAGLink] = {}
        for link in dag.links:
            try:
                existing_hashes[link.link_hash()] = link
            except Exception:
                continue

        for rev in revocations.revocations:
            if rev.link_hash not in existing_hashes:
                rejected.append((rev, "target link not found in DAG"))
                continue
            try:
                pk = key_resolver(rev.revoker_id)
            except Exception as e:
                rejected.append((rev, f"key_resolver raised: {e}"))
                continue
            if pk is None:
                rejected.append((rev, "no public key for revoker"))
                continue
            try:
                ok = verify_signature(
                    pk, rev.canonical_payload(), rev.signature)
            except Exception as e:
                rejected.append((rev,
                                 f"signature verification raised: {e}"))
                continue
            if not ok:
                rejected.append((rev, "signature INVALID"))
                continue
            accepted.append(rev)
            revoked_by_hash.setdefault(rev.link_hash, []).append(rev)

    # Effective signers: verified_signers minus anyone whose link is revoked
    revoked_signer_names: List[str] = []
    if dag_verdict.valid:
        # Map signer name → link hash; assumes unique signer names
        # per DAG (an identity signs at most one link in practice).
        # If a signer has multiple links, only the revoked ones are
        # dropped; the same name may appear twice.
        name_to_hashes: Dict[str, List[str]] = {}
        for link in dag.links:
            name_to_hashes.setdefault(link.signer_name, []).append(
                link.link_hash())
        for name in dag_verdict.verified_signers:
            hashes = name_to_hashes.get(name, [])
            if any(h in revoked_by_hash for h in hashes):
                revoked_signer_names.append(name)

    revoked_set = set(revoked_signer_names)
    effective = [n for n in dag_verdict.verified_signers
                 if n not in revoked_set]

    return DAGCombinedVerdict(
        dag_verdict=dag_verdict,
        accepted_revocations=accepted,
        rejected_revocations=rejected,
        revoked_link_hashes=revoked_by_hash,
        effective_signers=effective,
        revoked_signers=revoked_signer_names,
    )


# =====================================================================
# Demo: fork + merge + revocation
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> DAGCombinedVerdict:
    """Alice anchors; Bob and Carol both witness Alice (fork);
    Dave merges both. Then Bob retracts. Effective signers:
    Alice → Carol → Dave.

    Anchor: Emily Dickinson, 'Tell all the truth but tell it
    slant –', public domain.
    """
    import json
    from pathlib import Path
    from multiverse_c1 import create_identity
    from multiverse_c15 import PassportEntry
    from multiverse_c21 import ProvenanceReport, EntryProvenance
    from multiverse_c24 import sign_report, verify_signed_report
    from multiverse_c26 import revoke

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    # Keys and identities
    alice_kp = KeyPair.generate()
    alice = create_identity("Alice")
    bob_kp = KeyPair.generate()
    bob = create_identity("Bob")
    carol_kp = KeyPair.generate()
    carol = create_identity("Carol")
    dave_kp = KeyPair.generate()
    dave = create_identity("Dave")
    keys = {
        alice.token: alice_kp.public_key_hex(),
        bob.token: bob_kp.public_key_hex(),
        carol.token: carol_kp.public_key_hex(),
        dave.token: dave_kp.public_key_hex(),
    }

    # Alice signs a report
    rep = ProvenanceReport(
        passport_token="demo:passport",
        passport_name="Demo Visitor",
        registry_url="http://demo/registry",
    )
    entry = PassportEntry(
        entity_id="world:a",
        timestamp="2024-01-01T00:00:00+00:00",
        subject_token="demo:passport",
        signature="bb" * 64,
    )
    ep = EntryProvenance(entry=entry)
    ep.verdict = "verified"
    ep.reason = "all stages verified (demo)"
    rep.entries.append(ep)
    signed_report = sign_report(rep, alice_kp, alice)

    # Build the fork+merge DAG
    builder = DAGBuilder(signed_report)
    root = builder.attest(alice_kp, alice)
    root_hash = root.link_hash()
    bob_link = builder.attest(
        bob_kp, bob, previous_link_hashes=(root_hash,))
    carol_link = builder.attest(
        carol_kp, carol, previous_link_hashes=(root_hash,))
    dave_link = builder.attest(
        dave_kp, dave,
        previous_link_hashes=(bob_link.link_hash(),
                              carol_link.link_hash()))
    dag = builder.build()

    # Bob retracts
    rev = revoke(bob_link, bob_kp, bob,
                 reason="Retracting witness — did not fully inspect.")
    rev_set = RevocationSet()
    rev_set.add(rev)

    # Verify
    combined = verify_dag_with_revocations(
        dag, rev_set,
        key_resolver=lambda sid: keys.get(sid),
        report_verifier=lambda r: verify_signed_report(
            r, alice_kp.public_key_hex()),
    )

    print(dag.format())
    print()
    print(combined.format())
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'Tell all the truth but tell it slant –'")
    print("    'Success in Circuit lies'")

    if artifact_dir:
        path = Path(artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "attested_dag.json").write_text(
            json.dumps({
                "dag": dag.to_dict(),
                "revocations": rev_set.to_dict(),
            }, indent=2))
        (path / "attested_dag_verdict.json").write_text(
            json.dumps(combined.to_dict(), indent=2))
        print(f"\n  → {path}/attested_dag.json")
        print(f"  → {path}/attested_dag_verdict.json")

    return combined
