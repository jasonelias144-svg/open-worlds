# multiverse_c41_test.py
import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c13 import HAS_CRYPTO, KeyPair
from multiverse_c24 import sign_report
from multiverse_c27 import verify_dag
from multiverse_c34 import DictDAGResolver
from multiverse_c36 import create_person
from multiverse_c41 import (
    Intent, ArmReport, Arm, HigherOrderController,
    EpochResult, Octopus, demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

class _StubModel:
    def __init__(self, tag: str):
        self.tag = tag
        self.calls = 0

    def generate(self, prompt: str) -> str:
        self.calls += 1
        return f"{self.tag}:{prompt[:30]}"


def _make_arm(name: str, model=None) -> Arm:
    return Arm(
        name=name,
        world_id=f"world:{name}",
        dag_id=f"dag:{name}",
        model_backend=model or _StubModel(name),
        arm_report_kp=KeyPair.generate(),
        arm_report_identity=create_identity(f"report:{name}"),
        arm_dag_kp=KeyPair.generate(),
        arm_dag_identity=create_identity(f"dag:{name}"),
    )


def _make_octopus(arm_names=("poetry", "chemistry", "registry")):
    aria, aria_kp = create_person("Aria")
    octo = Octopus("Aria-Octopus", aria, aria_kp)
    for name in arm_names:
        octo.add_arm(_make_arm(name))
    return octo, aria, aria_kp


def _resolvers(octo: Octopus, epoch_results: list):
    dags = {}
    keys = {}
    for arm in octo._arms.values():
        keys[arm._dag_identity.token] = arm._dag_kp.public_key_hex()
    for result in epoch_results:
        for r in result.reports:
            dags[r.dag_id] = r.dag
    return DictDAGResolver(dags), (lambda sid: keys.get(sid))


# =====================================================================
# Arm — tick
# =====================================================================

def test_arm_tick_no_intent_returns_none():
    print("=== Arm.tick: no intent → None ===")
    arm = _make_arm("poetry")
    assert arm.tick(0) is None


def test_arm_tick_with_intent():
    print("=== Arm.tick: intent → ArmReport ===")
    arm = _make_arm("poetry")
    arm.receive_intent(Intent(
        target_arm="poetry", kind="compose",
        content={"seed": "x"}, epoch=0, issued_at="t"))
    report = arm.tick(0)
    assert report is not None
    assert report.arm_name == "poetry"
    assert report.epoch == 0
    assert report.dag_id == "dag:poetry"
    assert len(report.link_hash) == 64


def test_arm_tick_drains_queue():
    print("=== Arm.tick: drains the intent queue ===")
    arm = _make_arm("poetry")
    for _ in range(3):
        arm.receive_intent(Intent(
            target_arm="poetry", kind="compose",
            content={"x": 1}, epoch=0, issued_at="t"))
    report = arm.tick(0)
    assert report is not None
    assert report.content_summary["intent_count"] == 3
    # Second tick: queue empty → None
    assert arm.tick(0) is None


def test_arm_tick_reports_signature_valid():
    """The arm's DAG link verifies with the arm's key."""
    print("=== Arm.tick: DAG link verifies with arm's key ===")
    arm = _make_arm("poetry")
    arm.receive_intent(Intent(
        target_arm="poetry", kind="compose",
        content={"seed": "x"}, epoch=0, issued_at="t"))
    report = arm.tick(0)
    v = verify_dag(
        report.dag,
        key_resolver=lambda sid: (
            arm._dag_kp.public_key_hex()
            if sid == arm._dag_identity.token else None),
    )
    assert v.valid


def test_arm_tick_handles_model_exception():
    print("=== Arm.tick: model exception → error report, no raise ===")
    class BadModel:
        def generate(self, prompt):
            raise RuntimeError("model crashed")
    arm = _make_arm("poetry", model=BadModel())
    arm.receive_intent(Intent(
        target_arm="poetry", kind="compose",
        content={}, epoch=0, issued_at="t"))
    report = arm.tick(0)
    assert report is not None
    assert report.content_summary["kind"] == "error"


# =====================================================================
# Arm — reflex
# =====================================================================

def test_arm_local_reflex():
    print("=== Arm.local_reflex: produces report without intent ===")
    arm = _make_arm("poetry")
    report = arm.local_reflex(0, {"kind": "brightness"})
    assert report.arm_name == "poetry"
    assert report.content_summary["kind"] == "reflex"
    assert report.content_summary["stimulus_kind"] == "brightness"


def test_arm_reflex_does_not_drain_queue():
    print("=== Arm.reflex: intent queue is untouched ===")
    arm = _make_arm("poetry")
    arm.receive_intent(Intent(
        target_arm="poetry", kind="compose",
        content={}, epoch=0, issued_at="t"))
    arm.local_reflex(0, {"kind": "stimulus"})
    # Queue still has the intent
    report = arm.tick(0)
    assert report is not None
    assert report.content_summary["intent_count"] == 1


# =====================================================================
# HigherOrderController
# =====================================================================

def test_brain_issues_intent():
    print("=== Brain.issue_intent: creates and tracks ===")
    aria, aria_kp = create_person("Aria")
    brain = HigherOrderController(aria, aria_kp)
    intent = brain.issue_intent(
        "poetry", "compose", {"seed": "x"}, epoch=0)
    assert intent.target_arm == "poetry"
    assert intent.epoch == 0


def test_brain_close_epoch_too_few_reports():
    print("=== Brain.close_epoch: < 2 reports → None ===")
    aria, aria_kp = create_person("Aria")
    brain = HigherOrderController(aria, aria_kp)
    # 0 reports
    assert brain.close_epoch(0, {"a", "b"}) is None
    # 1 report
    arm = _make_arm("a")
    r = arm.local_reflex(0, {"kind": "x"})
    brain.receive_report(r)
    assert brain.close_epoch(0, {"a", "b"}) is None


def test_brain_close_epoch_signs():
    print("=== Brain.close_epoch: >= 2 reports → signed attestation ===")
    aria, aria_kp = create_person("Aria")
    brain = HigherOrderController(aria, aria_kp)
    for name in ("a", "b", "c"):
        arm = _make_arm(name)
        brain.receive_report(arm.local_reflex(0, {"kind": "x"}))
    att = brain.close_epoch(0, {"a", "b", "c"})
    assert att is not None
    assert att.person_token == aria.person.token
    assert len(att.claim.references) == 3


def test_brain_close_epoch_names_missing_arms():
    print("=== Brain.close_epoch: missing arms are recorded ===")
    aria, aria_kp = create_person("Aria")
    brain = HigherOrderController(aria, aria_kp)
    for name in ("a", "b"):
        arm = _make_arm(name)
        brain.receive_report(arm.local_reflex(0, {"kind": "x"}))
    att = brain.close_epoch(0, {"a", "b", "c", "d"})
    assert att is not None
    assert sorted(att.claim.content["missing_arms"]) == ["c", "d"]


def test_brain_attestation_chains():
    print("=== Brain: epoch N's content references epoch N-1 hash ===")
    aria, aria_kp = create_person("Aria")
    brain = HigherOrderController(aria, aria_kp)
    for name in ("a", "b"):
        brain.receive_report(
            _make_arm(name).local_reflex(0, {"k": "0"}))
    att0 = brain.close_epoch(0, {"a", "b"})
    assert att0.claim.content["prior_attestation_hash"] is None

    for name in ("a", "b"):
        brain.receive_report(
            _make_arm(name).local_reflex(1, {"k": "1"}))
    att1 = brain.close_epoch(1, {"a", "b"})
    # The prior hash should be the hash of att0's canonical payload
    import hashlib
    expected = hashlib.sha256(
        att0.canonical_payload()).hexdigest()
    assert att1.claim.content["prior_attestation_hash"] == expected


# =====================================================================
# Octopus — full flow
# =====================================================================

def test_run_epoch_all_arms_report():
    print("=== run_epoch: all arms report, attestation signed ===")
    octo, aria, _ = _make_octopus()
    result = octo.run_epoch({
        "poetry": [{"kind": "compose", "content": {"s": "x"}}],
        "chemistry": [{"kind": "react", "content": {"s": "y"}}],
        "registry": [{"kind": "index", "content": {"s": "z"}}],
    })
    assert result.epoch == 0
    assert len(result.reports) == 3
    assert result.attestation is not None
    assert len(result.attestation.claim.references) == 3
    assert result.missing_arms == []


def test_run_epoch_missing_arm():
    print("=== run_epoch: one arm gets no intent → missing ===")
    octo, _, _ = _make_octopus()
    result = octo.run_epoch({
        "poetry": [{"kind": "compose", "content": {}}],
        "chemistry": [{"kind": "react", "content": {}}],
        # registry: no intents
    })
    assert len(result.reports) == 2
    assert result.missing_arms == ["registry"]
    # Attestation still signed (>= 2 refs)
    assert result.attestation is not None


def test_run_epoch_only_one_arm_no_attestation():
    print("=== run_epoch: only one arm → no attestation ===")
    octo, _, _ = _make_octopus()
    result = octo.run_epoch({
        "poetry": [{"kind": "compose", "content": {}}],
    })
    assert len(result.reports) == 1
    assert result.attestation is None


def test_run_epoch_with_reflex():
    print("=== run_epoch: reflex adds an extra report ===")
    octo, _, _ = _make_octopus()
    result = octo.run_epoch(
        intents_per_arm={
            "poetry": [{"kind": "compose", "content": {}}],
            "chemistry": [{"kind": "react", "content": {}}],
        },
        reflexes={"registry": {"kind": "stimulus"}},
    )
    # 2 from intents + 1 reflex = 3
    assert len(result.reports) == 3
    reflex = next(
        r for r in result.reports if r.arm_name == "registry")
    assert reflex.content_summary["kind"] == "reflex"


def test_run_epoch_arm_independence():
    """Each arm's DAG verifies alone, before and after the brain
    attests."""
    print("=== run_epoch: arms verify alone after epoch ===")
    octo, _, _ = _make_octopus()
    result = octo.run_epoch({
        "poetry": [{"kind": "compose", "content": {}}],
        "chemistry": [{"kind": "react", "content": {}}],
        "registry": [{"kind": "index", "content": {}}],
    })
    for arm in octo._arms.values():
        key = arm._dag_kp.public_key_hex()
        sid = arm._dag_identity.token
        v = verify_dag(
            next(r.dag for r in result.reports
                 if r.arm_name == arm.name),
            key_resolver=lambda s, _k=key, _i=sid: (
                _k if s == _i else None),
        )
        assert v.valid


def test_run_epoch_verifies_attestation():
    print("=== run_epoch: attestation verifies via verify_all ===")
    octo, aria, _ = _make_octopus()
    e0 = octo.run_epoch({
        "poetry": [{"kind": "compose", "content": {}}],
        "chemistry": [{"kind": "react", "content": {}}],
        "registry": [{"kind": "index", "content": {}}],
    })
    resolver, key_resolver = _resolvers(octo, [e0])
    verdicts = octo.verify_all(
        resolver, key_resolver,
        trusted_person_public_key=aria.person_public_key)
    assert len(verdicts) == 1
    assert verdicts[0].valid


def test_two_epochs_verify_independently():
    print("=== run_epoch: two epochs, both attestations verify ===")
    octo, aria, _ = _make_octopus()
    e0 = octo.run_epoch({
        "poetry": [{"kind": "compose", "content": {"e": 0}}],
        "chemistry": [{"kind": "react", "content": {"e": 0}}],
        "registry": [{"kind": "index", "content": {"e": 0}}],
    })
    e1 = octo.run_epoch({
        "poetry": [{"kind": "compose", "content": {"e": 1}}],
        "chemistry": [{"kind": "react", "content": {"e": 1}}],
        "registry": [{"kind": "index", "content": {"e": 1}}],
    })
    resolver, key_resolver = _resolvers(octo, [e0, e1])
    verdicts = octo.verify_all(
        resolver, key_resolver,
        trusted_person_public_key=aria.person_public_key)
    assert len(verdicts) == 2
    assert all(v.valid for v in verdicts)


def test_add_arm_is_local():
    """Adding a fourth arm doesn't require touching the others."""
    print("=== Scaling: adding an arm is local ===")
    octo, aria, _ = _make_octopus(arm_names=("a", "b"))
    e0 = octo.run_epoch({
        "a": [{"kind": "x", "content": {}}],
        "b": [{"kind": "x", "content": {}}],
    })
    # Add a third arm
    octo.add_arm(_make_arm("c"))
    e1 = octo.run_epoch({
        "a": [{"kind": "x", "content": {}}],
        "b": [{"kind": "x", "content": {}}],
        "c": [{"kind": "x", "content": {}}],
    })
    # Epoch 0's reports and attestation unchanged
    assert len(e0.reports) == 2
    assert len(e0.attestation.claim.references) == 2
    # Epoch 1 has 3 arms
    assert len(e1.reports) == 3
    assert len(e1.attestation.claim.references) == 3


# =====================================================================
# Never raises
# =====================================================================

def test_octopus_never_raises_on_bad_input():
    print("=== Octopus: never raises on unexpected input ===")
    octo, _, _ = _make_octopus(arm_names=("a", "b"))
    # Intent for an unknown arm — no error, just unused
    result = octo.run_epoch({
        "nonexistent": [{"kind": "x", "content": {}}],
        "a": [{"kind": "x", "content": {}}],
        "b": [{"kind": "x", "content": {}}],
    })
    # 2 arms reported (a and b), the nonexistent intent went nowhere
    assert len(result.reports) == 2


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: three arms, two epochs, one reflex ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert len(audit["epochs"]) == 2
    # Epoch 0: 3 reports, no reflex
    assert len(audit["epochs"][0]["reports"]) == 3
    assert audit["epochs"][0]["attestation_signed"]
    # Epoch 1: 3 intents + 1 reflex = 4 reports
    assert len(audit["epochs"][1]["reports"]) == 4
    assert audit["epochs"][1]["attestation_signed"]
    assert audit["epochs"][1]["attestation_refs"] == 4
    # Both verdicts valid
    assert all(v["valid"] for v in audit["verdicts"])
    assert (tmp_path / "octopus_demo.json").exists()


if __name__ == "__main__":
    test_arm_tick_no_intent_returns_none()
    test_arm_tick_with_intent()
    test_arm_tick_drains_queue()
    test_arm_tick_reports_signature_valid()
    test_arm_tick_handles_model_exception()
    test_arm_local_reflex()
    test_arm_reflex_does_not_drain_queue()
    test_brain_issues_intent()
    test_brain_close_epoch_too_few_reports()
    test_brain_close_epoch_signs()
    test_brain_close_epoch_names_missing_arms()
    test_brain_attestation_chains()
    test_run_epoch_all_arms_report()
    test_run_epoch_missing_arm()
    test_run_epoch_only_one_arm_no_attestation()
    test_run_epoch_with_reflex()
    test_run_epoch_arm_independence()
    test_run_epoch_verifies_attestation()
    test_two_epochs_verify_independently()
    test_add_arm_is_local()
    test_octopus_never_raises_on_bad_input()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
