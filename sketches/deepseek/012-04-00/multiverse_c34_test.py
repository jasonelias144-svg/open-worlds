# multiverse_c34_test.py
import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c15 import PassportEntry
from multiverse_c21 import ProvenanceReport, EntryProvenance
from multiverse_c24 import sign_report
from multiverse_c27 import DAGLink, AttestedDAG, DAGVerdict, verify_dag
from multiverse_c34 import (
    ExtendingDAGLink, DictDAGResolver, ExtendedDAGBuilder,
    FederatedDAGVerdict, verify_dag_extended, demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _stub_report(name="Alice", entity_id="world:a"):
    kp = KeyPair.generate()
    who = create_identity(name)
    rep = ProvenanceReport(
        passport_token=f"{name.lower()}-token",
        passport_name=name,
        registry_url="http://r",
    )
    entry = PassportEntry(
        entity_id=entity_id,
        timestamp="2024-01-01T00:00:00+00:00",
        subject_token=f"{name.lower()}-token",
        signature="cc" * 64,
    )
    ep = EntryProvenance(entry=entry)
    ep.verdict = "verified"
    ep.reason = "stub"
    rep.entries.append(ep)
    return sign_report(rep, kp, who), kp, who


def _build_two_dags():
    """A two-DAG federation: A (2 links), B (2 links, extending A)."""
    # DAG-A: Alice → Bob
    report_a, alice_kp, alice = _stub_report("Alice", "world:a")
    bob_kp = KeyPair.generate(); bob = create_identity("Bob")
    ab = ExtendedDAGBuilder(report_a)
    a_root = ab.attest(alice_kp, alice)
    a_bob = ab.attest(bob_kp, bob,
                       previous_link_hashes=(a_root.link_hash(),))
    dag_a = ab.build()

    # DAG-B: Carol → Dave (Dave extends via Bob)
    report_b, carol_kp, carol = _stub_report("Carol", "world:b")
    dave_kp = KeyPair.generate(); dave = create_identity("Dave")
    bb = ExtendedDAGBuilder(report_b)
    b_root = bb.attest(carol_kp, carol)
    b_dave = bb.attest(
        dave_kp, dave,
        previous_link_hashes=(b_root.link_hash(),),
        external_references=(("dag-a", a_bob.link_hash()),))
    dag_b = bb.build()

    keys = {
        alice.token: alice_kp.public_key_hex(),
        bob.token: bob_kp.public_key_hex(),
        carol.token: carol_kp.public_key_hex(),
        dave.token: dave_kp.public_key_hex(),
    }
    return {
        "dag_a": dag_a, "dag_b": dag_b,
        "a_root": a_root, "a_bob": a_bob,
        "b_root": b_root, "b_dave": b_dave,
        "keys": keys,
        "alice_kp": alice_kp, "bob_kp": bob_kp,
        "carol_kp": carol_kp, "dave_kp": dave_kp,
        "alice": alice, "bob": bob,
        "carol": carol, "dave": dave,
    }


# =====================================================================
# ExtendingDAGLink construction
# =====================================================================

def test_extending_link_requires_external_refs():
    print("=== ExtendingDAGLink requires at least one external ref ===")
    with pytest.raises(ValueError):
        ExtendingDAGLink(
            signer_id="x", signer_name="X",
            previous_link_hashes=("a" * 64,), report_hash=None,
            timestamp="t", external_references=(),
            signature="s")


def test_extending_link_rejects_duplicate_refs():
    print("=== ExtendingDAGLink rejects duplicate external refs ===")
    ref = ("dag-a", "a" * 64)
    with pytest.raises(ValueError):
        ExtendingDAGLink(
            signer_id="x", signer_name="X",
            previous_link_hashes=("b" * 64,), report_hash=None,
            timestamp="t", external_references=(ref, ref),
            signature="s")


def test_extending_link_rejects_bad_link_hash():
    print("=== ExtendingDAGLink rejects malformed link_hash ===")
    with pytest.raises(ValueError):
        ExtendingDAGLink(
            signer_id="x", signer_name="X",
            previous_link_hashes=("a" * 64,), report_hash=None,
            timestamp="t",
            external_references=(("dag-a", "short"),),
            signature="s")


def test_extending_link_is_distinct_from_dag_link():
    print("=== ExtendingDAGLink and DAGLink are distinct types ===")
    parts = _build_two_dags()
    assert isinstance(parts["a_bob"], DAGLink)
    assert isinstance(parts["b_dave"], ExtendingDAGLink)
    assert not isinstance(parts["b_dave"], DAGLink)


# =====================================================================
# Verification — happy path
# =====================================================================

def test_dag_a_verifies_independently():
    print("=== DAG-A verifies independently (no extensions) ===")
    parts = _build_two_dags()
    resolver = DictDAGResolver({"dag-a": parts["dag_a"]})
    verdict = verify_dag_extended(
        parts["dag_a"],
        key_resolver=lambda sid: parts["keys"].get(sid),
        dag_resolver=resolver,
        report_verifier=lambda r: True)
    assert verdict.valid
    assert verdict.extension_results == {}


def test_dag_b_verifies_with_extension():
    print("=== DAG-B verifies; its extension into DAG-A resolves ===")
    parts = _build_two_dags()
    resolver = DictDAGResolver({
        "dag-a": parts["dag_a"], "dag-b": parts["dag_b"]})
    verdict = verify_dag_extended(
        parts["dag_b"],
        key_resolver=lambda sid: parts["keys"].get(sid),
        dag_resolver=resolver,
        report_verifier=lambda r: True)
    print(verdict.format())
    assert verdict.valid
    # The extension was checked
    assert len(verdict.extension_results) == 1
    b_dave_hash = parts["b_dave"].link_hash()
    assert b_dave_hash in verdict.extension_results
    results = verdict.extension_results[b_dave_hash]
    assert len(results) == 1
    assert results[0].ok


# =====================================================================
# Failure cases
# =====================================================================

def test_missing_external_dag_rejected():
    print("=== Missing external DAG → extension fails ===")
    parts = _build_two_dags()
    # Resolver knows only DAG-B, not DAG-A
    resolver = DictDAGResolver({"dag-b": parts["dag_b"]})
    verdict = verify_dag_extended(
        parts["dag_b"],
        key_resolver=lambda sid: parts["keys"].get(sid),
        dag_resolver=resolver,
        report_verifier=lambda r: True)
    assert not verdict.valid
    b_dave_hash = parts["b_dave"].link_hash()
    assert b_dave_hash in verdict.extension_results
    assert not verdict.extension_results[b_dave_hash][0].ok
    assert "no such DAG" in \
        verdict.extension_results[b_dave_hash][0].reason


def test_missing_external_link_rejected():
    print("=== External DAG present, but does not contain the link ===")
    parts = _build_two_dags()
    # Sabotage: swap Bob's link reference for a bogus hash
    bogus_hash = "0" * 64
    b_dave = parts["b_dave"]
    payload = canonical_bytes({
        "kind": "attestation_extending_dag_link",
        "signer_id": b_dave.signer_id,
        "signer_name": b_dave.signer_name,
        "previous_link_hashes": sorted(b_dave.previous_link_hashes),
        "report_hash": b_dave.report_hash,
        "timestamp": b_dave.timestamp,
        "external_references": [["dag-a", bogus_hash]],
    })
    sabotaged_dave = ExtendingDAGLink(
        signer_id=b_dave.signer_id,
        signer_name=b_dave.signer_name,
        previous_link_hashes=b_dave.previous_link_hashes,
        report_hash=b_dave.report_hash,
        timestamp=b_dave.timestamp,
        external_references=(("dag-a", bogus_hash),),
        signature=parts["dave_kp"].sign(payload).hex(),
    )
    # Build a new DAG-B with the sabotaged link
    sabotaged_b = AttestedDAG(
        report=parts["dag_b"].report,
        links=[parts["b_root"], sabotaged_dave])

    resolver = DictDAGResolver({
        "dag-a": parts["dag_a"], "dag-b": sabotaged_b})
    verdict = verify_dag_extended(
        sabotaged_b,
        key_resolver=lambda sid: parts["keys"].get(sid),
        dag_resolver=resolver,
        report_verifier=lambda r: True)
    assert not verdict.valid


def test_broken_external_dag_rejected():
    print("=== External DAG is broken → extension fails ===")
    parts = _build_two_dags()
    # Corrupt DAG-A: change a byte in its root's signature
    bad_links = []
    for link in parts["dag_a"].links:
        if isinstance(link, DAGLink) and link.report_hash is not None:
            sig = link.signature
            bad_sig = ("0" if sig[0] != "0" else "1") + sig[1:]
            bad_link = DAGLink(
                signer_id=link.signer_id,
                signer_name=link.signer_name,
                previous_link_hashes=link.previous_link_hashes,
                report_hash=link.report_hash,
                timestamp=link.timestamp,
                signature=bad_sig,
            )
            bad_links.append(bad_link)
        else:
            bad_links.append(link)
    corrupted_a = AttestedDAG(
        report=parts["dag_a"].report, links=bad_links)

    resolver = DictDAGResolver({
        "dag-a": corrupted_a, "dag-b": parts["dag_b"]})
    verdict = verify_dag_extended(
        parts["dag_b"],
        key_resolver=lambda sid: parts["keys"].get(sid),
        dag_resolver=resolver,
        report_verifier=lambda r: True)
    assert not verdict.valid
    # The reason mentions the external DAG failed
    for results in verdict.extension_results.values():
        for r in results:
            if not r.ok:
                assert "external DAG failed" in r.reason \
                    or "INVALID" in r.reason


def test_cycle_detection():
    print("=== Cycle in federated DAGs detected ===")
    # Construct a fake resolver that returns the same DAG for any
    # DAG id — this makes any external reference cycle.
    parts = _build_two_dags()
    def looping_resolver(dag_id):
        return parts["dag_b"]  # always return B

    verdict = verify_dag_extended(
        parts["dag_b"],
        key_resolver=lambda sid: parts["keys"].get(sid),
        dag_resolver=looping_resolver,
        report_verifier=lambda r: True)
    assert not verdict.valid
    assert "cycle" in verdict.reason.lower()


def test_max_depth_enforced():
    print("=== max_depth enforced ===")
    parts = _build_two_dags()
    resolver = DictDAGResolver({
        "dag-a": parts["dag_a"], "dag-b": parts["dag_b"]})
    # Depth 1: DAG-B verification, but not deep enough for DAG-A's
    # own (nonexistent) extensions. DAG-A has no extensions, so
    # actually depth 1 suffices. Test depth 0: fails immediately.
    verdict = verify_dag_extended(
        parts["dag_b"],
        key_resolver=lambda sid: parts["keys"].get(sid),
        dag_resolver=resolver,
        report_verifier=lambda r: True,
        max_depth=0)
    assert not verdict.valid


# =====================================================================
# JSON roundtrip
# =====================================================================

def test_extending_link_json_roundtrip():
    print("=== ExtendingDAGLink JSON roundtrip ===")
    parts = _build_two_dags()
    link = parts["b_dave"]
    wire = json.dumps(link.to_dict())
    revived = ExtendingDAGLink.from_dict(json.loads(wire))
    assert revived.canonical_payload() == link.canonical_payload()
    assert revived.link_hash() == link.link_hash()


# =====================================================================
# Never raises
# =====================================================================

def test_verify_never_raises_on_bad_input():
    print("=== verify_dag_extended never raises ===")
    assert not verify_dag_extended(
        None, lambda s: None, lambda d: None).valid
    assert not verify_dag_extended(
        "not a dag", lambda s: None, lambda d: None).valid
    # Resolver raising
    parts = _build_two_dags()
    def raising(sid):
        raise RuntimeError("boom")
    verdict = verify_dag_extended(
        parts["dag_a"], raising,
        DictDAGResolver({"dag-a": parts["dag_a"]}))
    assert not verdict.valid
    assert "boom" in verdict.reason


def test_dag_resolver_raising_is_caught():
    print("=== dag_resolver raising is caught ===")
    parts = _build_two_dags()
    def raising_dag(dag_id):
        raise RuntimeError("boom")
    verdict = verify_dag_extended(
        parts["dag_b"],
        key_resolver=lambda sid: parts["keys"].get(sid),
        dag_resolver=raising_dag,
        report_verifier=lambda r: True)
    assert not verdict.valid


# =====================================================================
# Composition with C27's plain verifier
# =====================================================================

def test_dag_a_verifies_with_c27_verifier():
    """A DAG with only DAGLinks (no extensions) verifies with C27's
    verify_dag unchanged."""
    print("=== DAG-A verifies with C27's verify_dag (unchanged) ===")
    parts = _build_two_dags()
    verdict = verify_dag(
        parts["dag_a"],
        key_resolver=lambda sid: parts["keys"].get(sid),
        report_verifier=lambda r: True)
    assert verdict.valid
    assert verdict.verified_signers == ["Alice", "Bob"]


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: two DAGs, cross-DAG extension ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["dag_a_valid"] is True
    assert audit["dag_b_valid"] is True
    assert audit["dag_b_extends_dag_a"] is True
    assert (tmp_path / "cross_dag_demo.json").exists()


if __name__ == "__main__":
    test_extending_link_requires_external_refs()
    test_extending_link_rejects_duplicate_refs()
    test_extending_link_rejects_bad_link_hash()
    test_extending_link_is_distinct_from_dag_link()
    test_dag_a_verifies_independently()
    test_dag_b_verifies_with_extension()
    test_missing_external_dag_rejected()
    test_missing_external_link_rejected()
    test_broken_external_dag_rejected()
    test_cycle_detection()
    test_max_depth_enforced()
    test_extending_link_json_roundtrip()
    test_verify_never_raises_on_bad_input()
    test_dag_resolver_raising_is_caught()
    test_dag_a_verifies_with_c27_verifier()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
