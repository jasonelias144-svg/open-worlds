"""
multiverse_c25.py — Component 25: The Attested Chain.

C24 made single audits portable. C25 makes them witnessed.

A chain is an ordered list of ChainLinks. Link 0 binds the
report's hash; each subsequent link binds the previous link's
hash. Every link is signed by its signer.

    link 0: Alice  "report_hash = H(report)"
    link 1: Bob    "previous_link_hash = H(link 0)"
    link 2: Carol  "previous_link_hash = H(link 1)"
    ...

What this attests: multiple signers looked at the chain and
endorsed the link that came before them. It does not attest
that the report is *true* — only that A said it, then B said
A said it, then C said B said A said it. That's the trust model.
A chain ending with someone you trust extends trust back to
the report. A chain ending with someone you don't trust adds
nothing — the chain doesn't decide for you.

Composes with C24 (SignedProvenanceReport) without re-verifying
the report. Optional report_verifier callback lets the caller
compose C24's verify_signed_report if they want the chain to
also check the report.

House rules honored:
  - "A world never raises on what a visitor sends" — the
    analog for a verifier: verify_chain returns a ChainVerdict
    with valid=False on any failure. Never raises. Tested.
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one test per failure mode: bad hash, bad sig,
    wrong position, wrong key, missing key, empty chain,
    swapped report, JSON roundtrip.
  - "History, not rank" — a chain is a record of who said what
    when, not a score. Nothing here ranks chains by length,
    signer prestige, or anything else.

Honest limits (documented, tested):
  - The chain attests to WHAT WAS SIGNED, not to WHAT IS TRUE.
    A chain of honest verifiers can endorse a fabricated
    report; the chain is valid, the report is a lie. Trust
    the report *and* the witnesses, or trust neither.
  - No timestamp verification. Same limit as C24.
  - No forking. A link attests to exactly one previous link.
    Merging two chains, or building a DAG, is future work.
  - No revocation. A link, once signed, is part of the chain
    forever. "I retract my witness" is future work.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional

from multiverse_c1 import Identity
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c24 import (
    SignedProvenanceReport, verify_signed_report,
)


# =====================================================================
# Hashing
# =====================================================================

def _hash_payload(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


# =====================================================================
# ChainLink
# =====================================================================

@dataclass(frozen=True)
class ChainLink:
    """One link in the chain.

    Link 0 has report_hash set, previous_link_hash=None.
    Link i>0 has report_hash=None, previous_link_hash=hash of link i-1.

    Both fields are in the canonical payload; both are checked by
    the verifier. A link that violates either invariant is rejected.
    """
    link_index: int
    signer_id: str
    signer_name: str
    previous_link_hash: Optional[str]   # None for index 0, else hex
    report_hash: Optional[str]          # set only for index 0
    timestamp: str
    signature: str

    def __post_init__(self):
        if self.link_index < 0:
            raise ValueError("link_index must be >= 0")
        if not self.signer_id:
            raise ValueError("signer_id required")
        if not self.signer_name:
            raise ValueError("signer_name required")
        if not self.timestamp:
            raise ValueError("timestamp required")
        if not self.signature:
            raise ValueError("signature required")
        # Exactly one of the two hash fields must be set
        if self.link_index == 0:
            if self.report_hash is None:
                raise ValueError("link 0 must have report_hash")
            if self.previous_link_hash is not None:
                raise ValueError("link 0 must not have previous_link_hash")
        else:
            if self.report_hash is not None:
                raise ValueError("non-zero link must not have report_hash")
            if self.previous_link_hash is None:
                raise ValueError("non-zero link must have previous_link_hash")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "attestation_link",
            "link_index": self.link_index,
            "signer_id": self.signer_id,
            "signer_name": self.signer_name,
            "previous_link_hash": self.previous_link_hash,
            "report_hash": self.report_hash,
            "timestamp": self.timestamp,
        })

    def link_hash(self) -> str:
        return _hash_payload(self.canonical_payload())

    def to_dict(self) -> Dict:
        return {
            "link_index": self.link_index,
            "signer_id": self.signer_id,
            "signer_name": self.signer_name,
            "previous_link_hash": self.previous_link_hash,
            "report_hash": self.report_hash,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "ChainLink":
        return cls(
            link_index=d["link_index"],
            signer_id=d["signer_id"],
            signer_name=d["signer_name"],
            previous_link_hash=d.get("previous_link_hash"),
            report_hash=d.get("report_hash"),
            timestamp=d["timestamp"],
            signature=d["signature"],
        )


# =====================================================================
# AttestedChain
# =====================================================================

@dataclass
class AttestedChain:
    """A report plus an ordered list of signed attestations."""
    report: SignedProvenanceReport
    links: List[ChainLink]

    def to_dict(self) -> Dict:
        return {
            "kind": "attested_chain",
            "report": self.report.to_dict(),
            "links": [link.to_dict() for link in self.links],
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "AttestedChain":
        return cls(
            report=SignedProvenanceReport.from_dict(d["report"]),
            links=[ChainLink.from_dict(l) for l in d["links"]],
        )

    def verify(
        self,
        key_resolver: Callable[[str], Optional[str]],
        report_verifier: Optional[Callable[[SignedProvenanceReport], bool]] = None,
    ) -> "ChainVerdict":
        return verify_chain(self, key_resolver, report_verifier)

    def format(self) -> str:
        lines = [
            "=" * 70,
            "Attested Chain",
            "=" * 70,
            f"  Report signer: {self.report.signer_name}",
            f"  Report type:   {self.report.report_type}",
            f"  Links:         {len(self.links)}",
            "",
        ]
        for link in self.links:
            lines.append(
                f"  [{link.link_index}] {link.signer_name}")
            if link.link_index == 0:
                lines.append(
                    f"      report_hash: {link.report_hash[:16]}...")
            else:
                lines.append(
                    f"      prev_link:   "
                    f"{link.previous_link_hash[:16]}...")
            lines.append(f"      timestamp:   {link.timestamp}")
            lines.append(
                f"      signature:   {link.signature[:16]}...")
        return "\n".join(lines)


# =====================================================================
# ChainVerdict
# =====================================================================

@dataclass(frozen=True)
class ChainVerdict:
    valid: bool
    link_index: Optional[int]           # index of the failing link, or None
    reason: str
    verified_signers: List[str]         # signer names in verification order

    def to_dict(self) -> Dict:
        return {
            "valid": self.valid,
            "link_index": self.link_index,
            "reason": self.reason,
            "verified_signers": list(self.verified_signers),
        }

    def format(self) -> str:
        lines = [
            "Chain Verification",
            "=" * 50,
        ]
        if self.valid:
            lines.append("  Result:  ✓ VALID")
            lines.append(f"  Signers: {' → '.join(self.verified_signers)}")
        else:
            lines.append("  Result:  ✗ INVALID")
            lines.append(f"  Failed at link {self.link_index}")
            lines.append(f"  Reason:  {self.reason}")
            if self.verified_signers:
                lines.append(
                    f"  Verified up to: "
                    f"{' → '.join(self.verified_signers)}")
        return "\n".join(lines)


# =====================================================================
# Builder
# =====================================================================

class ChainBuilder:
    """Build a chain link by link.

    Usage:
        builder = ChainBuilder(report)
        builder.attest(alice_kp, alice_identity)   # link 0
        builder.attest(bob_kp, bob_identity)       # link 1
        chain = builder.build()
    """

    def __init__(self, report: SignedProvenanceReport):
        if not HAS_CRYPTO:
            raise RuntimeError(
                "ChainBuilder requires `cryptography`. "
                "Install with: pip install cryptography")
        self._report = report
        self._links: List[ChainLink] = []
        self._tip_hash: Optional[str] = None

    def attest(self, keypair: KeyPair, signer: Identity) -> ChainLink:
        index = len(self._links)
        timestamp = datetime.now(timezone.utc).isoformat()
        if index == 0:
            report_hash = _hash_payload(
                self._report.canonical_payload())
            previous_hash = None
        else:
            report_hash = None
            previous_hash = self._tip_hash
        payload = canonical_bytes({
            "kind": "attestation_link",
            "link_index": index,
            "signer_id": signer.token,
            "signer_name": signer.name,
            "previous_link_hash": previous_hash,
            "report_hash": report_hash,
            "timestamp": timestamp,
        })
        link = ChainLink(
            link_index=index,
            signer_id=signer.token,
            signer_name=signer.name,
            previous_link_hash=previous_hash,
            report_hash=report_hash,
            timestamp=timestamp,
            signature=keypair.sign(payload).hex(),
        )
        self._links.append(link)
        self._tip_hash = link.link_hash()
        return link

    def build(self) -> AttestedChain:
        return AttestedChain(report=self._report,
                              links=list(self._links))

    def __len__(self) -> int:
        return len(self._links)


# =====================================================================
# Verification
# =====================================================================

def verify_chain(
    chain: AttestedChain,
    key_resolver: Callable[[str], Optional[str]],
    report_verifier: Optional[Callable[[SignedProvenanceReport], bool]] = None,
) -> ChainVerdict:
    """Verify a chain, never raising.

    Checks, in order:
      1. Chain is non-empty; cryptography is installed.
      2. Link 0's report_hash matches the report's canonical hash.
      3. Each link's position matches its index.
      4. Link 0 has no previous_link_hash; links i>0 have
         previous_link_hash matching link i-1's hash.
      5. Each link's signature verifies against its signer's key.
      6. (If provided) report_verifier returns True for the report.

    Returns a ChainVerdict. Never raises.
    """
    if not HAS_CRYPTO:
        return ChainVerdict(valid=False, link_index=None,
                            reason="cryptography not installed",
                            verified_signers=[])
    if not isinstance(chain, AttestedChain):
        return ChainVerdict(valid=False, link_index=None,
                            reason="not an AttestedChain",
                            verified_signers=[])
    if not chain.links:
        return ChainVerdict(valid=False, link_index=None,
                            reason="empty chain",
                            verified_signers=[])

    # Check 2: report hash matches link 0
    try:
        expected_report_hash = _hash_payload(
            chain.report.canonical_payload())
    except Exception as e:
        return ChainVerdict(valid=False, link_index=None,
                            reason=f"could not hash report: {e}",
                            verified_signers=[])
    if chain.links[0].report_hash != expected_report_hash:
        return ChainVerdict(valid=False, link_index=0,
                            reason="link 0 report_hash does not "
                                    "match the report's hash",
                            verified_signers=[])

    # Walk the chain
    verified_signers: List[str] = []
    prev_hash: Optional[str] = None
    for i, link in enumerate(chain.links):
        # Check 3: position
        if link.link_index != i:
            return ChainVerdict(valid=False, link_index=i,
                                reason=(f"position mismatch: link says "
                                        f"{link.link_index}, expected {i}"),
                                verified_signers=verified_signers)
        # Check 4: hash binding
        if i == 0:
            if link.previous_link_hash is not None:
                return ChainVerdict(valid=False, link_index=0,
                                    reason="link 0 must not have "
                                            "previous_link_hash",
                                    verified_signers=verified_signers)
        else:
            if link.previous_link_hash != prev_hash:
                return ChainVerdict(valid=False, link_index=i,
                                    reason="previous_link_hash does not "
                                            "match the previous link",
                                    verified_signers=verified_signers)
        # Check 5: signature
        try:
            pk = key_resolver(link.signer_id)
        except Exception as e:
            return ChainVerdict(valid=False, link_index=i,
                                reason=f"key_resolver raised: {e}",
                                verified_signers=verified_signers)
        if pk is None:
            return ChainVerdict(valid=False, link_index=i,
                                reason=f"no public key for "
                                        f"{link.signer_id!r}",
                                verified_signers=verified_signers)
        try:
            ok = verify_signature(pk, link.canonical_payload(),
                                    link.signature)
        except Exception as e:
            return ChainVerdict(valid=False, link_index=i,
                                reason=f"signature verification raised: "
                                        f"{e}",
                                verified_signers=verified_signers)
        if not ok:
            return ChainVerdict(valid=False, link_index=i,
                                reason="signature INVALID",
                                verified_signers=verified_signers)

        verified_signers.append(link.signer_name)
        prev_hash = link.link_hash()

    # Check 6: optional report verification
    if report_verifier is not None:
        try:
            if not report_verifier(chain.report):
                return ChainVerdict(valid=False, link_index=None,
                                    reason="report signature failed",
                                    verified_signers=verified_signers)
        except Exception as e:
            return ChainVerdict(valid=False, link_index=None,
                                reason=f"report_verifier raised: {e}",
                                verified_signers=verified_signers)

    return ChainVerdict(valid=True, link_index=None,
                        reason="all links verified",
                        verified_signers=verified_signers)


# =====================================================================
# Demo — three auditors, one chain
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> AttestedChain:
    """Alice signs a report, Alice anchors, Bob witnesses, Carol
    witnesses Bob. Verified by walking the chain with all three
    public keys. Anchor: Emily Dickinson, public domain."""
    import json
    from pathlib import Path
    from multiverse_c1 import create_identity
    from multiverse_c15 import PassportEntry
    from multiverse_c21 import ProvenanceReport, EntryProvenance

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    alice_kp = KeyPair.generate()
    bob_kp = KeyPair.generate()
    carol_kp = KeyPair.generate()
    alice = create_identity("Alice (auditor)")
    bob = create_identity("Bob (witness)")
    carol = create_identity("Carol (witness)")

    # Alice's report (stub: three verified entries)
    rep = ProvenanceReport(
        passport_token="demo:passport",
        passport_name="Demo Visitor",
        registry_url="http://demo/registry",
    )
    for eid in ("world:poetry", "world:chemistry", "world:a"):
        entry = PassportEntry(
            entity_id=eid,
            timestamp="2024-01-01T00:00:00+00:00",
            subject_token="demo:passport",
            signature="bb" * 64,
        )
        ep = EntryProvenance(entry=entry)
        ep.verdict = "verified"
        ep.reason = "all stages verified (demo)"
        rep.entries.append(ep)

    # C24: Alice signs the report
    from multiverse_c24 import sign_report
    signed_report = sign_report(rep, alice_kp, alice)

    # C25: build the chain
    builder = ChainBuilder(signed_report)
    builder.attest(alice_kp, alice)   # link 0 — Alice anchors
    builder.attest(bob_kp, bob)       # link 1 — Bob witnesses
    builder.attest(carol_kp, carol)   # link 2 — Carol witnesses Bob
    chain = builder.build()

    # Verify
    keys = {
        alice.token: alice_kp.public_key_hex(),
        bob.token: bob_kp.public_key_hex(),
        carol.token: carol_kp.public_key_hex(),
    }
    verdict = verify_chain(
        chain,
        key_resolver=lambda sid: keys.get(sid),
        report_verifier=lambda r: verify_signed_report(
            r, alice_kp.public_key_hex()),
    )

    print(chain.format())
    print()
    print(verdict.format())
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'I'm Nobody! Who are you?'")
    print("    'Are you – Nobody – too?'")

    if artifact_dir:
        path = Path(artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "attested_chain.json").write_text(
            json.dumps(chain.to_dict(), indent=2))
        (path / "attested_chain_verdict.json").write_text(
            json.dumps(verdict.to_dict(), indent=2))
        print(f"\n  → {path}/attested_chain.json")
        print(f"  → {path}/attested_chain_verdict.json")

    return chain
