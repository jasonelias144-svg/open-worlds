"""
multiverse_c70.py — Component 70: Revocation Coordination.

Closes C69's gap: curators can now coordinate bilateral
revocation of contracts.

Protocol (two-phase):

  A                            B
  |                            |
  | -- contract_revoke_intent ->|
  |    {contract_id, reason,    |
  |     timestamp, signer_role, |
  |     signature}              |
  |                             |  verify A's sig against
  |                             |  A's key over the
  |                             |  canonical payload
  |                             |  sign with B's key
  |                             |  construct BilateralRevocation
  |                             |  register in B's registry
  | <- contract_revoke_complete-|
  |    {revocation: full_dict}  |
  |                             |
  |  verify both sigs           |
  |  register in A's registry   |
  |  done                       |

The one commitment: the revocation's canonical payload is
FIXED by the first signer. The second signer signs the same
payload. No negotiation about fields. A proposes (timestamp,
reason); B accepts by signing. If B disagrees, B refuses.

What C70 does NOT do (v0.1):
  - Concurrent-initiation resolution. If A and B both send
    intents simultaneously, they'd construct different
    revocations (different timestamps). The second one to
    arrive would fail verification. Documented, not solved.
  - Revocation of a pending (not-yet-established) contract.
    Only established contracts can be revoked.
  - Revocation intent expiry. An intent that's sent but never
    delivered can be re-sent; no expiry mechanism.
  - Revocation rejection. There's no "B refuses to co-sign"
    response. If B's policy says no, B just refuses (returns
    Refusal from the handler), and A sees the refusal. No
    structured "rejected revocation" artifact.

Composition: C57 (BilateralRevocation), C68 (transport),
C69 (contract-aware curator).

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: intent construction, canonical payload
    fixed, signature verification, party check, established
    check, complete-revocation verification, idempotency,
    persistence, end-to-end A-initiated, end-to-end B-initiated,
    malformed refusals, never-raises.
  - "A world never raises on what a visitor sends" — handler
    returns Refusal; request returns (False, reason).
  - "History, not rank" — revocations logged, registries
    persisted.

Honest limits (documented, tested):
  - Same-payload commitment assumes A's timestamp is
    acceptable to B. If B needs a different timestamp, the
    handshake fails and A must re-initiate with a new value.
    This is a design choice, not a bug: the revocation
    content is atomic.
  - The `request_revocation` method is synchronous: it
    sends the intent and waits for the complete. If B is
    slow or down, the call blocks until timeout.
  - No retry on delivery failure (same as C69).
  - The revoker role must match the contract's parties:
    A's signer_role must be "a" (world_a) or "b" (world_b)
    and must match A's own world_id.
  - If the contract is in a pending or rejected state, B
    refuses the intent. Only established contracts can
    be revoked.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from multiverse_c3 import Ack, Refusal
from multiverse_c13 import (
    HAS_CRYPTO, canonical_bytes, verify_signature,
)
from multiverse_c55 import CuratorMessage, _now
from multiverse_c57 import (
    BilateralRevocation,
    ContractRecord,
    verify_bilateral_revocation,
)
from multiverse_c68 import CuratorHTTPClient
from multiverse_c69 import ContractAwareCuratorProcess


# =====================================================================
# Extend the message types (same pattern as C69)
# =====================================================================

REVOCATION_MESSAGE_TYPES = frozenset({
    "contract_revoke_intent",
    "contract_revoke_complete",
})

import multiverse_c55 as _c55
if not REVOCATION_MESSAGE_TYPES <= _c55.CURATOR_MESSAGE_TYPES:
    _c55.CURATOR_MESSAGE_TYPES = (
        _c55.CURATOR_MESSAGE_TYPES | REVOCATION_MESSAGE_TYPES)
import multiverse_c69 as _c69
_c69.CONTRACT_MESSAGE_TYPES = (
    _c69.CONTRACT_MESSAGE_TYPES | REVOCATION_MESSAGE_TYPES)


# =====================================================================
# RevocationIntentPayload
# =====================================================================

@dataclass(frozen=True)
class RevocationIntentPayload:
    """The wire-format payload A sends to B.

    The canonical bytes B needs to sign are derived from
    (contract_id, world_a_id, world_b_id, world_a_public_key,
    world_b_public_key, reason, timestamp) — the exact same
    shape C57's BilateralRevocation signs. This class carries
    those fields plus A's signature and role.
    """
    contract_id: str
    reason: str
    timestamp: str
    signer_role: str  # "a" or "b"
    signature: str

    def __post_init__(self):
        if len(self.contract_id) != 64:
            raise ValueError(
                "contract_id must be 64 hex chars")
        if self.signer_role not in ("a", "b"):
            raise ValueError(
                f"signer_role must be 'a' or 'b', "
                f"got {self.signer_role!r}")
        if not isinstance(self.signature, str) or not self.signature:
            raise ValueError("signature required")
        if not isinstance(self.timestamp, str) or not self.timestamp:
            raise ValueError("timestamp required")

    def to_dict(self) -> Dict:
        return {
            "contract_id": self.contract_id,
            "reason": self.reason,
            "timestamp": self.timestamp,
            "signer_role": self.signer_role,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "RevocationIntentPayload":
        return cls(
            contract_id=d["contract_id"],
            reason=d.get("reason", ""),
            timestamp=d["timestamp"],
            signer_role=d["signer_role"],
            signature=d["signature"],
        )


def revocation_canonical_payload(
    contract_id: str,
    world_a_id: str,
    world_a_public_key: str,
    world_b_id: str,
    world_b_public_key: str,
    reason: str,
    timestamp: str,
) -> bytes:
    """The exact canonical bytes C57's BilateralRevocation signs.

    Kept in sync with C57's
    BilateralRevocation.canonical_payload. If C57 changes its
    shape, this function and C70's intent payload must change
    together.
    """
    return canonical_bytes({
        "kind": "bilateral_revocation",
        "contract_id": contract_id,
        "world_a_id": world_a_id,
        "world_a_public_key": world_a_public_key,
        "world_b_id": world_b_id,
        "world_b_public_key": world_b_public_key,
        "reason": reason,
        "timestamp": timestamp,
    })


# =====================================================================
# RevocableCuratorProcess
# =====================================================================

class RevocableCuratorProcess(ContractAwareCuratorProcess):
    """A contract-aware curator that coordinates revocation."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add our two new message types to the dispatch
        self._reinstall_receive_hook()

    def _reinstall_receive_hook(self) -> None:
        """Extend C69's hook to also dispatch revocation
        messages."""
        c69_hook = self._curator.receive
        process = self

        def hooked(message: CuratorMessage):
            if message.message_type in REVOCATION_MESSAGE_TYPES:
                return process._handle_revocation_message(message)
            return c69_hook(message)

        self._curator.receive = hooked

    # -- Public entry point -------------------------------------

    def request_revocation(
        self,
        peer_id: str,
        contract_id: str,
        reason: str = "",
    ) -> Tuple[bool, str]:
        """Initiate a bilateral revocation with a peer.

        Returns (ok, reason). On success, both this process's
        registry and the peer's registry show the contract as
        revoked.
        """
        peer = self._peers.get(peer_id)
        if peer is None:
            return (False,
                    f"peer {peer_id!r} not registered")
        record = self.contract_registry.get(contract_id)
        if record is None:
            return (False,
                    f"contract {contract_id[:16]}... not in "
                    f"this registry")
        if not record.is_established():
            return (False,
                    "only established contracts can be revoked "
                    f"(state: "
                    f"{'pending' if record.is_pending() else 'rejected' if record.is_rejected() else 'revoked' if record.is_revoked() else 'unknown'})")
        # Determine our role
        if record.world_a_id == self.world_id:
            signer_role = "a"
        elif record.world_b_id == self.world_id:
            signer_role = "b"
        else:
            return (False,
                    "this world is not a party to the contract")
        # Look up the offer and acceptance for the canonical
        # payload fields
        offer = record.offer
        acceptance = record.acceptance
        if offer is None or acceptance is None:
            return (False, "contract missing offer or acceptance")
        # Build the canonical payload
        timestamp = _now()
        payload = revocation_canonical_payload(
            contract_id=contract_id,
            world_a_id=record.world_a_id,
            world_a_public_key=offer.proposer_public_key,
            world_b_id=record.world_b_id,
            world_b_public_key=acceptance.acceptor_public_key,
            reason=reason,
            timestamp=timestamp,
        )
        # Sign
        my_sig = self._world_kp.sign(payload).hex()
        # Build intent
        intent = RevocationIntentPayload(
            contract_id=contract_id,
            reason=reason,
            timestamp=timestamp,
            signer_role=signer_role,
            signature=my_sig,
        )
        # Send
        try:
            msg = self._curator._sign_message(
                "contract_revoke_intent",
                {"intent": intent.to_dict()})
        except Exception as e:
            return (False, f"sign failed: {e}")
        ok, deliver_reason = self._deliver(peer_id, msg)
        if not ok:
            return (False, f"delivery failed: {deliver_reason}")
        # Check our registry — did we register the complete
        # revocation that B sent back? B's handler should have
        # registered it on B's side and sent back a complete,
        # which our server received and processed.
        #
        # The flow is synchronous: deliver() returns only after
        # B has responded. B's response triggers our
        # _handle_revoke_complete, which registers the full
        # revocation in our registry. So by the time deliver()
        # returns, our registry should reflect the revocation.
        final = self.contract_registry.get(contract_id)
        if final is None or not final.is_revoked():
            return (False,
                    "revocation registered on peer but not "
                    "reflected in our registry (unexpected)")
        return (True, "revocation coordinated")

    # -- Inbound dispatch ---------------------------------------

    def _handle_revocation_message(
        self, message: CuratorMessage,
    ):
        if message.message_type == "contract_revoke_intent":
            return self._handle_revoke_intent(message)
        if message.message_type == "contract_revoke_complete":
            return self._handle_revoke_complete(message)
        return Refusal(
            reason=f"unknown revocation message "
                    f"{message.message_type!r}")

    def _handle_revoke_intent(self, message: CuratorMessage):
        """B's side: A has sent an intent; co-sign and reply."""
        peer = self._peers.get(message.sender_world_id)
        if peer is None:
            return Refusal(
                reason=f"unknown peer {message.sender_world_id!r}")
        peer_key = peer["public_key"]
        try:
            intent = RevocationIntentPayload.from_dict(
                message.payload["intent"])
        except (KeyError, ValueError, TypeError) as e:
            return Refusal(reason=f"malformed intent: {e}")
        # Look up the contract in our registry
        record = self.contract_registry.get(intent.contract_id)
        if record is None:
            return Refusal(
                reason=f"contract {intent.contract_id[:16]}... "
                        f"not in this registry")
        if record.is_revoked():
            # Idempotent: contract is already revoked
            return Ack(entity_id=self.world_id,
                        timestamp=_now())
        if not record.is_established():
            return Refusal(
                reason="only established contracts can be "
                        "revoked")
        offer = record.offer
        acceptance = record.acceptance
        if offer is None or acceptance is None:
            return Refusal(
                reason="contract missing offer or acceptance")
        # Verify A's signature against A's key
        # Determine which party A is
        if intent.signer_role == "a":
            if record.world_a_id != message.sender_world_id:
                return Refusal(
                    reason="signer_role 'a' does not match "
                            "sender world")
            a_pub_key = offer.proposer_public_key
            b_pub_key = acceptance.acceptor_public_key
        else:  # "b"
            if record.world_b_id != message.sender_world_id:
                return Refusal(
                    reason="signer_role 'b' does not match "
                            "sender world")
            a_pub_key = offer.proposer_public_key
            b_pub_key = acceptance.acceptor_public_key
        # Sanity: A's declared signature should verify against
        # A's key over the canonical payload
        canonical = revocation_canonical_payload(
            contract_id=intent.contract_id,
            world_a_id=record.world_a_id,
            world_a_public_key=a_pub_key,
            world_b_id=record.world_b_id,
            world_b_public_key=b_pub_key,
            reason=intent.reason,
            timestamp=intent.timestamp,
        )
        if not verify_signature(
                peer_key, canonical, intent.signature):
            return Refusal(
                reason="intent signature INVALID")
        # Co-sign with our key
        our_sig = self._world_kp.sign(canonical).hex()
        if intent.signer_role == "a":
            sig_a = intent.signature
            sig_b = our_sig
        else:
            sig_a = our_sig
            sig_b = intent.signature
        revocation = BilateralRevocation(
            contract_id=intent.contract_id,
            world_a_id=record.world_a_id,
            world_a_public_key=a_pub_key,
            world_b_id=record.world_b_id,
            world_b_public_key=b_pub_key,
            reason=intent.reason,
            timestamp=intent.timestamp,
            signature_a=sig_a,
            signature_b=sig_b,
        )
        # Verify the assembled revocation
        ok, reason = verify_bilateral_revocation(
            revocation, a_pub_key, b_pub_key)
        if not ok:
            return Refusal(
                reason=f"assembled revocation invalid: {reason}")
        # Register in our registry
        self.contract_registry.register_revocation(revocation)
        self._save_registry()
        # Send back
        try:
            reply = self._curator._sign_message(
                "contract_revoke_complete",
                {"revocation": revocation.to_dict()})
        except Exception as e:
            return Refusal(
                reason=f"sign reply failed: {e}")
        ok, deliver_reason = self._deliver(
            message.sender_world_id, reply)
        if not ok:
            return Refusal(
                reason=f"reply delivery failed: {deliver_reason}")
        return Ack(entity_id=self.world_id,
                   timestamp=_now())

    def _handle_revoke_complete(
        self, message: CuratorMessage,
    ):
        """A's side: B has completed the revocation; verify
        and register locally."""
        peer = self._peers.get(message.sender_world_id)
        if peer is None:
            return Refusal(
                reason=f"unknown peer {message.sender_world_id!r}")
        peer_key = peer["public_key"]
        try:
            raw = message.payload["revocation"]
            revocation = BilateralRevocation.from_dict(raw)
        except (KeyError, ValueError, TypeError) as e:
            return Refusal(
                reason=f"malformed revocation: {e}")
        # Verify both signatures
        ok, reason = verify_bilateral_revocation(
            revocation,
            revocation.world_a_public_key,
            revocation.world_b_public_key)
        if not ok:
            return Refusal(
                reason=f"revocation invalid: {reason}")
        # Sanity: the sender should be one of the parties
        if message.sender_world_id not in (
                revocation.world_a_id, revocation.world_b_id):
            return Refusal(
                reason="sender is not a party to the revocation")
        # Register locally
        self.contract_registry.register_revocation(revocation)
        self._save_registry()
        return Ack(entity_id=self.world_id,
                   timestamp=_now())

    # -- Convenience --------------------------------------------

    def revoked_contracts(self) -> List[ContractRecord]:
        return self.contract_registry.revoked()


def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Full lifecycle with revocation:

    1. Deploy + link two curators.
    2. Poetry proposes contract to Chemistry (auto-accept).
    3. Both registries show contract established.
    4. Poetry initiates revocation (request_revocation).
    5. Both registries show contract revoked.
    6. Reload from disk in fresh processes — revocation persists.
    7. Second demo: B initiates (reverse roles), same result.
    """
    import json as _json
    from multiverse_c1 import create_identity
    from multiverse_c57 import ContractTerms
    from multiverse_c66 import (
        DeployConfig, deploy_federation,
        _patch_c65_manifest_verification,
    )
    from multiverse_c69 import AutoAcceptPolicy

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    _patch_c65_manifest_verification()

    if artifact_dir is None:
        artifact_dir = "artifacts"
    root_dir = Path(artifact_dir) / "revocation"
    root_dir.mkdir(parents=True, exist_ok=True)
    fed_dir = root_dir / "federation"

    if fed_dir.exists():
        import shutil
        shutil.rmtree(fed_dir)

    fed = deploy_federation(DeployConfig(
        state_dir=fed_dir,
        federation_name="Revocation Demo",
    ))

    poetry_proc = None
    chem_proc = None
    try:
        # -- 1. Start two revocable curators --------------
        poetry_dir = root_dir / "poetry"
        chem_dir = root_dir / "chem"
        for d in (poetry_dir, chem_dir):
            if d.exists():
                import shutil
                shutil.rmtree(d)

        poetry_peers = PeerRegistry()
        chem_peers = PeerRegistry()

        poetry_proc = RevocableCuratorProcess(
            world=fed.poetry.base,
            world_kp=fed.poetry_kp,
            peers=poetry_peers,
            state_dir=poetry_dir,
            cycle_interval=0.1,
            contract_policy=AutoAcceptPolicy(),
            identity=create_identity("curator:poetry"),
        )
        chem_proc = RevocableCuratorProcess(
            world=fed.chemistry.base,
            world_kp=fed.chemistry_kp,
            peers=chem_peers,
            state_dir=chem_dir,
            cycle_interval=0.1,
            contract_policy=AutoAcceptPolicy(),
            identity=create_identity("curator:chemistry"),
        )
        poetry_proc.start()
        chem_proc.start()

        poetry_peers.add(
            "world:chemistry", chem_proc.url,
            fed.chemistry_kp.public_key_hex())
        chem_peers.add(
            "world:poetry", poetry_proc.url,
            fed.poetry_kp.public_key_hex())

        # -- 2. Link --------------------------------------
        for _ in range(20):
            poetry_proc.tick()
            chem_proc.tick()
            if (len(poetry_proc.links()) > 0
                    and len(chem_proc.links()) > 0):
                break

        # -- 3. Establish a contract ----------------------
        terms = ContractTerms(content={
            "kind": "mutual-recognition",
            "scope": "revocation-demo",
        })
        est_ok, est_reason, terms_hash = \
            poetry_proc.propose_contract("world:chemistry", terms)
        assert est_ok, est_reason
        established_before = (
            poetry_proc.contract_registry.is_active(terms_hash)
            and chem_proc.contract_registry.is_active(terms_hash))

        # -- 4. Poetry initiates revocation ---------------
        rev_ok, rev_reason = poetry_proc.request_revocation(
            "world:chemistry", terms_hash,
            reason="mutual agreement ended")

        # -- 5. Both registries show revoked --------------
        poetry_rec = poetry_proc.contract_registry.get(terms_hash)
        chem_rec = chem_proc.contract_registry.get(terms_hash)
        both_revoked = (
            poetry_rec is not None and poetry_rec.is_revoked()
            and chem_rec is not None and chem_rec.is_revoked())
        both_not_active = (
            not poetry_proc.contract_registry.is_active(terms_hash)
            and not chem_proc.contract_registry.is_active(terms_hash))

        # -- 6. Reload from disk --------------------------
        poetry_proc.stop()
        chem_proc.stop()
        poetry_peers2 = PeerRegistry()
        poetry_peers2.add(
            "world:chemistry", "http://ghost",
            fed.chemistry_kp.public_key_hex())
        poetry_reloaded = RevocableCuratorProcess(
            world=fed.poetry.base,
            world_kp=fed.poetry_kp,
            peers=poetry_peers2,
            state_dir=poetry_dir,
            cycle_interval=0.1,
            contract_policy=AutoAcceptPolicy(),
        )
        reloaded_rec = poetry_reloaded.contract_registry.get(terms_hash)
        reloaded_revoked = (
            reloaded_rec is not None and reloaded_rec.is_revoked())
        poetry_reloaded.stop()

        # -- 7. Reverse role: Chemistry initiates --------
        # (Fresh setup for role-reversal test)
        poetry_dir2 = root_dir / "poetry2"
        chem_dir2 = root_dir / "chem2"
        for d in (poetry_dir2, chem_dir2):
            if d.exists():
                import shutil
                shutil.rmtree(d)
        poetry_peers3 = PeerRegistry()
        chem_peers3 = PeerRegistry()
        poetry2 = RevocableCuratorProcess(
            world=fed.poetry.base,
            world_kp=fed.poetry_kp,
            peers=poetry_peers3,
            state_dir=poetry_dir2,
            cycle_interval=0.1,
            contract_policy=AutoAcceptPolicy(),
        )
        chem2 = RevocableCuratorProcess(
            world=fed.chemistry.base,
            world_kp=fed.chemistry_kp,
            peers=chem_peers3,
            state_dir=chem_dir2,
            cycle_interval=0.1,
            contract_policy=AutoAcceptPolicy(),
        )
        poetry2.start()
        chem2.start()
        poetry_peers3.add(
            "world:chemistry", chem2.url,
            fed.chemistry_kp.public_key_hex())
        chem_peers3.add(
            "world:poetry", poetry2.url,
            fed.poetry_kp.public_key_hex())
        try:
            for _ in range(20):
                poetry2.tick()
                chem2.tick()
                if (len(poetry2.links()) > 0
                        and len(chem2.links()) > 0):
                    break
            terms2 = ContractTerms(content={
                "kind": "mutual-recognition",
                "scope": "reverse-demo",
            })
            ok2, _, hash2 = poetry2.propose_contract(
                "world:chemistry", terms2)
            assert ok2
            # Now B (chemistry) initiates revocation
            rev2_ok, rev2_reason = chem2.request_revocation(
                "world:poetry", hash2,
                reason="chem terminates")
            rev2_both_revoked = (
                poetry2.contract_registry.get(hash2) is not None
                and poetry2.contract_registry.get(hash2).is_revoked()
                and chem2.contract_registry.get(hash2) is not None
                and chem2.contract_registry.get(hash2).is_revoked())
        finally:
            poetry2.stop()
            chem2.stop()

        # -- Print ---------------------------------------
        print("=" * 70)
        print("Revocation Coordination — two-phase handshake")
        print("=" * 70)
        print()
        print(f"  Scenario A: Poetry initiates revocation")
        print(f"    Contract established:   {established_before}")
        print(f"    Revocation requested:   {rev_ok} ({rev_reason})")
        print(f"    Poetry registry:        revoked={poetry_rec.is_revoked() if poetry_rec else None}")
        print(f"    Chemistry registry:     revoked={chem_rec.is_revoked() if chem_rec else None}")
        print(f"    Both revoked:           {both_revoked}")
        print(f"    Neither active:         {both_not_active}")
        print()
        print(f"  After restart (fresh process, loads from disk):")
        print(f"    Reloaded record found:  {reloaded_rec is not None}")
        print(f"    Reloaded revoked:       {reloaded_revoked}")
        print()
        print(f"  Scenario B: Chemistry initiates revocation (reverse roles)")
        print(f"    Revocation requested:   {rev2_ok} ({rev2_reason})")
        print(f"    Both revoked:           {rev2_both_revoked}")
        print()
        print("  What this demonstrates:")
        print("    - Revocation requires both parties to sign (C57's")
        print("      design); C70 coordinates the two signatures")
        print("      over the same canonical payload.")
        print("    - The canonical payload is fixed by the first")
        print("      signer. The second signs the same bytes — no")
        print("      negotiation about timestamp or reason.")
        print("    - Either party can initiate. The protocol is")
        print("      symmetric: A-initiated and B-initiated both")
        print("      produce a valid BilateralRevocation.")
        print("    - The registry persists across restarts. A")
        print("      fresh process loads the revoked state from")
        print("      disk without re-coordinating.")
        print()
        print("  Anchor (public domain, Emily Dickinson):")
        print("    'After great pain, a formal feeling comes –'")
        print("    'The Nerves sit ceremonious, like Tombs –'")

        audit = {
            "scenario_a": {
                "established_before": established_before,
                "revocation_ok": rev_ok,
                "revocation_reason": rev_reason,
                "both_revoked": both_revoked,
                "neither_active": both_not_active,
            },
            "reloaded": {
                "record_found": reloaded_rec is not None,
                "revoked": reloaded_revoked,
            },
            "scenario_b": {
                "revocation_ok": rev2_ok,
                "revocation_reason": rev2_reason,
                "both_revoked": rev2_both_revoked,
            },
        }
        (root_dir / "revocation_demo.json").write_text(
            _json.dumps(audit, indent=2))
        print(f"\n  → {root_dir}/revocation_demo.json")
        return audit
    finally:
        if poetry_proc is not None:
            try:
                poetry_proc.stop()
            except Exception:
                pass
        if chem_proc is not None:
            try:
                chem_proc.stop()
            except Exception:
                pass
        fed.stop()
