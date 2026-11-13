# multiverse_c21_test.py
import json
import time

import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import Act, Petition
from multiverse_c4 import PoetryWorld
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, SignedWorld, SignedAdmission,
    canonical_bytes,
)
from multiverse_c14 import PermissiveWorld
from multiverse_c15 import (
    PassportEntry, PassportV2, add_signed_admission,
)
from multiverse_c17 import SignedMultiverseRegistry
from multiverse_c21 import (
    EntryProvenance, ProvenanceReport,
    verify_cross_world_provenance,
    _verdict_marker, _post_http,
)
from wcp_http_shim import WorldProtocolServer


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO,
    reason="cryptography not installed")


# =====================================================================
# Helpers
# =====================================================================

def _run(entity):
    server = WorldProtocolServer(entity, port=0)
    server.serve_in_thread()
    time.sleep(0.1)
    port = server._httpd.server_address[1]
    return server, f"http://127.0.0.1:{port}"


def _admit_world_to_registry(reg_url, world_url,
                              admin_token="admin:setup"):
    _post_http(f"{reg_url}/petition", {
        "petitioner_token": admin_token,
        "petitioner_name": "Admin",
        "passport_admissions": [],
        "message": "setup",
    })
    return _post_http(f"{reg_url}/act", {
        "actor_token": admin_token,
        "type": "multiverse.admit",
        "payload": {"entity_url": world_url},
    })


def _stub_fetcher_from_registry(registry):
    """Serve registry.log_since() as /log; nothing else."""
    from multiverse_c3 import LogEntry  # noqa
    def fetch(url):
        if url.endswith("/log"):
            return {
                "entries": [
                    {"timestamp": e.timestamp, "kind": e.kind,
                     "actor_token": e.actor_token, "data": e.data}
                    for e in registry.log_since(None)
                ]
            }
        return None
    return fetch


# =====================================================================
# Happy path
# =====================================================================

def test_happy_path_three_worlds():
    print("=== Happy path: three worlds, three verified entries ===")
    worlds = [SignedWorld(PermissiveWorld(f"world:{n}", n.upper()))
              for n in ("a", "b", "c")]
    world_servers = [_run(w) for w in worlds]
    reg = SignedMultiverseRegistry("multiverse:r", "R")
    reg_server, reg_url = _run(reg)
    try:
        for (_, url) in world_servers:
            _admit_world_to_registry(reg_url, url)

        alice = create_identity("Alice")
        passport = PassportV2.new(alice)
        for (world, (_, url)) in zip(worlds, world_servers):
            resp = _post_http(f"{url}/petition", {
                "petitioner_token": alice.token,
                "petitioner_name": alice.name,
                "passport_admissions": list(
                    passport.to_plain_entries()),
                "message": "hi",
            })
            adm = SignedAdmission(
                entity_id=resp["entity_id"],
                timestamp=resp["timestamp"],
                subject_token=resp["subject_token"],
                signature=resp["signature"],
            )
            passport = add_signed_admission(passport, adm)

        report = verify_cross_world_provenance(
            passport, reg_url, reg.public_key_hex())
        print(report.format())
        assert report.all_verified()
        assert len(report.entries) == 3
        assert all(e.verdict == "verified" for e in report.entries)
        # Every entry has the full chain
        for e in report.entries:
            assert e.registry_listing is not None
            assert e.registry_verified
            assert e.listed_url is not None
            assert e.manifest_fetched
            assert e.manifest_public_key
            assert e.signature_valid
    finally:
        for s, _ in world_servers:
            s.stop()
        reg_server.stop()


# =====================================================================
# The diagnostic value: stage-named failures
# =====================================================================

def test_unlisted_world_reports_registry_stage():
    print("=== Unlisted world → unverifiable at registry stage ===")
    kp = KeyPair.generate()
    alice = create_identity("Alice")
    # Alice has an admission from a world the registry never listed
    canonical = canonical_bytes({
        "kind": "admission",
        "entity_id": "world:rogue",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "subject_token": alice.token,
    })
    entry = PassportEntry(
        entity_id="world:rogue",
        timestamp="2024-01-01T00:00:00+00:00",
        subject_token=alice.token,
        signature=kp.sign(canonical).hex(),
    )
    passport = PassportV2.new(alice).with_entry(entry)
    # Empty registry
    reg = SignedMultiverseRegistry("multiverse:r", "R")
    fetcher = _stub_fetcher_from_registry(reg)
    report = verify_cross_world_provenance(
        passport, "http://stub", reg.public_key_hex(),
        fetcher=fetcher)
    print(report.format())
    assert not report.all_verified()
    assert report.entries[0].verdict == "unverifiable"
    assert report.entries[0].failure_stage == "registry"


def test_invalid_admission_reports_signature_stage():
    print("=== Forged signature → invalid at signature stage ===")
    world = SignedWorld(PermissiveWorld("world:a", "A"))
    ws, url = _run(world)
    reg = SignedMultiverseRegistry("multiverse:r", "R")
    rs, reg_url = _run(reg)
    try:
        _admit_world_to_registry(reg_url, url)
        alice = create_identity("Alice")
        # Attacker forges an admission with attacker's key
        attacker = KeyPair.generate()
        canonical = canonical_bytes({
            "kind": "admission",
            "entity_id": "world:a",
            "timestamp": "2024-01-01T00:00:00+00:00",
            "subject_token": alice.token,
        })
        entry = PassportEntry(
            entity_id="world:a",
            timestamp="2024-01-01T00:00:00+00:00",
            subject_token=alice.token,
            signature=attacker.sign(canonical).hex(),
        )
        passport = PassportV2.new(alice).with_entry(entry)
        report = verify_cross_world_provenance(
            passport, reg_url, reg.public_key_hex())
        print(report.format())
        assert not report.all_verified()
        e = report.entries[0]
        assert e.verdict == "invalid"
        assert e.failure_stage == "signature"
        # Registry and manifest stages passed
        assert e.registry_verified
        assert e.manifest_fetched
    finally:
        ws.stop(); rs.stop()


def test_in_process_listing_reports_url_stage():
    print("=== In-process listing → unverifiable at URL stage ===")
    alice = create_identity("Alice")
    world = PermissiveWorld("world:a", "A")
    # Admit in-process (no entity_url)
    reg = SignedMultiverseRegistry("multiverse:r", "R")
    reg.petition(Petition(
        petitioner_token="admin", petitioner_name="Admin",
        passport_admissions=(), message="setup"))
    reg.act(Act(
        actor_token="admin", type="multiverse.admit",
        payload={"entity": world}))
    # Build a passport with a signed admission from world:a
    kp = KeyPair.generate()
    canonical = canonical_bytes({
        "kind": "admission",
        "entity_id": "world:a",
        "timestamp": "2024-01-01T00:00:00+00:00",
        "subject_token": alice.token,
    })
    entry = PassportEntry(
        entity_id="world:a",
        timestamp="2024-01-01T00:00:00+00:00",
        subject_token=alice.token,
        signature=kp.sign(canonical).hex(),
    )
    passport = PassportV2.new(alice).with_entry(entry)
    fetcher = _stub_fetcher_from_registry(reg)
    report = verify_cross_world_provenance(
        passport, "http://stub", reg.public_key_hex(),
        fetcher=fetcher)
    print(report.format())
    assert not report.all_verified()
    assert report.entries[0].verdict == "unverifiable"
    assert report.entries[0].failure_stage == "url"


def test_unsigned_entry_is_unverified():
    print("=== Unsigned entry → unverified (not invalid) ===")
    alice = create_identity("Alice")
    entry = PassportEntry(
        entity_id="world:a", timestamp="2024-01-01T00:00:00+00:00")
    passport = PassportV2.new(alice).with_entry(entry)
    reg = SignedMultiverseRegistry("multiverse:r", "R")
    fetcher = _stub_fetcher_from_registry(reg)
    report = verify_cross_world_provenance(
        passport, "http://stub", reg.public_key_hex(),
        fetcher=fetcher)
    # Unsigned → unverifiable at registry stage (no listing)
    e = report.entries[0]
    assert e.verdict == "unverifiable"
    assert e.failure_stage == "registry"


# =====================================================================
# Honest limits
# =====================================================================

def test_removed_world_still_verifies():
    """Honest limit: removal from the live registry does not
    invalidate the historical signed_listing."""
    print("=== Honest limit: removed world still verifies ===")
    world = SignedWorld(PermissiveWorld("world:a", "A"))
    ws, url = _run(world)
    reg = SignedMultiverseRegistry("multiverse:r", "R")
    rs, reg_url = _run(reg)
    try:
        _admit_world_to_registry(reg_url, url)
        alice = create_identity("Alice")
        resp = _post_http(f"{url}/petition", {
            "petitioner_token": alice.token,
            "petitioner_name": alice.name,
            "passport_admissions": [],
            "message": "hi",
        })
        adm = SignedAdmission(
            entity_id=resp["entity_id"],
            timestamp=resp["timestamp"],
            subject_token=resp["subject_token"],
            signature=resp["signature"],
        )
        passport = add_signed_admission(
            PassportV2.new(alice), adm)

        # Remove the world from the live registry
        _post_http(f"{reg_url}/act", {
            "actor_token": "admin:setup",
            "type": "multiverse.remove",
            "payload": {"entity_id": "world:a"},
        })

        # Verify — the historical signed_listing is still there
        report = verify_cross_world_provenance(
            passport, reg_url, reg.public_key_hex())
        assert report.all_verified()
        print("  ✓ removed world still verifies (documented limit)")
    finally:
        ws.stop(); rs.stop()


def test_wrong_registry_key_rejects_all():
    print("=== Wrong registry key → all entries fail at registry ===")
    world = SignedWorld(PermissiveWorld("world:a", "A"))
    ws, url = _run(world)
    reg = SignedMultiverseRegistry("multiverse:r", "R")
    rs, reg_url = _run(reg)
    try:
        _admit_world_to_registry(reg_url, url)
        alice = create_identity("Alice")
        resp = _post_http(f"{url}/petition", {
            "petitioner_token": alice.token,
            "petitioner_name": alice.name,
            "passport_admissions": [],
            "message": "hi",
        })
        adm = SignedAdmission(
            entity_id=resp["entity_id"],
            timestamp=resp["timestamp"],
            subject_token=resp["subject_token"],
            signature=resp["signature"],
        )
        passport = add_signed_admission(
            PassportV2.new(alice), adm)

        wrong_key = KeyPair.generate().public_key_hex()
        report = verify_cross_world_provenance(
            passport, reg_url, wrong_key)
        assert not report.all_verified()
        assert report.entries[0].failure_stage == "registry"
    finally:
        ws.stop(); rs.stop()


# =====================================================================
# Report format
# =====================================================================

def test_format_includes_staged_columns():
    print("=== Format shows registry / URL / manifest / signature ===")
    reg = SignedMultiverseRegistry("multiverse:r", "R")
    alice = create_identity("Alice")
    entry = PassportEntry(
        entity_id="world:a", timestamp="t")
    passport = PassportV2.new(alice).with_entry(entry)
    fetcher = _stub_fetcher_from_registry(reg)
    report = verify_cross_world_provenance(
        passport, "http://stub", reg.public_key_hex(),
        fetcher=fetcher)
    text = report.format()
    assert "Registry:" in text
    assert "URL:" in text
    assert "Manifest:" in text
    assert "Signature:" in text
    assert "Verdict:" in text
    assert "Summary:" in text


def test_to_dict_is_json_serializable():
    print("=== to_dict is JSON-serializable ===")
    reg = SignedMultiverseRegistry("multiverse:r", "R")
    alice = create_identity("Alice")
    entry = PassportEntry(entity_id="w:a", timestamp="t")
    passport = PassportV2.new(alice).with_entry(entry)
    fetcher = _stub_fetcher_from_registry(reg)
    report = verify_cross_world_provenance(
        passport, "http://stub", reg.public_key_hex(),
        fetcher=fetcher)
    d = report.to_dict()
    s = json.dumps(d)
    parsed = json.loads(s)
    assert parsed["passport_name"] == "Alice"
    assert len(parsed["entries"]) == 1
    assert "counts" in parsed
    assert "all_verified" in parsed


def test_verdict_markers():
    print("=== Verdict markers are distinct ===")
    markers = {_verdict_marker(v)
               for v in ("verified", "invalid",
                          "unverifiable", "unverified")}
    assert len(markers) == 4


# =====================================================================
# Demo
# =====================================================================

def test_demo_runs_end_to_end():
    print("=== Demo: three worlds, one registry, one passport ===")
    from multiverse_c21 import run_cross_world_demo
    report = run_cross_world_demo()
    assert report.all_verified()
    assert len(report.entries) == 3


if __name__ == "__main__":
    test_happy_path_three_worlds()
    test_unlisted_world_reports_registry_stage()
    test_invalid_admission_reports_signature_stage()
    test_in_process_listing_reports_url_stage()
    test_unsigned_entry_is_unverified()
    test_removed_world_still_verifies()
    test_wrong_registry_key_rejects_all()
    test_format_includes_staged_columns()
    test_to_dict_is_json_serializable()
    test_verdict_markers()
    test_demo_runs_end_to_end()
