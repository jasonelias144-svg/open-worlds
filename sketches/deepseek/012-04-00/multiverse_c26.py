"""
multiverse_c26.py — Component 26: Signed Revocations.

C25's chain has no retraction. C26 adds it: a signed statement
that a specific link is retracted.

Design:
  - A Revocation names a link by hash, is signed by the revoker,
    and carries a timestamp + reason.
  - Revocations live in a RevocationSet, applied to a chain at
    verification time. The chain itself is unchanged.
  - verify_chain_with_revocations() composes C25's verify_chain
    with a revocation overlay, producing a CombinedVerdict that
    names the effective signers (non-revoked) and the revoked
    signers.

Semantics:
  - A revocation is valid iff (a) its signature verifies against
    the revoker's key, and (b) its link_hash matches a link in
    the chain.
  - A link is revoked iff there exists at least one valid
    revocation targeting it.
  - Revocation does NOT cascade: revoking link i does not revoke
    link i+1, even if link i+1 witnessed link i. Each revocation
    targets exactly one link, and each link stands or falls on
    its own.
  - Self-revocation is allowed (the common case).
  - Cross-signer revocation is allowed (the caller's key_resolver
    determines who is trusted).

Composes with C24 (report) and C25 (chain) without changing them.

House rules honored:
  - "A world never raises on what a visitor sends" — the analog
    for a verifier: verify_revocations and
    verify_chain_with_revocations never raise. Tested.
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one test per case: valid self-revocation, valid
    cross-revocation, forged revocation, target-not-found,
    no-cascade, JSON roundtrip, never-raises.
  - "History, not rank" — a revocation annotates the record,
    it does not erase it. The chain still shows what was
    attested; the revocation shows what was retracted.

Honest limits (documented, tested):
  - Revoking a revocation is NOT supported. A revocation names
    a LINK hash, not another revocation's hash. If someone
    passes a revocation hash to `revoke()`, the resulting
    Revocation's link_hash won't match any link and will be
    rejected as "target not found" at verification.
  - No timestamp verification. A revoker can backdate. Same
    limit as C24 and C25.
  - No cascade. This is a design choice, not a limit — but
    it's a choice worth naming. A future component could add
    "transitive revocation" as an opt-in policy.
  - Duplicate revocations are permitted. Two valid revocations
    targeting the same link both appear in `revoked_links[i]`.
    Redundant, not invalid. The verifier doesn't deduplicate.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple

from multiverse_c1 import Identity
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c24 import SignedProvenanceReport
from multiverse_c25 import (
    AttestedChain, ChainLink, ChainVerdict,
    verify_chain,
)


# =====================================================================
# Revocation
# =====================================================================

@dataclass(frozen=True)
class Revocation:
    """A signed statement retracting a specific link."""
    link_hash: str
    revoker_id: str
    revoker_name: str
    timestamp: str
    reason: str
    signature: str

    def __post_init__(self):
        if not isinstance(self.link_hash, str) or not self.link_hash:
            raise ValueError("link_hash must be a non-empty string")
        if len(self.link_hash) != 64:
            raise ValueError("link_hash must be 64 hex chars (sha256)")
        if not isinstance(self.revoker_id, str) or not self.revoker_id:
            raise ValueError("revoker_id required")
        if not isinstance(self.revoker_name, str) or not self.revoker_name:
            raise ValueError("revoker_name required")
        if not isinstance(self.timestamp, str) or not self.timestamp:
            raise ValueError("timestamp required")
        if not isinstance(self.signature, str) or not self.signature:
            raise ValueError("signature required")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "revocation",
            "link_hash": self.link_hash,
            "revoker_id": self.revoker_id,
            "revoker_name": self.revoker_name,
            "timestamp": self.timestamp,
            "reason": self.reason,
        })

    def to_dict(self) -> Dict:
        return {
            "link_hash": self.link_hash,
            "revoker_id": self.revoker_id,
            "revoker_name": self.revoker_name,
            "timestamp": self.timestamp,
            "reason": self.reason,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "Revocation":
        return cls(
            link_hash=d["link_hash"],
            revoker_id=d["revoker_id"],
            revoker_name=d["revoker_name"],
            timestamp=d["timestamp"],
            reason=d.get("reason", ""),
            signature=d["signature"],
        )


# =====================================================================
# Builder — revoke a link
# =====================================================================

def revoke(
    link: ChainLink,
    keypair: KeyPair,
    signer: Identity,
    reason: str = "",
    timestamp: Optional[str] = None,
) -> Revocation:
    """Sign a revocation of the given link.

    Raises TypeError on a non-ChainLink argument — this is a
    builder, not a verifier, so programmer error is allowed to
    surface.
    """
    if not HAS_CRYPTO:
        raise RuntimeError(
            "revoke requires `cryptography`. "
            "Install with: pip install cryptography")
    if not isinstance(link, ChainLink):
        raise TypeError(
            f"revoke expects a ChainLink, got {type(link).__name__}")
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    link_hash = link.link_hash()
    payload = canonical_bytes({
        "kind": "revocation",
        "link_hash": link_hash,
        "revoker_id": signer.token,
        "revoker_name": signer.name,
        "timestamp": timestamp,
        "reason": reason,
    })
    return Revocation(
        link_hash=link_hash,
        revoker_id=signer.token,
        revoker_name=signer.name,
        timestamp=timestamp,
        reason=reason,
        signature=keypair.sign(payload).hex(),
    )


# =====================================================================
# RevocationSet
# =====================================================================

@dataclass
class RevocationSet:
    """An ordered list of revocations. Serializable."""
    revocations: List[Revocation] = field(default_factory=list)

    def add(self, revocation: Revocation) -> None:
        self.revocations.append(revocation)

    def __len__(self) -> int:
        return len(self.revocations)

    def to_dict(self) -> Dict:
        return {
            "kind": "revocation_set",
            "revocations": [r.to_dict() for r in self.revocations],
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "RevocationSet":
        return cls(revocations=[
            Revocation.from_dict(r) for r in d.get("revocations", [])
        ])


# =====================================================================
# RevocationVerdict
# =====================================================================

@dataclass
class RevocationVerdict:
    valid: bool
    revoked_links: Dict[int, List[Revocation]]
    accepted: List[Revocation]
    rejected: List[Tuple[Revocation, str]]
    reason: str

    def to_dict(self) -> Dict:
        return {
            "valid": self.valid,
            "revoked_link_indexes": sorted(self.revoked_links.keys()),
            "accepted_count": len(self.accepted),
            "rejected_count": len(self.rejected),
            "rejections": [
                {"reason": reason,
                 "revoker": r.revoker_name,
                 "link_hash": r.link_hash[:16] + "..."}
                for (r, reason) in self.rejected
            ],
            "reason": self.reason,
        }

    def format(self) -> str:
        lines = ["Revocation Verification", "=" * 50]
        lines.append(f"  Result:  "
                     f"{'✓ VALID' if self.valid else '✗ INVALID'}")
        lines.append(f"  Accepted: {len(self.accepted)}")
        lines.append(f"  Rejected: {len(self.rejected)}")
        if self.revoked_links:
            lines.append("  Revoked links:")
            for i in sorted(self.revoked_links.keys()):
                revs = self.revoked_links[i]
                lines.append(
                    f"    link {i}: {len(revs)} revocation(s)")
                for r in revs:
                    note = f" — {r.reason}" if r.reason else ""
                    lines.append(
                        f"      by {r.revoker_name} at {r.timestamp}{note}")
        if self.rejected:
            lines.append("  Rejections:")
            for r, reason in self.rejected:
                lines.append(
                    f"    {r.revoker_name} → {r.link_hash[:16]}...: "
                    f"{reason}")
        return "\n".join(lines)


# =====================================================================
# Verify revocations — the overlay
# =====================================================================

def verify_revocations(
    chain: AttestedChain,
    revocation_set: RevocationSet,
    key_resolver: Callable[[str], Optional[str]],
) -> RevocationVerdict:
    """Verify each revocation, determine which links are revoked.

    For each revocation:
      - Resolve the revoker's key (via key_resolver).
      - Verify the revocation's signature.
      - Find the link in the chain whose hash matches.
      - If the target link is not present, reject as "target not found".

    Never raises.
    """
    if not HAS_CRYPTO:
        return RevocationVerdict(
            valid=False, revoked_links={}, accepted=[], rejected=[],
            reason="cryptography not installed")
    if not isinstance(chain, AttestedChain) or not isinstance(
            revocation_set, RevocationSet):
        return RevocationVerdict(
            valid=False, revoked_links={}, accepted=[], rejected=[],
            reason="invalid arguments")

    # Build a hash → link_index map
    link_index_by_hash: Dict[str, int] = {}
    for i, link in enumerate(chain.links):
        try:
            link_index_by_hash[link.link_hash()] = i
        except Exception:
            continue

    accepted: List[Revocation] = []
    rejected: List[Tuple[Revocation, str]] = []
    revoked_links: Dict[int, List[Revocation]] = {}

    for rev in revocation_set.revocations:
        # Resolve the revoker's key (catch resolver raises)
        try:
            pk = key_resolver(rev.revoker_id)
        except Exception as e:
            rejected.append((rev, f"key_resolver raised: {e}"))
            continue
        if pk is None:
            rejected.append((rev, "no public key for revoker"))
            continue
        # Verify the signature
        try:
            ok = verify_signature(pk, rev.canonical_payload(),
                                   rev.signature)
        except Exception as e:
            rejected.append((rev, f"signature verification raised: {e}"))
            continue
        if not ok:
            rejected.append((rev, "signature INVALID"))
            continue
        # Find the target link
        idx = link_index_by_hash.get(rev.link_hash)
        if idx is None:
            rejected.append((rev, "target link not found in chain"))
            continue
        # Accept
        accepted.append(rev)
        revoked_links.setdefault(idx, []).append(rev)

    valid = len(rejected) == 0
    reason = ("all revocations valid"
              if valid
              else f"{len(rejected)} revocation(s) rejected")
    return RevocationVerdict(
        valid=valid,
        revoked_links=revoked_links,
        accepted=accepted,
        rejected=rejected,
        reason=reason,
    )


# =====================================================================
# CombinedVerdict — chain + revocations
# =====================================================================

@dataclass
class CombinedVerdict:
    chain_verdict: ChainVerdict
    revocation_verdict: RevocationVerdict

    @property
    def valid(self) -> bool:
        return (self.chain_verdict.valid
                and self.revocation_verdict.valid)

    @property
    def effective_signers(self) -> List[str]:
        """Signers of non-revoked links, in chain order."""
        if not self.chain_verdict.valid:
            return []
        revoked_idxs = set(self.revocation_verdict.revoked_links.keys())
        return [name for i, name
                in enumerate(self.chain_verdict.verified_signers)
                if i not in revoked_idxs]

    @property
    def revoked_signers(self) -> List[str]:
        """Signers of revoked links, in chain order."""
        if not self.chain_verdict.valid:
            return []
        revoked_idxs = set(self.revocation_verdict.revoked_links.keys())
        return [self.chain_verdict.verified_signers[i]
                for i in sorted(revoked_idxs)
                if i < len(self.chain_verdict.verified_signers)]

    def format(self) -> str:
        lines = [
            "=" * 70,
            "Combined Verdict: Chain + Revocations",
            "=" * 70,
            self.chain_verdict.format(),
            "",
            self.revocation_verdict.format(),
            "",
            f"  Effective signers: "
            f"{' → '.join(self.effective_signers) or '(none)'}",
            f"  Revoked signers:   "
            f"{', '.join(self.revoked_signers) or '(none)'}",
            f"  Overall valid:     {self.valid}",
        ]
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "chain_verdict": self.chain_verdict.to_dict(),
            "revocation_verdict": self.revocation_verdict.to_dict(),
            "effective_signers": self.effective_signers,
            "revoked_signers": self.revoked_signers,
            "valid": self.valid,
        }


# =====================================================================
# Top-level verification
# =====================================================================

def verify_chain_with_revocations(
    chain: AttestedChain,
    revocation_set: RevocationSet,
    key_resolver: Callable[[str], Optional[str]],
    report_verifier: Optional[Callable[[SignedProvenanceReport], bool]] = None,
) -> CombinedVerdict:
    """Verify the chain (C25) and overlay revocations.

    Never raises. Chain failures and revocation failures both
    appear in the combined verdict.
    """
    chain_verdict = verify_chain(chain, key_resolver, report_verifier)
    revocation_verdict = verify_revocations(
        chain, revocation_set, key_resolver)
    return CombinedVerdict(
        chain_verdict=chain_verdict,
        revocation_verdict=revocation_verdict,
    )


# =====================================================================
# RevokedChain — one artifact bundling chain + revocations
# =====================================================================

@dataclass
class RevokedChain:
    """A chain plus the set of revocations applied to it."""
    chain: AttestedChain
    revocations: RevocationSet

    def to_dict(self) -> Dict:
        return {
            "kind": "revoked_chain",
            "chain": self.chain.to_dict(),
            "revocations": self.revocations.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "RevokedChain":
        return cls(
            chain=AttestedChain.from_dict(d["chain"]),
            revocations=RevocationSet.from_dict(d["revocations"]),
        )

    def verify(
        self,
        key_resolver: Callable[[str], Optional[str]],
        report_verifier: Optional[Callable[[SignedProvenanceReport], bool]] = None,
    ) -> CombinedVerdict:
        return verify_chain_with_revocations(
            self.chain, self.revocations, key_resolver, report_verifier)


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> RevokedChain:
    """Alice anchors, Bob witnesses, Carol witnesses Bob. Bob
    retracts his witness. The chain still verifies; Bob's link is
    marked as revoked. Effective signers: Alice → Carol.

    Anchor: Emily Dickinson, 'After great pain, a formal feeling
    comes –', public domain."""
    from pathlib import Path
    from multiverse_c1 import create_identity
    from multiverse_c15 import PassportEntry
    from multiverse_c21 import ProvenanceReport, EntryProvenance
    from multiverse_c24 import sign_report, verify_signed_report
    from multiverse_c25 import ChainBuilder

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    alice_kp = KeyPair.generate()
    bob_kp = KeyPair.generate()
    carol_kp = KeyPair.generate()
    alice = create_identity("Alice")
    bob = create_identity("Bob")
    carol = create_identity("Carol")
    keys = {
        alice.token: alice_kp.public_key_hex(),
        bob.token: bob_kp.public_key_hex(),
        carol.token: carol_kp.public_key_hex(),
    }

    # Alice audits, Bob and Carol witness
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
    builder = ChainBuilder(signed_report)
    builder.attest(alice_kp, alice)
    builder.attest(bob_kp, bob)
    builder.attest(carol_kp, carol)
    chain = builder.build()

    # Bob retracts his witness
    bob_link = chain.links[1]
    bob_revocation = revoke(
        bob_link, bob_kp, bob,
        reason="Did not fully inspect; retracting witness.",
    )
    rev_set = RevocationSet()
    rev_set.add(bob_revocation)
    revoked_chain = RevokedChain(chain=chain, revocations=rev_set)

    # Verify
    verdict = revoked_chain.verify(
        key_resolver=lambda sid: keys.get(sid),
        report_verifier=lambda r: verify_signed_report(
            r, alice_kp.public_key_hex()),
    )
    print(verdict.format())
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'After great pain, a formal feeling comes –'")
    print("    'The Nerves sit ceremonious, like Tombs –'")

    if artifact_dir:
        path = Path(artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "revoked_chain.json").write_text(
            json.dumps(revoked_chain.to_dict(), indent=2))
        (path / "revoked_chain_verdict.json").write_text(
            json.dumps(verdict.to_dict(), indent=2))
        print(f"\n  → {path}/revoked_chain.json")
        print(f"  → {path}/revoked_chain_verdict.json")

    return revoked_chain
