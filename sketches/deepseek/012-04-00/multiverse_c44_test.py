import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c42 import SignalWorld
from multiverse_c44 import (
    Proposal, Vote, DECISIONS, verify_vote,
    QuorumRule, TriumvirateMember, Decision,
    Triumvirate, DecisionVerdict, verify_decision,
    demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _make_council(n=3, quorum=(2, 2)):
    """Council with n members; each votes yea by default."""
    council = Triumvirate(
        "council", QuorumRule(*quorum))
    members = {}
    for i in range(n):
        tok = f"member:{i}"
        kp = KeyPair.generate()
        member = TriumvirateMember(
            entity_id=tok, name=f"M{i}",
            member_kp=kp,
            decision_rule=lambda p: "yea")
        council.add_member(member)
        members[tok] = kp
    return council, members


def _public_keys(members):
    return {tok: kp.public_key_hex() for tok, kp in members.items()}


def _proposal(cost="low"):
    return Proposal(content={"action": "test", "cost": cost})


# =====================================================================
# Proposal
# =====================================================================

def test_proposal_validates_content_type():
    print("=== Proposal: content must be dict ===")
    with pytest.raises(ValueError):
        Proposal(content="not a dict")
    with pytest.raises(ValueError):
        Proposal(content=None)


def test_proposal_hash_is_deterministic():
    print("=== Proposal: hash is deterministic ===")
    p1 = Proposal(content={"a": 1, "b": 2})
    p2 = Proposal(content={"b": 2, "a": 1})  # key order differs
    assert p1.hash() == p2.hash()


def test_proposal_hash_differs_on_content():
    print("=== Proposal: different content → different hash ===")
    p1 = Proposal(content={"a": 1})
    p2 = Proposal(content={"a": 2})
    assert p1.hash() != p2.hash()


# =====================================================================
# Vote
# =====================================================================

def test_vote_validates_decision():
    print("=== Vote: decision must be yea/nay/abstain ===")
    with pytest.raises(ValueError):
        Vote(
            member_token="m", member_name="M",
            member_public_key="aa" * 32,
            proposal_hash="bb" * 32,
            decision="maybe",  # invalid
            timestamp="t", signature="s")


def test_vote_validates_fields():
    print("=== Vote: required fields validated ===")
    with pytest.raises(ValueError):
        Vote(
            member_token="", member_name="M",
            member_public_key="aa" * 32,
            proposal_hash="bb" * 32,
            decision="yea",
            timestamp="t", signature="s")
    with pytest.raises(ValueError):
        Vote(
            member_token="m", member_name="M",
            member_public_key="short",  # not 64
            proposal_hash="bb" * 32,
            decision="yea",
            timestamp="t", signature="s")


def test_vote_signed_correctly():
    print("=== Vote: signed correctly verifies ===")
    council, members = _make_council(n=1)
    proposal = _proposal()
    member = next(iter(council._members.values()))
    vote = member.cast_vote(proposal)
    kp = members[member.member_token]
    assert verify_vote(vote, kp.public_key_hex())


def test_vote_rejects_wrong_key():
    print("=== Vote: wrong key → verification fails ===")
    council, members = _make_council(n=1)
    proposal = _proposal()
    member = next(iter(council._members.values()))
    vote = member.cast_vote(proposal)
    wrong_kp = KeyPair.generate()
    assert not verify_vote(vote, wrong_kp.public_key_hex())


def test_vote_verify_never_raises():
    print("=== verify_vote: never raises on bad input ===")
    assert not verify_vote(None, "aa" * 32)
    assert not verify_vote("not a vote", "aa" * 32)
    assert not verify_vote({}, "aa" * 32)


# =====================================================================
# QuorumRule
# =====================================================================

def test_quorum_rule_validates():
    print("=== QuorumRule: validates its constraints ===")
    with pytest.raises(ValueError):
        QuorumRule(min_yea=0, min_present=1)
    with pytest.raises(ValueError):
        QuorumRule(min_yea=1, min_present=0)
    with pytest.raises(ValueError):
        QuorumRule(min_yea=3, min_present=2)  # yea > present


# =====================================================================
# Member
# =====================================================================

def test_member_decision_rule_exception_yields_nay():
    print("=== Member: decision rule exception → nay ===")
    kp = KeyPair.generate()
    def bad_rule(p):
        raise RuntimeError("boom")
    member = TriumvirateMember(
        entity_id="m", name="M",
        member_kp=kp, decision_rule=bad_rule)
    vote = member.cast_vote(_proposal())
    assert vote.decision == "nay"


def test_member_decision_rule_bad_return_yields_abstain():
    print("=== Member: bad return value → abstain ===")
    kp = KeyPair.generate()
    def weird_rule(p):
        return "definitely-maybe"
    member = TriumvirateMember(
        entity_id="m", name="M",
        member_kp=kp, decision_rule=weird_rule)
    vote = member.cast_vote(_proposal())
    assert vote.decision == "abstain"


def test_member_is_wcp_world():
    print("=== Member: is WCP world (conformance) ===")
    from wcp_conformance import run_conformance
    kp = KeyPair.generate()
    member = TriumvirateMember(
        entity_id="m", name="M",
        member_kp=kp, decision_rule=lambda p: "yea")
    assert run_conformance(member)["passed"]


# =====================================================================
# Triumvirate — outcomes
# =====================================================================

def test_passed_when_yea_meets_min():
    print("=== Triumvirate: passed when yea >= min_yea ===")
    council, members = _make_council(n=3, quorum=(2, 2))
    # All vote yea
    decision = council.resolve(_proposal())
    assert decision.outcome == "passed"
    assert decision.yea_count == 3


def test_rejected_when_yea_below_min():
    print("=== Triumvirate: rejected when yea < min_yea ===")
    council = Triumvirate("c", QuorumRule(min_yea=2, min_present=2))
    kps = [KeyPair.generate() for _ in range(3)]
    rules = [lambda p: "yea", lambda p: "nay", lambda p: "nay"]
    for i in range(3):
        council.add_member(TriumvirateMember(
            entity_id=f"m:{i}", name=f"M{i}",
            member_kp=kps[i], decision_rule=rules[i]))
    decision = council.resolve(_proposal())
    assert decision.outcome == "rejected"
    assert decision.yea_count == 1
    assert decision.nay_count == 2


def test_no_quorum_when_present_below_min():
    print("=== Triumvirate: no_quorum when present < min_present ===")
    council = Triumvirate("c",
                            QuorumRule(min_yea=2, min_present=3))
    # Only 2 members
    for i in range(2):
        council.add_member(TriumvirateMember(
            entity_id=f"m:{i}", name=f"M{i}",
            member_kp=KeyPair.generate(),
            decision_rule=lambda p: "yea"))
    decision = council.resolve(_proposal())
    assert decision.outcome == "no_quorum"
    assert decision.present_count == 2


def test_abstain_counts_as_present_not_yea():
    print("=== Triumvirate: abstain counts as present, not yea ===")
    council = Triumvirate("c", QuorumRule(min_yea=2, min_present=2))
    rules = [lambda p: "yea", lambda p: "abstain", lambda p: "nay"]
    for i in range(3):
        council.add_member(TriumvirateMember(
            entity_id=f"m:{i}", name=f"M{i}",
            member_kp=KeyPair.generate(),
            decision_rule=rules[i]))
    decision = council.resolve(_proposal())
    assert decision.present_count == 3
    assert decision.yea_count == 1
    assert decision.abstain_count == 1
    assert decision.outcome == "rejected"


# =====================================================================
# Triumvirate — member management
# =====================================================================

def test_add_and_remove_members():
    print("=== Triumvirate: add/remove members ===")
    council, members = _make_council(n=3)
    assert council.member_count() == 3
    council.remove_member("member:0")
    assert council.member_count() == 2


def test_failed_member_is_absent():
    print("=== Triumvirate: failed member → absent, no raise ===")
    council = Triumvirate("c", QuorumRule(1, 1))
    kp = KeyPair.generate()
    def raising_rule(p):
        raise RuntimeError("boom")
    # cast_vote catches the rule exception → produces a nay vote,
    # so the member still votes. To simulate *absence* we'd need
    # cast_vote to fail. Test the resiliency claim: an exception
    # in cast_vote itself doesn't crash resolve.
    class BrokenMember(TriumvirateMember):
        def cast_vote(self, proposal):
            raise RuntimeError("cast failure")
    council.add_member(BrokenMember(
        entity_id="broken", name="Broken",
        member_kp=kp, decision_rule=lambda p: "yea"))
    decision = council.resolve(_proposal())
    assert decision.present_count == 0
    assert decision.outcome == "no_quorum"


# =====================================================================
# verify_decision — the recomputation
# =====================================================================

def test_verify_decision_happy():
    print("=== verify_decision: valid decision → valid ===")
    council, members = _make_council(n=3)
    decision = council.resolve(_proposal())
    v = verify_decision(decision, _public_keys(members))
    assert v.valid
    assert v.tallies_match
    assert v.outcome_matches


def test_verify_decision_proposal_hash_mismatch():
    print("=== verify_decision: proposal_hash mismatch ===")
    council, members = _make_council(n=3)
    decision = council.resolve(_proposal())
    # Replace proposal content, keep hash → mismatch
    tampered = Decision(
        proposal={"action": "different", "cost": "low"},
        proposal_hash=decision.proposal_hash,
        votes=decision.votes,
        quorum=decision.quorum,
        yea_count=decision.yea_count,
        nay_count=decision.nay_count,
        abstain_count=decision.abstain_count,
        present_count=decision.present_count,
        outcome=decision.outcome,
        timestamp=decision.timestamp,
    )
    v = verify_decision(tampered, _public_keys(members))
    assert not v.valid
    assert "proposal_hash" in v.reason


def test_verify_decision_forged_vote():
    print("=== verify_decision: forged vote → invalid ===")
    council, members = _make_council(n=3)
    decision = council.resolve(_proposal())
    # Replace one vote with one signed by the wrong key
    attacker = KeyPair.generate()
    original = decision.votes[0]
    payload = canonical_bytes({
        "kind": "vote",
        "member_token": original.member_token,
        "member_name": original.member_name,
        "member_public_key": original.member_public_key,
        "proposal_hash": original.proposal_hash,
        "decision": "nay",
        "timestamp": original.timestamp,
    })
    forged = Vote(
        member_token=original.member_token,
        member_name=original.member_name,
        member_public_key=original.member_public_key,
        proposal_hash=original.proposal_hash,
        decision="nay",
        timestamp=original.timestamp,
        signature=attacker.sign(payload).hex(),
    )
    tampered = Decision(
        proposal=decision.proposal,
        proposal_hash=decision.proposal_hash,
        votes=(forged,) + decision.votes[1:],
        quorum=decision.quorum,
        yea_count=decision.yea_count,
        nay_count=decision.nay_count,
        abstain_count=decision.abstain_count,
        present_count=decision.present_count,
        outcome=decision.outcome,
        timestamp=decision.timestamp,
    )
    v = verify_decision(tampered, _public_keys(members))
    assert not v.valid
    assert len(v.bad_votes) == 1
    assert "INVALID" in v.bad_votes[0][1]


def test_verify_decision_tampered_decision_field():
    print("=== verify_decision: tampered vote field breaks signature ===")
    council, members = _make_council(n=3)
    decision = council.resolve(_proposal())
    orig = decision.votes[0]
    # Change decision to "nay" but keep original signature
    tampered_vote = Vote(
        member_token=orig.member_token,
        member_name=orig.member_name,
        member_public_key=orig.member_public_key,
        proposal_hash=orig.proposal_hash,
        decision="nay",  # was "yea"
        timestamp=orig.timestamp,
        signature=orig.signature,
    )
    tampered = Decision(
        proposal=decision.proposal,
        proposal_hash=decision.proposal_hash,
        votes=(tampered_vote,) + decision.votes[1:],
        quorum=decision.quorum,
        yea_count=decision.yea_count,
        nay_count=decision.nay_count,
        abstain_count=decision.abstain_count,
        present_count=decision.present_count,
        outcome=decision.outcome,
        timestamp=decision.timestamp,
    )
    v = verify_decision(tampered, _public_keys(members))
    assert not v.valid
    assert len(v.bad_votes) == 1


def test_verify_decision_wrong_proposal_hash_on_vote():
    print("=== verify_decision: vote's proposal_hash mismatch ===")
    council, members = _make_council(n=3)
    decision = council.resolve(_proposal())
    orig = decision.votes[0]
    tampered_vote = Vote(
        member_token=orig.member_token,
        member_name=orig.member_name,
        member_public_key=orig.member_public_key,
        proposal_hash="00" * 32,  # different
        decision=orig.decision,
        timestamp=orig.timestamp,
        signature=orig.signature,
    )
    tampered = Decision(
        proposal=decision.proposal,
        proposal_hash=decision.proposal_hash,
        votes=(tampered_vote,) + decision.votes[1:],
        quorum=decision.quorum,
        yea_count=decision.yea_count,
        nay_count=decision.nay_count,
        abstain_count=decision.abstain_count,
        present_count=decision.present_count,
        outcome=decision.outcome,
        timestamp=decision.timestamp,
    )
    v = verify_decision(tampered, _public_keys(members))
    assert not v.valid
    assert any("proposal_hash" in r for _, r in v.bad_votes)


def test_verify_decision_missing_member_key():
    print("=== verify_decision: missing member key → bad vote ===")
    council, members = _make_council(n=3)
    decision = council.resolve(_proposal())
    keys = _public_keys(members)
    del keys["member:0"]
    v = verify_decision(decision, keys)
    assert not v.valid
    assert any("no public key" in r for _, r in v.bad_votes)


def test_verify_decision_duplicate_member():
    print("=== verify_decision: duplicate member → invalid ===")
    council, members = _make_council(n=3)
    decision = council.resolve(_proposal())
    # Duplicate the first vote
    tampered = Decision(
        proposal=decision.proposal,
        proposal_hash=decision.proposal_hash,
        votes=(decision.votes[0], decision.votes[0])
              + decision.votes[1:],
        quorum=decision.quorum,
        yea_count=decision.yea_count + 1,
        nay_count=decision.nay_count,
        abstain_count=decision.abstain_count,
        present_count=decision.present_count + 1,
        outcome=decision.outcome,
        timestamp=decision.timestamp,
    )
    v = verify_decision(tampered, _public_keys(members))
    assert not v.valid
    assert len(v.duplicate_members) == 1


def test_verify_decision_tallies_mismatch():
    print("=== verify_decision: dishonest counts → mismatch ===")
    council, members = _make_council(n=3)
    decision = council.resolve(_proposal())
    # Same votes, wrong claimed counts
    dishonest = Decision(
        proposal=decision.proposal,
        proposal_hash=decision.proposal_hash,
        votes=decision.votes,
        quorum=decision.quorum,
        yea_count=1,  # was 3
        nay_count=2,  # was 0
        abstain_count=0,
        present_count=3,
        outcome="rejected",  # was passed
        timestamp=decision.timestamp,
    )
    v = verify_decision(dishonest, _public_keys(members))
    assert not v.valid
    assert not v.tallies_match


def test_verify_decision_outcome_mismatch():
    print("=== verify_decision: wrong outcome with right tallies ===")
    council, members = _make_council(n=3)
    decision = council.resolve(_proposal())
    # Same votes, right tallies, wrong outcome claim
    dishonest = Decision(
        proposal=decision.proposal,
        proposal_hash=decision.proposal_hash,
        votes=decision.votes,
        quorum=decision.quorum,
        yea_count=decision.yea_count,
        nay_count=decision.nay_count,
        abstain_count=decision.abstain_count,
        present_count=decision.present_count,
        outcome="rejected",  # was passed
        timestamp=decision.timestamp,
    )
    v = verify_decision(dishonest, _public_keys(members))
    assert not v.valid
    assert v.tallies_match
    assert not v.outcome_matches


def test_verify_decision_stricter_quorum_override():
    """A verifier with a stricter quorum rule recomputes a
    different outcome from the same votes."""
    print("=== verify_decision: stricter quorum override ===")
    council, members = _make_council(n=3, quorum=(2, 2))
    # 2 yea, 1 nay → passed under 2-of-2
    decision = council.resolve(_proposal())
    assert decision.outcome == "passed"
    # Verify under a stricter rule: 3-of-3
    stricter = QuorumRule(min_yea=3, min_present=3)
    v = verify_decision(
        decision, _public_keys(members), quorum=stricter)
    assert not v.valid
    assert v.tallies_match  # tallies are fine
    assert not v.outcome_matches  # outcome recomputed differently


def test_verify_decision_never_raises():
    print("=== verify_decision: never raises ===")
    assert not verify_decision(None, {}).valid
    assert not verify_decision("not a decision", {}).valid


# =====================================================================
# JSON roundtrips
# =====================================================================

def test_vote_json_roundtrip():
    print("=== Vote: JSON roundtrip ===")
    council, members = _make_council(n=1)
    member = next(iter(council._members.values()))
    vote = member.cast_vote(_proposal())
    wire = json.dumps(vote.to_dict())
    revived = Vote.from_dict(json.loads(wire))
    kp = members[member.member_token]
    assert verify_vote(revived, kp.public_key_hex())


def test_decision_json_roundtrip():
    print("=== Decision: JSON roundtrip ===")
    council, members = _make_council(n=3)
    decision = council.resolve(_proposal())
    wire = json.dumps(decision.to_dict())
    revived = Decision.from_dict(json.loads(wire))
    v = verify_decision(revived, _public_keys(members))
    assert v.valid


# =====================================================================
# Structural differences from C41 / C42 / C43
# =====================================================================

def test_member_has_no_c41_attrs():
    print("=== Member: no C41/C42/C43 attrs ===")
    kp = KeyPair.generate()
    member = TriumvirateMember(
        entity_id="m", name="M",
        member_kp=kp, decision_rule=lambda p: "yea")
    # No arm/brain attrs
    for attr in ("_model", "_intent_queue", "_arms"):
        assert not hasattr(member, attr), attr
    # No relay attrs
    for attr in ("_inputs", "_threshold", "_out_kind"):
        assert not hasattr(member, attr), attr
    # No swarm attrs
    for attr in ("_env_stream", "_position", "_known_food"):
        assert not hasattr(member, attr), attr


def test_member_has_vote_attrs():
    print("=== Member: has vote-specific attrs ===")
    kp = KeyPair.generate()
    member = TriumvirateMember(
        entity_id="m", name="M",
        member_kp=kp, decision_rule=lambda p: "yea")
    assert hasattr(member, "_member_kp")
    assert hasattr(member, "_member_public_key")
    assert hasattr(member, "_decision_rule")


def test_council_is_not_a_world():
    print("=== Council: not a WCP world, is an orchestrator ===")
    council, _ = _make_council(n=2)
    assert not hasattr(council, "manifest")
    assert not hasattr(council, "petition")
    # Has the orchestrator shape
    assert hasattr(council, "_members")
    assert hasattr(council, "_quorum")


def test_council_and_octopus_different_structures():
    print("=== Council vs Octopus: different orchestrator shapes ===")
    from multiverse_c41 import Octopus
    from multiverse_c36 import create_person

    aria, aria_kp = create_person("Aria")
    octo = Octopus("Aria-Octo", aria, aria_kp)
    council, _ = _make_council(n=3)

    # Octopus: has arms dict, has brain
    assert hasattr(octo, "_arms")
    assert hasattr(octo, "_brain")
    # Council: has members dict, has quorum; no brain
    assert hasattr(council, "_members")
    assert hasattr(council, "_quorum")
    assert not hasattr(council, "_brain")


def test_all_four_architectures_same_substrate():
    """The substrate supports all four. Conformance is architecture-
    agnostic."""
    print("=== Four architectures, one substrate ===")
    from wcp_conformance import run_conformance
    from multiverse_c41 import Arm
    from multiverse_c42 import RelayUnit, Stream, SignalWorld
    from multiverse_c43 import SwarmUnit
    from multiverse_c1 import create_identity

    class StubModel:
        def generate(self, prompt):
            return "x"

    # C41 arm
    arm = Arm(
        name="a", world_id="world:a", dag_id="dag:a",
        model_backend=StubModel(),
        arm_report_kp=KeyPair.generate(),
        arm_report_identity=create_identity("r"),
        arm_dag_kp=KeyPair.generate(),
        arm_dag_identity=create_identity("d"))

    # C42 relay neuron
    stim = SignalWorld("world:s", "S")
    neuron = RelayUnit(
        "world:n", "N", [Stream(stim)], threshold=1.0)

    # C43 swarm unit
    env = SignalWorld("world:e", "E")
    swarm = SwarmUnit(
        entity_id="world:u", name="U",
        env_stream=Stream(env),
        initial_position=(0, 0),
        seed=0, sample_probability=0.0)

    # C44 council member
    member = TriumvirateMember(
        entity_id="m", name="M",
        member_kp=KeyPair.generate(),
        decision_rule=lambda p: "yea")

    for name, e in [
        ("C41 arm", arm),
        ("C42 relay", neuron),
        ("C43 swarm", swarm),
        ("C44 member", member),
    ]:
        assert run_conformance(e)["passed"], name
        print(f"  ✓ {name}")


# =====================================================================
# End-to-end
# =====================================================================

def test_end_to_end_passed_and_verified():
    """A realistic flow: propose, resolve, verify, JSON roundtrip,
    verify again."""
    print("=== End-to-end: propose → resolve → verify → transport → verify ===")
    council, members = _make_council(n=3, quorum=(2, 2))
    proposal = Proposal(content={"action": "adopt-relay", "cost": "low"})
    decision = council.resolve(proposal)
    assert decision.outcome == "passed"

    v1 = verify_decision(decision, _public_keys(members))
    assert v1.valid

    # Transport via JSON
    wire = json.dumps(decision.to_dict())
    revived = Decision.from_dict(json.loads(wire))

    v2 = verify_decision(revived, _public_keys(members))
    assert v2.valid


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: passed, rejected, no_quorum, forged, dishonest ===")
    audit = demo(artifact_dir=str(tmp_path))
    s = audit["scenarios"]
    assert s["A_passed"]["outcome"] == "passed"
    assert s["A_passed"]["verified"] is True
    assert s["B_rejected"]["outcome"] == "rejected"
    assert s["B_rejected"]["verified"] is True
    assert s["C_no_quorum"]["outcome"] == "no_quorum"
    assert s["C_no_quorum"]["verified"] is True
    assert s["D_forged_vote"]["verified"] is False
    assert s["D_forged_vote"]["bad_vote_count"] == 1
    assert s["E_dishonest_claim"]["verified"] is False
    assert s["E_dishonest_claim"]["tallies_match"] is False
    assert (tmp_path / "triumvirate_demo.json").exists()


if __name__ == "__main__":
    test_proposal_validates_content_type()
    test_proposal_hash_is_deterministic()
    test_proposal_hash_differs_on_content()
    test_vote_validates_decision()
    test_vote_validates_fields()
    test_vote_signed_correctly()
    test_vote_rejects_wrong_key()
    test_vote_verify_never_raises()
    test_quorum_rule_validates()
    test_member_decision_rule_exception_yields_nay()
    test_member_decision_rule_bad_return_yields_abstain()
    test_member_is_wcp_world()
    test_passed_when_yea_meets_min()
    test_rejected_when_yea_below_min()
    test_no_quorum_when_present_below_min()
    test_abstain_counts_as_present_not_yea()
    test_add_and_remove_members()
    test_failed_member_is_absent()
    test_verify_decision_happy()
    test_verify_decision_proposal_hash_mismatch()
    test_verify_decision_forged_vote()
    test_verify_decision_tampered_decision_field()
    test_verify_decision_wrong_proposal_hash_on_vote()
    test_verify_decision_missing_member_key()
    test_verify_decision_duplicate_member()
    test_verify_decision_tallies_mismatch()
    test_verify_decision_outcome_mismatch()
    test_verify_decision_stricter_quorum_override()
    test_verify_decision_never_raises()
    test_vote_json_roundtrip()
    test_decision_json_roundtrip()
    test_member_has_no_c41_attrs()
    test_member_has_vote_attrs()
    test_council_is_not_a_world()
    test_council_and_octopus_different_structures()
    test_all_four_architectures_same_substrate()
    test_end_to_end_passed_and_verified()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
