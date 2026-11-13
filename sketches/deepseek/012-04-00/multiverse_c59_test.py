import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import Act, Ack, Refusal, Petition
from multiverse_c4 import PoetryWorld
from multiverse_c5 import ChemistryWorld
from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c54 import AttestedRumor
from multiverse_c55 import WorldCurator
from multiverse_c56 import (
    SigningVerifyingUnit, SignedRelayNetwork,
    verify_signed_relay_chain,
)
from multiverse_c57 import (
    ContractTerms, ContractRegistry, ContractOffer,
    ContractAcceptance, EstablishedContract,
    sign_offer, sign_acceptance,
    verify_established_contract,
)
from multiverse_c58 import ContractAwarePoetryWorld
from multiverse_c59 import (
    ContractAnnouncement,
    sign_announcement, verify_announcement,
    AnnouncementVerdict,
    announcement_to_attestation_signed,
    announcement_to_registry,
    C59_VERIFIER_REGISTRY,
    verify_announcement_attestation,
    AnnouncementPublisher,
    demo,
    _now,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _make_contract():
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
    return {
        "a": a, "b": b, "kp_a": kp_a, "kp_b": kp_b,
        "terms": terms, "offer": offer,
        "acceptance": acceptance, "contract": contract,
    }


# =====================================================================
# Kinds extension
# =====================================================================

def test_kind_extension():
    print("=== C59 extends C48's witnessed kinds ===")
    import multiverse_c48 as c48
    assert "contract_announcement" in c48.WITNESSED_KINDS
    assert "contract_announcement" in c48.ALL_KINDS


def test_verifier_registry_has_kind():
    print("=== C59 registry knows the kind ===")
    assert "contract_announcement" in C59_VERIFIER_REGISTRY


# =====================================================================
# Signing
# =====================================================================

def test_sign_announcement_happy():
    print("=== sign_announcement: happy path ===")
    parts = _make_contract()
    ann = sign_announcement(parts["contract"], parts["kp_a"])
    assert ann.announcer_world_id == "world:a"
    assert ann.announcer_public_key == \
        parts["kp_a"].public_key_hex()
    assert ann.terms_hash == parts["terms"].terms_hash()


def test_sign_from_acceptor_also_works():
    print("=== sign_announcement: acceptor can announce too ===")
    parts = _make_contract()
    ann = sign_announcement(parts["contract"], parts["kp_b"])
    assert ann.announcer_world_id == "world:b"


def test_sign_from_stranger_refused():
    print("=== sign_announcement: stranger cannot announce ===")
    parts = _make_contract()
    stranger_kp = KeyPair.generate()
    with pytest.raises(ValueError):
        sign_announcement(parts["contract"], stranger_kp)


def test_announcement_validates_fields():
    print("=== ContractAnnouncement: validates fields ===")
    with pytest.raises(ValueError):
        ContractAnnouncement(
            announcer_world_id="",
            announcer_public_key="aa" * 32,
            world_a_id="a", world_b_id="b",
            terms_hash="bb" * 32,
            offer={}, acceptance={},
            established_at="t", timestamp="t",
            signature="s")
    with pytest.raises(ValueError):
        ContractAnnouncement(
            announcer_world_id="w",
            announcer_public_key="short",
            world_a_id="a", world_b_id="b",
            terms_hash="bb" * 32,
            offer={}, acceptance={},
            established_at="t", timestamp="t",
            signature="s")
    with pytest.raises(ValueError):
        ContractAnnouncement(
            announcer_world_id="w",
            announcer_public_key="aa" * 32,
            world_a_id="same", world_b_id="same",
            terms_hash="bb" * 32,
            offer={}, acceptance={},
            established_at="t", timestamp="t",
            signature="s")


# =====================================================================
# Verification
# =====================================================================

def test_verify_announcement_happy():
    print("=== verify_announcement: happy path ===")
    parts = _make_contract()
    ann = sign_announcement(parts["contract"], parts["kp_a"])
    v = verify_announcement(ann)
    assert v.valid
    assert v.signature_valid
    assert v.announcer_is_party
    assert v.contract_valid
    assert v.terms_hash_matches


def test_verify_announcement_wrong_key():
    print("=== verify_announcement: wrong key → False ===")
    parts = _make_contract()
    ann = sign_announcement(parts["contract"], parts["kp_a"])
    wrong = KeyPair.generate()
    v = verify_announcement(ann, wrong.public_key_hex())
    assert not v.valid
    assert not v.signature_valid


def test_verify_announcement_tampered_offer():
    print("=== verify_announcement: tampered offer → False ===")
    parts = _make_contract()
    ann = sign_announcement(parts["contract"], parts["kp_a"])
    # Tamper with the offer
    tampered_offer = dict(ann.offer)
    tampered_terms = dict(tampered_offer["terms"])
    tampered_terms["kind"] = "TAMPERED"
    tampered_offer["terms"] = tampered_terms
    tampered_ann = ContractAnnouncement(
        announcer_world_id=ann.announcer_world_id,
        announcer_public_key=ann.announcer_public_key,
        world_a_id=ann.world_a_id,
        world_b_id=ann.world_b_id,
        terms_hash=ann.terms_hash,
        offer=tampered_offer,
        acceptance=ann.acceptance,
        established_at=ann.established_at,
        timestamp=ann.timestamp,
        signature=ann.signature)
    v = verify_announcement(tampered_ann)
    assert not v.valid
    assert not v.signature_valid  # sig was over untampered content


def test_verify_announcement_tampered_signature():
    print("=== verify_announcement: tampered signature → False ===")
    parts = _make_contract()
    ann = sign_announcement(parts["contract"], parts["kp_a"])
    attacker = KeyPair.generate()
    tampered = ContractAnnouncement(
        announcer_world_id=ann.announcer_world_id,
        announcer_public_key=ann.announcer_public_key,
        world_a_id=ann.world_a_id,
        world_b_id=ann.world_b_id,
        terms_hash=ann.terms_hash,
        offer=ann.offer,
        acceptance=ann.acceptance,
        established_at=ann.established_at,
        timestamp=ann.timestamp,
        signature=attacker.sign(
            ann.canonical_payload()).hex())
    v = verify_announcement(tampered)
    assert not v.valid
    assert not v.signature_valid


def test_verify_announcement_announcer_not_party():
    print("=== verify_announcement: announcer not a party → False ===")
    parts = _make_contract()
    ann = sign_announcement(parts["contract"], parts["kp_a"])
    # Replace announcer_public_key with a stranger's
    stranger_kp = KeyPair.generate()
    tampered = ContractAnnouncement(
        announcer_world_id=ann.announcer_world_id,
        announcer_public_key=stranger_kp.public_key_hex(),
        world_a_id=ann.world_a_id,
        world_b_id=ann.world_b_id,
        terms_hash=ann.terms_hash,
        offer=ann.offer,
        acceptance=ann.acceptance,
        established_at=ann.established_at,
        timestamp=ann.timestamp,
        signature=ann.signature)
    v = verify_announcement(tampered)
    assert not v.valid
    # Signature won't verify with the wrong declared key
    assert not v.signature_valid


def test_verify_announcement_malformed_offer():
    print("=== verify_announcement: malformed offer → False ===")
    parts = _make_contract()
    ann = sign_announcement(parts["contract"], parts["kp_a"])
    tampered = ContractAnnouncement(
        announcer_world_id=ann.announcer_world_id,
        announcer_public_key=ann.announcer_public_key,
        world_a_id=ann.world_a_id,
        world_b_id=ann.world_b_id,
        terms_hash=ann.terms_hash,
        offer={"garbage": True},  # not a valid offer
        acceptance=ann.acceptance,
        established_at=ann.established_at,
        timestamp=ann.timestamp,
        signature=ann.signature)
    v = verify_announcement(tampered)
    assert not v.valid


# =====================================================================
# Announcement JSON
# =====================================================================

def test_announcement_json_roundtrip():
    print("=== ContractAnnouncement: JSON roundtrip ===")
    parts = _make_contract()
    ann = sign_announcement(parts["contract"], parts["kp_a"])
    wire = json.dumps(ann.to_dict())
    revived = ContractAnnouncement.from_dict(json.loads(wire))
    v = verify_announcement(revived)
    assert v.valid


# =====================================================================
# Wrap as FederationAttestation
# =====================================================================

def test_wrap_as_attestation_happy():
    print("=== wrap as FederationAttestation: happy path ===")
    parts = _make_contract()
    ann = sign_announcement(parts["contract"], parts["kp_a"])
    att = announcement_to_attestation_signed(ann, parts["kp_a"])
    assert att.source_kind == "contract_announcement"
    assert att.is_witnessed
    v = verify_announcement_attestation(att)
    assert v.valid


def test_wrap_wrong_keypair_refused():
    print("=== wrap: wrong keypair → ValueError ===")
    parts = _make_contract()
    ann = sign_announcement(parts["contract"], parts["kp_a"])
    with pytest.raises(ValueError):
        announcement_to_attestation_signed(ann, parts["kp_b"])


def test_dispatch_unknown_kind_in_default_registry():
    print("=== C48 default registry: unknown kind for "
          "contract_announcement? C59 fixes it ===")
    from multiverse_c48 import DEFAULT_VERIFIER_REGISTRY
    # Before C59 extension, this would fail.
    # After C59, our own registry has it.
    assert "contract_announcement" not in DEFAULT_VERIFIER_REGISTRY
    assert "contract_announcement" in C59_VERIFIER_REGISTRY


# =====================================================================
# Registry population
# =====================================================================

def test_announcement_to_registry_happy():
    print("=== announcement_to_registry: populates registry ===")
    parts = _make_contract()
    ann = sign_announcement(parts["contract"], parts["kp_a"])
    reg = ContractRegistry()
    announcement_to_registry(ann, reg)
    assert reg.get(parts["terms"].terms_hash()) is not None
    assert reg.get(parts["terms"].terms_hash()).is_established()


def test_announcement_to_registry_rejects_invalid():
    print("=== announcement_to_registry: invalid → ValueError ===")
    parts = _make_contract()
    ann = sign_announcement(parts["contract"], parts["kp_a"])
    # Tamper signature
    tampered = ContractAnnouncement(
        announcer_world_id=ann.announcer_world_id,
        announcer_public_key=ann.announcer_public_key,
        world_a_id=ann.world_a_id,
        world_b_id=ann.world_b_id,
        terms_hash=ann.terms_hash,
        offer=ann.offer,
        acceptance=ann.acceptance,
        established_at=ann.established_at,
        timestamp=ann.timestamp,
        signature="00" * 64)
    reg = ContractRegistry()
    with pytest.raises(ValueError):
        announcement_to_registry(tampered, reg)


# =====================================================================
# Publisher
# =====================================================================

def test_publisher_announce():
    print("=== AnnouncementPublisher: announces ===")
    parts = _make_contract()
    curator = WorldCurator(parts["a"], parts["kp_a"])
    publisher = AnnouncementPublisher(curator)
    ann = publisher.announce(parts["contract"])
    assert verify_announcement(ann).valid


def test_publisher_wrap():
    print("=== AnnouncementPublisher: wraps ===")
    parts = _make_contract()
    curator = WorldCurator(parts["a"], parts["kp_a"])
    publisher = AnnouncementPublisher(curator)
    ann = publisher.announce(parts["contract"])
    att = publisher.wrap_as_attestation(ann)
    assert att.source_kind == "contract_announcement"
    assert verify_announcement_attestation(att).valid


# =====================================================================
# Integration: C56 relay propagation
# =====================================================================

def test_propagation_via_c56_relay():
    print("=== Propagation: announcement flows A→C via C56 ===")
    parts = _make_contract()
    ann = sign_announcement(parts["contract"], parts["kp_a"])
    att = announcement_to_attestation_signed(
        ann, parts["kp_a"])

    # Simple 2-node chain A→C
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
# Integration: C58 enforcement after learning
# =====================================================================

def test_learned_contract_can_be_cited():
    print("=== Learned contract: C can cite it (C58) ===")
    parts = _make_contract()
    ann = sign_announcement(parts["contract"], parts["kp_a"])
    reg = ContractRegistry()
    announcement_to_registry(ann, reg)
    # Build a C58-aware world with the populated registry
    world = ContractAwarePoetryWorld(
        "world:c", "C", registry=reg)
    ident = create_identity("Resident")
    world.petition(Petition(
        petitioner_token=ident.token,
        petitioner_name=ident.name,
        passport_admissions=(),
        message="hi"))
    r = world.act(Act(
        actor_token=ident.token, type="poem.turn",
        payload={
            "acknowledgment": "(seed)",
            "proposal": "a line",
            "invitation": "?",
            "holds_open": True,
            "cites_contract": parts["terms"].terms_hash(),
            "cites_world": "world:b",
        }))
    assert isinstance(r, Ack)


# =====================================================================
# Never raises
# =====================================================================

def test_verifiers_never_raise():
    print("=== Verifiers: never raise ===")
    assert not verify_announcement(None).valid
    assert not verify_announcement("not an announcement").valid
    assert not verify_announcement_attestation(None).valid


# =====================================================================
# C48 kind extension is documented
# =====================================================================

def test_c48_kind_still_disjoint():
    print("=== C48 kinds: still disjoint after extension ===")
    import multiverse_c48 as c48
    assert c48.DIRECT_KINDS & c48.WITNESSED_KINDS == set()
    assert c48.ALL_KINDS == (
        c48.DIRECT_KINDS | c48.WITNESSED_KINDS)


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: announce, propagate, learn ===")
    audit = demo(artifact_dir=str(tmp_path))
    s = audit["scenarios"]
    assert s["A_announce"]["valid"] is True
    assert s["A_announce"]["stranger_refused"] is True
    assert s["B_propagation"]["wrapped_valid"] is True
    assert s["B_propagation"]["relay_valid"] is True
    assert s["B_propagation"]["c_learned"] is True
    assert s["B_propagation"]["registry_populated"] is True
    assert s["B_propagation"]["c_can_cite"] is True
    assert s["C_tampered"]["valid"] is False
    assert (tmp_path / "contract_propagation_demo.json").exists()


if __name__ == "__main__":
    test_kind_extension()
    test_verifier_registry_has_kind()
    test_sign_announcement_happy()
    test_sign_from_acceptor_also_works()
    test_sign_from_stranger_refused()
    test_announcement_validates_fields()
    test_verify_announcement_happy()
    test_verify_announcement_wrong_key()
    test_verify_announcement_tampered_offer()
    test_verify_announcement_tampered_signature()
    test_verify_announcement_announcer_not_party()
    test_verify_announcement_malformed_offer()
    test_announcement_json_roundtrip()
    test_wrap_as_attestation_happy()
    test_wrap_wrong_keypair_refused()
    test_dispatch_unknown_kind_in_default_registry()
    test_announcement_to_registry_happy()
    test_announcement_to_registry_rejects_invalid()
    test_publisher_announce()
    test_publisher_wrap()
    test_propagation_via_c56_relay()
    test_learned_contract_can_be_cited()
    test_verifiers_never_raise()
    test_c48_kind_still_disjoint()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
