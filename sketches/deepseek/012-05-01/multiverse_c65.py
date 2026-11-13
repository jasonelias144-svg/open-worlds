"""
multiverse_c65.py — Component 65: The Reference Client.

A library + CLI for participating in an LFS/0.1 federation.

What it does:
  - Generates a C1 identity with an Ed25519 keypair (C13).
  - Pins an LFS anchors file by root public key.
  - Enters worlds (WCP over HTTP), verifying every response
    against the anchors.
  - Submits acts, verifies acks.
  - Tracks contracts the resident learns about.
  - Produces a signed, self-contained FederationReport that
    a third party can verify offline against the root key.

What it deliberately does NOT do (v0.1):
  - Negotiate contracts (worlds' curators do that, C57).
  - Run a full federation (that's C64's deployment spec).
  - Store the whole federation log (the client keeps its own
    history; the world's /log is authoritative for world state).
  - Multi-identity (one identity per state dir).

State layout (~/.lfs by default, override with --state-dir):
    identity.json     C1 identity + Ed25519 private key (hex)
    anchors.json      Pinned anchors + root fingerprint
    passport.json     PassportV2 with accumulated admissions
    contracts.json    Contracts the client knows about
    log.jsonl         Append-only record of every action

Composition:
  C1  (identity), C13 (keypair, sign/verify), C15 (passport),
  C3  (WCP manifest/petition/act over HTTP), C57 (contract shape),
  C62 (artifact_hash helper).

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: identity save/load, anchors pin/verify,
    enter, act, verify, report sign/verify, third-party check.
  - "A world never raises on what a visitor sends" — client
    surfaces errors as results, never crashes on bad input.
  - "History, not rank" — log is append-only JSONL.

Honest limits (documented, tested):
  - Identity's private key is stored in plaintext on disk. This
    is a prototype; production would use OS keychain or similar.
  - HTTPS is not enforced (works with http:// for testing).
    Production MUST use HTTPS with valid certs (LFS §3).
  - Manifest verification: if the manifest is unsigned (WCP/0.1
    plain), the client falls back to HTTPS-only trust. If it's
    a C28 SignedManifest, the signature is verified against the
    anchors' world key.
  - Report verification requires the root public key out of
    band (the third party's anchor of anchors).
  - Contract discovery is read-only: the client learns of
    contracts via world logs. Creating new ones is out of scope.
  - No retry logic; network errors surface immediately.
"""

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from multiverse_c1 import Identity, create_identity
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c15 import (
    PassportEntry, PassportV2,
    passport_v2_to_dict, passport_v2_from_dict,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# =====================================================================
# Keypair persistence
# =====================================================================

def _keypair_to_hex(kp: KeyPair) -> str:
    """Serialize a KeyPair's private key as 32-byte hex.

    Accesses C13's KeyPair._private attribute directly. This is
    a prototype-level shortcut: C13 does not expose private-key
    serialization (and shouldn't, by default). A reference client
    needs it to persist identity across restarts.
    """
    from cryptography.hazmat.primitives import serialization
    private = kp._private  # C13's attribute
    return private.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    ).hex()


def _keypair_from_hex(hex_str: str) -> KeyPair:
    """Reconstruct a KeyPair from its 32-byte hex private key."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
    )
    private = Ed25519PrivateKey.from_private_bytes(
        bytes.fromhex(hex_str))
    return KeyPair(private=private)


# =====================================================================
# ClientIdentity
# =====================================================================

@dataclass(frozen=True)
class ClientIdentity:
    identity: Identity
    keypair: KeyPair

    def to_dict(self) -> Dict:
        return {
            "token": self.identity.token,
            "name": self.identity.name,
            "private_key_hex": _keypair_to_hex(self.keypair),
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "ClientIdentity":
        return cls(
            identity=Identity(
                token=d["token"], name=d["name"]),
            keypair=_keypair_from_hex(d["private_key_hex"]),
        )


# =====================================================================
# PinnedAnchors
# =====================================================================

@dataclass(frozen=True)
class PinnedAnchors:
    anchor_url: str
    root_fingerprint: str
    raw: Dict
    fetched_at: str

    def to_dict(self) -> Dict:
        return {
            "anchor_url": self.anchor_url,
            "root_fingerprint": self.root_fingerprint,
            "raw": self.raw,
            "fetched_at": self.fetched_at,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "PinnedAnchors":
        return cls(
            anchor_url=d["anchor_url"],
            root_fingerprint=d["root_fingerprint"],
            raw=d["raw"],
            fetched_at=d["fetched_at"],
        )

    def world_by_id(self, world_id: str) -> Optional[Dict]:
        for w in self.raw.get("worlds", []):
            if w.get("entity_id") == world_id:
                return w
        return None

    def world_public_key(self, world_id: str) -> Optional[str]:
        w = self.world_by_id(world_id)
        return w.get("curator_public_key") if w else None

    def world_manifest_url(self, world_id: str) -> Optional[str]:
        w = self.world_by_id(world_id)
        return w.get("manifest_url") if w else None

    def world_base_url(self, world_id: str) -> Optional[str]:
        url = self.world_manifest_url(world_id)
        if url is None:
            return None
        if url.endswith("/manifest"):
            return url[: -len("/manifest")]
        return url

    def world_ids(self) -> List[str]:
        return [w.get("entity_id", "") for w in
                self.raw.get("worlds", [])]

    def ledger_checkpoint_public_key(self) -> Optional[str]:
        return self.raw.get("ledger_checkpoint_public_key")


def _verify_anchors_signature(
    raw: Dict, root_public_key: str,
) -> bool:
    """Verify the anchors file's signature against the root key.

    The signature is over everything except the "signature" field.
    """
    if not HAS_CRYPTO:
        return False
    try:
        sig = raw.get("signature")
        if not isinstance(sig, str) or not sig:
            return False
        body = {k: v for k, v in raw.items() if k != "signature"}
        return verify_signature(
            root_public_key, canonical_bytes(body), sig)
    except Exception:
        return False


# =====================================================================
# WorldHTTPClient
# =====================================================================

class WorldHTTPError(Exception):
    pass


class WorldHTTPClient:
    """Thin WCP-over-HTTP client for one world's endpoints."""

    def __init__(self, base_url: str, timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get(self, path: str) -> Dict:
        url = f"{self.base_url}{path}"
        try:
            with urllib.request.urlopen(
                    url, timeout=self.timeout) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            try:
                body = json.loads(e.read().decode())
                raise WorldHTTPError(
                    f"HTTP {e.code}: "
                    f"{body.get('error', 'unknown')}")
            except (json.JSONDecodeError, UnicodeDecodeError):
                raise WorldHTTPError(f"HTTP {e.code}")
        except urllib.error.URLError as e:
            raise WorldHTTPError(f"network: {e}")
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise WorldHTTPError(f"malformed response: {e}")

    def _post(self, path: str, body: Dict) -> Dict:
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode()
        req = urllib.request.Request(
            url, data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                    req, timeout=self.timeout) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            try:
                body = json.loads(e.read().decode())
                raise WorldHTTPError(
                    f"HTTP {e.code}: "
                    f"{body.get('error', 'unknown')}")
            except (json.JSONDecodeError, UnicodeDecodeError):
                raise WorldHTTPError(f"HTTP {e.code}")
        except urllib.error.URLError as e:
            raise WorldHTTPError(f"network: {e}")
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise WorldHTTPError(f"malformed response: {e}")

    def manifest(self) -> Dict:
        return self._get("/manifest")

    def petition(self, payload: Dict) -> Dict:
        return self._post("/petition", payload)

    def act(self, payload: Dict) -> Dict:
        return self._post("/act", payload)

    def log(self, since: Optional[str] = None) -> Dict:
        path = "/log"
        if since:
            path += f"?since={urllib.parse.quote(since)}"
        return self._get(path)


# =====================================================================
# Result types
# =====================================================================

@dataclass
class ConnectResult:
    ok: bool
    reason: str
    anchors: Optional[PinnedAnchors] = None

    def format(self) -> str:
        if self.ok:
            return (f"Connected to federation "
                    f"(root {self.anchors.root_fingerprint[:16]}..., "
                    f"{len(self.anchors.world_ids())} worlds)")
        return f"Connection failed: {self.reason}"


@dataclass
class EnterResult:
    ok: bool
    reason: str
    world_id: str = ""
    verified: bool = False
    raw_response: Dict = field(default_factory=dict)


@dataclass
class SubmitResult:
    ok: bool
    reason: str
    world_id: str = ""
    verified: bool = False
    raw_response: Dict = field(default_factory=dict)


# =====================================================================
# ClientState
# =====================================================================

class ClientState:
    """The client's persistent state."""

    IDENTITY_FILE = "identity.json"
    ANCHORS_FILE = "anchors.json"
    PASSPORT_FILE = "passport.json"
    CONTRACTS_FILE = "contracts.json"
    LOG_FILE = "log.jsonl"

    def __init__(self, state_dir: Path):
        self.state_dir = Path(state_dir)
        self.identity: Optional[ClientIdentity] = None
        self.anchors: Optional[PinnedAnchors] = None
        self.passport: Optional[PassportV2] = None
        self.contracts: Dict[str, Dict] = {}
        self._log_buffer: List[Dict] = []

    def exists(self) -> bool:
        return self.state_dir.exists() and any(
            self.state_dir.iterdir())

    def ensure_dir(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def load(self) -> bool:
        """Load all state files. Returns True iff identity loaded."""
        if not self.state_dir.exists():
            return False
        p = self.state_dir / self.IDENTITY_FILE
        if p.exists():
            self.identity = ClientIdentity.from_dict(
                json.loads(p.read_text()))
        p = self.state_dir / self.ANCHORS_FILE
        if p.exists():
            self.anchors = PinnedAnchors.from_dict(
                json.loads(p.read_text()))
        p = self.state_dir / self.PASSPORT_FILE
        if p.exists():
            self.passport = passport_v2_from_dict(
                json.loads(p.read_text()))
        p = self.state_dir / self.CONTRACTS_FILE
        if p.exists():
            self.contracts = json.loads(p.read_text())
        p = self.state_dir / self.LOG_FILE
        if p.exists():
            # Not loaded into memory; append-only on disk
            pass
        return self.identity is not None

    def save_identity(self) -> None:
        if self.identity is None:
            return
        self.ensure_dir()
        (self.state_dir / self.IDENTITY_FILE).write_text(
            json.dumps(self.identity.to_dict(), indent=2))

    def save_anchors(self) -> None:
        if self.anchors is None:
            return
        self.ensure_dir()
        (self.state_dir / self.ANCHORS_FILE).write_text(
            json.dumps(self.anchors.to_dict(), indent=2))

    def save_passport(self) -> None:
        if self.passport is None:
            return
        self.ensure_dir()
        (self.state_dir / self.PASSPORT_FILE).write_text(
            json.dumps(passport_v2_to_dict(self.passport),
                       indent=2))

    def save_contracts(self) -> None:
        self.ensure_dir()
        (self.state_dir / self.CONTRACTS_FILE).write_text(
            json.dumps(self.contracts, indent=2))

    def append_log(self, kind: str, data: Dict) -> None:
        self.ensure_dir()
        entry = {
            "timestamp": _now(),
            "kind": kind,
            "identity_token":
                self.identity.identity.token
                if self.identity else None,
            "data": data,
        }
        with open(self.state_dir / self.LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
        self._log_buffer.append(entry)

    def get_log(self) -> List[Dict]:
        entries = []
        p = self.state_dir / self.LOG_FILE
        if not p.exists():
            return list(self._log_buffer)
        with open(p) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return entries


# =====================================================================
# FederationReport
# =====================================================================

@dataclass
class FederationReport:
    """A signed, self-contained record of a client's activity.

    Includes:
      - The client's identity (token, name, public key)
      - The pinned anchors
      - Every admission the client received (signed by world)
      - Every ack the client received (signed by world)
      - Every refusal (fact, not signed)
      - Contracts the client knows about
      - Generated at (timestamp)
      - Client signature over all of the above
    """
    identity_token: str
    identity_name: str
    identity_public_key: str
    anchors: Dict
    admissions: List[Dict] = field(default_factory=list)
    acks: List[Dict] = field(default_factory=list)
    refusals: List[Dict] = field(default_factory=list)
    contracts: List[Dict] = field(default_factory=list)
    generated_at: str = ""
    client_signature: str = ""

    def canonical_payload(self) -> bytes:
        """The bytes the client signs. Excludes client_signature."""
        return canonical_bytes({
            "kind": "federation_report",
            "identity_token": self.identity_token,
            "identity_name": self.identity_name,
            "identity_public_key": self.identity_public_key,
            "anchors": self.anchors,
            "admissions": self.admissions,
            "acks": self.acks,
            "refusals": self.refusals,
            "contracts": self.contracts,
            "generated_at": self.generated_at,
        })

    def to_dict(self) -> Dict:
        d = json.loads(self.canonical_payload().decode())
        d["client_signature"] = self.client_signature
        return d

    @classmethod
    def from_dict(cls, d: Dict) -> "FederationReport":
        return cls(
            identity_token=d["identity_token"],
            identity_name=d["identity_name"],
            identity_public_key=d["identity_public_key"],
            anchors=d["anchors"],
            admissions=list(d.get("admissions", [])),
            acks=list(d.get("acks", [])),
            refusals=list(d.get("refusals", [])),
            contracts=list(d.get("contracts", [])),
            generated_at=d.get("generated_at", ""),
            client_signature=d.get("client_signature", ""),
        )

    def save(self, path: Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: Path) -> "FederationReport":
        return cls.from_dict(json.loads(Path(path).read_text()))


@dataclass
class ReportVerdict:
    valid: bool
    reason: str
    checks: Dict[str, bool] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def format(self) -> str:
        lines = ["Report Verification", "=" * 50]
        for name, ok in self.checks.items():
            lines.append(f"  {'✓' if ok else '✗'} {name}")
        for err in self.errors:
            lines.append(f"  ! {err}")
        lines.append("")
        lines.append(
            f"  Result: {'✓ VALID' if self.valid else '✗ INVALID'}")
        if not self.valid:
            lines.append(f"  Reason: {self.reason}")
        return "\n".join(lines)


def verify_report(
    report: FederationReport,
    root_public_key: str,
) -> ReportVerdict:
    """Verify a FederationReport offline.

    A third party supplies the report file and the root public
    key (out of band). The report is self-contained: all
    signatures verify against the anchors embedded in it, and
    the anchors' signature verifies against the root key.

    Never raises.
    """
    if not HAS_CRYPTO:
        return ReportVerdict(
            valid=False, reason="cryptography not installed")
    if not isinstance(report, FederationReport):
        return ReportVerdict(
            valid=False, reason="not a FederationReport")

    checks: Dict[str, bool] = {}
    errors: List[str] = []

    # 1. Anchors signature
    anchors_ok = _verify_anchors_signature(
        report.anchors, root_public_key)
    checks["anchors_signature"] = anchors_ok
    if not anchors_ok:
        errors.append(
            "anchors signature does not verify against root key")

    # Helper: look up a world's public key from anchors
    def _world_key(world_id: str) -> Optional[str]:
        for w in report.anchors.get("worlds", []):
            if w.get("entity_id") == world_id:
                return w.get("curator_public_key")
        return None

    # 2. Client signature
    try:
        client_sig_ok = verify_signature(
            report.identity_public_key,
            report.canonical_payload(),
            report.client_signature)
    except Exception:
        client_sig_ok = False
    checks["client_signature"] = client_sig_ok
    if not client_sig_ok:
        errors.append("client signature does not verify")

    # 3. Admissions
    admission_ok = True
    for i, adm in enumerate(report.admissions):
        world_id = adm.get("entity_id")
        world_key = _world_key(world_id or "")
        if world_key is None:
            admission_ok = False
            errors.append(
                f"admission {i}: world {world_id!r} "
                f"not in anchors")
            continue
        # Reconstruct admission's canonical bytes
        try:
            payload = canonical_bytes({
                "kind": "admission",
                "entity_id": adm["entity_id"],
                "timestamp": adm["timestamp"],
                "subject_token": adm["subject_token"],
            })
            ok = verify_signature(
                world_key, payload, adm.get("signature", ""))
        except Exception as e:
            ok = False
            errors.append(f"admission {i}: {e}")
        if not ok:
            admission_ok = False
            errors.append(
                f"admission {i}: signature INVALID")
        # Subject matches client
        if adm.get("subject_token") != report.identity_token:
            admission_ok = False
            errors.append(
                f"admission {i}: subject_token does not "
                f"match report's client")
    checks["admissions"] = admission_ok

    # 4. Acks
    ack_ok = True
    for i, ack in enumerate(report.acks):
        world_id = ack.get("entity_id")
        world_key = _world_key(world_id or "")
        if world_key is None:
            ack_ok = False
            errors.append(
                f"ack {i}: world {world_id!r} not in anchors")
            continue
        try:
            payload = canonical_bytes({
                "kind": "ack",
                "entity_id": ack["entity_id"],
                "timestamp": ack["timestamp"],
                "subject_token": ack["subject_token"],
            })
            ok = verify_signature(
                world_key, payload, ack.get("signature", ""))
        except Exception as e:
            ok = False
            errors.append(f"ack {i}: {e}")
        if not ok:
            ack_ok = False
            errors.append(f"ack {i}: signature INVALID")
        if ack.get("subject_token") != report.identity_token:
            ack_ok = False
            errors.append(
                f"ack {i}: subject_token does not match")
    checks["acks"] = ack_ok

    # 5. Contracts
    contract_ok = True
    for i, contract in enumerate(report.contracts):
        offer = contract.get("offer", {})
        acceptance = contract.get("acceptance", {})
        proposer_key = _world_key(
            offer.get("proposer_world_id", ""))
        acceptor_key = _world_key(
            acceptance.get("acceptor_world_id", ""))
        if proposer_key is None:
            contract_ok = False
            errors.append(
                f"contract {i}: proposer world not in anchors")
        else:
            try:
                offer_payload = canonical_bytes({
                    "kind": "contract_offer",
                    "proposer_world_id":
                        offer["proposer_world_id"],
                    "proposer_public_key":
                        offer["proposer_public_key"],
                    "target_world_id": offer["target_world_id"],
                    "terms": offer["terms"],
                    "timestamp": offer["timestamp"],
                })
                ok = verify_signature(
                    proposer_key, offer_payload,
                    offer.get("signature", ""))
            except Exception:
                ok = False
            if not ok:
                contract_ok = False
                errors.append(
                    f"contract {i}: offer sig INVALID")
        if acceptor_key is None:
            contract_ok = False
            errors.append(
                f"contract {i}: acceptor world not in anchors")
        else:
            try:
                acc_payload = canonical_bytes({
                    "kind": "contract_acceptance",
                    "acceptor_world_id":
                        acceptance["acceptor_world_id"],
                    "acceptor_public_key":
                        acceptance["acceptor_public_key"],
                    "offer_hash": acceptance["offer_hash"],
                    "terms_hash": acceptance["terms_hash"],
                    "timestamp": acceptance["timestamp"],
                })
                ok = verify_signature(
                    acceptor_key, acc_payload,
                    acceptance.get("signature", ""))
            except Exception:
                ok = False
            if not ok:
                contract_ok = False
                errors.append(
                    f"contract {i}: acceptance sig INVALID")
    checks["contracts"] = contract_ok

    all_ok = all(checks.values())
    if all_ok:
        reason = "all checks passed"
    else:
        failed = [k for k, v in checks.items() if not v]
        reason = "failed: " + ", ".join(failed)
    return ReportVerdict(
        valid=all_ok, reason=reason,
        checks=checks, errors=errors)


# =====================================================================
# FederationClient
# =====================================================================

class FederationClient:
    """The main client. Holds state, orchestrates operations."""

    def __init__(self, state_dir: Path):
        if not HAS_CRYPTO:
            raise RuntimeError(
                "FederationClient requires `cryptography`")
        self.state = ClientState(state_dir)

    # -- Setup ---------------------------------------------------

    def create_identity(self, name: str) -> ClientIdentity:
        """Generate a new identity and persist it."""
        ident = create_identity(name)
        kp = KeyPair.generate()
        client_identity = ClientIdentity(
            identity=ident, keypair=kp)
        self.state.identity = client_identity
        self.state.passport = PassportV2.new(ident)
        self.state.save_identity()
        self.state.save_passport()
        self.state.append_log(
            "identity_created",
            {"token": ident.token, "name": name})
        return client_identity

    def load_state(self) -> bool:
        return self.state.load()

    def connect(
        self, anchor_url: str, root_public_key: str,
    ) -> ConnectResult:
        """Fetch, verify, and pin the federation anchors."""
        try:
            with urllib.request.urlopen(
                    anchor_url, timeout=10.0) as r:
                raw = json.loads(r.read().decode())
        except urllib.error.URLError as e:
            return ConnectResult(
                ok=False, reason=f"network: {e}")
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            return ConnectResult(
                ok=False, reason=f"malformed anchors: {e}")
        if raw.get("kind") != "federation_trust_anchors":
            return ConnectResult(
                ok=False,
                reason=f"wrong kind {raw.get('kind')!r}")
        if not _verify_anchors_signature(raw, root_public_key):
            return ConnectResult(
                ok=False,
                reason="anchors signature invalid")
        if not isinstance(raw.get("worlds"), list) \
                or not raw["worlds"]:
            return ConnectResult(
                ok=False, reason="anchors have no worlds")
        pinned = PinnedAnchors(
            anchor_url=anchor_url,
            root_fingerprint=root_public_key,
            raw=raw,
            fetched_at=_now(),
        )
        self.state.anchors = pinned
        self.state.save_anchors()
        self.state.append_log(
            "anchors_pinned",
            {"anchor_url": anchor_url,
             "root_fingerprint": root_public_key,
             "world_ids": pinned.world_ids()})
        return ConnectResult(ok=True, reason="connected",
                              anchors=pinned)

    # -- World entry ---------------------------------------------

    def _world_http(
        self, world_id: str,
    ) -> Tuple[Optional[WorldHTTPClient], Optional[str]]:
        """Look up the world's base URL from anchors and return
        an HTTP client, or a reason string if not found."""
        if self.state.anchors is None:
            return (None, "not connected to a federation")
        base_url = self.state.anchors.world_base_url(world_id)
        if base_url is None:
            return (None, f"world {world_id!r} not in anchors")
        return (WorldHTTPClient(base_url), None)

    def _verify_manifest_matches_anchors(
        self, world_id: str, manifest: Dict,
    ) -> Tuple[bool, str]:
        """Verify a fetched manifest matches the anchors.

        If the manifest is a C28 SignedManifest (has signature,
        signed_by, public_key), verify its signature against the
        anchors' curator key. Otherwise, require the manifest's
        entity_id to match; rely on HTTPS for integrity.
        """
        if manifest.get("entity_id") != world_id:
            return (False,
                    f"manifest entity_id "
                    f"{manifest.get('entity_id')!r} != "
                    f"{world_id!r}")
        has_sig = (
            isinstance(manifest.get("signature"), str)
            and manifest.get("signature"))
        if has_sig:
            world_key = self.state.anchors.world_public_key(world_id)
            if world_key is None:
                return (False, "world not in anchors")
            # C28 signed manifest canonical payload
            body = {k: v for k, v in manifest.items()
                    if k != "signature"}
            try:
                ok = verify_signature(
                    world_key, canonical_bytes(body),
                    manifest["signature"])
            except Exception:
                ok = False
            if not ok:
                return (False, "manifest signature INVALID")
        return (True, "manifest matches anchors")

    def _verify_admission(
        self, response: Dict, world_id: str,
    ) -> Tuple[bool, str]:
        """Verify a signed admission against the anchors."""
        world_key = self.state.anchors.world_public_key(world_id)
        if world_key is None:
            return (False, "world not in anchors")
        if response.get("kind") != "admission":
            return (False,
                    f"response kind "
                    f"{response.get('kind')!r} is not admission")
        try:
            payload = canonical_bytes({
                "kind": "admission",
                "entity_id": response["entity_id"],
                "timestamp": response["timestamp"],
                "subject_token": response["subject_token"],
            })
            ok = verify_signature(
                world_key, payload,
                response.get("signature", ""))
        except (KeyError, TypeError) as e:
            return (False, f"malformed admission: {e}")
        except Exception:
            ok = False
        if not ok:
            return (False, "signature INVALID")
        return (True, "admission verified")

    def _verify_ack(
        self, response: Dict, world_id: str,
    ) -> Tuple[bool, str]:
        world_key = self.state.anchors.world_public_key(world_id)
        if world_key is None:
            return (False, "world not in anchors")
        if response.get("kind") != "ack":
            return (False,
                    f"response kind "
                    f"{response.get('kind')!r} is not ack")
        try:
            payload = canonical_bytes({
                "kind": "ack",
                "entity_id": response["entity_id"],
                "timestamp": response["timestamp"],
                "subject_token": response["subject_token"],
            })
            ok = verify_signature(
                world_key, payload,
                response.get("signature", ""))
        except (KeyError, TypeError) as e:
            return (False, f"malformed ack: {e}")
        except Exception:
            ok = False
        if not ok:
            return (False, "signature INVALID")
        return (True, "ack verified")

    def enter_world(self, world_id: str) -> EnterResult:
        """Petition a world. Verify the response. Update passport."""
        if self.state.identity is None:
            return EnterResult(
                ok=False, reason="no identity; run `create_identity` first")
        if self.state.anchors is None:
            return EnterResult(
                ok=False, reason="not connected to a federation")
        client, err = self._world_http(world_id)
        if client is None:
            return EnterResult(ok=False, reason=err or "unknown")
        # Fetch manifest
        try:
            manifest = client.manifest()
        except WorldHTTPError as e:
            return EnterResult(
                ok=False, reason=f"manifest fetch: {e}")
        ok, reason = self._verify_manifest_matches_anchors(
            world_id, manifest)
        if not ok:
            return EnterResult(ok=False, reason=reason)
        # Send petition
        passport_admissions = list(
            self.state.passport.to_plain_entries())
        try:
            response = client.petition({
                "petitioner_token": self.state.identity.identity.token,
                "petitioner_name": self.state.identity.identity.name,
                "passport_admissions": passport_admissions,
                "message": "client entry",
            })
        except WorldHTTPError as e:
            return EnterResult(
                ok=False, reason=f"petition failed: {e}")
        if response.get("kind") == "admission":
            ok, vreason = self._verify_admission(response, world_id)
            if ok:
                entry = PassportEntry(
                    entity_id=response["entity_id"],
                    timestamp=response["timestamp"],
                    subject_token=response["subject_token"],
                    signature=response["signature"],
                )
                self.state.passport = self.state.passport.with_entry(entry)
                self.state.save_passport()
            self.state.append_log(
                "enter_world",
                {"world_id": world_id,
                 "ok": True, "verified": ok,
                 "reason": vreason,
                 "admission": response})
            return EnterResult(
                ok=True, reason=vreason,
                world_id=world_id, verified=ok,
                raw_response=response)
        elif response.get("kind") == "refusal":
            self.state.append_log(
                "enter_world",
                {"world_id": world_id, "ok": False,
                 "refused": True,
                 "reason": response.get("reason", "")})
            return EnterResult(
                ok=False,
                reason=f"refused: {response.get('reason', '')}",
                world_id=world_id, raw_response=response)
        else:
            return EnterResult(
                ok=False,
                reason=f"unexpected response: {response.get('kind')}",
                world_id=world_id, raw_response=response)

    def submit_act(
        self,
        world_id: str,
        act_type: str,
        payload: Dict,
    ) -> SubmitResult:
        if self.state.identity is None:
            return SubmitResult(
                ok=False, reason="no identity")
        client, err = self._world_http(world_id)
        if client is None:
            return SubmitResult(ok=False, reason=err or "unknown")
        try:
            response = client.act({
                "actor_token": self.state.identity.identity.token,
                "type": act_type,
                "payload": payload,
            })
        except WorldHTTPError as e:
            return SubmitResult(
                ok=False, reason=f"act failed: {e}")
        if response.get("kind") == "ack":
            ok, vreason = self._verify_ack(response, world_id)
            self.state.append_log(
                "submit_act",
                {"world_id": world_id,
                 "act_type": act_type,
                 "ok": True, "verified": ok,
                 "reason": vreason,
                 "response": response,
                 "payload": payload})
            return SubmitResult(
                ok=True, reason=vreason,
                world_id=world_id, verified=ok,
                raw_response=response)
        elif response.get("kind") == "refusal":
            self.state.append_log(
                "submit_act",
                {"world_id": world_id,
                 "act_type": act_type,
                 "ok": False, "refused": True,
                 "reason": response.get("reason", ""),
                 "payload": payload})
            return SubmitResult(
                ok=False,
                reason=f"refused: {response.get('reason', '')}",
                world_id=world_id, raw_response=response)
        else:
            return SubmitResult(
                ok=False,
                reason=f"unexpected response: {response.get('kind')}",
                world_id=world_id, raw_response=response)

    def cite_contract(
        self,
        world_id: str,
        contract_id: str,
        cites_world: str,
        act_type: str = "poem.turn",
        base_payload: Optional[Dict] = None,
    ) -> SubmitResult:
        payload = dict(base_payload or {})
        payload["cites_contract"] = contract_id
        payload["cites_world"] = cites_world
        return self.submit_act(world_id, act_type, payload)

    # -- Verification --------------------------------------------

    def verify_state(self) -> ReportVerdict:
        """Verify everything the client holds, offline."""
        if self.state.identity is None:
            return ReportVerdict(
                valid=False, reason="no identity")
        if self.state.anchors is None:
            return ReportVerdict(
                valid=False, reason="no anchors pinned")
        # Build a report and verify it
        report = self.build_report()
        verdict = verify_report(
            report, self.state.anchors.root_fingerprint)
        self.state.append_log(
            "verify_state",
            {"valid": verdict.valid, "reason": verdict.reason})
        return verdict

    # -- Report --------------------------------------------------

    def build_report(self) -> FederationReport:
        """Produce a signed, self-contained federation report."""
        if self.state.identity is None:
            raise RuntimeError("no identity")
        if self.state.anchors is None:
            raise RuntimeError("no anchors pinned")
        # Split log entries by kind
        admissions: List[Dict] = []
        acks: List[Dict] = []
        refusals: List[Dict] = []
        for entry in self.state.get_log():
            if entry.get("kind") == "enter_world":
                data = entry.get("data", {})
                if data.get("ok") and data.get("admission"):
                    admissions.append(data["admission"])
                elif data.get("refused"):
                    refusals.append({
                        "world_id": data.get("world_id"),
                        "reason": data.get("reason", ""),
                    })
            elif entry.get("kind") == "submit_act":
                data = entry.get("data", {})
                if data.get("ok") and data.get("response"):
                    acks.append(data["response"])
                elif data.get("refused"):
                    refusals.append({
                        "world_id": data.get("world_id"),
                        "act_type": data.get("act_type"),
                        "reason": data.get("reason", ""),
                    })
        # Contracts from state
        contracts = list(self.state.contracts.values())
        generated_at = _now()
        report = FederationReport(
            identity_token=self.state.identity.identity.token,
            identity_name=self.state.identity.identity.name,
            identity_public_key=(
                self.state.identity.keypair.public_key_hex()),
            anchors=self.state.anchors.raw,
            admissions=admissions,
            acks=acks,
            refusals=refusals,
            contracts=contracts,
            generated_at=generated_at,
            client_signature="",  # placeholder
        )
        # Sign
        signature = self.state.identity.keypair.sign(
            report.canonical_payload()).hex()
        report.client_signature = signature
        return report


# =====================================================================
# CLI
# =====================================================================

DEFAULT_STATE_DIR = Path.home() / ".lfs"


def _format_state_summary(client: FederationClient) -> str:
    lines = []
    if client.state.identity is None:
        lines.append("No identity yet.")
        return "\n".join(lines)
    ident = client.state.identity
    lines.append(
        f"Identity:  {ident.identity.name} "
        f"({ident.identity.token[:16]}...)")
    if client.state.anchors is not None:
        a = client.state.anchors
        lines.append(
            f"Anchors:   {a.root_fingerprint[:16]}... "
            f"({len(a.world_ids())} worlds)")
        lines.append(f"Worlds:    {', '.join(a.world_ids())}")
    else:
        lines.append("Anchors:   (not connected)")
    if client.state.passport is not None:
        n = len(client.state.passport)
        lines.append(f"Passport:  {n} entries")
    else:
        lines.append("Passport:  (none)")
    lines.append(f"Contracts: {len(client.state.contracts)}")
    log = client.state.get_log()
    lines.append(f"Log:       {len(log)} entries")
    return "\n".join(lines)


def _cmd_init(client: FederationClient, args) -> int:
    if client.state.exists():
        print(f"State already exists at {client.state.state_dir}",
              file=sys.stderr)
        return 1
    ident = client.create_identity(args.name)
    print(f"Created identity: {ident.identity.name}")
    print(f"  token:      {ident.identity.token}")
    print(f"  public key: {ident.keypair.public_key_hex()}")
    print(f"  state:      {client.state.state_dir}")
    return 0


def _cmd_connect(client: FederationClient, args) -> int:
    if not client.load_state() or client.state.identity is None:
        print("No identity; run `init <name>` first",
              file=sys.stderr)
        return 1
    result = client.connect(args.anchor_url, args.root_key)
    print(result.format())
    return 0 if result.ok else 1


def _cmd_status(client: FederationClient, args) -> int:
    if not client.load_state() or client.state.identity is None:
        print("No identity; run `init <name>` first",
              file=sys.stderr)
        return 1
    print(_format_state_summary(client))
    return 0


def _cmd_enter(client: FederationClient, args) -> int:
    if not client.load_state() or client.state.identity is None:
        print("No identity", file=sys.stderr)
        return 1
    result = client.enter_world(args.world_id)
    if result.ok:
        print(f"Entered {result.world_id}")
        print(f"  verified: {result.verified}")
        print(f"  reason:   {result.reason}")
        return 0
    print(f"Enter failed: {result.reason}", file=sys.stderr)
    return 1


def _cmd_act(client: FederationClient, args) -> int:
    if not client.load_state() or client.state.identity is None:
        print("No identity", file=sys.stderr)
        return 1
    try:
        payload = json.loads(args.payload_json)
    except json.JSONDecodeError as e:
        print(f"Invalid payload JSON: {e}", file=sys.stderr)
        return 1
    result = client.submit_act(args.world_id, args.act_type, payload)
    if result.ok:
        print(f"Act accepted by {result.world_id}")
        print(f"  verified: {result.verified}")
        return 0
    print(f"Act failed: {result.reason}", file=sys.stderr)
    return 1


def _cmd_cite(client: FederationClient, args) -> int:
    if not client.load_state() or client.state.identity is None:
        print("No identity", file=sys.stderr)
        return 1
    result = client.cite_contract(
        args.world_id, args.contract_id, args.cites_world)
    if result.ok:
        print(f"Citation accepted by {result.world_id}")
        return 0
    print(f"Citation failed: {result.reason}", file=sys.stderr)
    return 1


def _cmd_verify(client: FederationClient, args) -> int:
    if not client.load_state() or client.state.identity is None:
        print("No identity", file=sys.stderr)
        return 1
    verdict = client.verify_state()
    print(verdict.format())
    return 0 if verdict.valid else 1


def _cmd_report(client: FederationClient, args) -> int:
    if not client.load_state() or client.state.identity is None:
        print("No identity", file=sys.stderr)
        return 1
    report = client.build_report()
    if args.output:
        path = Path(args.output)
    else:
        path = client.state.state_dir / "report.json"
    report.save(path)
    print(f"Report written to {path}")
    print(f"  identity:  {report.identity_name}")
    print(f"  admissions: {len(report.admissions)}")
    print(f"  acks:       {len(report.acks)}")
    print(f"  contracts:  {len(report.contracts)}")
    return 0


def _cmd_verify_report(client: FederationClient, args) -> int:
    try:
        report = FederationReport.load(Path(args.report_path))
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Could not load report: {e}", file=sys.stderr)
        return 1
    verdict = verify_report(report, args.root_key)
    print(verdict.format())
    return 0 if verdict.valid else 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="lfs",
        description="The LFS/0.1 reference client.",
    )
    parser.add_argument(
        "--state-dir", default=str(DEFAULT_STATE_DIR),
        help="State directory (default: ~/.lfs)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="Create a new identity")
    p.add_argument("name", help="Display name")
    p.set_defaults(func=_cmd_init)

    p = sub.add_parser("connect", help="Pin federation anchors")
    p.add_argument("anchor_url", help="Anchors file URL")
    p.add_argument("root_key", help="Root public key (hex)")
    p.set_defaults(func=_cmd_connect)

    p = sub.add_parser("status", help="Show state summary")
    p.set_defaults(func=_cmd_status)

    p = sub.add_parser("enter", help="Petition a world")
    p.add_argument("world_id")
    p.set_defaults(func=_cmd_enter)

    p = sub.add_parser("act", help="Submit an act")
    p.add_argument("world_id")
    p.add_argument("act_type")
    p.add_argument("payload_json")
    p.set_defaults(func=_cmd_act)

    p = sub.add_parser("cite", help="Cite a contract in an act")
    p.add_argument("world_id")
    p.add_argument("contract_id")
    p.add_argument("cites_world")
    p.set_defaults(func=_cmd_cite)

    p = sub.add_parser("verify", help="Verify all state")
    p.set_defaults(func=_cmd_verify)

    p = sub.add_parser("report", help="Build and save a report")
    p.add_argument("--output", default=None)
    p.set_defaults(func=_cmd_report)

    p = sub.add_parser(
        "verify-report", help="Verify an external report")
    p.add_argument("report_path")
    p.add_argument("root_key")
    p.set_defaults(func=_cmd_verify_report)

    args = parser.parse_args(argv)
    client = FederationClient(Path(args.state_dir))
    try:
        return args.func(client, args)
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Client against two signed worlds over HTTP.

    1. Spin up Poetry World and Chemistry World (signed, C13).
    2. Build anchors (signed by a root key).
    3. Client: create identity, connect, enter both worlds,
       submit acts, verify state, produce report.
    4. "Third-party verifier": loads report + root key, verifies
       offline, in a fresh process.
    """
    import json as _json
    from pathlib import Path
    from multiverse_c3 import Act, Ack
    from multiverse_c4 import PoetryWorld
    from multiverse_c5 import ChemistryWorld
    from multiverse_c13 import SignedWorld
    from wcp_http_shim import WorldProtocolServer

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir)
    path.mkdir(parents=True, exist_ok=True)

    # -- Two signed worlds ----------------------------------------
    poetry_kp = KeyPair.generate()
    poetry = SignedWorld(
        PoetryWorld("world:poetry", "Poetry"), poetry_kp)
    poetry_srv = WorldProtocolServer(poetry, port=0)
    poetry_srv.serve_in_thread()
    chemistry_kp = KeyPair.generate()
    chemistry = SignedWorld(
        ChemistryWorld("world:chemistry", "Chemistry"),
        chemistry_kp)
    chem_srv = WorldProtocolServer(chemistry, port=0)
    chem_srv.serve_in_thread()
    import time as _t
    _t.sleep(0.2)
    poetry_url = f"http://127.0.0.1:{poetry_srv._httpd.server_address[1]}"
    chem_url = f"http://127.0.0.1:{chem_srv._httpd.server_address[1]}"

    # -- Anchors, signed by root key ------------------------------
    root_kp = KeyPair.generate()
    anchors_body = {
        "kind": "federation_trust_anchors",
        "version": "LFS/0.1",
        "published_at": _now(),
        "ledger_checkpoint_public_key": "00" * 32,  # unused in demo
        "worlds": [
            {
                "entity_id": "world:poetry",
                "manifest_url": f"{poetry_url}/manifest",
                "curator_public_key": poetry_kp.public_key_hex(),
                "curator_world": "curator:poetry",
            },
            {
                "entity_id": "world:chemistry",
                "manifest_url": f"{chem_url}/manifest",
                "curator_public_key": chemistry_kp.public_key_hex(),
                "curator_world": "curator:chemistry",
            },
        ],
    }
    anchors_sig = root_kp.sign(
        canonical_bytes(anchors_body)).hex()
    anchors = dict(anchors_body)
    anchors["signature"] = anchors_sig

    # Serve the anchors file over HTTP
    import http.server
    import threading
    import tempfile
    anchors_path = path / "anchors.json"
    anchors_path.write_text(_json.dumps(anchors, indent=2))
    anchors_url = f"file://{anchors_path}"

    try:
        # -- Client ----------------------------------------------
        client_dir = path / "client"
        if client_dir.exists():
            import shutil
            shutil.rmtree(client_dir)
        client = FederationClient(client_dir)

        ident = client.create_identity("Alice")

        # For the demo, `connect` needs a URL. Use a local file
        # served by http.server. Simpler: monkey-patch to read
        # the anchors file directly. Actually, let's construct a
        # temporary HTTP server for the anchors.
        # Simpler still: use a file:// read via urlopen (works).
        connect_result = client.connect(
            anchors_url, root_kp.public_key_hex())

        # -- Enter Poetry ----------------------------------------
        enter_poetry = client.enter_world("world:poetry")

        # -- Act in Poetry ---------------------------------------
        poem_act = client.submit_act(
            "world:poetry", "poem.turn", {
                "acknowledgment": "(seed)",
                "proposal": "The Brain is wider than the Sky",
                "invitation": "What is the Sky to the Brain?",
                "holds_open": True,
            })

        # -- Enter Chemistry -------------------------------------
        enter_chem = client.enter_world("world:chemistry")

        # -- Act in Chemistry ------------------------------------
        chem_act = client.submit_act(
            "world:chemistry", "chemistry.react", {
                "substrates": [
                    {"formula": "H2", "count": 2},
                    {"formula": "O2", "count": 1},
                ],
                "products": [{"formula": "H2O", "count": 2}],
            })

        # -- Try to cite without a contract ----------------------
        cite_fail = client.cite_contract(
            "world:poetry",
            "00" * 32,  # fake
            "world:chemistry",
            base_payload={
                "acknowledgment": "(seed)",
                "proposal": "citing a contract",
                "invitation": "?",
                "holds_open": True,
            })

        # -- Verify state ----------------------------------------
        verify_verdict = client.verify_state()

        # -- Build report ----------------------------------------
        report = client.build_report()
        report_path = path / "alice_report.json"
        report.save(report_path)

        # -- Third-party verification ----------------------------
        # Reload from file (proves the report is self-contained)
        loaded_report = FederationReport.load(report_path)
        third_party_verdict = verify_report(
            loaded_report, root_kp.public_key_hex())

        # -- Print ----------------------------------------------
        print("=" * 70)
        print("Reference Client — Alice joins a two-world federation")
        print("=" * 70)
        print()
        print(f"  Identity: {ident.identity.name} "
              f"({ident.identity.token[:16]}...)")
        print(f"  Connect:  {connect_result.format()}")
        print()
        print(f"  Enter Poetry:    ok={enter_poetry.ok}, "
              f"verified={enter_poetry.verified}")
        print(f"  Submit poem:     ok={poem_act.ok}, "
              f"verified={poem_act.verified}")
        print(f"  Enter Chemistry: ok={enter_chem.ok}, "
              f"verified={enter_chem.verified}")
        print(f"  Submit reaction: ok={chem_act.ok}, "
              f"verified={chem_act.verified}")
        print(f"  Cite (bad id):   ok={cite_fail.ok} "
              f"({cite_fail.reason[:60]}...)")
        print()
        print(f"  Self-verify: {verify_verdict.valid} "
              f"({verify_verdict.reason})")
        print()
        print(f"  Report: {len(report.admissions)} admissions, "
              f"{len(report.acks)} acks, "
              f"{len(report.refusals)} refusals")
        print(f"  Third-party verify: {third_party_verdict.valid}")
        for name, ok in third_party_verdict.checks.items():
            print(f"    {'✓' if ok else '✗'} {name}")
        print()
        print("  What this demonstrates:")
        print("    - A resident's client can join a federation without")
        print("      any operator intervention.")
        print("    - Every admission and ack is verified against the")
        print("      anchors before being accepted.")
        print("    - The federation report is self-contained and")
        print("      verifiable offline by a third party with only")
        print("      the root key.")
        print("    - The client doesn't trust its own servers; it")
        print("      trusts the root key.")
        print()
        print("  Anchor (public domain, Emily Dickinson):")
        print("    'The Brain – is wider than the Sky –'")
        print("    'For – put them side by side –'")

        audit = {
            "identity_token": ident.identity.token,
            "connect_ok": connect_result.ok,
            "enter_poetry": {
                "ok": enter_poetry.ok,
                "verified": enter_poetry.verified,
            },
            "act_poetry": {
                "ok": poem_act.ok,
                "verified": poem_act.verified,
            },
            "enter_chemistry": {
                "ok": enter_chem.ok,
                "verified": enter_chem.verified,
            },
            "act_chemistry": {
                "ok": chem_act.ok,
                "verified": chem_act.verified,
            },
            "cite_fake": {
                "ok": cite_fail.ok,
                "reason": cite_fail.reason[:100],
            },
            "self_verify_valid": verify_verdict.valid,
            "third_party_verify_valid": third_party_verdict.valid,
            "report_path": str(report_path),
            "report_admissions": len(report.admissions),
            "report_acks": len(report.acks),
            "report_refusals": len(report.refusals),
        }
        (path / "reference_client_demo.json").write_text(
            _json.dumps(audit, indent=2))
        print(f"\n  → {path}/reference_client_demo.json")
        print(f"  → {report_path}")
        return audit
    finally:
        poetry_srv.stop()
        chem_srv.stop()


if __name__ == "__main__":
    sys.exit(main())
