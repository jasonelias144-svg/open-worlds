import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import Ack, Refusal
from multiverse_c4 import PoetryWorld
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c55 import CuratorMessage, _now
from multiverse_c57 import ContractTerms
from multiverse_c65 import _verify_anchors_signature
from multiverse_c68 import PeerRegistry
from multiverse_c69 import AutoAcceptPolicy
from multiverse_c72 import (
    FederationRecognition,
    sign_federation_recognition,
    verify_federation_recognition,
    RecognizedPeer,
    build_recognized_peer,
    verify_recognized_peer,
    verify_cross_federation_message,
    XfedCuratorServer,
    RecognizedPeerProcess,
    demo,
    _wrap_cross_federation_message,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _make_anchors(
    federation_name="Test",
    world_id="world:p",
    world_url="http://127.0.0.1:9999",
    curator_public_key=None,
    root_kp=None,
):
    if curator_public_key is None:
        curator_public_key = (
            KeyPair.generate().public_key_hex())
    if root_kp is None:
        root_kp = KeyPair.generate()
    body = {
        "kind": "federation_trust_anchors",
        "version": "LFS/0.1",
        "federation_name": federation_name,
        "published_at": _now(),
        "worlds": [{
            "entity_id": world_id,
            "manifest_url": f"{world_url}/manifest",
            "curator_public_key": curator_public_key,
            "curator_world": f"curator:{world_id}",
        }],
    }
    sig = root_kp.sign(canonical_bytes(body)).hex()
    return dict(body, signature=sig), root_kp, curator_public_key


def _make_message(sender_world_id, sender_kp):
    """A minimal signed CuratorMessage (status_report)."""
    body = canonical_bytes({
        "kind": "curator_message",
        "sender_world_id": sender_world_id,
        "sender_public_key": sender_kp.public_key_hex(),
        "sender_manifest_hash": "00" * 32,
        "message_type": "status_report",
        "payload": {"info": "test"},
        "timestamp": _now(),
    })
    return CuratorMessage(
        sender_world_id=sender_world_id,
        sender_public_key=sender_kp.public_key_hex(),
        sender_manifest_hash="00" * 32,
        message_type="status_report",
        payload={"info": "test"},
        timestamp=_now(),
        signature=sender_kp.sign(body).hex(),
    )


# =====================================================================
# Recognition sign/verify
# =====================================================================

def test_recognition_sign_verify():
    print("=== FederationRecognition: sign and verify ===")
    a_root = KeyPair.generate()
    z_root = KeyPair.generate()
    rec = sign_federation_recognition(
        recognizer_id="A", recognizer_root_kp=a_root,
        recognized_id="Z",
        recognized_root_public_key=(
            z_root.public_key_hex()),
        scope=("contracts",),
    )
    assert rec.recognizer_id == "A"
    assert rec.recognized_id == "Z"
    assert rec.scope == ("contracts",)
    assert verify_federation_recognition(
        rec, a_root.public_key_hex())


def test_recognition_wrong_root_key():
    print("=== Recognition: wrong root key → False ===")
    a_root = KeyPair.generate()
    z_root = KeyPair.generate()
    rec = sign_federation_recognition(
        "A", a_root, "Z", z_root.public_key_hex(),
        scope=("contracts",))
    wrong = KeyPair.generate()
    assert not verify_federation_recognition(
        rec, wrong.public_key_hex())


def test_recognition_tampered():
    print("=== Recognition: tampered → False ===")
    a_root = KeyPair.generate()
    z_root = KeyPair.generate()
    rec = sign_federation_recognition(
        "A", a_root, "Z", z_root.public_key_hex(),
        scope=("contracts",))
    tampered = FederationRecognition(
        recognizer_id=rec.recognizer_id,
        recognizer_root_public_key=(
            rec.recognizer_root_public_key),
        recognized_id=rec.recognized_id,
        recognized_root_public_key=(
            rec.recognized_root_public_key),
        scope=("artifacts",),  # was ("contracts",)
        timestamp=rec.timestamp,
        signature=rec.signature,
    )
    assert not verify_federation_recognition(
        tampered, a_root.public_key_hex())


def test_recognition_rejects_bad_scope():
    print("=== Recognition: rejects empty scope ===")
    a_root = KeyPair.generate()
    z_root = KeyPair.generate()
    with pytest.raises(ValueError):
        FederationRecognition(
            recognizer_id="A",
            recognizer_root_public_key=(
                a_root.public_key_hex()),
            recognized_id="Z",
            recognized_root_public_key=(
                z_root.public_key_hex()),
            scope=(),  # empty
            timestamp="t",
            signature="s")


# =====================================================================
# RecognizedPeer build/verify
# =====================================================================

def test_build_recognized_peer_happy():
    print("=== build_recognized_peer: happy path ===")
    a_root = KeyPair.generate()
    z_root = KeyPair.generate()
    z_curator_key = KeyPair.generate().public_key_hex()
    z_anchors, _, _ = _make_anchors(
        federation_name="Z",
        world_id="world:poetry-z",
        world_url="http://example-z",
        curator_public_key=z_curator_key,
        root_kp=z_root)
    rec = sign_federation_recognition(
        "A", a_root, "Z", z_root.public_key_hex(),
        scope=("contracts",))
    peer = build_recognized_peer(
        rec, z_anchors, "world:poetry-z",
        a_root.public_key_hex())
    assert peer.world_id == "world:poetry-z"
    assert peer.curator_url == "http://example-z"
    assert peer.curator_public_key == z_curator_key


def test_build_recognized_peer_missing_world():
    print("=== build_recognized_peer: missing world → ValueError ===")
    a_root = KeyPair.generate()
    z_root = KeyPair.generate()
    z_anchors, _, _ = _make_anchors(
        world_id="world:poetry-z",
        world_url="http://example-z",
        root_kp=z_root)
    rec = sign_federation_recognition(
        "A", a_root, "Z", z_root.public_key_hex(),
        scope=("contracts",))
    with pytest.raises(ValueError):
        build_recognized_peer(
            rec, z_anchors, "world:nonexistent",
            a_root.public_key_hex())


def test_build_recognized_peer_bad_anchors():
    print("=== build_recognized_peer: bad anchors → ValueError ===")
    a_root = KeyPair.generate()
    z_root = KeyPair.generate()
    wrong_root = KeyPair.generate()
    z_anchors, _, _ = _make_anchors(
        world_id="world:poetry-z",
        root_kp=wrong_root)  # signed by wrong key
    rec = sign_federation_recognition(
        "A", a_root, "Z", z_root.public_key_hex(),
        scope=("contracts",))
    with pytest.raises(ValueError):
        build_recognized_peer(
            rec, z_anchors, "world:poetry-z",
            a_root.public_key_hex())


def test_verify_recognized_peer_happy():
    print("=== verify_recognized_peer: happy path ===")
    a_root = KeyPair.generate()
    z_root = KeyPair.generate()
    z_anchors, _, _ = _make_anchors(
        world_id="world:poetry-z",
        world_url="http://example-z",
        root_kp=z_root)
    rec = sign_federation_recognition(
        "A", a_root, "Z", z_root.public_key_hex(),
        scope=("contracts",))
    peer = build_recognized_peer(
        rec, z_anchors, "world:poetry-z",
        a_root.public_key_hex())
    ok, reason = verify_recognized_peer(
        peer, a_root.public_key_hex())
    assert ok, reason


def test_verify_recognized_peer_wrong_local_key():
    print("=== verify_recognized_peer: wrong local key → False ===")
    a_root = KeyPair.generate()
    z_root = KeyPair.generate()
    z_anchors, _, _ = _make_anchors(
        world_id="world:poetry-z",
        world_url="http://example-z",
        root_kp=z_root)
    rec = sign_federation_recognition(
        "A", a_root, "Z", z_root.public_key_hex(),
        scope=("contracts",))
    peer = build_recognized_peer(
        rec, z_anchors, "world:poetry-z",
        a_root.public_key_hex())
    wrong = KeyPair.generate()
    ok, reason = verify_recognized_peer(
        peer, wrong.public_key_hex())
    assert not ok


# =====================================================================
# Cross-federation message
# =====================================================================

def test_cross_federation_message_verify():
    print("=== verify_cross_federation_message: happy ===")
    a_root = KeyPair.generate()
    z_root = KeyPair.generate()
    a_sender_kp = KeyPair.generate()
    a_anchors, _, _ = _make_anchors(
        world_id="world:poetry-a",
        world_url="http://a",
        curator_public_key=(
            a_sender_kp.public_key_hex()),
        root_kp=a_root)
    z_rec_of_a = sign_federation_recognition(
        "Z", z_root, "A", a_root.public_key_hex(),
        scope=("contracts",))
    inner = _make_message("world:poetry-a", a_sender_kp)
    wrapper = _wrap_cross_federation_message(inner, a_anchors)
    ok, reason, inner_dict = verify_cross_federation_message(
        wrapper, z_rec_of_a, z_root.public_key_hex())
    assert ok, reason
    assert inner_dict["sender_world_id"] == "world:poetry-a"


def test_cross_federation_message_tampered_inner():
    print("=== Cross-fed message: tampered inner → invalid ===")
    a_root = KeyPair.generate()
    z_root = KeyPair.generate()
    a_sender_kp = KeyPair.generate()
    a_anchors, _, _ = _make_anchors(
        world_id="world:poetry-a",
        world_url="http://a",
        curator_public_key=(
            a_sender_kp.public_key_hex()),
        root_kp=a_root)
    z_rec_of_a = sign_federation_recognition(
        "Z", z_root, "A", a_root.public_key_hex(),
        scope=("contracts",))
    inner = _make_message("world:poetry-a", a_sender_kp)
    wrapper = _wrap_cross_federation_message(inner, a_anchors)
    # Tamper inner
    wrapper["inner"] = dict(wrapper["inner"])
    wrapper["inner"]["payload"] = {"tampered": True}
    ok, reason, _ = verify_cross_federation_message(
        wrapper, z_rec_of_a, z_root.public_key_hex())
    assert not ok
    assert "signature" in reason.lower()


def test_cross_federation_message_tampered_anchors():
    print("=== Cross-fed message: tampered anchors → invalid ===")
    a_root = KeyPair.generate()
    z_root = KeyPair.generate()
    a_sender_kp = KeyPair.generate()
    a_anchors, _, _ = _make_anchors(
        world_id="world:poetry-a",
        world_url="http://a",
        curator_public_key=(
            a_sender_kp.public_key_hex()),
        root_kp=a_root)
    z_rec_of_a = sign_federation_recognition(
        "Z", z_root, "A", a_root.public_key_hex(),
        scope=("contracts",))
    inner = _make_message("world:poetry-a", a_sender_kp)
    wrapper = _wrap_cross_federation_message(inner, a_anchors)
    # Tamper anchors (change curator URL)
    wrapper["remote_anchors"] = dict(wrapper["remote_anchors"])
    wrapper["remote_anchors"]["worlds"] = [
        dict(w) for w in wrapper["remote_anchors"]["worlds"]]
    wrapper["remote_anchors"]["worlds"][0]["manifest_url"] = (
        "http://evil/manifest")
    ok, reason, _ = verify_cross_federation_message(
        wrapper, z_rec_of_a, z_root.public_key_hex())
    assert not ok


def test_cross_federation_message_wrong_local_rec():
    print("=== Cross-fed message: wrong local recognition → invalid ===")
    a_root = KeyPair.generate()
    z_root = KeyPair.generate()
    other_root = KeyPair.generate()
    a_sender_kp = KeyPair.generate()
    a_anchors, _, _ = _make_anchors(
        world_id="world:poetry-a",
        world_url="http://a",
        curator_public_key=(
            a_sender_kp.public_key_hex()),
        root_kp=a_root)
    # Recognition of a WRONG federation
    wrong_rec = sign_federation_recognition(
        "Z", z_root, "A",
        other_root.public_key_hex(),  # not a_root
        scope=("contracts",))
    inner = _make_message("world:poetry-a", a_sender_kp)
    wrapper = _wrap_cross_federation_message(inner, a_anchors)
    ok, reason, _ = verify_cross_federation_message(
        wrapper, wrong_rec, z_root.public_key_hex())
    assert not ok


# =====================================================================
# Xfed handler
# =====================================================================

def _make_xfed_process(tmp_path):
    """Construct a RecognizedPeerProcess with a stub world and
    return it plus its dependencies for inspection."""
    from multiverse_c4 import PoetryWorld
    world = PoetryWorld("world:test", "Test")
    world_kp = KeyPair.generate()
    local_root_kp = KeyPair.generate()
    proc = RecognizedPeerProcess(
        world=world, world_kp=world_kp,
        peers=PeerRegistry(),
        state_dir=tmp_path,
        cycle_interval=0.1,
        contract_policy=AutoAcceptPolicy(),
        identity=create_identity("curator:test"),
        local_root_kp=local_root_kp,
    )
    return proc, world_kp, local_root_kp


def test_xfed_handler_bad_wrapper(tmp_path):
    print("=== Xfed handler: bad wrapper → Refusal ===")
    proc, _, _ = _make_xfed_process(tmp_path)
    try:
        proc.start()
        result = proc._handle_xfed_message("not a dict")
        assert result["kind"] == "refusal"
        result = proc._handle_xfed_message({"kind": "wrong"})
        assert result["kind"] == "refusal"
    finally:
        proc.stop()


def test_xfed_handler_unknown_sender(tmp_path):
    print("=== Xfed handler: unknown sender → Refusal ===")
    proc, _, local_root_kp = _make_xfed_process(tmp_path)
    try:
        proc.start()
        # Build a recognition of an external federation
        ext_root = KeyPair.generate()
        ext_sender_kp = KeyPair.generate()
        ext_anchors, _, _ = _make_anchors(
            world_id="world:ext",
            world_url="http://ext",
            curator_public_key=(
                ext_sender_kp.public_key_hex()),
            root_kp=ext_root)
        rec = sign_federation_recognition(
            "Local", local_root_kp, "Ext",
            ext_root.public_key_hex(),
            scope=("contracts",))
        proc.add_recognition(rec)
        inner = _make_message("world:ext", ext_sender_kp)
        wrapper = _wrap_cross_federation_message(
            inner, ext_anchors)
        # Sender not registered as a peer
        result = proc._handle_xfed_message(wrapper)
        assert result["kind"] == "refusal"
        assert "unknown peer" in result["reason"]
    finally:
        proc.stop()


# =====================================================================
# _deliver uses xfed for recognized peers
# =====================================================================

def test_deliver_uses_xfed_for_recognized_peer(tmp_path):
    print("=== _deliver: uses xfed for recognized peer ===")
    proc, world_kp, local_root_kp = _make_xfed_process(tmp_path)
    try:
        # Build a fake peer
        ext_root = KeyPair.generate()
        ext_curator_kp = KeyPair.generate()
        ext_anchors, _, _ = _make_anchors(
            world_id="world:ext",
            world_url="http://ext",
            curator_public_key=(
                ext_curator_kp.public_key_hex()),
            root_kp=ext_root)
        rec = sign_federation_recognition(
            "Local", local_root_kp, "Ext",
            ext_root.public_key_hex(),
            scope=("contracts",))
        peer = build_recognized_peer(
            rec, ext_anchors, "world:ext",
            local_root_kp.public_key_hex())
        proc.add_recognition(rec)
        proc.add_recognized_peer(peer)
        # Set anchors (only needed to actually send; we're testing
        # routing, so we just check that _deliver chooses xfed)
        proc.set_local_anchors({"fake": "anchors"})
        # Mock urllib to fail so we know it tried to send
        import urllib.request
        original_urlopen = urllib.request.urlopen
        calls = []
        def fake_urlopen(req, timeout=None):
            calls.append(req.full_url)
            raise urllib.error.URLError("simulated")
        urllib.request.urlopen = fake_urlopen
        try:
            inner = _make_message(
                "world:test", world_kp)
            ok, reason = proc._deliver("world:ext", inner)
            assert not ok
            # It tried to hit /xfed/message
            assert len(calls) == 1
            assert "/xfed/message" in calls[0]
        finally:
            urllib.request.urlopen = original_urlopen
    finally:
        proc.stop()


# =====================================================================
# Real end-to-end
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: full inter-federation scenario ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["recognition"]["a_recognizes_z"] is True
    assert audit["recognition"]["z_recognizes_a"] is True
    assert audit["anchor_chain"]["a_anchors_verify"] is True
    assert audit["anchor_chain"]["z_anchors_verify"] is True
    assert audit["contract"]["propose_ok"] is True
    assert audit["contract"]["established_in_a"] is True
    assert audit["contract"]["established_in_z"] is True
    assert (tmp_path / "inter_federation" /
            "inter_federation_demo.json").exists()


if __name__ == "__main__":
    test_recognition_sign_verify()
    test_recognition_wrong_root_key()
    test_recognition_tampered()
    test_recognition_rejects_bad_scope()
    test_build_recognized_peer_happy()
    test_build_recognized_peer_missing_world()
    test_build_recognized_peer_bad_anchors()
    test_verify_recognized_peer_happy()
    test_verify_recognized_peer_wrong_local_key()
    test_cross_federation_message_verify()
    test_cross_federation_message_tampered_inner()
    test_cross_federation_message_tampered_anchors()
    test_cross_federation_message_wrong_local_rec()
    with tempfile.TemporaryDirectory() as tmp:
        test_xfed_handler_bad_wrapper(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_xfed_handler_unknown_sender(Path(tmp))
    with tempfile.TemporaryDirectory() as tmp:
        test_deliver_uses_xfed_for_recognized_peer(Path(tmp))
