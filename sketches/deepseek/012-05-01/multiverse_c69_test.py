import json
import tempfile
import time
import urllib.request
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import Ack, Refusal
from multiverse_c4 import PoetryWorld
from multiverse_c5 import ChemistryWorld
from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c55 import (
    CURATOR_MESSAGE_TYPES, CuratorMessage, WorldCurator,
    verify_curator_message,
)
from multiverse_c57 import (
    ContractTerms, ContractRegistry, ContractRecord,
    ContractOffer, ContractAcceptance, ContractRejection,
    sign_offer, sign_acceptance, sign_rejection,
    sign_bilateral_revocation,
    ContractNegotiator, verify_contract_offer,
    verify_contract_acceptance,
)
from multiverse_c66 import (
    DeployConfig, deploy_federation,
    _patch_c65_manifest_verification,
)
from multiverse_c68 import (
    CuratorProcess, PeerRegistry, CuratorStore,
)
from multiverse_c69 import (
    CONTRACT_MESSAGE_TYPES,
    ContractAcceptancePolicy,
    AutoAcceptPolicy, RejectAllPolicy, KindFilterPolicy,
    _record_to_dict, _record_from_dict,
    save_contract_registry, load_contract_registry,
    ContractAwareCuratorProcess,
    demo,
    _now,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Message type extension
# =====================================================================

def test_curator_message_types_extended():
    print("=== CURATOR_MESSAGE_TYPES: contract types added ===")
    import multiverse_c55 as c55
    for t in CONTRACT_MESSAGE_TYPES:
        assert t in c55.CURATOR_MESSAGE_TYPES


def test_curator_message_accepts_contract_type():
    print("=== CuratorMessage: accepts contract_offer type ===")
    kp = KeyPair.generate()
    from multiverse_c55 import WorldObservation
    # Construct a message manually with the new type
    payload = {"offer": {}}
    body = canonical_bytes({
        "kind": "curator_message",
        "sender_world_id": "world:p",
        "sender_public_key": kp.public_key_hex(),
        "sender_manifest_hash": "00" * 32,
        "message_type": "contract_offer",
        "payload": payload,
        "timestamp": "t",
    })
    msg = CuratorMessage(
        sender_world_id="world:p",
        sender_public_key=kp.public_key_hex(),
        sender_manifest_hash="00" * 32,
        message_type="contract_offer",
        payload=payload,
        timestamp="t",
        signature=kp.sign(body).hex(),
    )
    assert msg.message_type == "contract_offer"
    assert verify_curator_message(msg, kp.public_key_hex())


# =====================================================================
# Acceptance policies
# =====================================================================

def test_auto_accept_policy():
    print("=== AutoAcceptPolicy: accepts everything ===")
    policy = AutoAcceptPolicy()
    offer = sign_offer(
        "world:a", KeyPair.generate(), "world:b",
        ContractTerms(content={"kind": "x"}))
    accept, reason = policy.should_accept(offer, "world:a")
    assert accept
    assert "auto-accept" in reason


def test_reject_all_policy():
    print("=== RejectAllPolicy: rejects everything ===")
    policy = RejectAllPolicy()
    offer = sign_offer(
        "world:a", KeyPair.generate(), "world:b",
        ContractTerms(content={"kind": "x"}))
    accept, reason = policy.should_accept(offer, "world:a")
    assert not accept
    assert "rejects" in reason


def test_kind_filter_policy():
    print("=== KindFilterPolicy: filters by kind ===")
    policy = KindFilterPolicy(["mutual-recognition"])
    offer_ok = sign_offer(
        "world:a", KeyPair.generate(), "world:b",
        ContractTerms(content={"kind": "mutual-recognition"}))
    offer_bad = sign_offer(
        "world:a", KeyPair.generate(), "world:b",
        ContractTerms(content={"kind": "something-else"}))
    assert policy.should_accept(offer_ok, "world:a")[0]
    assert not policy.should_accept(offer_bad, "world:a")[0]


# =====================================================================
# Registry persistence
# =====================================================================

def test_record_roundtrip():
    print("=== _record_to_dict / _record_from_dict ===")
    kp_a = KeyPair.generate()
    kp_b = KeyPair.generate()
    terms = ContractTerms(content={"kind": "test"})
    offer = sign_offer("world:a", kp_a, "world:b", terms)
    acceptance = sign_acceptance("world:b", kp_b, offer)
    rec = ContractRecord(
        terms_hash=terms.terms_hash(),
        world_a_id="world:a",
        world_b_id="world:b",
        offer=offer,
        acceptance=acceptance,
        established_at="2024-01-01T00:00:00+00:00",
    )
    d = _record_to_dict(rec)
    rec2 = _record_from_dict(d)
    assert rec2.terms_hash == rec.terms_hash
    assert rec2.world_a_id == rec.world_a_id
    assert rec2.world_b_id == rec.world_b_id
    assert rec2.offer is not None
    assert rec2.acceptance is not None
    assert verify_contract_offer(rec2.offer,
                                    kp_a.public_key_hex())


def test_registry_save_load(tmp_path):
    print("=== save_contract_registry / load ===")
    reg = ContractRegistry()
    kp_a = KeyPair.generate()
    kp_b = KeyPair.generate()
    terms = ContractTerms(content={"kind": "test"})
    offer = sign_offer("world:a", kp_a, "world:b", terms)
    reg.register_offer(offer)
    acceptance = sign_acceptance("world:b", kp_b, offer)
    reg.register_acceptance(acceptance)
    p = tmp_path / "reg.json"
    save_contract_registry(reg, p)
    assert p.exists()
    reg2 = load_contract_registry(p)
    rec = reg2.get(terms.terms_hash())
    assert rec is not None
    assert rec.is_established()


def test_registry_load_missing_file(tmp_path):
    print("=== load_contract_registry: missing file → empty ===")
    reg = load_contract_registry(tmp_path / "nope.json")
    assert len(reg.list_all()) == 0


def test_registry_load_malformed(tmp_path):
    print("=== load_contract_registry: malformed → empty ===")
    p = tmp_path / "reg.json"
    p.write_text("not json")
    reg = load_contract_registry(p)
    assert len(reg.list_all()) == 0


# =====================================================================
# Deploy + two contract-aware processes
# =====================================================================

def _deploy_pair(tmp_path):
    _patch_c65_manifest_verification()
    cfg = DeployConfig(
        state_dir=tmp_path / "fed", federation_name="test")
    fed = deploy_federation(cfg)
    poetry_peers = PeerRegistry()
    chem_peers = PeerRegistry()
    poetry_proc = ContractAwareCuratorProcess(
        world=fed.poetry.base,
        world_kp=fed.poetry_kp,
        peers=poetry_peers,
        state_dir=tmp_path / "poetry",
        cycle_interval=0.1,
        contract_policy=AutoAcceptPolicy(),
        identity=create_identity("curator:poetry"),
    )
    chem_proc = ContractAwareCuratorProcess(
        world=fed.chemistry.base,
        world_kp=fed.chemistry_kp,
        peers=chem_peers,
        state_dir=tmp_path / "chemistry",
        cycle_interval=0.1,
        contract_policy=AutoAcceptPolicy(),
        identity=create_identity("curator:chemistry"),
    )
    poetry_proc.start()
    chem_proc.start()
    poetry_peers.add(
        "world:chemistry", chem_proc.url,
        fed.chemistry_kp.public_key_hex())
    chem_peers.add(
        "world:poetry", poetry_proc.url,
        fed.poetry_kp.public_key_hex())
    return fed, poetry_proc, chem_proc


def _tick_until_linked(a, b, max_ticks=20):
    for i in range(max_ticks):
        a.tick()
        b.tick()
        if len(a.links()) > 0 and len(b.links()) > 0:
            return i
    return None


def test_two_processes_link(tmp_path):
    print("=== Two contract-aware processes converge to link ===")
    fed, poetry, chem = _deploy_pair(tmp_path)
    try:
        linked_at = _tick_until_linked(poetry, chem)
        assert linked_at is not None
        assert len(poetry.links()) == 1
        assert len(chem.links()) == 1
    finally:
        poetry.stop()
        chem.stop()
        fed.stop()


def test_propose_contract_auto_accept(tmp_path):
    print("=== Propose → auto-accept → established ===")
    fed, poetry, chem = _deploy_pair(tmp_path)
    try:
        _tick_until_linked(poetry, chem)
        terms = ContractTerms(content={
            "kind": "mutual-recognition",
            "detail": "x",
        })
        ok, reason, terms_hash = poetry.propose_contract(
            "world:chemistry", terms)
        assert ok, reason
        assert terms_hash == terms.terms_hash()
        # Poetry's registry sees the offer (established after
        # acceptance came back during propose_contract)
        poetry_rec = poetry.contract_registry.get(terms_hash)
        assert poetry_rec is not None
        assert poetry_rec.is_established()
        # Chemistry's registry sees the offer and acceptance
        chem_rec = chem.contract_registry.get(terms_hash)
        assert chem_rec is not None
        assert chem_rec.is_established()
    finally:
        poetry.stop()
        chem.stop()
        fed.stop()


def test_propose_contract_reject_policy(tmp_path):
    print("=== Propose → reject policy → rejected ===")
    _patch_c65_manifest_verification()
    cfg = DeployConfig(
        state_dir=tmp_path / "fed", federation_name="test")
    fed = deploy_federation(cfg)
    poetry_peers = PeerRegistry()
    chem_peers = PeerRegistry()
    poetry = ContractAwareCuratorProcess(
        world=fed.poetry.base,
        world_kp=fed.poetry_kp,
        peers=poetry_peers,
        state_dir=tmp_path / "poetry",
        cycle_interval=0.1,
        contract_policy=AutoAcceptPolicy(),
    )
    chem = ContractAwareCuratorProcess(
        world=fed.chemistry.base,
        world_kp=fed.chemistry_kp,
        peers=chem_peers,
        state_dir=tmp_path / "chemistry",
        cycle_interval=0.1,
        contract_policy=RejectAllPolicy(),  # <-- reject
    )
    poetry.start()
    chem.start()
    try:
        poetry_peers.add(
            "world:chemistry", chem.url,
            fed.chemistry_kp.public_key_hex())
        chem_peers.add(
            "world:poetry", poetry.url,
            fed.poetry_kp.public_key_hex())
        _tick_until_linked(poetry, chem)
        terms = ContractTerms(content={"kind": "test"})
        ok, reason, terms_hash = poetry.propose_contract(
            "world:chemistry", terms)
        assert ok, reason
        poetry_rec = poetry.contract_registry.get(terms_hash)
        assert poetry_rec.is_rejected()
        chem_rec = chem.contract_registry.get(terms_hash)
        assert chem_rec.is_rejected()
    finally:
        poetry.stop()
        chem.stop()
        fed.stop()


def test_kind_filter_rejects_wrong_kind(tmp_path):
    print("=== KindFilterPolicy: rejects unknown kind ===")
    _patch_c65_manifest_verification()
    cfg = DeployConfig(
        state_dir=tmp_path / "fed", federation_name="test")
    fed = deploy_federation(cfg)
    poetry_peers = PeerRegistry()
    chem_peers = PeerRegistry()
    poetry = ContractAwareCuratorProcess(
        world=fed.poetry.base,
        world_kp=fed.poetry_kp,
        peers=poetry_peers,
        state_dir=tmp_path / "poetry",
        cycle_interval=0.1,
        contract_policy=AutoAcceptPolicy(),
    )
    chem = ContractAwareCuratorProcess(
        world=fed.chemistry.base,
        world_kp=fed.chemistry_kp,
        peers=chem_peers,
        state_dir=tmp_path / "chemistry",
        cycle_interval=0.1,
        contract_policy=KindFilterPolicy(["mutual-recognition"]),
    )
    poetry.start()
    chem.start()
    try:
        poetry_peers.add(
            "world:chemistry", chem.url,
            fed.chemistry_kp.public_key_hex())
        chem_peers.add(
            "world:poetry", poetry.url,
            fed.poetry_kp.public_key_hex())
        _tick_until_linked(poetry, chem)
        # Bad kind → reject
        bad_terms = ContractTerms(content={"kind": "not-allowed"})
        poetry.propose_contract("world:chemistry", bad_terms)
        assert poetry.contract_registry.get(
            bad_terms.terms_hash()).is_rejected()
        # Good kind → accept
        good_terms = ContractTerms(
            content={"kind": "mutual-recognition"})
        poetry.propose_contract("world:chemistry", good_terms)
        assert poetry.contract_registry.get(
            good_terms.terms_hash()).is_established()
    finally:
        poetry.stop()
        chem.stop()
        fed.stop()


def test_propose_unknown_peer(tmp_path):
    print("=== Propose: unknown peer → False ===")
    fed, poetry, chem = _deploy_pair(tmp_path)
    try:
        ok, reason, _ = poetry.propose_contract(
            "world:unknown",
            ContractTerms(content={"kind": "x"}))
        assert not ok
        assert "not registered" in reason.lower()
    finally:
        poetry.stop()
        chem.stop()
        fed.stop()


# =====================================================================
# Bad input rejection
# =====================================================================

def test_handler_rejects_wrong_peer_key(tmp_path):
    print("=== Handler: offer signed by wrong key → Refusal ===")
    fed, poetry, chem = _deploy_pair(tmp_path)
    try:
        _tick_until_linked(poetry, chem)
        # Craft a forged offer signed by a different key, from
        # chemistry's world_id but signed with an attacker's key
        attacker = KeyPair.generate()
        fake_terms = ContractTerms(content={"kind": "fake"})
        fake_offer = sign_offer(
            "world:chemistry", attacker,
            "world:poetry", fake_terms)
        # Build a message signed by chemistry's real key but with
        # the fake offer embedded — the offer's proposer_public_key
        # won't match chemistry's peer registry key
        msg = chem.curator._sign_message(
            "contract_offer",
            {"offer": fake_offer.to_dict()})
        # Deliver directly to poetry's server
        from multiverse_c68 import CuratorHTTPClient
        client = CuratorHTTPClient(poetry.url)
        ok, reason = client.deliver(msg)
        # The message signature is chemistry's real sig (peer
        # registered), so the message is accepted by the server.
        # But the offer's proposer_public_key is the attacker's
        # key, so _handle_offer refuses.
        assert not ok
        assert "proposer_public_key" in reason.lower() or \
            "signature" in reason.lower()
    finally:
        poetry.stop()
        chem.stop()
        fed.stop()


def test_handler_rejects_wrong_target(tmp_path):
    print("=== Handler: offer to wrong target → Refusal ===")
    fed, poetry, chem = _deploy_pair(tmp_path)
    try:
        _tick_until_linked(poetry, chem)
        # Chemistry signs an offer addressed to a different world
        fake_terms = ContractTerms(content={"kind": "x"})
        wrong_target_offer = sign_offer(
            "world:chemistry", fed.chemistry_kp,
            "world:somewhere-else", fake_terms)
        msg = chem.curator._sign_message(
            "contract_offer",
            {"offer": wrong_target_offer.to_dict()})
        from multiverse_c68 import CuratorHTTPClient
        client = CuratorHTTPClient(poetry.url)
        ok, reason = client.deliver(msg)
        assert not ok
        assert "not " in reason.lower() or "addressed" in reason.lower()
    finally:
        poetry.stop()
        chem.stop()
        fed.stop()


def test_handler_rejects_malformed_payload(tmp_path):
    print("=== Handler: malformed payload → Refusal ===")
    fed, poetry, chem = _deploy_pair(tmp_path)
    try:
        _tick_until_linked(poetry, chem)
        msg = chem.curator._sign_message(
            "contract_offer",
            {"not_offer": True})  # missing "offer"
        from multiverse_c68 import CuratorHTTPClient
        client = CuratorHTTPClient(poetry.url)
        ok, reason = client.deliver(msg)
        assert not ok
        assert "malformed" in reason.lower() or "offer" in reason.lower()
    finally:
        poetry.stop()
        chem.stop()
        fed.stop()


# =====================================================================
# Persistence
# =====================================================================

def test_contract_registry_persists(tmp_path):
    print("=== Contract registry persists to disk ===")
    fed, poetry, chem = _deploy_pair(tmp_path)
    try:
        _tick_until_linked(poetry, chem)
        terms = ContractTerms(content={"kind": "test"})
        ok, _, terms_hash = poetry.propose_contract(
            "world:chemistry", terms)
        assert ok
        # Poetry's registry file exists
        registry_path = poetry._registry_path
        assert registry_path.exists()
        # Load from disk into a fresh registry
        fresh = load_contract_registry(registry_path)
        rec = fresh.get(terms_hash)
        assert rec is not None
        assert rec.is_established()
    finally:
        poetry.stop()
        chem.stop()
        fed.stop()


def test_process_reloads_registry_from_disk(tmp_path):
    print("=== Process reloads registry on construction ===")
    fed, poetry, chem = _deploy_pair(tmp_path)
    try:
        _tick_until_linked(poetry, chem)
        terms = ContractTerms(content={"kind": "test"})
        ok, _, terms_hash = poetry.propose_contract(
            "world:chemistry", terms)
        assert ok
        poetry.stop()
        chem.stop()
        # Reconstruct poetry with the same state_dir but new peers
        poetry_peers2 = PeerRegistry()
        poetry_peers2.add(
            "world:chemistry",
            "http://ghost",  # not needed for reload
            fed.chemistry_kp.public_key_hex())
        poetry_reloaded = ContractAwareCuratorProcess(
            world=fed.poetry.base,
            world_kp=fed.poetry_kp,
            peers=poetry_peers2,
            state_dir=tmp_path / "poetry",  # same as before
            cycle_interval=0.1,
            contract_policy=AutoAcceptPolicy(),
        )
        rec = poetry_reloaded.contract_registry.get(terms_hash)
        assert rec is not None
        assert rec.is_established()
        poetry_reloaded.stop()
    finally:
        try:
            poetry.stop()
        except Exception:
            pass
        try:
            chem.stop()
        except Exception:
            pass
        fed.stop()


# =====================================================================
# Never raises on bad input
# =====================================================================

def test_propose_unknown_peer_does_not_raise(tmp_path):
    print("=== propose_contract: unknown peer, no raise ===")
    fed, poetry, chem = _deploy_pair(tmp_path)
    try:
        ok, reason, terms_hash = poetry.propose_contract(
            "world:nobody",
            ContractTerms(content={"kind": "x"}))
        assert not ok
        assert terms_hash == ""
    finally:
        poetry.stop()
        chem.stop()
        fed.stop()


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: full curator contract lifecycle ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["linked_at"] is not None
    assert audit["propose"]["ok"] is True
    assert audit["poetry"]["established"] is True
    assert audit["chemistry"]["established"] is True
    assert audit["artifacts"]["offer_verifies"] is True
    assert audit["artifacts"]["acceptance_verifies"] is True
    assert audit["reloaded"]["record_found"] is True
    assert audit["reloaded"]["established"] is True
    assert (tmp_path / "curator_contracts" /
            "curator_contracts_demo.json").exists()


if __name__ == "__main__":
    test_curator_message_types_extended()
    test_curator_message_accepts_contract_type()
    test_auto_accept_policy()
    test_reject_all_policy()
    test_kind_filter_policy()
    test_record_roundtrip()
    with tempfile.TemporaryDirectory() as tmp:
        test_registry_save_load(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_registry_load_missing_file(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_registry_load_malformed(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_two_processes_link(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_propose_contract_auto_accept(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_propose_contract_reject_policy(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_kind_filter_rejects_wrong_kind(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_propose_unknown_peer(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_handler_rejects_wrong_peer_key(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_handler_rejects_wrong_target(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_handler_rejects_malformed_payload(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_contract_registry_persists(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_process_reloads_registry_from_disk(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_propose_unknown_peer_does_not_raise(Path(tmp))
