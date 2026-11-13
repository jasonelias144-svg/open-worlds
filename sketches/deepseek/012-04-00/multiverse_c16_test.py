# multiverse_c16_test.py
import json
import pytest

from multiverse_c1 import create_identity
from multiverse_c3 import Petition
from multiverse_c4 import PoetryWorld
from multiverse_c13 import HAS_CRYPTO, SignedWorld, SignedAdmission
from multiverse_c14 import PermissiveWorld
from multiverse_c15 import (
    PassportV2, add_signed_admission,
    passport_v2_to_dict, passport_v2_from_dict,
)
from multiverse_c16 import (
    ManifestResolver, ChainResolver, StaticResolver,
)
from wcp_http_shim import WorldProtocolServer


pytestmark = pytest.mark.skipif(
    not HAS_CRYPTO,
    reason="cryptography not installed (pip install cryptography)")


# =====================================================================
# Helpers
# =====================================================================

def _run_server(world) -> tuple:
    """Start a WorldProtocolServer in a thread. Returns (server, base_url)."""
    server = WorldProtocolServer(world, port=0)
    server.serve_in_thread()
    import time; time.sleep(0.1)
    port = server._httpd.server_address[1]
    return server, f"http://127.0.0.1:{port}"


def _petition_and_admit(world, name: str, token: str):
    return world.petition(Petition(
        petitioner_token=token,
        petitioner_name=name,
        passport_admissions=(),
        message="test",
    ))


# =====================================================================
# Happy path
# =====================================================================

def test_resolver_fetches_public_key():
    print("=== Resolver fetches public_key from running world ===")
    base = PermissiveWorld("world:a", "World A")
    signed = SignedWorld(base)
    server, url = _run_server(signed)
    try:
        expected_key = signed.keypair.public_key_hex()
        resolver = ManifestResolver({"world:a": url})
        got = resolver("world:a")
        print(f"  expected: {expected_key[:16]}...")
        print(f"  got:      {got[:16] if got else None}...")
        assert got == expected_key
        stats = resolver.stats()
        print(f"  stats: {stats}")
        assert stats["fetches"] == 1
        assert stats["cache_hits"] == 0
    finally:
        server.stop()


def test_resolver_returns_none_for_unknown_entity():
    print("=== Unknown entity returns None ===")
    resolver = ManifestResolver()
    assert resolver("world:unknown") is None


def test_resolver_returns_none_for_wcp_0_1_world():
    print("=== WCP/0.1 world returns None (no public_key) ===")
    world = PoetryWorld("world:poetry", "The Poetry World")
    server, url = _run_server(world)
    try:
        resolver = ManifestResolver({"world:poetry": url})
        pk = resolver("world:poetry")
        print(f"  pk: {pk}")
        assert pk is None
        # Cached as "known WCP/0.1, no key"
        assert "world:poetry" in resolver._cache
    finally:
        server.stop()


# =====================================================================
# Caching
# =====================================================================

def test_caching_avoids_refetch():
    print("=== Caching avoids re-fetch ===")
    signed = SignedWorld(PermissiveWorld("world:a", "A"))
    server, url = _run_server(signed)
    try:
        resolver = ManifestResolver({"world:a": url})
        r1 = resolver("world:a")
        r2 = resolver("world:a")
        r3 = resolver("world:a")
        assert r1 == r2 == r3
        stats = resolver.stats()
        print(f"  fetches: {stats['fetches']} "
              f"(should be 1)")
        print(f"  cache hits: {stats['cache_hits']} "
              f"(should be 2)")
        assert stats["fetches"] == 1
        assert stats["cache_hits"] == 2
    finally:
        server.stop()


def test_clear_cache_forces_refetch():
    print("=== clear_cache forces re-fetch ===")
    signed = SignedWorld(PermissiveWorld("world:a", "A"))
    server, url = _run_server(signed)
    try:
        resolver = ManifestResolver({"world:a": url})
        resolver("world:a")
        assert resolver.stats()["fetches"] == 1
        resolver.clear_cache()
        resolver("world:a")
        assert resolver.stats()["fetches"] == 2
    finally:
        server.stop()


def test_register_with_new_url_invalidates_cache():
    print("=== Registering a new URL invalidates the cache ===")
    signed_a = SignedWorld(PermissiveWorld("world:a", "A"))
    signed_b = SignedWorld(PermissiveWorld("world:a", "A"))
    server_a, url_a = _run_server(signed_a)
    server_b, url_b = _run_server(signed_b)
    try:
        resolver = ManifestResolver({"world:a": url_a})
        pk_a = resolver("world:a")
        assert pk_a == signed_a.keypair.public_key_hex()
        # Register a different URL for the same entity_id
        resolver.register("world:a", url_b)
        pk_b = resolver("world:a")
        print(f"  pk_a: {pk_a[:16]}...")
        print(f"  pk_b: {pk_b[:16]}...")
        assert pk_a != pk_b
        assert pk_b == signed_b.keypair.public_key_hex()
    finally:
        server_a.stop()
        server_b.stop()


# =====================================================================
# Failure modes
# =====================================================================

def test_fetch_failure_not_cached():
    print("=== Fetch failure returns None and is NOT cached ===")
    calls = []
    def failing_fetcher(url):
        calls.append(url)
        return None
    resolver = ManifestResolver(
        {"world:a": "http://unreachable.example"},
        fetcher=failing_fetcher,
    )
    r1 = resolver("world:a")
    r2 = resolver("world:a")
    print(f"  r1: {r1}")
    print(f"  r2: {r2}")
    print(f"  fetch attempts: {len(calls)} (should be 2)")
    assert r1 is None and r2 is None
    assert len(calls) == 2


def test_malformed_manifest_returns_none():
    print("=== Malformed manifest → None (no crash) ===")
    def bad_fetcher(url):
        return {"not_a_manifest": True}  # missing public_key
    resolver = ManifestResolver(
        {"world:a": "http://x"},
        fetcher=bad_fetcher,
    )
    assert resolver("world:a") is None


def test_fetcher_that_raises_returns_none():
    print("=== Fetcher that raises → None (resolver never raises) ===")
    def raising_fetcher(url):
        raise RuntimeError("simulated network catastrophe")
    resolver = ManifestResolver(
        {"world:a": "http://x"},
        fetcher=raising_fetcher,
    )
    assert resolver("world:a") is None


def test_broken_wcp_0_2_manifest_returns_none():
    print("=== WCP/0.2 manifest with bad public_key → None ===")
    def bad_key_fetcher(url):
        return {
            "entity_id": "world:a",
            "protocol_version": "WCP/0.2",
            "public_key": "too-short",  # not 64 hex
        }
    resolver = ManifestResolver(
        {"world:a": "http://x"},
        fetcher=bad_key_fetcher,
    )
    assert resolver("world:a") is None


# =====================================================================
# Chain resolver
# =====================================================================

def test_chain_falls_through_to_fallback():
    print("=== Chain: primary fails, fallback wins ===")
    signed = SignedWorld(PermissiveWorld("world:a", "A"))
    real_key = signed.keypair.public_key_hex()

    # Primary: always fails to fetch
    primary = ManifestResolver(
        {"world:a": "http://unreachable.example"},
        fetcher=lambda url: None,
    )
    # Fallback: has the key pinned
    fallback = StaticResolver({"world:a": real_key})

    chain = ChainResolver(primary, fallback)
    got = chain("world:a")
    print(f"  got: {got[:16]}...")
    assert got == real_key


def test_chain_uses_primary_when_it_works():
    print("=== Chain: primary wins, fallback not consulted ===")
    signed = SignedWorld(PermissiveWorld("world:a", "A"))
    server, url = _run_server(signed)
    try:
        primary = ManifestResolver({"world:a": url})
        fallback_calls = []
        def counting_fallback(eid):
            fallback_calls.append(eid)
            return "deadbeef" * 8
        chain = ChainResolver(primary, counting_fallback)
        got = chain("world:a")
        print(f"  fallback calls: {len(fallback_calls)} (should be 0)")
        assert got == signed.keypair.public_key_hex()
        assert fallback_calls == []
    finally:
        server.stop()


# =====================================================================
# End-to-end: passport verifies with manifest fetch
# =====================================================================

def test_end_to_end_passport_verifies_via_manifest():
    """The demo C16 unlocks: a client verifies a passport against
    running worlds without pre-shared keys."""
    print("=== End-to-end: passport verifies via manifest fetch ===")
    world = SignedWorld(PermissiveWorld("world:a", "World A"))
    server, url = _run_server(world)
    try:
        # Client A: petition, get admission, add to passport
        alice = create_identity("Alice")
        passport = PassportV2.new(alice)
        adm = _petition_and_admit(world, "Alice", alice.token)
        assert isinstance(adm, SignedAdmission)
        passport = add_signed_admission(passport, adm)

        # Client A "sends" the passport to Client B (serialize)
        wire = passport_v2_to_dict(passport)

        # Client B: has the passport + the URL. Fresh resolver,
        # no pre-shared key. Must fetch the manifest to verify.
        passport_b = passport_v2_from_dict(wire)
        resolver = ManifestResolver({"world:a": url})
        report = passport_b.verify(resolver)
        print(report.format())
        assert report.all_verified is True
    finally:
        server.stop()


def test_end_to_end_two_worlds_verified_offline():
    """Two signed worlds, one passport, verification fetches both."""
    print("=== End-to-end: two worlds, one passport ===")
    world_a = SignedWorld(PermissiveWorld("world:a", "World A"))
    world_b = SignedWorld(PermissiveWorld("world:b", "World B"))
    server_a, url_a = _run_server(world_a)
    server_b, url_b = _run_server(world_b)
    try:
        alice = create_identity("Alice")
        passport = PassportV2.new(alice)

        # Petition A
        adm_a = _petition_and_admit(world_a, "Alice", alice.token)
        passport = add_signed_admission(passport, adm_a)

        # Petition B (carrying the passport entries as plain)
        adm_b = world_b.petition(Petition(
            petitioner_token=alice.token,
            petitioner_name=alice.name,
            passport_admissions=passport.to_plain_entries(),
            message="I was at A.",
        ))
        passport = add_signed_admission(passport, adm_b)

        # Verify: resolver only knows the two URLs, nothing else
        resolver = ManifestResolver({
            "world:a": url_a,
            "world:b": url_b,
        })
        report = passport.verify(resolver)
        print(report.format())
        assert report.all_verified is True
        assert len(report.verified()) == 2
        assert resolver.stats()["fetches"] == 2
    finally:
        server_a.stop()
        server_b.stop()


# =====================================================================
# The "pin" pattern: chain of live resolver + pins
# =====================================================================

def test_chain_pins_override_live_fetch():
    """A client can pin a key to override what the live world says.

    This is the SSH known_hosts pattern: if the client has pinned
    a key, trust the pin over the fetched key. Useful when the
    live world is compromised or in transition.

    In practice, the pin would go first in the chain to take
    precedence — but for the prototype, order is up to the caller.
    Here we show the pin-first configuration.
    """
    print("=== Chain: pin-first overrides live fetch ===")
    world = SignedWorld(PermissiveWorld("world:a", "A"))
    server, url = _run_server(world)
    try:
        pinned_key = world.keypair.public_key_hex()
        # An attacker-controlled "world:a" that would return a
        # different key if consulted:
        rogue = SignedWorld(PermissiveWorld("world:a", "A"))
        server_rogue, url_rogue = _run_server(rogue)
        try:
            # Client chooses to trust the pin over the live URL.
            # Live URL is the rogue; pin is the real.
            pins = StaticResolver({"world:a": pinned_key})
            live = ManifestResolver({"world:a": url_rogue})
            chain = ChainResolver(pins, live)
            got = chain("world:a")
            print(f"  got:    {got[:16]}...")
            print(f"  rogue:  {rogue.keypair.public_key_hex()[:16]}...")
            assert got == pinned_key
            assert got != rogue.keypair.public_key_hex()
        finally:
            server_rogue.stop()
    finally:
        server.stop()


if __name__ == "__main__":
    test_resolver_fetches_public_key()
    test_resolver_returns_none_for_unknown_entity()
    test_resolver_returns_none_for_wcp_0_1_world()
    test_caching_avoids_refetch()
    test_clear_cache_forces_refetch()
    test_register_with_new_url_invalidates_cache()
    test_fetch_failure_not_cached()
    test_malformed_manifest_returns_none()
    test_fetcher_that_raises_returns_none()
    test_broken_wcp_0_2_manifest_returns_none()
    test_chain_falls_through_to_fallback()
    test_chain_uses_primary_when_it_works()
    test_end_to_end_passport_verifies_via_manifest()
    test_end_to_end_two_worlds_verified_offline()
    test_chain_pins_override_live_fetch()
