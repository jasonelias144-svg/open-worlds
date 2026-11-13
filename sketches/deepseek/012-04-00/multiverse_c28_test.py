# multiverse_c28_test.py
import json
import tempfile
from pathlib import Path

import pytest

from multiverse_c13 import HAS_CRYPTO, KeyPair, canonical_bytes
from multiverse_c14 import PermissiveWorld
from multiverse_c15 import PassportV2, PassportEntry
from multiverse_c28 import (
    SignedManifest, sign_manifest, verify_manifest_signature,
    TOFUStore, ManifestFetchResult, SignedManifestResolver,
    SignedManifestWorld, demo,
)


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _manifest_dict(entity_id="world:a", public_key="aa" * 32):
    return {
        "entity_id": entity_id,
        "name": "World A",
        "protocol_version": "WCP/0.2",
        "law_url": f"http://a/law",
        "act_endpoint": f"http://a/act",
        "log_endpoint": f"http://a/log",
        "sub_registry_endpoint": None,
        "public_key": public_key,
    }


def _make_signed(kp=None, entity_id="world:a"):
    if kp is None:
        kp = KeyPair.generate()
    md = _manifest_dict(entity_id, kp.public_key_hex())
    return sign_manifest(md, kp), kp


# =====================================================================
# SignedManifest construction
# =====================================================================

def test_signed_manifest_construction():
    print("=== SignedManifest: required fields, hex validation ===")
    sm, kp = _make_signed()
    assert sm.entity_id == "world:a"
    assert sm.public_key == kp.public_key_hex()
    assert sm.signed_by == kp.public_key_hex()
    with pytest.raises(ValueError):
        SignedManifest(
            entity_id="", name="X", protocol_version="WCP/0.2",
            law_url="u", act_endpoint="u", log_endpoint="u",
            sub_registry_endpoint=None,
            public_key="aa" * 32, signed_by="aa" * 32,
            signature="bb" * 64,
        )
    with pytest.raises(ValueError):
        SignedManifest(
            entity_id="w", name="X", protocol_version="WCP/0.2",
            law_url="u", act_endpoint="u", log_endpoint="u",
            sub_registry_endpoint=None,
            public_key="short", signed_by="aa" * 32,
            signature="bb" * 64,
        )


# =====================================================================
# Sign/verify
# =====================================================================

def test_sign_and_verify_roundtrip():
    print("=== Sign and verify: happy path ===")
    sm, kp = _make_signed()
    assert verify_manifest_signature(sm, kp.public_key_hex())


def test_tampered_manifest_fails():
    print("=== Tampered field breaks signature ===")
    sm, kp = _make_signed()
    # Tamper with law_url
    tampered = SignedManifest(
        entity_id=sm.entity_id, name=sm.name,
        protocol_version=sm.protocol_version,
        law_url="http://attacker/law",   # changed
        act_endpoint=sm.act_endpoint,
        log_endpoint=sm.log_endpoint,
        sub_registry_endpoint=sm.sub_registry_endpoint,
        public_key=sm.public_key, signed_by=sm.signed_by,
        signature=sm.signature,
    )
    assert not verify_manifest_signature(tampered, kp.public_key_hex())


def test_tampered_signed_by_fails():
    print("=== Changing signed_by breaks signature ===")
    sm, kp = _make_signed()
    tampered = SignedManifest(
        entity_id=sm.entity_id, name=sm.name,
        protocol_version=sm.protocol_version,
        law_url=sm.law_url, act_endpoint=sm.act_endpoint,
        log_endpoint=sm.log_endpoint,
        sub_registry_endpoint=sm.sub_registry_endpoint,
        public_key=sm.public_key,
        signed_by="00" * 32,   # changed
        signature=sm.signature,
    )
    assert not verify_manifest_signature(tampered, kp.public_key_hex())


def test_wrong_key_fails():
    print("=== Wrong key fails verification ===")
    sm, _ = _make_signed()
    wrong = KeyPair.generate().public_key_hex()
    assert not verify_manifest_signature(sm, wrong)


def test_sign_manifest_rejects_mismatched_keypair():
    print("=== sign_manifest rejects keypair != signed_by ===")
    kp1 = KeyPair.generate()
    kp2 = KeyPair.generate()
    md = _manifest_dict(public_key=kp2.public_key_hex())
    # kp1 cannot sign as kp2
    with pytest.raises(ValueError):
        sign_manifest(md, kp1, signed_by=kp2.public_key_hex())


# =====================================================================
# TOFU: first use
# =====================================================================

def _fetcher_for(manifest_dict):
    def fetch(url):
        return manifest_dict if url.endswith("/manifest") else None
    return fetch


def test_first_use_self_signed_accepts():
    print("=== First use: self-signed → TOFU-pinned ===")
    sm, kp = _make_signed()
    resolver = SignedManifestResolver(
        {"world:a": "http://a"},
        fetcher=_fetcher_for(sm.to_dict()))
    pk = resolver("world:a")
    result = resolver.last_result("world:a")
    print(result)
    assert result.accepted
    assert result.first_use
    assert pk == kp.public_key_hex()
    assert resolver.tofu().check("world:a") == kp.public_key_hex()


def test_first_use_non_self_signed_rejected():
    print("=== First use: non-self-signed → rejected (no trust anchor) ===")
    old_kp = KeyPair.generate()
    new_kp = KeyPair.generate()
    md = _manifest_dict(public_key=new_kp.public_key_hex())
    sm = sign_manifest(md, old_kp,
                       signed_by=old_kp.public_key_hex())
    resolver = SignedManifestResolver(
        {"world:a": "http://a"},
        fetcher=_fetcher_for(sm.to_dict()))
    pk = resolver("world:a")
    result = resolver.last_result("world:a")
    print(result)
    assert not result.accepted
    assert pk is None
    assert "first contact" in result.reason


# =====================================================================
# TOFU: subsequent
# =====================================================================

def test_subsequent_same_key_accepts():
    print("=== Subsequent: same key, no rotation ===")
    sm, kp = _make_signed()
    resolver = SignedManifestResolver(
        {"world:a": "http://a"},
        fetcher=_fetcher_for(sm.to_dict()))
    resolver("world:a")  # TOFU-pin
    pk = resolver("world:a")  # second fetch
    result = resolver.last_result("world:a")
    assert result.accepted
    assert not result.rotation
    assert pk == kp.public_key_hex()


def test_subsequent_mitm_swap_rejected():
    print("=== Subsequent: attacker swaps manifest → rejected ===")
    sm, kp = _make_signed()
    resolver_1 = SignedManifestResolver(
        {"world:a": "http://a"},
        fetcher=_fetcher_for(sm.to_dict()))
    resolver_1("world:a")  # TOFU-pin real key

    # Attacker crafts a self-signed manifest with their own key
    attacker_kp = KeyPair.generate()
    attacker_sm, _ = _make_signed(attacker_kp)
    resolver_2 = SignedManifestResolver(
        {"world:a": "http://a"},
        tofu=resolver_1.tofu(),
        fetcher=_fetcher_for(attacker_sm.to_dict()))
    pk = resolver_2("world:a")
    result = resolver_2.last_result("world:a")
    print(result)
    assert not result.accepted
    assert pk is None
    assert "signature" in result.reason.lower()


# =====================================================================
# Key rotation
# =====================================================================

def test_rotation_accepted_and_tofu_updated():
    print("=== Rotation: old key signs new key → accepted ===")
    k1 = KeyPair.generate()
    k2 = KeyPair.generate()
    # First: K1 self-signed
    sm1, _ = _make_signed(k1)
    resolver = SignedManifestResolver(
        {"world:a": "http://a"},
        fetcher=_fetcher_for(sm1.to_dict()))
    resolver("world:a")
    assert resolver.tofu().check("world:a") == k1.public_key_hex()

    # Now: rotate to K2, signed by K1
    rotation_md = _manifest_dict(public_key=k2.public_key_hex())
    rotation_sm = sign_manifest(rotation_md, k1,
                                 signed_by=k1.public_key_hex())
    resolver_2 = SignedManifestResolver(
        {"world:a": "http://a"},
        tofu=resolver.tofu(),
        fetcher=_fetcher_for(rotation_sm.to_dict()))
    pk = resolver_2("world:a")
    result = resolver_2.last_result("world:a")
    print(result)
    assert result.accepted
    assert result.rotation
    assert pk == k2.public_key_hex()
    assert resolver_2.tofu().check("world:a") == k2.public_key_hex()


def test_rotation_with_wrong_signature_rejected():
    print("=== Rotation: signed_by claims old key, sig by attacker → rejected ===")
    k1 = KeyPair.generate()
    k2 = KeyPair.generate()
    sm1, _ = _make_signed(k1)
    resolver = SignedManifestResolver(
        {"world:a": "http://a"},
        fetcher=_fetcher_for(sm1.to_dict()))
    resolver("world:a")

    # Attacker crafts a rotation manifest signed by their own key
    attacker_kp = KeyPair.generate()
    rotation_md = _manifest_dict(public_key=k2.public_key_hex())
    # Attacker signs, but claims signed_by=K1
    fake_payload = canonical_bytes({
        "kind": "signed_manifest",
        "entity_id": "world:a",
        "name": "World A",
        "protocol_version": "WCP/0.2",
        "law_url": "http://a/law",
        "act_endpoint": "http://a/act",
        "log_endpoint": "http://a/log",
        "sub_registry_endpoint": None,
        "public_key": k2.public_key_hex(),
        "signed_by": k1.public_key_hex(),
    })
    forged = SignedManifest(
        entity_id="world:a", name="World A",
        protocol_version="WCP/0.2",
        law_url="http://a/law", act_endpoint="http://a/act",
        log_endpoint="http://a/log", sub_registry_endpoint=None,
        public_key=k2.public_key_hex(),
        signed_by=k1.public_key_hex(),
        signature=attacker_kp.sign(fake_payload).hex(),
    )
    resolver_2 = SignedManifestResolver(
        {"world:a": "http://a"},
        tofu=resolver.tofu(),
        fetcher=_fetcher_for(forged.to_dict()))
    pk = resolver_2("world:a")
    result = resolver_2.last_result("world:a")
    assert not result.accepted
    assert pk is None
    # TOFU not updated
    assert resolver_2.tofu().check("world:a") == k1.public_key_hex()


# =====================================================================
# Entity id mismatch
# =====================================================================

def test_entity_id_mismatch_rejected():
    print("=== Manifest claims a different entity_id → rejected ===")
    kp = KeyPair.generate()
    sm = sign_manifest(_manifest_dict("world:b",
                                       kp.public_key_hex()),
                        kp)  # valid, but for world:b
    resolver = SignedManifestResolver(
        {"world:a": "http://a"},
        fetcher=_fetcher_for(sm.to_dict()))
    pk = resolver("world:a")
    result = resolver.last_result("world:a")
    print(result)
    assert not result.accepted
    assert pk is None
    assert "entity_id" in result.reason.lower()


# =====================================================================
# Never raises
# =====================================================================

def test_never_raises():
    print("=== Resolver never raises on bad input ===")
    resolver = SignedManifestResolver(
        {"world:a": "http://a"},
        fetcher=lambda u: "not a dict")  # would fail parse
    assert resolver("world:a") is None
    assert not resolver.last_result("world:a").accepted

    # Fetcher raises
    def raising(u):
        raise RuntimeError("boom")
    resolver2 = SignedManifestResolver(
        {"world:a": "http://a"}, fetcher=raising)
    assert resolver2("world:a") is None
    assert "boom" in resolver2.last_result("world:a").reason

    # No URL
    resolver3 = SignedManifestResolver()
    assert resolver3("world:unknown") is None

    # verify_manifest_signature with bad args
    kp = KeyPair.generate()
    sm, _ = _make_signed()
    assert not verify_manifest_signature(sm, "")
    assert not verify_manifest_signature("not a manifest",
                                          kp.public_key_hex())


# =====================================================================
# JSON roundtrips
# =====================================================================

def test_signed_manifest_json_roundtrip():
    print("=== SignedManifest JSON roundtrip ===")
    sm, kp = _make_signed()
    wire = json.dumps(sm.to_dict())
    revived = SignedManifest.from_dict(json.loads(wire))
    assert revived.canonical_payload() == sm.canonical_payload()
    assert verify_manifest_signature(revived, kp.public_key_hex())


def test_tofu_store_json_roundtrip():
    print("=== TOFUStore JSON roundtrip ===")
    store = TOFUStore()
    store.record("world:a", "aa" * 32, "2024-01-01T00:00:00+00:00")
    store.record("world:b", "bb" * 32, "2024-02-01T00:00:00+00:00")
    wire = json.dumps(store.to_dict())
    revived = TOFUStore.from_dict(json.loads(wire))
    assert revived.check("world:a") == "aa" * 32
    assert revived.first_seen["world:a"] == "2024-01-01T00:00:00+00:00"


# =====================================================================
# HTTP end-to-end
# =====================================================================

def test_http_end_to_end():
    print("=== HTTP: signed manifest served, resolved, verified ===")
    import time
    import urllib.request as _ur
    from wcp_http_shim import WorldProtocolServer

    kp = KeyPair.generate()
    base = PermissiveWorld("world:a", "World A")
    world = SignedManifestWorld(base, kp)
    server = WorldProtocolServer(world, port=0)
    server.serve_in_thread()
    time.sleep(0.1)
    try:
        port = server._httpd.server_address[1]
        url = f"http://127.0.0.1:{port}"
        resolver = SignedManifestResolver({"world:a": url})
        pk = resolver("world:a")
        result = resolver.last_result("world:a")
        print(result)
        assert result.accepted
        assert pk == kp.public_key_hex()
        # And the manifest on the wire contains signed_by
        with _ur.urlopen(f"{url}/manifest", timeout=5) as r:
            data = json.loads(r.read().decode())
        assert data["signed_by"] == kp.public_key_hex()
        assert data["signature"]
    finally:
        server.stop()


# =====================================================================
# Composes with C15 passport
# =====================================================================

def test_composes_with_passport():
    """C15's PassportV2.verify() accepts any PublicKeyResolver.
    SignedManifestResolver is one. Verify a passport whose
    admission is signed by the world whose signed manifest we
    fetch."""
    print("=== Composes with C15 passport verification ===")
    import time
    from multiverse_c13 import SignedWorld, SignedAdmission
    from multiverse_c3 import Petition
    from wcp_http_shim import WorldProtocolServer

    kp = KeyPair.generate()
    base = PermissiveWorld("world:a", "World A")
    signed_responses = SignedWorld(base, kp)
    signed_manifest = SignedManifestWorld(signed_responses, kp)
    server = WorldProtocolServer(signed_manifest, port=0)
    server.serve_in_thread()
    time.sleep(0.1)
    try:
        port = server._httpd.server_address[1]
        url = f"http://127.0.0.1:{port}"

        # Client petitions and captures the signed admission
        resp = signed_manifest.petition(Petition(
            petitioner_token="alice-token",
            petitioner_name="Alice",
            passport_admissions=(),
            message="hi"))
        assert isinstance(resp, SignedAdmission)

        # Build the passport
        from multiverse_c15 import PassportEntry
        from multiverse_c1 import Identity
        passport = PassportV2(
            identity=Identity(token="alice-token", name="Alice"),
            entries=(PassportEntry(
                entity_id=resp.entity_id,
                timestamp=resp.timestamp,
                subject_token=resp.subject_token,
                signature=resp.signature,
            ),),
        )

        # Verify with SignedManifestResolver (fetches manifest)
        resolver = SignedManifestResolver({"world:a": url})
        report = passport.verify(resolver)
        print(report.format())
        assert report.all_verified()
    finally:
        server.stop()


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: TOFU + MITM rejection + rotation ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["step_1_first_contact"]["accepted"]
    assert not audit["step_2_attacker"]["accepted"]
    assert audit["step_3_rotation"]["accepted"]
    assert audit["step_3_rotation"]["rotation"]
    assert (tmp_path / "signed_manifest_demo.json").exists()


if __name__ == "__main__":
    test_signed_manifest_construction()
    test_sign_and_verify_roundtrip()
    test_tampered_manifest_fails()
    test_tampered_signed_by_fails()
    test_wrong_key_fails()
    test_sign_manifest_rejects_mismatched_keypair()
    test_first_use_self_signed_accepts()
    test_first_use_non_self_signed_rejected()
    test_subsequent_same_key_accepts()
    test_subsequent_mitm_swap_rejected()
    test_rotation_accepted_and_tofu_updated()
    test_rotation_with_wrong_signature_rejected()
    test_entity_id_mismatch_rejected()
    test_never_raises()
    test_signed_manifest_json_roundtrip()
    test_tofu_store_json_roundtrip()
    test_http_end_to_end()
    test_composes_with_passport()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
