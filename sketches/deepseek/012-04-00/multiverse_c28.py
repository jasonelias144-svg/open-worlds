"""
multiverse_c28.py — Component 28: Signed Manifests.

The manifest signature binds "this manifest content" to "the holder
of key K". It is a tamper-detector, not a trust anchor. The client
must have a reason to trust K:
  - from a pin (StaticResolver in a ChainResolver),
  - from a registry listing (C17),
  - or from this component's TOFU store.

Key rotation: a manifest with public_key=K_new and signed_by=K_old,
signed by K_old's private key, is a legitimate rotation. The
resolver verifies against the pinned key (K_old), accepts, and
updates TOFU to K_new. Rotation forgery is caught because
signed_by is in the canonical payload.

Composes with C16 (ManifestResolver's resolver interface) and C15
(PassportV2.verify accepts any PublicKeyResolver).

House rules honored:
  - "A world never raises on what a visitor sends" — resolver
    returns None on any failure, never raises. Tested.
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one test per failure mode: tamper, wrong key,
    wrong entity_id, first-use non-self-signed, MITM swap,
    rotation forgery.
  - "History, not rank" — the manifest is a factual statement
    (endpoints + keys). Nothing here ranks.

Honest limits (documented, tested):
  - Trust anchor is external. The signature proves "K signed
    this". Trusting "K is world:poetry's key" is the caller's
    decision — pin, registry, TOFU. C28 provides TOFU.
  - TOFU is vulnerable on first contact. If an attacker MITMs
    the very first fetch, TOFU pins their key. This is the
    documented weakness of TOFU (same as SSH known_hosts).
    Mitigation: pin out-of-band, or use a registry whose key
    you trust. C28 makes the weakness explicit.
  - No transparency log. If a world silently rotates to an
    attacker's key (both keys under attacker control), the
    client sees a legitimate rotation. Detecting this requires
    an external anchor — a transparency log (Certificate
    Transparency for worlds). Future work.
  - No timestamp verification. Manifest timestamps can be
    backdated. Same as C24/C25/C26.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, Optional, Tuple

from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)


# =====================================================================
# SignedManifest
# =====================================================================

@dataclass(frozen=True)
class SignedManifest:
    """A manifest with a signature over its own content."""
    entity_id: str
    name: str
    protocol_version: str
    law_url: str
    act_endpoint: str
    log_endpoint: str
    sub_registry_endpoint: Optional[str]
    public_key: str     # the current key (signs future manifests)
    signed_by: str      # the key that signed THIS manifest
    signature: str

    def __post_init__(self):
        for f in ("entity_id", "name", "protocol_version",
                  "law_url", "act_endpoint", "log_endpoint",
                  "public_key", "signed_by", "signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if len(self.public_key) != 64:
            raise ValueError("public_key must be 64 hex chars")
        if len(self.signed_by) != 64:
            raise ValueError("signed_by must be 64 hex chars")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "signed_manifest",
            "entity_id": self.entity_id,
            "name": self.name,
            "protocol_version": self.protocol_version,
            "law_url": self.law_url,
            "act_endpoint": self.act_endpoint,
            "log_endpoint": self.log_endpoint,
            "sub_registry_endpoint": self.sub_registry_endpoint,
            "public_key": self.public_key,
            "signed_by": self.signed_by,
        })

    def to_dict(self) -> Dict:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "protocol_version": self.protocol_version,
            "law_url": self.law_url,
            "act_endpoint": self.act_endpoint,
            "log_endpoint": self.log_endpoint,
            "sub_registry_endpoint": self.sub_registry_endpoint,
            "public_key": self.public_key,
            "signed_by": self.signed_by,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "SignedManifest":
        return cls(
            entity_id=d["entity_id"],
            name=d["name"],
            protocol_version=d["protocol_version"],
            law_url=d["law_url"],
            act_endpoint=d["act_endpoint"],
            log_endpoint=d["log_endpoint"],
            sub_registry_endpoint=d.get("sub_registry_endpoint"),
            public_key=d["public_key"],
            signed_by=d["signed_by"],
            signature=d["signature"],
        )


# =====================================================================
# Sign / verify
# =====================================================================

def sign_manifest(
    manifest_dict: Dict,
    keypair: KeyPair,
    signed_by: Optional[str] = None,
) -> SignedManifest:
    """Sign a manifest.

    signed_by defaults to the manifest's own public_key (self-signed,
    no rotation). For rotation, pass signed_by = the OLD public_key —
    which must equal keypair's public key.
    """
    if not HAS_CRYPTO:
        raise RuntimeError(
            "sign_manifest requires `cryptography`. "
            "Install with: pip install cryptography")
    public_key = manifest_dict.get("public_key")
    if not isinstance(public_key, str) or len(public_key) != 64:
        raise ValueError(
            "manifest_dict must have a 64-hex public_key")
    if signed_by is None:
        signed_by = public_key
    if keypair.public_key_hex() != signed_by:
        raise ValueError(
            f"keypair's public key ({keypair.public_key_hex()[:16]}...) "
            f"does not match signed_by ({signed_by[:16]}...); "
            f"the keypair must sign with the key claimed as signed_by")
    payload = canonical_bytes({
        "kind": "signed_manifest",
        "entity_id": manifest_dict["entity_id"],
        "name": manifest_dict["name"],
        "protocol_version": manifest_dict["protocol_version"],
        "law_url": manifest_dict["law_url"],
        "act_endpoint": manifest_dict["act_endpoint"],
        "log_endpoint": manifest_dict["log_endpoint"],
        "sub_registry_endpoint": manifest_dict.get(
            "sub_registry_endpoint"),
        "public_key": public_key,
        "signed_by": signed_by,
    })
    return SignedManifest(
        entity_id=manifest_dict["entity_id"],
        name=manifest_dict["name"],
        protocol_version=manifest_dict["protocol_version"],
        law_url=manifest_dict["law_url"],
        act_endpoint=manifest_dict["act_endpoint"],
        log_endpoint=manifest_dict["log_endpoint"],
        sub_registry_endpoint=manifest_dict.get(
            "sub_registry_endpoint"),
        public_key=public_key,
        signed_by=signed_by,
        signature=keypair.sign(payload).hex(),
    )


def verify_manifest_signature(
    signed_manifest: SignedManifest,
    expected_pubkey_hex: str,
) -> bool:
    """True iff the signature verifies against expected_pubkey_hex.
    Never raises."""
    if not HAS_CRYPTO:
        return False
    try:
        return verify_signature(
            expected_pubkey_hex,
            signed_manifest.canonical_payload(),
            signed_manifest.signature,
        )
    except Exception:
        return False


# =====================================================================
# TOFUStore
# =====================================================================

@dataclass
class TOFUStore:
    """Trust-on-first-use. Records (entity_id → pinned public_key)."""
    keys: Dict[str, str] = field(default_factory=dict)
    first_seen: Dict[str, str] = field(default_factory=dict)

    def check(self, entity_id: str) -> Optional[str]:
        return self.keys.get(entity_id)

    def record(self, entity_id: str, public_key: str,
               timestamp: Optional[str] = None) -> None:
        if timestamp is None:
            timestamp = datetime.now(timezone.utc).isoformat()
        self.keys[entity_id] = public_key
        self.first_seen.setdefault(entity_id, timestamp)

    def update_for_rotation(self, entity_id: str,
                             new_public_key: str) -> None:
        self.keys[entity_id] = new_public_key
        # first_seen stays as the ORIGINAL timestamp

    def to_dict(self) -> Dict:
        return {"keys": dict(self.keys),
                "first_seen": dict(self.first_seen)}

    @classmethod
    def from_dict(cls, d: Dict) -> "TOFUStore":
        s = cls()
        s.keys.update(d.get("keys", {}))
        s.first_seen.update(d.get("first_seen", {}))
        return s


# =====================================================================
# Fetch result
# =====================================================================

@dataclass(frozen=True)
class ManifestFetchResult:
    accepted: bool
    public_key: Optional[str]
    reason: str
    rotation: bool = False
    first_use: bool = False


# =====================================================================
# SignedManifestResolver
# =====================================================================

Fetcher = Callable[[str], Optional[Dict]]


def _default_fetch(url: str, timeout: float = 5.0) -> Optional[Dict]:
    import urllib.request
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


class SignedManifestResolver:
    """PublicKeyResolver backed by signed manifests with TOFU.

    On __call__(entity_id):
      1. Fetch <url>/manifest (registered via `register`).
      2. Parse as SignedManifest.
      3. Verify `entity_id` matches the request.
      4. If TOFU has no pin: require self-signature, pin on success.
      5. If TOFU has a pin: verify signature against the pin.
         - `signed_by == pinned` and `public_key == pinned`: no rotation.
         - `signed_by == pinned` and `public_key != pinned`: rotation.
         - `signed_by != pinned`: reject (manifest signed by
           untrusted key).
      6. Return the (possibly updated) public_key, or None on failure.

    Never raises.
    """

    def __init__(
        self,
        urls: Optional[Dict[str, str]] = None,
        tofu: Optional[TOFUStore] = None,
        fetcher: Optional[Fetcher] = None,
        timeout: float = 5.0,
    ):
        self._urls: Dict[str, str] = dict(urls) if urls else {}
        self._tofu = tofu or TOFUStore()
        self._fetcher = fetcher or (
            lambda u: _default_fetch(u, timeout))
        self._last_result: Dict[str, ManifestFetchResult] = {}

    def register(self, entity_id: str, base_url: str) -> None:
        self._urls[entity_id] = base_url.rstrip("/")

    def unregister(self, entity_id: str) -> None:
        self._urls.pop(entity_id, None)

    def tofu(self) -> TOFUStore:
        return self._tofu

    def last_result(self, entity_id: str) -> Optional[ManifestFetchResult]:
        return self._last_result.get(entity_id)

    def __call__(self, entity_id: str) -> Optional[str]:
        result = self._fetch_and_verify(entity_id)
        self._last_result[entity_id] = result
        return result.public_key if result.accepted else None

    def _fetch_and_verify(self, entity_id: str) -> ManifestFetchResult:
        url = self._urls.get(entity_id)
        if url is None:
            return ManifestFetchResult(
                accepted=False, public_key=None,
                reason=f"no URL registered for {entity_id!r}")

        try:
            data = self._fetcher(f"{url}/manifest")
        except Exception as e:
            return ManifestFetchResult(
                accepted=False, public_key=None,
                reason=f"fetcher raised: {e}")
        if data is None:
            return ManifestFetchResult(
                accepted=False, public_key=None,
                reason="fetcher returned no data")

        try:
            sm = SignedManifest.from_dict(data)
        except (KeyError, ValueError, TypeError) as e:
            return ManifestFetchResult(
                accepted=False, public_key=None,
                reason=f"malformed signed manifest: {e}")

        if sm.entity_id != entity_id:
            return ManifestFetchResult(
                accepted=False, public_key=None,
                reason=(f"manifest entity_id {sm.entity_id!r} "
                        f"!= requested {entity_id!r}"))

        pinned = self._tofu.check(entity_id)

        if pinned is None:
            # First use: must be self-signed (signed_by == public_key)
            if sm.signed_by != sm.public_key:
                return ManifestFetchResult(
                    accepted=False, public_key=None,
                    reason=("first contact with non-self-signed "
                            "manifest; cannot authenticate the "
                            "chain without a trust anchor"))
            if not verify_manifest_signature(sm, sm.public_key):
                return ManifestFetchResult(
                    accepted=False, public_key=None,
                    reason="self-signature INVALID")
            self._tofu.record(entity_id, sm.public_key)
            return ManifestFetchResult(
                accepted=True, public_key=sm.public_key,
                reason="first use (TOFU-pinned)",
                first_use=True)

        # Have a pin. Verify signature against pinned key.
        if not verify_manifest_signature(sm, pinned):
            return ManifestFetchResult(
                accepted=False, public_key=None,
                reason="signature does not verify against "
                        "TOFU-pinned key")
        if sm.signed_by != pinned:
            return ManifestFetchResult(
                accepted=False, public_key=None,
                reason="manifest signed_by does not match the "
                        "TOFU-pinned key")
        if sm.public_key == pinned:
            return ManifestFetchResult(
                accepted=True, public_key=sm.public_key,
                reason="signature verified, no rotation")
        # Rotation
        self._tofu.update_for_rotation(entity_id, sm.public_key)
        return ManifestFetchResult(
            accepted=True, public_key=sm.public_key,
            reason=(f"key rotation: {pinned[:16]} → "
                    f"{sm.public_key[:16]}"),
            rotation=True)


# =====================================================================
# SignedManifestWorld — wraps any world, serves a signed manifest
# =====================================================================

class SignedManifestWorld:
    """Wraps any world; serves a self-signed manifest via
    manifest_dict(). Delegates all other methods to the wrapped
    world.

    To have both a signed manifest AND signed responses, wrap a
    SignedWorld (C13): the SignedWorld handles responses, this
    wrapper handles the manifest, both use the same keypair.
    """

    def __init__(self, base, keypair: KeyPair):
        self.base = base
        self.keypair = keypair
        base_dict = self._base_manifest_dict()
        self._signed_manifest = sign_manifest(
            {**base_dict,
             "public_key": keypair.public_key_hex()},
            keypair,
        )

    def _base_manifest_dict(self) -> Dict:
        m = self.base.manifest()
        return {
            "entity_id": m.entity_id,
            "name": m.name,
            "protocol_version": "WCP/0.2",
            "law_url": m.law_url,
            "act_endpoint": m.act_endpoint,
            "log_endpoint": m.log_endpoint,
            "sub_registry_endpoint": m.sub_registry_endpoint,
        }

    def manifest_dict(self) -> Dict:
        return self._signed_manifest.to_dict()

    def __getattr__(self, name):
        return getattr(self.base, name)


# =====================================================================
# Demo: TOFU + MITM rejection + rotation
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Alice runs a world with keypair K1. Client TOFU-pins K1 on
    first contact. Attacker tries to substitute a manifest — rejected
    by signature. Alice rotates to K2, signed by K1 — accepted, TOFU
    updated. Post-rotation, the pinned key is K2.

    Anchor: Emily Dickinson, 'The Soul selects her own Society –',
    public domain.
    """
    from pathlib import Path
    from multiverse_c14 import PermissiveWorld

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    k1 = KeyPair.generate()
    k2 = KeyPair.generate()
    attacker_kp = KeyPair.generate()

    # Alice's world with key K1
    base = PermissiveWorld("world:poetry", "The Poetry World")
    world_v1 = SignedManifestWorld(base, k1)
    manifest_v1 = world_v1.manifest_dict()

    # --- Step 1: First contact (TOFU pins K1) ---
    def fetcher_v1(url: str) -> Optional[Dict]:
        return manifest_v1 if url.endswith("/manifest") else None

    resolver_1 = SignedManifestResolver(
        {"world:poetry": "http://poetry.example"},
        fetcher=fetcher_v1,
    )
    pk_1 = resolver_1("world:poetry")
    result_1 = resolver_1.last_result("world:poetry")

    # --- Step 2: Attacker tries to serve a different manifest ---
    attacker_manifest = {
        "entity_id": "world:poetry",
        "name": "The Poetry World",
        "protocol_version": "WCP/0.2",
        "law_url": "http://attacker.example/law",
        "act_endpoint": "http://attacker.example/act",
        "log_endpoint": "http://attacker.example/log",
        "sub_registry_endpoint": None,
        "public_key": attacker_kp.public_key_hex(),
        "signed_by": attacker_kp.public_key_hex(),
        "signature": "",  # will be filled below
    }
    attacker_manifest["signature"] = attacker_kp.sign(
        canonical_bytes({
            "kind": "signed_manifest",
            "entity_id": "world:poetry",
            "name": "The Poetry World",
            "protocol_version": "WCP/0.2",
            "law_url": "http://attacker.example/law",
            "act_endpoint": "http://attacker.example/act",
            "log_endpoint": "http://attacker.example/log",
            "sub_registry_endpoint": None,
            "public_key": attacker_kp.public_key_hex(),
            "signed_by": attacker_kp.public_key_hex(),
        })).hex()

    def fetcher_attacker(url: str) -> Optional[Dict]:
        return attacker_manifest if url.endswith("/manifest") else None

    resolver_2 = SignedManifestResolver(
        {"world:poetry": "http://poetry.example"},
        tofu=resolver_1.tofu(),
        fetcher=fetcher_attacker,
    )
    pk_2 = resolver_2("world:poetry")
    result_2 = resolver_2.last_result("world:poetry")

    # --- Step 3: Legitimate rotation K1 → K2, signed by K1 ---
    rotation_manifest = sign_manifest(
        {
            "entity_id": "world:poetry",
            "name": "The Poetry World",
            "protocol_version": "WCP/0.2",
            "law_url": "http://poetry.example/law",
            "act_endpoint": "http://poetry.example/act",
            "log_endpoint": "http://poetry.example/log",
            "sub_registry_endpoint": None,
            "public_key": k2.public_key_hex(),
        },
        k1,  # signed by OLD key
        signed_by=k1.public_key_hex(),
    ).to_dict()

    def fetcher_rotation(url: str) -> Optional[Dict]:
        return rotation_manifest if url.endswith("/manifest") else None

    resolver_3 = SignedManifestResolver(
        {"world:poetry": "http://poetry.example"},
        tofu=resolver_2.tofu(),
        fetcher=fetcher_rotation,
    )
    pk_3 = resolver_3("world:poetry")
    result_3 = resolver_3.last_result("world:poetry")

    print("=" * 70)
    print("Signed Manifests — demo")
    print("=" * 70)
    print()
    print("  Step 1: First contact (self-signed, TOFU-pin)")
    print(f"    accepted: {result_1.accepted}")
    print(f"    reason:   {result_1.reason}")
    print(f"    public_key: {(pk_1 or '')[:16]}...")
    print()
    print("  Step 2: Attacker serves a different manifest")
    print(f"    accepted: {result_2.accepted}")
    print(f"    reason:   {result_2.reason}")
    print(f"    public_key: {pk_2 or '(rejected)'}")
    print()
    print("  Step 3: Legitimate rotation K1 → K2, signed by K1")
    print(f"    accepted: {result_3.accepted}")
    print(f"    reason:   {result_3.reason}")
    print(f"    rotation: {result_3.rotation}")
    print(f"    public_key: {(pk_3 or '')[:16]}...")
    print(f"    (was: {(pk_1 or '')[:16]}...)")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'The Soul selects her own Society –'")
    print("    'Then – shuts the Door –'")

    audit = {
        "step_1_first_contact": {
            "accepted": result_1.accepted,
            "public_key": pk_1,
            "reason": result_1.reason,
        },
        "step_2_attacker": {
            "accepted": result_2.accepted,
            "public_key": pk_2,
            "reason": result_2.reason,
        },
        "step_3_rotation": {
            "accepted": result_3.accepted,
            "public_key": pk_3,
            "rotation": result_3.rotation,
            "reason": result_3.reason,
        },
    }

    if artifact_dir:
        path = Path(artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "signed_manifest_demo.json").write_text(
            json.dumps(audit, indent=2))
        print(f"\n  → {path}/signed_manifest_demo.json")

    return audit
