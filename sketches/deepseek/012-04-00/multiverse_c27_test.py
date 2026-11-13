# multiverse_c27_test.py
import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c13 import HAS_CRYPTO, KeyPair
from multiverse_c15 import PassportEntry
from multiverse_c21 import ProvenanceReport, EntryProvenance
from multiverse_c24 import sign_report, verify_signed_report
from multiverse_c26 import revoke, RevocationSet
from multiverse_c27 import (
    DAGLink, AttestedDAG, DAGVerdict, DAGBuilder, DAGCombinedVerdict,
    verify_dag, verify_dag_with_revocations, demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _stub_report():
    alice_kp = KeyPair.generate()
    alice = create_identity("Alice")
    rep = ProvenanceReport(
        passport_token="alice-token", passport_name="Alice",
        registry_url="http://r",
    )
    entry = PassportEntry(
        entity_id="world:a", timestamp="2024-01-01T00:00:00+00:00",
        subject_token="alice-token", signature="cc" * 64,
    )
    ep = EntryProvenance(entry=entry)
    ep.verdict = "verified"
    ep.reason = "stub"
    rep.entries.append(ep)
    return sign_report(rep, alice_kp, alice), alice_kp, alice


def _build_fork_merge():
    """Canonical DAG: Alice root, Bob + Carol fork, Dave merges."""
    signed_report, alice_kp, alice = _stub_report()
    bob_kp = KeyPair.generate(); bob = create_identity("Bob")
    carol_kp = KeyPair.generate(); carol = create_identity("Carol")
    dave_kp = KeyPair.generate(); dave = create_identity("Dave")
    keys = {
        alice.token: alice_kp.public_key_hex(),
        bob.token: bob_kp.public_key_hex(),
        carol.token: carol_kp.public_key_hex(),
        dave.token: dave_kp.public_key_hex(),
    }
    builder = DAGBuilder(signed_report)
    root = builder.attest(alice_kp, alice)
    bob_link = builder.attest(
        bob_kp, bob, previous_link_hashes=(root.link_hash(),))
    carol_link = builder.attest(
        carol_kp, carol, previous_link_hashes=(root.link_hash(),))
    dave_link = builder.attest(
        dave_kp, dave,
        previous_link_hashes=(bob_link.link_hash(),
                              carol_link.link_hash()))
    return (builder.build(), signed_report, alice_kp, alice,
            keys, {"bob": (bob, bob_kp, bob_link),
                   "carol": (carol, carol_kp, carol_link),
                   "dave": (dave, dave_kp, dave_link)})


# =====================================================================
# Construction
# =====================================================================

def test_dag_link_root_required():
    print("=== Root requires report_hash, non-root requires previous ===")
    with pytest.raises(ValueError):
        DAGLink(signer_id="x", signer_name="X",
                previous_link_hashes=(), report_hash=None,
                timestamp="t", signature="s")
    with pytest.raises(ValueError):
        DAGLink(signer_id="x", signer_name="X",
                previous_link_hashes=("a" * 64,), report_hash="r",
                timestamp="t", signature="s")


def test_dag_link_forbids_duplicate_previous():
    print("=== previous_link_hashes must not contain duplicates ===")
    with pytest.raises(ValueError):
        DAGLink(signer_id="x", signer_name="X",
                previous_link_hashes=("a" * 64, "a" * 64),
                report_hash=None, timestamp="t", signature="s")


def test_dag_link_canonical_payload_order_independent():
    print("=== canonical_payload sorts previous hashes ===")
    a, b = "a" * 64, "b" * 64
    l1 = DAGLink(signer_id="x", signer_name="X",
                 previous_link_hashes=(a, b), report_hash=None,
                 timestamp="t", signature="s")
    l2 = DAGLink(signer_id="x", signer_name="X",
                 previous_link_hashes=(b, a), report_hash=None,
                 timestamp="t", signature="s")
    assert l1.canonical_payload() == l2.canonical_payload()
    assert l1.link_hash() == l2.link_hash()


# =====================================================================
# Builder
# =====================================================================

def test_builder_first_must_be_root():
    print("=== Builder: first link must be root ===")
    signed_report, _, _ = _stub_report()
    builder = DAGBuilder(signed_report)
    kp = KeyPair.generate(); who = create_identity("X")
    with pytest.raises(ValueError):
        builder.attest(kp, who,
                       previous_link_hashes=("a" * 64,))


def test_builder_second_requires_previous():
    print("=== Builder: non-root requires previous hash ===")
    signed_report, alice_kp, alice = _stub_report()
    builder = DAGBuilder(signed_report)
    builder.attest(alice_kp, alice)
    kp = KeyPair.generate(); who = create_identity("X")
    with pytest.raises(ValueError):
        builder.attest(kp, who)


def test_builder_rejects_unknown_previous():
    print("=== Builder: unknown previous hash rejected ===")
    signed_report, alice_kp, alice = _stub_report()
    builder = DAGBuilder(signed_report)
    builder.attest(alice_kp, alice)
    kp = KeyPair.generate(); who = create_identity("X")
    with pytest.raises(ValueError):
        builder.attest(kp, who, previous_link_hashes=("f" * 64,))


# =====================================================================
# Happy path
# =====================================================================

def test_root_only_verifies():
    print("=== Root-only DAG verifies ===")
    signed_report, alice_kp, alice = _stub_report()
    builder = DAGBuilder(signed_report)
    builder.attest(alice_kp, alice)
    dag = builder.build()
    keys = {alice.token: alice_kp.public_key_hex()}
    verdict = verify_dag(dag, lambda sid: keys.get(sid))
    assert verdict.valid
    assert verdict.verified_signers == ["Alice"]
    assert verdict.leaf_signers == ["Alice"]


def test_fork_verifies():
    print("=== Fork verifies (Bob and Carol both witness Alice) ===")
    signed_report, alice_kp, alice = _stub_report()
    bob_kp = KeyPair.generate(); bob = create_identity("Bob")
    carol_kp = KeyPair.generate(); carol = create_identity("Carol")
    keys = {
        alice.token: alice_kp.public_key_hex(),
        bob.token: bob_kp.public_key_hex(),
        carol.token: carol_kp.public_key_hex(),
    }
    builder = DAGBuilder(signed_report)
    root = builder.attest(alice_kp, alice)
    builder.attest(bob_kp, bob, previous_link_hashes=(root.link_hash(),))
    builder.attest(carol_kp, carol,
                    previous_link_hashes=(root.link_hash(),))
    dag = builder.build()
    verdict = verify_dag(dag, lambda sid: keys.get(sid))
    print(verdict.format())
    assert verdict.valid
    # Alice first, then Bob and Carol in some order
    assert verdict.verified_signers[0] == "Alice"
    assert set(verdict.verified_signers) == {"Alice", "Bob", "Carol"}
    # Both Bob and Carol are leaves
    assert set(verdict.leaf_signers) == {"Bob", "Carol"}


def test_fork_merge_verifies():
    print("=== Fork + merge DAG verifies ===")
    (dag, signed_report, alice_kp, alice, keys, _) = _build_fork_merge()
    verdict = verify_dag(
        dag, lambda sid: keys.get(sid),
        report_verifier=lambda r: verify_signed_report(
            r, alice_kp.public_key_hex()))
    print(verdict.format())
    assert verdict.valid
    # Alice first; Dave last
    assert verdict.verified_signers[0] == "Alice"
    assert verdict.verified_signers[-1] == "Dave"
    # Dave is the only leaf (Bob and Carol are referenced by Dave)
    assert verdict.leaf_signers == ["Dave"]


# =====================================================================
# Failure modes
# =====================================================================

def test_no_root_rejected():
    print("=== DAG without a root rejected ===")
    signed_report, alice_kp, alice = _stub_report()
    # Construct manually: two non-root links referencing a phantom hash
    bogus = "0" * 64
    l1 = DAGLink(signer_id=alice.token, signer_name=alice.name,
                 previous_link_hashes=(bogus,), report_hash=None,
                 timestamp="t", signature="s")
    l2 = DAGLink(signer_id="x", signer_name="X",
                 previous_link_hashes=(bogus,), report_hash=None,
                 timestamp="t", signature="s")
    dag = AttestedDAG(report=signed_report, links=[l1, l2])
    verdict = verify_dag(dag, lambda sid: None)
    assert not verdict.valid
    assert "root" in verdict.reason.lower()


def test_two_roots_rejected():
    print("=== DAG with two roots rejected ===")
    signed_report, alice_kp, alice = _stub_report()
    builder = DAGBuilder(signed_report)
    builder.attest(alice_kp, alice)
    # Manually append a second root
    other_kp = KeyPair.generate(); other = create_identity("Other")
    from multiverse_c27 import _canonical_link_payload, _hash_payload
    report_hash = _hash_payload(signed_report.canonical_payload())
    payload = _canonical_link_payload(
        other.token, other.name, (), report_hash, "t")
    second_root = DAGLink(
        signer_id=other.token, signer_name=other.name,
        previous_link_hashes=(), report_hash=report_hash,
        timestamp="t", signature=other_kp.sign(payload).hex())
    dag = AttestedDAG(
        report=signed_report, links=builder.build().links + [second_root])
    verdict = verify_dag(dag, lambda sid: (
        alice_kp.public_key_hex() if sid == alice.token
        else other_kp.public_key_hex() if sid == other.token
        else None))
    assert not verdict.valid
    assert "root" in verdict.reason.lower()


def test_report_hash_mismatch_rejected():
    print("=== Root report_hash mismatch rejected ===")
    signed_report, alice_kp, alice = _stub_report()
    builder = DAGBuilder(signed_report)
    builder.attest(alice_kp, alice)
    dag = builder.build()
    # Swap in a different report
    other_report, _, _ = _stub_report()
    dag.report = other_report
    verdict = verify_dag(
        dag, lambda sid: alice_kp.public_key_hex())
    assert not verdict.valid
    assert "report_hash" in verdict.reason.lower()


def test_unknown_previous_rejected():
    print("=== Unknown previous hash rejected ===")
    signed_report, alice_kp, alice = _stub_report()
    bogus = "0" * 64
    l1 = DAGLink(signer_id=alice.token, signer_name=alice.name,
                 previous_link_hashes=(), report_hash="0" * 64,
                 timestamp="t", signature="s")
    l2 = DAGLink(signer_id="x", signer_name="X",
                 previous_link_hashes=(bogus,), report_hash=None,
                 timestamp="t", signature="s")
    dag = AttestedDAG(report=signed_report, links=[l1, l2])
    verdict = verify_dag(dag, lambda sid: "aa" * 32)
    assert not verdict.valid
    assert "unknown" in verdict.reason.lower()


def test_forged_link_rejected():
    print("=== Forged link (wrong signing key) rejected ===")
    (dag, _, _, _, keys, _) = _build_fork_merge()
    # Corrupt Bob's key
    bob_id = [k for k in keys if keys[k] and k.endswith("")][0]  # any
    # Instead, replace keys map to a wrong key for one signer
    bogus_keys = dict(keys)
    first_non_alice = list(bogus_keys.keys())[1]
    bogus_keys[first_non_alice] = KeyPair.generate().public_key_hex()
    verdict = verify_dag(dag, lambda sid: bogus_keys.get(sid))
    assert not verdict.valid


def test_duplicate_link_hash_rejected():
    print("=== Duplicate link hash rejected ===")
    signed_report, alice_kp, alice = _stub_report()
    builder = DAGBuilder(signed_report)
    root = builder.attest(alice_kp, alice)
    dag = builder.build()
    # Manually duplicate the root
    dag.links.append(root)
    verdict = verify_dag(
        dag, lambda sid: alice_kp.public_key_hex())
    assert not verdict.valid
    assert "duplicate" in verdict.reason.lower()


def test_never_raises_on_bad_input():
    print("=== verify_dag never raises on bad input ===")
    assert not verify_dag(None, lambda s: None).valid
    assert not verify_dag("not-a-dag", lambda s: None).valid
    assert not verify_dag({}, lambda s: None).valid


def test_key_resolver_raising_is_caught():
    print("=== key_resolver raising is caught ===")
    (dag, _, _, _, keys, _) = _build_fork_merge()
    def raising(sid):
        raise RuntimeError("boom")
    verdict = verify_dag(dag, raising)
    assert not verdict.valid
    assert "boom" in verdict.reason


# =====================================================================
# JSON roundtrip
# =====================================================================

def test_dag_json_roundtrip():
    print("=== DAG JSON roundtrip preserves verification ===")
    (dag, signed_report, alice_kp, alice, keys, _) = _build_fork_merge()
    wire = json.dumps(dag.to_dict())
    revived = AttestedDAG.from_dict(json.loads(wire))
    verdict = verify_dag(
        revived, lambda sid: keys.get(sid),
        report_verifier=lambda r: verify_signed_report(
            r, alice_kp.public_key_hex()))
    assert verdict.valid


# =====================================================================
# Revocation composition
# =====================================================================

def test_revoke_one_branch_noncascade():
    print("=== Revoking Bob does not revoke Dave (non-cascade) ===")
    (dag, signed_report, alice_kp, alice, keys, branches
    ) = _build_fork_merge()
    bob, bob_kp, bob_link = branches["bob"]
    rev = revoke(bob_link, bob_kp, bob, reason="retracted")
    rev_set = RevocationSet()
    rev_set.add(rev)

    combined = verify_dag_with_revocations(
        dag, rev_set, lambda sid: keys.get(sid),
        report_verifier=lambda r: verify_signed_report(
            r, alice_kp.public_key_hex()))
    print(combined.format())
    assert combined.valid
    # Bob is revoked; Alice, Carol, Dave are still effective
    assert "Bob" in combined.revoked_signers
    assert set(combined.effective_signers) == {"Alice", "Carol", "Dave"}


def test_revocation_target_not_in_dag():
    print("=== Revocation targeting a non-DAG hash rejected ===")
    (dag, _, _, _, keys, _) = _build_fork_merge()
    # Revoke a hash that doesn't exist in the DAG
    from multiverse_c13 import canonical_bytes
    kp = KeyPair.generate()
    who = create_identity("Somebody")
    bogus = "0" * 64
    payload = canonical_bytes({
        "kind": "revocation", "link_hash": bogus,
        "revoker_id": who.token, "revoker_name": who.name,
        "timestamp": "t", "reason": "",
    })
    from multiverse_c26 import Revocation
    fake_rev = Revocation(
        link_hash=bogus, revoker_id=who.token,
        revoker_name=who.name, timestamp="t", reason="",
        signature=kp.sign(payload).hex())
    rev_set = RevocationSet(); rev_set.add(fake_rev)

    keys_with_who = dict(keys)
    keys_with_who[who.token] = kp.public_key_hex()
    combined = verify_dag_with_revocations(
        dag, rev_set, lambda sid: keys_with_who.get(sid))
    assert not combined.valid
    assert any("target" in r[1].lower()
                for r in combined.rejected_revocations)


def test_forged_revocation_rejected():
    print("=== Forged revocation rejected ===")
    (dag, _, _, _, keys, branches) = _build_fork_merge()
    bob, bob_kp, bob_link = branches["bob"]
    # Attacker signs a revocation pretending to be Bob
    attacker = KeyPair.generate()
    from multiverse_c13 import canonical_bytes
    payload = canonical_bytes({
        "kind": "revocation",
        "link_hash": bob_link.link_hash(),
        "revoker_id": bob.token,
        "revoker_name": bob.name,
        "timestamp": "t",
        "reason": "",
    })
    from multiverse_c26 import Revocation
    forged = Revocation(
        link_hash=bob_link.link_hash(), revoker_id=bob.token,
        revoker_name=bob.name, timestamp="t", reason="",
        signature=attacker.sign(payload).hex())
    rev_set = RevocationSet(); rev_set.add(forged)
    combined = verify_dag_with_revocations(
        dag, rev_set, lambda sid: keys.get(sid))
    assert not combined.valid
    assert any("INVALID" in r[1] for r in combined.rejected_revocations)


def test_combined_to_dict_json():
    print("=== DAGCombinedVerdict to_dict is JSON-serializable ===")
    (dag, _, _, _, keys, _) = _build_fork_merge()
    combined = verify_dag_with_revocations(
        dag, RevocationSet(), lambda sid: keys.get(sid))
    d = combined.to_dict()
    s = json.dumps(d)
    parsed = json.loads(s)
    assert parsed["valid"] is True
    assert parsed["effective_signers"] == ["Alice", "Bob", "Carol", "Dave"]


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: fork + merge + revocation ===")
    combined = demo(artifact_dir=str(tmp_path))
    assert combined.valid
    # Alice, Carol, Dave remain effective; Bob was revoked
    assert set(combined.effective_signers) == {"Alice", "Carol", "Dave"}
    assert combined.revoked_signers == ["Bob"]
    assert (tmp_path / "attested_dag.json").exists()
    assert (tmp_path / "attested_dag_verdict.json").exists()
    data = json.loads(
        (tmp_path / "attested_dag_verdict.json").read_text())
    assert data["valid"] is True


if __name__ == "__main__":
    test_dag_link_root_required()
    test_dag_link_forbids_duplicate_previous()
    test_dag_link_canonical_payload_order_independent()
    test_builder_first_must_be_root()
    test_builder_second_requires_previous()
    test_builder_rejects_unknown_previous()
    test_root_only_verifies()
    test_fork_verifies()
    test_fork_merge_verifies()
    test_no_root_rejected()
    test_two_roots_rejected()
    test_report_hash_mismatch_rejected()
    test_unknown_previous_rejected()
    test_forged_link_rejected()
    test_duplicate_link_hash_rejected()
    test_never_raises_on_bad_input()
    test_key_resolver_raising_is_caught()
    test_dag_json_roundtrip()
    test_revoke_one_branch_noncascade()
    test_revocation_target_not_in_dag()
    test_forged_revocation_rejected()
    test_combined_to_dict_json()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
