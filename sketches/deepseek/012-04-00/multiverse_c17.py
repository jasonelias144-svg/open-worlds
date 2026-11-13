"""
multiverse_c17.py — Component 17: Signed Registries.

A signed registry extends MultiverseRegistry. It signs:

  1. Its admissions and acks (WCP/0.2, compatible with C13/C14).
  2. Every successful listing, as an additional log entry of kind
     'signed_listing', carrying {registry_id, entity_id, url,
     manifest, signature}.

The base 'entity_admitted' log entry is untouched (WCP/0.1
compatible). Signed clients filter for 'signed_listing' and
verify. Unsigned clients ignore the extra entries.

Design:
  - SignedMultiverseRegistry subclasses MultiverseRegistry.
    Overrides only _handle_admit (parent dispatches to parent's
    _handle_admit_url unchanged, so no double-signing).
  - RegistryEntry is the signed listing; from_log_entry /
    from_log_dict reconstruct from a log entry.
  - SignedRegistryClient fetches /log, filters signed_listing,
    verifies signatures, answers get_verified(entity_id).
  - RegistryToKeyResolver composes SignedRegistryClient with
    C16's ManifestResolver: (entity_id) -> public_key. It's a
    PublicKeyResolver compatible with C15's PassportV2.verify().

Honest limits:
  - The registry must be trusted. Its public key comes from
    out-of-band (pin, prior signed listing, C16 fetch of a URL
    the client already trusts). Base case is the client's call.
  - No revocation. Removing an entity from the live registry
    leaves the signed_listing in the log. A fresh client won't
    know to distrust it unless it also sees a 'removed' entry
    (future component: signed_removal).
  - The listing asserts the registry vouched; not that the
    world still exists. Rigorous clients still fetch the
    manifest (RegistryToKeyResolver does).
"""

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

from multiverse_c3 import (
    Manifest, Petition, Act, LogEntry,
    Admission as WCPAdmission, Refusal, Ack,
)
from multiverse_c6 import MultiverseRegistry, manifest_from_dict
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, SignedAdmission, SignedAck,
    canonical_bytes, verify_signature,
)
from multiverse_c16 import ManifestResolver


# =====================================================================
# RegistryEntry — one signed listing
# =====================================================================

@dataclass(frozen=True)
class RegistryEntry:
    """A signed assertion: registry R vouched for entity E at URL U."""
    registry_id: str
    entity_id: str
    url: str
    manifest: Dict           # the world's manifest as a dict
    timestamp: str
    signature: str

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "entity_listing",
            "registry_id": self.registry_id,
            "entity_id": self.entity_id,
            "url": self.url,
            "manifest": self.manifest,
            "timestamp": self.timestamp,
        })

    @classmethod
    def from_log_entry(cls, entry: LogEntry) -> "RegistryEntry":
        d = entry.data
        return cls(
            registry_id=d["registry_id"],
            entity_id=d["entity_id"],
            url=d["url"],
            manifest=d["manifest"],
            timestamp=entry.timestamp,
            signature=d["signature"],
        )

    @classmethod
    def from_log_dict(cls, d: Dict) -> "RegistryEntry":
        data = d["data"]
        return cls(
            registry_id=data["registry_id"],
            entity_id=data["entity_id"],
            url=data["url"],
            manifest=data["manifest"],
            timestamp=d["timestamp"],
            signature=data["signature"],
        )


def verify_registry_entry(public_key_hex: str,
                           entry: RegistryEntry) -> bool:
    if not HAS_CRYPTO:
        return False
    return verify_signature(public_key_hex,
                            entry.canonical_payload(),
                            entry.signature)


# =====================================================================
# SignedMultiverseRegistry
# =====================================================================

class SignedMultiverseRegistry(MultiverseRegistry):
    """A multiverse registry that signs its listings and acks."""

    def __init__(self, entity_id: str, name: str,
                 keypair: Optional[KeyPair] = None):
        super().__init__(entity_id, name)
        self._keypair = keypair or KeyPair.generate()

    # -- WCP/0.2 surface ---------------------------------------------

    def public_key_hex(self) -> str:
        return self._keypair.public_key_hex()

    def manifest_dict(self) -> Dict:
        m = self._manifest
        return {
            "entity_id": m.entity_id,
            "name": m.name,
            "protocol_version": "WCP/0.2",
            "law_url": m.law_url,
            "act_endpoint": m.act_endpoint,
            "log_endpoint": m.log_endpoint,
            "sub_registry_endpoint": m.sub_registry_endpoint,
            "public_key": self._keypair.public_key_hex(),
        }

    def petition(self, petition: Petition):
        response = super().petition(petition)
        if isinstance(response, WCPAdmission):
            payload = canonical_bytes({
                "kind": "admission",
                "entity_id": response.entity_id,
                "timestamp": response.timestamp,
                "subject_token": petition.petitioner_token,
            })
            return SignedAdmission(
                entity_id=response.entity_id,
                timestamp=response.timestamp,
                subject_token=petition.petitioner_token,
                signature=self._keypair.sign(payload).hex(),
            )
        return response

    def act(self, act: Act):
        response = super().act(act)
        if isinstance(response, Ack):
            payload = canonical_bytes({
                "kind": "ack",
                "entity_id": response.entity_id,
                "timestamp": response.timestamp,
                "subject_token": act.actor_token,
            })
            return SignedAck(
                entity_id=response.entity_id,
                timestamp=response.timestamp,
                subject_token=act.actor_token,
                signature=self._keypair.sign(payload).hex(),
            )
        return response

    # -- hook: sign each successful admission -----------------------

    def _handle_admit(self, timestamp: str, act: Act):
        ack = super()._handle_admit(timestamp, act)
        if isinstance(ack, Ack):
            url = act.payload.get("entity_url")  # None for in-process
            self._sign_last_admitted(timestamp, url)
        return ack

    def _sign_last_admitted(self, timestamp: str,
                             url: Optional[str]) -> None:
        for entry in reversed(self._log):
            if entry.kind == "entity_admitted":
                m = entry.data.get("manifest", {})
                entity_id = m.get("entity_id") \
                    if isinstance(m, dict) else None
                if entity_id:
                    final_url = url or f"in-process:{entity_id}"
                    payload = canonical_bytes({
                        "kind": "entity_listing",
                        "registry_id": self._manifest.entity_id,
                        "entity_id": entity_id,
                        "url": final_url,
                        "manifest": m,
                        "timestamp": entry.timestamp,
                    })
                    sig = self._keypair.sign(payload).hex()
                    self._log.append(LogEntry(
                        timestamp=entry.timestamp,
                        kind="signed_listing",
                        actor_token=self._manifest.entity_id,
                        data={
                            "registry_id": self._manifest.entity_id,
                            "entity_id": entity_id,
                            "url": final_url,
                            "manifest": m,
                            "signature": sig,
                        },
                    ))
                return

    # -- signed listing accessor ------------------------------------

    def list_sub_entities_signed(self) -> List[RegistryEntry]:
        out = []
        for entry in self._log:
            if entry.kind == "signed_listing":
                try:
                    out.append(RegistryEntry.from_log_entry(entry))
                except (KeyError, TypeError):
                    continue
        return out


# =====================================================================
# SignedRegistryClient
# =====================================================================

Fetcher = Callable[[str], Optional[dict]]


def _default_fetch(url: str, timeout: float = 5.0) -> Optional[dict]:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


class SignedRegistryClient:
    """Queries a signed registry, verifies listings, caches verified."""

    def __init__(self, base_url: str, registry_public_key_hex: str,
                 fetcher: Optional[Fetcher] = None,
                 timeout: float = 5.0):
        self._base_url = base_url.rstrip("/")
        self._public_key = registry_public_key_hex
        self._fetcher: Fetcher = fetcher or (
            lambda u: _default_fetch(u, timeout))
        self._all_cache: Optional[List[RegistryEntry]] = None
        self._rejected: List[RegistryEntry] = []

    def _fetch_log(self) -> List[Dict]:
        data = self._fetcher(f"{self._base_url}/log")
        if data is None:
            return []
        return data.get("entries", [])

    def _all_verified(self) -> List[RegistryEntry]:
        if self._all_cache is not None:
            return self._all_cache
        verified: List[RegistryEntry] = []
        for raw in self._fetch_log():
            if raw.get("kind") != "signed_listing":
                continue
            try:
                entry = RegistryEntry.from_log_dict(raw)
            except (KeyError, TypeError):
                continue
            if verify_registry_entry(self._public_key, entry):
                verified.append(entry)
            else:
                self._rejected.append(entry)
        self._all_cache = verified
        return verified

    def get_verified(self, entity_id: str) -> Optional[RegistryEntry]:
        for entry in self._all_verified():
            if entry.entity_id == entity_id:
                return entry
        return None

    def list_verified(self) -> List[RegistryEntry]:
        return list(self._all_verified())

    def rejected(self) -> List[RegistryEntry]:
        """Entries present in the log but that failed signature check."""
        self._all_verified()  # ensure we've scanned
        return list(self._rejected)

    def fresh(self) -> "SignedRegistryClient":
        """Return a new client with empty caches (for polling)."""
        return SignedRegistryClient(self._base_url, self._public_key,
                                    self._fetcher)


# =====================================================================
# RegistryToKeyResolver — composes registry + manifest
# =====================================================================

class RegistryToKeyResolver:
    """A PublicKeyResolver that chains registry lookup + manifest fetch.

    Compatible with C15's PassportV2.verify(). Given an entity_id:
      1. Query the signed registry for a verified listing.
      2. Register the listed URL with a ManifestResolver.
      3. Fetch the world's manifest, return its public_key.

    If any step fails, returns None (per the C15 contract).
    """

    def __init__(self, registry_url: str,
                 registry_public_key_hex: str,
                 fetcher: Optional[Fetcher] = None,
                 timeout: float = 5.0):
        self._registry = SignedRegistryClient(
            registry_url, registry_public_key_hex, fetcher, timeout)
        self._manifest = ManifestResolver(fetcher=fetcher, timeout=timeout)

    def __call__(self, entity_id: str) -> Optional[str]:
        entry = self._registry.get_verified(entity_id)
        if entry is None:
            return None
        if not entry.url or entry.url.startswith("in-process:"):
            return None  # no fetchable URL
        self._manifest.register(entity_id, entry.url)
        return self._manifest(entity_id)

    def registry_client(self) -> SignedRegistryClient:
        return self._registry
