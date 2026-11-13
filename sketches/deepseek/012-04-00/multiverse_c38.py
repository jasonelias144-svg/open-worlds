"""
multiverse_c38.py — Component 38: Person Manifests.

C36's honest limit #1: removing a binding from a presented
PersonIdentity is not detectable, because each binding is signed
but the *set* is not. C38 closes it with a signed PersonManifest.

A PersonManifest signs:
  - the person's token, name, public key
  - the sorted (token, binding_hash) pairs — every current binding
  - a timestamp

Tampering with any field or binding breaks the signature.
Removing a binding from the presented person while keeping the
manifest yields status="binding_mismatch" with the removed
tokens named.

Composes with C36 (PersonIdentity, TokenBinding, verify_person).

House rules honored:
  - "A world never raises on what a visitor sends" — verifier
    returns verdicts, never raises. Tested.
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: valid manifest, invalid signature,
    person token mismatch, person key mismatch, binding added,
    binding removed, binding changed.
  - "History, not rank" — a snapshot of a person's set, not a
    score.

Honest limits (documented, tested):
  - The manifest is a SNAPSHOT. A person can sign a new manifest
    that omits a binding they previously had; a reader who sees
    only the new manifest cannot detect the removal. This is
    the same TOFU-vs-transparency-log limit as C28/C24.
  - No "supersedes" event between manifests. Two manifests for
    the same person coexist; the reader decides which to trust.
    Future work.
  - No revocation events. A removed binding is removed by
    signing a new manifest without it; the old manifest stays
    in the historical record.
  - Trust anchor external. Verifying the manifest against a
    trusted key is only as good as the trust in that key. Same
    as everywhere.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c36 import (
    PersonIdentity, TokenBinding, PersonVerificationReport,
    verify_person,
)


def _hash_payload(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


# =====================================================================
# PersonManifest
# =====================================================================

@dataclass(frozen=True)
class PersonManifest:
    """A signed snapshot of a person's binding set.

    `bindings` is a tuple of (token, binding_hash) pairs, sorted
    by token (enforced at construction). The manifest's canonical
    payload sorts by token so it's deterministic regardless of
    how the caller presents the pairs.
    """
    person_token: str
    person_name: str
    person_public_key: str
    bindings: Tuple[Tuple[str, str], ...]
    timestamp: str
    signature: str

    def __post_init__(self):
        for f in ("person_token", "person_name", "person_public_key",
                  "timestamp", "signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if len(self.person_public_key) != 64:
            raise ValueError(
                "person_public_key must be 64 hex chars")
        for pair in self.bindings:
            if (not isinstance(pair, tuple) or len(pair) != 2):
                raise ValueError(
                    "each binding must be a (token, hash) tuple")
            tok, h = pair
            if not isinstance(tok, str) or not tok:
                raise ValueError(
                    "binding token must be non-empty string")
            if not isinstance(h, str) or len(h) != 64:
                raise ValueError(
                    "binding hash must be 64 hex chars")
        if self.bindings != tuple(sorted(self.bindings)):
            raise ValueError(
                "bindings must be sorted by token")
        tokens = [tok for tok, _ in self.bindings]
        if len(tokens) != len(set(tokens)):
            raise ValueError(
                "bindings must not contain duplicate tokens")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "person_manifest",
            "person_token": self.person_token,
            "person_name": self.person_name,
            "person_public_key": self.person_public_key,
            "bindings": [list(b) for b in sorted(self.bindings)],
            "timestamp": self.timestamp,
        })

    def binding_map(self) -> Dict[str, str]:
        return {tok: h for tok, h in self.bindings}

    def to_dict(self) -> Dict:
        return {
            "person_token": self.person_token,
            "person_name": self.person_name,
            "person_public_key": self.person_public_key,
            "bindings": [list(b) for b in self.bindings],
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "PersonManifest":
        return cls(
            person_token=d["person_token"],
            person_name=d["person_name"],
            person_public_key=d["person_public_key"],
            bindings=tuple(
                (b[0], b[1]) for b in d.get("bindings", [])),
            timestamp=d["timestamp"],
            signature=d["signature"],
        )


# =====================================================================
# Sign
# =====================================================================

def sign_person_manifest(
    person: PersonIdentity,
    person_kp: KeyPair,
    timestamp: Optional[str] = None,
) -> PersonManifest:
    """Produce a manifest for the person's current binding set.

    Raises ValueError if the keypair doesn't match the person's
    public key. That's a programmer error, not a visitor error.
    """
    if not HAS_CRYPTO:
        raise RuntimeError(
            "sign_person_manifest requires `cryptography`. "
            "Install with: pip install cryptography")
    if person_kp.public_key_hex() != person.person_public_key:
        raise ValueError(
            "keypair does not match person.person_public_key")
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    bindings = tuple(sorted(
        (b.token, b.binding_hash()) for b in person.bindings))
    payload = canonical_bytes({
        "kind": "person_manifest",
        "person_token": person.person.token,
        "person_name": person.person.name,
        "person_public_key": person.person_public_key,
        "bindings": [list(b) for b in bindings],
        "timestamp": timestamp,
    })
    return PersonManifest(
        person_token=person.person.token,
        person_name=person.person.name,
        person_public_key=person.person_public_key,
        bindings=bindings,
        timestamp=timestamp,
        signature=person_kp.sign(payload).hex(),
    )


# =====================================================================
# Verify manifest signature (alone)
# =====================================================================

def verify_manifest_signature(
    manifest: PersonManifest,
    trusted_person_public_key: str,
) -> bool:
    """True iff the signature verifies against the trusted key.
    Never raises."""
    if not HAS_CRYPTO:
        return False
    try:
        if not isinstance(manifest, PersonManifest):
            return False
        return verify_signature(
            trusted_person_public_key,
            manifest.canonical_payload(),
            manifest.signature,
        )
    except Exception:
        return False


# =====================================================================
# ManifestVerdict — the diagnostic
# =====================================================================

@dataclass
class ManifestVerdict:
    valid: bool
    status: str
    # status:
    #   "valid"              — sig ok, binding set matches
    #   "invalid_signature"  — sig doesn't verify against trusted key
    #   "person_mismatch"    — token or declared key differs
    #   "binding_mismatch"   — sig ok, but set differs (see below)
    reason: str
    added_tokens: List[str] = field(default_factory=list)
    removed_tokens: List[str] = field(default_factory=list)
    changed_tokens: List[Tuple[str, str, str]] = field(default_factory=list)
    # changed_tokens: (token, manifest_hash, actual_hash)

    def format(self) -> str:
        lines = [
            "Person Manifest Verification",
            "=" * 50,
            f"  status:  {self.status}",
            f"  valid:   {self.valid}",
            f"  reason:  {self.reason}",
        ]
        if self.added_tokens:
            lines.append("  added (in person, not manifest):")
            for t in self.added_tokens:
                lines.append(f"    + {t[:16]}...")
        if self.removed_tokens:
            lines.append("  removed (in manifest, not person):")
            for t in self.removed_tokens:
                lines.append(f"    - {t[:16]}...")
        if self.changed_tokens:
            lines.append("  changed (same token, different hash):")
            for tok, mh, ah in self.changed_tokens:
                lines.append(
                    f"    ~ {tok[:16]}...  "
                    f"manifest={mh[:12]}... actual={ah[:12]}...")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "valid": self.valid,
            "status": self.status,
            "reason": self.reason,
            "added_tokens": list(self.added_tokens),
            "removed_tokens": list(self.removed_tokens),
            "changed_tokens": [
                list(t) for t in self.changed_tokens],
        }


# =====================================================================
# Verify person against manifest
# =====================================================================

def verify_person_against_manifest(
    person: PersonIdentity,
    manifest: PersonManifest,
    trusted_person_public_key: str,
) -> ManifestVerdict:
    """Does the person's current binding set match the manifest?

    Checks, in order:
      1. Manifest signature verifies against the trusted key.
      2. Person's declared key == trusted key.
      3. Person token == manifest token.
      4. Binding sets match exactly (no added/removed/changed).

    Never raises.
    """
    if not HAS_CRYPTO:
        return ManifestVerdict(
            valid=False, status="invalid_signature",
            reason="cryptography not installed")
    if not isinstance(person, PersonIdentity):
        return ManifestVerdict(
            valid=False, status="person_mismatch",
            reason="not a PersonIdentity")
    if not isinstance(manifest, PersonManifest):
        return ManifestVerdict(
            valid=False, status="invalid_signature",
            reason="not a PersonManifest")

    # 1. Signature
    if not verify_manifest_signature(
            manifest, trusted_person_public_key):
        return ManifestVerdict(
            valid=False, status="invalid_signature",
            reason=("manifest signature does not verify "
                    "against the trusted key"))

    # 2. Declared key
    if person.person_public_key != trusted_person_public_key:
        return ManifestVerdict(
            valid=False, status="person_mismatch",
            reason=("person declares a different key than "
                    "trusted"))

    # 3. Token
    if person.person.token != manifest.person_token:
        return ManifestVerdict(
            valid=False, status="person_mismatch",
            reason=(f"person token {person.person.token[:16]}... "
                    f"!= manifest token "
                    f"{manifest.person_token[:16]}..."))

    # 4. Binding sets
    manifest_map = manifest.binding_map()
    person_map = {b.token: b.binding_hash() for b in person.bindings}

    added = sorted(set(person_map) - set(manifest_map))
    removed = sorted(set(manifest_map) - set(person_map))
    changed = sorted(
        (tok, manifest_map[tok], person_map[tok])
        for tok in set(person_map) & set(manifest_map)
        if person_map[tok] != manifest_map[tok]
    )

    if added or removed or changed:
        parts = []
        if removed:
            parts.append(f"{len(removed)} removed")
        if added:
            parts.append(f"{len(added)} added")
        if changed:
            parts.append(f"{len(changed)} changed")
        return ManifestVerdict(
            valid=False, status="binding_mismatch",
            reason="binding set differs: " + ", ".join(parts),
            added_tokens=added,
            removed_tokens=removed,
            changed_tokens=changed,
        )

    return ManifestVerdict(
        valid=True, status="valid",
        reason="manifest signature valid, binding set matches")


# =====================================================================
# PersonPresentation — bundle for a verifier
# =====================================================================

@dataclass(frozen=True)
class PersonPresentation:
    person: PersonIdentity
    manifest: PersonManifest

    def to_dict(self) -> Dict:
        return {
            "person": self.person.to_dict(),
            "manifest": self.manifest.to_dict(),
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "PersonPresentation":
        return cls(
            person=PersonIdentity.from_dict(d["person"]),
            manifest=PersonManifest.from_dict(d["manifest"]),
        )


# =====================================================================
# PresentationVerdict — full composition
# =====================================================================

@dataclass
class PresentationVerdict:
    bindings_ok: bool
    manifest_ok: bool
    set_matches: bool
    all_valid: bool
    reason: str
    manifest_verdict: ManifestVerdict
    bindings_report: PersonVerificationReport

    def format(self) -> str:
        lines = [
            "=" * 70,
            "Person Presentation Verification",
            "=" * 70,
            f"  person:       "
            f"{self.bindings_report.person_name} "
            f"({self.bindings_report.person_token[:16]}...)",
            f"  bindings_ok:  {self.bindings_ok}",
            f"  manifest_ok:  {self.manifest_ok}",
            f"  set_matches:  {self.set_matches}",
            f"  all_valid:    {self.all_valid}",
            f"  reason:       {self.reason}",
            "",
            self.manifest_verdict.format(),
        ]
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "bindings_ok": self.bindings_ok,
            "manifest_ok": self.manifest_ok,
            "set_matches": self.set_matches,
            "all_valid": self.all_valid,
            "reason": self.reason,
            "manifest_verdict": self.manifest_verdict.to_dict(),
            "bindings_report": self.bindings_report.to_dict(),
        }


def verify_presentation(
    presentation: PersonPresentation,
    trusted_person_public_key: str,
) -> PresentationVerdict:
    """Verify a PersonPresentation end to end.

    Checks:
      - every binding's dual signature (C36's verify_person)
      - the manifest signature (C38)
      - the binding set matches the manifest (C38)

    Never raises.
    """
    if not HAS_CRYPTO:
        return _unavailable_verdict()
    if not isinstance(presentation, PersonPresentation):
        return _unavailable_verdict()

    bindings_report = verify_person(presentation.person)
    manifest_verdict = verify_person_against_manifest(
        presentation.person, presentation.manifest,
        trusted_person_public_key)

    bindings_ok = bindings_report.all_valid
    manifest_ok = manifest_verdict.status in (
        "valid", "binding_mismatch")
    set_matches = manifest_verdict.status == "valid"
    all_valid = bindings_ok and manifest_ok and set_matches

    parts = []
    if not bindings_ok:
        parts.append("one or more bindings invalid")
    if not manifest_ok:
        parts.append(f"manifest: {manifest_verdict.reason}")
    elif not set_matches:
        parts.append(f"set: {manifest_verdict.reason}")
    reason = "; ".join(parts) if parts else "all checks passed"

    return PresentationVerdict(
        bindings_ok=bindings_ok,
        manifest_ok=manifest_ok,
        set_matches=set_matches,
        all_valid=all_valid,
        reason=reason,
        manifest_verdict=manifest_verdict,
        bindings_report=bindings_report,
    )


def _unavailable_verdict() -> PresentationVerdict:
    empty_report = PersonVerificationReport(
        person_token="", person_name="",
        person_public_key="",
        binding_verdicts=[],
    )
    return PresentationVerdict(
        bindings_ok=False, manifest_ok=False,
        set_matches=False, all_valid=False,
        reason="cryptography not installed or bad input",
        manifest_verdict=ManifestVerdict(
            valid=False, status="invalid_signature",
            reason="unavailable"),
        bindings_report=empty_report,
    )


# =====================================================================
# Demo — Aria with a manifest; detection of removed binding
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Aria, three embodiments, one signed manifest. A verifier
    confirms set completeness. An attacker presents Aria with one
    binding stripped; the manifest catches the removal.

    Anchor: Emily Dickinson, 'I heard a Fly buzz – when I died –',
    public domain.
    """
    import json
    from pathlib import Path
    from multiverse_c1 import create_identity
    from multiverse_c36 import create_person, bind_token

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    # Aria with three embodiments
    aria, aria_kp = create_person("Aria")
    for name in ("Aria@poetry", "Aria@chemistry", "Aria@registry"):
        tok = create_identity(name)
        aria, _ = bind_token(
            aria, aria_kp, tok.token, name, KeyPair.generate())

    # Aria signs a manifest of the set
    manifest = sign_person_manifest(aria, aria_kp)

    # Honest presentation
    honest = PersonPresentation(person=aria, manifest=manifest)
    honest_verdict = verify_presentation(
        honest, aria.person_public_key)

    # Attack: stripped presentation — remove one binding, keep manifest
    stripped_person = PersonIdentity(
        person=aria.person,
        person_public_key=aria.person_public_key,
        bindings=(aria.bindings[0], aria.bindings[1]),
    )
    stripped = PersonPresentation(
        person=stripped_person, manifest=manifest)
    stripped_verdict = verify_presentation(
        stripped, aria.person_public_key)

    print("=" * 70)
    print("Person Manifests — demo")
    print("=" * 70)
    print()
    print("  Aria's manifest:")
    print(f"    person:  {manifest.person_name} "
          f"({manifest.person_token[:16]}...)")
    print(f"    bindings: {len(manifest.bindings)}")
    print(f"    signed at: {manifest.timestamp}")
    print()
    print("  Honest presentation (3 bindings, matches manifest):")
    for line in honest_verdict.format().split("\n"):
        print(f"    {line}")
    print()
    print("  Attack: attacker strips one binding, keeps real manifest:")
    for line in stripped_verdict.format().split("\n"):
        print(f"    {line}")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'I heard a Fly buzz – when I died –'")
    print("    'The Stillness in the Room'")

    audit = {
        "bindings_in_manifest": len(manifest.bindings),
        "honest_all_valid": honest_verdict.all_valid,
        "stripped_all_valid": stripped_verdict.all_valid,
        "stripped_status": stripped_verdict.manifest_verdict.status,
        "stripped_removed_tokens":
            stripped_verdict.manifest_verdict.removed_tokens,
    }
    if artifact_dir:
        path = Path(artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "person_manifest_demo.json").write_text(
            json.dumps(audit, indent=2))
        print(f"\n  → {path}/person_manifest_demo.json")
    return audit
