import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import Petition, Act, Ack, Refusal
from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c22 import LeavePetition, Leave
from multiverse_c36 import (
    create_person, PersonIdentity, bind_token,
)
from multiverse_c37 import (
    CoordinationClaim, CoSigner, CoordinationAttestation,
    SignerVerdict, AttestationVerdict,
    create_coordination_attestation,
    verify_coordination_attestation,
    PersonWorldLaw, PersonWorld,
    demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _make_world_with_two_persons():
    world = PersonWorld(PersonWorldLaw(
        entity_id="collaboratory:test",
        name="Test Collaboratory"))
    aria, aria_kp = create_person("Aria")
    bob, bob_kp = create_person("Bob")
    for person in (aria, bob):
        world.petition(Petition(
            petitioner_token=person.person.token,
            petitioner_name=person.person.name,
            passport_admissions=(),
            message="hi",
            extra={"public_key": person.person_public_key},
        ))
    return world, aria, aria_kp, bob, bob_kp


def _attestation(world, aria, aria_kp, bob, bob_kp):
    claim = CoordinationClaim(
        kind="test-claim", content={"test": True})
    return claim, create_coordination_attestation(
        claim, [(aria, aria_kp), (bob, bob_kp)])


# =====================================================================
# C3 modification: extra field on Petition
# =====================================================================

def test_petition_accepts_extra_field():
    print("=== Petition.extra is optional and accepted ===")
    p = Petition(
        petitioner_token="t", petitioner_name="T",
        passport_admissions=(), message="m",
        extra={"public_key": "aa" * 32},
    )
    assert p.extra == {"public_key": "aa" * 32}
    # Existing callers that don't pass extra still work
    p2 = Petition(
        petitioner_token="t", petitioner_name="T",
        passport_admissions=(), message="m",
    )
    assert p2.extra is None


# =====================================================================
# CoordinationClaim / CoSigner / CoordinationAttestation
# =====================================================================

def test_claim_validates_fields():
    print("=== CoordinationClaim validates its fields ===")
    with pytest.raises(ValueError):
        CoordinationClaim(kind="", content={})
    with pytest.raises(ValueError):
        CoordinationClaim(kind="x", content="not a dict")


def test_attestation_requires_two_signers():
    print("=== CoordinationAttestation requires >= 2 co-signers ===")
    claim = CoordinationClaim(kind="x", content={})
    cs = CoSigner("t", "aa" * 32, "sig")
    with pytest.raises(ValueError):
        CoordinationAttestation(
            claim=claim, co_signers=(cs,), timestamp="t")
    with pytest.raises(ValueError):
        CoordinationAttestation(
            claim=claim, co_signers=(cs, cs), timestamp="t")  # dup


# =====================================================================
# create_coordination_attestation
# =====================================================================

def test_create_attestation_happy():
    print("=== create_coordination_attestation: happy path ===")
    _, aria, aria_kp, bob, bob_kp = _make_world_with_two_persons()
    claim, att = _attestation(None, aria, aria_kp, bob, bob_kp)
    assert len(att.co_signers) == 2
    tokens = {cs.person_token for cs in att.co_signers}
    assert aria.person.token in tokens
    assert bob.person.token in tokens


def test_create_attestation_rejects_wrong_keypair():
    print("=== create rejects keypair != person_public_key ===")
    aria, _ = create_person("Aria")
    bob, bob_kp = create_person("Bob")
    wrong = KeyPair.generate()
    with pytest.raises(ValueError):
        create_coordination_attestation(
            CoordinationClaim(kind="x", content={}),
            [(aria, wrong), (bob, bob_kp)])


def test_create_attestation_rejects_duplicate_signer():
    print("=== create rejects duplicate signers ===")
    aria, aria_kp = create_person("Aria")
    with pytest.raises(ValueError):
        create_coordination_attestation(
            CoordinationClaim(kind="x", content={}),
            [(aria, aria_kp), (aria, aria_kp)])


# =====================================================================
# verify_coordination_attestation
# =====================================================================

def test_verify_attestation_happy():
    print("=== verify: both signatures valid ===")
    _, aria, aria_kp, bob, bob_kp = _make_world_with_two_persons()
    _, att = _attestation(None, aria, aria_kp, bob, bob_kp)
    v = verify_coordination_attestation(att)
    assert v.valid
    assert len(v.signer_verdicts) == 2
    assert all(sv.signature_valid for sv in v.signer_verdicts)


def test_verify_attestation_forged_signature():
    print("=== verify: one forged signature → invalid ===")
    _, aria, aria_kp, bob, bob_kp = _make_world_with_two_persons()
    _, att = _attestation(None, aria, aria_kp, bob, bob_kp)
    # Replace Aria's signature with one from a different key
    attacker = KeyPair.generate()
    payload = canonical_bytes({
        "kind": "coordination_attestation",
        "claim": att.claim.to_dict(),
        "timestamp": att.timestamp,
    })
    forged_signers = (
        CoSigner(aria.person.token, aria.person_public_key,
                 attacker.sign(payload).hex()),
        att.co_signers[1],
    )
    forged = CoordinationAttestation(
        claim=att.claim, co_signers=forged_signers,
        timestamp=att.timestamp)
    v = verify_coordination_attestation(forged)
    assert not v.valid
    # First sig invalid, second still valid
    assert not v.signer_verdicts[0].signature_valid
    assert v.signer_verdicts[1].signature_valid


def test_verify_attestation_tampered_claim():
    print("=== verify: tampered claim → invalid ===")
    _, aria, aria_kp, bob, bob_kp = _make_world_with_two_persons()
    _, att = _attestation(None, aria, aria_kp, bob, bob_kp)
    tampered_claim = CoordinationClaim(
        kind=att.claim.kind, content={"test": False})  # changed
    tampered = CoordinationAttestation(
        claim=tampered_claim, co_signers=att.co_signers,
        timestamp=att.timestamp)
    v = verify_coordination_attestation(tampered)
    assert not v.valid


# =====================================================================
# PersonWorld — petition
# =====================================================================

def test_petition_requires_public_key():
    print("=== petition: missing public_key → Refusal ===")
    world = PersonWorld()
    r = world.petition(Petition(
        petitioner_token="t", petitioner_name="T",
        passport_admissions=(), message="hi",
        # no extra
    ))
    assert isinstance(r, Refusal)
    assert "public_key" in r.reason


def test_petition_with_public_key():
    print("=== petition: with public_key → Admission ===")
    world = PersonWorld()
    r = world.petition(Petition(
        petitioner_token="t", petitioner_name="T",
        passport_admissions=(), message="hi",
        extra={"public_key": "aa" * 32},
    ))
    from multiverse_c3 import Admission
    assert isinstance(r, Admission)


# =====================================================================
# PersonWorld — act
# =====================================================================

def test_act_requires_admission():
    print("=== act: unadmitted actor → Refusal ===")
    world = PersonWorld()
    r = world.act(Act(
        actor_token="nobody", type="coordination.attest",
        payload={}))
    assert isinstance(r, Refusal)
    assert "not admitted" in r.reason


def test_act_requires_coordination_type():
    print("=== act: wrong type → Refusal ===")
    world, aria, _, _, _ = _make_world_with_two_persons()
    r = world.act(Act(
        actor_token=aria.person.token, type="poem.turn",
        payload={}))
    assert isinstance(r, Refusal)
    assert "Unknown act type" in r.reason


def test_act_happy():
    print("=== act: valid attestation recorded ===")
    world, aria, aria_kp, bob, bob_kp = _make_world_with_two_persons()
    claim, att = _attestation(None, aria, aria_kp, bob, bob_kp)
    r = world.act(Act(
        actor_token=aria.person.token,
        type="coordination.attest",
        payload={
            "claim": claim.to_dict(),
            "co_signers": [cs.to_dict() for cs in att.co_signers],
        },
    ))
    assert isinstance(r, Ack)
    assert len(world.attestations()) == 1


def test_act_rejects_actor_not_in_co_signers():
    print("=== act: actor not among co-signers → Refusal ===")
    world, aria, aria_kp, bob, bob_kp = _make_world_with_two_persons()
    # Create an attestation signed by aria + bob, but bob submits it
    claim, att = _attestation(None, aria, aria_kp, bob, bob_kp)
    # Submit as a THIRD admitted person (Carol)
    carol, carol_kp = create_person("Carol")
    world.petition(Petition(
        petitioner_token=carol.person.token,
        petitioner_name=carol.person.name,
        passport_admissions=(), message="hi",
        extra={"public_key": carol.person_public_key}))
    r = world.act(Act(
        actor_token=carol.person.token,
        type="coordination.attest",
        payload={
            "claim": claim.to_dict(),
            "co_signers": [cs.to_dict() for cs in att.co_signers],
        },
    ))
    assert isinstance(r, Refusal)
    assert "must be among the co-signers" in r.reason


def test_act_rejects_unadmitted_co_signer():
    print("=== act: co-signer not admitted → Refusal ===")
    world, aria, aria_kp, _, _ = _make_world_with_two_persons()
    # Carol signs, but is not admitted to this world
    carol, carol_kp = create_person("Carol")
    claim, att = _attestation(None, aria, aria_kp, carol, carol_kp)
    r = world.act(Act(
        actor_token=aria.person.token,
        type="coordination.attest",
        payload={
            "claim": claim.to_dict(),
            "co_signers": [cs.to_dict() for cs in att.co_signers],
        },
    ))
    assert isinstance(r, Refusal)
    assert "not admitted" in r.reason


def test_act_rejects_forged_co_signature():
    print("=== act: forged co-signature → Refusal ===")
    world, aria, aria_kp, bob, bob_kp = _make_world_with_two_persons()
    claim, att = _attestation(None, aria, aria_kp, bob, bob_kp)
    # Replace Bob's sig with a signature from a different key,
    # but keep Bob's declared public key. The World checks the
    # signature against the ADMITTED key (Bob's real one), so
    # the forged sig won't verify.
    attacker = KeyPair.generate()
    payload = canonical_bytes({
        "kind": "coordination_attestation",
        "claim": claim.to_dict(),
        "timestamp": att.timestamp,
    })
    forged_signers = (
        att.co_signers[0],
        CoSigner(bob.person.token, bob.person_public_key,
                 attacker.sign(payload).hex()),
    )
    r = world.act(Act(
        actor_token=aria.person.token,
        type="coordination.attest",
        payload={
            "claim": claim.to_dict(),
            "co_signers": [
                cs.to_dict() for cs in forged_signers],
        },
    ))
    assert isinstance(r, Refusal)
    assert "invalid" in r.reason.lower()


def test_act_rejects_key_mismatch():
    print("=== act: co-signer key != admitted key → Refusal ===")
    world, aria, aria_kp, bob, bob_kp = _make_world_with_two_persons()
    claim, att = _attestation(None, aria, aria_kp, bob, bob_kp)
    # Replace Bob's declared public key with a different one
    wrong_pk = KeyPair.generate().public_key_hex()
    tampered_signers = (
        att.co_signers[0],
        CoSigner(bob.person.token, wrong_pk,
                 att.co_signers[1].signature),
    )
    r = world.act(Act(
        actor_token=aria.person.token,
        type="coordination.attest",
        payload={
            "claim": claim.to_dict(),
            "co_signers": [
                cs.to_dict() for cs in tampered_signers],
        },
    ))
    assert isinstance(r, Refusal)
    assert "mismatch" in r.reason.lower()


# =====================================================================
# Leave
# =====================================================================

def test_leave_cannot_be_refused_when_admitted():
    print("=== leave: admitted person can leave ===")
    world, aria, _, _, _ = _make_world_with_two_persons()
    r = world.leave(LeavePetition(leaver_token=aria.person.token))
    assert isinstance(r, Leave)


def test_leave_requires_admission():
    print("=== leave: never-admitted → Refusal ===")
    world = PersonWorld()
    r = world.leave(LeavePetition(leaver_token="nobody"))
    assert isinstance(r, Refusal)
    assert r.reason == "not admitted"


# =====================================================================
# Conformance
# =====================================================================

def test_personworld_conforms_to_wcp():
    print("=== PersonWorld passes WCP/0.1 conformance ===")
    from wcp_conformance import run_conformance
    world = PersonWorld()
    result = run_conformance(world)
    assert result["passed"], result["failures"]


# =====================================================================
# JSON roundtrips
# =====================================================================

def test_attestation_json_roundtrip():
    print("=== CoordinationAttestation JSON roundtrip ===")
    _, aria, aria_kp, bob, bob_kp = _make_world_with_two_persons()
    _, att = _attestation(None, aria, aria_kp, bob, bob_kp)
    wire = json.dumps(att.to_dict())
    revived = CoordinationAttestation.from_dict(json.loads(wire))
    assert revived.canonical_payload() == att.canonical_payload()
    v = verify_coordination_attestation(revived)
    assert v.valid


# =====================================================================
# Never raises
# =====================================================================

def test_verifier_never_raises():
    print("=== verify_coordination_attestation never raises ===")
    assert not verify_coordination_attestation(None).valid
    assert not verify_coordination_attestation("not an att").valid
    assert not verify_coordination_attestation({}).valid


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: Aria and Bob co-attest in PersonWorld ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["attestations_recorded"] == 1
    assert audit["verification_valid"] is True
    assert audit["forged_attestation_valid"] is False
    assert (tmp_path / "person_world_demo.json").exists()


if __name__ == "__main__":
    test_petition_accepts_extra_field()
    test_claim_validates_fields()
    test_attestation_requires_two_signers()
    test_create_attestation_happy()
    test_create_attestation_rejects_wrong_keypair()
    test_create_attestation_rejects_duplicate_signer()
    test_verify_attestation_happy()
    test_verify_attestation_forged_signature()
    test_verify_attestation_tampered_claim()
    test_petition_requires_public_key()
    test_petition_with_public_key()
    test_act_requires_admission()
    test_act_requires_coordination_type()
    test_act_happy()
    test_act_rejects_actor_not_in_co_signers()
    test_act_rejects_unadmitted_co_signer()
    test_act_rejects_forged_co_signature()
    test_act_rejects_key_mismatch()
    test_leave_cannot_be_refused_when_admitted()
    test_leave_requires_admission()
    test_personworld_conforms_to_wcp()
    test_attestation_json_roundtrip()
    test_verifier_never_raises()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
