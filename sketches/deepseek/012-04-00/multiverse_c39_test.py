# multiverse_c39_test.py
import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c36 import create_person, bind_token
from multiverse_c38 import sign_person_manifest
from multiverse_c39 import (
    ForkEvent, MergeEvent, ForkVerdict, MergeVerdict,
    create_fork, create_merge,
    verify_fork, verify_merge,
    LineageWalk, build_lineage,
    _hash_payload,
    demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _build_person(name, tokens=()):
    p, kp = create_person(name)
    for tn in tokens:
        tok = create_identity(tn)
        p, _ = bind_token(
            p, kp, tok.token, tn, KeyPair.generate())
    return p, kp, sign_person_manifest(p, kp)


def _simple_forks():
    """Aria forks into Aria-A and Aria-B."""
    aria, aria_kp, aria_m = _build_person(
        "Aria", ["Aria@poetry"])
    a, a_kp, a_m = _build_person("Aria-A", ["Aria-A@poetry"])
    b, b_kp, b_m = _build_person("Aria-B", ["Aria-B@chem"])
    fork = create_fork(aria, aria_kp, [a_m, b_m])
    return {
        "aria": aria, "aria_kp": aria_kp, "aria_m": aria_m,
        "a": a, "a_kp": a_kp, "a_m": a_m,
        "b": b, "b_kp": b_kp, "b_m": b_m,
        "fork": fork,
    }


def _simple_merge(a, a_kp, a_m, b, b_kp, b_m, merged_name="Aria-2"):
    merged, merged_kp, merged_m = _build_person(
        merged_name, ["merged@x"])
    merge = create_merge(a, a_kp, b, b_kp, merged_m)
    return merged, merged_kp, merged_m, merge


# =====================================================================
# Fork construction
# =====================================================================

def test_fork_construction():
    print("=== ForkEvent construction validates shape ===")
    d = _simple_forks()
    f = d["fork"]
    assert len(f.children) == 2
    tokens = [t for t, _ in f.children]
    assert tokens == sorted(tokens)
    assert f.parent_token == d["aria"].person.token


def test_fork_requires_two_children():
    print("=== create_fork requires >= 2 children ===")
    aria, aria_kp, aria_m = _build_person("Aria")
    child, _, child_m = _build_person("Child")
    with pytest.raises(ValueError):
        create_fork(aria, aria_kp, [child_m])


def test_fork_rejects_wrong_keypair():
    print("=== create_fork: keypair != parent key ===")
    aria, _, aria_m = _build_person("Aria")
    a, _, a_m = _build_person("A")
    b, _, b_m = _build_person("B")
    wrong_kp = KeyPair.generate()
    with pytest.raises(ValueError):
        create_fork(aria, wrong_kp, [a_m, b_m])


# =====================================================================
# verify_fork
# =====================================================================

def test_verify_fork_happy():
    print("=== verify_fork: happy path ===")
    d = _simple_forks()
    v = verify_fork(
        d["fork"], [d["a_m"], d["b_m"]],
        trusted_parent_key=d["aria"].person_public_key)
    assert v.valid
    assert v.parent_signature_valid
    assert all(ok for _, ok, _ in v.child_verdicts)


def test_verify_fork_tampered_child_manifest():
    print("=== verify_fork: tampered child manifest → fail ===")
    d = _simple_forks()
    # Tamper the child's name (changes hash)
    from multiverse_c38 import PersonManifest
    tampered = PersonManifest(
        person_token=d["a_m"].person_token,
        person_name="Tampered",
        person_public_key=d["a_m"].person_public_key,
        bindings=d["a_m"].bindings,
        timestamp=d["a_m"].timestamp,
        signature=d["a_m"].signature,
    )
    v = verify_fork(
        d["fork"], [tampered, d["b_m"]],
        trusted_parent_key=d["aria"].person_public_key)
    assert not v.valid


def test_verify_fork_missing_child():
    print("=== verify_fork: missing child manifest → fail ===")
    d = _simple_forks()
    v = verify_fork(
        d["fork"], [d["a_m"]],  # B missing
        trusted_parent_key=d["aria"].person_public_key)
    assert not v.valid
    assert any("not provided" in r for _, _, r in v.child_verdicts)


def test_verify_fork_wrong_parent_key():
    print("=== verify_fork: wrong trusted parent key → fail ===")
    d = _simple_forks()
    wrong = KeyPair.generate().public_key_hex()
    v = verify_fork(
        d["fork"], [d["a_m"], d["b_m"]],
        trusted_parent_key=wrong)
    assert not v.valid
    assert v.parent_signature_valid  # self-consistent sig is fine
    assert "trusted" in v.reason


def test_verify_fork_forged_signature():
    print("=== verify_fork: forged signature → fail ===")
    d = _simple_forks()
    f = d["fork"]
    tampered = ForkEvent(
        parent_token=f.parent_token,
        parent_name=f.parent_name,
        parent_public_key=f.parent_public_key,
        children=f.children,
        timestamp=f.timestamp,
        signature=KeyPair.generate().sign(
            f.canonical_payload()).hex(),
    )
    v = verify_fork(
        tampered, [d["a_m"], d["b_m"]],
        trusted_parent_key=d["aria"].person_public_key)
    assert not v.valid
    assert not v.parent_signature_valid


# =====================================================================
# Merge construction
# =====================================================================

def test_merge_construction():
    print("=== MergeEvent construction validates shape ===")
    d = _simple_forks()
    merged, _, merged_m, merge = _simple_merge(
        d["a"], d["a_kp"], d["a_m"],
        d["b"], d["b_kp"], d["b_m"])
    assert merge.parent_a_token != merge.parent_b_token
    assert merge.signature_a and merge.signature_b
    assert len(merge.merged_manifest_hash) == 64


def test_merge_rejects_same_parent():
    print("=== create_merge: distinct parents required ===")
    d = _simple_forks()
    merged, _, merged_m = _build_person("X")
    with pytest.raises(ValueError):
        create_merge(
            d["a"], d["a_kp"],
            d["a"], d["a_kp"], merged_m)


def test_merge_rejects_wrong_keypair():
    print("=== create_merge: keypair != parent key ===")
    d = _simple_forks()
    merged, _, merged_m = _build_person("X")
    wrong = KeyPair.generate()
    with pytest.raises(ValueError):
        create_merge(
            d["a"], wrong,
            d["b"], d["b_kp"], merged_m)


# =====================================================================
# verify_merge
# =====================================================================

def test_verify_merge_happy():
    print("=== verify_merge: happy path ===")
    d = _simple_forks()
    merged, _, merged_m, merge = _simple_merge(
        d["a"], d["a_kp"], d["a_m"],
        d["b"], d["b_kp"], d["b_m"])
    v = verify_merge(
        merge, merged_m,
        trusted_parent_a_key=d["a"].person_public_key,
        trusted_parent_b_key=d["b"].person_public_key)
    assert v.valid
    assert v.parent_a_signature_valid
    assert v.parent_b_signature_valid
    assert v.merged_manifest_matches


def test_verify_merge_one_forged_signature():
    print("=== verify_merge: forged parent_a sig → fail ===")
    d = _simple_forks()
    merged, _, merged_m, merge = _simple_merge(
        d["a"], d["a_kp"], d["a_m"],
        d["b"], d["b_kp"], d["b_m"])
    forged = MergeEvent(
        parent_a_token=merge.parent_a_token,
        parent_a_name=merge.parent_a_name,
        parent_a_public_key=merge.parent_a_public_key,
        parent_b_token=merge.parent_b_token,
        parent_b_name=merge.parent_b_name,
        parent_b_public_key=merge.parent_b_public_key,
        merged_token=merge.merged_token,
        merged_name=merge.merged_name,
        merged_public_key=merge.merged_public_key,
        merged_manifest_hash=merge.merged_manifest_hash,
        timestamp=merge.timestamp,
        signature_a=KeyPair.generate().sign(
            merge.canonical_payload()).hex(),
        signature_b=merge.signature_b,
    )
    v = verify_merge(
        forged, merged_m,
        trusted_parent_a_key=d["a"].person_public_key,
        trusted_parent_b_key=d["b"].person_public_key)
    assert not v.valid
    assert not v.parent_a_signature_valid
    assert v.parent_b_signature_valid


def test_verify_merge_tampered_merged_manifest():
    print("=== verify_merge: tampered merged manifest → fail ===")
    d = _simple_forks()
    merged, _, merged_m, merge = _simple_merge(
        d["a"], d["a_kp"], d["a_m"],
        d["b"], d["b_kp"], d["b_m"])
    from multiverse_c38 import PersonManifest
    tampered_m = PersonManifest(
        person_token=merged_m.person_token,
        person_name="Tampered",
        person_public_key=merged_m.person_public_key,
        bindings=merged_m.bindings,
        timestamp=merged_m.timestamp,
        signature=merged_m.signature,
    )
    v = verify_merge(
        merge, tampered_m,
        trusted_parent_a_key=d["a"].person_public_key,
        trusted_parent_b_key=d["b"].person_public_key)
    assert not v.valid
    assert not v.merged_manifest_matches


def test_verify_merge_wrong_trusted_key():
    print("=== verify_merge: wrong trusted parent key → fail ===")
    d = _simple_forks()
    merged, _, merged_m, merge = _simple_merge(
        d["a"], d["a_kp"], d["a_m"],
        d["b"], d["b_kp"], d["b_m"])
    wrong = KeyPair.generate().public_key_hex()
    v = verify_merge(
        merge, merged_m,
        trusted_parent_a_key=wrong,
        trusted_parent_b_key=d["b"].person_public_key)
    assert not v.valid
    assert "trusted" in v.reason


# =====================================================================
# build_lineage
# =====================================================================

def test_lineage_walk_single_fork():
    print("=== build_lineage: single fork ===")
    d = _simple_forks()
    manifests = {
        d["aria"].person.token: d["aria_m"],
        d["a"].person.token: d["a_m"],
        d["b"].person.token: d["b_m"],
    }
    # Walk from a_m: should find the fork, and Aria as ancestor
    walk = build_lineage(d["a_m"], manifests, [d["fork"]])
    assert walk.valid
    assert d["aria"].person.token in walk.ancestors
    assert len(walk.events) == 1


def test_lineage_walk_fork_then_merge():
    print("=== build_lineage: fork then merge ===")
    d = _simple_forks()
    merged, _, merged_m, merge = _simple_merge(
        d["a"], d["a_kp"], d["a_m"],
        d["b"], d["b_kp"], d["b_m"])
    manifests = {
        d["aria"].person.token: d["aria_m"],
        d["a"].person.token: d["a_m"],
        d["b"].person.token: d["b_m"],
        merged.person.token: merged_m,
    }
    walk = build_lineage(
        merged_m, manifests, [d["fork"], merge])
    assert walk.valid
    assert d["aria"].person.token in walk.ancestors
    assert d["a"].person.token in walk.ancestors
    assert d["b"].person.token in walk.ancestors
    assert d["fork"] in walk.events
    assert merge in walk.events


def test_lineage_walk_root_only():
    print("=== build_lineage: root only (no events) ===")
    aria, _, aria_m = _build_person("Aria")
    walk = build_lineage(
        aria_m, {aria.person.token: aria_m}, [])
    assert walk.valid
    assert walk.ancestors == []
    assert walk.events == []


def test_lineage_walk_missing_manifest():
    print("=== build_lineage: missing ancestor manifest → fail ===")
    d = _simple_forks()
    # Only provide Aria's manifest, not the children's
    manifests = {
        d["aria"].person.token: d["aria_m"],
    }
    walk = build_lineage(d["a_m"], manifests, [d["fork"]])
    assert not walk.valid
    assert "missing" in walk.reason.lower()


def test_lineage_walk_tampered_event_sig():
    print("=== build_lineage: tampered event signature → fail ===")
    d = _simple_forks()
    f = d["fork"]
    tampered = ForkEvent(
        parent_token=f.parent_token,
        parent_name=f.parent_name,
        parent_public_key=f.parent_public_key,
        children=f.children,
        timestamp=f.timestamp,
        signature=KeyPair.generate().sign(
            f.canonical_payload()).hex(),
    )
    manifests = {
        d["aria"].person.token: d["aria_m"],
        d["a"].person.token: d["a_m"],
        d["b"].person.token: d["b_m"],
    }
    walk = build_lineage(d["a_m"], manifests, [tampered])
    assert not walk.valid
    assert "signature" in walk.reason.lower()


# =====================================================================
# Never raises
# =====================================================================

def test_verifiers_never_raise():
    print("=== Verifiers never raise on bad input ===")
    assert not verify_fork(None, []).valid
    assert not verify_fork("not a fork", []).valid
    assert not verify_merge(None, None).valid
    assert not verify_merge("not a merge", None).valid
    walk = build_lineage(None, {}, [])
    assert not walk.valid


# =====================================================================
# JSON roundtrips
# =====================================================================

def test_fork_json_roundtrip():
    print("=== ForkEvent JSON roundtrip ===")
    d = _simple_forks()
    wire = json.dumps(d["fork"].to_dict())
    revived = ForkEvent.from_dict(json.loads(wire))
    assert revived.canonical_payload() == d["fork"].canonical_payload()
    v = verify_fork(
        revived, [d["a_m"], d["b_m"]],
        trusted_parent_key=d["aria"].person_public_key)
    assert v.valid


def test_merge_json_roundtrip():
    print("=== MergeEvent JSON roundtrip ===")
    d = _simple_forks()
    merged, _, merged_m, merge = _simple_merge(
        d["a"], d["a_kp"], d["a_m"],
        d["b"], d["b_kp"], d["b_m"])
    wire = json.dumps(merge.to_dict())
    revived = MergeEvent.from_dict(json.loads(wire))
    assert revived.canonical_payload() == merge.canonical_payload()
    v = verify_merge(revived, merged_m)
    assert v.valid


# =====================================================================
# Honest limit as a test
# =====================================================================

def test_fork_does_not_transfer_bindings():
    """The named limit: a fork declares lineage, not binding
    transfer. Aria's bindings stay in Aria's manifest; the
    children's manifests declare their own bindings. The fork
    event does not mention Aria's tokens in the children's sets."""
    print("=== Honest limit: fork declares lineage, not transfer ===")
    aria, aria_kp, aria_m = _build_person(
        "Aria", ["Aria@poetry"])
    child, _, child_m = _build_person("Aria-A", ["Aria-A@new"])
    child2, _, child2_m = _build_person("Aria-B", ["Aria-B@new"])
    fork = create_fork(aria, aria_kp, [child_m, child2_m])
    # Aria still has her binding
    assert len(aria_m.bindings) == 1
    # Children have their own tokens, not Aria's
    child_tokens = [t for t, _ in child_m.bindings]
    assert aria_m.bindings[0][0] not in child_tokens
    # The fork doesn't dictate what children hold
    for ct, _ch in fork.children:
        # ct is the child's person token, not a binding token
        assert ct != aria.person.token
    print("  Aria's tokens stay Aria's; children have their own")
    print("  (transferring would require a separate rebind op)")


def test_fork_can_be_forged_against_known_key():
    """A fork signed by an attacker's key claiming a known parent
    token: verify_fork catches it when trusted_parent_key is
    provided."""
    print("=== Honest limit: forged parent key caught by trust anchor ===")
    d = _simple_forks()
    aria_pk = d["aria"].person_public_key
    attacker = KeyPair.generate()
    a_m, b_m = d["a_m"], d["b_m"]
    fake_children = tuple(sorted([
        (a_m.person_token,
         _hash_payload(a_m.canonical_payload())),
        (b_m.person_token,
         _hash_payload(b_m.canonical_payload())),
    ]))
    payload = canonical_bytes({
        "kind": "fork_event",
        "parent_token": d["aria"].person.token,
        "parent_name": "Aria (impersonated)",
        "parent_public_key": attacker.public_key_hex(),
        "children": [list(c) for c in fake_children],
        "timestamp": "2024-01-01T00:00:00+00:00",
    })
    fake = ForkEvent(
        parent_token=d["aria"].person.token,
        parent_name="Aria (impersonated)",
        parent_public_key=attacker.public_key_hex(),
        children=fake_children,
        timestamp="2024-01-01T00:00:00+00:00",
        signature=attacker.sign(payload).hex(),
    )
    # Without trust anchor: passes (self-consistent)
    v_no_anchor = verify_fork(fake, [a_m, b_m])
    assert v_no_anchor.valid
    # With Aria's known key: fails
    v_with_anchor = verify_fork(
        fake, [a_m, b_m], trusted_parent_key=aria_pk)
    assert not v_with_anchor.valid
    print("  without trust anchor: passes (self-consistent)")
    print("  with Aria's known key: fails")


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: fork + merge + lineage + forged fork ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["fork_valid"]
    assert audit["merge_valid"]
    assert audit["lineage_valid"]
    assert audit["lineage_ancestors"] == 3
    assert audit["lineage_events"] == 2
    assert audit["fake_fork_valid_against_real_key"] is False
    assert (tmp_path / "lineage_demo.json").exists()


if __name__ == "__main__":
    test_fork_construction()
    test_fork_requires_two_children()
    test_fork_rejects_wrong_keypair()
    test_verify_fork_happy()
    test_verify_fork_tampered_child_manifest()
    test_verify_fork_missing_child()
    test_verify_fork_wrong_parent_key()
    test_verify_fork_forged_signature()
    test_merge_construction()
    test_merge_rejects_same_parent()
    test_merge_rejects_wrong_keypair()
    test_verify_merge_happy()
    test_verify_merge_one_forged_signature()
    test_verify_merge_tampered_merged_manifest()
    test_verify_merge_wrong_trusted_key()
    test_lineage_walk_single_fork()
    test_lineage_walk_fork_then_merge()
    test_lineage_walk_root_only()
    test_lineage_walk_missing_manifest()
    test_lineage_walk_tampered_event_sig()
    test_verifiers_never_raise()
    test_fork_json_roundtrip()
    test_merge_json_roundtrip()
    test_fork_does_not_transfer_bindings()
    test_fork_can_be_forged_against_known_key()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
