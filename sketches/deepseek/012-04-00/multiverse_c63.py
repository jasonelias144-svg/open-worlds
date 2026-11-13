"""
multiverse_c63.py — Component 63: Policy-Driven Contract Disputes.

C58 enforces one contract policy: "established and not revoked."
C63 makes the policy explicit, signed, and configurable.

Three policies provided:
  - current_status: valid iff currently established, not revoked
    (equivalent to C58's default behavior).
  - claimed_time:   valid iff citation's claimed time falls in the
    contract's active window, using the artifacts' own timestamps.
  - committed_time: valid iff the ledger's ordering shows the
    citation committed between establishment and revocation.

The policy is a signed declarative artifact (like C50's policy
texts). Two verifiers with the same policy and the same facts get
the same verdict. A reader with the policy knows the world's rule
without reading its code.

What C63 does NOT do:
  - Arbitrate between policies. If two worlds disagree about
    which policy is correct, that's their disagreement, not a
    protocol question. C63 makes each world's answer legible.
  - Verify the artifacts. It assumes the caller has already
    verified the contract record (C57) and the citation. It
    answers "given these facts, does the policy honor the
    citation?" — the facts are the caller's responsibility.
  - Change C58. C58's base class is untouched; the subclass
    replaces the state check with the policy-driven one.

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per policy, per case, per ledger state, plus
    C58-equivalence for current_status.
  - "A world never raises on what a visitor sends" — resolver
    returns verdicts; act refuses with reasons.
  - "History, not rank" — verdicts are diagnostic.

Honest limits (documented, tested):
  - World-involvement and cites_world checks remain C58's
    (unconditional). A policy that wanted to relax those would
    need a further override.
  - The `committed_time` policy requires the ledger. If it's
    absent, the policy refuses with a clear reason.
  - Citation hash: the caller must supply it (the resolver
    cannot derive it — the citation artifact may be an act, a
    wrapper, or an announcement). If missing, `committed_time`
    refuses.
  - No policy chaining. A policy is atomic.
  - No policy revocation. Once published, a policy is a fact
    about time. Publishing a new policy is a new artifact.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from multiverse_c3 import Act, Ack, Refusal
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c57 import ContractRecord
from multiverse_c58 import ContractAwarePoetryWorld


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_payload(p: bytes) -> str:
    return hashlib.sha256(p).hexdigest()


# =====================================================================
# ContractPolicy
# =====================================================================

@dataclass(frozen=True)
class ContractPolicy:
    """A signed declarative rule for resolving citation disputes.

    content["rule"] names the rule kind; content contains the
    fields the rule needs. The three standard rules are:

      {"rule": "current_status"}

      {"rule": "claimed_time"}

      {"rule": "committed_time",
       "requires_ledger": True}
    """
    policy_id: str
    version: int
    content: Dict
    author_world_id: str
    author_public_key: str
    timestamp: str
    signature: str

    def __post_init__(self):
        for f in ("policy_id", "author_world_id",
                  "author_public_key", "timestamp", "signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if len(self.author_public_key) != 64:
            raise ValueError(
                "author_public_key must be 64 hex chars")
        if self.version < 1:
            raise ValueError("version must be >= 1")
        if not isinstance(self.content, dict):
            raise ValueError("content must be a dict")
        rule = self.content.get("rule")
        if rule not in (
                "current_status", "claimed_time",
                "committed_time"):
            raise ValueError(
                f"unknown rule {rule!r}; must be one of "
                f"current_status, claimed_time, committed_time")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "contract_policy",
            "policy_id": self.policy_id,
            "version": self.version,
            "content": self.content,
            "author_world_id": self.author_world_id,
            "author_public_key": self.author_public_key,
            "timestamp": self.timestamp,
        })

    def policy_hash(self) -> str:
        return _hash_payload(self.canonical_payload())

    @property
    def rule(self) -> str:
        return self.content["rule"]

    def to_dict(self) -> Dict:
        return {
            "policy_id": self.policy_id,
            "version": self.version,
            "content": self.content,
            "author_world_id": self.author_world_id,
            "author_public_key": self.author_public_key,
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "ContractPolicy":
        return cls(
            policy_id=d["policy_id"],
            version=d["version"],
            content=d["content"],
            author_world_id=d["author_world_id"],
            author_public_key=d["author_public_key"],
            timestamp=d["timestamp"],
            signature=d["signature"],
        )


def verify_contract_policy(
    policy: ContractPolicy,
    expected_public_key: Optional[str] = None,
) -> bool:
    if not HAS_CRYPTO:
        return False
    try:
        if not isinstance(policy, ContractPolicy):
            return False
        key = expected_public_key or policy.author_public_key
        return verify_signature(
            key, policy.canonical_payload(), policy.signature)
    except Exception:
        return False


# =====================================================================
# Standard policy constructors
# =====================================================================

def make_current_status_policy(
    policy_id: str,
    author_world_id: str,
    author_kp: KeyPair,
    version: int = 1,
    timestamp: Optional[str] = None,
) -> ContractPolicy:
    """Policy: valid iff contract is currently established and
    not revoked. Equivalent to C58's default behavior.
    """
    if not HAS_CRYPTO:
        raise RuntimeError(
            "make_current_status_policy requires cryptography")
    if timestamp is None:
        timestamp = _now()
    content = {"rule": "current_status"}
    payload = canonical_bytes({
        "kind": "contract_policy",
        "policy_id": policy_id,
        "version": version,
        "content": content,
        "author_world_id": author_world_id,
        "author_public_key": author_kp.public_key_hex(),
        "timestamp": timestamp,
    })
    return ContractPolicy(
        policy_id=policy_id,
        version=version,
        content=content,
        author_world_id=author_world_id,
        author_public_key=author_kp.public_key_hex(),
        timestamp=timestamp,
        signature=author_kp.sign(payload).hex(),
    )


def make_claimed_time_policy(
    policy_id: str,
    author_world_id: str,
    author_kp: KeyPair,
    version: int = 1,
    timestamp: Optional[str] = None,
) -> ContractPolicy:
    """Policy: valid iff citation's claimed time falls within the
    contract's active window, using the artifacts' own timestamps.
    """
    if not HAS_CRYPTO:
        raise RuntimeError(
            "make_claimed_time_policy requires cryptography")
    if timestamp is None:
        timestamp = _now()
    content = {"rule": "claimed_time"}
    payload = canonical_bytes({
        "kind": "contract_policy",
        "policy_id": policy_id,
        "version": version,
        "content": content,
        "author_world_id": author_world_id,
        "author_public_key": author_kp.public_key_hex(),
        "timestamp": timestamp,
    })
    return ContractPolicy(
        policy_id=policy_id,
        version=version,
        content=content,
        author_world_id=author_world_id,
        author_public_key=author_kp.public_key_hex(),
        timestamp=timestamp,
        signature=author_kp.sign(payload).hex(),
    )


def make_committed_time_policy(
    policy_id: str,
    author_world_id: str,
    author_kp: KeyPair,
    version: int = 1,
    timestamp: Optional[str] = None,
) -> ContractPolicy:
    """Policy: valid iff the ledger's ordering shows the citation
    committed between establishment and (if present) revocation.
    Requires the caller to supply a ledger view.
    """
    if not HAS_CRYPTO:
        raise RuntimeError(
            "make_committed_time_policy requires cryptography")
    if timestamp is None:
        timestamp = _now()
    content = {
        "rule": "committed_time",
        "requires_ledger": True,
    }
    payload = canonical_bytes({
        "kind": "contract_policy",
        "policy_id": policy_id,
        "version": version,
        "content": content,
        "author_world_id": author_world_id,
        "author_public_key": author_kp.public_key_hex(),
        "timestamp": timestamp,
    })
    return ContractPolicy(
        policy_id=policy_id,
        version=version,
        content=content,
        author_world_id=author_world_id,
        author_public_key=author_kp.public_key_hex(),
        timestamp=timestamp,
        signature=author_kp.sign(payload).hex(),
    )


# =====================================================================
# DisputeVerdict
# =====================================================================

@dataclass(frozen=True)
class DisputeVerdict:
    honored: bool
    rule_applied: str
    reason: str
    details: Dict

    def format(self) -> str:
        marker = "✓" if self.honored else "✗"
        return "\n".join([
            "Contract Citation Dispute",
            "=" * 50,
            f"  honored: {self.honored}  {marker}",
            f"  rule:    {self.rule_applied}",
            f"  reason:  {self.reason}",
            f"  details: {self.details}",
        ])

    def to_dict(self) -> Dict:
        return {
            "honored": self.honored,
            "rule_applied": self.rule_applied,
            "reason": self.reason,
            "details": dict(self.details),
        }


# =====================================================================
# The resolver
# =====================================================================

def resolve_citation_dispute(
    policy: ContractPolicy,
    record: ContractRecord,
    citation_claimed_time: str,
    citation_hash: Optional[str] = None,
    ledger: Optional[Dict[str, int]] = None,
) -> DisputeVerdict:
    """Apply a policy to resolve a citation dispute. Never raises.

    `record` is a C57 ContractRecord (from the world's registry).
    `citation_claimed_time` is the time the citation claims.
    `citation_hash` is the hash of whatever artifact represents
    the citation in the ledger (needed for committed_time).
    `ledger` maps artifact_hash -> first-seen commit index
    (needed for committed_time).
    """
    if not HAS_CRYPTO:
        return DisputeVerdict(
            honored=False,
            rule_applied=policy.content.get("rule", "unknown"),
            reason="cryptography not installed",
            details={})
    if not isinstance(policy, ContractPolicy):
        return DisputeVerdict(
            honored=False, rule_applied="unknown",
            reason="not a ContractPolicy", details={})
    if not isinstance(record, ContractRecord):
        return DisputeVerdict(
            honored=False, rule_applied=policy.rule,
            reason="not a ContractRecord", details={})
    # Verify the policy itself
    if not verify_contract_policy(policy):
        return DisputeVerdict(
            honored=False, rule_applied=policy.rule,
            reason="policy signature INVALID", details={})

    rule = policy.content.get("rule")
    if rule == "current_status":
        return _resolve_current_status(record)
    if rule == "claimed_time":
        return _resolve_claimed_time(
            record, citation_claimed_time)
    if rule == "committed_time":
        return _resolve_committed_time(
            record, citation_hash, ledger)
    return DisputeVerdict(
        honored=False, rule_applied=rule or "unknown",
        reason=f"unknown rule {rule!r}", details={})


def _resolve_current_status(
    record: ContractRecord,
) -> DisputeVerdict:
    details = {
        "is_established": record.is_established(),
        "is_pending": record.is_pending(),
        "is_rejected": record.is_rejected(),
        "is_revoked": record.is_revoked(),
    }
    if record.is_revoked():
        return DisputeVerdict(
            honored=False, rule_applied="current_status",
            reason="contract is currently revoked",
            details=details)
    if record.is_pending():
        return DisputeVerdict(
            honored=False, rule_applied="current_status",
            reason="contract is still pending",
            details=details)
    if record.is_rejected():
        return DisputeVerdict(
            honored=False, rule_applied="current_status",
            reason="contract was rejected",
            details=details)
    if not record.is_established():
        return DisputeVerdict(
            honored=False, rule_applied="current_status",
            reason="contract is not established",
            details=details)
    return DisputeVerdict(
        honored=True, rule_applied="current_status",
        reason="contract is currently established",
        details=details)


def _parse_iso(ts: str) -> Optional[datetime]:
    if not isinstance(ts, str) or not ts:
        return None
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def _resolve_claimed_time(
    record: ContractRecord, citation_claimed_time: str,
) -> DisputeVerdict:
    details = {
        "citation_claimed_time": citation_claimed_time,
        "established_at": record.established_at,
        "revoked_at": record.revoked_at,
    }
    if not record.is_established() and not record.is_revoked():
        # Pending or rejected — no establishment time
        return DisputeVerdict(
            honored=False, rule_applied="claimed_time",
            reason=("contract was never established "
                     "(pending or rejected)"),
            details=details)
    if record.acceptance is None:
        return DisputeVerdict(
            honored=False, rule_applied="claimed_time",
            reason="contract has no acceptance timestamp",
            details=details)
    estab_dt = _parse_iso(record.established_at or "")
    cite_dt = _parse_iso(citation_claimed_time)
    if estab_dt is None or cite_dt is None:
        return DisputeVerdict(
            honored=False, rule_applied="claimed_time",
            reason="cannot parse establishment or citation time",
            details=details)
    if cite_dt < estab_dt:
        return DisputeVerdict(
            honored=False, rule_applied="claimed_time",
            reason=("citation claimed before establishment "
                     f"({citation_claimed_time} < "
                     f"{record.established_at})"),
            details=details)
    if record.revocation is not None:
        rev_dt = _parse_iso(record.revoked_at or "")
        if rev_dt is None:
            return DisputeVerdict(
                honored=False, rule_applied="claimed_time",
                reason="cannot parse revocation time",
                details=details)
        if cite_dt > rev_dt:
            return DisputeVerdict(
                honored=False, rule_applied="claimed_time",
                reason=("citation claimed after revocation "
                         f"({citation_claimed_time} > "
                         f"{record.revoked_at})"),
                details=details)
    return DisputeVerdict(
        honored=True, rule_applied="claimed_time",
        reason=("citation claimed within contract's active "
                 "window"),
        details=details)


def _resolve_committed_time(
    record: ContractRecord,
    citation_hash: Optional[str],
    ledger: Optional[Dict[str, int]],
) -> DisputeVerdict:
    details = {
        "citation_hash": citation_hash,
        "ledger_present": ledger is not None,
    }
    if ledger is None:
        return DisputeVerdict(
            honored=False, rule_applied="committed_time",
            reason="policy requires ledger; none supplied",
            details=details)
    if citation_hash is None:
        return DisputeVerdict(
            honored=False, rule_applied="committed_time",
            reason="citation_hash required by policy",
            details=details)
    if record.offer is None:
        return DisputeVerdict(
            honored=False, rule_applied="committed_time",
            reason="contract has no offer",
            details=details)
    estab_hash = record.offer.offer_hash()
    details["establishment_hash"] = estab_hash
    estab_idx = ledger.get(estab_hash)
    cite_idx = ledger.get(citation_hash)
    details["establishment_index"] = estab_idx
    details["citation_index"] = cite_idx
    if estab_idx is None:
        return DisputeVerdict(
            honored=False, rule_applied="committed_time",
            reason="establishment not in ledger",
            details=details)
    if cite_idx is None:
        return DisputeVerdict(
            honored=False, rule_applied="committed_time",
            reason="citation not in ledger",
            details=details)
    if cite_idx < estab_idx:
        return DisputeVerdict(
            honored=False, rule_applied="committed_time",
            reason=(f"citation committed before establishment "
                     f"(index {cite_idx} < {estab_idx})"),
            details=details)
    if record.revocation is not None:
        rev_hash = _hash_payload(
            record.revocation.canonical_payload())
        details["revocation_hash"] = rev_hash
        rev_idx = ledger.get(rev_hash)
        details["revocation_index"] = rev_idx
        if rev_idx is None:
            return DisputeVerdict(
                honored=False, rule_applied="committed_time",
                reason="revocation not in ledger",
                details=details)
        if cite_idx > rev_idx:
            return DisputeVerdict(
                honored=False, rule_applied="committed_time",
                reason=(f"citation committed after revocation "
                         f"(index {cite_idx} > {rev_idx})"),
                details=details)
    return DisputeVerdict(
        honored=True, rule_applied="committed_time",
        reason=("ledger ordering shows citation between "
                 "establishment and revocation"),
        details=details)


# =====================================================================
# PolicyAwareContractAwareWorld
# =====================================================================

class PolicyAwareContractAwareWorld(ContractAwarePoetryWorld):
    """A C58 world whose citation check is driven by a policy.

    Inherits everything from C58 except `_check_citation`, which
    is overridden: instead of C58's hardcoded "established and
    not revoked" rule, this world applies its policy to resolve
    the citation.

    The world-involvement and cites_world checks from C58 are
    preserved (they are facts about *this world's* relationship
    to the contract, not lifecycle questions a policy would
    answer).
    """

    def __init__(
        self,
        entity_id: str,
        name: str,
        *args,
        policy: ContractPolicy,
        ledger_view: Optional[Dict[str, int]] = None,
        **kwargs,
    ):
        super().__init__(entity_id, name, *args, **kwargs)
        if not verify_contract_policy(policy):
            raise ValueError(
                "policy signature does not verify")
        self._policy = policy
        self._ledger_view: Dict[str, int] = (
            dict(ledger_view) if ledger_view else {})

    @property
    def policy(self) -> ContractPolicy:
        return self._policy

    def set_ledger_view(self, ledger_view: Dict[str, int]) -> None:
        self._ledger_view = dict(ledger_view)

    def _check_citation(self, act: Act) -> Optional[str]:
        payload = act.payload or {}
        cites = payload.get("cites_contract")
        if not cites:
            if self._require_citation:
                return "act must cite a contract"
            return None
        if not isinstance(cites, str) or len(cites) != 64:
            return "cites_contract must be 64 hex chars"
        record = self._contract_registry.get(cites)
        if record is None:
            return (f"cited contract not found: {cites[:16]}...")
        # World-involvement checks (C58's discipline, kept)
        world_id = self._manifest.entity_id
        if (record.world_a_id != world_id
                and record.world_b_id != world_id):
            return "cited contract does not involve this world"
        cites_world = payload.get("cites_world")
        if cites_world is not None:
            expected = (world_id, cites_world)
            actual = (record.world_a_id, record.world_b_id)
            if not (actual == expected
                    or actual == expected[::-1]):
                return ("cited contract does not match "
                         "cites_world")
        # Policy resolution
        claimed = payload.get(
            "claimed_time", _now())
        citation_hash = payload.get("citation_hash")
        verdict = resolve_citation_dispute(
            policy=self._policy,
            record=record,
            citation_claimed_time=claimed,
            citation_hash=citation_hash,
            ledger=self._ledger_view,
        )
        if not verdict.honored:
            return (f"citation refused by policy "
                     f"'{verdict.rule_applied}': {verdict.reason}")
        return None
