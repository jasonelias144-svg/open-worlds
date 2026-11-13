"""
multiverse_c69.py — Component 69: Curator-to-Curator Contracts.

Wires C57's contract negotiation into C68's curator daemon.

New curator message types (added to C55's CURATOR_MESSAGE_TYPES):
  - contract_offer:  payload carries a C57 ContractOffer.
  - contract_accept: payload carries a C57 ContractAcceptance.
  - contract_reject: payload carries a C57 ContractRejection.

Flow:
  A.propose_contract(B, terms)
    → A registers offer in its own registry
    → A sends CuratorMessage(contract_offer, {offer: ...})
    → B's server verifies message against peer registry
    → B's _handle_contract_message:
        - verifies offer signature
        - consults acceptance policy
        - if accept: creates ContractAcceptance, registers in
          B's registry, sends back CuratorMessage(contract_accept)
        - if reject: creates ContractRejection, registers in
          B's registry, sends back CuratorMessage(contract_reject)
    → A's server receives accept/reject, verifies, registers,
      saves
    → A's propose_contract returns delivered-accepted or
      delivered-rejected

What C69 does NOT do (v0.1):
  - Revocation. Bilateral revocation needs a two-phase handshake
    (A announces intent, B co-signs). Deferred to v0.2.
  - Contract link requirement. Curators negotiate with any
    registered peer, not only with peers they're linked to. A
    future policy could require the link first.
  - Sync of registries on restart. Each process loads its own
    registry from disk. If two processes diverge (offer accepted
    on B, B's acceptance message lost in flight), the divergence
    is not auto-resolved — a v0.2 concern.

Composition: C3, C55, C57, C65, C68, plus C59/C60's kind-extension
pattern (but the message types, not C48 attestation kinds).

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: acceptance policy, message construction,
    registry persistence, accept flow, reject flow, wrong
    proposer key, target mismatch, malformed payload, end-to-end.
  - "A world never raises on what a visitor sends" — malformed
    contract messages yield Refusal.
  - "History, not rank" — registries and messages are records.

Honest limits (documented, tested):
  - Revocation coordination is not implemented. A contract can
    be revoked via C57's `sign_bilateral_revocation` out of
    band, but the curators do not coordinate the two signatures.
  - The acceptance policy is binary: accept-all or reject-all.
    A real policy would check the offer's terms (e.g., only
    accept contracts of a certain kind).
  - No retry on delivery failure. If B's server is down when A
    proposes, the offer is registered on A's side but never
    delivered; A's next tick does not retry. v0.2.
  - The registry is saved after every change but not
    periodically; a crash between the change and the save
    loses that change.
  - Offers are matched by terms_hash in the registry. Two
    offers with identical terms collide (C57's known issue).
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple

from multiverse_c3 import Ack, Refusal
from multiverse_c13 import HAS_CRYPTO, KeyPair
from multiverse_c55 import (
    CURATOR_MESSAGE_TYPES, CuratorMessage, WorldCurator,
    verify_curator_message, MockCuratorModel, _now,
)
from multiverse_c57 import (
    ContractTerms, ContractRegistry, ContractRecord,
    ContractOffer, ContractAcceptance, ContractRejection,
    ContractNegotiator,
    verify_contract_offer, verify_contract_acceptance,
    verify_contract_rejection,
    sign_acceptance, sign_rejection,
)
from multiverse_c68 import (
    CuratorProcess, PeerRegistry, CuratorStore,
)


# =====================================================================
# Extend CURATOR_MESSAGE_TYPES (additive, same as C59/C60 for C48)
# =====================================================================

CONTRACT_MESSAGE_TYPES = frozenset({
    "contract_offer",
    "contract_accept",
    "contract_reject",
})

if not CONTRACT_MESSAGE_TYPES <= CURATOR_MESSAGE_TYPES:
    CURATOR_MESSAGE_TYPES = (
        CURATOR_MESSAGE_TYPES | CONTRACT_MESSAGE_TYPES)
    import multiverse_c55 as _c55
    _c55.CURATOR_MESSAGE_TYPES = CURATOR_MESSAGE_TYPES


# =====================================================================
# Acceptance policy
# =====================================================================

class ContractAcceptancePolicy(Protocol):
    def should_accept(
        self,
        offer: ContractOffer,
        sender_world_id: str,
    ) -> Tuple[bool, str]:
        """Return (accept, reason)."""
        ...


class AutoAcceptPolicy:
    """Accept every offer. Demo-default; honest for testing."""

    def should_accept(
        self,
        offer: ContractOffer,
        sender_world_id: str,
    ) -> Tuple[bool, str]:
        return (True, "auto-accept")


class RejectAllPolicy:
    """Reject every offer. For testing."""

    def should_accept(
        self,
        offer: ContractOffer,
        sender_world_id: str,
    ) -> Tuple[bool, str]:
        return (False, "policy rejects all")


class KindFilterPolicy:
    """Accept only if the offer's terms.kind matches a list."""

    def __init__(self, allowed_kinds: List[str]):
        self._allowed = set(allowed_kinds)

    def should_accept(
        self,
        offer: ContractOffer,
        sender_world_id: str,
    ) -> Tuple[bool, str]:
        kind = offer.terms.content.get("kind")
        if kind in self._allowed:
            return (True, f"kind {kind!r} allowed")
        return (False, f"kind {kind!r} not in allowed set")


# =====================================================================
# Registry persistence
# =====================================================================

def _record_to_dict(rec: ContractRecord) -> Dict:
    return {
        "terms_hash": rec.terms_hash,
        "world_a_id": rec.world_a_id,
        "world_b_id": rec.world_b_id,
        "offer": rec.offer.to_dict() if rec.offer else None,
        "acceptance": (
            rec.acceptance.to_dict() if rec.acceptance else None),
        "rejection": (
            rec.rejection.to_dict() if rec.rejection else None),
        "revocation": (
            rec.revocation.to_dict() if rec.revocation else None),
        "established_at": rec.established_at,
        "revoked_at": rec.revoked_at,
    }


def _record_from_dict(d: Dict) -> ContractRecord:
    return ContractRecord(
        terms_hash=d["terms_hash"],
        world_a_id=d["world_a_id"],
        world_b_id=d["world_b_id"],
        offer=(ContractOffer.from_dict(d["offer"])
               if d.get("offer") else None),
        acceptance=(ContractAcceptance.from_dict(d["acceptance"])
                    if d.get("acceptance") else None),
        rejection=(ContractRejection.from_dict(d["rejection"])
                   if d.get("rejection") else None),
        revocation=None,  # C57 BilateralRevocation handled elsewhere
        established_at=d.get("established_at"),
        revoked_at=d.get("revoked_at"),
    )


def save_contract_registry(
    registry: ContractRegistry, path: Path,
) -> None:
    """Persist a ContractRegistry. Accesses _records directly
    (C57 does not expose a to_dict; documented here as a
    temporary coupling that a future C57 update might fix)."""
    records = {
        th: _record_to_dict(rec)
        for th, rec in registry._records.items()
    }
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps({
        "kind": "contract_registry",
        "saved_at": _now(),
        "records": records,
    }, indent=2))


def load_contract_registry(path: Path) -> ContractRegistry:
    """Load a persisted ContractRegistry. Returns an empty
    registry on any failure."""
    reg = ContractRegistry()
    if not Path(path).exists():
        return reg
    try:
        data = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError):
        return reg
    if data.get("kind") != "contract_registry":
        return reg
    for th, rec_d in data.get("records", {}).items():
        try:
            rec = _record_from_dict(rec_d)
            reg._records[th] = rec
        except (KeyError, ValueError, TypeError):
            continue
    return reg


# =====================================================================
# ContractAwareCuratorProcess
# =====================================================================

class ContractAwareCuratorProcess(CuratorProcess):
    """A C68 curator that negotiates C57 contracts.

    Adds:
      - A ContractNegotiator (C57) over the same WorldCurator.
      - An acceptance policy.
      - A receive hook that dispatches contract_* messages.
      - A contract_registry.json persisted alongside other state.
      - propose_contract(peer_id, terms) entry point.
    """

    REGISTRY_FILE = "contract_registry.json"

    def __init__(
        self,
        *args,
        contract_policy: Optional[ContractAcceptancePolicy] = None,
        initial_registry: Optional[ContractRegistry] = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        if not HAS_CRYPTO:
            raise RuntimeError(
                "ContractAwareCuratorProcess requires "
                "`cryptography`")
        self._contract_policy = (
            contract_policy or AutoAcceptPolicy())
        self._registry_path = (
            self._store.state_dir / self.REGISTRY_FILE)
        loaded = load_contract_registry(self._registry_path)
        # Merge in any caller-supplied registry
        if initial_registry is not None:
            for th, rec in initial_registry._records.items():
                loaded._records[th] = rec
        self._negotiator = ContractNegotiator(
            self.curator, registry=loaded)
        # Install the receive hook on the curator instance
        self._install_receive_hook()

    # -- Accessors -----------------------------------------------

    @property
    def contract_registry(self) -> ContractRegistry:
        return self._negotiator.registry

    @property
    def contract_policy(self) -> ContractAcceptancePolicy:
        return self._contract_policy

    # -- Hook installation ---------------------------------------

    def _install_receive_hook(self) -> None:
        """Replace curator.receive so contract messages route to
        this process's handler. Non-contract messages fall through
        to C55's receive() unchanged.
        """
        original_receive = self._curator.receive
        process = self

        def hooked(message: CuratorMessage):
            if message.message_type in CONTRACT_MESSAGE_TYPES:
                return process._handle_contract_message(message)
            return original_receive(message)

        self._curator.receive = hooked

    # -- Persistence ---------------------------------------------

    def _save_registry(self) -> None:
        try:
            save_contract_registry(
                self.contract_registry, self._registry_path)
        except Exception:
            pass

    # -- Outbound propose ----------------------------------------

    def propose_contract(
        self,
        peer_id: str,
        terms: ContractTerms,
    ) -> Tuple[bool, str, str]:
        """Propose a contract to a peer. Returns
        (ok, reason, terms_hash)."""
        peer = self._peers.get(peer_id)
        if peer is None:
            return (False, f"peer {peer_id!r} not registered", "")
        try:
            offer = self._negotiator.propose(peer_id, terms)
        except Exception as e:
            return (False, f"propose failed: {e}", "")
        self._save_registry()
        # Build the outbound message
        try:
            message = self._curator._sign_message(
                "contract_offer",
                {"offer": offer.to_dict()})
        except Exception as e:
            return (False, f"sign failed: {e}", offer.terms_hash)
        ok, reason = self._deliver(peer_id, message)
        return (ok, reason, offer.terms_hash)

    # -- Inbound dispatch ----------------------------------------

    def _handle_contract_message(
        self, message: CuratorMessage,
    ):
        """Dispatch a contract message. Returns Ack/Refusal."""
        peer = self._peers.get(message.sender_world_id)
        if peer is None:
            return Refusal(
                reason=(f"unknown peer "
                        f"{message.sender_world_id!r}"))
        peer_key = peer["public_key"]
        if message.message_type == "contract_offer":
            return self._handle_offer(message, peer_key)
        if message.message_type == "contract_accept":
            return self._handle_accept(message, peer_key)
        if message.message_type == "contract_reject":
            return self._handle_reject(message, peer_key)
        return Refusal(
            reason=f"unknown contract message {message.message_type!r}")

    def _handle_offer(
        self, message: CuratorMessage, peer_key: str,
    ):
        try:
            offer = ContractOffer.from_dict(
                message.payload["offer"])
        except (KeyError, ValueError, TypeError) as e:
            return Refusal(
                reason=f"malformed offer: {e}")
        if offer.proposer_public_key != peer_key:
            return Refusal(
                reason=("offer's proposer_public_key does "
                        "not match peer's registered key"))
        if offer.target_world_id != self.world_id:
            return Refusal(
                reason=(f"offer is addressed to "
                        f"{offer.target_world_id!r}, not "
                        f"{self.world_id!r}"))
        if not verify_contract_offer(offer, peer_key):
            return Refusal(
                reason="offer signature INVALID")
        # Register the offer in our registry
        self._negotiator.receive_offer(offer)
        # Consult acceptance policy
        accept, policy_reason = self._contract_policy.should_accept(
            offer, message.sender_world_id)
        if accept:
            # Create and send acceptance
            try:
                acceptance = self._negotiator.accept(offer)
            except Exception as e:
                return Refusal(
                    reason=f"accept failed: {e}")
            self._save_registry()
            try:
                msg = self._curator._sign_message(
                    "contract_accept",
                    {"acceptance": acceptance.to_dict(),
                     "terms_hash": offer.terms_hash})
            except Exception as e:
                return Refusal(
                    reason=f"sign failed: {e}")
            ok, reason = self._deliver(
                message.sender_world_id, msg)
            if not ok:
                return Refusal(
                    reason=(f"delivery of acceptance "
                            f"failed: {reason}"))
        else:
            # Create and send rejection
            try:
                rejection = self._negotiator.reject(
                    offer, reason=policy_reason)
            except Exception as e:
                return Refusal(
                    reason=f"reject failed: {e}")
            self._save_registry()
            try:
                msg = self._curator._sign_message(
                    "contract_reject",
                    {"rejection": rejection.to_dict(),
                     "terms_hash": offer.terms_hash})
            except Exception as e:
                return Refusal(
                    reason=f"sign failed: {e}")
            ok, reason = self._deliver(
                message.sender_world_id, msg)
            if not ok:
                return Refusal(
                    reason=(f"delivery of rejection "
                            f"failed: {reason}"))
        return Ack(entity_id=self.world_id,
                    timestamp=_now())

    def _handle_accept(
        self, message: CuratorMessage, peer_key: str,
    ):
        try:
            acceptance = ContractAcceptance.from_dict(
                message.payload["acceptance"])
        except (KeyError, ValueError, TypeError) as e:
            return Refusal(
                reason=f"malformed acceptance: {e}")
        if acceptance.acceptor_public_key != peer_key:
            return Refusal(
                reason=("acceptance's acceptor_public_key does "
                        "not match peer's registered key"))
        if not verify_contract_acceptance(acceptance, peer_key):
            return Refusal(
                reason="acceptance signature INVALID")
        # Register
        self._negotiator.receive_acceptance(acceptance)
        self._save_registry()
        return Ack(entity_id=self.world_id,
                    timestamp=_now())

    def _handle_reject(
        self, message: CuratorMessage, peer_key: str,
    ):
        try:
            rejection = ContractRejection.from_dict(
                message.payload["rejection"])
        except (KeyError, ValueError, TypeError) as e:
            return Refusal(
                reason=f"malformed rejection: {e}")
        if rejection.rejector_public_key != peer_key:
            return Refusal(
                reason=("rejection's rejector_public_key does "
                        "not match peer's registered key"))
        if not verify_contract_rejection(rejection, peer_key):
            return Refusal(
                reason="rejection signature INVALID")
        self._negotiator.receive_rejection(rejection)
        self._save_registry()
        return Ack(entity_id=self.world_id,
                    timestamp=_now())

    # -- Convenience queries -------------------------------------

    def established_contracts(self) -> List[ContractRecord]:
        return self.contract_registry.established()

    def is_contract_active(self, terms_hash: str) -> bool:
        return self.contract_registry.is_active(terms_hash)


def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Two contract-aware curators. Full lifecycle:

    1. Deploy federation (C66).
    2. Start two ContractAwareCuratorProcess, empty peers.
    3. Add peers, tick until linked.
    4. Poetry proposes a contract to Chemistry (AutoAcceptPolicy).
    5. Chemistry auto-accepts during the delivery, sends back.
    6. Poetry registers the acceptance.
    7. Both registries show the contract as established.
    8. Reload from disk in a fresh process to prove persistence.
    """
    import json as _json
    from multiverse_c1 import create_identity
    from multiverse_c4 import PoetryWorld
    from multiverse_c5 import ChemistryWorld
    from multiverse_c13 import KeyPair
    from multiverse_c57 import (
        ContractTerms, ContractRegistry, ContractOffer,
        ContractAcceptance,
        verify_contract_offer, verify_contract_acceptance,
    )
    from multiverse_c66 import (
        DeployConfig, deploy_federation,
        _patch_c65_manifest_verification,
    )

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    _patch_c65_manifest_verification()

    if artifact_dir is None:
        artifact_dir = "artifacts"
    root_dir = Path(artifact_dir) / "curator_contracts"
    root_dir.mkdir(parents=True, exist_ok=True)
    fed_dir = root_dir / "federation"
    poetry_dir = root_dir / "curator_poetry"
    chem_dir = root_dir / "curator_chemistry"

    for d in (fed_dir, poetry_dir, chem_dir):
        if d.exists():
            import shutil
            shutil.rmtree(d)

    fed = deploy_federation(DeployConfig(
        state_dir=fed_dir,
        federation_name="Curator Contracts Demo",
    ))

    poetry_proc = None
    chem_proc = None
    try:
        # -- 1. Start two contract-aware curators --------
        poetry_peers = PeerRegistry()
        chem_peers = PeerRegistry()

        poetry_proc = ContractAwareCuratorProcess(
            world=fed.poetry.base,
            world_kp=fed.poetry_kp,
            peers=poetry_peers,
            state_dir=poetry_dir,
            cycle_interval=0.3,
            contract_policy=AutoAcceptPolicy(),
            identity=create_identity("curator:poetry"),
        )
        chem_proc = ContractAwareCuratorProcess(
            world=fed.chemistry.base,
            world_kp=fed.chemistry_kp,
            peers=chem_peers,
            state_dir=chem_dir,
            cycle_interval=0.3,
            contract_policy=AutoAcceptPolicy(),
            identity=create_identity("curator:chemistry"),
        )
        poetry_proc.start()
        chem_proc.start()

        # -- 2. Add peers, tick until linked -------------
        poetry_peers.add(
            "world:chemistry",
            chem_proc.url,
            fed.chemistry_kp.public_key_hex())
        chem_peers.add(
            "world:poetry",
            poetry_proc.url,
            fed.poetry_kp.public_key_hex())

        linked_at = None
        for i in range(20):
            poetry_proc.tick()
            chem_proc.tick()
            if (len(poetry_proc.links()) > 0
                    and len(chem_proc.links()) > 0):
                linked_at = i
                break

        # -- 3. Poetry proposes a contract ---------------
        terms = ContractTerms(content={
            "kind": "mutual-recognition",
            "poetry_accepts": "chem-acts",
            "chemistry_accepts": "poetry-acts",
        })
        propose_ok, propose_reason, terms_hash = \
            poetry_proc.propose_contract("world:chemistry", terms)

        # -- 4. Check both registries -------------------
        poetry_rec = poetry_proc.contract_registry.get(terms_hash)
        chem_rec = chem_proc.contract_registry.get(terms_hash)
        poetry_established = (
            poetry_rec is not None and poetry_rec.is_established())
        chem_established = (
            chem_rec is not None and chem_rec.is_established())

        # -- 5. Verify the artifacts -------------------
        offer = poetry_rec.offer
        acceptance = poetry_rec.acceptance
        offer_ok = verify_contract_offer(
            offer, fed.poetry_kp.public_key_hex())
        acceptance_ok = verify_contract_acceptance(
            acceptance, fed.chemistry_kp.public_key_hex())

        # -- 6. Restart, reload from disk --------------
        poetry_proc.stop()
        chem_proc.stop()

        # Fresh instances, fresh construction (loads from disk)
        poetry_peers2 = PeerRegistry()
        poetry_peers2.add(
            "world:chemistry",
            "http://example:9999",  # not live; only for peer check
            fed.chemistry_kp.public_key_hex())
        poetry_reloaded = ContractAwareCuratorProcess(
            world=fed.poetry.base,
            world_kp=fed.poetry_kp,
            peers=poetry_peers2,
            state_dir=poetry_dir,
            cycle_interval=0.3,
            contract_policy=AutoAcceptPolicy(),
            identity=create_identity("curator:poetry"),
        )
        reloaded_rec = poetry_reloaded.contract_registry.get(terms_hash)
        reloaded_established = (
            reloaded_rec is not None
            and reloaded_rec.is_established())

        # -- Print -------------------------------------
        print("=" * 70)
        print("Curator-to-Curator Contracts — C57 artifacts, "
              "C68 transport")
        print("=" * 70)
        print()
        print(f"  Linked at tick:  {linked_at + 1 if linked_at is not None else 'never'}")
        print()
        print(f"  Poetry proposes to Chemistry:")
        print(f"    Propose ok:       {propose_ok}")
        print(f"    Reason:           {propose_reason}")
        print(f"    Terms hash:       {terms_hash[:16]}...")
        print()
        print(f"  Both registries see the contract:")
        print(f"    Poetry established:   {poetry_established}")
        print(f"    Chemistry established: {chem_established}")
        print()
        print(f"  Artifacts verify with world keys:")
        print(f"    Offer (by poetry):     {offer_ok}")
        print(f"    Acceptance (by chem):  {acceptance_ok}")
        print()
        print(f"  After restart (fresh process, loads from disk):")
        print(f"    Reloaded record found: {reloaded_rec is not None}")
        print(f"    Reloaded established:  {reloaded_established}")
        print()
        print(f"  Contract details:")
        print(f"    World A: {poetry_rec.world_a_id}")
        print(f"    World B: {poetry_rec.world_b_id}")
        print(f"    Terms:   {terms.content}")
        print()
        print("  What this demonstrates:")
        print("    - C57's contract artifacts are the payload of")
        print("      C68's curator messages. No new artifacts; only")
        print("      new message types.")
        print("    - The peer registry is the trust anchor: a")
        print("      message from an unregistered world is refused")
        print("      before its contract payload is even parsed.")
        print("    - The acceptance policy is pluggable. AutoAccept")
        print("      makes the demo run without human input; a real")
        print("      deploy would use KindFilterPolicy or a custom")
        print("      rule.")
        print("    - Registries persist to disk. A fresh process")
        print("      loaded from the same state_dir sees the")
        print("      contract immediately.")
        print()
        print("  Anchor (public domain, Emily Dickinson):")
        print("    'I'm Nobody! Who are you?'")
        print("    'Are you – Nobody – too?'")

        audit = {
            "linked_at": (
                linked_at + 1 if linked_at is not None else None),
            "propose": {
                "ok": propose_ok,
                "reason": propose_reason,
                "terms_hash": terms_hash,
            },
            "poetry": {
                "established": poetry_established,
                "world_a_id": poetry_rec.world_a_id,
                "world_b_id": poetry_rec.world_b_id,
            },
            "chemistry": {
                "established": chem_established,
            },
            "artifacts": {
                "offer_verifies": offer_ok,
                "acceptance_verifies": acceptance_ok,
            },
            "reloaded": {
                "record_found": reloaded_rec is not None,
                "established": reloaded_established,
            },
        }
        (root_dir / "curator_contracts_demo.json").write_text(
            _json.dumps(audit, indent=2))
        print(f"\n  → {root_dir}/curator_contracts_demo.json")
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
