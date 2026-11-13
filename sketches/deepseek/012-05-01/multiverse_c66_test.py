import json
import tempfile
import urllib.request
from pathlib import Path

import pytest

from multiverse_c3 import Ack, Refusal
from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c62 import (
    CommitmentLog, SignedTreeHead,
    verify_commitment_chain, verify_tree_head,
    _hash_payload,
)
from multiverse_c65 import (
    FederationClient, FederationReport, verify_report,
    _verify_anchors_signature,
)
from multiverse_c66 import (
    DeployConfig, DeployedFederation,
    deploy_federation, demo,
    _verify_signed_manifest_dict,
    _patch_c65_manifest_verification,
    _DelegatingSignedWorld,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Config and delegating wrapper
# =====================================================================

def test_config_construction():
    print("=== DeployConfig: construction ===")
    c = DeployConfig(
        state_dir=Path("/tmp/x"),
        federation_name="test")
    assert c.federation_name == "test"
    assert c.poetry_port == 0


def test_delegating_wrapper_delegates_manifest():
    print("=== _DelegatingSignedWorld: manifest delegated ===")
    from multiverse_c4 import PoetryWorld
    base = PoetryWorld("world:p", "P")
    kp = KeyPair.generate()
    w = _DelegatingSignedWorld(base, kp)
    assert w.manifest().entity_id == "world:p"
    # And signed responses still work
    from multiverse_c3 import Petition
    r = w.petition(Petition(
        petitioner_token="t", petitioner_name="T",
        passport_admissions=(), message="hi"))
    assert r is not None


def test_delegating_wrapper_still_signs():
    print("=== _DelegatingSignedWorld: still signs ===")
    from multiverse_c4 import PoetryWorld
    from multiverse_c3 import Petition
    from multiverse_c13 import SignedAdmission
    base = PoetryWorld("world:p", "P")
    kp = KeyPair.generate()
    w = _DelegatingSignedWorld(base, kp)
    r = w.petition(Petition(
        petitioner_token="t", petitioner_name="T",
        passport_admissions=(), message="hi"))
    assert isinstance(r, SignedAdmission)


# =====================================================================
# Manifest verification helper
# =====================================================================

def test_manifest_verifier_happy():
    print("=== _verify_signed_manifest_dict: valid ===")
    from multiverse_c28 import sign_manifest
    kp = KeyPair.generate()
    sm = sign_manifest({
        "entity_id": "world:p", "name": "P",
        "protocol_version": "WCP/0.2",
        "law_url": "u", "act_endpoint": "u", "log_endpoint": "u",
        "sub_registry_endpoint": None,
        "public_key": kp.public_key_hex(),
    }, kp)
    assert _verify_signed_manifest_dict(
        sm.to_dict(), kp.public_key_hex())


def test_manifest_verifier_wrong_key():
    print("=== _verify_signed_manifest_dict: wrong key → False ===")
    from multiverse_c28 import sign_manifest
    kp = KeyPair.generate()
    sm = sign_manifest({
        "entity_id": "world:p", "name": "P",
        "protocol_version": "WCP/0.2",
        "law_url": "u", "act_endpoint": "u", "log_endpoint": "u",
        "sub_registry_endpoint": None,
        "public_key": kp.public_key_hex(),
    }, kp)
    wrong = KeyPair.generate()
    assert not _verify_signed_manifest_dict(
        sm.to_dict(), wrong.public_key_hex())


# =====================================================================
# Deploy happy path
# =====================================================================

def test_deploy_creates_state(tmp_path):
    print("=== Deploy: creates state files ===")
    cfg = DeployConfig(
        state_dir=tmp_path / "fed",
        federation_name="test")
    fed = deploy_federation(cfg)
    try:
        assert fed.anchors_path.exists()
        assert fed.checkpoint_path.exists()
        assert fed.ledger_log_path.exists()
        assert fed.root_key_path.exists()
        # 3 genesis commits
        assert len(fed.genesis_commits) == 3
    finally:
        fed.stop()


def test_deploy_genesis_chain_valid(tmp_path):
    print("=== Deploy: genesis chain valid ===")
    cfg = DeployConfig(
        state_dir=tmp_path / "fed",
        federation_name="test")
    fed = deploy_federation(cfg)
    try:
        v = verify_commitment_chain(fed.ledger.entries())
        assert v.valid
    finally:
        fed.stop()


def test_deploy_checkpoint_verifies(tmp_path):
    print("=== Deploy: checkpoint verifies ===")
    cfg = DeployConfig(
        state_dir=tmp_path / "fed",
        federation_name="test")
    fed = deploy_federation(cfg)
    try:
        assert verify_tree_head(
            fed.checkpoint,
            fed.checkpoint_kp.public_key_hex())
    finally:
        fed.stop()


def test_deploy_anchors_verify(tmp_path):
    print("=== Deploy: anchors verify with root ===")
    cfg = DeployConfig(
        state_dir=tmp_path / "fed",
        federation_name="test")
    fed = deploy_federation(cfg)
    try:
        raw = json.loads(fed.anchors_path.read_text())
        assert _verify_anchors_signature(
            raw, fed.root_kp.public_key_hex())
        # Contains all three worlds
        assert len(raw["worlds"]) == 3
        ids = {w["entity_id"] for w in raw["worlds"]}
        assert ids == {
            "world:poetry", "world:chemistry",
            "multiverse:main"}
    finally:
        fed.stop()


def test_deploy_registry_lists_worlds(tmp_path):
    print("=== Deploy: registry lists worlds ===")
    cfg = DeployConfig(
        state_dir=tmp_path / "fed",
        federation_name="test")
    fed = deploy_federation(cfg)
    try:
        ids = set(fed.registry.entity_ids())
        assert ids == {"world:poetry", "world:chemistry"}
    finally:
        fed.stop()


def test_deploy_worlds_serve_manifests(tmp_path):
    print("=== Deploy: worlds serve manifests over HTTP ===")
    cfg = DeployConfig(
        state_dir=tmp_path / "fed",
        federation_name="test")
    fed = deploy_federation(cfg)
    try:
        for url, expected_id in (
            (fed.poetry_url, "world:poetry"),
            (fed.chemistry_url, "world:chemistry"),
            (fed.registry_url, "multiverse:main"),
        ):
            with urllib.request.urlopen(
                    f"{url}/manifest", timeout=5) as r:
                m = json.loads(r.read().decode())
            assert m["entity_id"] == expected_id
    finally:
        fed.stop()


# =====================================================================
# Deploy failure modes
# =====================================================================

def test_deploy_rejects_nonempty_state(tmp_path):
    print("=== Deploy: rejects non-empty state dir ===")
    cfg = DeployConfig(
        state_dir=tmp_path / "fed",
        federation_name="test")
    # Create a file in state_dir
    (tmp_path / "fed").mkdir()
    (tmp_path / "fed" / "x.txt").write_text("exists")
    with pytest.raises(RuntimeError):
        deploy_federation(cfg)


def test_deploy_rejects_non_config():
    print("=== Deploy: rejects non-config ===")
    with pytest.raises(TypeError):
        deploy_federation("not a config")


# =====================================================================
# Operator commits
# =====================================================================

def test_operator_commit_artifact(tmp_path):
    print("=== Operator: commits an artifact ===")
    cfg = DeployConfig(
        state_dir=tmp_path / "fed",
        federation_name="test")
    fed = deploy_federation(cfg)
    try:
        h = _hash_payload(b"test-artifact")
        rec = fed.commit_artifact(
            h, "test_kind", "world:poetry")
        assert rec.commit_index == 3  # after 3 genesis
        assert fed.ledger.size() == 4
        # Chain still valid
        v = verify_commitment_chain(fed.ledger.entries())
        assert v.valid
    finally:
        fed.stop()


def test_operator_commit_unknown_world(tmp_path):
    print("=== Operator: rejects unknown world ===")
    cfg = DeployConfig(
        state_dir=tmp_path / "fed",
        federation_name="test")
    fed = deploy_federation(cfg)
    try:
        with pytest.raises(ValueError):
            fed.commit_artifact(
                "aa" * 32, "test", "world:unknown")
    finally:
        fed.stop()


def test_operator_new_checkpoint(tmp_path):
    print("=== Operator: signs new checkpoint ===")
    cfg = DeployConfig(
        state_dir=tmp_path / "fed",
        federation_name="test")
    fed = deploy_federation(cfg)
    try:
        h = _hash_payload(b"new-artifact")
        fed.commit_artifact(h, "test", "world:poetry")
        head = fed.sign_new_checkpoint()
        assert head.tree_size == 4
        assert verify_tree_head(
            head, fed.checkpoint_kp.public_key_hex())
        # Old checkpoint still verifies (it was over the old root)
        # but its root doesn't match the new head's root
        assert head.root_hash != fed.genesis_commits[-1].ledger_commit_hash()
    finally:
        fed.stop()


# =====================================================================
# Client end-to-end
# =====================================================================

def test_full_client_end_to_end(tmp_path):
    print("=== End-to-end: client against deployed federation ===")
    _patch_c65_manifest_verification()
    cfg = DeployConfig(
        state_dir=tmp_path / "fed",
        federation_name="test")
    fed = deploy_federation(cfg)
    try:
        client = FederationClient(tmp_path / "client")
        ident = client.create_identity("Alice")
        # Connect
        r = client.connect(
            fed.anchors_url(), fed.root_kp.public_key_hex())
        assert r.ok, r.reason
        # Enter poetry
        r = client.enter_world("world:poetry")
        assert r.ok, r.reason
        assert r.verified
        # Act in poetry
        r = client.submit_act(
            "world:poetry", "poem.turn", {
                "acknowledgment": "(seed)",
                "proposal": "test",
                "invitation": "?",
                "holds_open": True,
            })
        assert r.ok
        assert r.verified
        # Self-verify
        v = client.verify_state()
        assert v.valid
        # Build report and third-party verify
        report = client.build_report()
        report_path = tmp_path / "report.json"
        report.save(report_path)
        loaded = FederationReport.load(report_path)
        third_party = verify_report(
            loaded, fed.root_kp.public_key_hex())
        assert third_party.valid
    finally:
        fed.stop()


def test_client_refuses_bad_anchor(tmp_path):
    print("=== Client: refuses bad anchors ===")
    cfg = DeployConfig(
        state_dir=tmp_path / "fed",
        federation_name="test")
    fed = deploy_federation(cfg)
    try:
        client = FederationClient(tmp_path / "client")
        client.create_identity("Alice")
        # Wrong root key
        wrong = KeyPair.generate()
        r = client.connect(
            fed.anchors_url(), wrong.public_key_hex())
        assert not r.ok
        assert "invalid" in r.reason.lower()
    finally:
        fed.stop()


# =====================================================================
# Clean shutdown
# =====================================================================

def test_stop_shuts_down_servers(tmp_path):
    print("=== Stop: servers no longer respond ===")
    cfg = DeployConfig(
        state_dir=tmp_path / "fed",
        federation_name="test")
    fed = deploy_federation(cfg)
    # Verify they're live first
    with urllib.request.urlopen(
            f"{fed.poetry_url}/manifest", timeout=5) as r:
        assert r.status == 200
    fed.stop()
    # Now they should be gone
    import time as _t
    _t.sleep(0.1)
    with pytest.raises(Exception):
        urllib.request.urlopen(
            f"{fed.poetry_url}/manifest", timeout=1)


# =====================================================================
# Never raises on bad input
# =====================================================================

def test_verify_helpers_never_raise():
    print("=== Verify helpers: never raise ===")
    assert not _verify_signed_manifest_dict(None, "aa" * 32)
    assert not _verify_signed_manifest_dict({}, "aa" * 32)


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: full LFS/0.1 scenario ===")
    audit = demo(artifact_dir=str(tmp_path))
    dc = audit["deploy_checks"]
    assert dc["genesis_chain_valid"] is True
    assert dc["genesis_head_signed"] is True
    assert dc["anchors_signed"] is True
    assert dc["registry_entity_ids"] == [
        "world:chemistry", "world:poetry"]
    assert dc["genesis_commit_count"] == 3
    c = audit["client"]
    assert c["connect_ok"] is True
    assert c["enter_poetry_verified"] is True
    assert c["act_poetry_verified"] is True
    assert c["enter_chemistry_verified"] is True
    assert c["act_chemistry_verified"] is True
    o = audit["operator"]
    assert o["committed"] >= 2
    assert o["new_checkpoint_signed"] is True
    assert o["chain_valid_after"] is True
    assert audit["report"]["self_verify"] is True
    assert audit["report"]["third_party_verify"] is True


if __name__ == "__main__":
    test_config_construction()
    test_delegating_wrapper_delegates_manifest()
    test_delegating_wrapper_still_signs()
    test_manifest_verifier_happy()
    test_manifest_verifier_wrong_key()
    with tempfile.TemporaryDirectory() as tmp:
        test_deploy_creates_state(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_deploy_genesis_chain_valid(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_deploy_checkpoint_verifies(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_deploy_anchors_verify(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_deploy_registry_lists_worlds(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_deploy_worlds_serve_manifests(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_deploy_rejects_nonempty_state(Path(tmp))
    test_deploy_rejects_non_config()
    with tempfile.TemporaryDirectory() as tmp:
        test_operator_commit_artifact(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_operator_commit_unknown_world(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_operator_new_checkpoint(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_full_client_end_to_end(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_client_refuses_bad_anchor(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_stop_shuts_down_servers(Path(tmp))
    test_verify_helpers_never_raise()
