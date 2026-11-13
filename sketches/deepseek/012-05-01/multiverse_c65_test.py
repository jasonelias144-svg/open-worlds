import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c1 import Identity
from multiverse_c3 import Petition, Act, Admission, Ack, Refusal
from multiverse_c4 import PoetryWorld
from multiverse_c5 import ChemistryWorld
from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c15 import PassportV2, PassportEntry
from multiverse_c65 import (
    _keypair_to_hex, _keypair_from_hex,
    ClientIdentity, PinnedAnchors,
    WorldHTTPClient, WorldHTTPError,
    ConnectResult, EnterResult, SubmitResult,
    ClientState,
    FederationReport, ReportVerdict, verify_report,
    FederationClient,
    _verify_anchors_signature,
    main,
    demo,
    _now,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Keypair serialization
# =====================================================================

def test_keypair_roundtrip():
    print("=== Keypair: hex roundtrip ===")
    kp = KeyPair.generate()
    h = _keypair_to_hex(kp)
    kp2 = _keypair_from_hex(h)
    assert kp.public_key_hex() == kp2.public_key_hex()
    # Both sign, both verify with the same public key
    sig = kp.sign(b"test").hex()
    from multiverse_c13 import verify_signature
    assert verify_signature(kp2.public_key_hex(), b"test", sig)


def test_client_identity_roundtrip():
    print("=== ClientIdentity: JSON roundtrip ===")
    from multiverse_c1 import create_identity
    ident = create_identity("Alice")
    kp = KeyPair.generate()
    ci = ClientIdentity(identity=ident, keypair=kp)
    d = ci.to_dict()
    ci2 = ClientIdentity.from_dict(d)
    assert ci2.identity.token == ident.token
    assert ci2.keypair.public_key_hex() == kp.public_key_hex()


# =====================================================================
# Anchors
# =====================================================================

def _make_anchors(root_kp=None, worlds=None):
    if root_kp is None:
        root_kp = KeyPair.generate()
    if worlds is None:
        w1_kp = KeyPair.generate()
        w2_kp = KeyPair.generate()
        worlds = [
            {"entity_id": "world:poetry",
             "manifest_url": "http://a/manifest",
             "curator_public_key": w1_kp.public_key_hex(),
             "curator_world": "curator:poetry"},
            {"entity_id": "world:chemistry",
             "manifest_url": "http://b/manifest",
             "curator_public_key": w2_kp.public_key_hex(),
             "curator_world": "curator:chemistry"},
        ]
    body = {
        "kind": "federation_trust_anchors",
        "version": "LFS/0.1",
        "published_at": _now(),
        "worlds": worlds,
    }
    sig = root_kp.sign(canonical_bytes(body)).hex()
    raw = dict(body)
    raw["signature"] = sig
    return raw, root_kp, worlds


def test_anchors_verify():
    print("=== _verify_anchors_signature: valid ===")
    raw, root_kp, _ = _make_anchors()
    assert _verify_anchors_signature(
        raw, root_kp.public_key_hex())


def test_anchors_wrong_key():
    print("=== _verify_anchors_signature: wrong key → False ===")
    raw, _, _ = _make_anchors()
    wrong_kp = KeyPair.generate()
    assert not _verify_anchors_signature(
        raw, wrong_kp.public_key_hex())


def test_anchors_tampered():
    print("=== _verify_anchors_signature: tampered → False ===")
    raw, root_kp, _ = _make_anchors()
    tampered = dict(raw)
    tampered["worlds"] = list(tampered["worlds"])
    tampered["worlds"][0] = dict(tampered["worlds"][0])
    tampered["worlds"][0]["curator_public_key"] = "ff" * 32
    assert not _verify_anchors_signature(
        tampered, root_kp.public_key_hex())


def test_pinned_anchors_lookup():
    print("=== PinnedAnchors: lookup helpers ===")
    raw, root_kp, _ = _make_anchors()
    anchors = PinnedAnchors(
        anchor_url="http://x", root_fingerprint=root_kp.public_key_hex(),
        raw=raw, fetched_at=_now())
    assert anchors.world_by_id("world:poetry") is not None
    assert anchors.world_by_id("world:nope") is None
    assert anchors.world_public_key("world:poetry") is not None
    assert anchors.world_manifest_url("world:poetry") == \
        "http://a/manifest"
    assert anchors.world_base_url("world:poetry") == "http://a"
    assert set(anchors.world_ids()) == {
        "world:poetry", "world:chemistry"}


def test_anchors_json_roundtrip():
    print("=== PinnedAnchors: JSON roundtrip ===")
    raw, root_kp, _ = _make_anchors()
    a = PinnedAnchors(
        anchor_url="http://x",
        root_fingerprint=root_kp.public_key_hex(),
        raw=raw, fetched_at="t")
    a2 = PinnedAnchors.from_dict(a.to_dict())
    assert a2.root_fingerprint == a.root_fingerprint
    assert a2.world_ids() == a.world_ids()


# =====================================================================
# ClientState
# =====================================================================

def test_state_lifecycle(tmp_path):
    print("=== ClientState: save/load ===")
    state = ClientState(tmp_path)
    assert not state.exists()
    state.ensure_dir()
    from multiverse_c1 import create_identity
    ident = create_identity("Alice")
    kp = KeyPair.generate()
    state.identity = ClientIdentity(identity=ident, keypair=kp)
    state.passport = PassportV2.new(ident)
    state.save_identity()
    state.save_passport()
    assert state.exists()
    # Reload in fresh state
    state2 = ClientState(tmp_path)
    loaded = state2.load()
    assert loaded
    assert state2.identity.identity.token == ident.token


def test_state_append_log(tmp_path):
    print("=== ClientState: append_log persists ===")
    state = ClientState(tmp_path)
    state.ensure_dir()
    state.append_log("test", {"a": 1})
    state.append_log("test", {"a": 2})
    entries = state.get_log()
    assert len(entries) == 2
    assert entries[0]["kind"] == "test"
    assert entries[1]["data"]["a"] == 2


def test_state_load_nonexistent(tmp_path):
    print("=== ClientState: load nonexistent → False ===")
    state = ClientState(tmp_path / "nope")
    assert not state.load()


# =====================================================================
# FederationClient: identity
# =====================================================================

def test_client_create_identity(tmp_path):
    print("=== FederationClient: create_identity persists ===")
    client = FederationClient(tmp_path)
    ident = client.create_identity("Alice")
    assert ident.identity.name == "Alice"
    # Reload
    client2 = FederationClient(tmp_path)
    assert client2.load_state()
    assert client2.state.identity.identity.name == "Alice"


# =====================================================================
# FederationClient: connect (requires HTTP; test with file:// in demo)
# =====================================================================

# Covered by demo


# =====================================================================
# FederationClient: verify_state without anchors
# =====================================================================

def test_verify_without_anchors(tmp_path):
    print("=== verify_state: no anchors → invalid ===")
    client = FederationClient(tmp_path)
    client.create_identity("Alice")
    v = client.verify_state()
    assert not v.valid


def test_enter_without_identity(tmp_path):
    print("=== enter_world: no identity → invalid ===")
    client = FederationClient(tmp_path)
    result = client.enter_world("world:poetry")
    assert not result.ok
    assert "identity" in result.reason.lower()


# =====================================================================
# Report verification (self-contained)
# =====================================================================

def _make_report(
    client_token="tok",
    client_name="Alice",
    client_kp=None,
    admissions=None,
    acks=None,
    contracts=None,
    root_kp=None,
    worlds=None,
):
    if client_kp is None:
        client_kp = KeyPair.generate()
    if root_kp is None:
        root_kp = KeyPair.generate()
    raw, root_kp, worlds = _make_anchors(
        root_kp=root_kp, worlds=worlds)
    report = FederationReport(
        identity_token=client_token,
        identity_name=client_name,
        identity_public_key=client_kp.public_key_hex(),
        anchors=raw,
        admissions=admissions or [],
        acks=acks or [],
        refusals=[],
        contracts=contracts or [],
        generated_at=_now(),
        client_signature="",
    )
    sig = client_kp.sign(report.canonical_payload()).hex()
    report.client_signature = sig
    return report, root_kp, client_kp, worlds


def test_report_verify_empty_happy():
    print("=== Report: empty, valid ===")
    report, root_kp, _, _ = _make_report()
    v = verify_report(report, root_kp.public_key_hex())
    assert v.valid
    assert v.checks["anchors_signature"]
    assert v.checks["client_signature"]
    assert v.checks["admissions"]  # trivially true (no entries)
    assert v.checks["acks"]
    assert v.checks["contracts"]


def test_report_verify_wrong_root_key():
    print("=== Report: wrong root key → invalid ===")
    report, _, _, _ = _make_report()
    wrong = KeyPair.generate()
    v = verify_report(report, wrong.public_key_hex())
    assert not v.valid
    assert not v.checks["anchors_signature"]


def test_report_verify_tampered_client_signature():
    print("=== Report: tampered client sig → invalid ===")
    report, root_kp, _, _ = _make_report()
    tampered = FederationReport.from_dict(report.to_dict())
    tampered.client_signature = "00" * 64
    v = verify_report(tampered, root_kp.public_key_hex())
    assert not v.valid
    assert not v.checks["client_signature"]


def test_report_verify_with_signed_admission():
    print("=== Report: with signed admission, valid ===")
    world_kp = KeyPair.generate()
    world_kp_hex = world_kp.public_key_hex()
    worlds = [
        {"entity_id": "world:p",
         "manifest_url": "http://p/manifest",
         "curator_public_key": world_kp_hex,
         "curator_world": "curator:p"},
        {"entity_id": "world:c",
         "manifest_url": "http://c/manifest",
         "curator_public_key": "00" * 32,
         "curator_world": "curator:c"},
    ]
    client_kp = KeyPair.generate()
    client_token = "tok"
    adm_payload = canonical_bytes({
        "kind": "admission",
        "entity_id": "world:p",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "subject_token": client_token,
    })
    adm = {
        "kind": "admission",
        "entity_id": "world:p",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "subject_token": client_token,
        "signature": world_kp.sign(adm_payload).hex(),
    }
    report, root_kp, _, _ = _make_report(
        client_token=client_token, client_kp=client_kp,
        admissions=[adm], worlds=worlds)
    v = verify_report(report, root_kp.public_key_hex())
    assert v.valid
    assert v.checks["admissions"]


def test_report_verify_wrong_subject_token():
    print("=== Report: admission subject != client token → "
          "invalid ===")
    world_kp = KeyPair.generate()
    client_kp = KeyPair.generate()
    client_token = "tok"
    adm_payload = canonical_bytes({
        "kind": "admission",
        "entity_id": "world:p",
        "timestamp": "t",
        "subject_token": "different-token",
    })
    adm = {
        "kind": "admission",
        "entity_id": "world:p",
        "timestamp": "t",
        "subject_token": "different-token",
        "signature": world_kp.sign(adm_payload).hex(),
    }
    worlds = [
        {"entity_id": "world:p",
         "manifest_url": "http://p/manifest",
         "curator_public_key": world_kp.public_key_hex(),
         "curator_world": "curator:p"},
        {"entity_id": "world:c",
         "manifest_url": "http://c/manifest",
         "curator_public_key": "00" * 32,
         "curator_world": "curator:c"},
    ]
    report, root_kp, _, _ = _make_report(
        client_token=client_token, client_kp=client_kp,
        admissions=[adm], worlds=worlds)
    v = verify_report(report, root_kp.public_key_hex())
    assert not v.valid
    assert not v.checks["admissions"]


# =====================================================================
# Never raises
# =====================================================================

def test_verify_report_never_raises():
    print("=== verify_report: never raises ===")
    assert not verify_report(None, "aa" * 32).valid
    assert not verify_report("not a report", "aa" * 32).valid


# =====================================================================
# CLI
# =====================================================================

def test_cli_init(tmp_path, capsys):
    print("=== CLI: init creates identity ===")
    state_dir = tmp_path / "state"
    rc = main(["--state-dir", str(state_dir), "init", "Alice"])
    out = capsys.readouterr()
    assert rc == 0
    assert "Created identity" in out.out
    assert (state_dir / "identity.json").exists()


def test_cli_status_after_init(tmp_path, capsys):
    print("=== CLI: status shows identity ===")
    state_dir = tmp_path / "state"
    main(["--state-dir", str(state_dir), "init", "Alice"])
    rc = main(["--state-dir", str(state_dir), "status"])
    out = capsys.readouterr()
    assert rc == 0
    assert "Alice" in out.out


def test_cli_status_no_identity(tmp_path, capsys):
    print("=== CLI: status without identity → error ===")
    state_dir = tmp_path / "state"
    rc = main(["--state-dir", str(state_dir), "status"])
    out = capsys.readouterr()
    assert rc == 1
    assert "No identity" in out.err


def test_cli_init_twice_fails(tmp_path, capsys):
    print("=== CLI: init twice → error ===")
    state_dir = tmp_path / "state"
    rc1 = main(["--state-dir", str(state_dir), "init", "Alice"])
    rc2 = main(["--state-dir", str(state_dir), "init", "Bob"])
    assert rc1 == 0
    assert rc2 == 1


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: full client flow against live worlds ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["connect_ok"] is True
    assert audit["enter_poetry"]["ok"] is True
    assert audit["enter_poetry"]["verified"] is True
    assert audit["act_poetry"]["ok"] is True
    assert audit["act_poetry"]["verified"] is True
    assert audit["enter_chemistry"]["ok"] is True
    assert audit["enter_chemistry"]["verified"] is True
    assert audit["act_chemistry"]["ok"] is True
    assert audit["act_chemistry"]["verified"] is True
    # Citing without a real contract should fail
    assert audit["cite_fake"]["ok"] is False
    # Both self-verification and third-party verification pass
    assert audit["self_verify_valid"] is True
    assert audit["third_party_verify_valid"] is True
    assert audit["report_admissions"] >= 2
    assert audit["report_acks"] >= 2
    assert (tmp_path / "reference_client_demo.json").exists()
    assert (tmp_path / "alice_report.json").exists()


if __name__ == "__main__":
    test_keypair_roundtrip()
    test_client_identity_roundtrip()
    test_anchors_verify()
    test_anchors_wrong_key()
    test_anchors_tampered()
    test_pinned_anchors_lookup()
    test_anchors_json_roundtrip()
    with tempfile.TemporaryDirectory() as tmp:
        test_state_lifecycle(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_state_append_log(Path(tmp))
    test_state_load_nonexistent(tmp_path=None) if False else None
    # (each tmp test needs its own dir; use pytest for the rest)
    print("\nUse pytest for the full suite.")
