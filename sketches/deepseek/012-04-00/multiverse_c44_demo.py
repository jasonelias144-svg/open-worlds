# multiverse_c44_demo.py

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """A three-member council with 2-of-3 quorum.

    Three scenarios:
      A. Proposal {cost: "low"}  → A yea, B yea, C nay → PASSED
      B. Proposal {cost: "high"} → A nay, B abstain, C nay → REJECTED
      C. A strict-quorum council (3-of-3) with only 2 members
         → NO_QUORUM

    Plus two negative cases:
      D. Forged vote — attacker signs a fake vote attributed to A
         → verify_decision catches it (signature INVALID)
      E. Honest votes, dishonest claim — a Decision with wrong
         counts → verify_decision catches the mismatch

    Anchor: Emily Dickinson, 'Much Madness is divinest Sense –',
    public domain — a poem about majority rule.
    """
    import json
    from pathlib import Path

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    # Three members, each with a decision rule
    member_kps = {
        "a": KeyPair.generate(),
        "b": KeyPair.generate(),
        "c": KeyPair.generate(),
    }
    # A: yea if cost is "low", else nay
    # B: yea if cost is "low", else abstain
    # C: always nay (the conservative voice)
    def rule_a(prop: Proposal) -> str:
        return "yea" if prop.content.get("cost") == "low" else "nay"
    def rule_b(prop: Proposal) -> str:
        return "yea" if prop.content.get("cost") == "low" else "abstain"
    def rule_c(prop: Proposal) -> str:
        return "nay"

    council = Triumvirate(
        "council-main",
        quorum=QuorumRule(min_yea=2, min_present=2))
    council.add_member(TriumvirateMember(
        "member:a", "Alpha", member_kps["a"], rule_a))
    council.add_member(TriumvirateMember(
        "member:b", "Beta", member_kps["b"], rule_b))
    council.add_member(TriumvirateMember(
        "member:c", "Gamma", member_kps["c"], rule_c))

    public_keys = {tok: kp.public_key_hex()
                    for tok, kp in member_kps.items()}

    # ---- Scenario A: passed ----
    proposal_a = Proposal(content={
        "action": "adopt-relay",
        "cost": "low",
    })
    decision_a = council.resolve(proposal_a)
    verdict_a = verify_decision(decision_a, public_keys)

    # ---- Scenario B: rejected ----
    proposal_b = Proposal(content={
        "action": "adopt-octopus",
        "cost": "high",
    })
    decision_b = council.resolve(proposal_b)
    verdict_b = verify_decision(decision_b, public_keys)

    # ---- Scenario C: no_quorum ----
    # Strict council with 3-of-3 quorum, only 2 members
    strict = Triumvirate(
        "council-strict",
        quorum=QuorumRule(min_yea=2, min_present=3))
    strict.add_member(TriumvirateMember(
        "member:a2", "Alpha", member_kps["a"], rule_a))
    strict.add_member(TriumvirateMember(
        "member:b2", "Beta", member_kps["b"], rule_b))
    proposal_c = Proposal(content={
        "action": "adopt-swarm",
        "cost": "low",
    })
    decision_c = strict.resolve(proposal_c)
    strict_keys = {
        "member:a2": member_kps["a"].public_key_hex(),
        "member:b2": member_kps["b"].public_key_hex(),
    }
    verdict_c = verify_decision(decision_c, strict_keys)

    # ---- Scenario D: forged vote ----
    attacker_kp = KeyPair.generate()
    # Attacker forges a vote attributed to member:a, but signs
    # with their own key
    payload = canonical_bytes({
        "kind": "vote",
        "member_token": "member:a",
        "member_name": "Alpha",
        "member_public_key": member_kps["a"].public_key_hex(),
        "proposal_hash": decision_a.proposal_hash,
        "decision": "nay",  # trying to flip A's yes to no
        "timestamp": "2024-01-01T00:00:00+00:00",
    })
    forged_vote = Vote(
        member_token="member:a",
        member_name="Alpha",
        member_public_key=member_kps["a"].public_key_hex(),
        proposal_hash=decision_a.proposal_hash,
        decision="nay",
        timestamp="2024-01-01T00:00:00+00:00",
        signature=attacker_kp.sign(payload).hex(),
    )
    # A Decision that includes the forged vote (as if the attacker
    # had tampered with the record)
    tampered_votes = (
        forged_vote,
        decision_a.votes[1],  # original B
        decision_a.votes[2],  # original C
    )
    # Recompute the *claimed* tallies to match the tampered votes
    # — i.e., the attacker also rewrote the counts
    tampered_decision = Decision(
        proposal=decision_a.proposal,
        proposal_hash=decision_a.proposal_hash,
        votes=tampered_votes,
        quorum=decision_a.quorum,
        yea_count=0,  # was 2
        nay_count=2,  # was 1
        abstain_count=0,
        present_count=3,
        outcome="rejected",  # was passed
        timestamp=decision_a.timestamp,
    )
    verdict_d = verify_decision(tampered_decision, public_keys)

    # ---- Scenario E: honest votes, dishonest claim ----
    # Take real decision_a votes, but claim the wrong counts
    dishonest_claim = Decision(
        proposal=decision_a.proposal,
        proposal_hash=decision_a.proposal_hash,
        votes=decision_a.votes,
        quorum=decision_a.quorum,
        yea_count=3,   # was 2 — inflated
        nay_count=0,   # was 1 — suppressed
        abstain_count=0,
        present_count=3,
        outcome="passed",  # same, but for wrong reasons
        timestamp=decision_a.timestamp,
    )
    verdict_e = verify_decision(dishonest_claim, public_keys)

    # ---- Print ----
    print("=" * 70)
    print("Triumvirate — council architecture")
    print("=" * 70)
    print()
    print("  Council: 3 members, quorum 2-of-3")
    print("    Alpha (member:a): yea if cost=low, else nay")
    print("    Beta  (member:b): yea if cost=low, else abstain")
    print("    Gamma (member:c): always nay")
    print()
    print("  Scenario A — Proposal {cost: low}")
    for line in decision_a.format().split("\n"):
        print(f"    {line}")
    print(f"    verified: {verdict_a.valid}")
    print()
    print("  Scenario B — Proposal {cost: high}")
    for line in decision_b.format().split("\n"):
        print(f"    {line}")
    print(f"    verified: {verdict_b.valid}")
    print()
    print("  Scenario C — Strict council (3-of-3), only 2 members")
    for line in decision_c.format().split("\n"):
        print(f"    {line}")
    print(f"    verified: {verdict_c.valid}")
    print()
    print("  Scenario D — Forged vote attributed to Alpha")
    for line in verdict_d.format().split("\n"):
        print(f"    {line}")
    print()
    print("  Scenario E — Honest votes, dishonest claimed counts")
    for line in verdict_e.format().split("\n"):
        print(f"    {line}")
    print()
    print("  What this demonstrates:")
    print("    - Every vote is signed by one member (origin-attributed).")
    print("    - Verification is recomputation, not trust in the claim.")
    print("    - A verifier with a different quorum rule gets a")
    print("      different outcome from the same votes.")
    print("    - Structural difference vs C41/C42/C43: no brain, no")
    print("      arms, no shared environment. N voters, one tally.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'Much Madness is divinest Sense –'")
    print("    'To a discerning Eye –'")
    print("    'Much Sense – the starkest Madness –'")
    print("    'Tis the Majority'")
    print("    'In this, as All, prevail –'")

    audit = {
        "scenarios": {
            "A_passed": {
                "outcome": decision_a.outcome,
                "yea": decision_a.yea_count,
                "nay": decision_a.nay_count,
                "abstain": decision_a.abstain_count,
                "verified": verdict_a.valid,
            },
            "B_rejected": {
                "outcome": decision_b.outcome,
                "yea": decision_b.yea_count,
                "nay": decision_b.nay_count,
                "abstain": decision_b.abstain_count,
                "verified": verdict_b.valid,
            },
            "C_no_quorum": {
                "outcome": decision_c.outcome,
                "verified": verdict_c.valid,
            },
            "D_forged_vote": {
                "verified": verdict_d.valid,
                "bad_vote_count": len(verdict_d.bad_votes),
            },
            "E_dishonest_claim": {
                "verified": verdict_e.valid,
                "tallies_match": verdict_e.tallies_match,
            },
        },
        "member_public_keys": public_keys,
    }
    if artifact_dir:
        path = Path(artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "triumvirate_demo.json").write_text(
            json.dumps(audit, indent=2))
        print(f"\n  → {path}/triumvirate_demo.json")
    return audit
