import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c3 import Act, Ack, Refusal
from multiverse_c13 import HAS_CRYPTO, KeyPair
from multiverse_c44 import QuorumRule
from multiverse_c45 import (
    Proposal, DeliberativeCouncil, DeliberativeMember,
)
from multiverse_c48 import (
    FederationAttestation,
    attest_deliberative_decision,
    verify_federation_attestation,
)
from multiverse_c52 import EpidemicUnit, EpochResult
from multiverse_c54 import (
    AttestedRumor,
    VerifyingEpidemicUnit,
    AttestedEpidemicNetwork,
    ExposureRecord, UnitAudit, RumorAuditTrail,
    build_audit_trail, _attestation_of,
    demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _make_attested_rumor():
    """Build a council decision, wrap it, return (attested, context)."""
    kps = [KeyPair.generate() for _ in range(3)]
    council = DeliberativeCouncil(
        "test-council", QuorumRule(2, 2),
        max_rounds=2, stability_rounds=1)
    for i, kp in enumerate(kps):
        council.add_member(DeliberativeMember(
            entity_id=f"test-council:m{i}",
            name=f"C-{i}", member_kp=kp,
            decision_rule=lambda p, c: ("yea", "ok")))
    keys = {f"test-council:m{i}": kp.public_key_hex()
            for i, kp in enumerate(kps)}
    decision = council.deliberate_and_resolve(
        Proposal(content={"action": "test"}))
    att = attest_deliberative_decision(
        "test-council", decision)
    return (AttestedRumor.from_attestation(att),
            {"member_keys": {"test-council": keys}})


def _make_chain(names, contexts):
    net = AttestedEpidemicNetwork()
    for i, name in enumerate(names):
        contacts = []
        if i > 0:
            contacts.append(names[i - 1])
        if i < len(names) - 1:
            contacts.append(names[i + 1])
        net.add_unit(name, VerifyingEpidemicUnit(
            entity_id=f"world:{name}", name=name,
            contacts=contacts, susceptibility=1,
            trust_context=contexts.get(name)))
    return net


# =====================================================================
# AttestedRumor
# =====================================================================

def test_attested_rumor_binds_id_to_content_hash():
    print("=== AttestedRumor: rumor_id == content_hash ===")
    attested, _ = _make_attested_rumor()
    assert attested.rumor_id == \
        attested.attestation.content_hash


def test_attested_rumor_rejects_mismatched_id():
    print("=== AttestedRumor: rejects id != content_hash ===")
    attested, _ = _make_attested_rumor()
    with pytest.raises(ValueError):
        AttestedRumor(
            rumor_id="some-other-id",
            attestation=attested.attestation)


def test_attested_rumor_json_roundtrip():
    print("=== AttestedRumor: JSON roundtrip ===")
    attested, _ = _make_attested_rumor()
    wire = json.dumps(attested.to_dict())
    revived = AttestedRumor.from_dict(json.loads(wire))
    assert revived.rumor_id == attested.rumor_id
    assert revived.attestation.content_hash == \
        attested.attestation.content_hash


# =====================================================================
# Unit construction and structural claims
# =====================================================================

def test_unit_is_a_c52_spreader():
    print("=== Unit: is-a C52 EpidemicUnit ===")
    _, context = _make_attested_rumor()
    unit = VerifyingEpidemicUnit(
        "world:u", "U", contacts=["A"],
        trust_context=context)
    assert isinstance(unit, EpidemicUnit)
    # C52 structural attrs still present
    assert hasattr(unit, "_contacts")
    assert hasattr(unit, "_susceptibility")
    assert hasattr(unit, "_exposures")
    assert hasattr(unit, "_spreading")
    # C54 additions
    assert hasattr(unit, "_trust_context")
    assert hasattr(unit, "_verified_exposures")
    assert hasattr(unit, "_attestations")


def test_unit_has_no_other_arch_attrs():
    print("=== Unit: no C41-C50 attrs ===")
    _, context = _make_attested_rumor()
    unit = VerifyingEpidemicUnit(
        "world:u", "U", trust_context=context)
    for attr in ("_model", "_intent_queue"):     # C41
        assert not hasattr(unit, attr), attr
    for attr in ("_inputs", "_threshold"):       # C42
        assert not hasattr(unit, attr), attr
    for attr in ("_env_stream", "_position"):    # C43
        assert not hasattr(unit, attr), attr
    for attr in ("_decision_rule", "_members"):  # C44
        assert not hasattr(unit, attr), attr
    for attr in ("_target", "_state"):           # C47
        assert not hasattr(unit, attr), attr
    for attr in ("_current_policy",
                 "_policy_history"):              # C50
        assert not hasattr(unit, attr), attr


# =====================================================================
# Verification at receipt
# =====================================================================

def test_act_infect_with_valid_attestation_accepted():
    print("=== act('infect'): valid attestation → verified ===")
    attested, context = _make_attested_rumor()
    unit = VerifyingEpidemicUnit(
        "world:u", "U", trust_context=context)
    r = unit.act(Act(
        actor_token="src", type="infect",
        payload={
            "rumor_id": attested.rumor_id,
            "source": "src",
            "attested": attested.to_dict(),
        }))
    assert isinstance(r, Ack)
    assert attested.rumor_id in \
        unit.verified_exposures(attested.rumor_id) or \
        "src" in unit.verified_exposures(attested.rumor_id)
    # Specifically:
    assert "src" in unit.verified_exposures(attested.rumor_id)
    assert unit.exposure_reason(
        attested.rumor_id, "src") == "attestation verified"


def test_act_infect_without_context_refused():
    print("=== act('infect'): no context → refused ===")
    attested, _ = _make_attested_rumor()
    unit = VerifyingEpidemicUnit(
        "world:u", "U", trust_context=None)
    r = unit.act(Act(
        actor_token="src", type="infect",
        payload={
            "rumor_id": attested.rumor_id,
            "source": "src",
            "attested": attested.to_dict(),
        }))
    assert isinstance(r, Ack)  # unit still records
    assert "src" not in unit.verified_exposures(
        attested.rumor_id)
    assert "no trust context" in (
        unit.exposure_reason(attested.rumor_id, "src") or "")


def test_act_infect_with_wrong_context_refused():
    print("=== act('infect'): wrong context → refused ===")
    attested, _ = _make_attested_rumor()
    wrong_context = {
        "member_keys": {"test-council": {
            "test-council:m0":
                KeyPair.generate().public_key_hex(),
        }},
    }
    unit = VerifyingEpidemicUnit(
        "world:u", "U", trust_context=wrong_context)
    unit.act(Act(
        actor_token="src", type="infect",
        payload={
            "rumor_id": attested.rumor_id,
            "source": "src",
            "attested": attested.to_dict(),
        }))
    assert "src" not in unit.verified_exposures(
        attested.rumor_id)
    reason = unit.exposure_reason(
        attested.rumor_id, "src") or ""
    assert "invalid" in reason.lower() or \
        "no member keys" in reason.lower()


def test_act_infect_tampered_attestation_refused():
    print("=== act('infect'): tampered attestation → refused ===")
    attested, context = _make_attested_rumor()
    # Tamper: content differs from hash
    tampered = FederationAttestation(
        source_id=attested.attestation.source_id,
        source_kind=attested.attestation.source_kind,
        content={**attested.attestation.content,
                 "tampered": True},
        content_hash=attested.attestation.content_hash)
    unit = VerifyingEpidemicUnit(
        "world:u", "U", trust_context=context)
    unit.act(Act(
        actor_token="src", type="infect",
        payload={
            "rumor_id": tampered.content_hash,
            "source": "src",
            "attested": {
                "rumor_id": tampered.content_hash,
                "attestation": tampered.to_dict(),
            },
        }))
    assert "src" not in unit.verified_exposures(
        tampered.content_hash)
    reason = unit.exposure_reason(
        tampered.content_hash, "src") or ""
    assert "hash" in reason.lower() or "invalid" in reason.lower()


def test_act_infect_rejects_missing_attested():
    print("=== act('infect'): missing attested → Refusal ===")
    _, context = _make_attested_rumor()
    unit = VerifyingEpidemicUnit(
        "world:u", "U", trust_context=context)
    r = unit.act(Act(
        actor_token="src", type="infect",
        payload={"rumor_id": "x", "source": "src"}))
    assert isinstance(r, Refusal)


def test_act_infect_rejects_mismatched_rumor_id():
    print("=== act('infect'): rumor_id != attested.rumor_id → Refusal ===")
    attested, context = _make_attested_rumor()
    unit = VerifyingEpidemicUnit(
        "world:u", "U", trust_context=context)
    r = unit.act(Act(
        actor_token="src", type="infect",
        payload={
            "rumor_id": "different-id",
            "source": "src",
            "attested": attested.to_dict(),
        }))
    assert isinstance(r, Refusal)


# =====================================================================
# Susceptibility counts only verified
# =====================================================================

def test_susceptibility_ignores_unverified():
    print("=== Susceptibility: only verified count ===")
    attested, context = _make_attested_rumor()
    unit = VerifyingEpidemicUnit(
        "world:u", "U", contacts=["A"],
        susceptibility=2, trust_context=context)
    # Two exposures: one verified, one not
    unit.act(Act(actor_token="src1", type="infect",
                  payload={
                      "rumor_id": attested.rumor_id,
                      "source": "src1",
                      "attested": attested.to_dict()}))
    # Unverified via no-context path
    def no_context_verify(*a, **kw): return (False, "nope")
    original = unit._trust_context
    unit._trust_context = {}
    unit.act(Act(actor_token="src2", type="infect",
                  payload={
                      "rumor_id": attested.rumor_id,
                      "source": "src2",
                      "attested": attested.to_dict()}))
    unit._trust_context = original
    # Only one verified source; susc=2 → no spread
    assert len(unit.verified_exposures(
        attested.rumor_id)) == 1
    pending = unit.tick(0)
    assert pending == []
    assert not unit.is_spreading(attested.rumor_id)


def test_susceptibility_reaches_with_two_verified():
    print("=== Susceptibility: two verified → starts spreading ===")
    attested, context = _make_attested_rumor()
    unit = VerifyingEpidemicUnit(
        "world:u", "U", contacts=["A"],
        susceptibility=2, trust_context=context)
    unit.act(Act(actor_token="src1", type="infect",
                  payload={
                      "rumor_id": attested.rumor_id,
                      "source": "src1",
                      "attested": attested.to_dict()}))
    unit.act(Act(actor_token="src2", type="infect",
                  payload={
                      "rumor_id": attested.rumor_id,
                      "source": "src2",
                      "attested": attested.to_dict()}))
    pending = unit.tick(0)
    assert unit.is_spreading(attested.rumor_id)
    assert len(pending) == 1
    assert pending[0] == ("A", attested.rumor_id)


# =====================================================================
# Network propagation
# =====================================================================

def test_network_full_chain_saturates():
    print("=== Network: full chain saturates ===")
    attested, context = _make_attested_rumor()
    chain = ["A", "B", "C", "D", "E"]
    net = _make_chain(chain, {n: context for n in chain})
    net.seed_attested("A", attested)
    net.run_until_quiet()
    trail = build_audit_trail(net, attested.rumor_id)
    assert trail.saturated()
    assert set(trail.verified()) == set(chain)


def test_network_skeptic_blocks():
    print("=== Network: skeptic blocks propagation ===")
    attested, context = _make_attested_rumor()
    chain = ["A", "B", "C", "D", "E"]
    contexts = {n: context for n in chain}
    contexts["C"] = None
    net = _make_chain(chain, contexts)
    net.seed_attested("A", attested)
    net.run_until_quiet()
    trail = build_audit_trail(net, attested.rumor_id)
    assert not trail.saturated()
    assert set(trail.verified()) == {"A", "B"}
    refused_units = [u for u, _ in trail.refused()]
    assert "C" in refused_units
    # D, E never reached
    assert "D" not in trail.reached()
    assert "E" not in trail.reached()


def test_network_branching_survives_one_bad_branch():
    print("=== Network: branching survives one bad branch ===")
    attested, context = _make_attested_rumor()
    # A→{B,C}; B,C→D; D→E
    net = AttestedEpidemicNetwork()
    for name, contacts in [
        ("A", ["B", "C"]),
        ("B", ["A", "D"]),
        ("C", ["A", "D"]),
        ("D", ["B", "C", "E"]),
        ("E", ["D"]),
    ]:
        ctx = None if name == "B" else context
        net.add_unit(name, VerifyingEpidemicUnit(
            entity_id=f"world:{name}", name=name,
            contacts=contacts, susceptibility=1,
            trust_context=ctx))
    net.seed_attested("A", attested)
    net.run_until_quiet()
    trail = build_audit_trail(net, attested.rumor_id)
    assert trail.saturated()
    assert "B" not in trail.verified()  # B refused
    assert set(trail.verified()) >= {"A", "C", "D", "E"}


def test_network_tampered_at_seed_no_propagation():
    print("=== Network: tampered attestation → zero propagation ===")
    attested, context = _make_attested_rumor()
    chain = ["A", "B", "C"]
    net = _make_chain(chain, {n: context for n in chain})
    # Build a tampered attestation and inject directly
    tampered = FederationAttestation(
        source_id=attested.attestation.source_id,
        source_kind=attested.attestation.source_kind,
        content={**attested.attestation.content,
                 "tampered": True},
        content_hash=attested.attestation.content_hash)
    r = net._units["A"].act(Act(
        actor_token="external", type="infect",
        payload={
            "rumor_id": tampered.content_hash,
            "source": "external",
            "attested": {
                "rumor_id": tampered.content_hash,
                "attestation": tampered.to_dict(),
            },
        }))
    net.run_until_quiet()
    trail = build_audit_trail(net, tampered.content_hash)
    assert not trail.saturated()
    # A recorded but couldn't verify; refused
    assert "A" in [u for u, _ in trail.refused()]


# =====================================================================
# Audit trail
# =====================================================================

def test_audit_trail_format():
    print("=== RumorAuditTrail: readable output ===")
    attested, context = _make_attested_rumor()
    chain = ["A", "B", "C"]
    net = _make_chain(chain, {n: context for n in chain})
    net.seed_attested("A", attested)
    net.run_until_quiet()
    trail = build_audit_trail(net, attested.rumor_id)
    text = trail.format()
    assert "Rumor Audit Trail" in text
    assert attested.rumor_id[:16] in text
    for n in chain:
        assert n in text
    assert "verified" in text


def test_audit_trail_json():
    print("=== RumorAuditTrail: JSON serializable ===")
    attested, context = _make_attested_rumor()
    chain = ["A", "B", "C"]
    net = _make_chain(chain, {n: context for n in chain})
    net.seed_attested("A", attested)
    net.run_until_quiet()
    trail = build_audit_trail(net, attested.rumor_id)
    wire = json.dumps(trail.to_dict())
    parsed = json.loads(wire)
    assert parsed["saturated"] is True
    assert len(parsed["units"]) == 3


def test_audit_trail_refused_has_reason():
    print("=== RumorAuditTrail: refused includes reason ===")
    attested, context = _make_attested_rumor()
    chain = ["A", "B", "C"]
    contexts = {n: context for n in chain}
    contexts["B"] = None
    net = _make_chain(chain, contexts)
    net.seed_attested("A", attested)
    net.run_until_quiet()
    trail = build_audit_trail(net, attested.rumor_id)
    refused = trail.refused()
    assert len(refused) == 1
    unit, reason = refused[0]
    assert unit == "B"
    assert "no trust context" in reason.lower() or \
        "invalid" in reason.lower()


# =====================================================================
# Composition: the attestation is independently verifiable
# =====================================================================

def test_attestation_independently_verifiable():
    """A third party can pull the attestation out of the audit
    trail and verify it against the same context, without the
    network's cooperation."""
    print("=== Composition: attestation verifiable independently ===")
    attested, context = _make_attested_rumor()
    # Verify directly, no network involved
    v = verify_federation_attestation(
        attested.attestation, context)
    assert v.valid
    # And via the default registry (no context override)
    v2 = verify_federation_attestation(
        attested.attestation, context,
        registry=None)  # uses C48's defaults
    assert v2.valid


def test_seed_attested_accepts_good():
    print("=== seed_attested: good attestation → accepted ===")
    attested, context = _make_attested_rumor()
    net = _make_chain(["A", "B"], {"A": context, "B": context})
    assert net.seed_attested("A", attested) is True
    assert "external" in net._units["A"].verified_exposures(
        attested.rumor_id)


def test_seed_attested_unknown_unit():
    print("=== seed_attested: unknown unit → False ===")
    attested, context = _make_attested_rumor()
    net = _make_chain(["A"], {"A": context})
    assert net.seed_attested("Z", attested) is False


# =====================================================================
# Never raises
# =====================================================================

def test_verify_attested_never_raises():
    print("=== verify_attested: never raises ===")
    attested, _ = _make_attested_rumor()
    unit = VerifyingEpidemicUnit(
        "world:u", "U", trust_context={})
    ok, reason = unit.verify_attested(attested)
    assert not ok
    assert "no trust context" in reason


def test_act_never_raises_on_bad_payload():
    print("=== act: never raises on bad payloads ===")
    _, context = _make_attested_rumor()
    unit = VerifyingEpidemicUnit(
        "world:u", "U", trust_context=context)
    for payload in (
        None, {}, {"rumor_id": "x"},
        {"rumor_id": "x", "source": "y"},
        {"rumor_id": "x", "source": "y",
         "attested": "not a dict"},
        {"rumor_id": "x", "source": "y",
         "attested": {"rumor_id": "z",
                       "attestation": {}}},
    ):
        r = unit.act(Act(actor_token="src", type="infect",
                          payload=payload or {}))
        assert isinstance(r, (Ack, Refusal))


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: four scenarios ===")
    audit = demo(artifact_dir=str(tmp_path))
    s = audit["scenarios"]
    assert s["A_all_good"]["saturated"] is True
    assert set(s["A_all_good"]["verified"]) == {
        "A", "B", "C", "D", "E"}
    assert s["B_skeptic"]["saturated"] is False
    assert "C" in [u for u, _ in s["B_skeptic"]["refused"]]
    assert set(s["B_skeptic"]["verified"]) == {"A", "B"}
    assert s["C_tampered"]["saturated"] is False
    assert s["D_branching"]["saturated"] is True
    assert "B" in [u for u, _ in s["D_branching"]["refused"]]
    assert (tmp_path / "rumor_attestation_demo.json").exists()


if __name__ == "__main__":
    test_attested_rumor_binds_id_to_content_hash()
    test_attested_rumor_rejects_mismatched_id()
    test_attested_rumor_json_roundtrip()
    test_unit_is_a_c52_spreader()
    test_unit_has_no_other_arch_attrs()
    test_act_infect_with_valid_attestation_accepted()
    test_act_infect_without_context_refused()
    test_act_infect_with_wrong_context_refused()
    test_act_infect_tampered_attestation_refused()
    test_act_infect_rejects_missing_attested()
    test_act_infect_rejects_mismatched_rumor_id()
    test_susceptibility_ignores_unverified()
    test_susceptibility_reaches_with_two_verified()
    test_network_full_chain_saturates()
    test_network_skeptic_blocks()
    test_network_branching_survives_one_bad_branch()
    test_network_tampered_at_seed_no_propagation()
    test_audit_trail_format()
    test_audit_trail_json()
    test_audit_trail_refused_has_reason()
    test_attestation_independently_verifiable()
    test_seed_attested_accepts_good()
    test_seed_attested_unknown_unit()
    test_verify_attested_never_raises()
    test_act_never_raises_on_bad_payload()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
