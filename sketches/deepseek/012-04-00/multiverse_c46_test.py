# multiverse_c46_test.py
import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c44 import (
    Proposal, Decision, QuorumRule, verify_decision,
)
from multiverse_c45 import (
    DeliberativeDecision, DeliberativeCouncil,
    SignedPosition, verify_position,
    _hash_payload,
)
from multiverse_c46 import (
    FederatedSignedPosition, verify_federated_position,
    FederationEvidence,
    FederatedDeliberativeMember,
    FederatedDeliberativeDecision,
    FederatedDeliberativeCouncil,
    FederatedDeliberativeVerdict,
    verify_federated_deliberation,
    demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _rule_fixed(stance):
    def rule(proposal, ctx):
        return (stance, f"rule-{stance}", ())
    return rule


def _make_council(council_id="c", rules=None, quorum=(2, 2)):
    council = FederatedDeliberativeCouncil(
        council_id, QuorumRule(*quorum),
        max_rounds=3, stability_rounds=1)
    keys = {}
    if rules is None:
        rules = [lambda p, c: ("yea", "yea", ()),
                 lambda p, c: ("yea", "yea", ()),
                 lambda p, c: ("yea", "yea", ())]
    for i, r in enumerate(rules):
        kp = KeyPair.generate()
        council.add_member(FederatedDeliberativeMember(
            entity_id=f"{council_id}:m{i}",
            name=f"{council_id}-{i}",
            member_kp=kp, decision_rule=r))
        keys[f"{council_id}:m{i}"] = kp.public_key_hex()
    return council, keys


def _simple_proposal():
    return Proposal(content={"action": "test"})


# =====================================================================
# FederatedSignedPosition
# =====================================================================

def test_position_validates_references():
    print("=== FederatedSignedPosition: references validated ===")
    with pytest.raises(ValueError):
        FederatedSignedPosition(
            member_token="m", member_name="M",
            member_public_key="aa" * 32,
            proposal_hash="bb" * 32,
            round_num=0, stance="yea",
            rationale="", timestamp="t", signature="s",
            references=(("only_one",),))  # not 2-tuple
    with pytest.raises(ValueError):
        FederatedSignedPosition(
            member_token="m", member_name="M",
            member_public_key="aa" * 32,
            proposal_hash="bb" * 32,
            round_num=0, stance="yea",
            rationale="", timestamp="t", signature="s",
            references=(("c", "short"),))  # hash too short


def test_position_canonical_payload_includes_refs():
    print("=== FederatedSignedPosition: payload includes refs ===")
    p = FederatedSignedPosition(
        member_token="m", member_name="M",
        member_public_key="aa" * 32,
        proposal_hash="bb" * 32,
        round_num=0, stance="yea",
        rationale="", timestamp="t", signature="s",
        references=(("alpha", "cc" * 32),))
    payload = p.canonical_payload()
    assert b'"references"' in payload
    assert b'"alpha"' in payload
    # Parent payload would not include references
    assert b'"references"' not in SignedPosition(
        member_token="m", member_name="M",
        member_public_key="aa" * 32,
        proposal_hash="bb" * 32,
        round_num=0, stance="yea",
        rationale="", timestamp="t", signature="s",
    ).canonical_payload()


def test_position_signature_verifies_with_parent_verifier():
    """Backward compat: C45's verify_position still works on a
    FederatedSignedPosition — polymorphic canonical_payload."""
    print("=== FederatedSignedPosition: parent verifier works ===")
    council, keys = _make_council()
    member = council._members["c:m0"]
    pos = member.produce_federated_position(
        _simple_proposal(), 0,
        context={"round_num": 0, "positions_by_member": {},
                 "federation_evidence": {}},
        available_refs=set())
    assert isinstance(pos, FederatedSignedPosition)
    # C45 verifier works
    assert verify_position(pos, keys["c:m0"])


def test_federated_position_verify_checks_references():
    print("=== verify_federated_position: checks refs ===")
    council, keys = _make_council()
    member = council._members["c:m0"]
    fake_evidence = {
        "alpha": {
            "decision_hash": "cc" * 32,
            "outcome": "passed",
            "yea": 2, "nay": 1, "abstain": 0,
        }
    }
    def rule_with_ref(p, ctx):
        return ("yea", "following",
                (("alpha", "cc" * 32),))
    member._decision_rule = rule_with_ref
    pos = member.produce_federated_position(
        _simple_proposal(), 0,
        context={"round_num": 0, "positions_by_member": {},
                 "federation_evidence": fake_evidence},
        available_refs={("alpha", "cc" * 32)})
    # Allowed ref passes
    ok, reason = verify_federated_position(
        pos, keys["c:m0"],
        allowed_references={("alpha", "cc" * 32)})
    assert ok
    # Wrong allowed set fails
    ok2, reason2 = verify_federated_position(
        pos, keys["c:m0"], allowed_references=set())
    assert not ok2
    assert "not in evidence" in reason2


# =====================================================================
# FederationEvidence
# =====================================================================

def test_evidence_from_decision_works():
    print("=== FederationEvidence.from_decision: plain + federated ===")
    council, _ = _make_council()
    dec = council.deliberate_and_resolve_federated(
        _simple_proposal(), evidence=[])
    ev = FederationEvidence.from_decision("alpha", dec)
    assert ev.council_id == "alpha"
    assert len(ev.decision_hash) == 64
    assert ev.outcome in ("passed", "rejected", "no_quorum")
    # Also works with plain Decision
    plain = dec.inner.final_decision
    ev2 = FederationEvidence.from_decision("beta", plain)
    assert ev2.outcome == plain.outcome


def test_evidence_rejects_wrong_type():
    print("=== FederationEvidence.from_decision: rejects other types ===")
    with pytest.raises(TypeError):
        FederationEvidence.from_decision("x", "not a decision")


def test_evidence_hash_is_content_derived():
    print("=== FederationEvidence: hash is content-derived ===")
    council, _ = _make_council()
    dec = council.deliberate_and_resolve_federated(
        _simple_proposal(), evidence=[])
    ev = FederationEvidence.from_decision("alpha", dec)
    recomputed = _hash_payload(canonical_bytes(dec.to_dict()))
    assert ev.decision_hash == recomputed


# =====================================================================
# DeliberativeCouncil with federated rules
# =====================================================================

def test_federated_member_rule_can_see_evidence():
    print("=== FederatedDeliberativeMember: rule sees evidence ===")
    kp = KeyPair.generate()
    captured = {}
    def rule(p, ctx):
        captured["evidence"] = dict(
            ctx.get("federation_evidence", {}))
        return ("yea", "", ())
    member = FederatedDeliberativeMember(
        entity_id="m", name="M", member_kp=kp,
        decision_rule=rule)
    fake_evidence = {
        "alpha": {"decision_hash": "cc" * 32,
                  "outcome": "passed",
                  "yea": 2, "nay": 0, "abstain": 0},
    }
    member.produce_federated_position(
        _simple_proposal(), 0,
        context={"round_num": 0, "positions_by_member": {},
                 "federation_evidence": fake_evidence},
        available_refs={("alpha", "cc" * 32)})
    assert "alpha" in captured["evidence"]
    assert captured["evidence"]["alpha"]["outcome"] == "passed"


def test_federated_member_can_return_2_tuple():
    """A rule that returns 2-tuple still produces a valid position
    (with empty references)."""
    print("=== FederatedDeliberativeMember: 2-tuple rule → no refs ===")
    kp = KeyPair.generate()
    def rule(p, ctx):
        return ("yea", "no evidence used")
    member = FederatedDeliberativeMember(
        entity_id="m", name="M", member_kp=kp,
        decision_rule=rule)
    pos = member.produce_federated_position(
        _simple_proposal(), 0,
        context={"round_num": 0, "positions_by_member": {},
                 "federation_evidence": {}},
        available_refs=set())
    assert pos.references == ()
    assert pos.stance == "yea"


# =====================================================================
# verify_federated_deliberation
# =====================================================================

def test_verify_federated_happy():
    print("=== verify_federated_deliberation: happy path ===")
    # Alpha
    alpha, alpha_keys = _make_council("alpha")
    alpha_dec = alpha.deliberate_and_resolve_federated(
        Proposal(content={"action": "a"}), evidence=[])
    ev = FederationEvidence.from_decision("alpha", alpha_dec)

    # Beta references alpha
    def beta_rule(p, ctx):
        evidence = ctx.get("federation_evidence", {})
        for cid, s in evidence.items():
            refs = ((cid, s["decision_hash"]),)
            if s["outcome"] == "passed":
                return ("yea", "following " + cid, refs)
        return ("abstain", "", ())
    beta, beta_keys = _make_council(
        "beta", rules=[beta_rule, beta_rule, beta_rule])
    beta_dec = beta.deliberate_and_resolve_federated(
        Proposal(content={"action": "b"}), evidence=[ev])

    v = verify_federated_deliberation(
        beta_dec, beta_keys, {"alpha": alpha_keys})
    assert v.valid
    assert v.local_valid
    assert v.evidence_valid
    assert v.references_valid


def test_verify_federated_evidence_hash_mismatch():
    print("=== verify: evidence decision_hash mismatch ===")
    alpha, alpha_keys = _make_council("alpha")
    alpha_dec = alpha.deliberate_and_resolve_federated(
        Proposal(content={"action": "a"}), evidence=[])
    ev = FederationEvidence.from_decision("alpha", alpha_dec)
    # Tamper: wrong hash claim
    tampered_ev = FederationEvidence(
        council_id=ev.council_id,
        decision=ev.decision,
        decision_hash="00" * 32,
        outcome=ev.outcome,
        yea_count=ev.yea_count,
        nay_count=ev.nay_count,
        abstain_count=ev.abstain_count,
        proposal_hash=ev.proposal_hash)
    def beta_rule(p, ctx):
        return ("yea", "", ())
    beta, beta_keys = _make_council(
        "beta", rules=[beta_rule, beta_rule, beta_rule])
    # Build a decision with the tampered evidence
    # (use empty-refs rule so references don't interfere)
    beta_dec = beta.deliberate_and_resolve_federated(
        Proposal(content={"action": "b"}),
        evidence=[tampered_ev])
    v = verify_federated_deliberation(
        beta_dec, beta_keys, {"alpha": alpha_keys})
    assert not v.valid
    assert not v.evidence_valid
    assert any("hash" in r for _, r in v.evidence_errors)


def test_verify_federated_bad_inner_decision():
    print("=== verify: evidence's inner decision invalid ===")
    alpha, alpha_keys = _make_council("alpha")
    alpha_dec = alpha.deliberate_and_resolve_federated(
        Proposal(content={"action": "a"}), evidence=[])
    ev = FederationEvidence.from_decision("alpha", alpha_dec)
    # Build a tampered inner decision (invalid vote)
    orig_inner = alpha_dec.inner
    tampered_votes = list(orig_inner.final_decision.votes)
    bad_vote = tampered_votes[0]
    attacker = KeyPair.generate()
    bad_sig = attacker.sign(bad_vote.canonical_payload()).hex()
    from multiverse_c44 import Vote
    tampered_votes[0] = Vote(
        member_token=bad_vote.member_token,
        member_name=bad_vote.member_name,
        member_public_key=bad_vote.member_public_key,
        proposal_hash=bad_vote.proposal_hash,
        decision=bad_vote.decision,
        timestamp=bad_vote.timestamp,
        signature=bad_sig)
    from multiverse_c44 import Decision
    fd = orig_inner.final_decision
    tampered_fd = Decision(
        proposal=fd.proposal, proposal_hash=fd.proposal_hash,
        votes=tuple(tampered_votes), quorum=fd.quorum,
        yea_count=fd.yea_count, nay_count=fd.nay_count,
        abstain_count=fd.abstain_count,
        present_count=fd.present_count,
        outcome=fd.outcome, timestamp=fd.timestamp)
    tampered_inner = DeliberativeDecision(
        proposal=orig_inner.proposal,
        proposal_hash=orig_inner.proposal_hash,
        positions=orig_inner.positions,
        rounds_run=orig_inner.rounds_run,
        converged_at_round=orig_inner.converged_at_round,
        final_decision=tampered_fd)
    # Recompute evidence hash on the tampered decision
    tampered_hash = _hash_payload(
        canonical_bytes(tampered_inner.to_dict()))
    tampered_ev = FederationEvidence(
        council_id="alpha",
        decision=tampered_inner,
        decision_hash=tampered_hash,
        outcome=ev.outcome,
        yea_count=ev.yea_count, nay_count=ev.nay_count,
        abstain_count=ev.abstain_count,
        proposal_hash=ev.proposal_hash)

    def beta_rule(p, ctx): return ("yea", "", ())
    beta, beta_keys = _make_council(
        "beta", rules=[beta_rule, beta_rule, beta_rule])
    beta_dec = beta.deliberate_and_resolve_federated(
        Proposal(content={"action": "b"}), evidence=[tampered_ev])
    v = verify_federated_deliberation(
        beta_dec, beta_keys, {"alpha": alpha_keys})
    assert not v.valid
    assert not v.evidence_valid


def test_verify_federated_forged_reference():
    print("=== verify: position references non-evidence ===")
    alpha, alpha_keys = _make_council("alpha")
    alpha_dec = alpha.deliberate_and_resolve_federated(
        Proposal(content={"action": "a"}), evidence=[])
    ev = FederationEvidence.from_decision("alpha", alpha_dec)
    def beta_rule(p, ctx):
        evidence = ctx.get("federation_evidence", {})
        for cid, s in evidence.items():
            return ("yea", "", ((cid, s["decision_hash"]),))
        return ("yea", "", ())
    beta, beta_keys = _make_council(
        "beta", rules=[beta_rule, beta_rule, beta_rule])
    beta_dec = beta.deliberate_and_resolve_federated(
        Proposal(content={"action": "b"}), evidence=[ev])
    # Tamper: change a position's reference to a fake hash
    attacker = KeyPair.generate()
    orig_pos = beta_dec.inner.positions[0]
    fake_hash = "00" * 32
    payload = canonical_bytes({
        "kind": "federated_deliberation_position",
        "member_token": orig_pos.member_token,
        "member_name": orig_pos.member_name,
        "member_public_key": orig_pos.member_public_key,
        "proposal_hash": orig_pos.proposal_hash,
        "round_num": orig_pos.round_num,
        "stance": orig_pos.stance,
        "rationale": orig_pos.rationale,
        "timestamp": orig_pos.timestamp,
        "references": [["alpha", fake_hash]],
    })
    forged = FederatedSignedPosition(
        member_token=orig_pos.member_token,
        member_name=orig_pos.member_name,
        member_public_key=orig_pos.member_public_key,
        proposal_hash=orig_pos.proposal_hash,
        round_num=orig_pos.round_num,
        stance=orig_pos.stance,
        rationale=orig_pos.rationale,
        timestamp=orig_pos.timestamp,
        signature=attacker.sign(payload).hex(),
        references=(("alpha", fake_hash),))
    tampered_inner = DeliberativeDecision(
        proposal=beta_dec.inner.proposal,
        proposal_hash=beta_dec.inner.proposal_hash,
        positions=(forged,) + beta_dec.inner.positions[1:],
        rounds_run=beta_dec.inner.rounds_run,
        converged_at_round=beta_dec.inner.converged_at_round,
        final_decision=beta_dec.inner.final_decision)
    tampered_dec = FederatedDeliberativeDecision(
        inner=tampered_inner,
        federation_evidence=beta_dec.federation_evidence)
    v = verify_federated_deliberation(
        tampered_dec, beta_keys, {"alpha": alpha_keys})
    assert not v.valid
    # Either the local verifier flags the signature (federated
    # payload doesn't match attacker's) OR the reference check
    # does; both are catches.
    assert not v.local_valid or not v.references_valid


def test_verify_federated_missing_evidence_keys():
    print("=== verify: missing evidence member keys ===")
    alpha, _ = _make_council("alpha")
    alpha_dec = alpha.deliberate_and_resolve_federated(
        Proposal(content={"action": "a"}), evidence=[])
    ev = FederationEvidence.from_decision("alpha", alpha_dec)
    def beta_rule(p, ctx): return ("yea", "", ())
    beta, beta_keys = _make_council(
        "beta", rules=[beta_rule, beta_rule, beta_rule])
    beta_dec = beta.deliberate_and_resolve_federated(
        Proposal(content={"action": "b"}), evidence=[ev])
    v = verify_federated_deliberation(
        beta_dec, beta_keys, evidence_member_keys={})  # missing
    assert not v.valid
    assert not v.evidence_valid
    assert any("no member keys" in r
                for _, r in v.evidence_errors)


# =====================================================================
# Structural claims
# =====================================================================

def test_federated_council_is_a_deliberative_council():
    print("=== FederatedDeliberativeCouncil IS-A "
          "DeliberativeCouncil ===")
    from multiverse_c45 import DeliberativeCouncil
    council, _ = _make_council()
    assert isinstance(council, DeliberativeCouncil)


def test_plain_c45_verifier_accepts_federated_inner():
    print("=== C45 verify_deliberative_decision works on inner ===")
    from multiverse_c45 import verify_deliberative_decision
    council, keys = _make_council()
    dec = council.deliberate_and_resolve_federated(
        _simple_proposal(), evidence=[])
    # The inner DeliberativeDecision is a C45 artifact
    v = verify_deliberative_decision(dec.inner, keys)
    assert v.valid


def test_backward_compat_plain_position_parses():
    print("=== Backward compat: C45 SignedPosition still works ===")
    # A plain SignedPosition should not fail in C46's machinery
    from multiverse_c45 import SignedPosition
    plain = SignedPosition(
        member_token="m", member_name="M",
        member_public_key="aa" * 32,
        proposal_hash="bb" * 32,
        round_num=0, stance="yea",
        rationale="r", timestamp="t", signature="s")
    # Not a FederatedSignedPosition
    assert not isinstance(plain, FederatedSignedPosition)


# =====================================================================
# Never raises
# =====================================================================

def test_verify_never_raises():
    print("=== verify_federated_deliberation: never raises ===")
    assert not verify_federated_deliberation(
        None, {}, {}).valid
    assert not verify_federated_deliberation(
        "not a decision", {}, {}).valid


def test_federated_position_verify_never_raises():
    print("=== verify_federated_position: never raises ===")
    ok, reason = verify_federated_position(
        None, "aa" * 32, set())
    assert not ok
    ok, reason = verify_federated_position(
        "not a position", "aa" * 32, set())
    assert not ok


# =====================================================================
# JSON roundtrips
# =====================================================================

def test_federated_position_json_roundtrip():
    print("=== FederatedSignedPosition: JSON roundtrip ===")
    council, keys = _make_council()
    member = council._members["c:m0"]
    fake_ev = {"alpha": {"decision_hash": "cc" * 32,
                          "outcome": "passed",
                          "yea": 2, "nay": 0, "abstain": 0}}
    def rule(p, ctx):
        return ("yea", "", (("alpha", "cc" * 32),))
    member._decision_rule = rule
    pos = member.produce_federated_position(
        _simple_proposal(), 0,
        context={"round_num": 0, "positions_by_member": {},
                 "federation_evidence": fake_ev},
        available_refs={("alpha", "cc" * 32)})
    wire = json.dumps(pos.to_dict())
    revived = FederatedSignedPosition.from_dict(json.loads(wire))
    assert revived.canonical_payload() == pos.canonical_payload()
    assert revived.references == pos.references


def test_federated_decision_json_roundtrip():
    print("=== FederatedDeliberativeDecision: JSON roundtrip ===")
    alpha, alpha_keys = _make_council("alpha")
    alpha_dec = alpha.deliberate_and_resolve_federated(
        Proposal(content={"a": 1}), evidence=[])
    ev = FederationEvidence.from_decision("alpha", alpha_dec)
    def beta_rule(p, ctx): return ("yea", "", ())
    beta, beta_keys = _make_council(
        "beta", rules=[beta_rule, beta_rule, beta_rule])
    beta_dec = beta.deliberate_and_resolve_federated(
        Proposal(content={"b": 1}), evidence=[ev])
    wire = json.dumps(beta_dec.to_dict())
    revived = FederatedDeliberativeDecision.from_dict(
        json.loads(wire))
    # Verify revived
    v = verify_federated_deliberation(
        revived, beta_keys, {"alpha": alpha_keys})
    assert v.valid


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: two councils, three scenarios ===")
    audit = demo(artifact_dir=str(tmp_path))
    a = audit["scenario_a_happy"]
    assert a["verified"] is True
    assert a["alpha_outcome"] == "passed"
    assert a["beta_outcome"] == "passed"
    b = audit["scenario_b_forged_reference"]
    assert b["verified"] is False
    c = audit["scenario_c_tampered_evidence"]
    assert c["verified"] is False
    assert c["evidence_error_count"] >= 1
    assert (tmp_path / "federated_deliberation_demo.json").exists()


if __name__ == "__main__":
    test_position_validates_references()
    test_position_canonical_payload_includes_refs()
    test_position_signature_verifies_with_parent_verifier()
    test_federated_position_verify_checks_references()
    test_evidence_from_decision_works()
    test_evidence_rejects_wrong_type()
    test_evidence_hash_is_content_derived()
    test_federated_member_rule_can_see_evidence()
    test_federated_member_can_return_2_tuple()
    test_verify_federated_happy()
    test_verify_federated_evidence_hash_mismatch()
    test_verify_federated_bad_inner_decision()
    test_verify_federated_forged_reference()
    test_verify_federated_missing_evidence_keys()
    test_federated_council_is_a_deliberative_council()
    test_plain_c45_verifier_accepts_federated_inner()
    test_backward_compat_plain_position_parses()
    test_verify_never_raises()
    test_federated_position_verify_never_raises()
    test_federated_position_json_roundtrip()
    test_federated_decision_json_roundtrip()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
