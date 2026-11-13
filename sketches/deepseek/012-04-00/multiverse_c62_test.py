import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c62 import (
    CommitmentRecord, verify_commitment,
    _leaf_hash, _internal_hash, _level_sizes,
    merkle_root, inclusion_proof, verify_inclusion,
    CommitmentLog, ChainVerdict, verify_commitment_chain,
    SignedTreeHead, verify_tree_head,
    CheckpointPublisher,
    artifact_hash,
    demo,
    _hash_payload,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _make_log(n=3):
    log = CommitmentLog()
    kp = KeyPair.generate()
    records = []
    for i in range(n):
        r = log.append(
            artifact_hash=_hash_payload(f"art-{i}".encode()),
            artifact_kind=f"kind-{i}",
            committer_world_id=f"world:{i}",
            committer_kp=kp,
        )
        records.append(r)
    return log, kp, records


# =====================================================================
# CommitmentRecord
# =====================================================================

def test_record_validates_fields():
    print("=== CommitmentRecord: validates fields ===")
    with pytest.raises(ValueError):
        CommitmentRecord(
            commit_index=-1,
            artifact_hash="aa" * 32,
            artifact_kind="x",
            committer_world_id="w",
            committer_public_key="aa" * 32,
            timestamp_claimed="t",
            signature="s",
            previous_commit_hash=None)
    with pytest.raises(ValueError):
        CommitmentRecord(
            commit_index=0,
            artifact_hash="short",
            artifact_kind="x",
            committer_world_id="w",
            committer_public_key="aa" * 32,
            timestamp_claimed="t",
            signature="s",
            previous_commit_hash=None)


def test_record_signature_verifies():
    print("=== verify_commitment: signature valid ===")
    log, kp, records = _make_log(1)
    r = records[0]
    assert verify_commitment(r)


def test_record_wrong_key():
    print("=== verify_commitment: wrong key → False ===")
    log, kp, records = _make_log(1)
    r = records[0]
    tampered = CommitmentRecord(
        commit_index=r.commit_index,
        artifact_hash=r.artifact_hash,
        artifact_kind=r.artifact_kind,
        committer_world_id=r.committer_world_id,
        committer_public_key=KeyPair.generate().public_key_hex(),
        timestamp_claimed=r.timestamp_claimed,
        signature=r.signature,
        previous_commit_hash=r.previous_commit_hash)
    assert not verify_commitment(tampered)


def test_record_tampered_payload():
    print("=== verify_commitment: tampered artifact_hash → False ===")
    log, kp, records = _make_log(1)
    r = records[0]
    tampered = CommitmentRecord(
        commit_index=r.commit_index,
        artifact_hash="ff" * 32,
        artifact_kind=r.artifact_kind,
        committer_world_id=r.committer_world_id,
        committer_public_key=r.committer_public_key,
        timestamp_claimed=r.timestamp_claimed,
        signature=r.signature,
        previous_commit_hash=r.previous_commit_hash)
    assert not verify_commitment(tampered)


def test_record_json_roundtrip():
    print("=== CommitmentRecord: JSON roundtrip ===")
    log, kp, records = _make_log(1)
    wire = json.dumps(records[0].to_dict())
    revived = CommitmentRecord.from_dict(json.loads(wire))
    assert verify_commitment(revived)
    assert revived.ledger_commit_hash() == \
        records[0].ledger_commit_hash()


# =====================================================================
# CommitmentLog
# =====================================================================

def test_log_append_assigns_indices():
    print("=== Log: append assigns monotonic indices ===")
    log, kp, records = _make_log(3)
    for i, r in enumerate(records):
        assert r.commit_index == i
    assert log.size() == 3


def test_log_append_chains_previous_hash():
    print("=== Log: append chains previous_commit_hash ===")
    log, kp, records = _make_log(3)
    assert records[0].previous_commit_hash is None
    assert records[1].previous_commit_hash == \
        records[0].ledger_commit_hash()
    assert records[2].previous_commit_hash == \
        records[1].ledger_commit_hash()


def test_log_append_rejects_bad_hash():
    print("=== Log: append rejects bad artifact_hash ===")
    log = CommitmentLog()
    kp = KeyPair.generate()
    for bad in ("short", "", "gg" * 32, 123):
        with pytest.raises((ValueError, TypeError)):
            log.append(
                artifact_hash=bad,
                artifact_kind="x",
                committer_world_id="w",
                committer_kp=kp)


def test_log_get_commit():
    print("=== Log: get_commit returns all for a hash ===")
    log = CommitmentLog()
    kp = KeyPair.generate()
    h = "aa" * 32
    log.append(h, "kind-a", "world:1", kp)
    log.append("bb" * 32, "kind-b", "world:2", kp)
    log.append(h, "kind-a", "world:3", kp)
    matches = log.get_commit(h)
    assert len(matches) == 2
    assert matches[0].commit_index == 0
    assert matches[1].commit_index == 2


def test_log_get_commits_by_kind():
    print("=== Log: get_commits_by_kind ===")
    log = CommitmentLog()
    kp = KeyPair.generate()
    log.append("aa" * 32, "kind-x", "world:1", kp)
    log.append("bb" * 32, "kind-y", "world:2", kp)
    log.append("cc" * 32, "kind-x", "world:3", kp)
    matches = log.get_commits_by_kind("kind-x")
    assert len(matches) == 2
    # Since index
    matches_from_1 = log.get_commits_by_kind(
        "kind-x", since_index=1)
    assert len(matches_from_1) == 1


def test_log_get_commit_chain():
    print("=== Log: get_commit_chain clamps bounds ===")
    log, kp, records = _make_log(5)
    chain = log.get_commit_chain(1, 4)
    assert len(chain) == 3
    # Out of bounds
    assert log.get_commit_chain(10, 20) == []
    assert log.get_commit_chain(-5, 2) == \
        log.get_commit_chain(0, 2)


def test_log_first_commit_index():
    print("=== Log: first_commit_index ===")
    log = CommitmentLog()
    kp = KeyPair.generate()
    h = "aa" * 32
    log.append("bb" * 32, "k", "w", kp)
    log.append(h, "k", "w", kp)
    log.append(h, "k", "w", kp)
    assert log.first_commit_index(h) == 1
    assert log.first_commit_index("ff" * 32) is None


# =====================================================================
# Merkle tree
# =====================================================================

def test_level_sizes():
    print("=== _level_sizes ===")
    assert _level_sizes(1) == [1]
    assert _level_sizes(2) == [2, 1]
    assert _level_sizes(3) == [3, 2, 1]
    assert _level_sizes(5) == [5, 3, 2, 1]
    assert _level_sizes(8) == [8, 4, 2, 1]
    assert _level_sizes(0) == []


def test_merkle_root_empty():
    print("=== merkle_root: empty → empty string ===")
    assert merkle_root([]) == ""


def test_merkle_root_single():
    print("=== merkle_root: one leaf → leaf hash ===")
    h = "aa" * 32
    assert merkle_root([h]) == _leaf_hash(h)


def test_merkle_root_two():
    print("=== merkle_root: two leaves ===")
    a, b = "aa" * 32, "bb" * 32
    assert merkle_root([a, b]) == _internal_hash(
        _leaf_hash(a), _leaf_hash(b))


def test_merkle_root_three():
    print("=== merkle_root: three leaves (promotion) ===")
    a, b, c = "aa" * 32, "bb" * 32, "cc" * 32
    expected = _internal_hash(
        _internal_hash(_leaf_hash(a), _leaf_hash(b)),
        _leaf_hash(c))
    assert merkle_root([a, b, c]) == expected


def test_merkle_root_deterministic():
    print("=== merkle_root: deterministic ===")
    leaves = ["aa" * 32, "bb" * 32, "cc" * 32, "dd" * 32]
    assert merkle_root(leaves) == merkle_root(list(leaves))


# =====================================================================
# Inclusion proofs
# =====================================================================

def test_inclusion_proof_single():
    print("=== inclusion_proof: single leaf → empty proof ===")
    assert inclusion_proof(["aa" * 32], 0) == []


def test_inclusion_proof_two():
    print("=== inclusion_proof: two leaves ===")
    a, b = "aa" * 32, "bb" * 32
    proof_a = inclusion_proof([a, b], 0)
    proof_b = inclusion_proof([a, b], 1)
    assert proof_a == [_leaf_hash(b)]
    assert proof_b == [_leaf_hash(a)]


def test_inclusion_proof_three_promoted():
    print("=== inclusion_proof: three leaves, last promoted ===")
    a, b, c = "aa" * 32, "bb" * 32, "cc" * 32
    # Leaf 0: sibling b, then sibling c (at next level, index 0
    # of size-2 level whose sibling is c)
    proof_0 = inclusion_proof([a, b, c], 0)
    assert len(proof_0) == 2
    # Leaf 2 (c): promoted at level 0, so no sibling.
    # At level 1, sibling is H(a,b).
    proof_2 = inclusion_proof([a, b, c], 2)
    assert len(proof_2) == 1


def test_inclusion_proof_range():
    print("=== inclusion_proof: out-of-range → IndexError ===")
    with pytest.raises(IndexError):
        inclusion_proof(["aa" * 32], 1)
    with pytest.raises(IndexError):
        inclusion_proof(["aa" * 32], -1)
    with pytest.raises(ValueError):
        inclusion_proof([], 0)


def test_verify_inclusion_happy():
    print("=== verify_inclusion: happy path ===")
    leaves = ["aa" * 32, "bb" * 32, "cc" * 32, "dd" * 32]
    root = merkle_root(leaves)
    for i in range(4):
        proof = inclusion_proof(leaves, i)
        assert verify_inclusion(leaves[i], proof, i, 4, root)


def test_verify_inclusion_three():
    print("=== verify_inclusion: three leaves (odd) ===")
    leaves = ["aa" * 32, "bb" * 32, "cc" * 32]
    root = merkle_root(leaves)
    for i in range(3):
        proof = inclusion_proof(leaves, i)
        assert verify_inclusion(leaves[i], proof, i, 3, root)


def test_verify_inclusion_five():
    print("=== verify_inclusion: five leaves (odd twice) ===")
    leaves = [_hash_payload(f"x{i}".encode()) for i in range(5)]
    root = merkle_root(leaves)
    for i in range(5):
        proof = inclusion_proof(leaves, i)
        assert verify_inclusion(leaves[i], proof, i, 5, root)


def test_verify_inclusion_wrong_leaf():
    print("=== verify_inclusion: wrong leaf → False ===")
    leaves = ["aa" * 32, "bb" * 32]
    root = merkle_root(leaves)
    proof = inclusion_proof(leaves, 0)
    wrong_leaf = "ff" * 32
    assert not verify_inclusion(
        wrong_leaf, proof, 0, 2, root)


def test_verify_inclusion_wrong_root():
    print("=== verify_inclusion: wrong root → False ===")
    leaves = ["aa" * 32, "bb" * 32]
    proof = inclusion_proof(leaves, 0)
    assert not verify_inclusion(
        leaves[0], proof, 0, 2, "00" * 32)


def test_verify_inclusion_tampered_proof():
    print("=== verify_inclusion: tampered proof → False ===")
    leaves = ["aa" * 32, "bb" * 32, "cc" * 32]
    root = merkle_root(leaves)
    proof = inclusion_proof(leaves, 0)
    tampered = ["00" * 32] + proof[1:]
    assert not verify_inclusion(
        leaves[0], tampered, 0, 3, root)


def test_verify_inclusion_extra_hashes():
    print("=== verify_inclusion: extra hashes → False ===")
    leaves = ["aa" * 32, "bb" * 32]
    root = merkle_root(leaves)
    proof = inclusion_proof(leaves, 0)
    extra = proof + ["00" * 32]
    assert not verify_inclusion(
        leaves[0], extra, 0, 2, root)


def test_verify_inclusion_empty_proof():
    print("=== verify_inclusion: empty proof for n>1 → False ===")
    leaves = ["aa" * 32, "bb" * 32]
    root = merkle_root(leaves)
    assert not verify_inclusion(
        leaves[0], [], 0, 2, root)


# =====================================================================
# Chain verification
# =====================================================================

def test_chain_verify_happy():
    print("=== verify_commitment_chain: happy ===")
    log, kp, records = _make_log(5)
    v = verify_commitment_chain(log.entries())
    assert v.valid


def test_chain_verify_tampered_index():
    print("=== chain: tampered index → invalid ===")
    log, kp, records = _make_log(3)
    # Tamper record 1's index
    tampered = CommitmentRecord(
        commit_index=5,
        artifact_hash=records[1].artifact_hash,
        artifact_kind=records[1].artifact_kind,
        committer_world_id=records[1].committer_world_id,
        committer_public_key=records[1].committer_public_key,
        timestamp_claimed=records[1].timestamp_claimed,
        signature=records[1].signature,
        previous_commit_hash=records[1].previous_commit_hash)
    entries = [records[0], tampered, records[2]]
    v = verify_commitment_chain(entries)
    assert not v.valid
    assert v.bad_index == 1


def test_chain_verify_broken_link():
    print("=== chain: broken previous_commit_hash → invalid ===")
    log, kp, records = _make_log(3)
    # Tamper record 2's previous_commit_hash
    tampered = CommitmentRecord(
        commit_index=2,
        artifact_hash=records[2].artifact_hash,
        artifact_kind=records[2].artifact_kind,
        committer_world_id=records[2].committer_world_id,
        committer_public_key=records[2].committer_public_key,
        timestamp_claimed=records[2].timestamp_claimed,
        signature=records[2].signature,
        previous_commit_hash="ff" * 32)
    entries = [records[0], records[1], tampered]
    v = verify_commitment_chain(entries)
    assert not v.valid
    assert v.bad_index == 2


def test_chain_verify_tampered_sig():
    print("=== chain: tampered signature → invalid ===")
    log, kp, records = _make_log(3)
    # Tamper record 1's signature but keep everything else
    attacker = KeyPair.generate()
    tampered = CommitmentRecord(
        commit_index=1,
        artifact_hash=records[1].artifact_hash,
        artifact_kind=records[1].artifact_kind,
        committer_world_id=records[1].committer_world_id,
        committer_public_key=records[1].committer_public_key,
        timestamp_claimed=records[1].timestamp_claimed,
        signature=attacker.sign(
            records[1].commitment_payload()).hex(),
        previous_commit_hash=records[1].previous_commit_hash)
    entries = [records[0], tampered, records[2]]
    v = verify_commitment_chain(entries)
    assert not v.valid
    assert v.bad_index == 1


def test_chain_verify_empty():
    print("=== chain: empty log is trivially valid ===")
    v = verify_commitment_chain([])
    assert v.valid


# =====================================================================
# Tree head
# =====================================================================

def test_tree_head_sign_verify():
    print("=== SignedTreeHead: sign and verify ===")
    log, kp, _ = _make_log(3)
    fed_kp = KeyPair.generate()
    publisher = CheckpointPublisher(log, fed_kp)
    head = publisher.publish()
    assert head.tree_size == 3
    assert head.root_hash == log.merkle_root()
    assert verify_tree_head(head, fed_kp.public_key_hex())


def test_tree_head_wrong_key():
    print("=== SignedTreeHead: wrong key → False ===")
    log, _, _ = _make_log(3)
    fed_kp = KeyPair.generate()
    head = CheckpointPublisher(log, fed_kp).publish()
    wrong = KeyPair.generate()
    assert not verify_tree_head(head, wrong.public_key_hex())


def test_tree_head_json_roundtrip():
    print("=== SignedTreeHead: JSON roundtrip ===")
    log, _, _ = _make_log(3)
    fed_kp = KeyPair.generate()
    head = CheckpointPublisher(log, fed_kp).publish()
    wire = json.dumps(head.to_dict())
    revived = SignedTreeHead.from_dict(json.loads(wire))
    assert verify_tree_head(revived, fed_kp.public_key_hex())


def test_tree_head_empty_log():
    print("=== SignedTreeHead: empty log ===")
    log = CommitmentLog()
    fed_kp = KeyPair.generate()
    head = CheckpointPublisher(log, fed_kp).publish()
    assert head.tree_size == 0
    assert head.root_hash == ""
    assert verify_tree_head(head, fed_kp.public_key_hex())


# =====================================================================
# Integration: append, checkpoint, prove, verify
# =====================================================================

def test_full_flow():
    print("=== Full flow: append 4 commits, checkpoint, prove ===")
    log = CommitmentLog()
    kp = KeyPair.generate()
    hashes = [_hash_payload(f"h{i}".encode()) for i in range(4)]
    for h in hashes:
        log.append(
            artifact_hash=h,
            artifact_kind="test",
            committer_world_id="world:test",
            committer_kp=kp)
    fed_kp = KeyPair.generate()
    head = CheckpointPublisher(log, fed_kp).publish()
    assert verify_tree_head(head, fed_kp.public_key_hex())
    for i, h in enumerate(hashes):
        proof = log.inclusion_proof_for(i)
        assert verify_inclusion(
            log.entries()[i].ledger_commit_hash(),
            proof, i, log.size(), head.root_hash)


# =====================================================================
# Artifact hash helper
# =====================================================================

def test_artifact_hash_has_content_hash():
    print("=== artifact_hash: uses content_hash when present ===")
    class FakeArtifact:
        content_hash = "cc" * 32
    assert artifact_hash(FakeArtifact()) == "cc" * 32


def test_artifact_hash_has_canonical_payload():
    print("=== artifact_hash: uses canonical_payload ===")
    class FakeArtifact:
        def canonical_payload(self):
            return b"test-bytes"
    h = artifact_hash(FakeArtifact())
    assert len(h) == 64
    assert h == _hash_payload(b"test-bytes")


def test_artifact_hash_unknown_type():
    print("=== artifact_hash: unknown type → TypeError ===")
    with pytest.raises(TypeError):
        artifact_hash(object())


# =====================================================================
# Never raises
# =====================================================================

def test_verifiers_never_raise():
    print("=== Verifiers: never raise ===")
    assert not verify_commitment(None)
    assert not verify_commitment("not a record")
    assert not verify_tree_head(None)
    assert not verify_inclusion(
        "aa" * 32, [], 0, 0, "bb" * 32)


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: Appendix A scenario ===")
    audit = demo(artifact_dir=str(tmp_path))
    a = audit["case_a"]
    assert a["chain_valid"] is True
    assert a["head_signed"] is True
    assert a["tree_size"] == 3
    assert all(p["verified"] for p in a["proofs"])
    # Claimed order matches commit order in Case A
    assert a["first_seen"]["establishment"] == 0
    assert a["first_seen"]["citation"] == 1
    assert a["first_seen"]["revocation"] == 2

    b = audit["case_b"]
    assert b["chain_valid"] is True
    assert b["head_signed"] is True
    assert b["tree_size"] == 3
    assert all(p["verified"] for p in b["proofs"])
    # In Case B, commit order differs from claimed order:
    # revocation (claim 18:00) was committed at index 1,
    # citation (claim 17:00) at index 2
    assert b["first_seen"]["establishment"] == 0
    assert b["first_seen"]["revocation"] == 1
    assert b["first_seen"]["citation"] == 2
    # And the claimed timestamps confirm the intended inconsistency
    revocation_claim = next(
        p["claimed"] for p in b["proofs"]
        if p["kind"] == "contract_revocation")
    citation_claim = next(
        p["claimed"] for p in b["proofs"]
        if p["kind"] == "citation_act")
    assert citation_claim < revocation_claim
    assert (tmp_path / "lcs_demo.json").exists()


if __name__ == "__main__":
    test_record_validates_fields()
    test_record_signature_verifies()
    test_record_wrong_key()
    test_record_tampered_payload()
    test_record_json_roundtrip()
    test_log_append_assigns_indices()
    test_log_append_chains_previous_hash()
    test_log_append_rejects_bad_hash()
    test_log_get_commit()
    test_log_get_commits_by_kind()
    test_log_get_commit_chain()
    test_log_first_commit_index()
    test_level_sizes()
    test_merkle_root_empty()
    test_merkle_root_single()
    test_merkle_root_two()
    test_merkle_root_three()
    test_merkle_root_deterministic()
    test_inclusion_proof_single()
    test_inclusion_proof_two()
    test_inclusion_proof_three_promoted()
    test_inclusion_proof_range()
    test_verify_inclusion_happy()
    test_verify_inclusion_three()
    test_verify_inclusion_five()
    test_verify_inclusion_wrong_leaf()
    test_verify_inclusion_wrong_root()
    test_verify_inclusion_tampered_proof()
    test_verify_inclusion_extra_hashes()
    test_verify_inclusion_empty_proof()
    test_chain_verify_happy()
    test_chain_verify_tampered_index()
    test_chain_verify_broken_link()
    test_chain_verify_tampered_sig()
    test_chain_verify_empty()
    test_tree_head_sign_verify()
    test_tree_head_wrong_key()
    test_tree_head_json_roundtrip()
    test_tree_head_empty_log()
    test_full_flow()
    test_artifact_hash_has_content_hash()
    test_artifact_hash_has_canonical_payload()
    test_artifact_hash_unknown_type()
    test_verifiers_never_raise()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
