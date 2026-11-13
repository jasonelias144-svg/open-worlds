# multiverse_c40_demo.py — the demo, factored out for clarity

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Aria: three arms, three worlds, one cross-world attestation.

    Structure (which is the C41 blueprint):

      - Three arms, each with its own holder keypair (from C36).
      - Three worlds, each with its own DAG. The arm signs one link
        per world.
      - Aria (the person) signs ONE cross-world attestation that
        references all three links.
      - A third party with Aria's public key + a DAG resolver
        verifies the whole structure.

    The key property the demo makes visible: each DAG verifies
    *alone*, before the cross-world attestation exists. The arms
    are self-sufficient. The attestation is optional coordination.

    Anchor: Emily Dickinson, 'The Brain – is wider than the Sky –',
    public domain.
    """
    import json
    from pathlib import Path
    from multiverse_c1 import create_identity
    from multiverse_c14 import PermissiveWorld
    from multiverse_c15 import PassportEntry
    from multiverse_c21 import ProvenanceReport, EntryProvenance
    from multiverse_c24 import sign_report
    from multiverse_c27 import (
        DAGLink, AttestedDAG, DAGVerdict, verify_dag,
    )
    from multiverse_c34 import (
        DictDAGResolver, ExtendedDAGBuilder, verify_dag_extended,
    )
    from multiverse_c36 import create_person, bind_token
    from multiverse_c40 import (
        WorldAttestationRef, CrossWorldClaim,
        create_cross_world_attestation,
        verify_cross_world_attestation,
    )

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    # ---------------------------------------------------------------
    # The person: Aria, three embodiments
    # ---------------------------------------------------------------
    aria, aria_kp = create_person("Aria")
    arm_keys = {}
    for name in ("poetry", "chemistry", "registry"):
        tok = create_identity(f"Aria@{name}")
        holder_kp = KeyPair.generate()
        aria, _ = bind_token(
            aria, aria_kp, tok.token, tok.name, holder_kp)
        arm_keys[name] = {
            "token": tok.token,
            "name": tok.name,
            "holder_kp": holder_kp,
        }

    # ---------------------------------------------------------------
    # Each arm produces its own DAG in its own world
    #
    # This is what makes it "octopus-shaped": no arm needs to see
    # another arm's output to produce its own.
    # ---------------------------------------------------------------
    def _stub_report(arm_name: str):
        """Each arm's DAG attests a report specific to its world."""
        rkp = arm_keys[arm_name]["holder_kp"]
        who = aria  # the arm signs as the person? no — as itself
        # Actually: the arm signs as itself (its holder identity).
        # Let's use a distinct arm identity for DAG signing.
        arm_identity = create_identity(f"{arm_name}-arm")
        from multiverse_c13 import KeyPair as KP
        arm_signing_kp = KP.generate()

        rep = ProvenanceReport(
            passport_token=arm_identity.token,
            passport_name=arm_identity.name,
            registry_url=f"http://{arm_name}.example/registry",
        )
        entry = PassportEntry(
            entity_id=f"world:{arm_name}",
            timestamp="2024-01-01T00:00:00+00:00",
            subject_token=arm_identity.token,
            signature="cc" * 64,
        )
        ep = EntryProvenance(entry=entry)
        ep.verdict = "verified"
        ep.reason = "stub"
        rep.entries.append(ep)
        signed = sign_report(rep, arm_signing_kp, arm_identity)
        return signed, arm_signing_kp, arm_identity

    arm_dags = {}
    arm_links = {}
    arm_keys_for_dag = {}
    for arm_name in ("poetry", "chemistry", "registry"):
        report, arm_kp, arm_identity = _stub_report(arm_name)
        builder = ExtendedDAGBuilder(report)
        link = builder.attest(arm_kp, arm_identity)
        arm_dags[f"dag:{arm_name}"] = builder.build()
        arm_links[arm_name] = link
        arm_keys_for_dag[arm_identity.token] = arm_kp.public_key_hex()

    # ---------------------------------------------------------------
    # The arms are locally complete. Each DAG verifies alone.
    #
    # This is the property the demo shows FIRST, before any
    # coordination. C41 will rely on exactly this: each arm's link
    # is its own attestation, complete in its world, no coordination
    # required to produce it.
    # ---------------------------------------------------------------
    local_dag_verdicts = {}
    for dag_id, dag in arm_dags.items():
        v = verify_dag(
            dag,
            key_resolver=lambda sid, _a=arm_keys_for_dag: _a.get(sid),
        )
        local_dag_verdicts[dag_id] = v

    arms_all_verify_alone = all(
        v.valid for v in local_dag_verdicts.values())

    # ---------------------------------------------------------------
    # The higher-order layer: Aria signs ONE cross-world attestation
    #
    # No N-way consensus. No round-trip. Aria's key signs a single
    # artifact. Each arm's consent was pre-established by C36's
    # dual-signed bindings. The attestation coordinates; the arms
    # don't need to.
    # ---------------------------------------------------------------
    claim = CrossWorldClaim(
        kind="distributed-self-manifestation",
        content={
            "person": "Aria",
            "seed_line": "The Brain – is wider than the Sky –",
            "note": ("Three arms, three worlds, one person. "
                     "Each arm's artifact is complete alone. "
                     "This attestation binds them, by choice, "
                     "not by necessity."),
        },
        references=(
            WorldAttestationRef(
                world_id="world:poetry",
                dag_id="dag:poetry",
                link_hash=arm_links["poetry"].link_hash(),
                purpose="poem authored this epoch",
            ),
            WorldAttestationRef(
                world_id="world:chemistry",
                dag_id="dag:chemistry",
                link_hash=arm_links["chemistry"].link_hash(),
                purpose="reaction performed this epoch",
            ),
            WorldAttestationRef(
                world_id="world:registry",
                dag_id="dag:registry",
                link_hash=arm_links["registry"].link_hash(),
                purpose="listing posted this epoch",
            ),
        ),
    )
    attestation = create_cross_world_attestation(
        aria, aria_kp, claim)

    # ---------------------------------------------------------------
    # Third-party verification
    # ---------------------------------------------------------------
    dag_resolver = DictDAGResolver(arm_dags)
    key_resolver = lambda sid: arm_keys_for_dag.get(sid)

    verdict = verify_cross_world_attestation(
        attestation, dag_resolver, key_resolver,
        trusted_person_public_key=aria.person_public_key,
    )

    # ---------------------------------------------------------------
    # Negative tests visible in the demo
    # ---------------------------------------------------------------
    # Attacker forges Aria's signature
    attacker_kp = KeyPair.generate()
    forged_signature = attacker_kp.sign(
        attestation.canonical_payload()).hex()
    from multiverse_c40 import CrossWorldPersonAttestation
    forged_attestation = CrossWorldPersonAttestation(
        person_token=attestation.person_token,
        person_name=attestation.person_name,
        person_public_key=attestation.person_public_key,
        claim=attestation.claim,
        timestamp=attestation.timestamp,
        signature=forged_signature,
    )
    forged_verdict = verify_cross_world_attestation(
        forged_attestation, dag_resolver, key_resolver,
        trusted_person_public_key=aria.person_public_key,
    )

    # Missing DAG in the resolver
    partial_resolver = DictDAGResolver({
        "dag:poetry": arm_dags["dag:poetry"],
        # chemistry and registry omitted
    })
    missing_verdict = verify_cross_world_attestation(
        attestation, partial_resolver, key_resolver,
        trusted_person_public_key=aria.person_public_key,
    )

    # Wrong trusted key
    wrong_key = KeyPair.generate().public_key_hex()
    wrong_verdict = verify_cross_world_attestation(
        attestation, dag_resolver, key_resolver,
        trusted_person_public_key=wrong_key,
    )

    # ---------------------------------------------------------------
    # Print the report
    # ---------------------------------------------------------------
    print("=" * 70)
    print("Cross-World Person Attestation — demo")
    print("=" * 70)
    print()
    print("  Step 1: Local autonomy.")
    print("    Each arm's DAG verifies alone. Before Aria has")
    print("    signed anything at the higher level.")
    print()
    for dag_id, v in local_dag_verdicts.items():
        marker = "✓" if v.valid else "✗"
        print(f"    {marker} {dag_id}: "
              f"{v.reason} "
              f"({len(v.verified_signers)} signer(s))")
    print(f"    arms_all_verify_alone: {arms_all_verify_alone}")
    print()
    print("  Step 2: Higher-order coordination.")
    print("    Aria signs ONE attestation. One signature.")
    print("    Each arm's link is referenced by (world_id, dag_id,")
    print("    link_hash). No round-trip.")
    print()
    for line in verdict.format().split("\n"):
        print(f"    {line}")
    print()
    print("  Step 3: The negative cases.")
    print()
    print(f"    Forged Aria signature:")
    print(f"      valid: {forged_verdict.valid}, "
          f"signature_valid: {forged_verdict.signature_valid}")
    print()
    print(f"    Missing DAG (chemistry and registry omitted):")
    print(f"      valid: {missing_verdict.valid}")
    for rr in missing_verdict.reference_results:
        if not rr.ok:
            print(f"      ✗ {rr.ref.world_id}: {rr.reason}")
    print()
    print(f"    Wrong trusted key:")
    print(f"      valid: {wrong_verdict.valid}, "
          f"signature_valid: {wrong_verdict.signature_valid}")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'The Brain – is wider than the Sky –'")
    print("    'For – put them side by side –'")
    print("    'The one the other will contain'")
    print("    'With ease – and You – beside –'")

    audit = {
        "arms_all_verify_alone": arms_all_verify_alone,
        "local_dag_verdicts": {
            dag_id: v.to_dict()
            for dag_id, v in local_dag_verdicts.items()
        },
        "attestation_valid": verdict.valid,
        "attestation_signature_valid": verdict.signature_valid,
        "reference_count": len(verdict.reference_results),
        "forged_signature_valid":
            forged_verdict.signature_valid,
        "missing_dag_valid": missing_verdict.valid,
        "wrong_trusted_key_valid": wrong_verdict.valid,
        "person_public_key": aria.person_public_key,
    }
    if artifact_dir:
        path = Path(artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "cross_world_attestation_demo.json").write_text(
            json.dumps(audit, indent=2))
        print(f"\n  → {path}/cross_world_attestation_demo.json")
    return audit
