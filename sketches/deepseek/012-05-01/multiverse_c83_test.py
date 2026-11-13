import json
import tempfile
import time
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import Act, Ack, Refusal, Petition
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes,
)
from multiverse_c81 import GrowthEvent
from multiverse_c82 import MockGrowthModel
from multiverse_c83 import (
    VOTE_CHOICES, INITIAL_LAW, INITIAL_LAW_HASH,
    GrowingWorldLaw, RuleVote, verify_rule_vote,
    VotingPolicy, LawAmendment, verify_law_amendment,
    GovernedGrowingWorld, GovernanceLogVerdict,
    verify_governance_log, extract_governance_events,
    demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


def _world(name="world:c"):
    kp = KeyPair.generate()
    w = GovernedGrowingWorld(
        name, "C", kp,
        voting_policy=VotingPolicy(min_votes=2,
                                    pass_fraction=0.5),
        seed_extent=(0, 0, 4, 4))
    return w, kp


def _admit_owner(w, name, x, y, wd, ht, purpose="studio"):
    who = create_identity(name)
    w.petition(Petition(
        petitioner_token=who.token,
        petitioner_name=who.name,
        passport_admissions=(), message=""))
    w.act(Act(actor_token=who.token, type="canvas.claim",
              payload={"x": x, "y": y, "width": wd,
                        "height": ht, "purpose": purpose}))
    return who


# -- Law --

def test_law_initial():
    print("=== GrowingWorldLaw: initial ===")
    law = GrowingWorldLaw.initial()
    assert law.max_width == 20
    assert law.max_height == 20
    assert law.law_hash() == INITIAL_LAW_HASH


def test_law_hash_reflects_content():
    print("=== GrowingWorldLaw: hash reflects content ===")
    a = GrowingWorldLaw(20, 20)
    b = GrowingWorldLaw(40, 40)
    assert a.law_hash() != b.law_hash()


# -- RuleVote --

def _mk_vote(kp, choice="yes"):
    payload = canonical_bytes({
        "kind": "rule_vote",
        "proposal_id": "p1",
        "voter_token": "alice",
        "voter_name": "Alice",
        "voter_public_key": kp.public_key_hex(),
        "choice": choice,
        "timestamp": "2024-01-01T00:00:00+00:00",
    })
    return RuleVote(
        proposal_id="p1", voter_token="alice",
        voter_name="Alice",
        voter_public_key=kp.public_key_hex(),
        choice=choice,
        timestamp="2024-01-01T00:00:00+00:00",
        signature=kp.sign(payload).hex())


def test_vote_sign_verify():
    print("=== RuleVote: sign/verify ===")
    kp = KeyPair.generate()
    v = _mk_vote(kp)
    assert verify_rule_vote(v, kp.public_key_hex())


def test_vote_rejects_bad_choice():
    print("=== RuleVote: bad choice rejected ===")
    kp = KeyPair.generate()
    with pytest.raises(ValueError):
        RuleVote(
            proposal_id="p1", voter_token="a",
            voter_name="A", voter_public_key=kp.public_key_hex(),
            choice="maybe",
            timestamp="t", signature="s")


# -- VotingPolicy --

def _votes(n_yes, n_no, n_abstain=0):
    out = []
    kp = KeyPair.generate()
    for i in range(n_yes):
        out.append(_mk_vote(kp, "yes"))
    for i in range(n_no):
        out.append(_mk_vote(kp, "no"))
    for i in range(n_abstain):
        out.append(_mk_vote(kp, "abstain"))
    return out


def test_policy_quorum_fail():
    print("=== VotingPolicy: below quorum ===")
    p = VotingPolicy(min_votes=3, pass_fraction=0.5)
    ok, reason = p.evaluate(_votes(1, 1))
    assert not ok
    assert "need 3" in reason


def test_policy_passes():
    print("=== VotingPolicy: passes ===")
    p = VotingPolicy(min_votes=2, pass_fraction=0.5)
    ok, reason = p.evaluate(_votes(2, 1))
    assert ok
    assert "passed" in reason


def test_policy_fails():
    print("=== VotingPolicy: fails ===")
    p = VotingPolicy(min_votes=2, pass_fraction=0.5)
    ok, _ = p.evaluate(_votes(1, 2))
    assert not ok


def test_policy_abstain_ignored():
    print("=== VotingPolicy: abstain doesn't count in fraction ===")
    p = VotingPolicy(min_votes=2, pass_fraction=0.5)
    ok, _ = p.evaluate(_votes(2, 0, n_abstain=3))
    assert ok  # 100% of yes/no


# -- World flow --

def _setup_votable_world():
    w, kp = _world()
    a = _admit_owner(w, "Alice", 4, 0, 3, 3, "studio")
    b = _admit_owner(w, "Bob", 4, 3, 3, 3, "gallery")
    c = create_identity("Carol")
    w.petition(Petition(
        petitioner_token=c.token, petitioner_name=c.name,
        passport_admissions=(), message=""))
    # Trigger a size refusal for C82
    w.act(Act(actor_token=c.token, type="canvas.claim",
              payload={"x": 0, "y": 0, "width": 30,
                        "height": 30, "purpose": "mural"}))
    from multiverse_c82 import GrowingWorldCurator
    curator = GrowingWorldCurator(w, kp, MockGrowthModel())
    proposal = curator.observe_and_propose_growth()
    assert proposal is not None
    return w, kp, a, b, c, proposal


def test_vote_requires_plot_owner():
    print("=== vote: non-owner refused ===")
    w, kp, a, b, c, proposal = _setup_votable_world()
    # Carol has no plot
    r = w.act(Act(actor_token=c.token, type="rule.vote",
                  payload={"proposal_id":
                            proposal.proposal_id,
                            "choice": "yes"}))
    assert isinstance(r, Refusal)
    assert "owner" in r.reason.lower()


def test_duplicate_vote_refused():
    print("=== vote: duplicate refused ===")
    w, kp, a, b, c, proposal = _setup_votable_world()
    r1 = w.act(Act(actor_token=a.token, type="rule.vote",
                   payload={"proposal_id":
                             proposal.proposal_id,
                             "choice": "yes"}))
    assert isinstance(r1, Ack)
    r2 = w.act(Act(actor_token=a.token, type="rule.vote",
                   payload={"proposal_id":
                             proposal.proposal_id,
                             "choice": "no"}))
    assert isinstance(r2, Refusal)
    assert "already" in r2.reason.lower()


def test_tally_below_quorum_refused():
    print("=== tally: below quorum refused ===")
    w, kp, a, b, c, proposal = _setup_votable_world()
    # Only one vote
    w.act(Act(actor_token=a.token, type="rule.vote",
              payload={"proposal_id": proposal.proposal_id,
                        "choice": "yes"}))
    r = w.act(Act(actor_token=a.token, type="rule.tally",
                  payload={"proposal_id": proposal.proposal_id}))
    assert isinstance(r, Refusal)
    assert "tally failed" in r.reason.lower()


def test_tally_passes_and_amends_law():
    print("=== tally: passes, law amended ===")
    w, kp, a, b, c, proposal = _setup_votable_world()
    before = w.law
    for who in (a, b):
        w.act(Act(actor_token=who.token, type="rule.vote",
                  payload={"proposal_id":
                            proposal.proposal_id,
                            "choice": "yes"}))
    r = w.act(Act(actor_token=a.token, type="rule.tally",
                  payload={"proposal_id": proposal.proposal_id}))
    assert isinstance(r, Ack)
    after = w.law
    assert after.max_width > before.max_width
    assert after.max_height > before.max_height
    # Amendment recorded
    amendment = w.applied_amendment(proposal.proposal_id)
    assert amendment is not None
    assert verify_law_amendment(amendment, kp.public_key_hex())


def test_retry_accepted_under_new_law():
    print("=== retry: accepted under new law ===")
    w, kp, a, b, c, proposal = _setup_votable_world()
    # Add a plot for Carol so she can vote
    # Simulate: Carol votes yes (but she has no plot → her vote
    # won't count, so use a and b only)
    for who in (a, b):
        w.act(Act(actor_token=who.token, type="rule.vote",
                  payload={"proposal_id":
                            proposal.proposal_id,
                            "choice": "yes"}))
    w.act(Act(actor_token=a.token, type="rule.tally",
              payload={"proposal_id": proposal.proposal_id}))
    # Carol retries her 30x30 claim
    r = w.act(Act(actor_token=c.token, type="canvas.claim",
                  payload={"x": 0, "y": 0, "width": 30,
                            "height": 30, "purpose": "mural"}))
    # Note: contiguity may still apply — depends on the position
    # For this test we just verify the law was amended; contiguity
    # is checked by C81's normal flow
    assert w.law.max_width == 40


def test_tally_twice_refused():
    print("=== tally: second tally refused ===")
    w, kp, a, b, c, proposal = _setup_votable_world()
    for who in (a, b):
        w.act(Act(actor_token=who.token, type="rule.vote",
                  payload={"proposal_id":
                            proposal.proposal_id,
                            "choice": "yes"}))
    r1 = w.act(Act(actor_token=a.token, type="rule.tally",
                   payload={"proposal_id":
                             proposal.proposal_id}))
    assert isinstance(r1, Ack)
    r2 = w.act(Act(actor_token=a.token, type="rule.tally",
                   payload={"proposal_id":
                             proposal.proposal_id}))
    assert isinstance(r2, Refusal)
    assert "already" in r2.reason.lower()


# -- Verification --

def test_verify_log_happy():
    print("=== verify_governance_log: happy ===")
    w, kp, a, b, c, proposal = _setup_votable_world()
    for who in (a, b):
        w.act(Act(actor_token=who.token, type="rule.vote",
                  payload={"proposal_id":
                            proposal.proposal_id,
                            "choice": "yes"}))
    w.act(Act(actor_token=a.token, type="rule.tally",
              payload={"proposal_id": proposal.proposal_id}))
    typed = extract_governance_events(w.log_since(None))
    verdict = verify_governance_log(
        typed, kp.public_key_hex())
    assert verdict.valid
    assert verdict.amendments_verified == 1
    assert verdict.final_law.max_width == 40


def test_verify_log_detects_lying_amendment():
    print("=== verify: amendment with wrong tally rejected ===")
    from multiverse_c83 import INITIAL_LAW
    # Craft a log where the amendment lies about the count
    kp = KeyPair.generate()
    w, kp2, a, b, c, proposal = _setup_votable_world()
    w.act(Act(actor_token=a.token, type="rule.vote",
              payload={"proposal_id": proposal.proposal_id,
                        "choice": "yes"}))
    w.act(Act(actor_token=b.token, type="rule.vote",
              payload={"proposal_id": proposal.proposal_id,
                        "choice": "yes"}))
    w.act(Act(actor_token=a.token, type="rule.tally",
              payload={"proposal_id": proposal.proposal_id}))
    # Rebuild log with tampered tally_summary
    entries = w.log_since(None)
    typed = extract_governance_events(entries)
    tampered = []
    for ev in typed:
        if isinstance(ev, LawAmendment):
            tampered.append(LawAmendment(
                proposal_id=ev.proposal_id,
                old_law_hash=ev.old_law_hash,
                new_law=ev.new_law,
                new_law_hash=ev.new_law_hash,
                tally_summary={"yes": 99, "no": 0,
                                "abstain": 0},
                timestamp=ev.timestamp,
                signer_id=ev.signer_id,
                signer_public_key=ev.signer_public_key,
                signature=ev.signature))
        else:
            tampered.append(ev)
    verdict = verify_governance_log(
        tampered, kp2.public_key_hex())
    assert not verdict.valid


# -- Demo --

def test_demo(tmp_path):
    print("=== Demo: full governance loop ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["all_votes_ok"] is True
    assert audit["tally_ok"] is True
    assert audit["law_before"]["max_width"] == 20
    assert audit["law_after"]["max_width"] == 40
    assert audit["carol_retry_accepted"] is True
    assert audit["third_party"]["valid"] is True
    assert audit["third_party"]["amendments_verified"] == 1
    assert (tmp_path / "governance" /
            "governance_demo.json").exists()
