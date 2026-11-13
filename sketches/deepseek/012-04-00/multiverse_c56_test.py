import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c44 import QuorumRule
from multiverse_c45 import (
    Proposal, DeliberativeCouncil, DeliberativeMember,
)
from multiverse_c48 import (
    FederationAttestation,
    attest_deliberative_decision,
    verify_federation_attestation,
)
from multiverse_c52 import EpochResult
from multiverse_c54 import (
    AttestedRumor,
    AttestedEpidemicNetwork,
    VerifyingEpidemicUnit,
)
from multiverse_c56 import (
    RelayAttestation, verify_relay,
    ReceiptAttestation, verify_receipt,
    SigningVerifyingUnit,
    SignedRelayNetwork,
    SignedRelayChain,
    Hop, SignedRelayVerdict,
    reconstruct_hops, verify_signed_relay_chain,
    demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _make_attested_and_context():
    kps = [KeyPair.generate() for _ in range(3)]
    council = DeliberativeCouncil(
        "council", QuorumRule(2, 2),
        max_rounds=2, stability_rounds=1)
    for i, kp in enumerate(kps):
        council.add_member(DeliberativeMember(
            entity_id=f"council:m{i}",
            name=f"C-{i}", member_kp=kp,
            decision_rule=lambda p, c: ("yea", "ok")))
    keys = {f"council:m{i}": kp.public_key_hex()
            for i, kp in enumerate(kps)}
    decision = council.deliberate_and_resolve(
        Proposal(content={"action": "test"}))
    att = attest_deliberative_decision("council", decision)
    attested = AttestedRumor.from_attestation(att)
    return attested, {"member_keys": {"council": keys}}


def _build_chain(names, contexts, unit_kps=None):
    net = SignedRelayNetwork()
    keys = dict(unit_kps or {})
    for i, name in enumerate(names):
        contacts = []
        if i > 0:
            contacts.append(names[i - 1])
        if i < len(names) - 1:
            contacts.append(names[i + 1])
        if name not in keys:
            keys[name] = KeyPair.generate()
        net.add_unit(name, SigningVerifyingUnit(
            entity_id=f"world:{name}", name=name,
            unit_kp=keys[name], contacts=contacts,
            susceptibility=1,
            trust_context=contexts.get(name)))
    return net, {n: kp.public_key_hex()
                 for n, kp in keys.items()}


# =====================================================================
# RelayAttestation / ReceiptAttestation
# =====================================================================

def test_relay_attestation_validates_fields():
    print("=== RelayAttestation: validates fields ===")
    with pytest.raises(ValueError):
        RelayAttestation(
            relayer_world_id="",
            relayer_public_key="aa" * 32,
            attestation_content_hash="bb" * 32,
            target_world_id="T", epoch=0,
            timestamp="t", signature="s")
    with pytest.raises(ValueError):
        RelayAttestation(
            relayer_world_id="R",
            relayer_public_key="short",
            attestation_content_hash="bb" * 32,
            target_world_id="T", epoch=0,
            timestamp="t", signature="s")


def test_receipt_attestation_validates_fields():
    print("=== ReceiptAttestation: validates fields ===")
    with pytest.raises(ValueError):
        ReceiptAttestation(
            receiver_world_id="R",
            receiver_public_key="aa" * 32,
            attestation_content_hash="bb" * 32,
            source_world_id="",
            verified=True, reason="", timestamp="t",
            signature="s")


def test_relay_signed_by_sender():
    print("=== Relay: signed by sender's key ===")
    unit_kp = KeyPair.generate()
    payload = canonical_bytes({
        "kind": "relay_attestation",
        "relayer_world_id": "S",
        "relayer_public_key": unit_kp.public_key_hex(),
        "attestation_content_hash": "aa" * 32,
        "target_world_id": "T",
        "epoch": 0,
        "timestamp": "t",
    })
    relay = RelayAttestation(
        relayer_world_id="S",
        relayer_public_key=unit_kp.public_key_hex(),
        attestation_content_hash="aa" * 32,
        target_world_id="T", epoch=0, timestamp="t",
        signature=unit_kp.sign(payload).hex(),
    )
    assert verify_relay(relay)


def test_relay_wrong_key_rejected():
    print("=== Relay: wrong key → False ===")
    unit_kp = KeyPair.generate()
    payload = canonical_bytes({
        "kind": "relay_attestation",
        "relayer_world_id": "S",
        "relayer_public_key": unit_kp.public_key_hex(),
        "attestation_content_hash": "aa" * 32,
        "target_world_id": "T",
        "epoch": 0,
        "timestamp": "t",
    })
    relay = RelayAttestation(
        relayer_world_id="S",
        relayer_public_key=unit_kp.public_key_hex(),
        attestation_content_hash="aa" * 32,
        target_world_id="T", epoch=0, timestamp="t",
        signature=unit_kp.sign(payload).hex(),
    )
    wrong = KeyPair.generate()
    assert not verify_relay(relay, wrong.public_key_hex())


def test_receipt_signed_by_receiver():
    print("=== Receipt: signed by receiver's key ===")
    unit_kp = KeyPair.generate()
    payload = canonical_bytes({
        "kind": "receipt_attestation",
        "receiver_world_id": "T",
        "receiver_public_key": unit_kp.public_key_hex(),
        "attestation_content_hash": "aa" * 32,
        "source_world_id": "S",
        "verified": True,
        "reason": "ok",
        "timestamp": "t",
    })
    receipt = ReceiptAttestation(
        receiver_world_id="T",
        receiver_public_key=unit_kp.public_key_hex(),
        attestation_content_hash="aa" * 32,
        source_world_id="S", verified=True, reason="ok",
        timestamp="t",
        signature=unit_kp.sign(payload).hex(),
    )
    assert verify_receipt(receipt)


# =====================================================================
# SigningVerifyingUnit
# =====================================================================

def test_signing_unit_is_a_c54_unit():
    print("=== SigningUnit: is-a C54 VerifyingEpidemicUnit ===")
    attested, context = _make_attested_and_context()
    kp = KeyPair.generate()
    unit = SigningVerifyingUnit(
        "world:u", "U", unit_kp=kp,
        contacts=["A"], trust_context=context)
    assert isinstance(unit, VerifyingEpidemicUnit)
    # C52 attributes preserved
    assert hasattr(unit, "_contacts")
    assert hasattr(unit, "_exposures")
    # C54 attributes preserved
    assert hasattr(unit, "_verified_exposures")
    assert hasattr(unit, "_trust_context")
    # C56 attributes added
    assert hasattr(unit, "_unit_kp")
    assert hasattr(unit, "_relay_attestations")
    assert hasattr(unit, "_receipt_attestations")


def test_receipt_signed_on_act():
    print("=== SigningUnit: signs a receipt on act ===")
    attested, context = _make_attested_and_context()
    kp = KeyPair.generate()
    unit = SigningVerifyingUnit(
        "world:u", "U", unit_kp=kp, trust_context=context)
    from multiverse_c3 import Act
    unit.act(Act(
        actor_token="src", type="infect",
        payload={
            "rumor_id": attested.rumor_id,
            "source": "src",
            "attested": attested.to_dict(),
        }))
    receipts = unit.receipt_attestations()
    assert len(receipts) == 1
    r = receipts[0]
    assert r.receiver_world_id == "world:u"
    assert r.source_world_id == "src"
    assert r.verified is True  # valid context
    assert verify_receipt(r, kp.public_key_hex())


def test_receipt_signed_with_refusal():
    print("=== SigningUnit: signs receipt with verified=False ===")
    attested, _ = _make_attested_and_context()
    kp = KeyPair.generate()
    unit = SigningVerifyingUnit(
        "world:u", "U", unit_kp=kp,
        trust_context=None)  # no context
    from multiverse_c3 import Act
    unit.act(Act(
        actor_token="src", type="infect",
        payload={
            "rumor_id": attested.rumor_id,
            "source": "src",
            "attested": attested.to_dict(),
        }))
    receipts = unit.receipt_attestations()
    assert len(receipts) == 1
    assert receipts[0].verified is False
    assert "no trust context" in receipts[0].reason


def test_relay_signed_on_record_delivery():
    print("=== SigningUnit: signs relay on record_delivery ===")
    attested, context = _make_attested_and_context()
    kp = KeyPair.generate()
    unit = SigningVerifyingUnit(
        "world:u", "U", unit_kp=kp,
        contacts=["A"], trust_context=context)
    from multiverse_c3 import Act
    # First receive so unit has the attestation
    unit.act(Act(
        actor_token="external", type="infect",
        payload={
            "rumor_id": attested.rumor_id,
            "source": "external",
            "attested": attested.to_dict(),
        }))
    # Then tick to start spreading
    unit.tick(0)
    # Then record a delivery
    unit.record_delivery("A", attested.rumor_id, 0)
    relays = unit.relay_attestations()
    assert len(relays) == 1
    r = relays[0]
    assert r.relayer_world_id == "world:u"
    assert r.target_world_id == "A"
    assert verify_relay(r, kp.public_key_hex())


# =====================================================================
# SignedRelayNetwork
# =====================================================================

def test_network_seed_attested_creates_receipt():
    print("=== Network: seed_attested → seed receipt ===")
    attested, context = _make_attested_and_context()
    net, keys = _build_chain(["A"], {"A": context})
    net.seed_attested("A", attested)
    receipts = net._units["A"].receipt_attestations()
    assert len(receipts) == 1
    assert receipts[0].source_world_id == "external"


def test_network_full_chain_produces_relays_and_receipts():
    print("=== Network: full chain produces relays + receipts ===")
    attested, context = _make_attested_and_context()
    chain = ["A", "B", "C"]
    net, keys = _build_chain(
        chain, {n: context for n in chain})
    net.seed_attested("A", attested)
    net.run_until_quiet()
    rc = net.collect_relay_chain(attested.rumor_id)
    assert rc is not None
    # A relays to B; B relays to C
    assert len(rc.relays) == 2
    # A receipt from external; B receipt from A; C receipt from B
    assert len(rc.receipts) == 3


def test_network_collect_unknown_rumor_returns_none():
    print("=== Network: collect unknown rumor → None ===")
    _, context = _make_attested_and_context()
    net, _ = _build_chain(["A"], {"A": context})
    assert net.collect_relay_chain("nonexistent") is None


# =====================================================================
# Hop reconstruction
# =====================================================================

def test_reconstruct_hops_matches_relay_receipt():
    print("=== reconstruct_hops: matches relay to receipt ===")
    attested, context = _make_attested_and_context()
    chain = ["A", "B", "C"]
    net, keys = _build_chain(
        chain, {n: context for n in chain})
    net.seed_attested("A", attested)
    net.run_until_quiet()
    rc = net.collect_relay_chain(attested.rumor_id)
    hops = reconstruct_hops(rc)
    # Two hops: A→B, B→C; both confirmed
    assert len(hops) == 2
    assert all(h.confirmed for h in hops)


# =====================================================================
# Verification
# =====================================================================

def test_verify_chain_happy():
    print("=== verify: happy chain valid ===")
    attested, context = _make_attested_and_context()
    chain = ["A", "B", "C", "D"]
    net, keys = _build_chain(
        chain, {n: context for n in chain})
    net.seed_attested("A", attested)
    net.run_until_quiet()
    rc = net.collect_relay_chain(attested.rumor_id)
    v = verify_signed_relay_chain(
        rc, context=context,
        relay_public_keys=keys,
        receipt_public_keys=keys)
    assert v.valid
    assert v.attestation_valid
    assert v.all_relays_signed
    assert v.all_receipts_signed
    assert v.seed_recipient == "A"
    assert set(v.reached) == set(chain)


def test_verify_chain_skeptic():
    print("=== verify: skeptic breaks reach but chain valid ===")
    attested, context = _make_attested_and_context()
    chain = ["A", "B", "C"]
    contexts = {n: context for n in chain}
    contexts["B"] = None  # skeptic
    net, keys = _build_chain(chain, contexts)
    net.seed_attested("A", attested)
    net.run_until_quiet()
    rc = net.collect_relay_chain(attested.rumor_id)
    v = verify_signed_relay_chain(
        rc, context=context,
        relay_public_keys=keys,
        receipt_public_keys=keys)
    # A→B confirmed (receipt from B, verified=False)
    # B→C: no relay (B never spreading)
    assert v.valid
    assert "B" not in v.reached
    # Only A and B received
    receipt_holders = {
        r.receiver_world_id for r in rc.receipts}
    assert receipt_holders == {"A", "B"}


def test_verify_chain_forged_relay():
    print("=== verify: forged relay → invalid ===")
    attested, context = _make_attested_and_context()
    chain = ["A", "B"]
    net, keys = _build_chain(
        chain, {n: context for n in chain})
    net.seed_attested("A", attested)
    net.run_until_quiet()
    rc = net.collect_relay_chain(attested.rumor_id)
    # Tamper with a relay's signature
    attacker = KeyPair.generate()
    tampered_relays = list(rc.relays)
    orig = tampered_relays[0]
    tampered = RelayAttestation(
        relayer_world_id=orig.relayer_world_id,
        relayer_public_key=orig.relayer_public_key,
        attestation_content_hash=orig.attestation_content_hash,
        target_world_id=orig.target_world_id,
        epoch=orig.epoch,
        timestamp=orig.timestamp,
        signature=attacker.sign(
            orig.canonical_payload()).hex(),
    )
    tampered_relays[0] = tampered
    tampered_chain = SignedRelayChain(
        attestation=rc.attestation,
        relays=tuple(tampered_relays),
        receipts=rc.receipts)
    v = verify_signed_relay_chain(
        tampered_chain, context=context,
        relay_public_keys=keys,
        receipt_public_keys=keys)
    assert not v.valid
    assert not v.all_relays_signed


def test_verify_chain_forged_receipt():
    print("=== verify: forged receipt → invalid ===")
    attested, context = _make_attested_and_context()
    chain = ["A", "B"]
    net, keys = _build_chain(
        chain, {n: context for n in chain})
    net.seed_attested("A", attested)
    net.run_until_quiet()
    rc = net.collect_relay_chain(attested.rumor_id)
    attacker = KeyPair.generate()
    tampered_receipts = list(rc.receipts)
    orig = tampered_receipts[0]
    tampered = ReceiptAttestation(
        receiver_world_id=orig.receiver_world_id,
        receiver_public_key=orig.receiver_public_key,
        attestation_content_hash=orig.attestation_content_hash,
        source_world_id=orig.source_world_id,
        verified=orig.verified,
        reason=orig.reason,
        timestamp=orig.timestamp,
        signature=attacker.sign(
            orig.canonical_payload()).hex(),
    )
    tampered_receipts[0] = tampered
    tampered_chain = SignedRelayChain(
        attestation=rc.attestation,
        relays=rc.relays,
        receipts=tuple(tampered_receipts))
    v = verify_signed_relay_chain(
        tampered_chain, context=context,
        relay_public_keys=keys,
        receipt_public_keys=keys)
    assert not v.valid
    assert not v.all_receipts_signed


def test_verify_chain_attestation_invalid():
    print("=== verify: invalid attestation → invalid ===")
    attested, context = _make_attested_and_context()
    chain = ["A", "B"]
    net, keys = _build_chain(
        chain, {n: context for n in chain})
    net.seed_attested("A", attested)
    net.run_until_quiet()
    rc = net.collect_relay_chain(attested.rumor_id)
    # Tamper the attestation content
    tampered_att = FederationAttestation(
        source_id=rc.attestation.source_id,
        source_kind=rc.attestation.source_kind,
        content={**rc.attestation.content,
                 "tampered": True},
        content_hash=rc.attestation.content_hash,
    )
    tampered_chain = SignedRelayChain(
        attestation=tampered_att,
        relays=rc.relays, receipts=rc.receipts)
    v = verify_signed_relay_chain(
        tampered_chain, context=context,
        relay_public_keys=keys,
        receipt_public_keys=keys)
    assert not v.valid
    assert not v.attestation_valid


def test_verify_chain_no_seed():
    print("=== verify: no seed receipt → invalid ===")
    attested, context = _make_attested_and_context()
    chain = ["A", "B"]
    net, keys = _build_chain(
        chain, {n: context for n in chain})
    net.seed_attested("A", attested)
    net.run_until_quiet()
    rc = net.collect_relay_chain(attested.rumor_id)
    # Drop all receipts (so no seed)
    no_receipts = SignedRelayChain(
        attestation=rc.attestation,
        relays=rc.relays, receipts=())
    v = verify_signed_relay_chain(
        no_receipts, context=context,
        relay_public_keys=keys,
        receipt_public_keys=keys)
    assert not v.valid
    assert v.seed_recipient is None


# =====================================================================
# JSON roundtrip
# =====================================================================

def test_chain_json_roundtrip():
    print("=== SignedRelayChain: JSON roundtrip ===")
    attested, context = _make_attested_and_context()
    chain = ["A", "B"]
    net, keys = _build_chain(
        chain, {n: context for n in chain})
    net.seed_attested("A", attested)
    net.run_until_quiet()
    rc = net.collect_relay_chain(attested.rumor_id)
    wire = json.dumps(rc.to_dict())
    revived = SignedRelayChain.from_dict(json.loads(wire))
    v = verify_signed_relay_chain(
        revived, context=context,
        relay_public_keys=keys,
        receipt_public_keys=keys)
    assert v.valid


# =====================================================================
# Never raises
# =====================================================================

def test_verify_never_raises():
    print("=== verify: never raises ===")
    assert not verify_signed_relay_chain(None).valid
    assert not verify_signed_relay_chain("not a chain").valid
    assert not verify_signed_relay_chain({}).valid


def test_verify_relay_never_raises():
    print("=== verify_relay: never raises ===")
    assert not verify_relay(None)
    assert not verify_relay("not a relay")


def test_verify_receipt_never_raises():
    print("=== verify_receipt: never raises ===")
    assert not verify_receipt(None)
    assert not verify_receipt("not a receipt")


# =====================================================================
# Structural claims
# =====================================================================

def test_c52_and_c54_untouched():
    """C52 and C54 classes still work unchanged."""
    print("=== C52 and C54 classes unchanged ===")
    from multiverse_c52 import EpidemicUnit
    from multiverse_c54 import VerifyingEpidemicUnit
    # C52 works as before
    u = EpidemicUnit("world:u", "U", contacts=["A"])
    assert hasattr(u, "_contacts")
    assert not hasattr(u, "_unit_kp")
    # C54 works as before
    _, context = _make_attested_and_context()
    v = VerifyingEpidemicUnit(
        "world:v", "V", contacts=["A"],
        trust_context=context)
    assert hasattr(v, "_verified_exposures")
    assert not hasattr(v, "_unit_kp")
    # C56 subclass adds signing without modifying parent
    kp = KeyPair.generate()
    s = SigningVerifyingUnit(
        "world:s", "S", unit_kp=kp, contacts=["A"],
        trust_context=context)
    assert hasattr(s, "_unit_kp")
    assert hasattr(s, "_verified_exposures")


def test_network_and_unit_no_foreign_attrs():
    print("=== Network and unit: no foreign attrs ===")
    _, context = _make_attested_and_context()
    kp = KeyPair.generate()
    unit = SigningVerifyingUnit(
        "world:u", "U", unit_kp=kp,
        trust_context=context)
    for attr in ("_model", "_intent_queue"):       # C41
        assert not hasattr(unit, attr), attr
    for attr in ("_inputs", "_threshold"):         # C42
        assert not hasattr(unit, attr), attr
    for attr in ("_decision_rule", "_members"):    # C44
        assert not hasattr(unit, attr), attr
    for attr in ("_target", "_state"):             # C47
        assert not hasattr(unit, attr), attr
    for attr in ("_current_policy",
                 "_policy_history"):                # C50
        assert not hasattr(unit, attr), attr


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: happy chain, skeptic, diamond ===")
    audit = demo(artifact_dir=str(tmp_path))
    a = audit["scenarios"]["A_happy_chain"]
    assert a["valid"] is True
    assert a["attestation_valid"] is True
    assert a["all_relays_signed"] is True
    assert a["all_receipts_signed"] is True
    assert a["seed_recipient"] == "A"
    assert set(a["reached"]) == {"A", "B", "C", "D"}

    b = audit["scenarios"]["B_skeptic"]
    assert b["valid"] is True  # chain itself is valid
    assert b["seed_recipient"] == "A"
    # B refused verification, so B doesn't spread; only A, B reached
    assert set(b["reached"]) == {"A", "B"} or \
        set(b["reached"]) == {"A"}  # depends on B's verified state

    c = audit["scenarios"]["C_diamond"]
    assert c["valid"] is True
    assert c["seed_recipient"] == "A"
    assert set(c["reached"]) == {"A", "B", "C", "D", "E"}

    assert (tmp_path / "signed_relay_demo.json").exists()


if __name__ == "__main__":
    test_relay_attestation_validates_fields()
    test_receipt_attestation_validates_fields()
    test_relay_signed_by_sender()
    test_relay_wrong_key_rejected()
    test_receipt_signed_by_receiver()
    test_signing_unit_is_a_c54_unit()
    test_receipt_signed_on_act()
    test_receipt_signed_with_refusal()
    test_relay_signed_on_record_delivery()
    test_network_seed_attested_creates_receipt()
    test_network_full_chain_produces_relays_and_receipts()
    test_network_collect_unknown_rumor_returns_none()
    test_reconstruct_hops_matches_relay_receipt()
    test_verify_chain_happy()
    test_verify_chain_skeptic()
    test_verify_chain_forged_relay()
    test_verify_chain_forged_receipt()
    test_verify_chain_attestation_invalid()
    test_verify_chain_no_seed()
    test_chain_json_roundtrip()
    test_verify_never_raises()
    test_verify_relay_never_raises()
    test_verify_receipt_never_raises()
    test_c52_and_c54_untouched()
    test_network_and_unit_no_foreign_attrs()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
