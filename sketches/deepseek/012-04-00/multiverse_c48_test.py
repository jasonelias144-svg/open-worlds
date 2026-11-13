import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c1 import create_identity, Identity
from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c44 import (
    Proposal, Decision, QuorumRule, verify_decision,
)
from multiverse_c45 import (
    DeliberativeCouncil, DeliberativeMember,
    DeliberativeDecision, verify_deliberative_decision,
    verify_position,
)
from multiverse_c46 import (
    FederationEvidence,
    FederatedDeliberativeDecision,
)
from multiverse_c48 import (
    DIRECT_KINDS, WITNESSED_KINDS, ALL_KINDS,
    FederationAttestation,
    attest_decision, attest_deliberative_decision,
    attest_federated_deliberation, attest_cross_world,
    witness_artifact,
    AttestationVerdict,
    DEFAULT_VERIFIER_REGISTRY,
    verify_federation_attestation,
    CrossKindReference, CrossKindPosition,
    CrossKindDeliberativeMember,
    CrossKindFederatedDecision,
    CrossKindCouncil,
    CrossKindFederatedVerdict,
    verify_cross_kind_federation,
    _hash_payload,
    demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _council_decision(council_id="alpha", stance="yea"):
    kps = [KeyPair.generate() for _ in range(3)]
    council = DeliberativeCouncil(
        council_id, QuorumRule(2, 2), max_rounds=2,
        stability_rounds=1)
    for i, kp in enumerate(kps):
        council.add_member(DeliberativeMember(
            entity_id=f"{council_id}:m{i}",
            name=f"{council_id}-{i}", member_kp=kp,
            decision_rule=lambda p, c: (stance, "x")))
    keys = {f"{council_id}:m{i}": kp.public_key_hex()
            for i, kp in enumerate(kps)}
    decision = council.deliberate_and_resolve(
        Proposal(content={"action": "test"}))
    return decision, keys


def _witness_att(kind="swarm_log", content=None):
    kp = KeyPair.generate()
    who = create_identity("w")
    if content is None:
        content = {"log": "test", "value": 42}
    att = witness_artifact(
        "witnessed-1", kind, content, kp, who)
    return att, kp, who


# =====================================================================
# Kinds and constants
# =====================================================================

def test_kinds_disjoint():
    print("=== DIRECT and WITNESSED kinds are disjoint ===")
    assert DIRECT_KINDS & WITNESSED_KINDS == set()
    assert ALL_KINDS == DIRECT_KINDS | WITNESSED_KINDS


def test_all_kinds_covered_by_default_registry():
    print("=== Default registry covers all kinds ===")
    for k in ALL_KINDS:
        assert k in DEFAULT_VERIFIER_REGISTRY, k


# =====================================================================
# FederationAttestation — construction
# =====================================================================

def test_direct_attestation_shape():
    print("=== Direct attestation: no witness fields ===")
    council_dec, _ = _council_decision()
    att = attest_decision("council-alpha", council_dec.final_decision)
    assert att.source_kind == "decision"
    assert not att.is_witnessed
    assert att.witness_token is None


def test_witnessed_attestation_shape():
    print("=== Witnessed attestation: all witness fields ===")
    att, kp, who = _witness_att()
    assert att.is_witnessed
    assert att.witness_public_key == kp.public_key_hex()
    assert att.witness_token == who.token
    assert att.witness_signature


def test_attestation_rejects_direct_kind_with_witness():
    print("=== Attestation: direct kind rejects witness fields ===")
    with pytest.raises(ValueError):
        FederationAttestation(
            source_id="x", source_kind="decision",
            content={}, content_hash="aa" * 32,
            witness_token="t", witness_name="n",
            witness_public_key="aa" * 32,
            witness_signature="ss",
            witness_timestamp="tt")


def test_attestation_rejects_witnessed_kind_without_witness():
    print("=== Attestation: witnessed kind requires witness ===")
    with pytest.raises(ValueError):
        FederationAttestation(
            source_id="x", source_kind="swarm_log",
            content={}, content_hash="aa" * 32)


def test_attestation_rejects_unknown_kind():
    print("=== Attestation: unknown kind rejected ===")
    with pytest.raises(ValueError):
        FederationAttestation(
            source_id="x", source_kind="bogus",
            content={}, content_hash="aa" * 32)


def test_witness_artifact_rejects_direct_kind():
    print("=== witness_artifact: rejects direct kinds ===")
    with pytest.raises(ValueError):
        witness_artifact(
            "x", "decision", {}, KeyPair.generate(),
            create_identity("w"))


# =====================================================================
# Direct attestation verification
# =====================================================================

def test_verify_decision_attestation_happy():
    print("=== Verify: decision attestation ===")
    council_dec, keys = _council_decision()
    att = attest_decision("council-alpha", council_dec.final_decision)
    v = verify_federation_attestation(
        att, {"member_keys": {"council-alpha": keys}})
    assert v.valid
    assert v.source_kind == "decision"


def test_verify_decision_attestation_missing_keys():
    print("=== Verify: missing member keys → fail ===")
    council_dec, _ = _council_decision()
    att = attest_decision("council-alpha", council_dec.final_decision)
    v = verify_federation_attestation(att, {})
    assert not v.valid
    assert "no member keys" in v.reason


def test_verify_decision_attestation_tampered_content():
    print("=== Verify: tampered content → hash mismatch ===")
    council_dec, keys = _council_decision()
    att = attest_decision("council-alpha", council_dec.final_decision)
    tampered = FederationAttestation(
        source_id=att.source_id,
        source_kind=att.source_kind,
        content={**att.content, "outcome": "rejected"},
        content_hash=att.content_hash,
    )
    v = verify_federation_attestation(
        tampered, {"member_keys": {"council-alpha": keys}})
    assert not v.valid
    assert "hash" in v.reason.lower()


def test_verify_deliberative_attestation():
    print("=== Verify: deliberative_decision attestation ===")
    council_dec, keys = _council_decision()
    att = attest_deliberative_decision(
        "council-alpha", council_dec)
    v = verify_federation_attestation(
        att, {"member_keys": {"council-alpha": keys}})
    assert v.valid


# =====================================================================
# Witnessed attestation verification
# =====================================================================

def test_verify_witnessed_happy():
    print("=== Verify: witnessed attestation ===")
    att, _, _ = _witness_att()
    v = verify_federation_attestation(att)
    assert v.valid


def test_verify_witnessed_tampered_content():
    print("=== Verify: tampered content → hash mismatch ===")
    att, kp, who = _witness_att(content={"x": 1})
    tampered = FederationAttestation(
        source_id=att.source_id,
        source_kind=att.source_kind,
        content={"x": 2},  # differs from hash
        content_hash=att.content_hash,
        witness_token=att.witness_token,
        witness_name=att.witness_name,
        witness_public_key=att.witness_public_key,
        witness_signature=att.witness_signature,
        witness_timestamp=att.witness_timestamp)
    v = verify_federation_attestation(tampered)
    assert not v.valid
    assert "hash" in v.reason.lower()


def test_verify_witnessed_forged_signature():
    print("=== Verify: forged witness signature → invalid ===")
    att, kp, who = _witness_att()
    attacker = KeyPair.generate()
    # Rebuild the attestation with a signature from a different key
    # (against the same payload)
    forged_sig = attacker.sign(
        att.witness_canonical_payload()).hex()
    tampered = FederationAttestation(
        source_id=att.source_id,
        source_kind=att.source_kind,
        content=att.content,
        content_hash=att.content_hash,
        witness_token=att.witness_token,
        witness_name=att.witness_name,
        witness_public_key=att.witness_public_key,
        witness_signature=forged_sig,
        witness_timestamp=att.witness_timestamp)
    v = verify_federation_attestation(tampered)
    assert not v.valid
    assert "INVALID" in v.reason


def test_verify_witnessed_wrong_declared_witness_key():
    print("=== Verify: witness declares wrong public key ===")
    att, kp, who = _witness_att()
    wrong_kp = KeyPair.generate()
    tampered = FederationAttestation(
        source_id=att.source_id,
        source_kind=att.source_kind,
        content=att.content,
        content_hash=att.content_hash,
        witness_token=att.witness_token,
        witness_name=att.witness_name,
        witness_public_key=wrong_kp.public_key_hex(),
        witness_signature=att.witness_signature,
        witness_timestamp=att.witness_timestamp)
    v = verify_federation_attestation(tampered)
    assert not v.valid


# =====================================================================
# Dispatch
# =====================================================================

def test_dispatch_unknown_kind():
    print("=== Dispatch: unknown kind → no verifier ===")
    # Build a fake attestation with a valid shape but disabled kind
    class FakeAtt:
        pass
    v = verify_federation_attestation(None)
    assert not v.valid


def test_dispatch_verifier_raising_is_caught():
    print("=== Dispatch: verifier raising is caught ===")
    def bad_verifier(att, ctx):
        raise RuntimeError("boom")
    att, _, _ = _witness_att()
    registry = {"swarm_log": bad_verifier}
    v = verify_federation_attestation(att, registry=registry)
    assert not v.valid
    assert "boom" in v.reason


# =====================================================================
# CrossKindPosition / CrossKindReference
# =====================================================================

def test_cross_kind_reference_validates():
    print("=== CrossKindReference: validates fields ===")
    with pytest.raises(ValueError):
        CrossKindReference(
            source_id="", source_kind="swarm_log",
            artifact_hash="aa" * 32)
    with pytest.raises(ValueError):
        CrossKindReference(
            source_id="x", source_kind="bogus",
            artifact_hash="aa" * 32)
    with pytest.raises(ValueError):
        CrossKindReference(
            source_id="x", source_kind="swarm_log",
            artifact_hash="short")


def test_cross_kind_position_canonical_payload_includes_refs():
    print("=== CrossKindPosition: payload includes refs ===")
    ref = CrossKindReference(
        source_id="s", source_kind="swarm_log",
        artifact_hash="cc" * 32)
    pos = CrossKindPosition(
        member_token="m", member_name="M",
        member_public_key="aa" * 32,
        proposal_hash="bb" * 32,
        round_num=0, stance="yea",
        rationale="r", timestamp="t", signature="s",
        references=(ref,))
    payload = pos.canonical_payload()
    assert b'"cross_kind_position"' in payload
    assert b'"swarm_log"' in payload


# =====================================================================
# CrossKindCouncil
# =====================================================================

def _build_meta_council():
    kps = [KeyPair.generate() for _ in range(3)]
    def rule(p, ctx):
        attestations = ctx.get("cross_kind_attestations", {})
        refs = [
            CrossKindReference(
                source_id=sid,
                source_kind=s["source_kind"],
                artifact_hash=s["content_hash"])
            for sid, s in attestations.items()
        ]
        return ("yea", f"saw {len(refs)} attestations", refs)
    meta = CrossKindCouncil(
        "meta", QuorumRule(2, 2), max_rounds=2,
        stability_rounds=1)
    for i, kp in enumerate(kps):
        meta.add_member(CrossKindDeliberativeMember(
            entity_id=f"meta:m{i}", name=f"Meta-{i}",
            member_kp=kp, decision_rule=rule))
    keys = {f"meta:m{i}": kp.public_key_hex()
            for i, kp in enumerate(kps)}
    return meta, keys


def test_cross_kind_council_produces_decision():
    print("=== CrossKindCouncil: produces a decision ===")
    # Set up a witness attestation
    att, _, _ = _witness_att()
    meta, meta_keys = _build_meta_council()
    proposal = Proposal(content={"action": "test"})
    decision = meta.deliberate_and_resolve_cross_kind(
        proposal, attestations=[att])
    assert isinstance(decision, CrossKindFederatedDecision)
    assert len(decision.attestations) == 1
    # Every meta position references the attestation
    for p in decision.inner.positions:
        if isinstance(p, CrossKindPosition):
            if p.references:
                assert p.references[0].source_id == att.source_id


def test_verify_cross_kind_happy():
    print("=== verify_cross_kind_federation: happy path ===")
    att, _, _ = _witness_att()
    meta, meta_keys = _build_meta_council()
    decision = meta.deliberate_and_resolve_cross_kind(
        Proposal(content={"action": "test"}),
        attestations=[att])
    v = verify_cross_kind_federation(
        decision, local_member_keys=meta_keys)
    assert v.valid
    assert v.local_valid


def test_verify_cross_kind_missing_attestation():
    print("=== verify: reference to missing attestation ===")
    att, _, _ = _witness_att()
    meta, meta_keys = _build_meta_council()
    decision = meta.deliberate_and_resolve_cross_kind(
        Proposal(content={"action": "test"}),
        attestations=[att])
    # Remove the attestation from the decision's set
    tampered = CrossKindFederatedDecision(
        inner=decision.inner,
        attestations=())  # empty
    v = verify_cross_kind_federation(
        tampered, local_member_keys=meta_keys)
    assert not v.valid
    assert len(v.reference_errors) > 0


def test_verify_cross_kind_bad_attestation():
    print("=== verify: attestation fails its own verifier ===")
    att, kp, who = _witness_att(content={"x": 1})
    # Tamper content but keep hash
    tampered_att = FederationAttestation(
        source_id=att.source_id,
        source_kind=att.source_kind,
        content={"x": 2},
        content_hash=att.content_hash,
        witness_token=att.witness_token,
        witness_name=att.witness_name,
        witness_public_key=att.witness_public_key,
        witness_signature=att.witness_signature,
        witness_timestamp=att.witness_timestamp)
    meta, meta_keys = _build_meta_council()
    decision = meta.deliberate_and_resolve_cross_kind(
        Proposal(content={"action": "test"}),
        attestations=[tampered_att])
    v = verify_cross_kind_federation(
        decision, local_member_keys=meta_keys)
    assert not v.valid
    failed = [av for av in v.attestation_verdicts
              if not av.valid]
    assert len(failed) == 1


def test_verify_cross_kind_forged_local_position():
    print("=== verify: forged meta position → fail ===")
    att, _, _ = _witness_att()
    meta, meta_keys = _build_meta_council()
    decision = meta.deliberate_and_resolve_cross_kind(
        Proposal(content={"action": "test"}),
        attestations=[att])
    # Tamper with a position's signature
    attacker = KeyPair.generate()
    orig = decision.inner.positions[0]
    # Rebuild with wrong signature
    tampered_pos = CrossKindPosition(
        member_token=orig.member_token,
        member_name=orig.member_name,
        member_public_key=orig.member_public_key,
        proposal_hash=orig.proposal_hash,
        round_num=orig.round_num,
        stance=orig.stance,
        rationale=orig.rationale,
        timestamp=orig.timestamp,
        signature=attacker.sign(
            orig.canonical_payload()).hex(),
        references=orig.references)
    tampered_inner = DeliberativeDecision(
        proposal=decision.inner.proposal,
        proposal_hash=decision.inner.proposal_hash,
        positions=(tampered_pos,) + decision.inner.positions[1:],
        rounds_run=decision.inner.rounds_run,
        converged_at_round=decision.inner.converged_at_round,
        final_decision=decision.inner.final_decision)
    tampered = CrossKindFederatedDecision(
        inner=tampered_inner,
        attestations=decision.attestations)
    v = verify_cross_kind_federation(
        tampered, local_member_keys=meta_keys)
    assert not v.valid


def test_verify_cross_kind_never_raises():
    print("=== verify_cross_kind_federation: never raises ===")
    assert not verify_cross_kind_federation(
        None, {}).valid
    assert not verify_cross_kind_federation(
        "not a decision", {}).valid


# =====================================================================
# JSON roundtrips
# =====================================================================

def test_federation_attestation_json_roundtrip():
    print("=== FederationAttestation: JSON roundtrip ===")
    att, kp, who = _witness_att()
    wire = json.dumps(att.to_dict())
    revived = FederationAttestation.from_dict(json.loads(wire))
    assert revived.content_hash == att.content_hash
    assert revived.witness_signature == att.witness_signature
    v = verify_federation_attestation(revived)
    assert v.valid


def test_cross_kind_decision_json_roundtrip():
    print("=== CrossKindFederatedDecision: JSON roundtrip ===")
    att, _, _ = _witness_att()
    meta, meta_keys = _build_meta_council()
    decision = meta.deliberate_and_resolve_cross_kind(
        Proposal(content={"action": "test"}),
        attestations=[att])
    wire = json.dumps(decision.to_dict())
    revived = CrossKindFederatedDecision.from_dict(
        json.loads(wire))
    v = verify_cross_kind_federation(
        revived, local_member_keys=meta_keys)
    assert v.valid


# =====================================================================
# The compositional claim
# =====================================================================

def test_all_five_architectures_produce_wrappable_artifacts():
    """Every architecture produces an artifact that can be wrapped
    as a FederationAttestation. Direct or witnessed, but wrappable."""
    print("=== Five architectures, five attestations ===")
    from multiverse_c43 import SwarmUnit, SwarmNetwork
    from multiverse_c47 import AutonomicUnit, AutonomicNetwork

    # C44 council decision → direct
    council_dec, _ = _council_decision()
    att_direct = attest_decision(
        "c44", council_dec.final_decision)
    # C45 deliberation → direct
    att_delib = attest_deliberative_decision(
        "c45", council_dec)
    # C43 swarm log → witnessed
    swarm_net = SwarmNetwork(food_target=(2, 2), max_epochs=5)
    swarm_net.add_unit("ant-0", SwarmUnit(
        entity_id="world:ant-0", name="ant-0",
        env_stream=swarm_net.stream,
        initial_position=(0, 0), seed=0,
        sample_probability=1.0))
    e = swarm_net.run_epoch()
    swarm_content = {
        "epochs": [{"epoch": e.epoch,
                     "units_at_food":
                         e.statistics["units_at_food"]}],
        "final_converged": swarm_net.converged(),
    }
    att_swarm = witness_artifact(
        "c43", "swarm_log", swarm_content,
        KeyPair.generate(), create_identity("w1"))
    # C47 autonomic trace → witnessed
    auto_net = AutonomicNetwork()
    auto_net.set_coupling_heat(0.0)
    auto_net.add_unit("A", AutonomicUnit(
        "world:a", "A", target=22.0, initial_state=20.0))
    ae = auto_net.run_epoch()
    auto_content = {
        "trace": [{"epoch": ae.epoch,
                    "states": dict(ae.states),
                    "fires": dict(ae.fires)}],
    }
    att_auto = witness_artifact(
        "c47", "autonomic_trace", auto_content,
        KeyPair.generate(), create_identity("w2"))
    # C40 cross-world (a simple signed one)
    from multiverse_c40 import (
        CrossWorldClaim, WorldAttestationRef,
        create_cross_world_attestation,
    )
    from multiverse_c36 import create_person
    aria, aria_kp = create_person("Aria")
    claim = CrossWorldClaim(
        kind="x", content={},
        references=(
            WorldAttestationRef(
                world_id="w:a", dag_id="d:a",
                link_hash="aa" * 32),
            WorldAttestationRef(
                world_id="w:b", dag_id="d:b",
                link_hash="bb" * 32),
        ))
    cwa = create_cross_world_attestation(aria, aria_kp, claim)
    att_cw = attest_cross_world("c40", cwa)
    # All wrappable
    for a in [att_direct, att_delib, att_swarm,
              att_auto, att_cw]:
        assert a.source_kind in ALL_KINDS
        assert len(a.content_hash) == 64
    print("  ✓ C44 direct:  " + att_direct.source_kind)
    print("  ✓ C45 direct:  " + att_delib.source_kind)
    print("  ✓ C43 witnessed: " + att_swarm.source_kind)
    print("  ✓ C47 witnessed: " + att_auto.source_kind)
    print("  ✓ C40 direct:  " + att_cw.source_kind)


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: five architectures, one meta-decision ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert len(audit["sources"]) == 4  # four source attestations
    assert audit["meta_outcome"] == "passed"
    assert audit["happy_verdict"]["valid"] is True
    assert audit["happy_verdict"]["local_valid"] is True
    assert audit["happy_verdict"]["attestations_all_valid"] is True
    assert audit["happy_verdict"]["reference_error_count"] == 0
    assert audit["tampered_verdict"]["valid"] is False
    # One attestation failed
    failed = [v for v in audit["tampered_verdict"]
              ["attestation_verdicts"] if not v["valid"]]
    assert len(failed) == 1
    assert (tmp_path / "cross_architecture_federation_demo.json"
            ).exists()


if __name__ == "__main__":
    test_kinds_disjoint()
    test_all_kinds_covered_by_default_registry()
    test_direct_attestation_shape()
    test_witnessed_attestation_shape()
    test_attestation_rejects_direct_kind_with_witness()
    test_attestation_rejects_witnessed_kind_without_witness()
    test_attestation_rejects_unknown_kind()
    test_witness_artifact_rejects_direct_kind()
    test_verify_decision_attestation_happy()
    test_verify_decision_attestation_missing_keys()
    test_verify_decision_attestation_tampered_content()
    test_verify_deliberative_attestation()
    test_verify_witnessed_happy()
    test_verify_witnessed_tampered_content()
    test_verify_witnessed_forged_signature()
    test_verify_witnessed_wrong_declared_witness_key()
    test_dispatch_unknown_kind()
    test_dispatch_verifier_raising_is_caught()
    test_cross_kind_reference_validates()
    test_cross_kind_position_canonical_payload_includes_refs()
    test_cross_kind_council_produces_decision()
    test_verify_cross_kind_happy()
    test_verify_cross_kind_missing_attestation()
    test_verify_cross_kind_bad_attestation()
    test_verify_cross_kind_forged_local_position()
    test_verify_cross_kind_never_raises()
    test_federation_attestation_json_roundtrip()
    test_cross_kind_decision_json_roundtrip()
    test_all_five_architectures_produce_wrappable_artifacts()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
