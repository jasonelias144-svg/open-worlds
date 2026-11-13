import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import Ack, Refusal
from multiverse_c4 import PoetryWorld
from multiverse_c5 import ChemistryWorld
from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c55 import CURATOR_MESSAGE_TYPES, _now
from multiverse_c57 import (
    ContractTerms, ContractRegistry,
    sign_offer, sign_acceptance,
    sign_bilateral_revocation,
    ContractRecord,
    verify_bilateral_revocation,
)
from multiverse_c66 import (
    DeployConfig, deploy_federation,
    _patch_c65_manifest_verification,
)
from multiverse_c68 import PeerRegistry
from multiverse_c69 import AutoAcceptPolicy, RejectAllPolicy
from multiverse_c70 import (
    REVOCATION_MESSAGE_TYPES,
    RevocationIntentPayload,
    revocation_canonical_payload,
    RevocableCuratorProcess,
    demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Message type extension
# =====================================================================

def test_revocation_message_types_extended():
    print("=== CURATOR_MESSAGE_TYPES: revocation types added ===")
    import multiverse_c55 as c55
    for t in REVOCATION_MESSAGE_TYPES:
        assert t in c55.CURATOR_MESSAGE_TYPES


# =====================================================================
# RevocationIntentPayload
# =====================================================================

def test_intent_payload_validates():
    print("=== RevocationIntentPayload: validates fields ===")
    with pytest.raises(ValueError):
        RevocationIntentPayload(
            contract_id="short", reason="",
            timestamp="t", signer_role="a",
            signature="s")
    with pytest.raises(ValueError):
        RevocationIntentPayload(
            contract_id="aa" * 32, reason="",
            timestamp="t", signer_role="x",  # invalid role
            signature="s")
    with pytest.raises(ValueError):
        RevocationIntentPayload(
            contract_id="aa" * 32, reason="",
            timestamp="", signer_role="a",
            signature="s")


def test_intent_payload_json_roundtrip():
    print("=== RevocationIntentPayload: JSON roundtrip ===")
    p = RevocationIntentPayload(
        contract_id="aa" * 32, reason="r",
        timestamp="t", signer_role="a",
        signature="sig")
    p2 = RevocationIntentPayload.from_dict(p.to_dict())
    assert p2 == p


# =====================================================================
# Canonical payload matches C57
# =====================================================================

def test_canonical_payload_matches_c57():
    print("=== revocation_canonical_payload == C57's ===")
    from multiverse_c57 import BilateralRevocation
    kp_a = KeyPair.generate()
    kp_b = KeyPair.generate()
    rev = sign_bilateral_revocation(
        contract_id="aa" * 32,
        world_a_id="world:a", world_a_kp=kp_a,
        world_b_id="world:b", world_b_kp=kp_b,
        reason="test",
        timestamp="2024-01-01T00:00:00+00:00")
    # Reconstruct the same payload via our helper
    ours = revocation_canonical_payload(
        contract_id=rev.contract_id,
        world_a_id=rev.world_a_id,
        world_a_public_key=rev.world_a_public_key,
        world_b_id=rev.world_b_id,
        world_b_public_key=rev.world_b_public_key,
        reason=rev.reason,
        timestamp=rev.timestamp)
    assert ours == rev.canonical_payload()


# =====================================================================
# Deploy + two processes
# =====================================================================

def _deploy_pair(tmp_path):
    _patch_c65_manifest_verification()
    cfg = DeployConfig(
        state_dir=tmp_path / "fed", federation_name="test")
    fed = deploy_federation(cfg)
    poetry_peers = PeerRegistry()
    chem_peers = PeerRegistry()
    poetry = RevocableCuratorProcess(
        world=fed.poetry.base,
        world_kp=fed.poetry_kp,
        peers=poetry_peers,
        state_dir=tmp_path / "poetry",
        cycle_interval=0.1,
        contract_policy=AutoAcceptPolicy(),
        identity=create_identity("curator:poetry"),
    )
    chem = RevocableCuratorProcess(
        world=fed.chemistry.base,
        world_kp=fed.chemistry_kp,
        peers=chem_peers,
        state_dir=tmp_path / "chem",
        cycle_interval=0.1,
        contract_policy=AutoAcceptPolicy(),
        identity=create_identity("curator:chemistry"),
    )
    poetry.start()
    chem.start()
    poetry_peers.add(
        "world:chemistry", chem.url,
        fed.chemistry_kp.public_key_hex())
    chem_peers.add(
        "world:poetry", poetry.url,
        fed.poetry_kp.public_key_hex())
    return fed, poetry, chem


def _tick_until_linked(a, b, max_ticks=20):
    for i in range(max_ticks):
        a.tick()
        b.tick()
        if len(a.links()) > 0 and len(b.links()) > 0:
            return i
    return None


def _establish_contract(poetry, chem, kind="test"):
    terms = ContractTerms(content={"kind": kind})
    ok, _, terms_hash = poetry.propose_contract(
        "world:chemistry", terms)
    assert ok
    return terms_hash


# =====================================================================
# Happy path — A initiates
# =====================================================================

def test_a_initiated_revocation(tmp_path):
    print("=== A initiates revocation ===")
    fed, poetry, chem = _deploy_pair(tmp_path)
    try:
        _tick_until_linked(poetry, chem)
        terms_hash = _establish_contract(poetry, chem)
        assert poetry.contract_registry.is_active(terms_hash)
        assert chem.contract_registry.is_active(terms_hash)
        # Poetry initiates
        ok, reason = poetry.request_revocation(
            "world:chemistry", terms_hash,
            reason="mutual agreement")
        assert ok, reason
        # Both registries show revoked
        p_rec = poetry.contract_registry.get(terms_hash)
        c_rec = chem.contract_registry.get(terms_hash)
        assert p_rec.is_revoked()
        assert c_rec.is_revoked()
        assert not poetry.contract_registry.is_active(terms_hash)
        assert not chem.contract_registry.is_active(terms_hash)
    finally:
        poetry.stop()
        chem.stop()
        fed.stop()


def test_b_initiated_revocation(tmp_path):
    print("=== B initiates revocation (reverse roles) ===")
    fed, poetry, chem = _deploy_pair(tmp_path)
    try:
        _tick_until_linked(poetry, chem)
        terms_hash = _establish_contract(poetry, chem)
        # Chemistry initiates
        ok, reason = chem.request_revocation(
            "world:poetry", terms_hash,
            reason="chem terminates")
        assert ok, reason
        p_rec = poetry.contract_registry.get(terms_hash)
        c_rec = chem.contract_registry.get(terms_hash)
        assert p_rec.is_revoked()
        assert c_rec.is_revoked()
    finally:
        poetry.stop()
        chem.stop()
        fed.stop()


def test_revocation_canonical_payload_is_shared(tmp_path):
    print("=== Revocation: both parties sign the same payload ===")
    fed, poetry, chem = _deploy_pair(tmp_path)
    try:
        _tick_until_linked(poetry, chem)
        terms_hash = _establish_contract(poetry, chem)
        poetry.request_revocation(
            "world:chemistry", terms_hash, reason="test")
        rec = poetry.contract_registry.get(terms_hash)
        rev = rec.revocation
        # Both sigs verify against the same canonical payload
        canonical = rev.canonical_payload()
        from multiverse_c13 import verify_signature
        ok_a = verify_signature(
            rev.world_a_public_key, canonical,
            rev.signature_a)
        ok_b = verify_signature(
            rev.world_b_public_key, canonical,
            rev.signature_b)
        assert ok_a
        assert ok_b
    finally:
        poetry.stop()
        chem.stop()
        fed.stop()


# =====================================================================
# Refusals
# =====================================================================

def test_revocation_unknown_peer(tmp_path):
    print("=== request_revocation: unknown peer → False ===")
    fed, poetry, chem = _deploy_pair(tmp_path)
    try:
        _tick_until_linked(poetry, chem)
        terms_hash = _establish_contract(poetry, chem)
        ok, reason = poetry.request_revocation(
            "world:unknown", terms_hash)
        assert not ok
        assert "not registered" in reason.lower()
    finally:
        poetry.stop()
        chem.stop()
        fed.stop()


def test_revocation_unknown_contract(tmp_path):
    print("=== request_revocation: unknown contract → False ===")
    fed, poetry, chem = _deploy_pair(tmp_path)
    try:
        _tick_until_linked(poetry, chem)
        ok, reason = poetry.request_revocation(
            "world:chemistry", "00" * 32)
        assert not ok
        assert "not in this registry" in reason.lower()
    finally:
        poetry.stop()
        chem.stop()
        fed.stop()


def test_revocation_pending_contract_refused(tmp_path):
    print("=== request_revocation: pending contract → False ===")
    fed, poetry, chem = _deploy_pair(tmp_path)
    try:
        _tick_until_linked(poetry, chem)
        # Establish with RejectAllPolicy in chemistry so we
        # can create a rejected contract
        # (Recreate chem with reject policy)
        chem.stop()
        chem_peers2 = PeerRegistry()
        chem_peers2.add(
            "world:poetry", poetry.url,
            fed.poetry_kp.public_key_hex())
        chem2 = RevocableCuratorProcess(
            world=fed.chemistry.base,
            world_kp=fed.chemistry_kp,
            peers=chem_peers2,
            state_dir=tmp_path / "chem_reject",
            cycle_interval=0.1,
            contract_policy=RejectAllPolicy(),
        )
        chem2.start()
        try:
            # Replace peer URL in poetry's peers
            poetry.peers.remove("world:chemistry")
            poetry.peers.add(
                "world:chemistry", chem2.url,
                fed.chemistry_kp.public_key_hex())
            for _ in range(20):
                poetry.tick()
                chem2.tick()
                if (len(poetry.links()) > 0
                        and len(chem2.links()) > 0):
                    break
            # Establish → chemistry rejects
            terms = ContractTerms(content={"kind": "test"})
            poetry.propose_contract("world:chemistry", terms)
            rec = poetry.contract_registry.get(
                terms.terms_hash())
            assert rec.is_rejected()
            # Try to revoke — should fail
            ok, reason = poetry.request_revocation(
                "world:chemistry", terms.terms_hash())
            assert not ok
            assert "established" in reason.lower()
        finally:
            chem2.stop()
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
# Idempotency
# =====================================================================

def test_revoke_already_revoked_contract(tmp_path):
    print("=== Revoke already-revoked: idempotent at handler ===")
    fed, poetry, chem = _deploy_pair(tmp_path)
    try:
        _tick_until_linked(poetry, chem)
        terms_hash = _establish_contract(poetry, chem)
        # First revocation
        ok1, _ = poetry.request_revocation(
            "world:chemistry", terms_hash)
        assert ok1
        # Second attempt — should fail because request_revocation
        # checks "is_established" first
        ok2, reason2 = poetry.request_revocation(
            "world:chemistry", terms_hash)
        assert not ok2
        # The handler is also idempotent: re-sending the intent
        # would return Ack without re-signing
    finally:
        poetry.stop()
        chem.stop()
        fed.stop()


# =====================================================================
# Persistence
# =====================================================================

def test_revocation_persists(tmp_path):
    print("=== Revocation persists to disk ===")
    fed, poetry, chem = _deploy_pair(tmp_path)
    try:
        _tick_until_linked(poetry, chem)
        terms_hash = _establish_contract(poetry, chem)
        poetry.request_revocation(
            "world:chemistry", terms_hash)
        # Registry file exists and contains the revocation
        path = poetry._registry_path
        assert path.exists()
        from multiverse_c69 import load_contract_registry
        fresh = load_contract_registry(path)
        rec = fresh.get(terms_hash)
        assert rec is not None
        assert rec.is_revoked()
    finally:
        poetry.stop()
        chem.stop()
        fed.stop()


def test_revocation_reloads_in_fresh_process(tmp_path):
    print("=== Fresh process loads revocation from disk ===")
    fed, poetry, chem = _deploy_pair(tmp_path)
    try:
        _tick_until_linked(poetry, chem)
        terms_hash = _establish_contract(poetry, chem)
        poetry.request_revocation(
            "world:chemistry", terms_hash)
        poetry.stop()
        chem.stop()
        # Reconstruct poetry from same state_dir
        peers2 = PeerRegistry()
        peers2.add(
            "world:chemistry", "http://ghost",
            fed.chemistry_kp.public_key_hex())
        poetry2 = RevocableCuratorProcess(
            world=fed.poetry.base,
            world_kp=fed.poetry_kp,
            peers=peers2,
            state_dir=tmp_path / "poetry",  # same
            cycle_interval=0.1,
            contract_policy=AutoAcceptPolicy(),
        )
        rec = poetry2.contract_registry.get(terms_hash)
        assert rec is not None
        assert rec.is_revoked()
        poetry2.stop()
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
# Never raises
# =====================================================================

def test_request_revocation_never_raises(tmp_path):
    print("=== request_revocation: never raises ===")
    fed, poetry, chem = _deploy_pair(tmp_path)
    try:
        _tick_until_linked(poetry, chem)
        # Try with garbage inputs
        ok, reason = poetry.request_revocation("", "")
        assert not ok
        ok, reason = poetry.request_revocation(
            "world:chemistry", "not-hex")
        assert not ok
    finally:
        poetry.stop()
        chem.stop()
        fed.stop()


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: full revocation lifecycle ===")
    audit = demo(artifact_dir=str(tmp_path))
    a = audit["scenario_a"]
    assert a["established_before"] is True
    assert a["revocation_ok"] is True
    assert a["both_revoked"] is True
    assert a["neither_active"] is True
    r = audit["reloaded"]
    assert r["record_found"] is True
    assert r["revoked"] is True
    b = audit["scenario_b"]
    assert b["revocation_ok"] is True
    assert b["both_revoked"] is True


if __name__ == "__main__":
    test_revocation_message_types_extended()
    test_intent_payload_validates()
    test_intent_payload_json_roundtrip()
    test_canonical_payload_matches_c57()
    with tempfile.TemporaryDirectory() as tmp:
        test_a_initiated_revocation(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_b_initiated_revocation(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_revocation_canonical_payload_is_shared(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_revocation_unknown_peer(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_revocation_unknown_contract(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_revoke_already_revoked_contract(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_revocation_persists(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_revocation_reloads_in_fresh_process(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_request_revocation_never_raises(Path(tmp))
