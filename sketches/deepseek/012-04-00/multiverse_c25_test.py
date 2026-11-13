# multiverse_c25_test.py
import json
import pytest

from multiverse_c1 import create_identity
from multiverse_c13 import HAS_CRYPTO, KeyPair
from multiverse_c15 import PassportEntry
from multiverse_c21 import ProvenanceReport, EntryProvenance
from multiverse_c24 import (
    SignedProvenanceReport, sign_report, verify_signed_report,
)
from multiverse_c25 import (
    ChainLink, AttestedChain, ChainVerdict, ChainBuilder,
    verify_chain, _hash_payload,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _stub_report(name="Auditor") -> SignedProvenanceReport:
    """A minimal signed report. Real signature, stub content."""
    from multiverse_c1 import create_identity as mk
    kp = KeyPair.generate()
    auditor = mk(name)
    rep = ProvenanceReport(
        passport_token="alice-token",
        passport_name="Alice",
        registry_url="http://r",
    )
    entry = PassportEntry(
        entity_id="world:a",
        timestamp="2024-01-01T00:00:00+00:00",
        subject_token="alice-token",
        signature="cc" * 64,
    )
    ep = EntryProvenance(entry=entry)
    ep.verdict = "verified"
    ep.reason = "stub"
    rep.entries.append(ep)
    return sign_report(rep, kp, auditor), kp, auditor


def _build_chain(n_witnesses=2):
    """Build a chain with 1 anchor + n_witnesses, return everything."""
    signed_report, alice_kp, alice = _stub_report("Alice")
    keys = {alice.token: alice_kp.public_key_hex()}

    builder = ChainBuilder(signed_report)
    builder.attest(alice_kp, alice)  # link 0

    witnesses = []
    for i in range(n_witnesses):
        w_kp = KeyPair.generate()
        w = create_identity(f"Witness{i}")
        builder.attest(w_kp, w)
        keys[w.token] = w_kp.public_key_hex()
        witnesses.append((w, w_kp))

    return builder.build(), signed_report, alice_kp, alice, keys, witnesses


# =====================================================================
# ChainLink construction
# =====================================================================

def test_link_zero_requires_report_hash():
    print("=== Link 0 requires report_hash, forbids previous_link_hash ===")
    with pytest.raises(ValueError):
        ChainLink(link_index=0, signer_id="x", signer_name="X",
                  previous_link_hash=None, report_hash=None,
                  timestamp="t", signature="s")
    with pytest.raises(ValueError):
        ChainLink(link_index=0, signer_id="x", signer_name="X",
                  previous_link_hash="abc", report_hash="def",
                  timestamp="t", signature="s")


def test_link_nonzero_requires_previous_link_hash():
    print("=== Link i>0 requires previous_link_hash, forbids report_hash ===")
    with pytest.raises(ValueError):
        ChainLink(link_index=1, signer_id="x", signer_name="X",
                  previous_link_hash=None, report_hash=None,
                  timestamp="t", signature="s")
    with pytest.raises(ValueError):
        ChainLink(link_index=1, signer_id="x", signer_name="X",
                  previous_link_hash="abc", report_hash="def",
                  timestamp="t", signature="s")


# =====================================================================
# Happy path
# =====================================================================

def test_chain_of_three_verifies():
    print("=== Chain of 3 (anchor + 2 witnesses) verifies ===")
    chain, report, alice_kp, alice, keys, witnesses = _build_chain(2)
    verdict = verify_chain(
        chain,
        key_resolver=lambda sid: keys.get(sid),
        report_verifier=lambda r: verify_signed_report(
            r, alice_kp.public_key_hex()))
    print(verdict.format())
    assert verdict.valid
    assert verdict.verified_signers == ["Alice",
                                         "Witness0", "Witness1"]


def test_chain_of_one_verifies():
    print("=== Chain of 1 (anchor only) verifies ===")
    chain, report, alice_kp, alice, keys, _ = _build_chain(0)
    verdict = verify_chain(
        chain,
        key_resolver=lambda sid: keys.get(sid),
        report_verifier=lambda r: verify_signed_report(
            r, alice_kp.public_key_hex()))
    assert verdict.valid
    assert len(verdict.verified_signers) == 1


def test_chain_without_report_verifier():
    """report_verifier is optional."""
    print("=== verify_chain without report_verifier ===")
    chain, _, _, _, keys, _ = _build_chain(1)
    verdict = verify_chain(chain,
                            key_resolver=lambda sid: keys.get(sid))
    assert verdict.valid


# =====================================================================
# Tampering
# =====================================================================

def _retamper_sign(link: ChainLink, kp: KeyPair,
                    **overrides) -> ChainLink:
    """Rebuild a link with overrides, re-sign with a key."""
    from multiverse_c13 import canonical_bytes
    fields = dict(
        link_index=link.link_index,
        signer_id=link.signer_id,
        signer_name=link.signer_name,
        previous_link_hash=link.previous_link_hash,
        report_hash=link.report_hash,
        timestamp=link.timestamp,
    )
    fields.update(overrides)
    payload = canonical_bytes({
        "kind": "attestation_link",
        **fields,
    })
    return ChainLink(**fields,
                      signature=kp.sign(payload).hex())


def test_tampered_link_breaks_chain():
    print("=== Tampered link name breaks chain ===")
    chain, _, _, _, keys, _ = _build_chain(2)
    # Attacker tampers with link 1's signer_name but doesn't re-sign
    link1 = chain.links[1]
    tampered = ChainLink(
        link_index=link1.link_index,
        signer_id=link1.signer_id,
        signer_name="Impostor",
        previous_link_hash=link1.previous_link_hash,
        report_hash=link1.report_hash,
        timestamp=link1.timestamp,
        signature=link1.signature,  # original
    )
    chain.links[1] = tampered
    verdict = verify_chain(chain,
                            key_resolver=lambda sid: keys.get(sid))
    assert not verdict.valid
    assert verdict.link_index == 1
    assert "INVALID" in verdict.reason


def test_reordered_links_caught():
    print("=== Reordering links breaks the chain (position check) ===")
    chain, _, _, _, keys, _ = _build_chain(2)
    # Swap link 1 and link 2
    chain.links[1], chain.links[2] = chain.links[2], chain.links[1]
    verdict = verify_chain(chain,
                            key_resolver=lambda sid: keys.get(sid))
    assert not verdict.valid
    assert verdict.link_index == 1
    assert "position" in verdict.reason.lower()


def test_dropped_link_caught():
    print("=== Dropping a middle link is caught by hash binding ===")
    chain, _, _, _, keys, _ = _build_chain(3)
    # Remove link 1 (middle)
    del chain.links[1]
    verdict = verify_chain(chain,
                            key_resolver=lambda sid: keys.get(sid))
    assert not verdict.valid
    # The next link (now at position 1, was position 2) has
    # link_index=2, but expected 1 → position mismatch
    assert verdict.link_index == 1
    assert "position" in verdict.reason.lower()


def test_swapped_report_caught():
    print("=== Swapping the report is caught by report_hash ===")
    chain, _, _, _, keys, _ = _build_chain(2)
    # Replace report with a different one
    other_report, _, _ = _stub_report("Different")
    chain.report = other_report
    verdict = verify_chain(chain,
                            key_resolver=lambda sid: keys.get(sid))
    assert not verdict.valid
    assert verdict.link_index == 0
    assert "report_hash" in verdict.reason.lower()


def test_wrong_public_key_rejected():
    print("=== Wrong key at any link breaks verification ===")
    chain, _, _, _, keys, witnesses = _build_chain(2)
    # Corrupt one witness's key
    bad_key = KeyPair.generate().public_key_hex()
    keys[witnesses[0][0].token] = bad_key
    verdict = verify_chain(chain,
                            key_resolver=lambda sid: keys.get(sid))
    assert not verdict.valid
    assert verdict.link_index == 1


def test_missing_public_key_rejected():
    print("=== Missing key → INVALID ===")
    chain, _, _, _, keys, witnesses = _build_chain(2)
    del keys[witnesses[0][0].token]
    verdict = verify_chain(chain,
                            key_resolver=lambda sid: keys.get(sid))
    assert not verdict.valid
    assert verdict.link_index == 1


def test_report_verifier_rejects():
    print("=== report_verifier failure breaks the chain ===")
    chain, _, _, _, keys, _ = _build_chain(2)
    verdict = verify_chain(
        chain,
        key_resolver=lambda sid: keys.get(sid),
        report_verifier=lambda r: False,
    )
    assert not verdict.valid
    assert "report" in verdict.reason.lower()


def test_report_verifier_raises_is_caught():
    print("=== report_verifier raising is caught ===")
    chain, _, _, _, keys, _ = _build_chain(1)
    def raising(r):
        raise RuntimeError("boom")
    verdict = verify_chain(chain,
                            key_resolver=lambda sid: keys.get(sid),
                            report_verifier=raising)
    assert not verdict.valid
    assert "boom" in verdict.reason


# =====================================================================
# Never raises
# =====================================================================

def test_verifier_never_raises_on_bad_input():
    print("=== verify_chain never raises on bad input ===")
    assert not verify_chain(None, lambda s: None).valid
    assert not verify_chain("not-a-chain", lambda s: None).valid
    assert not verify_chain({}, lambda s: None).valid
    empty = AttestedChain(report=_stub_report()[0], links=[])
    assert not verify_chain(empty, lambda s: None).valid


def test_key_resolver_raising_is_caught():
    print("=== key_resolver raising is caught ===")
    chain, _, _, _, _, _ = _build_chain(1)
    def raising(sid):
        raise RuntimeError("boom")
    verdict = verify_chain(chain, key_resolver=raising)
    assert not verdict.valid
    assert "boom" in verdict.reason


# =====================================================================
# JSON roundtrip
# =====================================================================

def test_chain_json_roundtrip():
    print("=== Chain JSON roundtrip preserves verification ===")
    chain, _, alice_kp, _, keys, _ = _build_chain(2)
    wire = json.dumps(chain.to_dict())
    revived = AttestedChain.from_dict(json.loads(wire))
    verdict = verify_chain(
        revived,
        key_resolver=lambda sid: keys.get(sid),
        report_verifier=lambda r: verify_signed_report(
            r, alice_kp.public_key_hex()))
    assert verdict.valid
    assert len(revived.links) == len(chain.links)
    assert revived.report.signer_name == chain.report.signer_name


# =====================================================================
# Hash stability
# =====================================================================

def test_link_hash_is_stable():
    print("=== Link hash is stable across calls ===")
    chain, _, _, _, _, _ = _build_chain(1)
    for link in chain.links:
        assert link.link_hash() == link.link_hash()


def test_link_hash_changes_with_content():
    print("=== Link hash changes when content changes ===")
    chain, _, _, _, _, _ = _build_chain(1)
    link = chain.links[0]
    tampered = ChainLink(
        link_index=link.link_index,
        signer_id=link.signer_id,
        signer_name="Different",
        previous_link_hash=link.previous_link_hash,
        report_hash=link.report_hash,
        timestamp=link.timestamp,
        signature=link.signature,
    )
    assert tampered.link_hash() != link.link_hash()


# =====================================================================
# The honest limit, as a test
# =====================================================================

def test_chain_attests_who_said_not_what_is_true():
    """A chain of honest-looking witnesses can endorse a fabricated
    report. The chain is valid; the report's content is a lie.
    That's not a bug. The chain is a record of attestations; trust
    decisions look at WHO signed, not just that they did.
    """
    print("=== Honest limit: chain attests to WHO said, not to TRUTH ===")
    # Alice signs a report claiming all_verified=True
    alice_kp = KeyPair.generate()
    alice = create_identity("Alice")
    rep = ProvenanceReport(
        passport_token="t",
        passport_name="Alice",
        registry_url="http://r",
    )
    # (No entries at all — an empty report "claiming" all_verified)
    signed_report = sign_report(rep, alice_kp, alice)

    # Bob and Carol witness it without inspecting
    bob_kp = KeyPair.generate()
    bob = create_identity("Bob")
    carol_kp = KeyPair.generate()
    carol = create_identity("Carol")
    keys = {
        alice.token: alice_kp.public_key_hex(),
        bob.token: bob_kp.public_key_hex(),
        carol.token: carol_kp.public_key_hex(),
    }
    builder = ChainBuilder(signed_report)
    builder.attest(alice_kp, alice)
    builder.attest(bob_kp, bob)
    builder.attest(carol_kp, carol)
    chain = builder.build()

    verdict = verify_chain(chain,
                            key_resolver=lambda sid: keys.get(sid))
    assert verdict.valid
    # The report's content is an empty entries list — but the chain
    # doesn't judge. It only says: Alice anchored, Bob witnessed,
    # Carol witnessed. Whether the report is meaningful is the
    # reader's call.
    print(f"  chain valid: {verdict.valid}")
    print(f"  signers: {verdict.verified_signers}")
    print(f"  report entries: {len(chain.report.report.get('entries', []))}")


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: Alice anchors, Bob and Carol witness ===")
    from multiverse_c25 import demo
    chain = demo(artifact_dir=str(tmp_path))
    assert len(chain.links) == 3
    assert chain.links[0].link_index == 0
    assert chain.links[1].previous_link_hash == chain.links[0].link_hash()
    assert chain.links[2].previous_link_hash == chain.links[1].link_hash()
    assert (tmp_path / "attested_chain.json").exists()
    assert (tmp_path / "attested_chain_verdict.json").exists()
    verdict_data = json.loads(
        (tmp_path / "attested_chain_verdict.json").read_text())
    assert verdict_data["valid"] is True


if __name__ == "__main__":
    test_link_zero_requires_report_hash()
    test_link_nonzero_requires_previous_link_hash()
    test_chain_of_three_verifies()
    test_chain_of_one_verifies()
    test_chain_without_report_verifier()
    test_tampered_link_breaks_chain()
    test_reordered_links_caught()
    test_dropped_link_caught()
    test_swapped_report_caught()
    test_wrong_public_key_rejected()
    test_missing_public_key_rejected()
    test_report_verifier_rejects()
    test_report_verifier_raises_is_caught()
    test_verifier_never_raises_on_bad_input()
    test_key_resolver_raising_is_caught()
    test_chain_json_roundtrip()
    test_link_hash_is_stable()
    test_link_hash_changes_with_content()
    test_chain_attests_who_said_not_what_is_true()
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        from pathlib import Path
        test_demo(Path(tmp))
