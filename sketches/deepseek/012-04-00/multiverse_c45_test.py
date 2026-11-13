# multiverse_c45_test.py
import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c44 import (
    Proposal, QuorumRule, Decision, verify_decision,
)
from multiverse_c45 import (
    SignedPosition, verify_position,
    DeliberativeMember, DeliberativeDecision,
    DeliberativeCouncil, DeliberativeVerdict,
    verify_deliberative_decision,
    demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _proposal(cost="low"):
    return Proposal(content={"action": "test", "cost": cost})


def _fixed(decision: str, rationale: str = ""):
    def rule(proposal, ctx):
        return (decision, rationale)
    return rule


def _make_council(
    rules=("yea", "nay", "abstain"),
    quorum=(2, 2),
    max_rounds=5,
    stability_rounds=1,
):
    """Build a council. `rules` are simple fixed stances unless
    they're callables."""
    council = DeliberativeCouncil(
        "council", QuorumRule(*quorum),
        max_rounds=max_rounds,
        stability_rounds=stability_rounds)
    keys = {}
    for i, r in enumerate(rules):
        kp = KeyPair.generate()
        rule = r if callable(r) else _fixed(r, f"rule{i}")
        member = DeliberativeMember(
            entity_id=f"member:{i}", name=f"M{i}",
            member_kp=kp, decision_rule=rule)
        council.add_member(member)
        keys[f"member:{i}"] = kp.public_key_hex()
    return council, keys


# =====================================================================
# SignedPosition
# =====================================================================

def test_position_validates_fields():
    print("=== SignedPosition: validates required fields ===")
    with pytest.raises(ValueError):
        SignedPosition(
            member_token="", member_name="M",
            member_public_key="aa" * 32,
            proposal_hash="bb" * 32,
            round_num=0, stance="yea",
            rationale="", timestamp="t", signature="s")
    with pytest.raises(ValueError):
        SignedPosition(
            member_token="m", member_name="M",
            member_public_key="aa" * 32,
            proposal_hash="bb" * 32,
            round_num=0, stance="bogus",  # not in DECISIONS
            rationale="", timestamp="t", signature="s")
    with pytest.raises(ValueError):
        SignedPosition(
            member_token="m", member_name="M",
            member_public_key="short",
            proposal_hash="bb" * 32,
            round_num=0, stance="yea",
            rationale="", timestamp="t", signature="s")


def test_position_signed_correctly():
    print("=== SignedPosition: signed by member key ===")
    council, keys = _make_council()
    member = council._members["member:0"]
    pos = member.produce_position(_proposal(), 0)
    assert verify_position(pos, keys["member:0"])


def test_position_rejects_wrong_key():
    print("=== SignedPosition: wrong key → invalid ===")
    council, keys = _make_council()
    member = council._members["member:0"]
    pos = member.produce_position(_proposal(), 0)
    wrong = KeyPair.generate()
    assert not verify_position(pos, wrong.public_key_hex())


def test_verify_position_never_raises():
    print("=== verify_position: never raises ===")
    assert not verify_position(None, "aa" * 32)
    assert not verify_position("not a position", "aa" * 32)


# =====================================================================
# DeliberativeMember — rule arity
# =====================================================================

def test_one_arg_rule_wrapped():
    print("=== DeliberativeMember: one-arg rule (C44 compat) ===")
    kp = KeyPair.generate()
    def one_arg(proposal):
        return "yea"
    member = DeliberativeMember(
        entity_id="m", name="M",
        member_kp=kp, decision_rule=one_arg)
    assert not member._rule_takes_context
    pos = member.produce_position(_proposal(), 0)
    assert pos.stance == "yea"


def test_two_arg_rule_uses_context():
    print("=== DeliberativeMember: two-arg rule sees context ===")
    kp = KeyPair.generate()
    seen_ctx = {}
    def two_arg(proposal, ctx):
        seen_ctx.update(ctx)
        return ("yea", "yes because I saw context")
    member = DeliberativeMember(
        entity_id="m", name="M",
        member_kp=kp, decision_rule=two_arg)
    assert member._rule_takes_context
    pos = member.produce_position(_proposal(), 2,
        context={"round_num": 2, "positions_by_member": {}})
    assert seen_ctx["round_num"] == 2
    assert pos.stance == "yea"
    assert "context" in pos.rationale


def test_rule_exception_yields_nay():
    print("=== DeliberativeMember: rule exception → nay ===")
    kp = KeyPair.generate()
    def bad(proposal, ctx):
        raise RuntimeError("boom")
    member = DeliberativeMember(
        entity_id="m", name="M",
        member_kp=kp, decision_rule=bad)
    pos = member.produce_position(_proposal(), 0)
    assert pos.stance == "nay"


def test_rule_bad_return_yields_abstain():
    print("=== DeliberativeMember: bad return value → abstain ===")
    kp = KeyPair.generate()
    def weird(proposal, ctx):
        return "definitely-maybe"
    member = DeliberativeMember(
        entity_id="m", name="M",
        member_kp=kp, decision_rule=weird)
    pos = member.produce_position(_proposal(), 0)
    assert pos.stance == "abstain"


# =====================================================================
# DeliberativeCouncil — stability detection
# =====================================================================

def test_stable_from_start_converges_fast():
    print("=== Council: all fixed → converges at round 1 ===")
    council, keys = _make_council(
        rules=("yea", "nay", "abstain"),
        max_rounds=10, stability_rounds=1)
    decision = council.deliberate_and_resolve(_proposal())
    # Round 0: initial. Round 1: matches round 0 → stable → stop
    assert decision.rounds_run == 2
    assert decision.converged_at_round == 1


def test_deliberation_continues_when_positions_change():
    print("=== Council: changing position extends rounds ===")
    seen = {"count": 0}
    def changing(proposal, ctx):
        seen["count"] += 1
        # Flip on each round
        return ("yea" if seen["count"] % 2 == 1 else "nay",
                f"round {ctx['round_num']}")
    council = DeliberativeCouncil(
        "c", QuorumRule(1, 1),
        max_rounds=5, stability_rounds=1)
    council.add_member(DeliberativeMember(
        "m", "M", KeyPair.generate(), changing))
    council.add_member(DeliberativeMember(
        "m2", "M2", KeyPair.generate(),
        _fixed("yea")))
    decision = council.deliberate_and_resolve(_proposal())
    # Never converges because M keeps flipping
    assert decision.converged_at_round is None
    assert decision.rounds_run == 5  # max_rounds


def test_deliberation_bounded_by_max_rounds():
    print("=== Council: max_rounds enforced ===")
    council, _ = _make_council(
        rules=("yea", "yea", "yea"),
        max_rounds=3, stability_rounds=5)  # never stabilize
    decision = council.deliberate_and_resolve(_proposal())
    assert decision.rounds_run == 3
    assert decision.converged_at_round is None


def test_members_see_prior_positions_in_context():
    print("=== Council: members see prior positions ===")
    captured = {}
    def observer(proposal, ctx):
        captured.update(ctx["positions_by_member"])
        return ("yea", "")
    council = DeliberativeCouncil(
        "c", QuorumRule(1, 1),
        max_rounds=2, stability_rounds=1)
    council.add_member(DeliberativeMember(
        "obs", "Obs", KeyPair.generate(), observer))
    council.add_member(DeliberativeMember(
        "fix", "Fix", KeyPair.generate(),
        _fixed("nay")))
    council.deliberate_and_resolve(_proposal())
    # By round 1, observer should see 'fix' as nay
    # (round 0 snapshot is empty; round 1 snapshot has round 0 entries)
    assert "fix" in captured
    assert captured["fix"]["stance"] == "nay"


# =====================================================================
# Final vote + verification
# =====================================================================

def test_final_decision_is_c44():
    print("=== Final decision: verifiable as C44 Decision ===")
    council, keys = _make_council(rules=("yea", "yea", "nay"))
    decision = council.deliberate_and_resolve(_proposal())
    # Final vote is a C44 Decision
    v = verify_decision(decision.final_decision, keys)
    assert v.valid


def test_deliberative_decision_verifies():
    print("=== DeliberativeDecision: verifies with positions + votes ===")
    council, keys = _make_council(rules=("yea", "yea", "nay"))
    decision = council.deliberate_and_resolve(_proposal())
    v = verify_deliberative_decision(decision, keys)
    assert v.valid
    assert v.positions_valid
    assert v.final_decision_valid
    assert v.rounds_match


def test_forged_position_rejected():
    print("=== Forged position → verify fails ===")
    council, keys = _make_council(rules=("yea", "nay", "abstain"))
    decision = council.deliberate_and_resolve(_proposal())
    attacker = KeyPair.generate()
    orig = decision.positions[0]
    payload = canonical_bytes({
        "kind": "deliberation_position",
        "member_token": orig.member_token,
        "member_name": orig.member_name,
        "member_public_key": orig.member_public_key,
        "proposal_hash": orig.proposal_hash,
        "round_num": orig.round_num,
        "stance": "nay",   # forged flip
        "rationale": "forged",
        "timestamp": orig.timestamp,
    })
    forged = SignedPosition(
        member_token=orig.member_token,
        member_name=orig.member_name,
        member_public_key=orig.member_public_key,
        proposal_hash=orig.proposal_hash,
        round_num=orig.round_num,
        stance="nay",
        rationale="forged",
        timestamp=orig.timestamp,
        signature=attacker.sign(payload).hex(),
    )
    tampered = DeliberativeDecision(
        proposal=decision.proposal,
        proposal_hash=decision.proposal_hash,
        positions=(forged,) + decision.positions[1:],
        rounds_run=decision.rounds_run,
        converged_at_round=decision.converged_at_round,
        final_decision=decision.final_decision,
    )
    v = verify_deliberative_decision(tampered, keys)
    assert not v.valid
    assert not v.positions_valid
    assert len(v.bad_positions) >= 1


def test_tampered_final_vote_caught():
    print("=== Tampered final vote caught by C44 verify ===")
    council, keys = _make_council(rules=("yea", "yea", "nay"))
    decision = council.deliberate_and_resolve(_proposal())
    # Swap a vote's signature
    tampered_votes = list(decision.final_decision.votes)
    v0 = tampered_votes[0]
    attacker = KeyPair.generate()
    bad_sig = attacker.sign(
        v0.canonical_payload()).hex()
    from multiverse_c44 import Vote
    tampered_vote = Vote(
        member_token=v0.member_token,
        member_name=v0.member_name,
        member_public_key=v0.member_public_key,
        proposal_hash=v0.proposal_hash,
        decision=v0.decision,
        timestamp=v0.timestamp,
        signature=bad_sig)
    tampered_votes[0] = tampered_vote
    fd = decision.final_decision
    tampered_final = Decision(
        proposal=fd.proposal,
        proposal_hash=fd.proposal_hash,
        votes=tuple(tampered_votes),
        quorum=fd.quorum,
        yea_count=fd.yea_count,
        nay_count=fd.nay_count,
        abstain_count=fd.abstain_count,
        present_count=fd.present_count,
        outcome=fd.outcome,
        timestamp=fd.timestamp)
    tampered = DeliberativeDecision(
        proposal=decision.proposal,
        proposal_hash=decision.proposal_hash,
        positions=decision.positions,
        rounds_run=decision.rounds_run,
        converged_at_round=decision.converged_at_round,
        final_decision=tampered_final)
    v = verify_deliberative_decision(tampered, keys)
    assert not v.valid
    assert not v.final_decision_valid


def test_missing_position_rejected():
    print("=== Missing position → rounds don't match ===")
    council, keys = _make_council(rules=("yea", "yea", "yea"))
    decision = council.deliberate_and_resolve(_proposal())
    tampered = DeliberativeDecision(
        proposal=decision.proposal,
        proposal_hash=decision.proposal_hash,
        positions=decision.positions[:-1],
        rounds_run=decision.rounds_run + 2,
        converged_at_round=decision.converged_at_round,
        final_decision=decision.final_decision)
    v = verify_deliberative_decision(tampered, keys)
    assert not v.valid
    assert not v.rounds_match


def test_verify_deliberative_never_raises():
    print("=== verify_deliberative_decision: never raises ===")
    assert not verify_deliberative_decision(None, {}).valid
    assert not verify_deliberative_decision(
        "not a decision", {}).valid


# =====================================================================
# JSON roundtrip
# =====================================================================

def test_deliberative_decision_json_roundtrip():
    print("=== DeliberativeDecision: JSON roundtrip ===")
    council, keys = _make_council(rules=("yea", "nay", "abstain"))
    decision = council.deliberate_and_resolve(_proposal())
    wire = json.dumps(decision.to_dict())
    revived = DeliberativeDecision.from_dict(json.loads(wire))
    v = verify_deliberative_decision(revived, keys)
    assert v.valid


# =====================================================================
# Structural claims
# =====================================================================

def test_council_can_be_used_as_triumvirate():
    """A DeliberativeCouncil IS-A Triumvirate (inherits). Its
    members ARE TriumvirateMembers. The C44 machinery still works."""
    print("=== DeliberativeCouncil is-a Triumvirate ===")
    from multiverse_c44 import Triumvirate
    council, keys = _make_council(rules=("yea", "yea", "nay"))
    assert isinstance(council, Triumvirate)
    # The C44 resolve() method still works
    c44_decision = council.resolve(_proposal())
    v = verify_decision(c44_decision, keys)
    assert v.valid


def test_deliberation_log_is_signalworld():
    print("=== Deliberation log is a SignalWorld ===")
    from multiverse_c42 import SignalWorld
    council, _ = _make_council()
    assert isinstance(council.deliberation_log(), SignalWorld)


def test_deliberation_log_has_positions():
    print("=== Deliberation log records positions ===")
    council, _ = _make_council(rules=("yea", "nay", "abstain"))
    council.deliberate_and_resolve(_proposal())
    log = council.deliberation_log().log_since(None)
    positions = [e for e in log if e.kind == "position"]
    assert len(positions) >= 3  # at least one round of three members


def test_deliberation_log_entries_well_signed():
    """Every position in the log carries a signature that matches
    the member's position."""
    print("=== Deliberation log entries signed ===")
    council, keys = _make_council(rules=("yea", "nay", "abstain"))
    decision = council.deliberate_and_resolve(_proposal())
    log_positions = [
        e for e in council.deliberation_log().log_since(None)
        if e.kind == "position"]
    # Match each log entry to a SignedPosition in the decision
    for entry in log_positions:
        member_token = entry.data["member_token"]
        # Find matching SignedPosition
        match = next(
            (p for p in decision.positions
             if p.member_token == member_token
             and p.round_num == entry.data["round_num"]
             and p.signature == entry.data["signature"]),
            None)
        assert match is not None, (
            f"log entry without matching position: "
            f"{member_token} round {entry.data['round_num']}")


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: persuasion, stability, forgery ===")
    audit = demo(artifact_dir=str(tmp_path))
    a = audit["scenario_a_persuasion"]
    assert a["verified"] is True
    assert a["final_outcome"] == "passed"
    # Gamma's stance path: abstain (round 0) then yea (round 1+)
    assert a["gamma_stance_path"][0] == "abstain"
    assert a["gamma_stance_path"][-1] == "yea"

    b = audit["scenario_b_stable"]
    assert b["verified"] is True
    assert b["final_outcome"] == "rejected"
    # Converges at round 1 (matches round 0)
    assert b["rounds_run"] == 2

    c = audit["scenario_c_forged"]
    assert c["verified"] is False
    assert c["positions_valid"] is False
    assert c["bad_position_count"] >= 1

    assert (tmp_path / "deliberation_demo.json").exists()


if __name__ == "__main__":
    test_position_validates_fields()
    test_position_signed_correctly()
    test_position_rejects_wrong_key()
    test_verify_position_never_raises()
    test_one_arg_rule_wrapped()
    test_two_arg_rule_uses_context()
    test_rule_exception_yields_nay()
    test_rule_bad_return_yields_abstain()
    test_stable_from_start_converges_fast()
    test_deliberation_continues_when_positions_change()
    test_deliberation_bounded_by_max_rounds()
    test_members_see_prior_positions_in_context()
    test_final_decision_is_c44()
    test_deliberative_decision_verifies()
    test_forged_position_rejected()
    test_tampered_final_vote_caught()
    test_missing_position_rejected()
    test_verify_deliberative_never_raises()
    test_deliberative_decision_json_roundtrip()
    test_council_can_be_used_as_triumvirate()
    test_deliberation_log_is_signalworld()
    test_deliberation_log_has_positions()
    test_deliberation_log_entries_well_signed()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
