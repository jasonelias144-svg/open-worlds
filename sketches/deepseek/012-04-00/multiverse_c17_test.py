# multiverse_c17_test.py
import json
import time
import urllib.request
import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import Act, Petition, Ack, Refusal
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, SignedWorld, SignedAdmission, SignedAck,
    canonical_bytes, verify_signature,
)
from multiverse_c14 import PermissiveWorld
from multiverse_c15 import PassportV2, add_signed_admission
from multiverse_c16 import InMemoryKeyResolver
from multiverse_c17 import (
    RegistryEntry, verify_registry_entry,
    SignedMultiverseRegistry, SignedRegistryClient,
    RegistryToKeyResolver,
)
from wcp_http_shim import WorldProtocolServer


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO,
    reason="cryptography not installed (pip install cryptography)")


# =====================================================================
# Helpers
# =====================================================================

def _run(entity) -> tuple:
    server = WorldProtocolServer(entity, port=0)
    server.serve_in_thread()
    time.sleep(0.1)
    port = server._httpd.server_address[1]
    return server, f"http://127.0.0.1:{port}"


def _post(url, body):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())


def _admit_world_to_registry(registry_url, world_url,
                              admin_token="admin:setup"):
    _post(f"{registry_url}/petition", {
        "petitioner_token": admin_token,
        "petitioner_name": "Admin",
        "passport_admissions": [],
        "message": "setup",
    })
    return _post(f"{registry_url}/act", {
        "actor_token": admin_token,
        "type": "multiverse.admit",
        "payload": {"entity_url": world_url},
    })


# =====================================================================
# RegistryEntry basics
# =====================================================================

def test_registry_entry_canonical_payload():
    print("=== RegistryEntry: canonical payload matches server sig ===")
    kp = KeyPair.generate()
    payload = canonical_bytes({
        "kind": "entity_listing",
        "registry_id": "multiverse:r",
        "entity_id": "world:a",
        "url": "http://a",
        "manifest": {"entity_id": "world:a", "name": "A"},
        "timestamp": "2024-01-01T00:00:00+00:00",
    })
    sig = kp.sign(payload).hex()
    entry = RegistryEntry(
        registry_id="multiverse:r", entity_id="world:a",
        url="http://a",
        manifest={"entity_id": "world:a", "name": "A"},
        timestamp="2024-01-01T00:00:00+00:00",
        signature=sig,
    )
    assert entry.canonical_payload() == payload
    assert verify_registry_entry(kp.public_key_hex(), entry)


def test_tampered_manifest_rejected():
    print("=== Tampered manifest → invalid ===")
    kp = KeyPair.generate()
    payload = canonical_bytes({
        "kind": "entity_listing", "registry_id": "multiverse:r",
        "entity_id": "world:a", "url": "http://a",
        "manifest": {"entity_id": "world:a", "name": "A"},
        "timestamp": "t",
    })
    sig = kp.sign(payload).hex()
    # Attacker changes the manifest but keeps the signature
    entry = RegistryEntry(
        registry_id="multiverse:r", entity_id="world:a",
        url="http://a",
        manifest={"entity_id": "world:a", "name": "ROGUE"},
        timestamp="t", signature=sig,
    )
    assert not verify_registry_entry(kp.public_key_hex(), entry)


# =====================================================================
# SignedMultiverseRegistry: signing behavior
# =====================================================================

def test_registry_is_wcp_0_2():
    print("=== Registry manifest_dict is WCP/0.2 ===")
    reg = SignedMultiverseRegistry("multiverse:r", "R")
    m = reg.manifest_dict()
    assert m["protocol_version"] == "WCP/0.2"
    assert len(m["public_key"]) == 64


def test_registry_signs_admissions_and_acks():
    print("=== Registry signs admissions and acks ===")
    reg = SignedMultiverseRegistry("multiverse:r", "R")
    alice = create_identity("Alice")
    adm = reg.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="hi"))
    assert isinstance(adm, SignedAdmission)
    # Verify
    payload = canonical_bytes({
        "kind": "admission", "entity_id": adm.entity_id,
        "timestamp": adm.timestamp, "subject_token": alice.token,
    })
    assert verify_signature(reg.public_key_hex(), payload, adm.signature)


def test_registry_appends_signed_listing_on_admit():
    print("=== Registry appends signed_listing on admit ===")
    reg = SignedMultiverseRegistry("multiverse:r", "R")
    alice = create_identity("Alice")
    reg.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="hi"))
    # Admit an in-process world
    reg.act(Act(
        actor_token=alice.token, type="multiverse.admit",
        payload={"entity": PermissiveWorld("world:a", "World A")},
    ))
    kinds = [e.kind for e in reg.log_since(None)]
    assert "entity_admitted" in kinds
    assert "signed_listing" in kinds
    # Verify the signed listing
    entries = reg.list_sub_entities_signed()
    assert len(entries) == 1
    assert verify_registry_entry(reg.public_key_hex(), entries[0])


def test_registry_refuses_conformance_failures():
    print("=== Registry refuses non-conforming entities (no signed_listing) ===")
    class Broken:
        def manifest(self): return None
        def petition(self, p): return "yes"
        def act(self, a): return "ok"
        def log_since(self, ts=None): return None
    reg = SignedMultiverseRegistry("multiverse:r", "R")
    alice = create_identity("Alice")
    reg.petition(Petition(
        petitioner_token=alice.token, petitioner_name=alice.name,
        passport_admissions=(), message="hi"))
    resp = reg.act(Act(
        actor_token=alice.token, type="multiverse.admit",
        payload={"entity": Broken()}))
    assert isinstance(resp, Refusal)
    entries = reg.list_sub_entities_signed()
    assert len(entries) == 0


# =====================================================================
# SignedRegistryClient: verification
# =====================================================================

def test_client_verifies_listing_over_http():
    print("=== Client verifies listing over HTTP ===")
    world = SignedWorld(PermissiveWorld("world:a", "A"))
    ws, world_url = _run(world)
    reg = SignedMultiverseRegistry("multiverse:r", "R")
    rs, reg_url = _run(reg)
    try:
        _admit_world_to_registry(reg_url, world_url)
        client = SignedRegistryClient(reg_url, reg.public_key_hex())
        entry = client.get_verified("world:a")
        assert entry is not None
        assert entry.url == world_url
        print(f"  verified: {entry.entity_id} at {entry.url}")
    finally:
        ws.stop(); rs.stop()


def test_client_rejects_tampered_listing():
    print("=== Client rejects tampered listing ===")
    reg = SignedMultiverseRegistry("multiverse:r", "R")
    rs, reg_url = _run(reg)
    try:
        # Force a tampered signed_listing into the registry's log
        reg._log.append(type(reg._log[0] if reg._log else
            __import__("multiverse_c3").LogEntry(
                timestamp="2024-01-01T00:00:00+00:00",
                kind="signed_listing", actor_token=None,
                data={
                    "registry_id": "multiverse:r",
                    "entity_id": "world:fake",
                    "url": "http://fake",
                    "manifest": {"entity_id": "world:fake"},
                    "signature": "00" * 64,  # invalid
                }))(
            timestamp="2024-01-01T00:00:00+00:00",
            kind="signed_listing", actor_token=None,
            data=reg._log[-1].data if reg._log else {
                "registry_id": "multiverse:r",
                "entity_id": "world:fake",
                "url": "http://fake",
                "manifest": {"entity_id": "world:fake"},
                "signature": "00" * 64,
            }))
        client = SignedRegistryClient(reg_url, reg.public_key_hex())
        entry = client.get_verified("world:fake")
        assert entry is None
        assert len(client.rejected()) >= 1
    finally:
        rs.stop()


def test_client_rejects_wrong_registry_key():
    print("=== Client rejects entries signed with a different key ===")
    reg = SignedMultiverseRegistry("multiverse:r", "R")
    rs, reg_url = _run(reg)
    try:
        world = SignedWorld(PermissiveWorld("world:a", "A"))
        ws, world_url = _run(world)
        try:
            _admit_world_to_registry(reg_url, world_url)
            # Client uses the WRONG key
            wrong = KeyPair.generate().public_key_hex()
            client = SignedRegistryClient(reg_url, wrong)
            assert client.get_verified("world:a") is None
        finally:
            ws.stop()
    finally:
        rs.stop()


# =====================================================================
# RegistryToKeyResolver — full chain
# =====================================================================

def test_registry_to_key_resolver():
    print("=== RegistryToKeyResolver: entity_id → public_key ===")
    world = SignedWorld(PermissiveWorld("world:a", "A"))
    ws, world_url = _run(world)
    reg = SignedMultiverseRegistry("multiverse:r", "R")
    rs, reg_url = _run(reg)
    try:
        _admit_world_to_registry(reg_url, world_url)
        resolver = RegistryToKeyResolver(reg_url, reg.public_key_hex())
        pk = resolver("world:a")
        assert pk == world.keypair.public_key_hex()
    finally:
        ws.stop(); rs.stop()


def test_registry_to_key_resolver_unknown():
    print("=== RegistryToKeyResolver: unknown entity → None ===")
    reg = SignedMultiverseRegistry("multiverse:r", "R")
    rs, reg_url = _run(reg)
    try:
        resolver = RegistryToKeyResolver(reg_url, reg.public_key_hex())
        assert resolver("world:unknown") is None
    finally:
        rs.stop()


# =====================================================================
# End-to-end: signed federation
# =====================================================================

def test_end_to_end_signed_federation():
    """The definitive integration: signed worlds + signed registry +
    signed passport → all_verified."""
    print("=== End-to-end: signed federation ===")
    world_a = SignedWorld(PermissiveWorld("world:a", "World A"))
    world_b = SignedWorld(PermissiveWorld("world:b", "World B"))
    sa, url_a = _run(world_a)
    sb, url_b = _run(world_b)
    reg = SignedMultiverseRegistry("multiverse:r", "R")
    sr, reg_url = _run(reg)
    try:
        _admit_world_to_registry(reg_url, url_a)
        _admit_world_to_registry(reg_url, url_b)

        alice = create_identity("Alice")
        passport = PassportV2.new(alice)

        # Petition A
        adm_a = _post(f"{url_a}/petition", {
            "petitioner_token": alice.token,
            "petitioner_name": alice.name,
            "passport_admissions": [],
            "message": "hi A",
        })
        passport = passport.with_entry(
            RegistryEntry if False else  # noise to avoid unused
            __import__("multiverse_c15").PassportEntry(
                entity_id=adm_a["entity_id"],
                timestamp=adm_a["timestamp"],
                subject_token=adm_a["subject_token"],
                signature=adm_a["signature"],
            ))

        # Petition B
        adm_b = _post(f"{url_b}/petition", {
            "petitioner_token": alice.token,
            "petitioner_name": alice.name,
            "passport_admissions": list(passport.to_plain_entries()),
            "message": "hi B",
        })
        passport = passport.with_entry(
            __import__("multiverse_c15").PassportEntry(
                entity_id=adm_b["entity_id"],
                timestamp=adm_b["timestamp"],
                subject_token=adm_b["subject_token"],
                signature=adm_b["signature"],
            ))

        # Verify using the registry-derived resolver
        resolver = RegistryToKeyResolver(reg_url,
                                          reg.public_key_hex())
        report = passport.verify(resolver)
        print(report.format())
        assert report.all_verified is True
    finally:
        sa.stop(); sb.stop(); sr.stop()


if __name__ == "__main__":
    test_registry_entry_canonical_payload()
    test_tampered_manifest_rejected()
    test_registry_is_wcp_0_2()
    test_registry_signs_admissions_and_acks()
    test_registry_appends_signed_listing_on_admit()
    test_registry_refuses_conformance_failures()
    test_client_verifies_listing_over_http()
    test_client_rejects_wrong_registry_key()
    test_registry_to_key_resolver()
    test_registry_to_key_resolver_unknown()
    test_end_to_end_signed_federation()
