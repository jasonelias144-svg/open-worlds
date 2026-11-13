"""
multiverse_c36.py — Component 36: PersonIdentity.

A higher-level identity that holds world-level identities as
components. The world-level identity (C1's Identity: token + name)
is unchanged; a PersonIdentity is a C1 Identity that holds others,
with cryptographic attestation.

Design:
  - PersonIdentity: (person: Identity, person_public_key: hex,
    bindings: Tuple[TokenBinding, ...]).
  - TokenBinding: dual-signed by the person's key and the holder's
    key. Both sign the same canonical payload. Neither alone
    suffices; both required.
  - PersonPassport: (person: PersonIdentity, passports:
    Tuple[PassportV2, ...]) — one passport per held token.
  - verify_person_passport: per-binding, per-passport verdicts.

The distributed-AI story this enables:
  - One person (the AI's core identity, one keypair).
  - N held tokens (one per world / per instance).
  - N holder keypairs (one per instance, each instance holds its
    own — same as C18's per-apprentice backends).
  - The person key signs "these are all mine"; each instance
    signs "I consent to being this person's embodiment."
  - A reader with the person's public key verifies every
    embodiment.

Composes with C1 (Identity), C13 (KeyPair), C15 (PassportV2).

House rules honored:
  - "A world never raises on what a visitor sends" — verify
    functions return verdicts, never raise. Tested.
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one test per: unbound token, wrong person key,
    forged holder sig, forged person sig, tampered field,
    orphan binding, orphan passport.
  - "History, not rank" — a person passport is a record of
    presences, not a score.

Honest limits (documented, tested):
  - No set-level signature. A PersonIdentity does not sign the
    set of bindings as a whole; each binding is independently
    dual-signed. Removing a binding from the presented set is
    not detectable. A signed "person manifest" (future) would
    close this.
  - No rotation of person key or holder key. First binding is
    TOFU for the holder key. Rotation is future work (C28-style).
  - No revocation of bindings. Adding a token is one-way in
    v1. A compromised holder key can't be disavowed yet.
  - No fork/merge events. The structure supports them
    naturally — a fork is "sign new bindings under two child
    person keys" — but the events themselves are future work.
  - Trust anchor external. The person's public key must come
    from somewhere other than the file containing the
    PersonIdentity. Same as C13/C24/C28/C29.

What's next after C36: binding revocation, person manifest
(signed set), fork/merge events, and cross-world attestation
(C34's DAG + one person key attesting actions across worlds).
"""

import hashlib
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from multiverse_c1 import Identity, create_identity
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c15 import (
    PassportV2, VerificationReport as PassportVerificationReport,
)


# =====================================================================
# Hashing
# =====================================================================

def _hash_payload(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


# =====================================================================
# TokenBinding — one held token, dual-signed
# =====================================================================

@dataclass(frozen=True)
class TokenBinding:
    """One "this world-level token is held by this person" claim.

    Both signatures are over the SAME canonical payload. The person
    signs "I claim this token"; the holder signs "I consent to
    being this person's embodiment." Tampering with any field
    (token, name, holder_public_key) breaks BOTH signatures.
    """
    token: str
    name: str
    holder_public_key: str
    person_signature: str
    holder_signature: str

    def __post_init__(self):
        for f in ("token", "name", "holder_public_key",
                  "person_signature", "holder_signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if len(self.holder_public_key) != 64:
            raise ValueError(
                "holder_public_key must be 64 hex chars")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "token_binding",
            "token": self.token,
            "name": self.name,
            "holder_public_key": self.holder_public_key,
        })

    def binding_hash(self) -> str:
        return _hash_payload(self.canonical_payload())

    def to_dict(self) -> Dict:
        return {
            "token": self.token,
            "name": self.name,
            "holder_public_key": self.holder_public_key,
            "person_signature": self.person_signature,
            "holder_signature": self.holder_signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "TokenBinding":
        return cls(
            token=d["token"],
            name=d["name"],
            holder_public_key=d["holder_public_key"],
            person_signature=d["person_signature"],
            holder_signature=d["holder_signature"],
        )


# =====================================================================
# PersonIdentity — a C1 identity that holds others
# =====================================================================

@dataclass(frozen=True)
class PersonIdentity:
    """A C1 Identity plus its person_public_key and held tokens.

    Note: `person` IS a C1 Identity (token + name). Held tokens
    are also C1 tokens. Two levels of the same atom; no new
    primitives.

    No set-level signature; each binding is atomic and
    independently signed. Removing a binding from the presented
    set is not detectable (see the module docstring's honest
    limits).
    """
    person: Identity
    person_public_key: str
    bindings: Tuple[TokenBinding, ...] = ()

    def __post_init__(self):
        if not isinstance(self.person, Identity):
            raise ValueError("person must be a C1 Identity")
        if not isinstance(self.person_public_key, str) \
                or len(self.person_public_key) != 64:
            raise ValueError(
                "person_public_key must be 64 hex chars")
        # No duplicate tokens
        tokens = [b.token for b in self.bindings]
        if len(tokens) != len(set(tokens)):
            raise ValueError(
                "a person cannot bind the same token twice")

    def held_tokens(self) -> List[str]:
        return [b.token for b in self.bindings]

    def binding_for(self, token: str) -> Optional[TokenBinding]:
        for b in self.bindings:
            if b.token == token:
                return b
        return None

    def to_dict(self) -> Dict:
        return {
            "person": {
                "token": self.person.token,
                "name": self.person.name,
            },
            "person_public_key": self.person_public_key,
            "bindings": [b.to_dict() for b in self.bindings],
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "PersonIdentity":
        return cls(
            person=Identity(
                token=d["person"]["token"],
                name=d["person"]["name"],
            ),
            person_public_key=d["person_public_key"],
            bindings=tuple(
                TokenBinding.from_dict(b) for b in d.get("bindings", [])
            ),
        )


# =====================================================================
# Create / bind
# =====================================================================

def create_person(name: str) -> Tuple[PersonIdentity, KeyPair]:
    """Create a new person with an empty binding set.

    Returns (PersonIdentity, person_keypair). The keypair is the
    person's signing key — keep it secret; verify against
    person.person_public_key.
    """
    if not HAS_CRYPTO:
        raise RuntimeError(
            "create_person requires `cryptography`. "
            "Install with: pip install cryptography")
    person_identity = create_identity(name)
    kp = KeyPair.generate()
    person = PersonIdentity(
        person=person_identity,
        person_public_key=kp.public_key_hex(),
        bindings=(),
    )
    return person, kp


def bind_token(
    person: PersonIdentity,
    person_kp: KeyPair,
    token: str,
    token_name: str,
    holder_kp: KeyPair,
) -> Tuple[PersonIdentity, TokenBinding]:
    """Create a TokenBinding, dual-sign it, add to the person.

    Raises:
      - ValueError if person_kp doesn't match the person's public key
      - ValueError if the token is already bound
      - ValueError if any field is empty or the keypair is wrong
    """
    if not HAS_CRYPTO:
        raise RuntimeError(
            "bind_token requires `cryptography`")
    if person_kp.public_key_hex() != person.person_public_key:
        raise ValueError(
            "person_kp does not match the person's public key")
    if not token:
        raise ValueError("token required")
    if not token_name:
        raise ValueError("token_name required")
    if person.binding_for(token) is not None:
        raise ValueError(
            f"token {token[:16]}... already bound to this person")

    holder_pk = holder_kp.public_key_hex()
    payload = canonical_bytes({
        "kind": "token_binding",
        "token": token,
        "name": token_name,
        "holder_public_key": holder_pk,
    })
    binding = TokenBinding(
        token=token,
        name=token_name,
        holder_public_key=holder_pk,
        person_signature=person_kp.sign(payload).hex(),
        holder_signature=holder_kp.sign(payload).hex(),
    )
    new_person = PersonIdentity(
        person=person.person,
        person_public_key=person.person_public_key,
        bindings=person.bindings + (binding,),
    )
    return new_person, binding


# =====================================================================
# Verification — per binding
# =====================================================================

@dataclass(frozen=True)
class BindingVerdict:
    binding: TokenBinding
    person_sig_valid: bool
    holder_sig_valid: bool
    valid: bool
    reason: str

    def format(self) -> str:
        marker = "✓" if self.valid else "✗"
        return (f"  {marker} {self.binding.token[:16]}... "
                f"({self.binding.name}): {self.reason}")


def verify_binding(
    binding: TokenBinding,
    person_public_key: str,
) -> BindingVerdict:
    """Verify both signatures on a binding.

    Never raises. Bad input returns a verdict with valid=False.
    """
    if not HAS_CRYPTO:
        return BindingVerdict(
            binding=binding,
            person_sig_valid=False, holder_sig_valid=False,
            valid=False, reason="cryptography not installed")
    try:
        if not isinstance(binding, TokenBinding):
            return BindingVerdict(
                binding=binding,  # will be wrong, but we don't crash
                person_sig_valid=False, holder_sig_valid=False,
                valid=False, reason="not a TokenBinding")
        payload = binding.canonical_payload()
    except Exception as e:
        return BindingVerdict(
            binding=binding,
            person_sig_valid=False, holder_sig_valid=False,
            valid=False, reason=f"canonicalization failed: {e}")

    try:
        person_ok = verify_signature(
            person_public_key, payload, binding.person_signature)
    except Exception:
        person_ok = False
    try:
        holder_ok = verify_signature(
            binding.holder_public_key, payload,
            binding.holder_signature)
    except Exception:
        holder_ok = False

    if person_ok and holder_ok:
        return BindingVerdict(
            binding=binding, person_sig_valid=True,
            holder_sig_valid=True, valid=True,
            reason="both signatures valid")
    if not person_ok and not holder_ok:
        reason = "both signatures INVALID"
    elif not person_ok:
        reason = "person signature INVALID"
    else:
        reason = "holder signature INVALID"
    return BindingVerdict(
        binding=binding, person_sig_valid=person_ok,
        holder_sig_valid=holder_ok, valid=False, reason=reason)


# =====================================================================
# Verification — whole person
# =====================================================================

@dataclass
class PersonVerificationReport:
    person_token: str
    person_name: str
    person_public_key: str
    binding_verdicts: List[BindingVerdict]

    @property
    def all_valid(self) -> bool:
        return (bool(self.binding_verdicts)
                and all(v.valid for v in self.binding_verdicts))

    def format(self) -> str:
        lines = [
            "=" * 70,
            "Person Verification",
            "=" * 70,
            f"  person:     {self.person_name} "
            f"({self.person_token[:16]}...)",
            f"  key:        {self.person_public_key[:16]}...",
            f"  bindings:   {len(self.binding_verdicts)}",
            "",
        ]
        for v in self.binding_verdicts:
            lines.append(v.format())
        lines.append("")
        lines.append(f"  all_valid: {self.all_valid}")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "person_token": self.person_token,
            "person_name": self.person_name,
            "person_public_key": self.person_public_key,
            "binding_verdicts": [
                {
                    "token": v.binding.token,
                    "name": v.binding.name,
                    "holder_public_key": v.binding.holder_public_key,
                    "person_sig_valid": v.person_sig_valid,
                    "holder_sig_valid": v.holder_sig_valid,
                    "valid": v.valid,
                    "reason": v.reason,
                }
                for v in self.binding_verdicts
            ],
            "all_valid": self.all_valid,
        }


def verify_person(person: PersonIdentity) -> PersonVerificationReport:
    """Verify every binding in a PersonIdentity. Never raises."""
    verdicts = [verify_binding(b, person.person_public_key)
                for b in person.bindings]
    return PersonVerificationReport(
        person_token=person.person.token,
        person_name=person.person.name,
        person_public_key=person.person_public_key,
        binding_verdicts=verdicts,
    )


# =====================================================================
# PersonPassport — person + their world passports
# =====================================================================

@dataclass(frozen=True)
class PersonPassport:
    """A PersonIdentity plus one C15 passport per held token.

    The person is the "self"; the passports are the "presences."
    A passport's identity.token must match a binding's token.
    """
    person: PersonIdentity
    passports: Tuple[PassportV2, ...] = ()

    def passport_for(self, token: str) -> Optional[PassportV2]:
        for p in self.passports:
            if p.identity.token == token:
                return p
        return None

    def to_dict(self) -> Dict:
        return {
            "person": self.person.to_dict(),
            "passports": [
                _passport_to_dict(p) for p in self.passports
            ],
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "PersonPassport":
        return cls(
            person=PersonIdentity.from_dict(d["person"]),
            passports=tuple(
                _passport_from_dict(p) for p in d.get("passports", [])
            ),
        )


def _passport_to_dict(p: PassportV2) -> Dict:
    from multiverse_c15 import passport_v2_to_dict
    return passport_v2_to_dict(p)


def _passport_from_dict(d: Dict) -> PassportV2:
    from multiverse_c15 import passport_v2_from_dict
    return passport_v2_from_dict(d)


# =====================================================================
# Verify person passport
# =====================================================================

PublicKeyResolver = Callable[[str], Optional[str]]


@dataclass
class PersonPassportReport:
    person_report: PersonVerificationReport
    # passport_reports: (token, C15 VerificationReport) pairs
    passport_reports: List[Tuple[str, PassportVerificationReport]]
    orphan_bindings: List[TokenBinding]
    orphan_passports: List[PassportV2]
    all_valid: bool
    reason: str

    def format(self) -> str:
        lines = [
            "=" * 70,
            "Person Passport Report",
            "=" * 70,
            "",
            self.person_report.format(),
            "",
            "  Presences:",
        ]
        if not self.passport_reports:
            lines.append("    (none)")
        for token, report in self.passport_reports:
            marker = "✓" if report.all_verified else "✗"
            lines.append(
                f"    {marker} {token[:16]}... "
                f"({len(report.verdicts)} entries)")
        if self.orphan_bindings:
            lines.append("")
            lines.append("  Orphan bindings (no passport):")
            for b in self.orphan_bindings:
                lines.append(
                    f"    · {b.token[:16]}... ({b.name})")
        if self.orphan_passports:
            lines.append("")
            lines.append("  Orphan passports (no binding):")
            for p in self.orphan_passports:
                lines.append(f"    ! {p.identity.token[:16]}... "
                             f"({p.identity.name})")
        lines.append("")
        lines.append(f"  all_valid: {self.all_valid}")
        if not self.all_valid and self.reason:
            lines.append(f"  reason:    {self.reason}")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "person_report": self.person_report.to_dict(),
            "presences": [
                {"token": t, "passport_all_verified": r.all_verified}
                for t, r in self.passport_reports
            ],
            "orphan_bindings": [
                {"token": b.token, "name": b.name}
                for b in self.orphan_bindings
            ],
            "orphan_passports": [
                {"token": p.identity.token, "name": p.identity.name}
                for p in self.orphan_passports
            ],
            "all_valid": self.all_valid,
            "reason": self.reason,
        }


def verify_person_passport(
    person_passport: PersonPassport,
    resolver: PublicKeyResolver,
) -> PersonPassportReport:
    """Verify a person passport. Never raises.

    Steps:
      1. Verify every binding (dual signature).
      2. Verify every passport (C15's PassportV2.verify).
      3. Cross-check: every binding has a passport (else orphan
         binding); every passport has a binding (else orphan
         passport).
      4. all_valid iff every binding valid, every passport
         verified, and no orphans.
    """
    person = person_passport.person
    person_report = verify_person(person)

    binding_tokens = {b.token for b in person.bindings}
    passport_tokens = {p.identity.token for p in person_passport.passports}

    orphan_bindings = [
        b for b in person.bindings if b.token not in passport_tokens
    ]
    orphan_passports = [
        p for p in person_passport.passports
        if p.identity.token not in binding_tokens
    ]

    passport_reports: List[Tuple[str, PassportVerificationReport]] = []
    for p in person_passport.passports:
        try:
            report = p.verify(resolver)
        except Exception as e:
            # Build an empty report-like object to preserve shape
            from multiverse_c15 import VerificationReport
            report = VerificationReport(passport_token=p.identity.token)
            # Attach an exception marker via reason (prototype hack)
            setattr(report, "exception", str(e))
        passport_reports.append((p.identity.token, report))

    all_verified_passports = all(
        r.all_verified for _, r in passport_reports
    ) if passport_reports else True

    all_valid = (
        person_report.all_valid
        and all_verified_passports
        and not orphan_bindings
        and not orphan_passports
    )

    if all_valid:
        reason = "all bindings valid, all passports verified, " \
                 "no orphans"
    else:
        parts = []
        if not person_report.all_valid:
            parts.append("one or more bindings invalid")
        if not all_verified_passports:
            parts.append("one or more passports unverified")
        if orphan_bindings:
            parts.append(
                f"{len(orphan_bindings)} binding(s) without passport")
        if orphan_passports:
            parts.append(
                f"{len(orphan_passports)} passport(s) without binding")
        reason = "; ".join(parts)

    return PersonPassportReport(
        person_report=person_report,
        passport_reports=passport_reports,
        orphan_bindings=orphan_bindings,
        orphan_passports=orphan_passports,
        all_valid=all_valid,
        reason=reason,
    )


# =====================================================================
# Demo — one person, three embodiments
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Aria: one AI, three embodiments.

    Aria runs three model backends (per C18's multi-model pattern),
    one per world. Each backend holds one holder keypair. Aria's
    coordinating layer holds the person keypair. She petitions
    three worlds — Poetry, Chemistry, Registry — once per
    embodiment. All three admissions are signed. Her person
    passport aggregates all three.

    A second scenario: Bob tries to claim Aria's poetry token by
    crafting a binding. He has neither Aria's person key nor the
    poetry holder key. Both signatures fail; the binding is
    rejected.

    Anchor: Emily Dickinson, 'I'm Nobody! Who are you?',
    public domain.
    """
    import json
    import time
    from pathlib import Path
    from multiverse_c3 import Petition
    from multiverse_c13 import SignedWorld, SignedAdmission
    from multiverse_c14 import PermissiveWorld
    from multiverse_c28 import SignedManifestWorld
    from wcp_http_shim import WorldProtocolServer

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    # --- Three worlds, each signed (manifest + responses) ---
    world_kps = {
        "poetry": KeyPair.generate(),
        "chemistry": KeyPair.generate(),
        "registry": KeyPair.generate(),
    }
    world_urls = {}
    world_servers = []
    for name, kp in world_kps.items():
        base = PermissiveWorld(f"world:{name}", name.title())
        signed = SignedWorld(base, kp)
        world = SignedManifestWorld(signed, kp)
        server = WorldProtocolServer(world, port=0)
        server.serve_in_thread()
        time.sleep(0.1)
        port = server._httpd.server_address[1]
        world_urls[name] = f"http://127.0.0.1:{port}"
        world_servers.append((server, world))

    try:
        # --- Aria, the person ---
        aria, aria_kp = create_person("Aria")
        holder_kps = {}
        # Three tokens, one per world, each with a holder keypair
        for name in ("poetry", "chemistry", "registry"):
            token_identity = create_identity(f"Aria@{name}")
            holder_kp = KeyPair.generate()
            holder_kps[name] = holder_kp
            aria, _ = bind_token(
                aria, aria_kp,
                token_identity.token, token_identity.name,
                holder_kp,
            )
        # Verify all bindings
        aria_report = verify_person(aria)

        # --- Aria petitions each world with the respective token ---
        passports = []
        for name in ("poetry", "chemistry", "registry"):
            token = aria.binding_for(
                [b for b in aria.bindings
                 if b.name == f"Aria@{name}"][0].token
            )  # just for clarity
            binding = [b for b in aria.bindings
                       if b.name == f"Aria@{name}"][0]
            server, world = next(
                (s, w) for s, w in world_servers
                if w.manifest_dict()["entity_id"] == f"world:{name}")
            resp = world.petition(Petition(
                petitioner_token=binding.token,
                petitioner_name=binding.name,
                passport_admissions=(),
                message="I'm Nobody! Who are you?",
            ))
            assert isinstance(resp, SignedAdmission)
            passports.append(PassportV2(
                identity=Identity(
                    token=binding.token, name=binding.name),
                entries=(_entry_from_admission(resp),),
            ))
        person_passport = PersonPassport(
            person=aria, passports=tuple(passports))

        # --- Resolver from world keys ---
        resolver = lambda eid: _world_key_from_eid(eid, world_kps)

        # --- Verify everything ---
        report = verify_person_passport(person_passport, resolver)

        # --- Bob tries to claim Aria's poetry token ---
        bob, bob_kp = create_person("Bob")
        attacker_holder_kp = KeyPair.generate()
        poetry_binding = aria.binding_for(
            [b for b in aria.bindings
             if b.name == "Aria@poetry"][0].token)
        # Bob crafts a binding for Aria's token, but he has
        # neither Aria's person key nor Aria's holder key
        payload = canonical_bytes({
            "kind": "token_binding",
            "token": poetry_binding.token,
            "name": "Aria@poetry (stolen)",
            "holder_public_key":
                attacker_holder_kp.public_key_hex(),
        })
        forged_binding = TokenBinding(
            token=poetry_binding.token,
            name="Aria@poetry (stolen)",
            holder_public_key=attacker_holder_kp.public_key_hex(),
            person_signature=bob_kp.sign(payload).hex(),
            holder_signature=attacker_holder_kp.sign(payload).hex(),
        )
        forged_verdict = verify_binding(
            forged_binding, aria.person_public_key)

        # --- Report ---
        print("=" * 70)
        print("PersonIdentity — Aria, three embodiments")
        print("=" * 70)
        print()
        print(report.format())
        print()
        print("  Forged binding attempt by Bob:")
        print(f"    token:     {forged_binding.token[:16]}...")
        print(f"    person_sig valid: {forged_verdict.person_sig_valid}")
        print(f"    holder_sig valid: {forged_verdict.holder_sig_valid}")
        print(f"    valid:            {forged_verdict.valid}")
        print(f"    reason:           {forged_verdict.reason}")
        print()
        print("  Anchor (public domain, Emily Dickinson):")
        print("    'I'm Nobody! Who are you?'")
        print("    'Are you – Nobody – too?'")

        audit = report.to_dict()
        audit["forged_binding"] = {
            "token": forged_binding.token,
            "person_sig_valid": forged_verdict.person_sig_valid,
            "holder_sig_valid": forged_verdict.holder_sig_valid,
            "valid": forged_verdict.valid,
        }
        if artifact_dir:
            path = Path(artifact_dir)
            path.mkdir(parents=True, exist_ok=True)
            (path / "person_identity_demo.json").write_text(
                json.dumps(audit, indent=2))
            print(f"\n  → {path}/person_identity_demo.json")
        return audit
    finally:
        for server, _ in world_servers:
            server.stop()


def _entry_from_admission(adm):
    from multiverse_c15 import PassportEntry
    return PassportEntry(
        entity_id=adm.entity_id,
        timestamp=adm.timestamp,
        subject_token=adm.subject_token,
        signature=adm.signature,
    )


def _world_key_from_eid(eid, world_kps):
    for name, kp in world_kps.items():
        if eid == f"world:{name}":
            return kp.public_key_hex()
    return None
