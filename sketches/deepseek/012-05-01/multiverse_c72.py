"""
multiverse_c72.py — Component 72: The Inter-Federation Protocol.

A specification and implementation for two federations to
recognize each other, exchange artifacts, and negotiate
contracts across federation boundaries.

Design commitments:

  1. Recognition is a signed statement (FederationRecognition),
     one hop of trust from one federation's root key to another.

  2. A cross-federation message carries the SENDER's federation
     anchors. The receiver verifies:
       a. its own recognition of the sender's federation,
       b. the sender's anchors signature,
       c. the sender's curator signature on the inner message.

  3. Recognition is directional and scoped. A→Z does not imply
     Z→A. Scope names what the recognition permits.

  4. No global trust root. No federation registry. N federations
     recognize each other through N² (or fewer) signed statements.

What C72 does NOT do (v0.1):
  - Namespacing across federations. Demo uses distinct world
    IDs per federation (`world:poetry-a` vs `world:poetry-z`).
    A v0.2 spec would formalize prefixes; C72 documents the
    constraint.
  - Federation-level identity. Two federations can have the
    same world_id; the demo avoids this. A v0.2 spec would
    require federations to namespaces their world IDs.
  - Aggregate recognition. If A recognizes Z and Z recognizes
    X, A does not transitively recognize X. Recognition is
    one hop; chains are explicit (A→Z and Z→X are separate
    statements; A→X would need its own).
  - Scope enforcement beyond "contracts". The demo scopes
    recognition to "contracts"; enforcement is a policy
    concern (C63-style) not in C72.
  - Cross-federation ledger. Each federation has its own
    commitment store (C62). Cross-federation artifacts are
    referenced by the chain, not by a shared log.
  - Inter-federation revocation. Contract revocation works
    within a federation (C70). Cross-federation revocation
    is symmetric but not demonstrated in C72.

Composition: C13 (signing), C55 (curator messages), C57
(contracts), C62 (ledger), C68 (transport), C69 (contract
negotiation), C70 (revocation). No new cryptographic
primitives; only new artifacts (recognition, recognized peer,
cross-federation wrapper).

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: recognition sign/verify, tampered
    recognition, wrong root key, peer chain building, chain
    with bad anchors, chain with missing world, wrapper
    verify, tampered inner, tampered anchors, xfed handler
    happy/bad/unknown-sender, real round-trip, deliver uses
    xfed for recognized peer.
  - "A world never raises on what a visitor sends" —
    verifiers return verdicts; xfed handler returns
    Refusal on any error.
  - "History, not rank" — recognitions and wrappers are
    signed, timestamped, and logged.

Usage:
  fed_a = RecognizedPeerProcess(...)
  fed_z = RecognizedPeerProcess(...)
  a_rec = sign_federation_recognition(...)  # A → Z
  z_rec = sign_federation_recognition(...)  # Z → A
  fed_a.add_recognition(a_rec)
  fed_z.add_recognition(z_rec)
  a_peer = build_recognized_peer(a_rec, z_anchors,
                                   "world:poetry-z", a_root_key)
  fed_a.add_recognized_peer(a_peer)
  ok, reason, terms_hash = fed_a.propose_contract(
      "world:poetry-z", terms)
"""

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from multiverse_c3 import Ack, Refusal
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c55 import CuratorMessage, verify_curator_message, _now
from multiverse_c65 import _verify_anchors_signature
from multiverse_c68 import (
    CuratorServer, _ack_or_refusal_to_dict,
)
from multiverse_c70 import RevocableCuratorProcess


# =====================================================================
# FederationRecognition — the atom
# =====================================================================

@dataclass(frozen=True)
class FederationRecognition:
    """A signed statement: "I recognize federation X for scope S."

    Signed by the recognizer's root key. Scoped. Directional.
    """
    recognizer_id: str
    recognizer_root_public_key: str
    recognized_id: str
    recognized_root_public_key: str
    scope: Tuple[str, ...]
    timestamp: str
    signature: str

    def __post_init__(self):
        for f in ("recognizer_id", "recognizer_root_public_key",
                  "recognized_id", "recognized_root_public_key",
                  "timestamp", "signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        for f in ("recognizer_root_public_key",
                  "recognized_root_public_key"):
            if len(getattr(self, f)) != 64:
                raise ValueError(
                    f"{f} must be 64 hex chars")
        if not isinstance(self.scope, tuple) or not self.scope:
            raise ValueError(
                "scope must be a non-empty tuple")
        for s in self.scope:
            if not isinstance(s, str) or not s:
                raise ValueError(
                    "each scope entry must be a non-empty string")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "federation_recognition",
            "recognizer_id": self.recognizer_id,
            "recognizer_root_public_key":
                self.recognizer_root_public_key,
            "recognized_id": self.recognized_id,
            "recognized_root_public_key":
                self.recognized_root_public_key,
            "scope": sorted(self.scope),
            "timestamp": self.timestamp,
        })

    def to_dict(self) -> Dict:
        return {
            "kind": "federation_recognition",
            "recognizer_id": self.recognizer_id,
            "recognizer_root_public_key":
                self.recognizer_root_public_key,
            "recognized_id": self.recognized_id,
            "recognized_root_public_key":
                self.recognized_root_public_key,
            "scope": list(self.scope),
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "FederationRecognition":
        return cls(
            recognizer_id=d["recognizer_id"],
            recognizer_root_public_key=(
                d["recognizer_root_public_key"]),
            recognized_id=d["recognized_id"],
            recognized_root_public_key=(
                d["recognized_root_public_key"]),
            scope=tuple(d["scope"]),
            timestamp=d["timestamp"],
            signature=d["signature"],
        )


def sign_federation_recognition(
    recognizer_id: str,
    recognizer_root_kp: KeyPair,
    recognized_id: str,
    recognized_root_public_key: str,
    scope: Tuple[str, ...],
    timestamp: Optional[str] = None,
) -> FederationRecognition:
    if not HAS_CRYPTO:
        raise RuntimeError(
            "sign_federation_recognition requires cryptography")
    if timestamp is None:
        timestamp = _now()
    payload = canonical_bytes({
        "kind": "federation_recognition",
        "recognizer_id": recognizer_id,
        "recognizer_root_public_key":
            recognizer_root_kp.public_key_hex(),
        "recognized_id": recognized_id,
        "recognized_root_public_key":
            recognized_root_public_key,
        "scope": sorted(scope),
        "timestamp": timestamp,
    })
    return FederationRecognition(
        recognizer_id=recognizer_id,
        recognizer_root_public_key=(
            recognizer_root_kp.public_key_hex()),
        recognized_id=recognized_id,
        recognized_root_public_key=(
            recognized_root_public_key),
        scope=tuple(sorted(scope)),
        timestamp=timestamp,
        signature=recognizer_root_kp.sign(payload).hex(),
    )


def verify_federation_recognition(
    rec: FederationRecognition,
    expected_root_key: Optional[str] = None,
) -> bool:
    """True iff the recognition's signature verifies. Never raises."""
    if not HAS_CRYPTO:
        return False
    try:
        if not isinstance(rec, FederationRecognition):
            return False
        key = (expected_root_key
               or rec.recognizer_root_public_key)
        return verify_signature(
            key, rec.canonical_payload(), rec.signature)
    except Exception:
        return False


# =====================================================================
# RecognizedPeer — a peer registration from a verified chain
# =====================================================================

@dataclass(frozen=True)
class RecognizedPeer:
    """A peer in another federation, with the chain that
    legitimizes it.

    - world_id: the remote world's entity ID
    - curator_url: base URL for the remote curator's endpoints
    - curator_public_key: the remote curator's signing key
    - remote_anchors: the remote federation's signed anchors
    - recognition: the LOCAL federation's recognition of the
      remote federation's root key
    """
    world_id: str
    curator_url: str
    curator_public_key: str
    remote_anchors: Dict
    recognition: FederationRecognition

    def __post_init__(self):
        if not self.world_id:
            raise ValueError("world_id required")
        if not self.curator_url:
            raise ValueError("curator_url required")
        if len(self.curator_public_key) != 64:
            raise ValueError(
                "curator_public_key must be 64 hex chars")
        if not isinstance(self.remote_anchors, dict):
            raise ValueError("remote_anchors must be a dict")
        if not isinstance(self.recognition,
                          FederationRecognition):
            raise ValueError(
                "recognition must be FederationRecognition")


def _curator_url_from_manifest_url(manifest_url: str) -> str:
    if manifest_url.endswith("/manifest"):
        return manifest_url[: -len("/manifest")]
    return manifest_url


def build_recognized_peer(
    recognition: FederationRecognition,
    remote_anchors: Dict,
    remote_world_id: str,
    local_root_key: str,
) -> RecognizedPeer:
    """Build a RecognizedPeer from a chain. Raises ValueError if
    the chain does not verify.

    Chain:
      1. `recognition` is signed by `local_root_key`.
      2. `recognition.recognized_root_public_key` is the remote
         federation's root key.
      3. `remote_anchors` is signed by that root key.
      4. `remote_anchors` contains `remote_world_id` with a
         curator URL and public key.
    """
    if not HAS_CRYPTO:
        raise RuntimeError(
            "build_recognized_peer requires cryptography")
    if not verify_federation_recognition(
            recognition, local_root_key):
        raise ValueError(
            "recognition signature does not verify against "
            "local root key")
    if not _verify_anchors_signature(
            remote_anchors,
            recognition.recognized_root_public_key):
        raise ValueError(
            "remote anchors signature does not verify against "
            "recognized root key")
    for w in remote_anchors.get("worlds", []):
        if w.get("entity_id") == remote_world_id:
            manifest_url = w.get("manifest_url", "")
            if not manifest_url:
                raise ValueError(
                    f"world {remote_world_id!r} has no "
                    f"manifest_url")
            curator_url = _curator_url_from_manifest_url(
                manifest_url)
            public_key = w.get("curator_public_key", "")
            if len(public_key) != 64:
                raise ValueError(
                    f"world {remote_world_id!r} has invalid "
                    f"curator_public_key")
            return RecognizedPeer(
                world_id=remote_world_id,
                curator_url=curator_url,
                curator_public_key=public_key,
                remote_anchors=dict(remote_anchors),
                recognition=recognition,
            )
    raise ValueError(
        f"world {remote_world_id!r} not found in "
        f"remote anchors")


def verify_recognized_peer(
    peer: RecognizedPeer, local_root_key: str,
) -> Tuple[bool, str]:
    """Re-verify the chain in a RecognizedPeer. Never raises."""
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    if not isinstance(peer, RecognizedPeer):
        return (False, "not a RecognizedPeer")
    if not verify_federation_recognition(
            peer.recognition, local_root_key):
        return (False, "recognition does not verify against "
                        "local root key")
    if not _verify_anchors_signature(
            peer.remote_anchors,
            peer.recognition.recognized_root_public_key):
        return (False, "remote anchors do not verify against "
                        "recognized root key")
    for w in peer.remote_anchors.get("worlds", []):
        if w.get("entity_id") == peer.world_id:
            if w.get("curator_public_key") != \
                    peer.curator_public_key:
                return (False, "curator public key mismatch")
            return (True, "chain verified")
    return (False, f"world {peer.world_id!r} not in "
                    f"remote anchors")


# =====================================================================
# CrossFederationMessage — the wrapper
# =====================================================================

def _wrap_cross_federation_message(
    inner: CuratorMessage, local_anchors: Dict,
) -> Dict:
    return {
        "kind": "cross_federation_message",
        "inner": inner.to_dict(),
        "remote_anchors": dict(local_anchors),
    }


def verify_cross_federation_message(
    wrapper: Dict,
    local_recognition: FederationRecognition,
    local_root_key: str,
) -> Tuple[bool, str, Optional[Dict]]:
    """Verify a cross-federation message. Never raises.

    Returns (ok, reason, inner_message_dict).
    """
    if not HAS_CRYPTO:
        return (False, "cryptography not installed", None)
    if not isinstance(wrapper, dict):
        return (False, "wrapper is not a dict", None)
    if wrapper.get("kind") != "cross_federation_message":
        return (False,
                 f"wrapper kind is "
                 f"{wrapper.get('kind')!r}, expected "
                 f"'cross_federation_message'", None)
    # 1. Verify local_recognition
    if not verify_federation_recognition(
            local_recognition, local_root_key):
        return (False,
                 "local recognition does not verify against "
                 "local root key", None)
    # 2. Verify remote anchors against recognized root key
    remote_anchors = wrapper.get("remote_anchors")
    if not isinstance(remote_anchors, dict):
        return (False, "remote_anchors is not a dict", None)
    if not _verify_anchors_signature(
            remote_anchors,
            local_recognition.recognized_root_public_key):
        return (False,
                 "remote anchors do not verify against the "
                 "recognized root key", None)
    # 3. Parse inner message
    inner_dict = wrapper.get("inner")
    if not isinstance(inner_dict, dict):
        return (False, "inner is not a dict", None)
    try:
        inner = CuratorMessage.from_dict(inner_dict)
    except (KeyError, ValueError, TypeError) as e:
        return (False, f"malformed inner message: {e}", None)
    # 4. Verify inner signature against a curator key from
    # remote anchors
    sender_world_id = inner.sender_world_id
    sender_key = None
    for w in remote_anchors.get("worlds", []):
        if w.get("entity_id") == sender_world_id:
            sender_key = w.get("curator_public_key")
            break
    if sender_key is None:
        return (False,
                 f"sender {sender_world_id!r} not in remote "
                 f"anchors", None)
    if not verify_curator_message(inner, sender_key):
        return (False,
                 "inner message signature INVALID", None)
    return (True, "verified", inner_dict)


# =====================================================================
# XfedCuratorServer — extends CuratorServer with /xfed/message
# =====================================================================

class XfedCuratorServer(CuratorServer):
    """CuratorServer plus a /xfed/message endpoint.

    The endpoint accepts cross-federation messages, verifies them
    via the process's recognitions, and dispatches the inner
    CuratorMessage.
    """

    def __init__(
        self, curator, peers, xfed_handler,
        *args, **kwargs,
    ):
        self._xfed_handler = xfed_handler
        super().__init__(curator, peers, *args, **kwargs)

    def _make_handler(self):
        BaseHandler = super()._make_handler()
        server = self

        class Handler(BaseHandler):
            def do_POST(self):
                if self.path == "/xfed/message":
                    try:
                        length = int(
                            self.headers.get(
                                "Content-Length", 0))
                        body = json.loads(
                            self.rfile.read(length).decode())
                    except (json.JSONDecodeError,
                            UnicodeDecodeError,
                            ValueError) as e:
                        server._send(self, 400, {
                            "kind": "refusal",
                            "reason": f"malformed body: {e}"})
                        return
                    result = server._xfed_handler(body)
                    server._send(self, 200, result)
                    return
                super().do_POST()

        return Handler


# =====================================================================
# RecognizedPeerProcess
# =====================================================================

class RecognizedPeerProcess(RevocableCuratorProcess):
    """A RevocableCuratorProcess that recognizes peers from
    other federations via signed chains.

    - Anchors can be set after start (see set_local_anchors).
    - Recognitions are stored by the remote federation's root key.
    - Recognized peers are also registered in the standard
      PeerRegistry, so C68/C69's `_deliver` finds them.
    - `_deliver` routes recognized peers over /xfed/message.
    """

    def __init__(
        self,
        *args,
        local_root_kp: KeyPair,
        local_anchors: Optional[Dict] = None,
        recognitions: Optional[List[FederationRecognition]] = None,
        **kwargs,
    ):
        if not HAS_CRYPTO:
            raise RuntimeError(
                "RecognizedPeerProcess requires cryptography")
        self._local_anchors: Optional[Dict] = (
            dict(local_anchors) if local_anchors else None)
        self._local_root_kp = local_root_kp
        self._recognitions: Dict[str, FederationRecognition] = {
            rec.recognized_root_public_key: rec
            for rec in (recognitions or [])
        }
        self._recognized_peers: Dict[str, RecognizedPeer] = {}
        super().__init__(*args, **kwargs)
        # Replace the server with an xfed-aware one
        old_server = self._server
        self._server = XfedCuratorServer(
            self._curator, self._peers,
            xfed_handler=self._handle_xfed_message,
            host=old_server._host,
            port=old_server._port,
        )

    # -- Configuration after construction ------------------------

    def set_local_anchors(self, anchors: Dict) -> None:
        """Set the local federation's anchors.

        Needed because anchors carry the curator URL, which is
        only known after the server binds its port.
        """
        if not isinstance(anchors, dict):
            raise ValueError("anchors must be a dict")
        self._local_anchors = dict(anchors)

    def add_recognition(
        self, rec: FederationRecognition,
    ) -> None:
        """Register a recognition of a remote federation."""
        if not verify_federation_recognition(
                rec, self._local_root_kp.public_key_hex()):
            raise ValueError(
                "recognition signature does not verify "
                "against local root key")
        self._recognitions[rec.recognized_root_public_key] = rec

    def add_recognized_peer(self, peer: RecognizedPeer) -> None:
        """Register a peer via its chain. Raises ValueError if
        the chain does not verify."""
        ok, reason = verify_recognized_peer(
            peer, self._local_root_kp.public_key_hex())
        if not ok:
            raise ValueError(f"peer chain invalid: {reason}")
        self._peers.add(
            peer.world_id, peer.curator_url,
            peer.curator_public_key)
        self._recognized_peers[peer.world_id] = peer

    # -- Delivery routing ----------------------------------------

    def _deliver(
        self, peer_id: str, message: CuratorMessage,
    ) -> Tuple[bool, str]:
        if peer_id in self._recognized_peers:
            return self._send_xfed(
                self._recognized_peers[peer_id], message)
        return super()._deliver(peer_id, message)

    def _send_xfed(
        self, peer: RecognizedPeer, message: CuratorMessage,
    ) -> Tuple[bool, str]:
        if self._local_anchors is None:
            return (False, "local anchors not set")
        wrapper = _wrap_cross_federation_message(
            message, self._local_anchors)
        url = f"{peer.curator_url}/xfed/message"
        body = json.dumps(wrapper).encode()
        req = urllib.request.Request(
            url, data=body,
            headers={"Content-Type": "application/json"},
            method="POST")
        try:
            with urllib.request.urlopen(
                    req, timeout=10) as r:
                resp = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            return (False, f"HTTP {e.code}")
        except urllib.error.URLError as e:
            return (False, f"network: {e}")
        except (json.JSONDecodeError,
                UnicodeDecodeError) as e:
            return (False, f"malformed response: {e}")
        if resp.get("kind") == "ack":
            return (True, "delivered")
        if resp.get("kind") == "refusal":
            return (False, resp.get("reason", "refused"))
        return (False,
                 f"unexpected response: {resp.get('kind')}")

    # -- Inbound cross-federation dispatch -----------------------

    def _handle_xfed_message(self, wrapper: Any) -> Dict:
        """Handle an inbound cross-federation message.

        Returns ack/refusal dict — never raises.
        """
        if not isinstance(wrapper, dict):
            return {"kind": "refusal",
                    "reason": "wrapper is not a dict"}
        if wrapper.get("kind") != "cross_federation_message":
            return {"kind": "refusal",
                    "reason": f"wrong kind: "
                              f"{wrapper.get('kind')!r}"}
        local_root = self._local_root_kp.public_key_hex()
        # Try each recognition
        for root_key, rec in list(self._recognitions.items()):
            ok, reason, inner_dict = \
                verify_cross_federation_message(
                    wrapper, rec, local_root)
            if not ok:
                continue
            try:
                msg = CuratorMessage.from_dict(inner_dict)
            except (KeyError, ValueError, TypeError) as e:
                return {"kind": "refusal",
                        "reason": f"malformed inner: {e}"}
            peer = self._peers.get(msg.sender_world_id)
            if peer is None:
                return {"kind": "refusal",
                        "reason": (f"unknown peer: "
                                    f"{msg.sender_world_id!r}")}
            result = self._curator.receive(msg)
            return _ack_or_refusal_to_dict(result)
        return {"kind": "refusal",
                "reason": "no matching recognition"}


def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Two federations recognize each other; a contract is
    negotiated across the boundary.

    1. Federation A: one world (`world:poetry-a`), root key K_A,
       anchors signed by K_A.
    2. Federation Z: one world (`world:poetry-z`), root key K_Z,
       anchors signed by K_Z.
    3. Reciprocal recognition: A→Z and Z→A (scoped to contracts).
    4. Each side builds a RecognizedPeer for the other via the
       chain.
    5. A proposes a contract to Z across the boundary.
    6. Z receives via /xfed/message, verifies the chain,
       auto-accepts, sends back via /xfed/message.
    7. A receives, verifies, registers. Both registries show the
       contract as established.
    8. Third party verifies the whole chain offline.
    """
    import json as _json
    from multiverse_c1 import create_identity
    from multiverse_c4 import PoetryWorld
    from multiverse_c13 import KeyPair, canonical_bytes
    from multiverse_c57 import ContractTerms
    from multiverse_c68 import PeerRegistry
    from multiverse_c69 import AutoAcceptPolicy

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    if artifact_dir is None:
        artifact_dir = "artifacts"
    root_dir = Path(artifact_dir) / "inter_federation"
    root_dir.mkdir(parents=True, exist_ok=True)

    for sub in ("a", "z"):
        d = root_dir / sub
        if d.exists():
            import shutil
            shutil.rmtree(d)

    # -- 1. Two federations ----------------------------------
    a_root_kp = KeyPair.generate()
    z_root_kp = KeyPair.generate()
    a_world_kp = KeyPair.generate()
    z_world_kp = KeyPair.generate()

    a_world = PoetryWorld("world:poetry-a", "Poetry A")
    z_world = PoetryWorld("world:poetry-z", "Poetry Z")

    a_process = RecognizedPeerProcess(
        world=a_world, world_kp=a_world_kp,
        peers=PeerRegistry(),
        state_dir=root_dir / "a",
        cycle_interval=0.1,
        contract_policy=AutoAcceptPolicy(),
        identity=create_identity("curator:poetry-a"),
        local_root_kp=a_root_kp,
    )
    z_process = RecognizedPeerProcess(
        world=z_world, world_kp=z_world_kp,
        peers=PeerRegistry(),
        state_dir=root_dir / "z",
        cycle_interval=0.1,
        contract_policy=AutoAcceptPolicy(),
        identity=create_identity("curator:poetry-z"),
        local_root_kp=z_root_kp,
    )
    a_process.start()
    z_process.start()

    # -- 2. Anchors (now that URLs are known) ----------------
    def make_anchors(federation_name, world_id, world_url,
                      curator_key_hex, root_kp):
        body = {
            "kind": "federation_trust_anchors",
            "version": "LFS/0.1",
            "federation_name": federation_name,
            "published_at": _now(),
            "worlds": [{
                "entity_id": world_id,
                "manifest_url": f"{world_url}/manifest",
                "curator_public_key": curator_key_hex,
                "curator_world": f"curator:{world_id}",
            }],
        }
        sig = root_kp.sign(
            canonical_bytes(body)).hex()
        return dict(body, signature=sig)

    a_anchors = make_anchors(
        "Federation A", "world:poetry-a", a_process.url,
        a_world_kp.public_key_hex(), a_root_kp)
    z_anchors = make_anchors(
        "Federation Z", "world:poetry-z", z_process.url,
        z_world_kp.public_key_hex(), z_root_kp)
    a_process.set_local_anchors(a_anchors)
    z_process.set_local_anchors(z_anchors)

    try:
        # -- 3. Reciprocal recognition ----------------------
        a_rec_of_z = sign_federation_recognition(
            recognizer_id="Federation A",
            recognizer_root_kp=a_root_kp,
            recognized_id="Federation Z",
            recognized_root_public_key=(
                z_root_kp.public_key_hex()),
            scope=("contracts",),
        )
        z_rec_of_a = sign_federation_recognition(
            recognizer_id="Federation Z",
            recognizer_root_kp=z_root_kp,
            recognized_id="Federation A",
            recognized_root_public_key=(
                a_root_kp.public_key_hex()),
            scope=("contracts",),
        )
        a_process.add_recognition(a_rec_of_z)
        z_process.add_recognition(z_rec_of_a)

        # -- 4. Build recognized peers ----------------------
        a_peer_of_z = build_recognized_peer(
            a_rec_of_z, z_anchors, "world:poetry-z",
            a_root_kp.public_key_hex())
        z_peer_of_a = build_recognized_peer(
            z_rec_of_a, a_anchors, "world:poetry-a",
            z_root_kp.public_key_hex())
        a_process.add_recognized_peer(a_peer_of_z)
        z_process.add_recognized_peer(z_peer_of_a)

        # -- 5. Cross-federation contract negotiation ------
        terms = ContractTerms(content={
            "kind": "inter-federation",
            "a_scope": "poetry-a-world",
            "z_scope": "poetry-z-world",
        })
        propose_ok, propose_reason, terms_hash = \
            a_process.propose_contract("world:poetry-z", terms)

        # -- 6. Check both registries ----------------------
        a_rec = a_process.contract_registry.get(terms_hash)
        z_rec = z_process.contract_registry.get(terms_hash)
        a_established = (
            a_rec is not None and a_rec.is_established())
        z_established = (
            z_rec is not None and z_rec.is_established())

        # -- 7. Verify the chain offline -------------------
        a_anchors_ok = _verify_anchors_signature(
            a_anchors, a_root_kp.public_key_hex())
        z_anchors_ok = _verify_anchors_signature(
            z_anchors, z_root_kp.public_key_hex())
        a_rec_of_z_ok = verify_federation_recognition(
            a_rec_of_z, a_root_kp.public_key_hex())
        z_rec_of_a_ok = verify_federation_recognition(
            z_rec_of_a, z_root_kp.public_key_hex())

        # -- 8. Print -------------------------------------
        print("=" * 70)
        print("Inter-Federation — two federations, one contract")
        print("=" * 70)
        print()
        print(f"  Federation A:")
        print(f"    world:       world:poetry-a")
        print(f"    root key:    "
              f"{a_root_kp.public_key_hex()[:16]}...")
        print(f"    curator:     {a_process.url}")
        print()
        print(f"  Federation Z:")
        print(f"    world:       world:poetry-z")
        print(f"    root key:    "
              f"{z_root_kp.public_key_hex()[:16]}...")
        print(f"    curator:     {z_process.url}")
        print()
        print(f"  Recognition:")
        print(f"    A → Z signed by K_A:   {a_rec_of_z_ok}")
        print(f"    Z → A signed by K_Z:   {z_rec_of_a_ok}")
        print()
        print(f"  Anchor chain:")
        print(f"    A anchors (signed by K_A):  {a_anchors_ok}")
        print(f"    Z anchors (signed by K_Z):  {z_anchors_ok}")
        print()
        print(f"  Cross-federation contract:")
        print(f"    Propose from A to Z:   "
              f"{propose_ok} ({propose_reason})")
        print(f"    Terms hash:            "
              f"{terms_hash[:16]}...")
        print(f"    Established in A:      {a_established}")
        print(f"    Established in Z:      {z_established}")
        print()
        print("  What this demonstrates:")
        print("    - Two federations, each with its own root key and")
        print("      anchors, recognize each other through signed")
        print("      statements (one hop each, scoped to contracts).")
        print("    - A cross-federation message carries the SENDER's")
        print("      anchors. The receiver verifies: its own")
        print("      recognition → sender's anchors → sender's")
        print("      curator signature. Three signatures, no global")
        print("      trust root.")
        print("    - C57 contract negotiation (C69) works across the")
        print("      boundary without modification — the daemon")
        print("      wraps and unwraps transparently.")
        print("    - The whole chain verifies offline against the")
        print("      two root keys.")
        print()
        print("  Anchor (public domain, Emily Dickinson):")
        print("    'The Brain – is wider than the Sky –'")
        print("    'For – put them side by side –'")
        print("    'The one the other will contain'")
        print("    'With ease – and You – beside –'")

        audit = {
            "federation_a": {
                "world_id": "world:poetry-a",
                "root_key": a_root_kp.public_key_hex(),
                "curator_url": a_process.url,
            },
            "federation_z": {
                "world_id": "world:poetry-z",
                "root_key": z_root_kp.public_key_hex(),
                "curator_url": z_process.url,
            },
            "recognition": {
                "a_recognizes_z": a_rec_of_z_ok,
                "z_recognizes_a": z_rec_of_a_ok,
            },
            "anchor_chain": {
                "a_anchors_verify": a_anchors_ok,
                "z_anchors_verify": z_anchors_ok,
            },
            "contract": {
                "propose_ok": propose_ok,
                "propose_reason": propose_reason,
                "terms_hash": terms_hash,
                "established_in_a": a_established,
                "established_in_z": z_established,
            },
        }
        (root_dir / "inter_federation_demo.json").write_text(
            _json.dumps(audit, indent=2))
        print(f"\n  → {root_dir}/inter_federation_demo.json")
        return audit
    finally:
        a_process.stop()
        z_process.stop()
