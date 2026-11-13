import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c3 import Ack, Refusal
from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c55 import WorldCurator
from multiverse_c57 import (
    ContractTerms,
    ContractOffer, ContractAcceptance, ContractRejection,
    EstablishedContract, BilateralRevocation,
    verify_contract_offer, verify_contract_acceptance,
    verify_contract_rejection,
    verify_established_contract,
    verify_bilateral_revocation,
    sign_offer, sign_acceptance, sign_rejection,
    sign_bilateral_revocation,
    ContractRecord, ContractRegistry,
    ContractNegotiator,
    demo,
    _now,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _make_pair(name_a="a", name_b="b"):
    from multiverse_c4 import PoetryWorld
    from multiverse_c5 import ChemistryWorld
    world_a = PoetryWorld(f"world:{name_a}", name_a)
    world_b = ChemistryWorld(f"world:{name_b}", name_b)
    kp_a = KeyPair.generate()
    kp_b = KeyPair.generate()
    curator_a = WorldCurator(world_a, kp_a)
    curator_b = WorldCurator(world_b, kp_b)
    return {
        "world_a": world_a, "world_b": world_b,
        "kp_a": kp_a, "kp_b": kp_b,
        "curator_a": curator_a, "curator_b": curator_b,
        "neg_a": ContractNegotiator(curator_a),
        "neg_b": ContractNegotiator(curator_b),
    }


def _make_terms(**overrides):
    base = {"kind": "test", "clause": "x"}
    base.update(overrides)
    return ContractTerms(content=base)


# =====================================================================
# ContractTerms
# =====================================================================

def test_terms_validates_content():
    print("=== ContractTerms: content must be dict ===")
    with pytest.raises(ValueError):
        ContractTerms(content="not a dict")


def test_terms_hash_deterministic():
    print("=== ContractTerms: hash is deterministic ===")
    t1 = ContractTerms(content={"a": 1, "b": 2})
    t2 = ContractTerms(content={"b": 2, "a": 1})
    assert t1.terms_hash() == t2.terms_hash()


def test_terms_hash_differs_on_content():
    print("=== ContractTerms: different content → different hash ===")
    t1 = ContractTerms(content={"a": 1})
    t2 = ContractTerms(content={"a": 2})
    assert t1.terms_hash() != t2.terms_hash()


# =====================================================================
# Sign / verify offer
# =====================================================================

def test_offer_signed_by_proposer():
    print("=== Offer: signed by proposer's key ===")
    parts = _make_pair()
    terms = _make_terms()
    offer = sign_offer(
        parts["neg_a"].world_id,
        parts["kp_a"],
        parts["neg_b"].world_id,
        terms)
    assert verify_contract_offer(
        offer, parts["kp_a"].public_key_hex())


def test_offer_wrong_key():
    print("=== Offer: wrong key → False ===")
    parts = _make_pair()
    offer = sign_offer(
        parts["neg_a"].world_id, parts["kp_a"],
        parts["neg_b"].world_id, _make_terms())
    wrong = KeyPair.generate()
    assert not verify_contract_offer(
        offer, wrong.public_key_hex())


def test_offer_rejects_self_target():
    print("=== Offer: rejects proposing to oneself ===")
    parts = _make_pair()
    with pytest.raises(ValueError):
        sign_offer(
            parts["neg_a"].world_id, parts["kp_a"],
            parts["neg_a"].world_id, _make_terms())


def test_offer_rejects_empty_fields():
    print("=== ContractOffer: validates fields ===")
    with pytest.raises(ValueError):
        ContractOffer(
            proposer_world_id="",
            proposer_public_key="aa" * 32,
            target_world_id="b",
            terms=_make_terms(),
            timestamp="t", signature="s")
    with pytest.raises(ValueError):
        ContractOffer(
            proposer_world_id="a",
            proposer_public_key="short",
            target_world_id="b",
            terms=_make_terms(),
            timestamp="t", signature="s")


# =====================================================================
# Sign / verify acceptance
# =====================================================================

def test_acceptance_signed_by_acceptor():
    print("=== Acceptance: signed by acceptor's key ===")
    parts = _make_pair()
    offer = sign_offer(
        parts["neg_a"].world_id, parts["kp_a"],
        parts["neg_b"].world_id, _make_terms())
    acc = sign_acceptance(
        parts["neg_b"].world_id, parts["kp_b"], offer)
    assert verify_contract_acceptance(
        acc, parts["kp_b"].public_key_hex())
    assert acc.offer_hash == offer.offer_hash()
    assert acc.terms_hash == offer.terms_hash


def test_acceptance_references_offer_and_terms():
    print("=== Acceptance: references offer and terms hashes ===")
    parts = _make_pair()
    terms = _make_terms()
    offer = sign_offer(
        parts["neg_a"].world_id, parts["kp_a"],
        parts["neg_b"].world_id, terms)
    acc = sign_acceptance(
        parts["neg_b"].world_id, parts["kp_b"], offer)
    assert acc.offer_hash == offer.offer_hash()
    assert acc.terms_hash == terms.terms_hash()


# =====================================================================
# Sign / verify rejection
# =====================================================================

def test_rejection_signed():
    print("=== Rejection: signed by rejector ===")
    parts = _make_pair()
    offer = sign_offer(
        parts["neg_a"].world_id, parts["kp_a"],
        parts["neg_b"].world_id, _make_terms())
    rej = sign_rejection(
        parts["neg_b"].world_id, parts["kp_b"],
        offer, reason="terms unacceptable")
    assert verify_contract_rejection(
        rej, parts["kp_b"].public_key_hex())
    assert rej.reason == "terms unacceptable"
    assert rej.offer_hash == offer.offer_hash()


# =====================================================================
# EstablishedContract verification
# =====================================================================

def test_established_contract_happy():
    print("=== EstablishedContract: happy path ===")
    parts = _make_pair()
    terms = _make_terms()
    offer = sign_offer(
        parts["neg_a"].world_id, parts["kp_a"],
        parts["neg_b"].world_id, terms)
    acc = sign_acceptance(
        parts["neg_b"].world_id, parts["kp_b"], offer)
    contract = EstablishedContract(
        offer=offer, acceptance=acc,
        established_at=_now())
    ok, reason = verify_established_contract(
        contract,
        parts["kp_a"].public_key_hex(),
        parts["kp_b"].public_key_hex())
    assert ok


def test_established_contract_bad_offer_sig():
    print("=== EstablishedContract: bad offer signature ===")
    parts = _make_pair()
    offer = sign_offer(
        parts["neg_a"].world_id, parts["kp_a"],
        parts["neg_b"].world_id, _make_terms())
    acc = sign_acceptance(
        parts["neg_b"].world_id, parts["kp_b"], offer)
    # Tamper with offer signature
    attacker = KeyPair.generate()
    tampered_offer = ContractOffer(
        proposer_world_id=offer.proposer_world_id,
        proposer_public_key=offer.proposer_public_key,
        target_world_id=offer.target_world_id,
        terms=offer.terms,
        timestamp=offer.timestamp,
        signature=attacker.sign(
            offer.canonical_payload()).hex())
    contract = EstablishedContract(
        offer=tampered_offer, acceptance=acc,
        established_at=_now())
    ok, reason = verify_established_contract(
        contract,
        parts["kp_a"].public_key_hex(),
        parts["kp_b"].public_key_hex())
    assert not ok
    assert "offer" in reason.lower()


def test_established_contract_bad_acceptance_sig():
    print("=== EstablishedContract: bad acceptance signature ===")
    parts = _make_pair()
    offer = sign_offer(
        parts["neg_a"].world_id, parts["kp_a"],
        parts["neg_b"].world_id, _make_terms())
    acc = sign_acceptance(
        parts["neg_b"].world_id, parts["kp_b"], offer)
    attacker = KeyPair.generate()
    tampered_acc = ContractAcceptance(
        acceptor_world_id=acc.acceptor_world_id,
        acceptor_public_key=acc.acceptor_public_key,
        offer_hash=acc.offer_hash,
        terms_hash=acc.terms_hash,
        timestamp=acc.timestamp,
        signature=attacker.sign(
            acc.canonical_payload()).hex())
    contract = EstablishedContract(
        offer=offer, acceptance=tampered_acc,
        established_at=_now())
    ok, reason = verify_established_contract(
        contract,
        parts["kp_a"].public_key_hex(),
        parts["kp_b"].public_key_hex())
    assert not ok
    assert "acceptance" in reason.lower()


def test_established_contract_wrong_offer_hash():
    print("=== EstablishedContract: wrong offer hash ===")
    parts = _make_pair()
    offer = sign_offer(
        parts["neg_a"].world_id, parts["kp_a"],
        parts["neg_b"].world_id, _make_terms())
    acc = sign_acceptance(
        parts["neg_b"].world_id, parts["kp_b"], offer)
    # Tamper with offer_hash
    tampered_acc = ContractAcceptance(
        acceptor_world_id=acc.acceptor_world_id,
        acceptor_public_key=acc.acceptor_public_key,
        offer_hash="ff" * 32,
        terms_hash=acc.terms_hash,
        timestamp=acc.timestamp,
        signature=acc.signature)
    contract = EstablishedContract(
        offer=offer, acceptance=tampered_acc,
        established_at=_now())
    ok, reason = verify_established_contract(
        contract,
        parts["kp_a"].public_key_hex(),
        parts["kp_b"].public_key_hex())
    assert not ok


def test_established_contract_wrong_terms_hash():
    print("=== EstablishedContract: wrong terms hash ===")
    parts = _make_pair()
    offer = sign_offer(
        parts["neg_a"].world_id, parts["kp_a"],
        parts["neg_b"].world_id, _make_terms())
    acc = sign_acceptance(
        parts["neg_b"].world_id, parts["kp_b"], offer)
    tampered_acc = ContractAcceptance(
        acceptor_world_id=acc.acceptor_world_id,
        acceptor_public_key=acc.acceptor_public_key,
        offer_hash=acc.offer_hash,
        terms_hash="ff" * 32,  # wrong
        timestamp=acc.timestamp,
        signature=acc.signature)
    contract = EstablishedContract(
        offer=offer, acceptance=tampered_acc,
        established_at=_now())
    ok, reason = verify_established_contract(
        contract,
        parts["kp_a"].public_key_hex(),
        parts["kp_b"].public_key_hex())
    assert not ok


def test_established_contract_acceptor_not_target():
    print("=== EstablishedContract: acceptor != target ===")
    parts = _make_pair()
    offer = sign_offer(
        parts["neg_a"].world_id, parts["kp_a"],
        "world:somewhere-else", _make_terms())
    acc = sign_acceptance(
        parts["neg_b"].world_id, parts["kp_b"], offer)
    contract = EstablishedContract(
        offer=offer, acceptance=acc,
        established_at=_now())
    ok, reason = verify_established_contract(
        contract,
        parts["kp_a"].public_key_hex(),
        parts["kp_b"].public_key_hex())
    assert not ok
    assert "not the offer's target" in reason


# =====================================================================
# BilateralRevocation
# =====================================================================

def test_bilateral_revocation_happy():
    print("=== BilateralRevocation: happy path ===")
    parts = _make_pair()
    terms = _make_terms()
    rev = sign_bilateral_revocation(
        contract_id=terms.terms_hash(),
        world_a_id=parts["neg_a"].world_id,
        world_a_kp=parts["kp_a"],
        world_b_id=parts["neg_b"].world_id,
        world_b_kp=parts["kp_b"],
        reason="mutual agreement ended")
    ok, reason = verify_bilateral_revocation(
        rev,
        parts["kp_a"].public_key_hex(),
        parts["kp_b"].public_key_hex())
    assert ok


def test_bilateral_revocation_one_sided():
    print("=== BilateralRevocation: one-sided → fails ===")
    parts = _make_pair()
    terms = _make_terms()
    rev = sign_bilateral_revocation(
        contract_id=terms.terms_hash(),
        world_a_id=parts["neg_a"].world_id,
        world_a_kp=parts["kp_a"],
        world_b_id=parts["neg_b"].world_id,
        world_b_kp=parts["kp_b"],
        reason="test")
    attacker = KeyPair.generate()
    one_sided = BilateralRevocation(
        contract_id=rev.contract_id,
        world_a_id=rev.world_a_id,
        world_a_public_key=rev.world_a_public_key,
        world_b_id=rev.world_b_id,
        world_b_public_key=rev.world_b_public_key,
        reason=rev.reason,
        timestamp=rev.timestamp,
        signature_a=rev.signature_a,
        signature_b=attacker.sign(
            rev.canonical_payload()).hex())
    ok, reason = verify_bilateral_revocation(
        one_sided,
        parts["kp_a"].public_key_hex(),
        parts["kp_b"].public_key_hex())
    assert not ok
    assert "world_b" in reason


def test_revocation_rejects_same_world():
    print("=== BilateralRevocation: rejects same world ===")
    kp = KeyPair.generate()
    with pytest.raises(ValueError):
        BilateralRevocation(
            contract_id="aa" * 32,
            world_a_id="w",
            world_a_public_key=kp.public_key_hex(),
            world_b_id="w",  # same
            world_b_public_key=kp.public_key_hex(),
            reason="", timestamp="t",
            signature_a="s", signature_b="s")


# =====================================================================
# ContractNegotiator
# =====================================================================

def test_negotiator_propose():
    print("=== Negotiator.propose: registers locally ===")
    parts = _make_pair()
    terms = _make_terms()
    offer = parts["neg_a"].propose(
        parts["neg_b"].world_id, terms)
    rec = parts["neg_a"].get_contract(terms.terms_hash())
    assert rec is not None
    assert rec.offer is not None
    assert rec.is_pending()


def test_negotiator_receive_offer_wrong_target():
    print("=== Negotiator.receive_offer: wrong target → Refusal ===")
    parts = _make_pair()
    offer = sign_offer(
        parts["neg_a"].world_id, parts["kp_a"],
        "world:someone-else", _make_terms())
    r = parts["neg_b"].receive_offer(offer)
    assert isinstance(r, Refusal)


def test_negotiator_receive_offer_bad_sig():
    print("=== Negotiator.receive_offer: bad sig → Refusal ===")
    parts = _make_pair()
    offer = sign_offer(
        parts["neg_a"].world_id, parts["kp_a"],
        parts["neg_b"].world_id, _make_terms())
    attacker = KeyPair.generate()
    tampered = ContractOffer(
        proposer_world_id=offer.proposer_world_id,
        proposer_public_key=offer.proposer_public_key,
        target_world_id=offer.target_world_id,
        terms=offer.terms,
        timestamp=offer.timestamp,
        signature=attacker.sign(
            offer.canonical_payload()).hex())
    r = parts["neg_b"].receive_offer(tampered)
    assert isinstance(r, Refusal)


def test_negotiator_full_flow():
    print("=== Negotiator: full flow (offer → accept → established) ===")
    parts = _make_pair()
    terms = _make_terms()
    offer = parts["neg_a"].propose(
        parts["neg_b"].world_id, terms)
    ack = parts["neg_b"].receive_offer(offer)
    assert isinstance(ack, Ack)
    acc = parts["neg_b"].accept(offer)
    ack2 = parts["neg_a"].receive_acceptance(acc)
    assert isinstance(ack2, Ack)
    # Both sides see the contract as established
    assert parts["neg_a"].is_active(terms.terms_hash())
    assert parts["neg_b"].is_active(terms.terms_hash())


def test_negotiator_reject():
    print("=== Negotiator: reject ===")
    parts = _make_pair()
    terms = _make_terms()
    offer = parts["neg_a"].propose(
        parts["neg_b"].world_id, terms)
    parts["neg_b"].receive_offer(offer)
    rej = parts["neg_b"].reject(offer, reason="bad terms")
    # A receives the rejection
    ack = parts["neg_a"].receive_rejection(rej)
    assert isinstance(ack, Ack)
    rec = parts["neg_a"].get_contract(terms.terms_hash())
    assert rec.is_rejected()
    assert not rec.is_established()


def test_negotiator_revocation_via_registry():
    print("=== Negotiator: bilateral revocation via registry ===")
    parts = _make_pair()
    terms = _make_terms()
    offer = parts["neg_a"].propose(
        parts["neg_b"].world_id, terms)
    acc = parts["neg_b"].accept(offer)
    parts["neg_a"].receive_acceptance(acc)
    assert parts["neg_a"].is_active(terms.terms_hash())
    # Bilateral revocation
    rev = sign_bilateral_revocation(
        contract_id=terms.terms_hash(),
        world_a_id=parts["neg_a"].world_id,
        world_a_kp=parts["kp_a"],
        world_b_id=parts["neg_b"].world_id,
        world_b_kp=parts["kp_b"],
        reason="revoked by mutual agreement")
    parts["neg_a"].registry.register_revocation(rev)
    parts["neg_b"].registry.register_revocation(rev)
    assert not parts["neg_a"].is_active(terms.terms_hash())
    assert not parts["neg_b"].is_active(terms.terms_hash())


# =====================================================================
# ContractRegistry
# =====================================================================

def test_registry_pending():
    print("=== Registry: pending ===")
    reg = ContractRegistry()
    parts = _make_pair()
    offer = sign_offer(
        parts["neg_a"].world_id, parts["kp_a"],
        parts["neg_b"].world_id, _make_terms())
    reg.register_offer(offer)
    assert len(reg.pending()) == 1
    assert len(reg.established()) == 0


def test_registry_established():
    print("=== Registry: established ===")
    reg = ContractRegistry()
    parts = _make_pair()
    offer = sign_offer(
        parts["neg_a"].world_id, parts["kp_a"],
        parts["neg_b"].world_id, _make_terms())
    acc = sign_acceptance(
        parts["neg_b"].world_id, parts["kp_b"], offer)
    reg.register_offer(offer)
    reg.register_acceptance(acc)
    assert len(reg.established()) == 1
    assert len(reg.pending()) == 0


def test_registry_revoked():
    print("=== Registry: revoked ===")
    reg = ContractRegistry()
    parts = _make_pair()
    terms = _make_terms()
    offer = sign_offer(
        parts["neg_a"].world_id, parts["kp_a"],
        parts["neg_b"].world_id, terms)
    acc = sign_acceptance(
        parts["neg_b"].world_id, parts["kp_b"], offer)
    reg.register_offer(offer)
    reg.register_acceptance(acc)
    rev = sign_bilateral_revocation(
        contract_id=terms.terms_hash(),
        world_a_id=parts["neg_a"].world_id,
        world_a_kp=parts["kp_a"],
        world_b_id=parts["neg_b"].world_id,
        world_b_kp=parts["kp_b"])
    reg.register_revocation(rev)
    assert len(reg.revoked()) == 1
    assert not reg.is_active(terms.terms_hash())


# =====================================================================
# Never raises
# =====================================================================

def test_verifiers_never_raise():
    print("=== Verifiers: never raise ===")
    assert not verify_contract_offer(None)
    assert not verify_contract_acceptance(None)
    assert not verify_contract_rejection(None)
    ok, _ = verify_established_contract(None)
    assert not ok
    ok, _ = verify_bilateral_revocation(None)
    assert not ok


def test_receive_methods_never_raise():
    print("=== Negotiator: receive methods never raise ===")
    parts = _make_pair()
    for bad in (None, "str", {}, 5):
        assert isinstance(
            parts["neg_b"].receive_offer(bad), Refusal)
        assert isinstance(
            parts["neg_a"].receive_acceptance(bad), Refusal)
        assert isinstance(
            parts["neg_a"].receive_rejection(bad), Refusal)


# =====================================================================
# JSON roundtrips
# =====================================================================

def test_offer_json_roundtrip():
    print("=== ContractOffer: JSON roundtrip ===")
    parts = _make_pair()
    offer = sign_offer(
        parts["neg_a"].world_id, parts["kp_a"],
        parts["neg_b"].world_id, _make_terms())
    wire = json.dumps(offer.to_dict())
    revived = ContractOffer.from_dict(json.loads(wire))
    assert verify_contract_offer(
        revived, parts["kp_a"].public_key_hex())


def test_established_contract_json_roundtrip():
    print("=== EstablishedContract: JSON roundtrip ===")
    parts = _make_pair()
    offer = sign_offer(
        parts["neg_a"].world_id, parts["kp_a"],
        parts["neg_b"].world_id, _make_terms())
    acc = sign_acceptance(
        parts["neg_b"].world_id, parts["kp_b"], offer)
    contract = EstablishedContract(
        offer=offer, acceptance=acc,
        established_at=_now())
    wire = json.dumps(contract.to_dict())
    revived = EstablishedContract.from_dict(json.loads(wire))
    ok, _ = verify_established_contract(
        revived,
        parts["kp_a"].public_key_hex(),
        parts["kp_b"].public_key_hex())
    assert ok


def test_revocation_json_roundtrip():
    print("=== BilateralRevocation: JSON roundtrip ===")
    parts = _make_pair()
    rev = sign_bilateral_revocation(
        contract_id="aa" * 32,
        world_a_id=parts["neg_a"].world_id,
        world_a_kp=parts["kp_a"],
        world_b_id=parts["neg_b"].world_id,
        world_b_kp=parts["kp_b"],
        reason="r")
    wire = json.dumps(rev.to_dict())
    revived = BilateralRevocation.from_dict(json.loads(wire))
    ok, _ = verify_bilateral_revocation(
        revived,
        parts["kp_a"].public_key_hex(),
        parts["kp_b"].public_key_hex())
    assert ok


# =====================================================================
# Structural claims
# =====================================================================

def test_c55_curator_untouched():
    print("=== C55 WorldCurator: untouched ===")
    parts = _make_pair()
    # Curator still has its methods; no negotiation attrs
    assert hasattr(parts["curator_a"], "hello")
    assert hasattr(parts["curator_a"], "receive")
    assert not hasattr(parts["curator_a"], "_registry")
    assert not hasattr(parts["curator_a"], "propose")


def test_negotiator_uses_curator():
    print("=== Negotiator: uses curator's world key ===")
    parts = _make_pair()
    assert parts["neg_a"].public_key == \
        parts["kp_a"].public_key_hex()
    assert parts["neg_a"].world_id == "world:a"


def test_negotiator_is_not_a_world():
    print("=== Negotiator: is not a WCP world ===")
    parts = _make_pair()
    assert not hasattr(parts["neg_a"], "manifest")
    assert not hasattr(parts["neg_a"], "petition")
    # But has negotiation methods
    assert hasattr(parts["neg_a"], "propose")
    assert hasattr(parts["neg_a"], "accept")
    assert hasattr(parts["neg_a"], "reject")


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: happy path, tamper, mismatch, one-sided ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["happy_path"]["established"] is True
    assert audit["happy_path"]["active_from_a"] is True
    assert audit["happy_path"]["active_from_b"] is True
    assert audit["tampered_offer"]["verified"] is False
    assert audit["mismatched_acceptance"]["verified"] is False
    assert audit["one_sided_revocation"]["verified"] is False
    assert (tmp_path / "contract_demo.json").exists()


if __name__ == "__main__":
    test_terms_validates_content()
    test_terms_hash_deterministic()
    test_terms_hash_differs_on_content()
    test_offer_signed_by_proposer()
    test_offer_wrong_key()
    test_offer_rejects_self_target()
    test_offer_rejects_empty_fields()
    test_acceptance_signed_by_acceptor()
    test_acceptance_references_offer_and_terms()
    test_rejection_signed()
    test_established_contract_happy()
    test_established_contract_bad_offer_sig()
    test_established_contract_bad_acceptance_sig()
    test_established_contract_wrong_offer_hash()
    test_established_contract_wrong_terms_hash()
    test_established_contract_acceptor_not_target()
    test_bilateral_revocation_happy()
    test_bilateral_revocation_one_sided()
    test_revocation_rejects_same_world()
    test_negotiator_propose()
    test_negotiator_receive_offer_wrong_target()
    test_negotiator_receive_offer_bad_sig()
    test_negotiator_full_flow()
    test_negotiator_reject()
    test_negotiator_revocation_via_registry()
    test_registry_pending()
    test_registry_established()
    test_registry_revoked()
    test_verifiers_never_raise()
    test_receive_methods_never_raise()
    test_offer_json_roundtrip()
    test_established_contract_json_roundtrip()
    test_revocation_json_roundtrip()
    test_c55_curator_untouched()
    test_negotiator_uses_curator()
    test_negotiator_is_not_a_world()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
