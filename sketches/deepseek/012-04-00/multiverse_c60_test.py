import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import Act, Ack, Refusal, Petition
from multiverse_c4 import PoetryWorld
from multiverse_c5 import ChemistryWorld
from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c48 import (
    FederationAttestation, AttestationVerdict,
    DEFAULT_VERIFIER_REGISTRY,
)
from multiverse_c54 import AttestedRumor
from multiverse_c55 import WorldCurator
from multiverse_c56 import (
    SigningVerifyingUnit, SignedRelayNetwork,
    verify_signed_relay_chain,
)
from multiverse_c57 import (
    ContractTerms, ContractRegistry,
    sign_offer, sign_acceptance,
    sign_bilateral_revocation,
    EstablishedContract, BilateralRevocation,
    verify_established_contract,
    verify_bilateral_revocation,
)
from multiverse_c58 import ContractAwarePoetryWorld
from multiverse_c60 import (
    RevocationAnnouncement,
    sign_revocation_announcement,
    verify_revocation_announcement,
    RevocationAnnouncementVerdict,
    revocation_announcement_to_attestation_signed,
    revocation_announcement_to_registry,
    C60_VERIFIER_REGISTRY,
    verify_revocation_announcement_attestation,
    RevocationPublisher,
    demo,
    _now,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _make_contract_and_revocation():
    a = PoetryWorld("world:a", "A")
    b = ChemistryWorld("world:b", "B")
    kp_a = KeyPair.generate()
    kp_b = KeyPair.generate()
    terms = ContractTerms(content={"kind": "test"})
    offer = sign_offer("world:a", kp_a, "world:b", terms)
    acceptance = sign_acceptance("world:b", kp_b, offer)
    contract = EstablishedContract(
        offer=offer, acceptance=acceptance,
        established_at=_now())
    rev = sign_bilateral_revocation(
        contract_id=terms.terms_hash(),
        world_a_id="world:a", world_a_kp=kp_a,
        world_b_id="world:b", world_b_kp=kp_b,
        reason="test revocation")
    return {
        "a": a, "b": b, "kp_a": kp_a, "kp_b": kp_b,
        "terms": terms, "offer": offer,
        "acceptance": acceptance, "contract": contract,
        "revocation": rev,
    }


# =====================================================================
# Kind extension
# =====================================================================

def test_kind_extension():
    print("=== C60 extends C48's witnessed kinds ===")
    import multiverse_c48 as c48
    assert "contract_revocation" in c48.WITNESSED_KINDS
    assert "contract_revocation" in c48.ALL_KINDS


def test_verifier_registry_has_kind():
    print("=== C60 registry knows the kind ===")
    assert "contract_revocation" in C60_VERIFIER_REGISTRY


def test_c48_kinds_still_disjoint():
    print("=== C48 kinds: still disjoint after C60 extension ===")
    import multiverse_c48 as c48
    assert c48.DIRECT_KINDS & c48.WITNESSED_KINDS == set()


# =====================================================================
# Signing
# =====================================================================

def test_sign_happy():
    print("=== sign_revocation_announcement: happy path ===")
    parts = _make_contract_and_revocation()
    ann = sign_revocation_announcement(
        parts["revocation"], parts["kp_a"])
    assert ann.announcer_world_id == "world:a"
    assert ann.contract_id == parts["terms"].terms_hash()


def test_sign_from_either_party():
    print("=== sign: either party can announce ===")
    parts = _make_contract_and_revocation()
    ann_a = sign_revocation_announcement(
        parts["revocation"], parts["kp_a"])
    ann_b = sign_revocation_announcement(
        parts["revocation"], parts["kp_b"])
    assert ann_a.announcer_world_id == "world:a"
    assert ann_b.announcer_world_id == "world:b"


def test_sign_from_stranger_refused():
    print("=== sign: stranger cannot announce ===")
    parts = _make_contract_and_revocation()
    stranger_kp = KeyPair.generate()
    with pytest.raises(ValueError):
        sign_revocation_announcement(
            parts["revocation"], stranger_kp)


def test_announcement_validates_fields():
    print("=== RevocationAnnouncement: validates fields ===")
    with pytest.raises(ValueError):
        RevocationAnnouncement(
            announcer_world_id="",
            announcer_public_key="aa" * 32,
            contract_id="bb" * 32,
            world_a_id="a", world_b_id="b",
            revocation={},
            revoked_at="t", timestamp="t",
            signature="s")
    with pytest.raises(ValueError):
        RevocationAnnouncement(
            announcer_world_id="w",
            announcer_public_key="short",
            contract_id="bb" * 32,
            world_a_id="a", world_b_id="b",
            revocation={},
            revoked_at="t", timestamp="t",
            signature="s")
    with pytest.raises(ValueError):
        RevocationAnnouncement(
            announcer_world_id="w",
            announcer_public_key="aa" * 32,
            contract_id="bb" * 32,
            world_a_id="same", world_b_id="same",
            revocation={},
            revoked_at="t", timestamp="t",
            signature="s")


# =====================================================================
# Verification
# =====================================================================

def test_verify_happy():
    print("=== verify_revocation_announcement: happy ===")
    parts = _make_contract_and_revocation()
    ann = sign_revocation_announcement(
        parts["revocation"], parts["kp_a"])
    v = verify_revocation_announcement(ann)
    assert v.valid
    assert v.signature_valid
    assert v.announcer_is_party
    assert v.revocation_valid
    assert v.contract_id_matches


def test_verify_wrong_key():
    print("=== verify: wrong key → False ===")
    parts = _make_contract_and_revocation()
    ann = sign_revocation_announcement(
        parts["revocation"], parts["kp_a"])
    wrong = KeyPair.generate()
    v = verify_revocation_announcement(
        ann, wrong.public_key_hex())
    assert not v.valid
    assert not v.signature_valid


def test_verify_tampered_revocation():
    print("=== verify: tampered revocation → False ===")
    parts = _make_contract_and_revocation()
    ann = sign_revocation_announcement(
        parts["revocation"], parts["kp_a"])
    tampered_rev = dict(ann.revocation)
    tampered_rev["reason"] = "TAMPERED"
    tampered = RevocationAnnouncement(
        announcer_world_id=ann.announcer_world_id,
        announcer_public_key=ann.announcer_public_key,
        contract_id=ann.contract_id,
        world_a_id=ann.world_a_id,
        world_b_id=ann.world_b_id,
        revocation=tampered_rev,
        revoked_at=ann.revoked_at,
        timestamp=ann.timestamp,
        signature=ann.signature)
    v = verify_revocation_announcement(tampered)
    assert not v.valid
    assert not v.signature_valid


def test_verify_tampered_signature():
    print("=== verify: tampered signature → False ===")
    parts = _make_contract_and_revocation()
    ann = sign_revocation_announcement(
        parts["revocation"], parts["kp_a"])
    attacker = KeyPair.generate()
    tampered = RevocationAnnouncement(
        announcer_world_id=ann.announcer_world_id,
        announcer_public_key=ann.announcer_public_key,
        contract_id=ann.contract_id,
        world_a_id=ann.world_a_id,
        world_b_id=ann.world_b_id,
        revocation=ann.revocation,
        revoked_at=ann.revoked_at,
        timestamp=ann.timestamp,
        signature=attacker.sign(
            ann.canonical_payload()).hex())
    v = verify_revocation_announcement(tampered)
    assert not v.valid
    assert not v.signature_valid


def test_verify_announcer_not_party():
    print("=== verify: announcer not a party ===")
    parts = _make_contract_and_revocation()
    ann = sign_revocation_announcement(
        parts["revocation"], parts["kp_a"])
    stranger_kp = KeyPair.generate()
    tampered = RevocationAnnouncement(
        announcer_world_id=ann.announcer_world_id,
        announcer_public_key=stranger_kp.public_key_hex(),
        contract_id=ann.contract_id,
        world_a_id=ann.world_a_id,
        world_b_id=ann.world_b_id,
        revocation=ann.revocation,
        revoked_at=ann.revoked_at,
        timestamp=ann.timestamp,
        signature=ann.signature)
    v = verify_revocation_announcement(tampered)
    assert not v.valid


def test_verify_one_sided_revocation():
    print("=== verify: one-sided revocation embedded → False ===")
    parts = _make_contract_and_revocation()
    ann = sign_revocation_announcement(
        parts["revocation"], parts["kp_a"])
    # Tamper the embedded revocation's b-signature
    attacker = KeyPair.generate()
    tampered_rev = dict(ann.revocation)
    tampered_rev["signature_b"] = attacker.sign(
        canonical_bytes({
            "kind": "bilateral_revocation",
            "contract_id": tampered_rev["contract_id"],
            "world_a_id": tampered_rev["world_a_id"],
            "world_a_public_key":
                tampered_rev["world_a_public_key"],
            "world_b_id": tampered_rev["world_b_id"],
            "world_b_public_key":
                tampered_rev["world_b_public_key"],
            "reason": tampered_rev.get("reason", ""),
            "timestamp": tampered_rev["timestamp"],
        })).hex()
    tampered = RevocationAnnouncement(
        announcer_world_id=ann.announcer_world_id,
        announcer_public_key=ann.announcer_public_key,
        contract_id=ann.contract_id,
        world_a_id=ann.world_a_id,
        world_b_id=ann.world_b_id,
        revocation=tampered_rev,
        revoked_at=ann.revoked_at,
        timestamp=ann.timestamp,
        signature=ann.signature)
    v = verify_revocation_announcement(tampered)
    assert not v.valid
    # Signature might be broken by tampering, or the revocation
    # check might fail — either way, invalid
    assert not v.valid


# =====================================================================
# JSON roundtrip
# =====================================================================

def test_json_roundtrip():
    print("=== RevocationAnnouncement: JSON roundtrip ===")
    parts = _make_contract_and_revocation()
    ann = sign_revocation_announcement(
        parts["revocation"], parts["kp_a"])
    wire = json.dumps(ann.to_dict())
    revived = RevocationAnnouncement.from_dict(
        json.loads(wire))
    v = verify_revocation_announcement(revived)
    assert v.valid


# =====================================================================
# Wrap and dispatch
# =====================================================================

def test_wrap_happy():
    print("=== wrap as FederationAttestation: happy ===")
    parts = _make_contract_and_revocation()
    ann = sign_revocation_announcement(
        parts["revocation"], parts["kp_a"])
    att = revocation_announcement_to_attestation_signed(
        ann, parts["kp_a"])
    assert att.source_kind == "contract_revocation"
    assert att.is_witnessed
    v = verify_revocation_announcement_attestation(att)
    assert v.valid


def test_wrap_wrong_keypair():
    print("=== wrap: wrong keypair → ValueError ===")
    parts = _make_contract_and_revocation()
    ann = sign_revocation_announcement(
        parts["revocation"], parts["kp_a"])
    with pytest.raises(ValueError):
        revocation_announcement_to_attestation_signed(
            ann, parts["kp_b"])


# =====================================================================
# Registry population
# =====================================================================

def test_registry_population_from_announcement():
    print("=== revocation_announcement_to_registry: populates ===")
    parts = _make_contract_and_revocation()
    ann = sign_revocation_announcement(
        parts["revocation"], parts["kp_a"])
    reg = ContractRegistry()
    revocation_announcement_to_registry(ann, reg)
    rec = reg.get(parts["terms"].terms_hash())
    assert rec is not None
    assert rec.is_revoked()
    assert not rec.is_active(parts["terms"].terms_hash()) \
        if hasattr(rec, "is_active") else True


def test_registry_population_rejects_invalid():
    print("=== revocation_announcement_to_registry: invalid → "
          "ValueError ===")
    parts = _make_contract_and_revocation()
    ann = sign_revocation_announcement(
        parts["revocation"], parts["kp_a"])
    tampered = RevocationAnnouncement(
        announcer_world_id=ann.announcer_world_id,
        announcer_public_key=ann.announcer_public_key,
        contract_id=ann.contract_id,
        world_a_id=ann.world_a_id,
        world_b_id=ann.world_b_id,
        revocation=ann.revocation,
        revoked_at=ann.revoked_at,
        timestamp=ann.timestamp,
        signature="00" * 64)
    reg = ContractRegistry()
    with pytest.raises(ValueError):
        revocation_announcement_to_registry(tampered, reg)


def test_registry_populates_after_establishment():
    print("=== registry: establishment then revocation ===")
    parts = _make_contract_and_revocation()
    # First: populate with offer + acceptance (establishment)
    reg = ContractRegistry()
    reg.register_offer(parts["offer"])
    reg.register_acceptance(parts["acceptance"])
    rec = reg.get(parts["terms"].terms_hash())
    assert rec.is_established()
    # Then: populate with revocation (via C60)
    ann = sign_revocation_announcement(
        parts["revocation"], parts["kp_a"])
    revocation_announcement_to_registry(ann, reg)
    rec = reg.get(parts["terms"].terms_hash())
    assert rec.is_revoked()
    assert not rec.is_established()


# =====================================================================
# Publisher
# =====================================================================

def test_publisher_announce():
    print("=== RevocationPublisher: announces ===")
    parts = _make_contract_and_revocation()
    curator = WorldCurator(parts["a"], parts["kp_a"])
    pub = RevocationPublisher(curator)
    ann = pub.announce_revocation(parts["revocation"])
    assert verify_revocation_announcement(ann).valid


def test_publisher_wrap():
    print("=== RevocationPublisher: wraps ===")
    parts = _make_contract_and_revocation()
    curator = WorldCurator(parts["a"], parts["kp_a"])
    pub = RevocationPublisher(curator)
    ann = pub.announce_revocation(parts["revocation"])
    att = pub.wrap_as_attestation(ann)
    assert att.source_kind == "contract_revocation"
    assert verify_revocation_announcement_attestation(att).valid


# =====================================================================
# C56 propagation
# =====================================================================

def test_propagation_via_c56_relay():
    print("=== Propagation: revocation announcement via C56 ===")
    parts = _make_contract_and_revocation()
    ann = sign_revocation_announcement(
        parts["revocation"], parts["kp_a"])
    att = revocation_announcement_to_attestation_signed(
        ann, parts["kp_a"])

    net = SignedRelayNetwork()
    kp_A = KeyPair.generate()
    kp_C = KeyPair.generate()
    net.add_unit("A", SigningVerifyingUnit(
        entity_id="world:relay-A", name="A",
        unit_kp=kp_A, contacts=["C"]))
    net.add_unit("C", SigningVerifyingUnit(
        entity_id="world:relay-C", name="C",
        unit_kp=kp_C, contacts=["A"]))
    attested = AttestedRumor.from_attestation(att)
    net.seed_attested("A", attested)
    net.run_until_quiet()
    chain = net.collect_relay_chain(attested.rumor_id)
    assert chain is not None
    keys = {
        "world:relay-A": kp_A.public_key_hex(),
        "world:relay-C": kp_C.public_key_hex(),
    }
    v = verify_signed_relay_chain(
        chain, relay_public_keys=keys,
        receipt_public_keys=keys)
    assert v.valid


# =====================================================================
# C58 integration: citation refused after revocation
# =====================================================================

def test_c58_refuses_after_learned_revocation():
    print("=== C58: refuses after revocation is learned ===")
    parts = _make_contract_and_revocation()
    reg = ContractRegistry()
    # Establish first
    reg.register_offer(parts["offer"])
    reg.register_acceptance(parts["acceptance"])
    # Build a C58 world with this registry
    world = ContractAwarePoetryWorld(
        "world:c", "C", registry=reg)
    ident = create_identity("Resident")
    world.petition(Petition(
        petitioner_token=ident.token,
        petitioner_name=ident.name,
        passport_admissions=(),
        message="hi"))
    # Before revocation, citation works
    r1 = world.act(Act(
        actor_token=ident.token, type="poem.turn",
        payload={
            "acknowledgment": "(seed)",
            "proposal": "a line",
            "invitation": "?",
            "holds_open": True,
            "cites_contract": parts["terms"].terms_hash(),
            "cites_world": "world:b",
        }))
    assert isinstance(r1, Ack)
    # Revocation announced (C60)
    ann = sign_revocation_announcement(
        parts["revocation"], parts["kp_a"])
    revocation_announcement_to_registry(ann, reg)
    # After revocation, citation refused
    r2 = world.act(Act(
        actor_token=ident.token, type="poem.turn",
        payload={
            "acknowledgment": "(seed)",
            "proposal": "a line",
            "invitation": "?",
            "holds_open": True,
            "cites_contract": parts["terms"].terms_hash(),
            "cites_world": "world:b",
        }))
    assert isinstance(r2, Refusal)
    assert "revoked" in r2.reason


# =====================================================================
# Never raises
# =====================================================================

def test_verifiers_never_raise():
    print("=== Verifiers: never raise ===")
    assert not verify_revocation_announcement(None).valid
    assert not verify_revocation_announcement(
        "not an announcement").valid
    assert not verify_revocation_announcement_attestation(
        None).valid


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: full lifecycle ===")
    audit = demo(artifact_dir=str(tmp_path))
    s = audit["scenarios"]
    assert s["A_establishment"]["announcement_valid"] is True
    assert s["A_establishment"]["c_learned"] is True
    assert s["A_establishment"]["c_can_cite_before"] is True
    assert s["B_revocation"]["announcement_valid"] is True
    assert s["B_revocation"]["wrapped_valid"] is True
    assert s["C_c_learns_revocation"]["c_learns"] is True
    assert s["C_c_learns_revocation"]["c_refuses_after"] is True
    assert "revoked" in \
        s["C_c_learns_revocation"]["refusal_reason"]
    assert s["D_tampered"]["valid"] is False
    assert s["E_stranger"]["refused"] is True
    assert (tmp_path / "revocation_propagation_demo.json"
            ).exists()


if __name__ == "__main__":
    test_kind_extension()
    test_verifier_registry_has_kind()
    test_c48_kinds_still_disjoint()
    test_sign_happy()
    test_sign_from_either_party()
    test_sign_from_stranger_refused()
    test_announcement_validates_fields()
    test_verify_happy()
    test_verify_wrong_key()
    test_verify_tampered_revocation()
    test_verify_tampered_signature()
    test_verify_announcer_not_party()
    test_verify_one_sided_revocation()
    test_json_roundtrip()
    test_wrap_happy()
    test_wrap_wrong_keypair()
    test_registry_population_from_announcement()
    test_registry_population_rejects_invalid()
    test_registry_populates_after_establishment()
    test_publisher_announce()
    test_publisher_wrap()
    test_propagation_via_c56_relay()
    test_c58_refuses_after_learned_revocation()
    test_verifiers_never_raise()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
