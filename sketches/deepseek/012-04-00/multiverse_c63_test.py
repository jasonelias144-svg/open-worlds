import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import Act, Ack, Refusal, Petition
from multiverse_c4 import PoetryWorld
from multiverse_c5 import ChemistryWorld
from multiverse_c13 import HAS_CRYPTO, KeyPair
from multiverse_c57 import (
    ContractTerms, ContractRecord, ContractRegistry,
    sign_offer, sign_acceptance,
    sign_bilateral_revocation,
    ContractOffer, ContractAcceptance, ContractRejection,
    BilateralRevocation,
)
from multiverse_c58 import ContractAwarePoetryWorld
from multiverse_c63 import (
    ContractPolicy,
    make_current_status_policy,
    make_claimed_time_policy,
    make_committed_time_policy,
    verify_contract_policy,
    DisputeVerdict,
    resolve_citation_dispute,
    PolicyAwareContractAwareWorld,
    demo,
    _hash_payload,
    _now,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _make_record(revoked: bool = False, pending: bool = False):
    """Construct a ContractRecord with controllable state."""
    kp_a = KeyPair.generate()
    kp_b = KeyPair.generate()
    terms = ContractTerms(content={"kind": "test"})
    offer = sign_offer("world:a", kp_a, "world:b", terms)
    acceptance = sign_acceptance("world:b", kp_b, offer)
    reg = ContractRegistry()
    reg.register_offer(offer)
    if not pending:
        reg.register_acceptance(acceptance)
    rec = reg.get(terms.terms_hash())
    if rec is None:
        # pending-only case: register_offer creates the record
        rec = reg.get(terms.terms_hash())
    rec.established_at = "2024-03-01T12:00:00+00:00"
    if revoked and not pending:
        rev = sign_bilateral_revocation(
            contract_id=terms.terms_hash(),
            world_a_id="world:a", world_a_kp=kp_a,
            world_b_id="world:b", world_b_kp=kp_b,
            reason="revoked",
            timestamp="2024-03-05T18:00:00+00:00")
        reg.register_revocation(rev)
        rec.revoked_at = "2024-03-05T18:00:00+00:00"
    return rec, offer, kp_a, kp_b, terms


def _policy_current():
    kp = KeyPair.generate()
    return make_current_status_policy("p", "w", kp)


def _policy_claimed():
    kp = KeyPair.generate()
    return make_claimed_time_policy("p", "w", kp)


def _policy_committed():
    kp = KeyPair.generate()
    return make_committed_time_policy("p", "w", kp)


# =====================================================================
# ContractPolicy construction
# =====================================================================

def test_policy_validates_fields():
    print("=== ContractPolicy: validates fields ===")
    with pytest.raises(ValueError):
        ContractPolicy(
            policy_id="", version=1,
            content={"rule": "current_status"},
            author_world_id="w",
            author_public_key="aa" * 32,
            timestamp="t", signature="s")
    with pytest.raises(ValueError):
        ContractPolicy(
            policy_id="p", version=0,
            content={"rule": "current_status"},
            author_world_id="w",
            author_public_key="aa" * 32,
            timestamp="t", signature="s")
    with pytest.raises(ValueError):
        ContractPolicy(
            policy_id="p", version=1,
            content={"rule": "bogus"},  # unknown rule
            author_world_id="w",
            author_public_key="aa" * 32,
            timestamp="t", signature="s")


def test_policy_json_roundtrip():
    print("=== ContractPolicy: JSON roundtrip ===")
    kp = KeyPair.generate()
    p = make_current_status_policy("p", "w", kp)
    wire = json.dumps(p.to_dict())
    revived = ContractPolicy.from_dict(json.loads(wire))
    assert verify_contract_policy(revived)


def test_standard_constructors():
    print("=== Three standard policy constructors ===")
    kp = KeyPair.generate()
    for maker, rule in (
        (make_current_status_policy, "current_status"),
        (make_claimed_time_policy, "claimed_time"),
        (make_committed_time_policy, "committed_time"),
    ):
        p = maker("p", "w", kp)
        assert p.rule == rule
        assert verify_contract_policy(p)


# =====================================================================
# current_status policy
# =====================================================================

def test_current_status_established_honors():
    print("=== current_status: established → honored ===")
    rec, _, _, _, _ = _make_record()
    v = resolve_citation_dispute(
        _policy_current(), rec,
        citation_claimed_time="2024-03-03T00:00:00+00:00")
    assert v.honored
    assert v.rule_applied == "current_status"


def test_current_status_revoked_refuses():
    print("=== current_status: revoked → refused ===")
    rec, _, _, _, _ = _make_record(revoked=True)
    v = resolve_citation_dispute(
        _policy_current(), rec,
        citation_claimed_time="2024-03-03T00:00:00+00:00")
    assert not v.honored
    assert "revoked" in v.reason


def test_current_status_pending_refuses():
    print("=== current_status: pending → refused ===")
    rec, _, _, _, _ = _make_record(pending=True)
    v = resolve_citation_dispute(
        _policy_current(), rec,
        citation_claimed_time="2024-03-03T00:00:00+00:00")
    assert not v.honored
    assert "pending" in v.reason


# =====================================================================
# claimed_time policy
# =====================================================================

def test_claimed_time_inside_window_honors():
    print("=== claimed_time: inside window → honored ===")
    rec, _, _, _, _ = _make_record(revoked=True)
    v = resolve_citation_dispute(
        _policy_claimed(), rec,
        citation_claimed_time="2024-03-03T00:00:00+00:00")
    assert v.honored


def test_claimed_time_after_revocation_refuses():
    print("=== claimed_time: after revocation → refused ===")
    rec, _, _, _, _ = _make_record(revoked=True)
    v = resolve_citation_dispute(
        _policy_claimed(), rec,
        citation_claimed_time="2024-03-05T20:00:00+00:00")
    assert not v.honored
    assert "after revocation" in v.reason


def test_claimed_time_before_establishment_refuses():
    print("=== claimed_time: before establishment → refused ===")
    rec, _, _, _, _ = _make_record()
    v = resolve_citation_dispute(
        _policy_claimed(), rec,
        citation_claimed_time="2024-02-01T00:00:00+00:00")
    assert not v.honored
    assert "before establishment" in v.reason


def test_claimed_time_bad_timestamp_refuses():
    print("=== claimed_time: unparseable → refused ===")
    rec, _, _, _, _ = _make_record()
    v = resolve_citation_dispute(
        _policy_claimed(), rec,
        citation_claimed_time="not-a-date")
    assert not v.honored


# =====================================================================
# committed_time policy
# =====================================================================

def test_committed_time_no_ledger_refuses():
    print("=== committed_time: no ledger → refused ===")
    rec, _, _, _, _ = _make_record()
    v = resolve_citation_dispute(
        _policy_committed(), rec,
        citation_claimed_time="2024-03-03T00:00:00+00:00",
        citation_hash="aa" * 32,
        ledger=None)
    assert not v.honored
    assert "ledger" in v.reason.lower()


def test_committed_time_no_citation_hash_refuses():
    print("=== committed_time: no citation_hash → refused ===")
    rec, offer, _, _, _ = _make_record()
    ledger = {offer.offer_hash(): 0}
    v = resolve_citation_dispute(
        _policy_committed(), rec,
        citation_claimed_time="2024-03-03T00:00:00+00:00",
        citation_hash=None,
        ledger=ledger)
    assert not v.honored
    assert "citation_hash" in v.reason


def test_committed_time_in_order_honors():
    print("=== committed_time: citation between establish and "
          "revoke → honored ===")
    rec, offer, kp_a, kp_b, terms = _make_record(revoked=True)
    citation_hash = _hash_payload(b"cit")
    rev_hash = _hash_payload(rec.revocation.canonical_payload())
    ledger = {
        offer.offer_hash(): 0,
        citation_hash: 1,
        rev_hash: 2,
    }
    v = resolve_citation_dispute(
        _policy_committed(), rec,
        citation_claimed_time="ignored",
        citation_hash=citation_hash,
        ledger=ledger)
    assert v.honored


def test_committed_time_citation_after_revoke_refuses():
    print("=== committed_time: citation after revoke → refused ===")
    rec, offer, _, _, _ = _make_record(revoked=True)
    citation_hash = _hash_payload(b"cit")
    rev_hash = _hash_payload(rec.revocation.canonical_payload())
    ledger = {
        offer.offer_hash(): 0,
        rev_hash: 1,
        citation_hash: 2,
    }
    v = resolve_citation_dispute(
        _policy_committed(), rec,
        citation_claimed_time="ignored",
        citation_hash=citation_hash,
        ledger=ledger)
    assert not v.honored
    assert "after revocation" in v.reason


def test_committed_time_citation_before_establish_refuses():
    print("=== committed_time: citation before establish → refused ===")
    rec, offer, _, _, _ = _make_record()
    citation_hash = _hash_payload(b"cit")
    ledger = {
        citation_hash: 0,
        offer.offer_hash(): 5,
    }
    v = resolve_citation_dispute(
        _policy_committed(), rec,
        citation_claimed_time="ignored",
        citation_hash=citation_hash,
        ledger=ledger)
    assert not v.honored
    assert "before establishment" in v.reason


def test_committed_time_establish_not_in_ledger_refuses():
    print("=== committed_time: establishment not in ledger → "
          "refused ===")
    rec, offer, _, _, _ = _make_record()
    citation_hash = _hash_payload(b"cit")
    v = resolve_citation_dispute(
        _policy_committed(), rec,
        citation_claimed_time="ignored",
        citation_hash=citation_hash,
        ledger={citation_hash: 5})  # no establishment
    assert not v.honored
    assert "establishment not in ledger" in v.reason


# =====================================================================
# Policy verification
# =====================================================================

def test_policy_wrong_key():
    print("=== verify_contract_policy: wrong key → False ===")
    kp = KeyPair.generate()
    p = make_current_status_policy("p", "w", kp)
    wrong = KeyPair.generate()
    assert not verify_contract_policy(p, wrong.public_key_hex())


def test_policy_tampered():
    print("=== verify_contract_policy: tampered → False ===")
    kp = KeyPair.generate()
    p = make_current_status_policy("p", "w", kp)
    tampered = ContractPolicy(
        policy_id=p.policy_id,
        version=p.version,
        content={"rule": "claimed_time"},  # tampered
        author_world_id=p.author_world_id,
        author_public_key=p.author_public_key,
        timestamp=p.timestamp,
        signature=p.signature)
    assert not verify_contract_policy(tampered)


def test_resolver_rejects_tampered_policy():
    print("=== resolve: tampered policy → refused ===")
    rec, _, _, _, _ = _make_record()
    p = _policy_current()
    tampered = ContractPolicy(
        policy_id=p.policy_id,
        version=p.version,
        content={"rule": "claimed_time"},
        author_world_id=p.author_world_id,
        author_public_key=p.author_public_key,
        timestamp=p.timestamp,
        signature=p.signature)
    v = resolve_citation_dispute(
        tampered, rec,
        citation_claimed_time="2024-03-03T00:00:00+00:00")
    assert not v.honored
    assert "INVALID" in v.reason


# =====================================================================
# Never raises
# =====================================================================

def test_resolver_never_raises():
    print("=== resolve_citation_dispute: never raises ===")
    rec, _, _, _, _ = _make_record()
    p = _policy_current()
    assert not resolve_citation_dispute(
        None, rec, "t").honored
    assert not resolve_citation_dispute(
        p, None, "t").honored
    assert not resolve_citation_dispute(
        p, rec, None).honored  # type: ignore


# =====================================================================
# C58 integration — policy replaces state check
# =====================================================================

def _world_with_policy(policy, registry, ledger=None):
    return PolicyAwareContractAwareWorld(
        "world:c", "C",
        registry=registry,
        policy=policy,
        ledger_view=ledger or {})


def test_current_status_policy_equivalent_to_c58():
    """A PolicyAwareWorld with current_status policy behaves
    identically to a plain ContractAware world on the same
    registry."""
    print("=== current_status policy ≡ C58 default ===")
    rec, offer, kp_a, kp_b, terms = _make_record(revoked=True)
    reg = rec.__dict__.get("_registry")  # not available; rebuild
    reg = ContractRegistry()
    reg.register_offer(offer)
    rec2 = reg.get(terms.terms_hash())
    rec2.established_at = rec.established_at
    reg.register_revocation(rec.revocation)
    rec2.revoked_at = rec.revoked_at

    kp = KeyPair.generate()
    policy = make_current_status_policy("p", "w", kp)
    world = _world_with_policy(policy, reg)
    ident = create_identity("R")
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
            "cites_contract": terms.terms_hash(),
            "cites_world": "world:b",
        }))
    assert isinstance(r, Refusal)
    assert "policy" in r.reason.lower()
    assert "current_status" in r.reason


def test_claimed_time_policy_honors_after_revocation():
    print("=== claimed_time policy: honors after revocation "
          "if claimed inside window ===")
    rec, offer, kp_a, kp_b, terms = _make_record(revoked=True)
    reg = ContractRegistry()
    reg.register_offer(offer)
    rec2 = reg.get(terms.terms_hash())
    rec2.established_at = rec.established_at
    reg.register_revocation(rec.revocation)
    rec2.revoked_at = rec.revoked_at
    kp = KeyPair.generate()
    policy = make_claimed_time_policy("p", "w", kp)
    world = _world_with_policy(policy, reg)
    ident = create_identity("R")
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
            "cites_contract": terms.terms_hash(),
            "cites_world": "world:b",
            "claimed_time": "2024-03-03T00:00:00+00:00",
        }))
    assert isinstance(r, Ack)


def test_committed_time_policy_refuses_case_b():
    print("=== committed_time policy: refuses Case B ordering ===")
    rec, offer, kp_a, kp_b, terms = _make_record(revoked=True)
    reg = ContractRegistry()
    reg.register_offer(offer)
    rec2 = reg.get(terms.terms_hash())
    rec2.established_at = rec.established_at
    reg.register_revocation(rec.revocation)
    rec2.revoked_at = rec.revoked_at
    citation_hash = _hash_payload(b"cit")
    rev_hash = _hash_payload(rec.revocation.canonical_payload())
    ledger_b = {
        offer.offer_hash(): 0,
        rev_hash: 1,
        citation_hash: 2,
    }
    kp = KeyPair.generate()
    policy = make_committed_time_policy("p", "w", kp)
    world = _world_with_policy(policy, reg, ledger=ledger_b)
    ident = create_identity("R")
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
            "cites_contract": terms.terms_hash(),
            "cites_world": "world:b",
            "claimed_time": "2024-03-03T00:00:00+00:00",
            "citation_hash": citation_hash,
        }))
    assert isinstance(r, Refusal)
    assert "committed_time" in r.reason
    assert "after revocation" in r.reason


def test_committed_time_policy_honors_case_a():
    print("=== committed_time policy: honors Case A ordering ===")
    rec, offer, kp_a, kp_b, terms = _make_record(revoked=True)
    reg = ContractRegistry()
    reg.register_offer(offer)
    rec2 = reg.get(terms.terms_hash())
    rec2.established_at = rec.established_at
    reg.register_revocation(rec.revocation)
    rec2.revoked_at = rec.revoked_at
    citation_hash = _hash_payload(b"cit")
    rev_hash = _hash_payload(rec.revocation.canonical_payload())
    ledger_a = {
        offer.offer_hash(): 0,
        citation_hash: 1,
        rev_hash: 2,
    }
    kp = KeyPair.generate()
    policy = make_committed_time_policy("p", "w", kp)
    world = _world_with_policy(policy, reg, ledger=ledger_a)
    ident = create_identity("R")
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
            "cites_contract": terms.terms_hash(),
            "cites_world": "world:b",
            "claimed_time": "2024-03-03T00:00:00+00:00",
            "citation_hash": citation_hash,
        }))
    assert isinstance(r, Ack)


def test_world_rejects_bad_policy():
    print("=== PolicyAwareWorld: rejects bad policy signature ===")
    reg = ContractRegistry()
    kp = KeyPair.generate()
    policy = make_current_status_policy("p", "w", kp)
    tampered = ContractPolicy(
        policy_id=policy.policy_id,
        version=policy.version,
        content={"rule": "claimed_time"},
        author_world_id=policy.author_world_id,
        author_public_key=policy.author_public_key,
        timestamp=policy.timestamp,
        signature=policy.signature)
    with pytest.raises(ValueError):
        PolicyAwareContractAwareWorld(
            "world:c", "C", registry=reg, policy=tampered)


# =====================================================================
# World-involvement and cites_world checks preserved
# =====================================================================

def test_world_involvement_check_preserved():
    print("=== PolicyAwareWorld: world-involvement check preserved ===")
    rec, offer, kp_a, kp_b, terms = _make_record()
    # Build a record about a DIFFERENT world pair
    other_terms = ContractTerms(content={"other": True})
    other_offer = sign_offer(
        "world:x", KeyPair.generate(),
        "world:y", other_terms)
    other_acc = sign_acceptance(
        "world:y", KeyPair.generate(), other_offer)
    reg = ContractRegistry()
    reg.register_offer(other_offer)
    reg.register_acceptance(other_acc)
    kp = KeyPair.generate()
    policy = make_claimed_time_policy("p", "w", kp)
    world = _world_with_policy(policy, reg)
    ident = create_identity("R")
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
            "cites_contract": other_terms.terms_hash(),
            "claimed_time": "2024-03-03T00:00:00+00:00",
        }))
    assert isinstance(r, Refusal)
    assert "not involve" in r.reason


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: 3 policies × 2 ledger orderings ===")
    audit = demo(artifact_dir=str(tmp_path))
    v = audit["verdicts"]
    # current_status refuses both cases (contract is revoked now)
    assert v["Case A"]["current_status"]["honored"] is False
    assert v["Case B"]["current_status"]["honored"] is False
    # claimed_time honors both cases (claims put citation in window)
    assert v["Case A"]["claimed_time"]["honored"] is True
    assert v["Case B"]["claimed_time"]["honored"] is True
    # committed_time honors Case A, refuses Case B
    assert v["Case A"]["committed_time"]["honored"] is True
    assert v["Case B"]["committed_time"]["honored"] is False
    # C58 integration
    assert audit["c58_integration"]["committed_time_case_b"] == "Refusal"
    assert audit["c58_integration"]["committed_time_case_a"] == "Ack"
    assert (tmp_path / "policy_disputes_demo.json").exists()


if __name__ == "__main__":
    test_policy_validates_fields()
    test_policy_json_roundtrip()
    test_standard_constructors()
    test_current_status_established_honors()
    test_current_status_revoked_refuses()
    test_current_status_pending_refuses()
    test_claimed_time_inside_window_honors()
    test_claimed_time_after_revocation_refuses()
    test_claimed_time_before_establishment_refuses()
    test_claimed_time_bad_timestamp_refuses()
    test_committed_time_no_ledger_refuses()
    test_committed_time_no_citation_hash_refuses()
    test_committed_time_in_order_honors()
    test_committed_time_citation_after_revoke_refuses()
    test_committed_time_citation_before_establish_refuses()
    test_committed_time_establish_not_in_ledger_refuses()
    test_policy_wrong_key()
    test_policy_tampered()
    test_resolver_rejects_tampered_policy()
    test_resolver_never_raises()
    test_current_status_policy_equivalent_to_c58()
    test_claimed_time_policy_honors_after_revocation()
    test_committed_time_policy_refuses_case_b()
    test_committed_time_policy_honors_case_a()
    test_world_rejects_bad_policy()
    test_world_involvement_check_preserved()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
