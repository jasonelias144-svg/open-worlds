# multiverse_c31_test.py
import json
import pytest

from multiverse_c1 import create_identity
from multiverse_c13 import HAS_CRYPTO, KeyPair
from multiverse_c31 import (
    FederationVerdict, SignedFederationVerdict,
    sign_federation_verdict, verify_signed_federation_verdict,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _verdict(**overrides) -> FederationVerdict:
    defaults = dict(
        conformance_passed=True,
        world_admitted=True,
        world_offline_at_verification=True,
        listing_count=1,
        passport_verified_without_world=True,
        world_public_key="aa" * 32,
        registry_public_key="bb" * 32,
    )
    defaults.update(overrides)
    return FederationVerdict(**defaults)


def _signed(v=None, name="Live Verifier"):
    if v is None:
        v = _verdict()
    kp = KeyPair.generate()
    signer = create_identity(name)
    return sign_federation_verdict(v, kp, signer), kp, signer


# =====================================================================
# FederationVerdict construction
# =====================================================================

def test_federation_verdict_validates_fields():
    print("=== FederationVerdict validates field types ===")
    with pytest.raises(ValueError):
        _verdict(conformance_passed="yes")  # not a bool
    with pytest.raises(ValueError):
        _verdict(listing_count=-1)
    with pytest.raises(ValueError):
        _verdict(world_public_key="short")
    with pytest.raises(ValueError):
        _verdict(registry_public_key="not-hex")


def test_all_pass_requires_every_check():
    print("=== all_pass: AND of every check ===")
    assert _verdict().all_pass is True
    assert _verdict(conformance_passed=False).all_pass is False
    assert _verdict(world_admitted=False).all_pass is False
    assert _verdict(world_offline_at_verification=False).all_pass is False
    assert _verdict(passport_verified_without_world=False).all_pass is False


def test_federation_verdict_json_roundtrip():
    print("=== FederationVerdict JSON roundtrip ===")
    v = _verdict()
    wire = json.dumps(v.to_dict())
    revived = FederationVerdict.from_dict(json.loads(wire))
    assert revived == v


# =====================================================================
# Sign and verify — happy path
# =====================================================================

def test_sign_and_verify_happy():
    print("=== Sign and verify: happy path ===")
    signed, kp, signer = _signed()
    assert verify_signed_federation_verdict(
        signed, kp.public_key_hex())
    assert signed.signer_name == "Live Verifier"
    assert signed.verdict.all_pass is True


def test_sign_rejects_non_verdict():
    print("=== sign_federation_verdict rejects non-verdict ===")
    kp = KeyPair.generate()
    signer = create_identity("X")
    with pytest.raises(TypeError):
        sign_federation_verdict("not a verdict", kp, signer)


# =====================================================================
# Tampering — signature covers everything
# =====================================================================

def test_tampered_verdict_field_breaks_signature():
    print("=== Tampering with a verdict field breaks the signature ===")
    signed, kp, _ = _signed()
    # Flip one field in the verdict, keep original signature
    tampered_verdict = _verdict(
        passport_verified_without_world=False)  # was True
    tampered = SignedFederationVerdict(
        signer_id=signed.signer_id,
        signer_name=signed.signer_name,
        verdict=tampered_verdict,
        timestamp=signed.timestamp,
        signature=signed.signature,
    )
    assert not verify_signed_federation_verdict(
        tampered, kp.public_key_hex())


def test_tampered_world_public_key_breaks_signature():
    print("=== Tampering with world_public_key breaks signature ===")
    signed, kp, _ = _signed()
    tampered_verdict = _verdict(
        world_public_key="ff" * 32)
    tampered = SignedFederationVerdict(
        signer_id=signed.signer_id,
        signer_name=signed.signer_name,
        verdict=tampered_verdict,
        timestamp=signed.timestamp,
        signature=signed.signature,
    )
    assert not verify_signed_federation_verdict(
        tampered, kp.public_key_hex())


def test_tampered_signer_name_breaks_signature():
    print("=== Tampering with signer_name breaks the signature ===")
    signed, kp, _ = _signed()
    tampered = SignedFederationVerdict(
        signer_id=signed.signer_id,
        signer_name="Impostor",
        verdict=signed.verdict,
        timestamp=signed.timestamp,
        signature=signed.signature,
    )
    assert not verify_signed_federation_verdict(
        tampered, kp.public_key_hex())


def test_tampered_signer_id_breaks_signature():
    print("=== Tampering with signer_id breaks the signature ===")
    signed, kp, _ = _signed()
    tampered = SignedFederationVerdict(
        signer_id="other-token",
        signer_name=signed.signer_name,
        verdict=signed.verdict,
        timestamp=signed.timestamp,
        signature=signed.signature,
    )
    assert not verify_signed_federation_verdict(
        tampered, kp.public_key_hex())


def test_tampered_timestamp_breaks_signature():
    print("=== Tampering with the timestamp breaks the signature ===")
    signed, kp, _ = _signed()
    tampered = SignedFederationVerdict(
        signer_id=signed.signer_id,
        signer_name=signed.signer_name,
        verdict=signed.verdict,
        timestamp="2030-01-01T00:00:00+00:00",
        signature=signed.signature,
    )
    assert not verify_signed_federation_verdict(
        tampered, kp.public_key_hex())


# =====================================================================
# Wrong key
# =====================================================================

def test_wrong_public_key():
    print("=== Wrong public key → verification fails ===")
    signed, kp_real, _ = _signed()
    kp_other = KeyPair.generate()
    assert verify_signed_federation_verdict(
        signed, kp_real.public_key_hex())
    assert not verify_signed_federation_verdict(
        signed, kp_other.public_key_hex())


# =====================================================================
# JSON roundtrip
# =====================================================================

def test_json_roundtrip():
    print("=== SignedFederationVerdict JSON roundtrip ===")
    signed, kp, _ = _signed()
    wire = json.dumps(signed.to_dict())
    revived = SignedFederationVerdict.from_dict(json.loads(wire))
    assert verify_signed_federation_verdict(
        revived, kp.public_key_hex())
    assert revived.verdict == signed.verdict
    assert revived.signer_name == signed.signer_name


def test_json_roundtrip_preserves_all_pass():
    print("=== JSON roundtrip preserves all_pass ===")
    signed, kp, _ = _signed(_verdict(
        conformance_passed=True,
        passport_verified_without_world=True,
    ))
    wire = json.dumps(signed.to_dict())
    revived = SignedFederationVerdict.from_dict(json.loads(wire))
    assert revived.verdict.all_pass is True


# =====================================================================
# Never raises
# =====================================================================

def test_verifier_never_raises():
    print("=== verify_signed_federation_verdict never raises ===")
    assert not verify_signed_federation_verdict(None, "aa" * 32)
    assert not verify_signed_federation_verdict("not-a-verdict", "aa" * 32)
    assert not verify_signed_federation_verdict({}, "aa" * 32)
    # Missing key
    signed, _, _ = _signed()
    assert not verify_signed_federation_verdict(signed, "")


def test_signed_verdict_validates_fields():
    print("=== SignedFederationVerdict validates its fields ===")
    with pytest.raises(ValueError):
        SignedFederationVerdict(
            signer_id="", signer_name="X",
            verdict=_verdict(), timestamp="t", signature="s")
    with pytest.raises(ValueError):
        SignedFederationVerdict(
            signer_id="x", signer_name="X",
            verdict="not a verdict", timestamp="t", signature="s")


# =====================================================================
# Honest limit: authorship, not truth
# =====================================================================

def test_signature_attests_authorship_not_truth():
    """The limit, as a test. A dishonest client can sign a
    fabricated verdict. The signature is valid — the client really
    did sign it. The verifier must decide whether to trust the
    client, separately from verifying the signature.
    """
    print("=== Honest limit: signature attests authorship, not truth ===")
    # A fabricated verdict: everything claims success, but the keys
    # are not real federation keys
    fabricated = _verdict(
        world_public_key="00" * 32,
        registry_public_key="11" * 32,
    )
    signed, kp, _ = _signed(fabricated)
    # The signature IS valid
    assert verify_signed_federation_verdict(
        signed, kp.public_key_hex())
    print("  signature valid: True")
    print("  content true:    ???  (signature cannot tell)")
    # What a real trust decision looks like:
    #   1. verify_signed_federation_verdict(signed, known_key)
    #   2. Decide whether to trust the key's holder
    # C31 does (1). (2) is external.


if __name__ == "__main__":
    test_federation_verdict_validates_fields()
    test_all_pass_requires_every_check()
    test_federation_verdict_json_roundtrip()
    test_sign_and_verify_happy()
    test_sign_rejects_non_verdict()
    test_tampered_verdict_field_breaks_signature()
    test_tampered_world_public_key_breaks_signature()
    test_tampered_signer_name_breaks_signature()
    test_tampered_signer_id_breaks_signature()
    test_tampered_timestamp_breaks_signature()
    test_wrong_public_key()
    test_json_roundtrip()
    test_json_roundtrip_preserves_all_pass()
    test_verifier_never_raises()
    test_signed_verdict_validates_fields()
    test_signature_attests_authorship_not_truth()
