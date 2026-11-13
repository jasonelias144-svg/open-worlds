"""
multiverse_c29.py — Component 29: Signed Manifests in the Registry.

Composes C28 (SignedManifest) with C17 (SignedMultiverseRegistry).

On admission (multiverse.admit with entity_url):
  - Registry fetches <url>/manifest.
  - Requires a valid SignedManifest (self-signed on first registration).
  - Verifies the manifest's self-signature; refuses if invalid.
  - Emits signed_listing with:
      * manifest         — plain dict, backward compatible
      * signed_manifest  — the SignedManifest dict, new
      * signature        — over original C17 payload (backward compat)
      * signature_v2     — over new payload (includes signed_manifest)

Client:
  - Fetches /log, filters signed_listing entries.
  - Verifies registry signature at v2 (if signature_v2 present),
    else v1 (backward compat).
  - If signed_manifest present, verifies the world's self-signature.
  - Returns verified SignedListing; key is signed_manifest["public_key"].
  - ListingKeyResolver returns that key without fetching the world.

Trust chain (fully verifiable by a client that pins the registry key):
  registry key
    → signed_listing (registry sig)
    → signed_manifest (world sig)
    → world public_key
    → passport entries signed by that key

House rules honored:
  - "A world never raises on what a visitor sends" — registry
    refuses bad manifests; client returns None on bad input. Never raises.
  - "Every behaviour has a test that fails if the behaviour breaks" —
    one test per case: registry refuses malformed manifest, registry
    refuses forged manifest, client accepts v2 listing, client
    rejects tampered manifest, client falls back to v1, key resolver
    works without fetch, passport verifies via listing-only.
  - "History, not rank" — the listing is a snapshot of facts (which
    world, at which URL, with which signed manifest). No score.

Honest limits (documented, tested):
  - The listing is a SNAPSHOT. A world that rotates its key after
    listing has a stale key in the listing. Clients verifying
    historical admissions use the listing's key; clients verifying
    live state must re-fetch (via C28). Both modes are supported;
    the tradeoff is the caller's call.
  - The registry's key is still the caller's pin. Same recursion
    bottom as C17.
  - No timestamp verification. Same as C24/C25/C26.
  - No registry-level revocation. A removed listing is still in
    the log; the log is append-only. (Same as C17's documented
    limit.)
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple

from multiverse_c13 import (
    HAS_CRYPTO, canonical_bytes, verify_signature,
)
from multiverse_c17 import (
    RegistryEntry, SignedMultiverseRegistry,
    verify_registry_entry,
)
from multiverse_c28 import (
    SignedManifest, verify_manifest_signature,
)


# =====================================================================
# SignedListing — one listing, potentially carrying a signed manifest
# =====================================================================

@dataclass(frozen=True)
class SignedListing:
    """A signed_listing entry, from either v1 (no signed_manifest)
    or v2 (with signed_manifest) of the registry's log format.

    `signature` covers the v1 payload (C17). `signature_v2` covers
    the v2 payload (includes signed_manifest). A new client verifies
    v2 if present; falls back to v1 otherwise.
    """
    registry_id: str
    entity_id: str
    url: str
    manifest: Dict                    # plain dict, always present
    signed_manifest: Optional[Dict]   # SignedManifest dict, or None
    timestamp: str
    signature: str                    # over v1 payload
    signature_v2: Optional[str]       # over v2 payload, or None

    def canonical_payload_v1(self) -> bytes:
        return canonical_bytes({
            "kind": "entity_listing",
            "registry_id": self.registry_id,
            "entity_id": self.entity_id,
            "url": self.url,
            "manifest": self.manifest,
            "timestamp": self.timestamp,
        })

    def canonical_payload_v2(self) -> bytes:
        return canonical_bytes({
            "kind": "entity_listing_with_manifest",
            "registry_id": self.registry_id,
            "entity_id": self.entity_id,
            "url": self.url,
            "signed_manifest": self.signed_manifest,
            "timestamp": self.timestamp,
        })

    @classmethod
    def from_log_dict(cls, d: Dict) -> "SignedListing":
        data = d["data"]
        return cls(
            registry_id=data["registry_id"],
            entity_id=data["entity_id"],
            url=data["url"],
            manifest=data["manifest"],
            signed_manifest=data.get("signed_manifest"),
            timestamp=d["timestamp"],
            signature=data["signature"],
            signature_v2=data.get("signature_v2"),
        )


def verify_signed_listing(
    registry_public_key_hex: str,
    listing: SignedListing,
) -> bool:
    """Verify the registry's signature. Prefers v2 (covers
    signed_manifest); falls back to v1. Never raises."""
    if not HAS_CRYPTO:
        return False
    try:
        if listing.signature_v2 is not None:
            return verify_signature(
                registry_public_key_hex,
                listing.canonical_payload_v2(),
                listing.signature_v2,
            )
        return verify_signature(
            registry_public_key_hex,
            listing.canonical_payload_v1(),
            listing.signature,
        )
    except Exception:
        return False


def verify_listing_world_manifest(listing: SignedListing) -> bool:
    """If the listing carries a signed_manifest, verify the world's
    self-signature on it. Returns True if absent (nothing to verify)
    or if present and valid."""
    if listing.signed_manifest is None:
        return True
    if not HAS_CRYPTO:
        return False
    try:
        sm = SignedManifest.from_dict(listing.signed_manifest)
    except Exception:
        return False
    if sm.entity_id != listing.entity_id:
        return False
    if sm.signed_by != sm.public_key:
        # Not self-signed; listings from C29 are self-signed
        return False
    return verify_manifest_signature(sm, sm.public_key)


def verify_listing(
    registry_public_key_hex: str,
    listing: SignedListing,
) -> bool:
    """Verify both signatures (registry + world manifest). Never raises."""
    return (verify_signed_listing(registry_public_key_hex, listing)
            and verify_listing_world_manifest(listing))


# =====================================================================
# SignedListingRegistry — registry that fetches signed manifests
# =====================================================================

Fetcher = Callable[[str], Optional[Dict]]


def _default_fetch(url: str, timeout: float = 5.0) -> Optional[Dict]:
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


class SignedListingRegistry(SignedMultiverseRegistry):
    """Registry that requires a signed manifest on admission and
    embeds it in signed_listing entries.

    Inherits C17's signing behavior for admissions, acks, and the
    original signed_listing payload. Adds a v2 signature that covers
    the embedded signed_manifest.
    """

    def __init__(self, entity_id: str, name: str,
                 keypair=None,
                 fetcher: Optional[Fetcher] = None,
                 timeout: float = 5.0):
        super().__init__(entity_id, name, keypair)
        self._fetcher = fetcher or (lambda u: _default_fetch(u, timeout))

    # -- override: require signed manifest on URL admission ---------

    def _handle_admit_url(self, timestamp: str, act, entity_url: str):
        from multiverse_c3 import Ack, Refusal

        # Fetch the manifest (raw, as dict)
        try:
            data = self._fetcher(
                entity_url.rstrip("/") + "/manifest")
        except Exception as e:
            return self._refuse(timestamp, act.actor_token,
                                 f"Could not fetch manifest: {e}", "act")
        if not isinstance(data, dict):
            return self._refuse(timestamp, act.actor_token,
                                 "Manifest fetch returned no JSON", "act")

        # Require valid SignedManifest (self-signed on admission)
        try:
            sm = SignedManifest.from_dict(data)
        except (KeyError, ValueError, TypeError) as e:
            return self._refuse(timestamp, act.actor_token,
                                 f"Manifest is not a valid "
                                 f"SignedManifest: {e}", "act")
        if sm.entity_id != data.get("entity_id"):
            return self._refuse(timestamp, act.actor_token,
                                 "Manifest entity_id mismatch", "act")
        if not verify_manifest_signature(sm, sm.public_key):
            return self._refuse(timestamp, act.actor_token,
                                 "Manifest signature INVALID", "act")
        if sm.signed_by != sm.public_key:
            return self._refuse(timestamp, act.actor_token,
                                 "Manifest signed_by != public_key "
                                 "(rotation not supported at admission; "
                                 "client should TOFU/verify separately)",
                                 "act")

        # Already listed?
        if sm.entity_id in self._registry:
            return self._refuse(timestamp, act.actor_token,
                                 f"Entity {sm.entity_id} already listed",
                                 "act")

        # Run conformance (from C17, unchanged) against the URL
        conformance = self._run_conformance(entity_url)
        if not conformance["passed"]:
            return self._refuse(timestamp, act.actor_token,
                                 f"Entity {sm.entity_id} fails conformance",
                                 "act")

        # Accept: register + emit both signature formats
        self._registry[sm.entity_id] = data
        self._conformance_reports[sm.entity_id] = conformance

        # V1 payload (backward compat with C17's client)
        v1_payload = canonical_bytes({
            "kind": "entity_listing",
            "registry_id": self._manifest.entity_id,
            "entity_id": sm.entity_id,
            "url": entity_url,
            "manifest": data,
            "timestamp": timestamp,
        })
        signature_v1 = self._keypair.sign(v1_payload).hex()

        # V2 payload (includes signed_manifest)
        signed_manifest_dict = sm.to_dict()
        v2_payload = canonical_bytes({
            "kind": "entity_listing_with_manifest",
            "registry_id": self._manifest.entity_id,
            "entity_id": sm.entity_id,
            "url": entity_url,
            "signed_manifest": signed_manifest_dict,
            "timestamp": timestamp,
        })
        signature_v2 = self._keypair.sign(v2_payload).hex()

        self._log.append(type(self._log[0])(**{
            "timestamp": timestamp,
            "kind": "signed_listing",
            "actor_token": self._manifest.entity_id,
            "data": {
                "registry_id": self._manifest.entity_id,
                "entity_id": sm.entity_id,
                "url": entity_url,
                "manifest": data,
                "signed_manifest": signed_manifest_dict,
                "signature": signature_v1,
                "signature_v2": signature_v2,
            },
        }))

        # entity_admitted for backward-compat log readers
        self._log.append(type(self._log[0])(**{
            "timestamp": timestamp,
            "kind": "entity_admitted",
            "actor_token": act.actor_token,
            "data": {
                "entity_id": sm.entity_id,
                "manifest": data,
                "conformance": conformance,
                "source_url": entity_url,
            },
        }))

        return Ack(entity_id=self._manifest.entity_id, timestamp=timestamp)

    # -- inherit _handle_admit (in-process path) from parent ---------

    # -- helper -----------------------------------------------------

    def _run_conformance(self, entity_url: str) -> Dict:
        """Same as C17's _http_conformance. Extracted for clarity."""
        import subprocess
        try:
            r = subprocess.run(
                ["python", "-m", "wcp_conformance",
                 "--url", entity_url, "--quiet"],
                capture_output=True, text=True, timeout=30,
            )
            if r.returncode == 0:
                return {"passed": True, "failures": []}
            return {"passed": False, "failures": [r.stdout, r.stderr]}
        except Exception as e:
            return {"passed": False, "failures": [str(e)]}

    def signed_listings(self) -> List[SignedListing]:
        """All signed_listing entries, in log order."""
        out: List[SignedListing] = []
        for entry in self._log:
            if entry.kind != "signed_listing":
                continue
            try:
                out.append(SignedListing.from_log_dict({
                    "timestamp": entry.timestamp,
                    "kind": entry.kind,
                    "data": entry.data,
                }))
            except (KeyError, TypeError):
                continue
        return out


# =====================================================================
# SignedListingClient — fetch log, verify at two layers
# =====================================================================

class SignedListingClient:
    """Fetch the registry's log and verify signed listings.

    Result: a list of SignedListing objects, each verified at both
    the registry level and (if present) the world manifest level.
    """

    def __init__(self, base_url: str, registry_public_key_hex: str,
                 fetcher: Optional[Fetcher] = None,
                 timeout: float = 5.0):
        self._base_url = base_url.rstrip("/")
        self._public_key = registry_public_key_hex
        self._fetcher = fetcher or (
            lambda u: _default_fetch(u, timeout))
        self._verified: Optional[List[SignedListing]] = None
        self._rejected: List[Tuple[SignedListing, str]] = []

    def _fetch_log(self) -> List[Dict]:
        data = self._fetcher(f"{self._base_url}/log")
        if data is None:
            return []
        return data.get("entries", [])

    def _collect(self) -> None:
        if self._verified is not None:
            return
        verified: List[SignedListing] = []
        for raw in self._fetch_log():
            if raw.get("kind") != "signed_listing":
                continue
            try:
                listing = SignedListing.from_log_dict(raw)
            except (KeyError, TypeError):
                continue
            if not verify_signed_listing(self._public_key, listing):
                self._rejected.append(
                    (listing, "registry signature invalid"))
                continue
            if not verify_listing_world_manifest(listing):
                self._rejected.append(
                    (listing, "world manifest signature invalid"))
                continue
            verified.append(listing)
        self._verified = verified

    def list_verified(self) -> List[SignedListing]:
        self._collect()
        return list(self._verified or [])

    def get(self, entity_id: str) -> Optional[SignedListing]:
        for listing in self.list_verified():
            if listing.entity_id == entity_id:
                return listing
        return None

    def get_public_key(self, entity_id: str) -> Optional[str]:
        listing = self.get(entity_id)
        if listing is None:
            return None
        if listing.signed_manifest is None:
            # v1 listing: no key without a fetch
            return None
        pk = listing.signed_manifest.get("public_key")
        if not isinstance(pk, str) or len(pk) != 64:
            return None
        return pk

    def rejected(self) -> List[Tuple[SignedListing, str]]:
        self._collect()
        return list(self._rejected)


# =====================================================================
# ListingKeyResolver — PublicKeyResolver from signed listings
# =====================================================================

class ListingKeyResolver:
    """A PublicKeyResolver (entity_id → public_key) backed by
    SignedListingClient. No HTTP fetch of the world at all.

    Fetches the registry's log on first call; subsequent calls use
    the cached verified listings. Use .fresh() to re-poll.

    Compatible with C15's PassportV2.verify().
    """

    def __init__(self, client: SignedListingClient):
        self._client = client

    def __call__(self, entity_id: str) -> Optional[str]:
        try:
            return self._client.get_public_key(entity_id)
        except Exception:
            return None


# =====================================================================
# Demo: registry vouches for world's key, client verifies without
# contacting the world
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Alice's world serves a signed manifest. Registry fetches it,
    verifies, signs a listing. Client fetches the log, verifies
    registry sig + world sig, gets Alice's key. World goes offline.
    Client still verifies her passport.

    Anchor: Emily Dickinson, 'I never saw a Moor –', public domain.
    """
    import time
    from pathlib import Path
    from multiverse_c1 import create_identity, Identity
    from multiverse_c3 import Petition
    from multiverse_c13 import (
        KeyPair, SignedWorld, SignedAdmission,
    )
    from multiverse_c14 import PermissiveWorld
    from multiverse_c15 import PassportEntry, PassportV2
    from multiverse_c28 import SignedManifestWorld
    from wcp_http_shim import WorldProtocolServer

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    world_kp = KeyPair.generate()
    registry_kp = KeyPair.generate()

    # 1. World with signed manifest + signed responses
    base = PermissiveWorld("world:poetry", "The Poetry World")
    signed_world = SignedWorld(base, world_kp)
    world = SignedManifestWorld(signed_world, world_kp)
    world_server = WorldProtocolServer(world, port=0)
    world_server.serve_in_thread()
    time.sleep(0.1)
    world_url = f"http://127.0.0.1:{world_server._httpd.server_address[1]}"

    # 2. Registry
    registry = SignedListingRegistry(
        "multiverse:main", "Main Multiverse", registry_kp)
    reg_server = WorldProtocolServer(registry, port=0)
    reg_server.serve_in_thread()
    time.sleep(0.1)
    reg_url = f"http://127.0.0.1:{reg_server._httpd.server_address[1]}"

    try:
        # 3. Admit the world (registry fetches + verifies signed manifest)
        import urllib.request as _ur
        def _post(path, body):
            req = _ur.Request(f"{reg_url}{path}",
                               data=json.dumps(body).encode(),
                               headers={"Content-Type":
                                        "application/json"},
                               method="POST")
            with _ur.urlopen(req, timeout=10) as r:
                return json.loads(r.read().decode())
        _post("/petition", {
            "petitioner_token": "admin",
            "petitioner_name": "Admin",
            "passport_admissions": [],
            "message": "setup",
        })
        admit_resp = _post("/act", {
            "actor_token": "admin",
            "type": "multiverse.admit",
            "payload": {"entity_url": world_url},
        })

        # 4. Alice petitions world, captures signed admission
        alice = create_identity("Alice")
        alice_adm = world.petition(Petition(
            petitioner_token=alice.token,
            petitioner_name=alice.name,
            passport_admissions=(),
            message="hi"))
        assert isinstance(alice_adm, SignedAdmission)

        # 5. Build passport
        passport = PassportV2(
            identity=Identity(token=alice.token, name=alice.name),
            entries=(PassportEntry(
                entity_id=alice_adm.entity_id,
                timestamp=alice_adm.timestamp,
                subject_token=alice_adm.subject_token,
                signature=alice_adm.signature,
            ),),
        )

        # 6. Stop the world (client should verify without it)
        world_server.stop()
        world_server = None

        # 7. Client fetches registry log, gets world's key
        client = SignedListingClient(
            reg_url, registry_kp.public_key_hex())
        listing = client.get("world:poetry")
        assert listing is not None
        world_pk = client.get_public_key("world:poetry")
        assert world_pk == world_kp.public_key_hex()

        # 8. Verify passport using ListingKeyResolver (no world fetch)
        resolver = ListingKeyResolver(client)
        passport_report = passport.verify(resolver)

        print("=" * 70)
        print("Signed Manifests in Registry — demo")
        print("=" * 70)
        print(f"  World admitted: {admit_resp.get('kind')}")
        print(f"  World stopped:  (server shut down before verification)")
        print()
        print(f"  Client fetched registry log:")
        print(f"    verified listings: {len(client.list_verified())}")
        print(f"    rejected listings: {len(client.rejected())}")
        print(f"    world's key from listing: {world_pk[:16]}...")
        print()
        print(f"  Passport verification (world offline):")
        print(f"    {passport_report.format()}")
        print()
        print("  Anchor (public domain, Emily Dickinson):")
        print("    'I never saw a Moor –'")
        print("    'I never saw the Sea –'")

        audit = {
            "admit_response_kind": admit_resp.get("kind"),
            "verified_listing_count": len(client.list_verified()),
            "world_public_key": world_pk,
            "passport_verified_without_world": passport_report.all_verified(),
        }
        if artifact_dir:
            path = Path(artifact_dir)
            path.mkdir(parents=True, exist_ok=True)
            (path / "signed_listing_demo.json").write_text(
                json.dumps(audit, indent=2))
            print(f"\n  → {path}/signed_listing_demo.json")
        return audit
    finally:
        if world_server is not None:
            world_server.stop()
        reg_server.stop()
