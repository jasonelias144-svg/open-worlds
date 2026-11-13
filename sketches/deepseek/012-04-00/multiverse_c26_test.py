# multiverse_c26_test.py
import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c13 import HAS_CRYPTO, KeyPair
from multiverse_c15 import PassportEntry
from multiverse_c21 import ProvenanceReport, EntryProvenance
from multiverse_c24 import sign_report, verify_signed_report
from multiverse_c25 import ChainBuilder, verify_chain
from multiverse_c26 import (
    Revocation, RevocationSet,
    revoke, verify_revocations, verify_chain_with_revocations,
    CombinedVerdict, RevokedChain, demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _build_chain(n_witnesses=2):
    """Return (chain, report, alice_kp, alice, keys, witnesses)."""
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
    signed_report = sign_report(rep, alice_kp, alice)

    builder = ChainBuilder(signed_report)
    builder.attest(alice_kp, alice)
    keys = {alice.token: alice_kp.public_key_hex()}
    witnesses = []
    for i in range(n_witnesses):
        w_kp = KeyPair.generate()
        w = create_identity(f"Witness{i}")
        builder.attest(w_kp, w)
        keys[w.token] = w_kp.public_key_hex()
        witnesses.append((w, w_kp))
    return (builder.build(), signed_report, alice_kp, alice,
            keys, witnesses)


def _empty_revocation_set() -> RevocationSet:
    return RevocationSet()


# =====================================================================
# Revocation construction
# =====================================================================

def test_revocation_requires_valid_link_hash():
    print("=== Revocation validates link_hash ===")
    with pytest.raises(ValueError):
        Revocation(link_hash="", revoker_id="x", revoker_name="X",
                   timestamp="t", reason="", signature="s")
    with pytest.raises(ValueError):
        Revocation(link_hash="abc", revoker_id="x", revoker_name="X",
                   timestamp="t", reason="", signature="s")


def test_revoke_rejects_non_link():
    print("=== revoke() rejects non-ChainLink ===")
    kp = KeyPair.generate()
    signer = create_identity("Alice")
    with pytest.raises(TypeError):
        revoke("not-a-link", kp, signer)


# =====================================================================
# Self-revocation (the common case)
# =====================================================================

def test_self_revocation_verifies():
    print("=== Self-revocation verifies ===")
    chain, _, _, _, keys, witnesses = _build_chain(2)
    bob, bob_kp = witnesses[0]
    bob_link = chain.links[1]
    rev = revoke(bob_link, bob_kp, bob, reason="retracted")
    rev_set = RevocationSet()
    rev_set.add(rev)

    verdict = verify_revocations(
        chain, rev_set, key_resolver=lambda sid: keys.get(sid))
    print(verdict.format())
    assert verdict.valid
    assert len(verdict.revoked_links) == 1
    assert 1 in verdict.revoked_links
    assert verdict.revoked_links[1][0].revoker_id == bob.token


def test_self_revocation_changes_effective_signers():
    print("=== Self-revocation removes signer from effective list ===")
    chain, signed_report, alice_kp, _, keys, witnesses = _build_chain(2)
    bob, bob_kp = witnesses[0]
    rev = revoke(chain.links[1], bob_kp, bob, reason="")
    rev_set = RevocationSet(); rev_set.add(rev)

    combined = verify_chain_with_revocations(
        chain, rev_set, lambda sid: keys.get(sid),
        report_verifier=lambda r: verify_signed_report(
            r, alice_kp.public_key_hex()))
    print(combined.format())
    assert combined.valid
    assert combined.chain_verdict.verified_signers == [
        "Alice", "Witness0", "Witness1"]
    assert combined.effective_signers == ["Alice", "Witness1"]
    assert combined.revoked_signers == ["Witness0"]


# =====================================================================
# Cross-signer revocation
# =====================================================================

def test_cross_signer_revocation_verifies():
    print("=== Cross-signer revocation verifies ===")
    chain, _, _, _, keys, witnesses = _build_chain(2)
    bob, _ = witnesses[0]
    carol, carol_kp = witnesses[1]
    # Carol revokes Bob's link
    rev = revoke(chain.links[1], carol_kp, carol,
                 reason="I cannot vouch for Bob.")
    rev_set = RevocationSet(); rev_set.add(rev)
    verdict = verify_revocations(
        chain, rev_set, key_resolver=lambda sid: keys.get(sid))
    assert verdict.valid
    assert verdict.revoked_links[1][0].revoker_id == carol.token


# =====================================================================
# Rejection cases
# =====================================================================

def test_forged_revocation_rejected():
    print("=== Forged revocation → rejected ===")
    chain, _, _, _, keys, witnesses = _build_chain(2)
    bob, bob_kp = witnesses[0]
    real_rev = revoke(chain.links[1], bob_kp, bob, reason="")
    # Attacker forges one with attacker's key
    attacker = KeyPair.generate()
    from multiverse_c13 import canonical_bytes
    payload = canonical_bytes({
        "kind": "revocation",
        "link_hash": real_rev.link_hash,
        "revoker_id": bob.token,
        "revoker_name": bob.name,
        "timestamp": real_rev.timestamp,
        "reason": real_rev.reason,
    })
    forged = Revocation(
        link_hash=real_rev.link_hash,
        revoker_id=bob.token, revoker_name=bob.name,
        timestamp=real_rev.timestamp, reason=real_rev.reason,
        signature=attacker.sign(payload).hex(),
    )
    rev_set = RevocationSet(); rev_set.add(forged)
    verdict = verify_revocations(
        chain, rev_set, key_resolver=lambda sid: keys.get(sid))
    assert not verdict.valid
    assert len(verdict.rejected) == 1
    assert "INVALID" in verdict.rejected[0][1]
    assert len(verdict.revoked_links) == 0


def test_target_not_found_rejected():
    print("=== Revocation targeting a non-link hash → rejected ===")
    chain, _, _, _, keys, witnesses = _build_chain(2)
    bob, bob_kp = witnesses[0]
    # Revoke a hash that isn't any link's hash
    from multiverse_c13 import canonical_bytes
    bogus_hash = "00" * 32
    payload = canonical_bytes({
        "kind": "revocation", "link_hash": bogus_hash,
        "revoker_id": bob.token, "revoker_name": bob.name,
        "timestamp": "t", "reason": "",
    })
    rev = Revocation(
        link_hash=bogus_hash, revoker_id=bob.token,
        revoker_name=bob.name, timestamp="t", reason="",
        signature=bob_kp.sign(payload).hex(),
    )
    rev_set = RevocationSet(); rev_set.add(rev)
    verdict = verify_revocations(
        chain, rev_set, key_resolver=lambda sid: keys.get(sid))
    assert not verdict.valid
    assert len(verdict.rejected) == 1
    assert "target" in verdict.rejected[0][1].lower()


def test_unknown_revoker_rejected():
    print("=== Revocation from a signer with no known key → rejected ===")
    chain, _, _, _, keys, witnesses = _build_chain(2)
    bob, bob_kp = witnesses[0]
    rev = revoke(chain.links[1], bob_kp, bob, reason="")
    rev_set = RevocationSet(); rev_set.add(rev)
    # Remove Bob's key
    del keys[bob.token]
    verdict = verify_revocations(
        chain, rev_set, key_resolver=lambda sid: keys.get(sid))
    assert not verdict.valid
    assert "no public key" in verdict.rejected[0][1].lower()


# =====================================================================
# No cascade — the design commitment
# =====================================================================

def test_revoking_middle_link_does_not_cascade():
    """Revoking Bob's link does NOT revoke Carol's link even
    though Carol witnessed Bob. Carol's attestation ('I saw Bob's
    link at time T') remains true. Bob's link is now annotated as
    'retracted by Bob'. Both records stand."""
    print("=== No cascade: middle revocation leaves Carol's link intact ===")
    chain, _, _, _, keys, witnesses = _build_chain(2)
    bob, bob_kp = witnesses[0]
    carol, _ = witnesses[1]
    rev = revoke(chain.links[1], bob_kp, bob, reason="retracted")
    rev_set = RevocationSet(); rev_set.add(rev)

    verdict = verify_revocations(
        chain, rev_set, key_resolver=lambda sid: keys.get(sid))
    # Only Bob's link (index 1) is revoked
    assert list(verdict.revoked_links.keys()) == [1]
    # Carol's link (index 2) is NOT revoked
    assert 2 not in verdict.revoked_links
    # The chain verdict is still fully valid
    from multiverse_c25 import verify_chain
    cv = verify_chain(chain, lambda sid: keys.get(sid))
    assert cv.valid
    assert cv.verified_signers == ["Alice", "Witness0", "Witness1"]


# =====================================================================
# No revocation-of-revocation
# =====================================================================

def test_revoking_a_revocation_is_rejected_as_target_not_found():
    """A revocation names a LINK hash. If someone passes a
    revocation's payload hash to revoke(), it won't match any link
    and will be rejected."""
    print("=== Revocation of revocation → target not found ===")
    chain, _, _, _, keys, witnesses = _build_chain(2)
    bob, bob_kp = witnesses[0]
    rev = revoke(chain.links[1], bob_kp, bob, reason="")
    # Try to revoke the revocation itself:
    # fake a ChainLink whose hash equals the revocation's payload hash
    from multiverse_c13 import canonical_bytes
    import hashlib
    rev_hash = hashlib.sha256(rev.canonical_payload()).hexdigest()
    # Build a revocation targeting that hash
    carol, carol_kp = witnesses[1]
    payload = canonical_bytes({
        "kind": "revocation", "link_hash": rev_hash,
        "revoker_id": carol.token, "revoker_name": carol.name,
        "timestamp": "t", "reason": "retract the retraction",
    })
    rev2 = Revocation(
        link_hash=rev_hash, revoker_id=carol.token,
        revoker_name=carol.name, timestamp="t",
        reason="retract the retraction",
        signature=carol_kp.sign(payload).hex(),
    )
    rev_set = RevocationSet(); rev_set.add(rev); rev_set.add(rev2)
    verdict = verify_revocations(
        chain, rev_set, key_resolver=lambda sid: keys.get(sid))
    assert not verdict.valid
    assert any("target" in r[1].lower() for r in verdict.rejected)


# =====================================================================
# JSON roundtrip
# =====================================================================

def test_revoked_chain_json_roundtrip():
    print("=== RevokedChain JSON roundtrip preserves verification ===")
    chain, signed_report, alice_kp, _, keys, witnesses = _build_chain(2)
    bob, bob_kp = witnesses[0]
    rev = revoke(chain.links[1], bob_kp, bob, reason="retracted")
    rev_set = RevocationSet(); rev_set.add(rev)
    rc = RevokedChain(chain=chain, revocations=rev_set)

    wire = json.dumps(rc.to_dict())
    revived = RevokedChain.from_dict(json.loads(wire))

    combined = revived.verify(
        key_resolver=lambda sid: keys.get(sid),
        report_verifier=lambda r: verify_signed_report(
            r, alice_kp.public_key_hex()))
    assert combined.valid
    assert combined.effective_signers == ["Alice", "Witness1"]
    assert combined.revoked_signers == ["Witness0"]


def test_revocation_set_roundtrip():
    print("=== RevocationSet JSON roundtrip ===")
    chain, _, _, _, _, witnesses = _build_chain(1)
    bob, bob_kp = witnesses[0]
    rev = revoke(chain.links[1], bob_kp, bob, reason="r")
    rev_set = RevocationSet(); rev_set.add(rev)
    wire = json.dumps(rev_set.to_dict())
    revived = RevocationSet.from_dict(json.loads(wire))
    assert len(revived) == 1
    assert revived.revocations[0].link_hash == rev.link_hash
    assert revived.revocations[0].signature == rev.signature


# =====================================================================
# Never raises
# =====================================================================

def test_verify_revocations_never_raises():
    print("=== verify_revocations never raises ===")
    chain, _, _, _, _, _ = _build_chain(1)
    # Bad types
    assert not verify_revocations(
        None, RevocationSet(), lambda s: None).valid
    assert not verify_revocations(
        chain, None, lambda s: None).valid
    assert not verify_revocations(
        "not-a-chain", RevocationSet(), lambda s: None).valid
    # Resolver raising
    rev = revoke(chain.links[0], KeyPair.generate(),
                 create_identity("X"), reason="")
    rev_set = RevocationSet(); rev_set.add(rev)
    def raising(sid):
        raise RuntimeError("boom")
    verdict = verify_revocations(chain, rev_set, raising)
    assert not verdict.valid
    assert any("boom" in r[1] for r in verdict.rejected)


def test_combined_verdict_never_raises():
    print("=== verify_chain_with_revocations never raises ===")
    chain, _, _, _, _, _ = _build_chain(1)
    # Both chain and revocations broken
    combined = verify_chain_with_revocations(
        None, None, lambda s: None)
    assert not combined.valid


# =====================================================================
# Multiple revocations
# =====================================================================

def test_multiple_revocations_of_same_link():
    """Two valid revocations targeting the same link: both count;
    the link stays revoked; both appear in revoked_links[i]."""
    print("=== Multiple valid revocations of the same link ===")
    chain, _, _, _, keys, witnesses = _build_chain(2)
    bob, bob_kp = witnesses[0]
    carol, carol_kp = witnesses[1]
    rev1 = revoke(chain.links[1], bob_kp, bob, reason="self")
    rev2 = revoke(chain.links[1], carol_kp, carol, reason="witness")
    rev_set = RevocationSet(); rev_set.add(rev1); rev_set.add(rev2)
    verdict = verify_revocations(
        chain, rev_set, key_resolver=lambda sid: keys.get(sid))
    assert verdict.valid
    assert len(verdict.revoked_links[1]) == 2


def test_revoke_two_different_links():
    print("=== Revoking two different links ===")
    chain, _, _, _, keys, witnesses = _build_chain(2)
    bob, bob_kp = witnesses[0]
    carol, carol_kp = witnesses[1]
    rev_set = RevocationSet()
    rev_set.add(revoke(chain.links[1], bob_kp, bob, reason=""))
    rev_set.add(revoke(chain.links[2], carol_kp, carol, reason=""))
    verdict = verify_revocations(
        chain, rev_set, key_resolver=lambda sid: keys.get(sid))
    assert verdict.valid
    assert sorted(verdict.revoked_links.keys()) == [1, 2]


# =====================================================================
# Honest limit, as a test
# =====================================================================

def test_no_cascade_means_effective_signers_is_per_link():
    """The 'effective_signers' list is computed per-link. Revoking
    Bob's link does not remove Carol's link from the effective list,
    even though Carol witnessed Bob. This is the documented choice."""
    print("=== Effective signers: only directly-revoked links removed ===")
    chain, _, _, _, keys, witnesses = _build_chain(2)
    bob, bob_kp = witnesses[0]
    rev = revoke(chain.links[1], bob_kp, bob, reason="")
    rev_set = RevocationSet(); rev_set.add(rev)
    combined = verify_chain_with_revocations(
        chain, rev_set, lambda sid: keys.get(sid))
    # Chain still valid, verified_signers is all three
    assert combined.chain_verdict.valid
    assert combined.chain_verdict.verified_signers == [
        "Alice", "Witness0", "Witness1"]
    # Only Witness0's link is revoked
    assert combined.effective_signers == ["Alice", "Witness1"]
    assert combined.revoked_signers == ["Witness0"]


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: Bob retracts his witness ===")
    rc = demo(artifact_dir=str(tmp_path))
    assert len(rc.chain.links) == 3
    assert len(rc.revocations) == 1
    assert (tmp_path / "revoked_chain.json").exists()
    assert (tmp_path / "revoked_chain_verdict.json").exists()
    data = json.loads(
        (tmp_path / "revoked_chain_verdict.json").read_text())
    assert data["valid"] is True
    assert data["effective_signers"] == ["Alice", "Carol"]
    assert data["revoked_signers"] == ["Bob"]


if __name__ == "__main__":
    test_revocation_requires_valid_link_hash()
    test_revoke_rejects_non_link()
    test_self_revocation_verifies()
    test_self_revocation_changes_effective_signers()
    test_cross_signer_revocation_verifies()
    test_forged_revocation_rejected()
    test_target_not_found_rejected()
    test_unknown_revoker_rejected()
    test_revoking_middle_link_does_not_cascade()
    test_revoking_a_revocation_is_rejected_as_target_not_found()
    test_revoked_chain_json_roundtrip()
    test_revocation_set_roundtrip()
    test_verify_revocations_never_raises()
    test_combined_verdict_never_raises()
    test_multiple_revocations_of_same_link()
    test_revoke_two_different_links()
    test_no_cascade_means_effective_signers_is_per_link()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
