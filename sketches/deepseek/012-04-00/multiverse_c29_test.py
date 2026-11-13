# multiverse_c29_test.py
import json
import time
import tempfile
from pathlib import Path

import pytest

from multiverse_c1 import create_identity, Identity
from multiverse_c13 import HAS_CRYPTO, KeyPair, SignedWorld, SignedAdmission
from multiverse_c14 import PermissiveWorld
from multiverse_c15 import PassportEntry, PassportV2
from multiverse_c28 import SignedManifestWorld
from multiverse_c29 import (
    SignedListing, verify_signed_listing,
    verify_listing_world_manifest, verify_listing,
    SignedListingRegistry, SignedListingClient, ListingKeyResolver,
    demo,
)
from wcp_http_shim import WorldProtocolServer


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO, reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _run(entity):
    server = WorldProtocolServer(entity, port=0)
    server.serve_in_thread()
    time.sleep(0.1)
    port = server._httpd.server_address[1]
    return server, f"http://127.0.0.1:{port}"


def _post(url, body):
    import urllib.request as _ur
    req = _ur.Request(url, data=json.dumps(body).encode(),
                       headers={"Content-Type": "application/json"},
                       method="POST")
    with _ur.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode())


def _setup_world_with_manifest(port_world=None):
    kp = KeyPair.generate()
    base = PermissiveWorld("world:poetry", "The Poetry World")
    signed_responses = SignedWorld(base, kp)
    world = SignedManifestWorld(signed_responses, kp)
    server, url = _run(world)
    return kp, world, server, url


def _admit_world_to_registry(reg_url, world_url):
    _post(f"{reg_url}/petition", {
        "petitioner_token": "admin",
        "petitioner_name": "Admin",
        "passport_admissions": [],
        "message": "setup",
    })
    return _post(f"{reg_url}/act", {
        "actor_token": "admin",
        "type": "multiverse.admit",
        "payload": {"entity_url": world_url},
    })


# =====================================================================
# Signed listing verification
# =====================================================================

def test_verify_v2_listing():
    print("=== Verify v2 signed listing (with signed_manifest) ===")
    reg_kp = KeyPair.generate()
    world_kp = KeyPair.generate()
    manifest_dict = {
        "entity_id": "world:a", "name": "A",
        "protocol_version": "WCP/0.2",
        "law_url": "u", "act_endpoint": "u", "log_endpoint": "u",
        "sub_registry_endpoint": None,
        "public_key": world_kp.public_key_hex(),
        "signed_by": world_kp.public_key_hex(),
        "signature": "00" * 64,
    }
    from multiverse_c28 import sign_manifest
    signed_manifest = sign_manifest(
        {k: v for k, v in manifest_dict.items()
         if k not in ("signature",)},
        world_kp,
    )
    signed_manifest_dict = signed_manifest.to_dict()

    from multiverse_c13 import canonical_bytes
    v2_payload = canonical_bytes({
        "kind": "entity_listing_with_manifest",
        "registry_id": "multiverse:r",
        "entity_id": "world:a",
        "url": "http://a",
        "signed_manifest": signed_manifest_dict,
        "timestamp": "t",
    })
    sig_v2 = reg_kp.sign(v2_payload).hex()

    listing = SignedListing(
        registry_id="multiverse:r", entity_id="world:a",
        url="http://a", manifest=manifest_dict,
        signed_manifest=signed_manifest_dict,
        timestamp="t",
        signature="irrelevant",  # v1 not needed
        signature_v2=sig_v2,
    )
    assert verify_signed_listing(reg_kp.public_key_hex(), listing)
    assert verify_listing_world_manifest(listing)
    assert verify_listing(reg_kp.public_key_hex(), listing)


def test_verify_v1_fallback_when_no_v2():
    print("=== v1 fallback: listing without signed_manifest verifies via v1 ===")
    reg_kp = KeyPair.generate()
    from multiverse_c13 import canonical_bytes
    manifest_dict = {"entity_id": "world:a", "name": "A"}
    v1_payload = canonical_bytes({
        "kind": "entity_listing",
        "registry_id": "multiverse:r",
        "entity_id": "world:a",
        "url": "http://a",
        "manifest": manifest_dict,
        "timestamp": "t",
    })
    sig_v1 = reg_kp.sign(v1_payload).hex()
    listing = SignedListing(
        registry_id="multiverse:r", entity_id="world:a",
        url="http://a", manifest=manifest_dict,
        signed_manifest=None, timestamp="t",
        signature=sig_v1, signature_v2=None,
    )
    assert verify_signed_listing(reg_kp.public_key_hex(), listing)
    assert verify_listing_world_manifest(listing)  # nothing to verify
    assert verify_listing(reg_kp.public_key_hex(), listing)


def test_tampered_signed_manifest_breaks_v2():
    print("=== Tampering with signed_manifest breaks v2 signature ===")
    reg_kp = KeyPair.generate()
    world_kp = KeyPair.generate()
    from multiverse_c28 import sign_manifest
    from multiverse_c13 import canonical_bytes
    sm = sign_manifest(
        {"entity_id": "world:a", "name": "A",
         "protocol_version": "WCP/0.2",
         "law_url": "u", "act_endpoint": "u", "log_endpoint": "u",
         "sub_registry_endpoint": None,
         "public_key": world_kp.public_key_hex()},
        world_kp,
    ).to_dict()
    v2_payload = canonical_bytes({
        "kind": "entity_listing_with_manifest",
        "registry_id": "multiverse:r", "entity_id": "world:a",
        "url": "http://a", "signed_manifest": sm, "timestamp": "t",
    })
    sig_v2 = reg_kp.sign(v2_payload).hex()
    # Tamper
    tampered_sm = dict(sm)
    tampered_sm["law_url"] = "http://attacker/law"
    listing = SignedListing(
        registry_id="multiverse:r", entity_id="world:a",
        url="http://a", manifest=tampered_sm,
        signed_manifest=tampered_sm, timestamp="t",
        signature="x", signature_v2=sig_v2,
    )
    assert not verify_signed_listing(reg_kp.public_key_hex(), listing)


# =====================================================================
# Registry: admission requires signed manifest
# =====================================================================

def test_registry_admits_signed_manifest_world():
    print("=== Registry admits world with signed manifest ===")
    world_kp, _, ws, world_url = _setup_world_with_manifest()
    reg_kp = KeyPair.generate()
    registry = SignedListingRegistry(
        "multiverse:main", "Main MV", reg_kp)
    rs, reg_url = _run(registry)
    try:
        resp = _admit_world_to_registry(reg_url, world_url)
        assert resp["kind"] == "ack"
        listings = registry.signed_listings()
        assert len(listings) == 1
        assert listings[0].entity_id == "world:poetry"
        assert listings[0].signed_manifest is not None
        # Verify the listing verifies
        assert verify_signed_listing(
            reg_kp.public_key_hex(), listings[0])
        assert verify_listing_world_manifest(listings[0])
    finally:
        ws.stop(); rs.stop()


def test_registry_refuses_unsigned_world():
    print("=== Registry refuses world with unsigned manifest ===")
    # Plain SignedWorld serves .manifest() (not .manifest_dict())
    world_kp = KeyPair.generate()
    base = PermissiveWorld("world:plain", "Plain")
    world = SignedWorld(base, world_kp)
    ws, world_url = _run(world)
    reg_kp = KeyPair.generate()
    registry = SignedListingRegistry(
        "multiverse:main", "Main MV", reg_kp)
    rs, reg_url = _run(registry)
    try:
        resp = _admit_world_to_registry(reg_url, world_url)
        assert resp["kind"] == "refusal"
        assert "SignedManifest" in resp["reason"]
        assert len(registry.signed_listings()) == 0
    finally:
        ws.stop(); rs.stop()


def test_registry_refuses_forged_manifest():
    print("=== Registry refuses manifest with forged signature ===")
    attacker_kp = KeyPair.generate()
    real_kp = KeyPair.generate()
    # Build a world serving a manifest signed by the wrong key
    from multiverse_c28 import SignedManifest
    fake_manifest = {
        "entity_id": "world:fake", "name": "Fake",
        "protocol_version": "WCP/0.2",
        "law_url": "u", "act_endpoint": "u", "log_endpoint": "u",
        "sub_registry_endpoint": None,
        "public_key": attacker_kp.public_key_hex(),
        "signed_by": attacker_kp.public_key_hex(),
        "signature": "00" * 64,  # invalid sig
    }
    class FakeWorld:
        def manifest(self):
            return PermissiveWorld(
                "world:fake", "Fake").manifest()
        def manifest_dict(self):
            return fake_manifest
        def petition(self, p):
            return PermissiveWorld(
                "world:fake", "Fake").petition(p)
        def act(self, a):
            return PermissiveWorld(
                "world:fake", "Fake").act(a)
        def log_since(self, ts=None):
            return []
    ws, world_url = _run(FakeWorld())
    reg_kp = KeyPair.generate()
    registry = SignedListingRegistry(
        "multiverse:main", "Main MV", reg_kp)
    rs, reg_url = _run(registry)
    try:
        resp = _admit_world_to_registry(reg_url, world_url)
        assert resp["kind"] == "refusal"
        assert "signature" in resp["reason"].lower()
    finally:
        ws.stop(); rs.stop()


# =====================================================================
# Client: fetch, verify, get key without world fetch
# =====================================================================

def test_client_gets_key_from_registry_log():
    print("=== Client gets world's key from registry log (no world fetch) ===")
    world_kp, world, ws, world_url = _setup_world_with_manifest()
    reg_kp = KeyPair.generate()
    registry = SignedListingRegistry(
        "multiverse:main", "Main MV", reg_kp)
    rs, reg_url = _run(registry)
    try:
        _admit_world_to_registry(reg_url, world_url)
        # Stop the world
        ws.stop()
        ws = None
        # Client fetches registry only
        client = SignedListingClient(
            reg_url, reg_kp.public_key_hex())
        pk = client.get_public_key("world:poetry")
        assert pk == world_kp.public_key_hex()
        assert len(client.list_verified()) == 1
        assert len(client.rejected()) == 0
    finally:
        if ws: ws.stop()
        rs.stop()


def test_client_rejects_wrong_registry_key():
    print("=== Client with wrong registry key rejects all listings ===")
    world_kp, _, ws, world_url = _setup_world_with_manifest()
    reg_kp = KeyPair.generate()
    registry = SignedListingRegistry(
        "multiverse:main", "Main MV", reg_kp)
    rs, reg_url = _run(registry)
    try:
        _admit_world_to_registry(reg_url, world_url)
        # Client uses wrong key
        wrong = KeyPair.generate().public_key_hex()
        client = SignedListingClient(reg_url, wrong)
        assert client.get_public_key("world:poetry") is None
        assert len(client.rejected()) == 1
    finally:
        ws.stop(); rs.stop()


def test_client_publishes_manifest_with_backward_signature():
    print("=== Registry log entry carries both v1 and v2 signatures ===")
    world_kp, _, ws, world_url = _setup_world_with_manifest()
    reg_kp = KeyPair.generate()
    registry = SignedListingRegistry(
        "multiverse:main", "Main MV", reg_kp)
    rs, reg_url = _run(registry)
    try:
        _admit_world_to_registry(reg_url, world_url)
        # Inspect the log directly
        import urllib.request as _ur
        with _ur.urlopen(f"{reg_url}/log", timeout=5) as r:
            log = json.loads(r.read().decode())
        listings = [e for e in log["entries"]
                    if e["kind"] == "signed_listing"]
        assert len(listings) == 1
        data = listings[0]["data"]
        assert data["signature"]  # v1 present
        assert data["signature_v2"]  # v2 present
        assert data["signed_manifest"]  # v2 field
        # Both signatures are distinct
        assert data["signature"] != data["signature_v2"]
    finally:
        ws.stop(); rs.stop()


# =====================================================================
# ListingKeyResolver → passport verification
# =====================================================================

def test_passport_verifies_via_listing_no_world_fetch():
    print("=== Passport verifies via listing (world offline) ===")
    world_kp, world, ws, world_url = _setup_world_with_manifest()
    reg_kp = KeyPair.generate()
    registry = SignedListingRegistry(
        "multiverse:main", "Main MV", reg_kp)
    rs, reg_url = _run(registry)
    try:
        _admit_world_to_registry(reg_url, world_url)
        # Client petitions world while online
        alice = create_identity("Alice")
        from multiverse_c3 import Petition
        adm = world.petition(Petition(
            petitioner_token=alice.token,
            petitioner_name=alice.name,
            passport_admissions=(),
            message="hi"))
        assert isinstance(adm, SignedAdmission)
        passport = PassportV2(
            identity=Identity(token=alice.token, name=alice.name),
            entries=(PassportEntry(
                entity_id=adm.entity_id,
                timestamp=adm.timestamp,
                subject_token=adm.subject_token,
                signature=adm.signature,
            ),),
        )
        # Stop the world
        ws.stop()
        ws = None
        # Verify via registry listing (no world fetch)
        client = SignedListingClient(
            reg_url, reg_kp.public_key_hex())
        resolver = ListingKeyResolver(client)
        report = passport.verify(resolver)
        print(report.format())
        assert report.all_verified()
    finally:
        if ws: ws.stop()
        rs.stop()


# =====================================================================
# JSON roundtrips
# =====================================================================

def test_signed_listing_json_roundtrip():
    print("=== SignedListing JSON roundtrip ===")
    world_kp, _, ws, world_url = _setup_world_with_manifest()
    reg_kp = KeyPair.generate()
    registry = SignedListingRegistry(
        "multiverse:main", "Main MV", reg_kp)
    rs, reg_url = _run(registry)
    try:
        _admit_world_to_registry(reg_url, world_url)
        listing = registry.signed_listings()[0]
        wire = json.dumps({
            "timestamp": listing.timestamp,
            "kind": "signed_listing",
            "data": {
                "registry_id": listing.registry_id,
                "entity_id": listing.entity_id,
                "url": listing.url,
                "manifest": listing.manifest,
                "signed_manifest": listing.signed_manifest,
                "signature": listing.signature,
                "signature_v2": listing.signature_v2,
            },
        })
        revived = SignedListing.from_log_dict(json.loads(wire))
        assert verify_signed_listing(
            reg_kp.public_key_hex(), revived)
        assert revived.signed_manifest == listing.signed_manifest
    finally:
        ws.stop(); rs.stop()


# =====================================================================
# Never raises
# =====================================================================

def test_verifiers_never_raise():
    print("=== verify functions never raise ===")
    assert not verify_signed_listing("", None)
    assert not verify_signed_listing("aa" * 32, "not a listing")
    assert not verify_listing_world_manifest(None)
    assert not verify_listing("aa" * 32, None)


# =====================================================================
# Demo
# =====================================================================

def test_demo(tmp_path):
    print("=== Demo: registry vouches, client verifies, world offline ===")
    audit = demo(artifact_dir=str(tmp_path))
    assert audit["admit_response_kind"] == "ack"
    assert audit["verified_listing_count"] == 1
    assert audit["passport_verified_without_world"] is True
    assert (tmp_path / "signed_listing_demo.json").exists()


if __name__ == "__main__":
    test_verify_v2_listing()
    test_verify_v1_fallback_when_no_v2()
    test_tampered_signed_manifest_breaks_v2()
    test_registry_admits_signed_manifest_world()
    test_registry_refuses_unsigned_world()
    test_registry_refuses_forged_manifest()
    test_client_gets_key_from_registry_log()
    test_client_rejects_wrong_registry_key()
    test_client_publishes_manifest_with_backward_signature()
    test_passport_verifies_via_listing_no_world_fetch()
    test_signed_listing_json_roundtrip()
    test_verifiers_never_raise()
    with tempfile.TemporaryDirectory() as tmp:
        test_demo(Path(tmp))
