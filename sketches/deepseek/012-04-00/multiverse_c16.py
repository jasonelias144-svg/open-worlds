"""
multiverse_c16.py — Component 16: The Manifest Resolver.

A PublicKeyResolver backed by GET /manifest. Wires C15's passport
verification to real, running worlds without pre-shared keys.

Design:
  - Caller registers `entity_id -> base_url`.
  - On first __call__, the resolver fetches <base_url>/manifest,
    extracts `public_key`, caches the result, and returns it.
  - Subsequent calls return the cached value.
  - Resolvers MUST NOT raise. Any failure returns None.

Contract (C15 relies on this): returning None means "unverifiable",
which is distinct from "invalid". A WCP/0.1 world returns None.
An unknown entity returns None. A network failure returns None.
Only a *forged* signature produces "invalid".

Honest limits:
  - HTTP, not HTTPS. Production MUST use HTTPS with valid certs.
    MITM on the manifest fetch is a real attack; the prototype
    trusts the caller to supply the right URL.
  - Cache is forever. Key rotation requires `clear_cache()`.
  - The URL is caller-supplied. Verifying "this URL is really
    world:a" is out of scope — a signed registry (C17) would
    provide that assertion, and this resolver consumes it.
"""

import json
import urllib.error
import urllib.request
from typing import Callable, Dict, Optional


Fetcher = Callable[[str], Optional[dict]]
# A Fetcher takes a URL and returns the parsed manifest as a dict,
# or None on any failure. The default fetcher uses urllib.


# =====================================================================
# ManifestResolver — the HTTP-backed PublicKeyResolver
# =====================================================================

class ManifestResolver:
    """Fetch and cache public keys from GET /manifest.

    Implements PublicKeyResolver from C15: given an entity_id,
    return its 64-hex public_key or None. Handles three cases:
      - WCP/0.2 world: manifest has `public_key`, returned.
      - WCP/0.1 world: manifest has no `public_key`, returns None.
                    (C15 treats this as "unverifiable" — right.)
      - Fetch failure: returns None, NOT cached, retry next call.
    """

    def __init__(
        self,
        urls: Optional[Dict[str, str]] = None,
        fetcher: Optional[Fetcher] = None,
        timeout: float = 5.0,
    ):
        self._urls: Dict[str, str] = dict(urls) if urls else {}
        # None in the cache is meaningful: "known WCP/0.1, no key"
        self._cache: Dict[str, Optional[str]] = {}
        self._fetcher: Fetcher = fetcher or self._default_fetch
        self._timeout = timeout
        # Diagnostics
        self._fetch_count = 0
        self._cache_hits = 0
        self._misses = 0

    # -- registration -----------------------------------------------

    def register(self, entity_id: str, base_url: str) -> None:
        """Register (or update) the URL for an entity.

        If the URL changes, any cached key is invalidated.
        """
        url = base_url.rstrip("/")
        old = self._urls.get(entity_id)
        self._urls[entity_id] = url
        if old != url:
            self._cache.pop(entity_id, None)

    def unregister(self, entity_id: str) -> None:
        self._urls.pop(entity_id, None)
        self._cache.pop(entity_id, None)

    def clear_cache(self) -> None:
        """Force re-fetch on next call (e.g., after key rotation)."""
        self._cache.clear()

    # -- the resolver call ------------------------------------------

    def __call__(self, entity_id: str) -> Optional[str]:
        # 1. Cache hit (including cached None for WCP/0.1 worlds)
        if entity_id in self._cache:
            self._cache_hits += 1
            return self._cache[entity_id]

        # 2. No URL registered
        url = self._urls.get(entity_id)
        if url is None:
            self._misses += 1
            return None

        # 3. Fetch (never raises — contract for C15)
        manifest = self._fetch(url)
        if manifest is None:
            self._misses += 1
            return None  # NOT cached — retry next call

        # 4. Extract public_key, tolerate malformed entries
        pk = manifest.get("public_key")
        if not isinstance(pk, str) or len(pk) != 64:
            pk = None  # WCP/0.1, or a broken WCP/0.2 manifest

        # 5. Cache: this is a stable fact (signed / unsigned)
        self._cache[entity_id] = pk
        return pk

    # -- fetch ------------------------------------------------------

    def _fetch(self, base_url: str) -> Optional[dict]:
        self._fetch_count += 1
        try:
            return self._fetcher(f"{base_url}/manifest")
        except Exception:
            # Never raise; treat any fetcher crash as a miss
            return None

    def _default_fetch(self, url: str) -> Optional[dict]:
        try:
            with urllib.request.urlopen(
                    url, timeout=self._timeout) as resp:
                return json.loads(resp.read().decode())
        except (urllib.error.URLError, urllib.error.HTTPError,
                json.JSONDecodeError, OSError):
            return None

    # -- diagnostics -------------------------------------------------

    def stats(self) -> dict:
        return {
            "registered": len(self._urls),
            "cached": len(self._cache),
            "fetches": self._fetch_count,
            "cache_hits": self._cache_hits,
            "misses": self._misses,
        }


# =====================================================================
# ChainResolver — try resolvers in order, first non-None wins
# =====================================================================

class ChainResolver:
    """Compose multiple resolvers. First non-None answer wins.

    Typical chain:
      [ManifestResolver(live worlds),
       StaticResolver(pinned keys),
       InMemoryKeyResolver(test fixtures)]

    Used when some worlds are network-reachable and others are
    pinned locally (e.g., a client that has both a live federation
    and a local dev set of worlds it trusts).
    """

    def __init__(self, *resolvers):
        self._resolvers = list(resolvers)

    def append(self, resolver) -> None:
        self._resolvers.append(resolver)

    def __call__(self, entity_id: str) -> Optional[str]:
        for r in self._resolvers:
            try:
                pk = r(entity_id)
            except Exception:
                continue
            if pk is not None:
                return pk
        return None


# =====================================================================
# StaticResolver — pins, for tests and offline usage
# =====================================================================

class StaticResolver:
    """A resolver backed by a fixed dict. No I/O.

    Useful for:
      - Tests where you want to control exactly which keys are known.
      - Pinned trust stores (a client that pins a small set of worlds).
      - A local dev federation where all worlds live on localhost
        and their keys are known ahead of time.
    """

    def __init__(self, keys: Optional[Dict[str, str]] = None):
        self._keys: Dict[str, str] = dict(keys) if keys else {}

    def register(self, entity_id: str, public_key_hex: str) -> None:
        self._keys[entity_id] = public_key_hex

    def __call__(self, entity_id: str) -> Optional[str]:
        return self._keys.get(entity_id)
