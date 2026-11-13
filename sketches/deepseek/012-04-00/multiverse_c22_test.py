# multiverse_c22_test.py
import time
import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import Petition, Act, Refusal
from multiverse_c13 import HAS_CRYPTO, KeyPair, SignedAdmission, SignedAck
from multiverse_c14 import PermissiveWorld
from multiverse_c15 import PassportV2
from multiverse_c22 import (
    LeavePetition, Leave, SignedLeave,
    LeaveCapableWorld, SignedLeaveWorld,
    Departure, PassportV2WithDepartures,
    verify_departure, enrich_with_departure,
    EntryProvenance,
)
from wcp_http_shim import WorldProtocolServer


# =====================================================================
# Leave: house rules
# =====================================================================

def test_leave_requires_admission():
    print("=== Leave without admission → Refusal (never raises) ===")
    world = LeaveCapableWorld("world:a", "World A")
    alice = create_identity("Alice")
    # Alice never petitioned. Leave must be a Refusal, not an error.
    result = world.leave(LeavePetition(leaver_token=alice.token))
    assert isinstance(result, Refusal)
    assert result.reason == "not admitted"


def test_leave_after_admission():
    print("=== Leave after admission → Leave ===")
    world = LeaveCapableWorld("world:a", "World A")
    alice = create_identity("Alice")
    adm = world.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="hi"))
    assert adm is not None
    leave = world.leave(LeavePetition(leaver_token=alice.token))
    assert isinstance(leave, Leave)
    assert leave.entity_id == "world:a"


def test_leave_is_idempotent():
    """Leaving twice returns the SAME timestamp. No duplicate log."""
    print("=== Leave is idempotent ===")
    world = LeaveCapableWorld("world:a", "World A")
    alice = create_identity("Alice")
    world.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="hi"))
    l1 = world.leave(LeavePetition(leaver_token=alice.token))
    l2 = world.leave(LeavePetition(leaver_token=alice.token))
    assert isinstance(l1, Leave)
    assert isinstance(l2, Leave)
    assert l1.timestamp == l2.timestamp
    # Only one "leave" log entry
    leave_entries = [e for e in world.log_since(None)
                     if e.kind == "leave"]
    assert len(leave_entries) == 1


def test_act_after_leave_is_refused():
    """Leaving isn't symbolic. After leave, act is refused."""
    print("=== Act after leave → Refusal ===")
    world = LeaveCapableWorld("world:a", "World A")
    alice = create_identity("Alice")
    world.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="hi"))
    world.leave(LeavePetition(leaver_token=alice.token))
    response = world.act(Act(
        actor_token=alice.token, type="poem.turn",
        payload={"acknowledgment": "x", "proposal": "y",
                 "invitation": "z", "holds_open": True}))
    assert isinstance(response, Refusal)
    assert "not admitted" in response.reason


def test_reenter_after_leave():
    """Re-entry is a new admission, not a re-open."""
    print("=== Re-enter after leave → new admission, act works ===")
    world = LeaveCapableWorld("world:a", "World A")
    alice = create_identity("Alice")
    world.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="hi"))
    world.leave(LeavePetition(leaver_token=alice.token))
    # Re-petition
    adm2 = world.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="back"))
    assert adm2 is not None
    # Act works
    ack = world.act(Act(
        actor_token=alice.token, type="poem.turn",
        payload={"acknowledgment": "(seed)",
                 "proposal": "new line",
                 "invitation": "next?",
                 "holds_open": True}))
    from multiverse_c3 import Ack
    assert isinstance(ack, Ack)


def test_leave_is_logged():
    print("=== Leave is logged with kind 'leave' ===")
    world = LeaveCapableWorld("world:a", "World A")
    alice = create_identity("Alice")
    world.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="hi"))
    world.leave(LeavePetition(leaver_token=alice.token))
    log = world.log_since(None)
    kinds = [e.kind for e in log]
    assert "admission" in kinds
    assert "leave" in kinds


# =====================================================================
# Signed leave
# =====================================================================

pytestmark_signed = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


@pytestmark_signed
def test_signed_leave_verifies():
    print("=== SignedLeave verifies against the world's public key ===")
    base = LeaveCapableWorld("world:a", "World A")
    kp = KeyPair.generate()
    signed = SignedLeaveWorld(base, kp)
    alice = create_identity("Alice")
    signed.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="hi"))
    result = signed.leave(LeavePetition(leaver_token=alice.token))
    assert isinstance(result, SignedLeave)
    # Verify
    from multiverse_c13 import verify_signature
    ok = verify_signature(kp.public_key_hex(),
                          result.canonical_payload(),
                          result.signature)
    assert ok


@pytestmark_signed
def test_signed_leave_wrong_key_fails():
    print("=== SignedLeave fails against the wrong key ===")
    base = LeaveCapableWorld("world:a", "World A")
    kp = KeyPair.generate()
    attacker = KeyPair.generate()
    signed = SignedLeaveWorld(base, kp)
    alice = create_identity("Alice")
    signed.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="hi"))
    result = signed.leave(LeavePetition(leaver_token=alice.token))
    assert isinstance(result, SignedLeave)
    from multiverse_c13 import verify_signature
    ok = verify_signature(attacker.public_key_hex(),
                          result.canonical_payload(),
                          result.signature)
    assert not ok


# =====================================================================
# Passport departures
# =====================================================================

def test_passport_records_departure():
    print("=== PassportV2WithDepartures records a signed departure ===")
    alice = create_identity("Alice")
    passport = PassportV2WithDepartures(base=PassportV2.new(alice))
    leave = SignedLeave(
        entity_id="world:a", timestamp="2024-01-01T00:00:00+00:00",
        subject_token=alice.token, signature="ab" * 64)
    passport = passport.with_departure(leave)
    assert len(passport.departures) == 1
    assert passport.departure_for("world:a") is not None
    assert passport.departure_for("world:b") is None


def test_passport_rejects_mismatched_subject():
    print("=== Passport rejects a departure for a different identity ===")
    alice = create_identity("Alice")
    bob = create_identity("Bob")
    passport = PassportV2WithDepartures(base=PassportV2.new(alice))
    bad_leave = SignedLeave(
        entity_id="world:a", timestamp="t",
        subject_token=bob.token, signature="ab" * 64)
    with pytest.raises(ValueError):
        passport.with_departure(bad_leave)


# =====================================================================
# Provenance: residency
# =====================================================================

def _stub_entry_prov(entity_id="world:a"):
    entry = PassportEntry(entity_id=entity_id, timestamp="t1")
    prov = EntryProvenance(entry=entry)
    prov.manifest_public_key = "aa" * 32  # placeholder, unused
    return prov


def test_provenance_resident_without_departure():
    print("=== Provenance: no departure → resident ===")
    alice = create_identity("Alice")
    passport = PassportV2WithDepartures(base=PassportV2.new(alice))
    prov = _stub_entry_prov()
    prov = enrich_with_departure(prov, passport)
    assert prov.residency == "resident"
    assert prov.departure is None


@pytestmark_signed
def test_provenance_departed_with_valid_signature():
    print("=== Provenance: departure with valid sig → departed ===")
    alice = create_identity("Alice")
    kp = KeyPair.generate()
    leave = SignedLeave(
        entity_id="world:a", timestamp="2024-01-01T00:00:00+00:00",
        subject_token=alice.token, signature="")
    from multiverse_c13 import canonical_bytes
    payload = canonical_bytes({
        "kind": "leave",
        "entity_id": leave.entity_id,
        "timestamp": leave.timestamp,
        "subject_token": leave.subject_token,
    })
    leave = SignedLeave(
        entity_id=leave.entity_id, timestamp=leave.timestamp,
        subject_token=leave.subject_token,
        signature=kp.sign(payload).hex())
    passport = PassportV2WithDepartures(
        base=PassportV2.new(alice)).with_departure(leave)
    prov = _stub_entry_prov()
    prov.manifest_public_key = kp.public_key_hex()
    prov = enrich_with_departure(prov, passport)
    assert prov.residency == "departed"
    assert prov.departure is not None
    assert prov.departure_signature_valid


@pytestmark_signed
def test_provenance_departed_but_signature_invalid():
    print("=== Provenance: departure present but sig invalid ===")
    alice = create_identity("Alice")
    real = KeyPair.generate()
    attacker = KeyPair.generate()
    from multiverse_c13 import canonical_bytes
    payload = canonical_bytes({
        "kind": "leave", "entity_id": "world:a",
        "timestamp": "t", "subject_token": alice.token,
    })
    forged = SignedLeave(
        entity_id="world:a", timestamp="t",
        subject_token=alice.token,
        signature=attacker.sign(payload).hex())
    passport = PassportV2WithDepartures(
        base=PassportV2.new(alice)).with_departure(forged)
    prov = _stub_entry_prov()
    prov.manifest_public_key = real.public_key_hex()
    prov = enrich_with_departure(prov, passport)
    assert prov.residency == "departed"
    assert not prov.departure_signature_valid


# =====================================================================
# End-to-end: Dickinson anchor
# =====================================================================

def test_dickinson_leaves_three_worlds():
    """Alice visits three worlds, leaves two, stays in one. Her
    passport records two departures and one residency. Everything
    verifiable offline. Public-domain anchor: Dickinson's
    'Because I could not stop for Death –'."""
    print("=== Dickinson demo: three worlds, two departures ===")
    worlds = {}
    for name in ("a", "b", "c"):
        base = LeaveCapableWorld(f"world:{name}", name.upper())
        worlds[name] = (base, KeyPair.generate())
    signed = {n: SignedLeaveWorld(b, kp)
              for n, (b, kp) in worlds.items()}

    alice = create_identity("Alice")
    passport = PassportV2WithDepartures(base=PassportV2.new(alice))

    # Admit to all three worlds
    for n in ("a", "b", "c"):
        resp = signed[n].petition(Petition(
            petitioner_token=alice.token,
            petitioner_name=alice.name,
            passport_admissions=(),
            message="Because I could not stop for Death –",
        ))
        assert isinstance(resp, SignedAdmission)
        passport = passport.with_admission(resp)

    # Leave worlds a and b, stay in c
    for n in ("a", "b"):
        leave = signed[n].leave(LeavePetition(
            leaver_token=alice.token))
        assert isinstance(leave, SignedLeave)
        passport = passport.with_departure(leave)

    # Check residency per world
    for n in ("a", "b"):
        prov = _stub_entry_prov(f"world:{n}")
        prov.manifest_public_key = worlds[n][1].public_key_hex()
        prov = enrich_with_departure(prov, passport)
        assert prov.residency == "departed"
        assert prov.departure_signature_valid

    prov_c = _stub_entry_prov("world:c")
    prov_c.manifest_public_key = worlds["c"][1].public_key_hex()
    prov_c = enrich_with_departure(prov_c, passport)
    assert prov_c.residency == "resident"
    assert prov_c.departure is None

    print("  world:a departed (signature verified)")
    print("  world:b departed (signature verified)")
    print("  world:c resident")


# =====================================================================
# HTTP shim supports leave (backward-compatible addition)
# =====================================================================

def test_http_shim_leave_roundtrip():
    """Leave works over HTTP via the shim — the protocol is
    language-agnostic and leave is part of it."""
    print("=== HTTP shim: leave roundtrip ===")
    world = LeaveCapableWorld("world:a", "World A")
    server = WorldProtocolServer(world, port=0)
    server.serve_in_thread()
    time.sleep(0.1)
    port = server._httpd.server_address[1]
    url = f"http://127.0.0.1:{port}"
    try:
        import json as _json
        import urllib.request as _ur
        def _post(path, body):
            req = _ur.Request(
                f"{url}{path}", data=_json.dumps(body).encode(),
                headers={"Content-Type": "application/json"},
                method="POST")
            with _ur.urlopen(req, timeout=5) as r:
                return _json.loads(r.read().decode())
        alice = create_identity("Alice")
        adm = _post("/petition", {
            "petitioner_token": alice.token,
            "petitioner_name": alice.name,
            "passport_admissions": [], "message": "hi"})
        assert adm["kind"] == "admission"
        result = _post("/leave", {"leaver_token": alice.token,
                                   "message": "bye"})
        assert result["kind"] == "leave"
        assert result["entity_id"] == "world:a"
    finally:
        server.stop()


if __name__ == "__main__":
    test_leave_requires_admission()
    test_leave_after_admission()
    test_leave_is_idempotent()
    test_act_after_leave_is_refused()
    test_reenter_after_leave()
    test_leave_is_logged()
    if HAS_CRYPTO:
        test_signed_leave_verifies()
        test_signed_leave_wrong_key_fails()
    test_passport_records_departure()
    test_passport_rejects_mismatched_subject()
    test_provenance_resident_without_departure()
    if HAS_CRYPTO:
        test_provenance_departed_with_valid_signature()
        test_provenance_departed_but_signature_invalid()
    test_dickinson_leaves_three_worlds()
    test_http_shim_leave_roundtrip()
