import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c15 import PassportEntry
from multiverse_c21 import ProvenanceReport, EntryProvenance
from multiverse_c24 import sign_report
from multiverse_c27 import (
    AttestedDAG, DAGLink, verify_dag,
)
from multiverse_c34 import (
    DictDAGResolver, ExtendedDAGBuilder, ExtendingDAGLink,
)
from multiverse_c36 import create_person, bind_token
from multiverse_c40 import (
    WorldAttestationRef, CrossWorldClaim,
    CrossWorldPersonAttestation,
    ReferenceResult, CrossWorldVerdict,
    create_cross_world_attestation,
    verify_cross_world_attestation,
    demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _make_arm(arm_name: str, world_name: str):
    """Build one arm: a report, a DAG, a single link, and its keys."""
    arm_identity = create_identity(f"{arm_name}-arm")
    arm_kp = KeyPair.generate()
    rep = ProvenanceReport(
        passport_token=arm_identity.token,
        passport_name=arm_identity.name,
        registry_url=f"http://{world_name}.example/registry",
    )
    entry = PassportEntry(
        entity_id=f"world:{world_name}",
        timestamp="2024-01-01T00:00:00+00:00",
        subject_token=arm_identity.token,
        signature="cc" * 64,
    )
    ep = EntryProvenance(entry=entry)
    ep.verdict = "verified"
    ep.reason = "stub"
    rep.entries.append(ep)
    signed = sign_report(rep, arm_kp, arm_identity)
    builder = ExtendedDAGBuilder(signed)
    link = builder.attest(arm_kp, arm_identity)
    dag = builder.build()
    return {
        "identity": arm_identity,
        "kp": arm_kp,
        "public_key": arm_kp.public_key_hex(),
        "report": signed,
        "dag": dag,
        "link": link,
        "link_hash": link.link_hash(),
    }


def _make_three_arms():
    return {
        "poetry": _make_arm("poetry", "poetry"),
        "chemistry": _make_arm("chemistry", "chemistry"),
        "registry": _make_arm("registry", "registry"),
    }


def _claim_for(arms, person_name="Aria"):
    refs = tuple(
        WorldAttestationRef(
            world_id=f"world:{name}",
            dag_id=f"dag:{name}",
            link_hash=arms[name]["link_hash"],
            purpose=f"{name} this epoch",
        )
        for name in arms
    )
    return CrossWorldClaim(
        kind="distributed-self-manifestation",
        content={"person": person_name},
        references=refs,
    )


def _resolvers_for(arms):
    dags = {f"dag:{name}": a["dag"] for name, a in arms.items()}
    keys = {a["identity"].token: a["public_key"]
            for a in arms.values()}
    return DictDAGResolver(dags), (lambda sid: keys.get(sid))


# =====================================================================
# Construction validation
# =====================================================================

def test_claim_requires_at_least_two_refs():
    print("=== CrossWorldClaim requires >= 2 references ===")
    ref = WorldAttestationRef(
        world_id="world:a", dag_id="dag:a", link_hash="aa" * 32)
    with pytest.raises(ValueError):
        CrossWorldClaim(
            kind="x", content={}, references=(ref,))


def test_claim_requires_two_distinct_worlds():
    print("=== CrossWorldClaim requires >= 2 distinct worlds ===")
    ref1 = WorldAttestationRef(
        world_id="world:a", dag_id="dag:a", link_hash="aa" * 32)
    ref2 = WorldAttestationRef(
        world_id="world:a", dag_id="dag:a2", link_hash="bb" * 32)
    with pytest.raises(ValueError):
        CrossWorldClaim(
            kind="x", content={}, references=(ref1, ref2))


def test_claim_rejects_duplicate_refs():
    print("=== CrossWorldClaim rejects duplicate (world, link) ===")
    ref1 = WorldAttestationRef(
        world_id="world:a", dag_id="dag:a", link_hash="aa" * 32)
    ref2 = WorldAttestationRef(
        world_id="world:b", dag_id="dag:b", link_hash="bb" * 32)
    ref2_dup = WorldAttestationRef(
        world_id="world:b", dag_id="dag:b", link_hash="bb" * 32)
    with pytest.raises(ValueError):
        CrossWorldClaim(
            kind="x", content={},
            references=(ref1, ref2, ref2_dup))


def test_ref_validates_hex_link_hash():
    print("=== WorldAttestationRef: link_hash must be 64 hex ===")
    with pytest.raises(ValueError):
        WorldAttestationRef(
            world_id="w", dag_id="d", link_hash="short")


# =====================================================================
# create_cross_world_attestation
# =====================================================================

def test_create_happy():
    print("=== create_cross_world_attestation: happy path ===")
    arms = _make_three_arms()
    aria, aria_kp = create_person("Aria")
    claim = _claim_for(arms)
    att = create_cross_world_attestation(aria, aria_kp, claim)
    assert att.person_token == aria.person.token
    assert att.person_public_key == aria.person_public_key
    assert len(att.claim.references) == 3


def test_create_rejects_wrong_keypair():
    print("=== create rejects wrong keypair ===")
    arms = _make_three_arms()
    aria, _ = create_person("Aria")
    wrong_kp = KeyPair.generate()
    with pytest.raises(ValueError):
        create_cross_world_attestation(
            aria, wrong_kp, _claim_for(arms))


# =====================================================================
# verify_cross_world_attestation — happy path
# =====================================================================

def test_verify_happy():
    print("=== verify: happy path (3 arms) ===")
    arms = _make_three_arms()
    aria, aria_kp = create_person("Aria")
    att = create_cross_world_attestation(
        aria, aria_kp, _claim_for(arms))
    dag_resolver, key_resolver = _resolvers_for(arms)
    v = verify_cross_world_attestation(
        att, dag_resolver, key_resolver,
        trusted_person_public_key=aria.person_public_key)
    assert v.valid
    assert v.signature_valid
    assert len(v.reference_results) == 3
    assert all(r.ok for r in v.reference_results)


def test_verify_without_trusted_key_self_consistent():
    """No trusted key: verifies against declared key."""
    print("=== verify: no trusted key, self-consistent ===")
    arms = _make_three_arms()
    aria, aria_kp = create_person("Aria")
    att = create_cross_world_attestation(
        aria, aria_kp, _claim_for(arms))
    dag_resolver, key_resolver = _resolvers_for(arms)
    v = verify_cross_world_attestation(
        att, dag_resolver, key_resolver)  # no trusted key
    assert v.valid


def test_verify_four_arms():
    print("=== verify: N=4 arms ===")
    arms = {
        "poetry": _make_arm("poetry", "poetry"),
        "chemistry": _make_arm("chemistry", "chemistry"),
        "registry": _make_arm("registry", "registry"),
        "chess": _make_arm("chess", "chess"),
    }
    aria, aria_kp = create_person("Aria")
    att = create_cross_world_attestation(
        aria, aria_kp, _claim_for(arms))
    dag_resolver, key_resolver = _resolvers_for(arms)
    v = verify_cross_world_attestation(
        att, dag_resolver, key_resolver,
        trusted_person_public_key=aria.person_public_key)
    assert v.valid
    assert len(v.reference_results) == 4


# =====================================================================
# Signature failures
# =====================================================================

def test_forged_signature_rejected():
    print("=== verify: forged signature → INVALID ===")
    arms = _make_three_arms()
    aria, aria_kp = create_person("Aria")
    att = create_cross_world_attestation(
        aria, aria_kp, _claim_for(arms))
    attacker = KeyPair.generate()
    forged = CrossWorldPersonAttestation(
        person_token=att.person_token,
        person_name=att.person_name,
        person_public_key=att.person_public_key,
        claim=att.claim,
        timestamp=att.timestamp,
        signature=attacker.sign(att.canonical_payload()).hex(),
    )
    dag_resolver, key_resolver = _resolvers_for(arms)
    v = verify_cross_world_attestation(
        forged, dag_resolver, key_resolver,
        trusted_person_public_key=aria.person_public_key)
    assert not v.valid
    assert not v.signature_valid
    assert "INVALID" in v.reason


def test_tampered_claim_rejected():
    print("=== verify: tampered claim → signature breaks ===")
    arms = _make_three_arms()
    aria, aria_kp = create_person("Aria")
    claim = _claim_for(arms)
    att = create_cross_world_attestation(aria, aria_kp, claim)
    # Swap out the references (smaller subset) — same signature
    truncated = CrossWorldClaim(
        kind=claim.kind, content=claim.content,
        references=claim.references[:2],
    )
    tampered = CrossWorldPersonAttestation(
        person_token=att.person_token,
        person_name=att.person_name,
        person_public_key=att.person_public_key,
        claim=truncated,
        timestamp=att.timestamp,
        signature=att.signature,
    )
    dag_resolver, key_resolver = _resolvers_for(arms)
    v = verify_cross_world_attestation(
        tampered, dag_resolver, key_resolver,
        trusted_person_public_key=aria.person_public_key)
    assert not v.valid
    assert not v.signature_valid


def test_wrong_trusted_key_rejected():
    print("=== verify: wrong trusted key → INVALID ===")
    arms = _make_three_arms()
    aria, aria_kp = create_person("Aria")
    att = create_cross_world_attestation(
        aria, aria_kp, _claim_for(arms))
    dag_resolver, key_resolver = _resolvers_for(arms)
    wrong_key = KeyPair.generate().public_key_hex()
    v = verify_cross_world_attestation(
        att, dag_resolver, key_resolver,
        trusted_person_public_key=wrong_key)
    assert not v.valid
    assert not v.signature_valid


# =====================================================================
# Reference failures
# =====================================================================

def test_missing_dag_rejected():
    print("=== verify: missing DAG → reference fails ===")
    arms = _make_three_arms()
    aria, aria_kp = create_person("Aria")
    att = create_cross_world_attestation(
        aria, aria_kp, _claim_for(arms))
    # Resolver only knows dag:poetry
    partial_dags = {"dag:poetry": arms["poetry"]["dag"]}
    keys = {a["identity"].token: a["public_key"]
            for a in arms.values()}
    resolver = DictDAGResolver(partial_dags)
    v = verify_cross_world_attestation(
        att, resolver, lambda sid: keys.get(sid),
        trusted_person_public_key=aria.person_public_key)
    assert not v.valid
    failed = [r for r in v.reference_results if not r.ok]
    assert len(failed) == 2
    assert all("not found" in r.reason.lower() for r in failed)


def test_invalid_dag_rejected():
    print("=== verify: external DAG invalid → reference fails ===")
    arms = _make_three_arms()
    aria, aria_kp = create_person("Aria")
    att = create_cross_world_attestation(
        aria, aria_kp, _claim_for(arms))
    # Corrupt the poetry DAG by changing its root link's signature
    bad_links = []
    for link in arms["poetry"]["dag"].links:
        sig = link.signature
        bad_sig = ("0" if sig[0] != "0" else "1") + sig[1:]
        bad_links.append(DAGLink(
            signer_id=link.signer_id,
            signer_name=link.signer_name,
            previous_link_hashes=link.previous_link_hashes,
            report_hash=link.report_hash,
            timestamp=link.timestamp,
            signature=bad_sig,
        ))
    corrupted_poetry = AttestedDAG(
        report=arms["poetry"]["dag"].report, links=bad_links)
    dags = {
        "dag:poetry": corrupted_poetry,
        "dag:chemistry": arms["chemistry"]["dag"],
        "dag:registry": arms["registry"]["dag"],
    }
    keys = {a["identity"].token: a["public_key"]
            for a in arms.values()}
    v = verify_cross_world_attestation(
        att, DictDAGResolver(dags), lambda sid: keys.get(sid),
        trusted_person_public_key=aria.person_public_key)
    assert not v.valid
    failed = [r for r in v.reference_results if not r.ok]
    assert len(failed) == 1
    assert "invalid" in failed[0].reason.lower()


def test_link_not_found_rejected():
    print("=== verify: link not in DAG → reference fails ===")
    arms = _make_three_arms()
    aria, aria_kp = create_person("Aria")
    # Claim references a bogus link hash for poetry
    bogus_hash = "0" * 64
    claim = CrossWorldClaim(
        kind="test", content={},
        references=(
            WorldAttestationRef(
                world_id="world:poetry",
                dag_id="dag:poetry",
                link_hash=bogus_hash,
            ),
            WorldAttestationRef(
                world_id="world:chemistry",
                dag_id="dag:chemistry",
                link_hash=arms["chemistry"]["link_hash"],
            ),
        ),
    )
    att = create_cross_world_attestation(aria, aria_kp, claim)
    dag_resolver, key_resolver = _resolvers_for(arms)
    v = verify_cross_world_attestation(
        att, dag_resolver, key_resolver,
        trusted_person_public_key=aria.person_public_key)
    assert not v.valid
    poetry_result = next(
        r for r in v.reference_results
        if r.ref.world_id == "world:poetry")
    assert not poetry_result.link_found
    assert "not in DAG" in poetry_result.reason


def test_link_signer_not_verified_rejected():
    print("=== verify: link's signer not in DAG verified set ===")
    # Two-link DAG where the referenced link's signer is not in the
    # verified signers list. This is hard to construct via the
    # builders (which verify signatures), so we forge a DAG with a
    # mismatched key resolver.
    arms = _make_three_arms()
    aria, aria_kp = create_person("Aria")
    att = create_cross_world_attestation(
        aria, aria_kp, _claim_for(arms))
    # Replace poetry's key with a wrong one — verify_dag will fail
    # before reaching the "signer not in verified set" check, so
    # the reference fails at the DAG-invalid stage. This test
    # demonstrates the propagation: broken DAG → failed reference.
    dags = {f"dag:{name}": a["dag"] for name, a in arms.items()}
    keys = {a["identity"].token: a["public_key"]
            for a in arms.values()}
    # Corrupt poetry's key
    keys[arms["poetry"]["identity"].token] = \
        KeyPair.generate().public_key_hex()
    v = verify_cross_world_attestation(
        att, DictDAGResolver(dags), lambda sid: keys.get(sid),
        trusted_person_public_key=aria.person_public_key)
    assert not v.valid
    failed = [r for r in v.reference_results if not r.ok]
    assert len(failed) == 1
    assert failed[0].ref.world_id == "world:poetry"


# =====================================================================
# Never raises
# =====================================================================

def test_verifier_never_raises():
    print("=== verify_cross_world_attestation never raises ===")
    assert not verify_cross_world_attestation(
        None, lambda d: None, lambda s: None).valid
    assert not verify_cross_world_attestation(
        "not an att", lambda d: None, lambda s: None).valid
    assert not verify_cross_world_attestation(
        {}, lambda d: None, lambda s: None).valid


def test_dag_resolver_raising_caught():
    print("=== dag_resolver raising → reference fails, no exception ===")
    arms = _make_three_arms()
    aria, aria_kp = create_person("Aria")
    att = create_cross_world_attestation(
        aria, aria_kp, _claim_for(arms))
    def raising(dag_id):
        raise RuntimeError("boom")
    keys = {a["identity"].token: a["public_key"]
            for a in arms.values()}
    v = verify_cross_world_attestation(
        att, raising, lambda sid: keys.get(sid),
        trusted_person_public_key=aria.person_public_key)
    assert not v.valid
    assert all("boom" in r.reason for r in v.reference_results)


# =====================================================================
# JSON roundtrips
# =====================================================================

def test_claim_json_roundtrip():
    print("=== CrossWorldClaim JSON roundtrip ===")
    arms = _make_three_arms()
    claim = _claim_for(arms)
    d = claim.to_claim_dict()
    revived = CrossWorldClaim.from_dict(d)
    assert revived.to_claim_dict() == d
    assert len(revived.references) == 3


def test_attestation_json_roundtrip():
    print("=== CrossWorldPersonAttestation JSON roundtrip ===")
    arms = _make_three_arms()
    aria, aria_kp = create_person("Aria")
    att = create_cross_world_attestation(
        aria, aria_kp, _claim_for(arms))
    wire = json.dumps(att.to_dict())
    revived = CrossWorldPersonAttestation.from_dict(
        json.loads(wire))
    assert revived.canonical_payload() == att.canonical_payload()
    dag_resolver, key_resolver = _resolvers_for(arms)
    v = verify_cross_world_attestation(
        revived, dag_resolver, key_resolver,
        trusted_person_public_key=aria.person_public_key)
    assert v.valid


# =====================================================================
# The C41 property: arm independence
# =====================================================================

def test_each_arm_verifies_without_cross_world_attestation():
    """The property C41 will depend on: each arm's DAG is complete
    on its own. The cross-world attestation is optional coordination.
    """
    print("=== ARM INDEPENDENCE: each DAG verifies alone ===")
    arms = _make_three_arms()
    for name, arm in arms.items():
        v = verify_dag(
            arm["dag"],
            key_resolver=lambda sid, _a=arm: (
                _a["public_key"] if sid == _a["identity"].token
                else None),
        )
        assert v.valid, f"{name} DAG did not verify alone"
        assert arm["identity"].name in v.verified_signers
        print(f"  ✓ dag:{name} verifies alone "
              f"({v.verified_signers})")


def test_adding_an_arm_does_not_require_touching_others():
    """C41's scaling property: adding a fourth arm is local. The
    other three arms' DAGs are unchanged; a new attestation is
    signed referencing all four. No other artifact changes."""
    print("=== SCALING: adding an arm is local ===")
    # Build three arms and attest
    arms_3 = _make_three_arms()
    aria, aria_kp = create_person("Aria")
    att_3 = create_cross_world_attestation(
        aria, aria_kp, _claim_for(arms_3))
    # Add a fourth arm — the first three's DAGs are unchanged
    arms_4 = dict(arms_3)
    arms_4["chess"] = _make_arm("chess", "chess")
    att_4 = create_cross_world_attestation(
        aria, aria_kp, _claim_for(arms_4))

    # Both attestations verify
    dr_3, kr_3 = _resolvers_for(arms_3)
    v_3 = verify_cross_world_attestation(
        att_3, dr_3, kr_3,
        trusted_person_public_key=aria.person_public_key)
    dr_4, kr_4 = _resolvers_for(arms_4)
    v_4 = verify_cross_world_attestation(
        att_4, dr_4, kr_4,
        trusted_person_public_key=aria.person_public_key)
    assert v_3.valid
    assert v_4.valid
    # The first three arms' DAGs are unchanged:
    for name in ("poetry", "chemistry", "registry"):
        assert (arms_3[name]["link_hash"]
                == arms_4[name]["link_hash"])
    print(f"  att_3 valid: {v_3.valid} "
          f"({len(v_3.reference_results)} refs)")
    print(f"  att_4 valid: {v_4.valid} "
          f"({len(v_4.reference_results)} refs)")
    print(f"  first 3 links unchanged: ✓")


# =====================================================================
# The honest limit: attestation is by the signer, not endorsement
# =====================================================================

def test_attestation_is_by_signer_not_endorsement():
    """Bob can sign a cross-world attestation referencing Aria's
    arms' DAG links. That's Bob's claim, not Aria's endorsement.
    The verifier sees "Bob says X," not "Aria agrees with Bob."
    """
    print("=== Honest limit: attestation is by the signer ===")
    arms = _make_three_arms()
    aria, aria_kp = create_person("Aria")
    bob, bob_kp = create_person("Bob")

    # Bob claims his own distributed self, referencing Aria's links
    bob_claim = CrossWorldClaim(
        kind="observation",
        content={
            "note": "Aria's arms are doing interesting work; "
                    "I am attesting that I observed them.",
        },
        references=tuple(
            WorldAttestationRef(
                world_id=f"world:{name}",
                dag_id=f"dag:{name}",
                link_hash=arms[name]["link_hash"],
            )
            for name in arms
        ),
    )
    bob_att = create_cross_world_attestation(
        bob, bob_kp, bob_claim)

    dr, kr = _resolvers_for(arms)
    v = verify_cross_world_attestation(
        bob_att, dr, kr,
        trusted_person_public_key=bob.person_public_key)
    # The attestation verifies AS BOB'S CLAIM.
    assert v.valid
    assert v.person_token == bob.person.token
    # It is NOT Aria's attestation. Verifying against Aria's key
    # would fail.
    v_as_aria = verify_cross_world_attestation(
        bob_att, dr, kr,
        trusted_person_public_key=aria.person_public_key)
    assert not v_as_aria.valid
    assert not v_as_aria.signature_valid
    print("  verified as Bob's claim: ✓")
    print("  verifies as Aria's attestation: ✗ (signature INVALID)")
    print("  (the attestation claims authorship, not endorsement)")


# =====================================================================
# Composition with C34: cross-DAG inside a world
# =====================================================================

def test_composition_with_cross_dag_reference():
    """A world's DAG can itself extend another world's DAG (C34).
    The cross-world attestation's reference still verifies — the
    resolver handles the extension transparently."""
    print("=== Composition: cross-world attestation + C34 cross-DAG ===")
    arms = _make_three_arms()

    # Make dag:poetry extend dag:chemistry via C34
    poetry_arm = arms["poetry"]
    chemistry_arm = arms["chemistry"]
    from multiverse_c13 import KeyPair as KP
    # Rebuild poetry's DAG with an extension link
    b = ExtendedDAGBuilder(poetry_arm["report"])
    root = b.attest(poetry_arm["kp"], poetry_arm["identity"])
    # Second link extends chemistry's link
    link2_kp = KP.generate()
    link2_id = create_identity("poetry-arm-link2")
    link2 = b.attest(
        link2_kp, link2_id,
        previous_link_hashes=(root.link_hash(),),
        external_references=(
            ("dag:chemistry", chemistry_arm["link_hash"]),
        ),
    )
    extended_poetry_dag = b.build()

    # Attestation references poetry's root link (still valid)
    claim = CrossWorldClaim(
        kind="composed", content={},
        references=(
            WorldAttestationRef(
                world_id="world:poetry",
                dag_id="dag:poetry",
                link_hash=root.link_hash(),
            ),
            WorldAttestationRef(
                world_id="world:chemistry",
                dag_id="dag:chemistry",
                link_hash=chemistry_arm["link_hash"],
            ),
        ),
    )
    aria, aria_kp = create_person("Aria")
    att = create_cross_world_attestation(aria, aria_kp, claim)

    # Resolver: poetry DAG is the extended one
    dags = {
        "dag:poetry": extended_poetry_dag,
        "dag:chemistry": chemistry_arm["dag"],
    }
    keys = {
        poetry_arm["identity"].token: poetry_arm["public_key"],
        chemistry_arm["identity"].token: chemistry_arm["public_key"],
        link2_id.token: link2_kp.public_key_hex(),
    }
    v = verify_cross_world_attestation(
        att, DictDAGResolver(dags), lambda sid: keys.get(sid),
        trusted_person_public_key=aria.person_public_key)
    assert v.valid, v.reason


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: three arms, one attestation, negative cases ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["arms_all_verify_alone"] is True
    assert audit["attestation_valid"] is True
    assert audit["attestation_signature_valid"] is True
    assert audit["reference_count"] == 3
    assert audit["forged_signature_valid"] is False
    assert audit["missing_dag_valid"] is False
    assert audit["wrong_trusted_key_valid"] is False
    assert (tmp_path / "cross_world_attestation_demo.json").exists()
    # All three DAGs verify locally
    for dag_id, v_dict in audit["local_dag_verdicts"].items():
        assert v_dict["valid"] is True


if __name__ == "__main__":
    test_claim_requires_at_least_two_refs()
    test_claim_requires_two_distinct_worlds()
    test_claim_rejects_duplicate_refs()
    test_ref_validates_hex_link_hash()
    test_create_happy()
    test_create_rejects_wrong_keypair()
    test_verify_happy()
    test_verify_without_trusted_key_self_consistent()
    test_verify_four_arms()
    test_forged_signature_rejected()
    test_tampered_claim_rejected()
    test_wrong_trusted_key_rejected()
    test_missing_dag_rejected()
    test_invalid_dag_rejected()
    test_link_not_found_rejected()
    test_link_signer_not_verified_rejected()
    test_verifier_never_raises()
    test_dag_resolver_raising_caught()
    test_claim_json_roundtrip()
    test_attestation_json_roundtrip()
    test_each_arm_verifies_without_cross_world_attestation()
    test_adding_an_arm_does_not_require_touching_others()
    test_attestation_is_by_signer_not_endorsement()
    test_composition_with_cross_dag_reference()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
