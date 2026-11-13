"""
multiverse_c21.py — Component 21: Cross-World Provenance.

Ties C15 (PassportV2), C16 (ManifestResolver), and C17 (signed
registry) into a single staged audit trail.

For each admission in a passport, the report shows:
  - Did the registry list this world? (registry stage)
  - Does the listing point to a fetchable URL? (url stage)
  - Did the manifest fetch succeed, with a public_key? (manifest stage)
  - Does the admission's signature verify against that key? (signature stage)

Failures are named by stage. A verifier can distinguish "never
listed" from "forged signature" — the flat verdict (invalid /
unverifiable) from C15 does not.

No new protocol. No new trust primitive. Composition of existing
pieces into a diagnostic artifact.

Honest limits:
  - The report is client-side; it is not signed by the verifier.
    To convince a third party, they run the same verification
    with the same inputs. A signed verification report is future.
  - The registry key is caller-supplied (C17's recursion bottom).
  - No revocation: a world removed from the live registry still
    verifies historically. See test_removed_world_still_verifies.
  - In-process listings (admitted with {"entity": obj}) cannot
    be verified — no URL to fetch a manifest from.
"""

import json
import urllib.request
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from multiverse_c13 import HAS_CRYPTO, canonical_bytes, verify_signature
from multiverse_c15 import PassportEntry, PassportV2
from multiverse_c16 import ManifestResolver
from multiverse_c17 import (
    RegistryEntry, SignedRegistryClient, verify_registry_entry,
)


# =====================================================================
# EntryProvenance — one admission's full audit trail
# =====================================================================

@dataclass
class EntryProvenance:
    entry: PassportEntry
    # Registry stage
    registry_listing: Optional[RegistryEntry] = None
    registry_verified: bool = False
    # URL stage
    listed_url: Optional[str] = None
    # Manifest stage
    manifest_fetched: bool = False
    manifest_public_key: Optional[str] = None
    # Signature stage
    signature_valid: bool = False
    # Final
    verdict: str = "unverified"  # verified | invalid | unverifiable | unverified
    reason: str = ""
    failure_stage: Optional[str] = None  # registry | url | manifest | signature | None

    def to_dict(self) -> Dict:
        return {
            "entity_id": self.entry.entity_id,
            "timestamp": self.entry.timestamp,
            "signed": self.entry.is_signed,
            "registry": {
                "listed": self.registry_listing is not None,
                "verified": self.registry_verified,
                "url": self.listed_url,
            },
            "manifest": {
                "fetched": self.manifest_fetched,
                "public_key": self.manifest_public_key,
            },
            "signature_valid": self.signature_valid,
            "verdict": self.verdict,
            "reason": self.reason,
            "failure_stage": self.failure_stage,
        }


# =====================================================================
# ProvenanceReport — the whole passport's audit
# =====================================================================

@dataclass
class ProvenanceReport:
    passport_token: str
    passport_name: str
    registry_url: str
    entries: List[EntryProvenance] = field(default_factory=list)

    def all_verified(self) -> bool:
        return (bool(self.entries)
                and all(e.verdict == "verified" for e in self.entries))

    def count_by_verdict(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for e in self.entries:
            counts[e.verdict] = counts.get(e.verdict, 0) + 1
        return counts

    def failures(self) -> List[EntryProvenance]:
        return [e for e in self.entries if e.verdict != "verified"]

    def format(self) -> str:
        lines = [
            "=" * 70,
            "Cross-World Provenance Report",
            "=" * 70,
            f"  Passport: {self.passport_token[:16]}... "
            f"({self.passport_name})",
            f"  Registry: {self.registry_url}",
            f"  Entries:  {len(self.entries)}",
            "",
        ]
        for i, e in enumerate(self.entries, 1):
            marker = _verdict_marker(e.verdict)
            lines.append(f"  [{i}] {marker} {e.entry.entity_id}")
            if e.registry_listing is not None:
                reg_note = ("✓ signed_listing verified"
                            if e.registry_verified
                            else "✗ signed_listing INVALID")
                lines.append(f"      Registry:  {reg_note}")
            else:
                lines.append(f"      Registry:  ✗ no listing")
            if e.listed_url:
                lines.append(f"      URL:       {e.listed_url}")
            else:
                lines.append(f"      URL:       —")
            if e.manifest_fetched and e.manifest_public_key:
                lines.append(
                    f"      Manifest:  ✓ public_key="
                    f"{e.manifest_public_key[:16]}...")
            elif e.manifest_fetched:
                lines.append(f"      Manifest:  ✗ fetched, no public_key")
            else:
                lines.append(f"      Manifest:  —")
            if e.entry.is_signed:
                sig_note = ("✓ verified" if e.signature_valid
                            else "✗ INVALID")
                lines.append(f"      Signature: {sig_note}")
            else:
                lines.append(f"      Signature: — (unsigned)")
            lines.append(f"      Verdict:   {e.verdict}"
                         + (f" ({e.failure_stage} stage)"
                            if e.failure_stage else ""))
            if e.reason:
                lines.append(f"      Note:      {e.reason}")
            lines.append("")
        counts = self.count_by_verdict()
        lines.append("  Summary:")
        for verdict in ("verified", "invalid", "unverifiable", "unverified"):
            n = counts.get(verdict, 0)
            if n:
                lines.append(f"    {verdict:12s}: {n}")
        lines.append(f"    all_verified: {self.all_verified()}")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "passport_token": self.passport_token,
            "passport_name": self.passport_name,
            "registry_url": self.registry_url,
            "entries": [e.to_dict() for e in self.entries],
            "counts": self.count_by_verdict(),
            "all_verified": self.all_verified(),
        }


def _verdict_marker(verdict: str) -> str:
    return {"verified": "✓", "invalid": "✗",
            "unverifiable": "?", "unverified": "·"}.get(verdict, "?")


# =====================================================================
# The verifier — staged pipeline
# =====================================================================

Fetcher = Callable[[str], Optional[dict]]


def verify_cross_world_provenance(
    passport: PassportV2,
    registry_url: str,
    registry_public_key_hex: str,
    fetcher: Optional[Fetcher] = None,
    timeout: float = 5.0,
) -> ProvenanceReport:
    """Staged verification of every admission in the passport.

    Returns a ProvenanceReport with per-entry audit trails.
    Does not raise — every failure is captured in a verdict.
    """
    registry = SignedRegistryClient(
        registry_url, registry_public_key_hex, fetcher, timeout)
    manifest = ManifestResolver(fetcher=fetcher, timeout=timeout)

    report = ProvenanceReport(
        passport_token=passport.identity.token,
        passport_name=passport.identity.name,
        registry_url=registry_url,
    )

    for entry in passport.entries:
        report.entries.append(_verify_entry(
            entry, passport.identity.token,
            registry, manifest))

    return report


def _verify_entry(entry: PassportEntry,
                   identity_token: str,
                   registry: SignedRegistryClient,
                   manifest: ManifestResolver) -> EntryProvenance:
    p = EntryProvenance(entry=entry)

    # -- Stage 1: registry listing --
    listing = registry.get_verified(entry.entity_id)
    if listing is None:
        # Distinguish "not present at all" from "present but forged"
        # (the SignedRegistryClient tracks rejected entries).
        rejected = [r for r in registry.rejected()
                    if r.entity_id == entry.entity_id]
        if rejected:
            p.verdict = "invalid"
            p.failure_stage = "registry"
            p.reason = "registry listing failed signature verification"
        else:
            p.verdict = "unverifiable"
            p.failure_stage = "registry"
            p.reason = f"world {entry.entity_id!r} is not listed"
        return p

    p.registry_listing = listing
    p.registry_verified = verify_registry_entry(
        registry._public_key, listing)
    if not p.registry_verified:
        p.verdict = "invalid"
        p.failure_stage = "registry"
        p.reason = "registry listing signature INVALID"
        return p

    # -- Stage 2: URL --
    if not listing.url or listing.url.startswith("in-process:"):
        p.verdict = "unverifiable"
        p.failure_stage = "url"
        p.reason = "listing has no fetchable URL"
        return p
    p.listed_url = listing.url

    # -- Stage 3: manifest --
    manifest.register(entry.entity_id, listing.url)
    pk = manifest(entry.entity_id)
    if pk is None:
        p.verdict = "unverifiable"
        p.failure_stage = "manifest"
        p.reason = "manifest fetch failed or has no public_key"
        return p
    p.manifest_fetched = True
    p.manifest_public_key = pk

    # -- Stage 4: signature --
    if not entry.is_signed:
        p.verdict = "unverified"
        p.failure_stage = None
        p.reason = "entry is unsigned (WCP/0.1 admission)"
        return p
    if entry.subject_token != identity_token:
        p.verdict = "invalid"
        p.failure_stage = "signature"
        p.reason = "subject_token does not match passport identity"
        return p
    if not HAS_CRYPTO:
        p.verdict = "unverifiable"
        p.failure_stage = "signature"
        p.reason = "cryptography not installed"
        return p
    ok = verify_signature(pk, entry.canonical_payload(),
                          entry.signature or "")
    if not ok:
        p.verdict = "invalid"
        p.failure_stage = "signature"
        p.reason = "signature INVALID"
        return p

    p.signature_valid = True
    p.verdict = "verified"
    p.reason = "registry → url → manifest → signature all verified"
    return p


# =====================================================================
# Demo: three signed worlds, one passport, one registry
# =====================================================================

def run_cross_world_demo(
    artifact_dir: Optional[str] = None,
) -> ProvenanceReport:
    """The demo C21 unlocks: one identity, three signed worlds,
    one signed registry, one audit trail."""
    from multiverse_c1 import create_identity
    from multiverse_c3 import Petition
    from multiverse_c13 import SignedWorld
    from multiverse_c14 import PermissiveWorld
    from multiverse_c15 import add_signed_admission
    from multiverse_c17 import SignedMultiverseRegistry
    from wcp_http_shim import WorldProtocolServer
    import time as _t

    if not HAS_CRYPTO:
        raise RuntimeError(
            "provenance demo requires `cryptography`. "
            "Install with: pip install cryptography")

    # 1. Three signed worlds
    worlds = [
        SignedWorld(PermissiveWorld(f"world:{n}", f"World {n.upper()}"))
        for n in ("a", "b", "c")
    ]
    world_servers = []
    for w in worlds:
        s = WorldProtocolServer(w, port=0)
        s.serve_in_thread()
        _t.sleep(0.1)
        url = f"http://127.0.0.1:{s._httpd.server_address[1]}"
        world_servers.append((s, url))

    # 2. One signed registry
    registry = SignedMultiverseRegistry("multiverse:r", "Registry")
    reg_server = WorldProtocolServer(registry, port=0)
    reg_server.serve_in_thread()
    _t.sleep(0.1)
    reg_url = f"http://127.0.0.1:{reg_server._httpd.server_address[1]}"

    try:
        # 3. Admit the three worlds to the registry
        admin_token = "admin:setup"
        _post_http(f"{reg_url}/petition", {
            "petitioner_token": admin_token,
            "petitioner_name": "Admin",
            "passport_admissions": [],
            "message": "setup",
        })
        for (_, wurl) in world_servers:
            _post_http(f"{reg_url}/act", {
                "actor_token": admin_token,
                "type": "multiverse.admit",
                "payload": {"entity_url": wurl},
            })

        # 4. Alice petitions all three worlds
        alice = create_identity("Alice")
        passport = PassportV2.new(alice)
        for (world, (_, wurl)) in zip(worlds, world_servers):
            resp = _post_http(f"{wurl}/petition", {
                "petitioner_token": alice.token,
                "petitioner_name": alice.name,
                "passport_admissions": list(
                    passport.to_plain_entries()),
                "message": f"Let me in to {wurl}.",
            })
            from multiverse_c13 import SignedAdmission
            adm = SignedAdmission(
                entity_id=resp["entity_id"],
                timestamp=resp["timestamp"],
                subject_token=resp["subject_token"],
                signature=resp["signature"],
            )
            passport = add_signed_admission(passport, adm)

        # 5. Verify offline via the registry
        report = verify_cross_world_provenance(
            passport, reg_url, registry.public_key_hex())
        print(report.format())

        # 6. Save artifact if requested
        if artifact_dir:
            from pathlib import Path
            from datetime import datetime, timezone
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            path = Path(artifact_dir) / ts
            path.mkdir(parents=True, exist_ok=True)
            (path / "provenance.json").write_text(
                json.dumps(report.to_dict(), indent=2))
            (path / "provenance.txt").write_text(report.format())
            print(f"\n→ {path}/provenance.json")
            print(f"→ {path}/provenance.txt")

        return report
    finally:
        for (s, _) in world_servers:
            s.stop()
        reg_server.stop()


def _post_http(url: str, body: dict) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read().decode())


if __name__ == "__main__":
    run_cross_world_demo(artifact_dir="artifacts")
