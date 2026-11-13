# multiverse_c13_test.py
import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import Petition, Act, Refusal
from multiverse_c4 import PoetryWorld

from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, SignedAdmission, SignedAck,
    canonical_bytes, verify_signature,
    verify_signed_admission, verify_signed_ack,
    signed_manifest_dict, SignedWorld, SignedClient,
    VerifiedResponse,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO,
    reason="cryptography not installed (pip install cryptography)")


def _petition(name="Alice", token=None):
    if token is None:
        token = create_identity(name).token
    return Petition(
        petitioner_token=token, petitioner_name=name,
        passport_admissions=(), message="test",
    )


# =====================================================================
# Basic crypto
# =====================================================================

def test_keypair_sign_verify_roundtrip():
    print("=== KeyPair: sign and verify ===")
    kp = KeyPair.generate()
    pub = kp.public_key_hex()
    payload = b"hello, wcp/0.2"
    sig = kp.sign(payload).hex()
    print(f"  public_key: {pub[:16]}... ({len(pub)} hex chars)")
    print(f"  signature:  {sig[:16]}... ({len(sig)} hex chars)")
    assert verify_signature(pub, payload, sig)


def test_signature_rejects_tampered_payload():
    print("=== Signature rejects tampered payload ===")
    kp = KeyPair.generate()
    pub = kp.public_key_hex()
    payload = b"original message"
    sig = kp.sign(payload).hex()
    assert verify_signature(pub, payload, sig)
    # Change one byte
    tampered = b"original messagf"
    assert not verify_signature(pub, tampered, sig)


def test_signature_rejects_wrong_key():
    print("=== Signature rejects wrong key ===")
    kp1 = KeyPair.generate()
    kp2 = KeyPair.generate()
    payload = b"message"
    sig = kp1.sign(payload).hex()
    # Verifying with kp2's public key should fail
    assert not verify_signature(kp2.public_key_hex(), payload, sig)
    # Verifying with kp1's public key should succeed
    assert verify_signature(kp1.public_key_hex(), payload, sig)


# =====================================================================
# Signed world
# =====================================================================

def test_signed_world_manifest_has_public_key():
    print("=== Signed world: manifest has public_key ===")
    base = PoetryWorld("world:poetry", "The Poetry World")
    signed = SignedWorld(base)
    m = signed.manifest_dict()
    print(f"  protocol_version: {m['protocol_version']}")
    print(f"  public_key: {m['public_key'][:16]}...")
    assert m["protocol_version"] == "WCP/0.2"
    assert len(m["public_key"]) == 64


def test_signed_world_petition_returns_signed_admission():
    print("=== Signed world: petition → SignedAdmission ===")
    base = PoetryWorld("world:poetry", "The Poetry World")
    signed = SignedWorld(base)
    client = SignedClient(signed)

    p = _petition()
    result = client.petition(p)
    print(f"  verified: {result.verified}")
    print(f"  reason:   {result.reason}")
    assert result.verified is True
    assert isinstance(result.response, SignedAdmission)
    assert result.response.subject_token == p.petitioner_token


def test_signed_world_act_returns_signed_ack():
    print("=== Signed world: act → SignedAck ===")
    base = PoetryWorld("world:poetry", "The Poetry World")
    signed = SignedWorld(base)
    client = SignedClient(signed)

    p = _petition()
    client.petition(p)  # admit
    act = Act(
        actor_token=p.petitioner_token,
        type="poem.turn",
        payload={
            "acknowledgment": "(seed)",
            "proposal": "a line",
            "invitation": "?",
            "holds_open": True,
        },
    )
    result = client.act(act)
    print(f"  verified: {result.verified}")
    print(f"  reason:   {result.reason}")
    assert result.verified is True
    assert isinstance(result.response, SignedAck)


# =====================================================================
# The security property: forgery is now DETECTED
# =====================================================================

def test_forged_admission_detected():
    """The key test. Compare to Component 2's demonstration that
    a forged admission was structurally indistinguishable from a
    real one. Now: verifiable.
    """
    print("=== FORGERY: attacker cannot fabricate an admission ===")

    # Real world, real keypair
    real_world = SignedWorld(
        PoetryWorld("world:real", "The Real World"))
    real_pub = real_world.keypair.public_key_hex()

    # Attacker's keypair (their own, NOT the real world's)
    attacker_kp = KeyPair.generate()

    # Attacker crafts an admission claiming to be from world:real
    # They sign with their own key
    forge_payload = canonical_bytes({
        "kind": "admission",
        "entity_id": "world:real",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "subject_token": "attacker:token",
    })
    forged = SignedAdmission(
        entity_id="world:real",
        timestamp="2024-01-01T00:00:00+00:00",
        subject_token="attacker:token",
        signature=attacker_kp.sign(forge_payload).hex(),
    )

    # Verify against the REAL world's public key
    is_valid = verify_signed_admission(real_pub, forged)
    print(f"  forged admission verified: {is_valid}")
    print(f"  (Component 2 would have said: structurally indistinguishable)")
    assert is_valid is False
    print("  → Forgery DETECTED")


def test_tampered_admission_detected():
    print("=== TAMPERING: modified timestamp fails verification ===")
    real_world = SignedWorld(
        PoetryWorld("world:real", "The Real World"))
    client = SignedClient(real_world)

    p = _petition()
    result = client.petition(p)
    original = result.response
    assert isinstance(original, SignedAdmission)

    # Attacker alters the timestamp
    tampered = SignedAdmission(
        entity_id=original.entity_id,
        timestamp="2030-01-01T00:00:00+00:00",  # changed
        subject_token=original.subject_token,
        signature=original.signature,           # original sig
    )
    # Verify
    ok = verify_signed_admission(
        real_world.keypair.public_key_hex(), tampered)
    print(f"  tampered admission verified: {ok}")
    assert ok is False
    print("  → Tampering DETECTED")


def test_tampered_subject_detected():
    print("=== TAMPERING: swapping subject token fails verification ===")
    real_world = SignedWorld(
        PoetryWorld("world:real", "The Real World"))
    client = SignedClient(real_world)

    p = _petition()
    result = client.petition(p)
    original = result.response

    # Attacker tries to redirect the admission to themselves
    tampered = SignedAdmission(
        entity_id=original.entity_id,
        timestamp=original.timestamp,
        subject_token="attacker:different-token",   # changed
        signature=original.signature,
    )
    ok = verify_signed_admission(
        real_world.keypair.public_key_hex(), tampered)
    print(f"  tampered admission verified: {ok}")
    assert ok is False
    print("  → Subject swap DETECTED")


# =====================================================================
# Full signed collaboration
# =====================================================================

def test_full_signed_collaboration():
    print("=== Full signed collaboration ===")
    base = PoetryWorld(
        "world:poetry", "The Poetry World",
        law=__import__("multiverse_c4").PoetryWorldLaw(
            convergence_window=3, convergence_similarity=0.5,
        ))
    signed = SignedWorld(base)
    client = SignedClient(signed)

    # Jason petitions — verified
    jason = _petition("Jason")
    r = client.petition(jason)
    assert r.verified is True

    # Jason turns — verified
    seed = Act(
        actor_token=jason.petitioner_token,
        type="poem.turn",
        payload={
            "acknowledgment": "(seed)",
            "proposal": "Go\nBe a black widow\nAnd dangle in webs.",
            "invitation": "What does 'Go' open?",
            "holds_open": True,
        },
    )
    a = client.act(seed)
    assert a.verified is True

    # Alice petitions — verified
    alice = _petition("Alice")
    r2 = client.petition(alice)
    assert r2.verified is True

    # Alice turns — verified
    alice_turn = Act(
        actor_token=alice.petitioner_token,
        type="poem.turn",
        payload={
            "acknowledgment": "You said 'black widow' and 'web'.",
            "proposal": "The web is not hers.",
            "invitation": "Whose voice is the thread?",
            "holds_open": True,
        },
    )
    a2 = client.act(alice_turn)
    assert a2.verified is True

    # Log is append-only and reflects all events
    log = signed.log_since(None)
    kinds = [e.kind for e in log]
    print(f"  log kinds: {kinds}")
    assert "admission" in kinds
    assert "turn" in kinds


# =====================================================================
# Backward compatibility
# =====================================================================

def test_unsigned_world_still_works():
    print("=== Unsigned WCP/0.1 world still works ===")
    # A plain WCP/0.1 world (no signing wrapper)
    base = PoetryWorld("world:poetry", "The Poetry World")
    # It has no signature support — but the base class still works
    r = base.petition(_petition("Alice"))
    print(f"  petition response type: {type(r).__name__}")
    # The response is a WCPAdmission — WCP/0.1 shape
    from multiverse_c3 import Admission
    assert isinstance(r, Admission)


def test_signed_admission_converts_to_wcp_0_1():
    print("=== SignedAdmission → WCP/0.1 Admission ===")
    kp = KeyPair.generate()
    adm = SignedAdmission(
        entity_id="world:test",
        timestamp="2024-01-01T00:00:00+00:00",
        subject_token="alice:token",
        signature="deadbeef" * 16,
    )
    # Convert
    plain = adm.to_wcp_0_1()
    print(f"  plain: {plain}")
    from multiverse_c3 import Admission
    assert isinstance(plain, Admission)
    assert plain.entity_id == "world:test"
    assert plain.timestamp == "2024-01-01T00:00:00+00:00"


if __name__ == "__main__":
    if not HAS_CRYPTO:
        print("SKIP: cryptography not installed")
        print("  pip install cryptography")
    else:
        test_keypair_sign_verify_roundtrip()
        test_signature_rejects_tampered_payload()
        test_signature_rejects_wrong_key()
        test_signed_world_manifest_has_public_key()
        test_signed_world_petition_returns_signed_admission()
        test_signed_world_act_returns_signed_ack()
        test_forged_admission_detected()
        test_tampered_admission_detected()
        test_tampered_subject_detected()
        test_full_signed_collaboration()
        test_unsigned_world_still_works()
        test_signed_admission_converts_to_wcp_0_1()
