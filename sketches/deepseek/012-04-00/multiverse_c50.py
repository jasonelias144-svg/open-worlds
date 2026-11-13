"""
multiverse_c50.py — Component 50: The Institutional Architecture.

Sixth architecture. The unit's behavior is determined by a
signed PolicyText, not by code, weights, thresholds, or a
callable. Amendments are themselves signed artifacts. Rulings
carry the policy_hash they applied and the clause_id that fired,
so a third party can reproduce the outcome without the unit.

Structural differences from C41-C47:
  C41 Octopus:    unit has model + intent queue
  C42 Relay:      unit has inputs + threshold
  C43 Swarm:      unit has env stream + position
  C44 Council:    unit has a callable decision_rule (opaque)
  C47 Autonomic:  unit has state + target
  C50 Institution: unit has policy (signed doc) + policy history

The distinguishing test: a third party with the policy text and
facts reproduces the ruling exactly, without the unit's help.

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per behavior, per predicate, plus
    determinism and reproducibility tests.
  - "A world never raises on what a visitor sends" — act
    handler catches, returns Refusal on bad payloads.
  - "History, not rank" — policy history and ruling log are
    append-only records.

Honest limits (documented, tested):
  - The evaluator has a specific clause language (eq, ne, gt,
    lt, ge, le, in, contains, exists, all_of, any_of, not).
    Not Turing-complete; not meant to be.
  - Amend authorization is TOFU: the initial policy's
    author_public_key is trusted at construction; every
    amendment must be by the same author. Changing the author
    requires a different mechanism (a meta-policy) not in this
    prototype.
  - No cross-unit policy sharing. Two units could hold the
    same PolicyText; the protocol doesn't give them a way to
    know. That's federation (C48), not institution.
  - No delegation. A unit's policy can't say "ask unit B".
  - Facts are unstructured dicts; no schema validation.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from multiverse_c1 import Identity, create_identity
from multiverse_c3 import Act, Ack, Refusal
from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c42 import SignalWorld


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_payload(p: bytes) -> str:
    return hashlib.sha256(p).hexdigest()


EVALUATOR_VERSION = "1.0"


# =====================================================================
# Clause
# =====================================================================

@dataclass(frozen=True)
class Clause:
    clause_id: str
    condition: Dict
    outcome: str
    notes: str = ""

    def __post_init__(self):
        if not isinstance(self.clause_id, str) or not self.clause_id:
            raise ValueError("clause_id required")
        if not isinstance(self.condition, dict):
            raise ValueError("condition must be dict")
        if not isinstance(self.outcome, str) or not self.outcome:
            raise ValueError("outcome required")

    def to_dict(self) -> Dict:
        return {"clause_id": self.clause_id,
                "condition": self.condition,
                "outcome": self.outcome,
                "notes": self.notes}

    @classmethod
    def from_dict(cls, d: Dict) -> "Clause":
        return cls(clause_id=d["clause_id"],
                   condition=d["condition"],
                   outcome=d["outcome"],
                   notes=d.get("notes", ""))


# =====================================================================
# PolicyText
# =====================================================================

@dataclass(frozen=True)
class PolicyText:
    policy_id: str
    version: int
    clauses: Tuple[Clause, ...]
    default_outcome: str
    author_token: str
    author_public_key: str
    author_signature: str

    def __post_init__(self):
        for f in ("policy_id", "default_outcome",
                  "author_token", "author_public_key",
                  "author_signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if self.version < 1:
            raise ValueError("version must be >= 1")
        if not self.clauses:
            raise ValueError("policy needs at least one clause")
        ids = [c.clause_id for c in self.clauses]
        if len(ids) != len(set(ids)):
            raise ValueError("clause_ids must be unique")
        if len(self.author_public_key) != 64:
            raise ValueError(
                "author_public_key must be 64 hex chars")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "policy_text",
            "policy_id": self.policy_id,
            "version": self.version,
            "clauses": [c.to_dict() for c in self.clauses],
            "default_outcome": self.default_outcome,
            "author_token": self.author_token,
            "author_public_key": self.author_public_key,
        })

    def policy_hash(self) -> str:
        return _hash_payload(self.canonical_payload())

    def to_dict(self) -> Dict:
        return {"policy_id": self.policy_id,
                "version": self.version,
                "clauses": [c.to_dict() for c in self.clauses],
                "default_outcome": self.default_outcome,
                "author_token": self.author_token,
                "author_public_key": self.author_public_key,
                "author_signature": self.author_signature}

    @classmethod
    def from_dict(cls, d: Dict) -> "PolicyText":
        return cls(
            policy_id=d["policy_id"],
            version=d["version"],
            clauses=tuple(
                Clause.from_dict(c) for c in d["clauses"]),
            default_outcome=d["default_outcome"],
            author_token=d["author_token"],
            author_public_key=d["author_public_key"],
            author_signature=d["author_signature"],
        )


def sign_policy(
    policy_id: str,
    version: int,
    clauses: List[Clause],
    default_outcome: str,
    author: Identity,
    author_kp: KeyPair,
) -> PolicyText:
    if not HAS_CRYPTO:
        raise RuntimeError(
            "sign_policy requires `cryptography`")
    payload = canonical_bytes({
        "kind": "policy_text",
        "policy_id": policy_id,
        "version": version,
        "clauses": [c.to_dict() for c in clauses],
        "default_outcome": default_outcome,
        "author_token": author.token,
        "author_public_key": author_kp.public_key_hex(),
    })
    return PolicyText(
        policy_id=policy_id, version=version,
        clauses=tuple(clauses),
        default_outcome=default_outcome,
        author_token=author.token,
        author_public_key=author_kp.public_key_hex(),
        author_signature=author_kp.sign(payload).hex(),
    )


def verify_policy_signature(
    policy: PolicyText,
    expected_public_key: Optional[str] = None,
) -> bool:
    if not HAS_CRYPTO:
        return False
    try:
        key = expected_public_key or policy.author_public_key
        return verify_signature(
            key, policy.canonical_payload(),
            policy.author_signature)
    except Exception:
        return False


# =====================================================================
# Evaluator — deterministic, general-purpose
# =====================================================================

def _get_nested(facts: Dict, path: Optional[str]):
    if path is None:
        return None
    current = facts
    for part in path.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current


def _matches(condition: Dict, facts: Dict) -> bool:
    if "all_of" in condition:
        items = condition["all_of"]
        if not isinstance(items, list):
            return False
        return all(_matches(c, facts)
                   for c in items if isinstance(c, dict))
    if "any_of" in condition:
        items = condition["any_of"]
        if not isinstance(items, list):
            return False
        return any(_matches(c, facts)
                   for c in items if isinstance(c, dict))
    if "not" in condition:
        inner = condition["not"]
        if not isinstance(inner, dict):
            return False
        return not _matches(inner, facts)
    field = condition.get("field")
    op = condition.get("op")
    expected = condition.get("value")
    actual = _get_nested(facts, field)
    if op == "eq": return actual == expected
    if op == "ne": return actual != expected
    if op == "exists": return actual is not None
    try:
        if op == "gt": return actual is not None and actual > expected
        if op == "lt": return actual is not None and actual < expected
        if op == "ge": return actual is not None and actual >= expected
        if op == "le": return actual is not None and actual <= expected
        if op == "in": return actual in expected
        if op == "contains": return expected in actual
    except TypeError:
        return False
    return False


def evaluate_policy(
    policy: PolicyText, facts: Dict,
) -> Tuple[Optional[str], str]:
    """First matching clause fires. Otherwise default. Deterministic."""
    for clause in policy.clauses:
        if _matches(clause.condition, facts):
            return (clause.clause_id, clause.outcome)
    return (None, policy.default_outcome)


# =====================================================================
# Ruling and Amendment
# =====================================================================

@dataclass(frozen=True)
class Ruling:
    unit_id: str
    unit_public_key: str
    policy_hash: str
    policy_version: int
    facts_hash: str
    fired_clause_id: Optional[str]
    outcome: str
    evaluator_version: str
    timestamp: str
    signature: str

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "ruling",
            "unit_id": self.unit_id,
            "unit_public_key": self.unit_public_key,
            "policy_hash": self.policy_hash,
            "policy_version": self.policy_version,
            "facts_hash": self.facts_hash,
            "fired_clause_id": self.fired_clause_id,
            "outcome": self.outcome,
            "evaluator_version": self.evaluator_version,
            "timestamp": self.timestamp,
        })

    def to_dict(self) -> Dict:
        return {"unit_id": self.unit_id,
                "unit_public_key": self.unit_public_key,
                "policy_hash": self.policy_hash,
                "policy_version": self.policy_version,
                "facts_hash": self.facts_hash,
                "fired_clause_id": self.fired_clause_id,
                "outcome": self.outcome,
                "evaluator_version": self.evaluator_version,
                "timestamp": self.timestamp,
                "signature": self.signature}

    @classmethod
    def from_dict(cls, d: Dict) -> "Ruling":
        return cls(
            unit_id=d["unit_id"],
            unit_public_key=d["unit_public_key"],
            policy_hash=d["policy_hash"],
            policy_version=d["policy_version"],
            facts_hash=d["facts_hash"],
            fired_clause_id=d.get("fired_clause_id"),
            outcome=d["outcome"],
            evaluator_version=d["evaluator_version"],
            timestamp=d["timestamp"],
            signature=d["signature"],
        )


def verify_ruling(
    ruling: Ruling,
    expected_public_key: Optional[str] = None,
) -> bool:
    if not HAS_CRYPTO:
        return False
    try:
        key = expected_public_key or ruling.unit_public_key
        return verify_signature(
            key, ruling.canonical_payload(), ruling.signature)
    except Exception:
        return False


@dataclass(frozen=True)
class Amendment:
    unit_id: str
    unit_public_key: str
    old_policy_hash: str
    new_policy_hash: str
    old_version: int
    new_version: int
    timestamp: str
    signature: str

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "amendment",
            "unit_id": self.unit_id,
            "unit_public_key": self.unit_public_key,
            "old_policy_hash": self.old_policy_hash,
            "new_policy_hash": self.new_policy_hash,
            "old_version": self.old_version,
            "new_version": self.new_version,
            "timestamp": self.timestamp,
        })

    def to_dict(self) -> Dict:
        return {"unit_id": self.unit_id,
                "unit_public_key": self.unit_public_key,
                "old_policy_hash": self.old_policy_hash,
                "new_policy_hash": self.new_policy_hash,
                "old_version": self.old_version,
                "new_version": self.new_version,
                "timestamp": self.timestamp,
                "signature": self.signature}

    @classmethod
    def from_dict(cls, d: Dict) -> "Amendment":
        return cls(
            unit_id=d["unit_id"],
            unit_public_key=d["unit_public_key"],
            old_policy_hash=d["old_policy_hash"],
            new_policy_hash=d["new_policy_hash"],
            old_version=d["old_version"],
            new_version=d["new_version"],
            timestamp=d["timestamp"],
            signature=d["signature"],
        )


def verify_amendment(
    amendment: Amendment,
    expected_public_key: Optional[str] = None,
) -> bool:
    if not HAS_CRYPTO:
        return False
    try:
        key = expected_public_key or amendment.unit_public_key
        return verify_signature(
            key, amendment.canonical_payload(),
            amendment.signature)
    except Exception:
        return False


# =====================================================================
# InstitutionalUnit
# =====================================================================

class InstitutionalUnit(SignalWorld):
    def __init__(
        self,
        entity_id: str,
        name: str,
        unit_kp: KeyPair,
        initial_policy: PolicyText,
    ):
        super().__init__(entity_id, name)
        if not verify_policy_signature(
                initial_policy,
                initial_policy.author_public_key):
            raise ValueError(
                "initial_policy signature does not verify")
        self._unit_kp = unit_kp
        self._unit_public_key = unit_kp.public_key_hex()
        self._current_policy = initial_policy
        self._policy_history: List[PolicyText] = [initial_policy]
        self._rulings: List[Ruling] = []
        self._log.append(type(self._log[0])(**{
            "timestamp": _now(), "kind": "policy_set",
            "actor_token": initial_policy.author_token,
            "data": {"policy_hash":
                        initial_policy.policy_hash(),
                     "version": initial_policy.version}}))

    @property
    def current_policy(self) -> PolicyText:
        return self._current_policy

    @property
    def policy_history(self) -> List[PolicyText]:
        return list(self._policy_history)

    def rulings(self) -> List[Ruling]:
        return list(self._rulings)

    def policy_by_hash(
        self, policy_hash: str,
    ) -> Optional[PolicyText]:
        for p in self._policy_history:
            if p.policy_hash() == policy_hash:
                return p
        return None

    def evaluate(self, facts: Dict) -> Ruling:
        policy = self._current_policy
        fired, outcome = evaluate_policy(policy, facts)
        facts_hash = _hash_payload(canonical_bytes(facts))
        ts = _now()
        payload = canonical_bytes({
            "kind": "ruling",
            "unit_id": self._manifest.entity_id,
            "unit_public_key": self._unit_public_key,
            "policy_hash": policy.policy_hash(),
            "policy_version": policy.version,
            "facts_hash": facts_hash,
            "fired_clause_id": fired,
            "outcome": outcome,
            "evaluator_version": EVALUATOR_VERSION,
            "timestamp": ts,
        })
        ruling = Ruling(
            unit_id=self._manifest.entity_id,
            unit_public_key=self._unit_public_key,
            policy_hash=policy.policy_hash(),
            policy_version=policy.version,
            facts_hash=facts_hash,
            fired_clause_id=fired,
            outcome=outcome,
            evaluator_version=EVALUATOR_VERSION,
            timestamp=ts,
            signature=self._unit_kp.sign(payload).hex(),
        )
        self._rulings.append(ruling)
        self._log.append(type(self._log[0])(**{
            "timestamp": ts, "kind": "ruling",
            "actor_token": self._manifest.entity_id,
            "data": ruling.to_dict()}))
        return ruling

    def amend(self, new_policy: PolicyText) -> Amendment:
        """Amend policy. Raises ValueError on invalid amendment."""
        if not verify_policy_signature(
                new_policy, new_policy.author_public_key):
            raise ValueError(
                "new_policy signature does not verify")
        if new_policy.policy_id != \
                self._current_policy.policy_id:
            raise ValueError(
                "policy_id must match current policy")
        if new_policy.author_public_key != \
                self._current_policy.author_public_key:
            raise ValueError(
                "new_policy author must match current author")
        if new_policy.version <= self._current_policy.version:
            raise ValueError(
                f"new_policy version ({new_policy.version}) "
                f"must exceed current "
                f"({self._current_policy.version})")
        old_hash = self._current_policy.policy_hash()
        new_hash = new_policy.policy_hash()
        ts = _now()
        payload = canonical_bytes({
            "kind": "amendment",
            "unit_id": self._manifest.entity_id,
            "unit_public_key": self._unit_public_key,
            "old_policy_hash": old_hash,
            "new_policy_hash": new_hash,
            "old_version": self._current_policy.version,
            "new_version": new_policy.version,
            "timestamp": ts,
        })
        amendment = Amendment(
            unit_id=self._manifest.entity_id,
            unit_public_key=self._unit_public_key,
            old_policy_hash=old_hash,
            new_policy_hash=new_hash,
            old_version=self._current_policy.version,
            new_version=new_policy.version,
            timestamp=ts,
            signature=self._unit_kp.sign(payload).hex(),
        )
        self._current_policy = new_policy
        self._policy_history.append(new_policy)
        self._log.append(type(self._log[0])(**{
            "timestamp": ts, "kind": "amendment",
            "actor_token": self._manifest.entity_id,
            "data": amendment.to_dict()}))
        return amendment

    def act(self, act: Act):
        if act.type == "evaluate":
            facts = act.payload.get("facts")
            if not isinstance(facts, dict):
                return Refusal(
                    reason="evaluate requires payload.facts dict")
            try:
                self.evaluate(facts)
            except Exception as e:
                return Refusal(reason=f"evaluation failed: {e}")
            return Ack(entity_id=self._manifest.entity_id,
                       timestamp=_now())
        if act.type == "amend":
            try:
                new_policy = PolicyText.from_dict(
                    act.payload.get("new_policy", {}))
                self.amend(new_policy)
            except (KeyError, ValueError, TypeError) as e:
                return Refusal(reason=f"amendment failed: {e}")
            return Ack(entity_id=self._manifest.entity_id,
                       timestamp=_now())
        return Refusal(
            reason=(f"InstitutionalUnit refuses act type "
                    f"{act.type!r}; only 'evaluate' and 'amend' "
                    f"are accepted"))


# =====================================================================
# Reproducibility — the distinguishing claim
# =====================================================================

def reproduce_ruling(
    ruling: Ruling, policy: PolicyText, facts: Dict,
) -> Tuple[bool, str]:
    """Given a ruling and the artifacts it references, reproduce it.

    A third party with the policy and facts can re-derive the
    outcome without the unit's cooperation. Never raises.

    Checks:
      1. facts_hash matches the given facts
      2. policy_hash matches the given policy
      3. Re-evaluating yields (fired_clause_id, outcome) matching
    """
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    try:
        facts_hash = _hash_payload(canonical_bytes(facts))
    except Exception as e:
        return (False, f"cannot hash facts: {e}")
    if facts_hash != ruling.facts_hash:
        return (False, "facts_hash does not match")
    if policy.policy_hash() != ruling.policy_hash:
        return (False, "policy_hash does not match")
    fired, outcome = evaluate_policy(policy, facts)
    if fired != ruling.fired_clause_id:
        return (False,
                f"fired_clause_id mismatch: expected {fired!r}, "
                f"ruling says {ruling.fired_clause_id!r}")
    if outcome != ruling.outcome:
        return (False,
                f"outcome mismatch: expected {outcome!r}, "
                f"ruling says {ruling.outcome!r}")
    return (True, "ruling reproduced")
