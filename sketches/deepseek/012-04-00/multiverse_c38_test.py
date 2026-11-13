# multiverse_c38_test.py
import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c1 import create_identity, Identity
from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c36 import (
    PersonIdentity, TokenBinding, create_person, bind_token,
)
from multiverse_c38 import (
    PersonManifest, ManifestVerdict,
    sign_person_manifest, verify_manifest_signature,
    verify_person_against_manifest,
    PersonPresentation, PresentationVerdict,
    verify_presentation,
    demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _person_with_n(n: int, name: str = "Aria"):
    person, kp = create_person(name)
    for i in range(n):
        tok = create_identity(f"{name}@{i}")
        person, _ = bind_token(
            person, kp, tok.token, tok.name, KeyPair.generate())
    return person, kp


# =====================================================================
# PersonManifest construction
# =====================================================================

def test_manifest_validates_fields():
    print("=== PersonManifest validates its fields ===")
    with pytest.raises(ValueError):
        PersonManifest(
            person_token="", person_name="X",
            person_public_key="aa" * 32,
            bindings=(), timestamp="t", signature="s")
    with pytest.raises(ValueError):
        PersonManifest(
            person_token="t", person_name="X",
            person_public_key="short",
            bindings=(), timestamp="t", signature="s")


def test_manifest_rejects_unsorted_bindings():
    print("=== PersonManifest rejects unsorted bindings ===")
    with pytest.raises(ValueError):
        PersonManifest(
            person_token="t", person_name="X",
            person_public_key="aa" * 32,
            bindings=(("b", "0" * 64), ("a", "1" * 64)),
            timestamp="t", signature="s")


def test_manifest_rejects_duplicate_tokens():
    print("=== PersonManifest rejects duplicate tokens ===")
    with pytest.raises(ValueError):
        PersonManifest(
            person_token="t", person_name="X",
            person_public_key="aa" * 32,
            bindings=(("a", "0" * 64), ("a", "1" * 64)),
            timestamp="t", signature="s")


# =====================================================================
# sign_person_manifest
# =====================================================================

def test_sign_manifest_happy():
    print("=== sign_person_manifest: happy path ===")
    person, kp = _person_with_n(3)
    manifest = sign_person_manifest(person, kp)
    assert len(manifest.bindings) == 3
    assert manifest.person_token == person.person.token
    assert manifest.person_public_key == kp.public_key_hex()
    tokens = [tok for tok, _ in manifest.bindings]
    assert tokens == sorted(tokens)


def test_sign_manifest_rejects_wrong_keypair():
    print("=== sign_person_manifest: wrong keypair raises ===")
    person, _ = _person_with_n(1)
    wrong_kp = KeyPair.generate()
    with pytest.raises(ValueError):
        sign_person_manifest(person, wrong_kp)


# =====================================================================
# verify_manifest_signature
# =====================================================================

def test_verify_manifest_sig_happy():
    print("=== verify_manifest_signature: valid ===")
    person, kp = _person_with_n(2)
    manifest = sign_person_manifest(person, kp)
    assert verify_manifest_signature(
        manifest, kp.public_key_hex())


def test_verify_manifest_sig_wrong_key():
    print("=== verify_manifest_signature: wrong key ===")
    person, kp = _person_with_n(2)
    manifest = sign_person_manifest(person, kp)
    wrong = KeyPair.generate().public_key_hex()
    assert not verify_manifest_signature(manifest, wrong)


def test_verify_manifest_sig_tampered():
    print("=== verify_manifest_signature: tampered bindings ===")
    person, kp = _person_with_n(2)
    manifest = sign_person_manifest(person, kp)
    tampered = PersonManifest(
        person_token=manifest.person_token,
        person_name=manifest.person_name,
        person_public_key=manifest.person_public_key,
        bindings=(manifest.bindings[0],),  # dropped one
        timestamp=manifest.timestamp,
        signature=manifest.signature,
    )
    assert not verify_manifest_signature(
        tampered, kp.public_key_hex())


# =====================================================================
# verify_person_against_manifest
# =====================================================================

def test_verify_person_manifest_happy():
    print("=== verify_person_against_manifest: valid ===")
    person, kp = _person_with_n(3)
    manifest = sign_person_manifest(person, kp)
    v = verify_person_against_manifest(
        person, manifest, kp.public_key_hex())
    assert v.valid
    assert v.status == "valid"
    assert not v.added_tokens
    assert not v.removed_tokens
    assert not v.changed_tokens


def test_verify_person_manifest_invalid_sig():
    print("=== verify: invalid signature ===")
    person, kp = _person_with_n(2)
    manifest = sign_person_manifest(person, kp)
    wrong = KeyPair.generate().public_key_hex()
    v = verify_person_against_manifest(person, manifest, wrong)
    assert not v.valid
    assert v.status == "invalid_signature"


def test_verify_person_manifest_person_key_mismatch():
    print("=== verify: person's declared key != trusted ===")
    person, kp = _person_with_n(2)
    manifest = sign_person_manifest(person, kp)
    # Attacker presents a person with a different declared key
    bad_person = PersonIdentity(
        person=person.person,
        person_public_key="ff" * 32,
        bindings=person.bindings,
    )
    v = verify_person_against_manifest(
        bad_person, manifest, kp.public_key_hex())
    assert not v.valid
    assert v.status == "person_mismatch"


def test_verify_person_manifest_token_mismatch():
    print("=== verify: person token != manifest token ===")
    person, kp = _person_with_n(2)
    manifest = sign_person_manifest(person, kp)
    other_person, other_kp = _person_with_n(2, "Bob")
    v = verify_person_against_manifest(
        other_person, manifest, kp.public_key_hex())
    # Sig verifies, but token check fails (person is Bob, manifest
    # was signed for Aria). Also person_public_key differs.
    assert not v.valid
    assert v.status in ("person_mismatch", "invalid_signature")


def test_verify_person_manifest_removed():
    print("=== verify: removed binding (person has fewer) ===")
    person, kp = _person_with_n(3)
    manifest = sign_person_manifest(person, kp)
    stripped = PersonIdentity(
        person=person.person,
        person_public_key=person.person_public_key,
        bindings=(person.bindings[0], person.bindings[1]),
    )
    v = verify_person_against_manifest(
        stripped, manifest, kp.public_key_hex())
    assert not v.valid
    assert v.status == "binding_mismatch"
    assert len(v.removed_tokens) == 1
    assert v.removed_tokens[0] == person.bindings[2].token


def test_verify_person_manifest_added():
    print("=== verify: added binding (person has more) ===")
    person, kp = _person_with_n(2)
    manifest = sign_person_manifest(person, kp)
    # Add a 3rd binding
    extra_tok = create_identity("Aria@extra")
    extended, _ = bind_token(
        person, kp, extra_tok.token, extra_tok.name,
        KeyPair.generate())
    v = verify_person_against_manifest(
        extended, manifest, kp.public_key_hex())
    assert not v.valid
    assert v.status == "binding_mismatch"
    assert len(v.added_tokens) == 1
    assert v.added_tokens[0] == extra_tok.token


def test_verify_person_manifest_changed():
    print("=== verify: changed binding (same token, new hash) ===")
    person, kp = _person_with_n(2)
    manifest = sign_person_manifest(person, kp)
    # Modify one binding's name (hash changes; binding's own sig is
    # now invalid, but the manifest check is only over hashes)
    original = person.bindings[0]
    modified = TokenBinding(
        token=original.token,
        name=original.name + "-modified",
        holder_public_key=original.holder_public_key,
        person_signature=original.person_signature,
        holder_signature=original.holder_signature,
    )
    tampered = PersonIdentity(
        person=person.person,
        person_public_key=person.person_public_key,
        bindings=(modified, person.bindings[1]),
    )
    v = verify_person_against_manifest(
        tampered, manifest, kp.public_key_hex())
    assert not v.valid
    assert v.status == "binding_mismatch"
    assert len(v.changed_tokens) == 1
    tok, _mh, _ah = v.changed_tokens[0]
    assert tok == original.token


def test_verify_person_manifest_never_raises():
    print("=== verify_person_against_manifest never raises ===")
    person, kp = _person_with_n(1)
    manifest = sign_person_manifest(person, kp)
    # Bad types
    assert not verify_person_against_manifest(
        None, manifest, kp.public_key_hex()).valid
    assert not verify_person_against_manifest(
        person, None, kp.public_key_hex()).valid
    assert not verify_person_against_manifest(
        person, manifest, "").valid


# =====================================================================
# PersonPresentation + verify_presentation
# =====================================================================

def test_presentation_happy():
    print("=== verify_presentation: valid ===")
    person, kp = _person_with_n(2)
    manifest = sign_person_manifest(person, kp)
    pp = PersonPresentation(person=person, manifest=manifest)
    v = verify_presentation(pp, kp.public_key_hex())
    assert v.all_valid
    assert v.bindings_ok
    assert v.manifest_ok
    assert v.set_matches


def test_presentation_stripped():
    print("=== verify_presentation: stripped binding → not all_valid ===")
    person, kp = _person_with_n(3)
    manifest = sign_person_manifest(person, kp)
    stripped = PersonIdentity(
        person=person.person,
        person_public_key=person.person_public_key,
        bindings=(person.bindings[0], person.bindings[1]),
    )
    pp = PersonPresentation(person=stripped, manifest=manifest)
    v = verify_presentation(pp, kp.public_key_hex())
    assert not v.all_valid
    assert v.bindings_ok  # each present binding still valid
    assert v.manifest_ok  # signature still valid
    assert not v.set_matches
    assert len(v.manifest_verdict.removed_tokens) == 1


def test_presentation_forged_manifest():
    print("=== verify_presentation: manifest signed by wrong key ===")
    person, kp = _person_with_n(2)
    attacker_kp = KeyPair.generate()
    # Attacker signs a manifest claiming to be Aria
    from multiverse_c38 import sign_person_manifest as spm
    # Can't sign AS Aria without her key; use an empty person and
    # a manifest with Aria's fields signed by attacker
    fake_person = PersonIdentity(
        person=person.person,
        person_public_key=attacker_kp.public_key_hex(),
        bindings=person.bindings,
    )
    # Attacker signs a manifest for the fake_person
    fake_manifest = spm(fake_person, attacker_kp)
    pp = PersonPresentation(person=person, manifest=fake_manifest)
    v = verify_presentation(pp, kp.public_key_hex())
    assert not v.all_valid
    assert not v.manifest_ok


def test_presentation_never_raises():
    print("=== verify_presentation never raises ===")
    person, kp = _person_with_n(1)
    manifest = sign_person_manifest(person, kp)
    pp = PersonPresentation(person=person, manifest=manifest)
    assert not verify_presentation(None, kp.public_key_hex()).all_valid
    assert not verify_presentation(pp, "").all_valid


# =====================================================================
# JSON roundtrips
# =====================================================================

def test_manifest_json_roundtrip():
    print("=== PersonManifest JSON roundtrip ===")
    person, kp = _person_with_n(3)
    manifest = sign_person_manifest(person, kp)
    wire = json.dumps(manifest.to_dict())
    revived = PersonManifest.from_dict(json.loads(wire))
    assert revived.canonical_payload() == manifest.canonical_payload()
    assert verify_manifest_signature(revived, kp.public_key_hex())


def test_presentation_json_roundtrip():
    print("=== PersonPresentation JSON roundtrip ===")
    person, kp = _person_with_n(2)
    manifest = sign_person_manifest(person, kp)
    pp = PersonPresentation(person=person, manifest=manifest)
    wire = json.dumps(pp.to_dict())
    revived = PersonPresentation.from_dict(json.loads(wire))
    v = verify_presentation(revived, kp.public_key_hex())
    assert v.all_valid


# =====================================================================
# Honest limit, tested
# =====================================================================

def test_honest_limit_person_can_shrink_their_own_manifest():
    """The limit named in the module docstring, as a test.

    A dishonest person can sign a new manifest that omits a
    binding they previously had. A reader who sees only the new
    manifest cannot detect the removal. This is the
    TOFU-vs-transparency-log limit; C38 does not close it.
    """
    print("=== Honest limit: person can shrink their own set ===")
    person, kp = _person_with_n(3)
    full_manifest = sign_person_manifest(person, kp)
    # Aria "removes" one binding by signing a new manifest
    # (unilaterally; no co-signer required)
    reduced_person = PersonIdentity(
        person=person.person,
        person_public_key=person.person_public_key,
        bindings=(person.bindings[0], person.bindings[1]),
    )
    reduced_manifest = sign_person_manifest(reduced_person, kp)
    # Against the REDUCED manifest, the presentation is valid
    pp = PersonPresentation(
        person=reduced_person, manifest=reduced_manifest)
    v = verify_presentation(pp, kp.public_key_hex())
    assert v.all_valid
    # But against the FULL manifest, the reduced presentation
    # shows the removal
    pp_against_full = PersonPresentation(
        person=reduced_person, manifest=full_manifest)
    v2 = verify_presentation(pp_against_full, kp.public_key_hex())
    assert not v2.all_valid
    assert len(v2.manifest_verdict.removed_tokens) == 1
    print("  reduced manifest verifies against reduced set: "
          f"{v.all_valid}")
    print("  reduced set against full manifest: "
          f"{len(v2.manifest_verdict.removed_tokens)} removed")
    print("  (Detecting the reduction requires a third party to")
    print("   have seen the full manifest — that's the limit.)")


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: Aria's manifest, honest and stripped ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["bindings_in_manifest"] == 3
    assert audit["honest_all_valid"] is True
    assert audit["stripped_all_valid"] is False
    assert audit["stripped_status"] == "binding_mismatch"
    assert len(audit["stripped_removed_tokens"]) == 1
    assert (tmp_path / "person_manifest_demo.json").exists()


if __name__ == "__main__":
    test_manifest_validates_fields()
    test_manifest_rejects_unsorted_bindings()
    test_manifest_rejects_duplicate_tokens()
    test_sign_manifest_happy()
    test_sign_manifest_rejects_wrong_keypair()
    test_verify_manifest_sig_happy()
    test_verify_manifest_sig_wrong_key()
    test_verify_manifest_sig_tampered()
    test_verify_person_manifest_happy()
    test_verify_person_manifest_invalid_sig()
    test_verify_person_manifest_person_key_mismatch()
    test_verify_person_manifest_token_mismatch()
    test_verify_person_manifest_removed()
    test_verify_person_manifest_added()
    test_verify_person_manifest_changed()
    test_verify_person_manifest_never_raises()
    test_presentation_happy()
    test_presentation_stripped()
    test_presentation_forged_manifest()
    test_presentation_never_raises()
    test_manifest_json_roundtrip()
    test_presentation_json_roundtrip()
    test_honest_limit_person_can_shrink_their_own_manifest()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
