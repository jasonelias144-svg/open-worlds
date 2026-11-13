"""
multiverse_c39.py — Component 39: Fork and Merge Events.

The lineage layer. A person can fork into successors; successors
can merge. Both are signed events, verified offline.

Design:
  - ForkEvent: signed by the parent's key. Declares children by
    (token, manifest_hash). Does NOT transfer bindings.
  - MergeEvent: co-signed by both parents. Declares the merged
    person by (token, manifest_hash). Both signatures required.
  - verify_fork / verify_merge: verify a single event.
  - build_lineage: walk backward from a leaf manifest, verifying
    each event it uses. Returns ancestor tokens + events used.

Composes with C36 (PersonIdentity, TokenBinding), C38
(PersonManifest).

House rules honored:
  - "A world never raises on what a visitor sends" — verifiers
    return verdicts, never raise.
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: valid fork, tampered child, wrong key,
    valid merge, forged one side, self-merge, lineage walk,
    missing event, broken lineage.
  - "History, not rank" — a fork/merge event is a record of
    lineage, not a score.

Honest limits (documented, tested):
  - A fork declares lineage; it does not transfer bindings. What
    a child holds is in the child's manifest. If a parent wanted
    "the child takes my poetry token," that requires the parent to
    release it (sign a new manifest without it) AND the child to
    bind it (sign a new binding with a new holder key). That
    rebind operation is future work.
  - Children do not consent to a fork. A parent can declare a
    fork into children who are unaware. Detection: the child's
    manifest doesn't reference the parent; only the parent's
    fork does. A verifier who trusts only the child sees no
    lineage. Future: signed child acceptance.
  - Lineage walk requires the full event set. A single manifest
    cannot prove its own ancestry. This is the same limit as
    C32's bundle: the history must be published.
  - No cycles. build_lineage detects cycles via visited set;
    with real timestamps cycles cannot occur, but the check is
    defensive.
  - No revocation of forks/merges. A fork once signed is part
    of the lineage forever. Future: signed retraction.
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple, Union

from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)
from multiverse_c36 import PersonIdentity
from multiverse_c38 import PersonManifest


def _hash_payload(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


# =====================================================================
# ForkEvent
# =====================================================================

@dataclass(frozen=True)
class ForkEvent:
    """A parent declares: 'these children descended from me.'"""
    parent_token: str
    parent_name: str
    parent_public_key: str
    children: Tuple[Tuple[str, str], ...]  # (child_token, child_manifest_hash)
    timestamp: str
    signature: str

    def __post_init__(self):
        for f in ("parent_token", "parent_name",
                  "parent_public_key", "timestamp", "signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if len(self.parent_public_key) != 64:
            raise ValueError(
                "parent_public_key must be 64 hex chars")
        if len(self.children) < 2:
            raise ValueError(
                "a fork requires at least 2 children")
        for pair in self.children:
            if not isinstance(pair, tuple) or len(pair) != 2:
                raise ValueError(
                    "each child must be a (token, hash) tuple")
            tok, h = pair
            if not isinstance(tok, str) or not tok:
                raise ValueError("child token required")
            if not isinstance(h, str) or len(h) != 64:
                raise ValueError("child hash must be 64 hex chars")
        if self.children != tuple(sorted(self.children)):
            raise ValueError("children must be sorted by token")
        tokens = [t for t, _ in self.children]
        if len(tokens) != len(set(tokens)):
            raise ValueError("children must have distinct tokens")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "fork_event",
            "parent_token": self.parent_token,
            "parent_name": self.parent_name,
            "parent_public_key": self.parent_public_key,
            "children": [list(c) for c in sorted(self.children)],
            "timestamp": self.timestamp,
        })

    def to_dict(self) -> Dict:
        return {
            "parent_token": self.parent_token,
            "parent_name": self.parent_name,
            "parent_public_key": self.parent_public_key,
            "children": [list(c) for c in self.children],
            "timestamp": self.timestamp,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "ForkEvent":
        return cls(
            parent_token=d["parent_token"],
            parent_name=d["parent_name"],
            parent_public_key=d["parent_public_key"],
            children=tuple(
                (c[0], c[1]) for c in d.get("children", [])),
            timestamp=d["timestamp"],
            signature=d["signature"],
        )


# =====================================================================
# MergeEvent
# =====================================================================

@dataclass(frozen=True)
class MergeEvent:
    """Two parents declare: 'we merged into X.'  Both sign."""
    parent_a_token: str
    parent_a_name: str
    parent_a_public_key: str
    parent_b_token: str
    parent_b_name: str
    parent_b_public_key: str
    merged_token: str
    merged_name: str
    merged_public_key: str
    merged_manifest_hash: str
    timestamp: str
    signature_a: str
    signature_b: str

    def __post_init__(self):
        for f in ("parent_a_token", "parent_a_name",
                  "parent_a_public_key",
                  "parent_b_token", "parent_b_name",
                  "parent_b_public_key",
                  "merged_token", "merged_name",
                  "merged_public_key", "merged_manifest_hash",
                  "timestamp", "signature_a", "signature_b"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        for f in ("parent_a_public_key", "parent_b_public_key",
                  "merged_public_key", "merged_manifest_hash"):
            if len(getattr(self, f)) != 64:
                raise ValueError(f"{f} must be 64 hex chars")
        if self.parent_a_token == self.parent_b_token:
            raise ValueError(
                "a merge requires two distinct parents")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "merge_event",
            "parent_a_token": self.parent_a_token,
            "parent_a_name": self.parent_a_name,
            "parent_a_public_key": self.parent_a_public_key,
            "parent_b_token": self.parent_b_token,
            "parent_b_name": self.parent_b_name,
            "parent_b_public_key": self.parent_b_public_key,
            "merged_token": self.merged_token,
            "merged_name": self.merged_name,
            "merged_public_key": self.merged_public_key,
            "merged_manifest_hash": self.merged_manifest_hash,
            "timestamp": self.timestamp,
        })

    def to_dict(self) -> Dict:
        return {
            "parent_a_token": self.parent_a_token,
            "parent_a_name": self.parent_a_name,
            "parent_a_public_key": self.parent_a_public_key,
            "parent_b_token": self.parent_b_token,
            "parent_b_name": self.parent_b_name,
            "parent_b_public_key": self.parent_b_public_key,
            "merged_token": self.merged_token,
            "merged_name": self.merged_name,
            "merged_public_key": self.merged_public_key,
            "merged_manifest_hash": self.merged_manifest_hash,
            "timestamp": self.timestamp,
            "signature_a": self.signature_a,
            "signature_b": self.signature_b,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "MergeEvent":
        return cls(
            parent_a_token=d["parent_a_token"],
            parent_a_name=d["parent_a_name"],
            parent_a_public_key=d["parent_a_public_key"],
            parent_b_token=d["parent_b_token"],
            parent_b_name=d["parent_b_name"],
            parent_b_public_key=d["parent_b_public_key"],
            merged_token=d["merged_token"],
            merged_name=d["merged_name"],
            merged_public_key=d["merged_public_key"],
            merged_manifest_hash=d["merged_manifest_hash"],
            timestamp=d["timestamp"],
            signature_a=d["signature_a"],
            signature_b=d["signature_b"],
        )


# =====================================================================
# create_fork
# =====================================================================

def create_fork(
    parent: PersonIdentity,
    parent_kp: KeyPair,
    children: List[PersonManifest],
    timestamp: Optional[str] = None,
) -> ForkEvent:
    if not HAS_CRYPTO:
        raise RuntimeError(
            "create_fork requires `cryptography`")
    if parent_kp.public_key_hex() != parent.person_public_key:
        raise ValueError(
            "keypair does not match parent.person_public_key")
    if len(children) < 2:
        raise ValueError("fork requires at least 2 children")
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    child_pairs = tuple(sorted(
        (c.person_token, _hash_payload(c.canonical_payload()))
        for c in children
    ))
    payload = canonical_bytes({
        "kind": "fork_event",
        "parent_token": parent.person.token,
        "parent_name": parent.person.name,
        "parent_public_key": parent.person_public_key,
        "children": [list(c) for c in child_pairs],
        "timestamp": timestamp,
    })
    return ForkEvent(
        parent_token=parent.person.token,
        parent_name=parent.person.name,
        parent_public_key=parent.person_public_key,
        children=child_pairs,
        timestamp=timestamp,
        signature=parent_kp.sign(payload).hex(),
    )


# =====================================================================
# create_merge
# =====================================================================

def create_merge(
    parent_a: PersonIdentity,
    parent_a_kp: KeyPair,
    parent_b: PersonIdentity,
    parent_b_kp: KeyPair,
    merged: PersonManifest,
    timestamp: Optional[str] = None,
) -> MergeEvent:
    if not HAS_CRYPTO:
        raise RuntimeError(
            "create_merge requires `cryptography`")
    if parent_a_kp.public_key_hex() != parent_a.person_public_key:
        raise ValueError(
            "parent_a keypair does not match its person key")
    if parent_b_kp.public_key_hex() != parent_b.person_public_key:
        raise ValueError(
            "parent_b keypair does not match its person key")
    if parent_a.person.token == parent_b.person.token:
        raise ValueError("merge requires two distinct parents")
    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    merged_hash = _hash_payload(merged.canonical_payload())
    payload = canonical_bytes({
        "kind": "merge_event",
        "parent_a_token": parent_a.person.token,
        "parent_a_name": parent_a.person.name,
        "parent_a_public_key": parent_a.person_public_key,
        "parent_b_token": parent_b.person.token,
        "parent_b_name": parent_b.person.name,
        "parent_b_public_key": parent_b.person_public_key,
        "merged_token": merged.person_token,
        "merged_name": merged.person_name,
        "merged_public_key": merged.person_public_key,
        "merged_manifest_hash": merged_hash,
        "timestamp": timestamp,
    })
    return MergeEvent(
        parent_a_token=parent_a.person.token,
        parent_a_name=parent_a.person.name,
        parent_a_public_key=parent_a.person_public_key,
        parent_b_token=parent_b.person.token,
        parent_b_name=parent_b.person.name,
        parent_b_public_key=parent_b.person_public_key,
        merged_token=merged.person_token,
        merged_name=merged.person_name,
        merged_public_key=merged.person_public_key,
        merged_manifest_hash=merged_hash,
        timestamp=timestamp,
        signature_a=parent_a_kp.sign(payload).hex(),
        signature_b=parent_b_kp.sign(payload).hex(),
    )


# =====================================================================
# Verdicts
# =====================================================================

@dataclass
class ForkVerdict:
    valid: bool
    reason: str
    parent_signature_valid: bool
    child_verdicts: List[Tuple[str, bool, str]] = field(default_factory=list)

    def format(self) -> str:
        lines = [
            "Fork Verification", "=" * 50,
            f"  valid:  {self.valid}",
            f"  reason: {self.reason}",
            f"  parent_signature_valid: {self.parent_signature_valid}",
        ]
        for token, ok, reason in self.child_verdicts:
            marker = "✓" if ok else "✗"
            lines.append(
                f"  {marker} child {token[:16]}...: {reason}")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "valid": self.valid, "reason": self.reason,
            "parent_signature_valid": self.parent_signature_valid,
            "child_verdicts": [
                {"token": t, "ok": ok, "reason": r}
                for t, ok, r in self.child_verdicts],
        }


@dataclass
class MergeVerdict:
    valid: bool
    reason: str
    parent_a_signature_valid: bool
    parent_b_signature_valid: bool
    merged_manifest_matches: bool

    def format(self) -> str:
        return "\n".join([
            "Merge Verification", "=" * 50,
            f"  valid:  {self.valid}",
            f"  reason: {self.reason}",
            f"  parent_a_sig_valid: {self.parent_a_signature_valid}",
            f"  parent_b_sig_valid: {self.parent_b_signature_valid}",
            f"  merged_manifest_matches: {self.merged_manifest_matches}",
        ])

    def to_dict(self) -> Dict:
        return {
            "valid": self.valid, "reason": self.reason,
            "parent_a_signature_valid": self.parent_a_signature_valid,
            "parent_b_signature_valid": self.parent_b_signature_valid,
            "merged_manifest_matches": self.merged_manifest_matches,
        }


# =====================================================================
# verify_fork
# =====================================================================

def verify_fork(
    fork: ForkEvent,
    children: List[PersonManifest],
    trusted_parent_key: Optional[str] = None,
) -> ForkVerdict:
    """Verify a fork event against the children manifests.

    If trusted_parent_key is provided, the fork's declared parent
    key must match it. If not, the signature is checked against
    fork.parent_public_key (self-consistent only — the caller
    decides whether to trust that key).

    Never raises.
    """
    if not HAS_CRYPTO:
        return ForkVerdict(
            valid=False, reason="cryptography not installed",
            parent_signature_valid=False)
    if not isinstance(fork, ForkEvent):
        return ForkVerdict(
            valid=False, reason="not a ForkEvent",
            parent_signature_valid=False)

    # Signature
    try:
        sig_ok = verify_signature(
            fork.parent_public_key,
            fork.canonical_payload(),
            fork.signature)
    except Exception:
        sig_ok = False

    if not sig_ok:
        return ForkVerdict(
            valid=False, reason="parent signature INVALID",
            parent_signature_valid=False)

    if trusted_parent_key is not None and \
            trusted_parent_key != fork.parent_public_key:
        return ForkVerdict(
            valid=False,
            reason=("fork's declared parent key does not match "
                    "the trusted parent key"),
            parent_signature_valid=True)

    # Children
    children_by_token = {c.person_token: c for c in children}
    child_verdicts: List[Tuple[str, bool, str]] = []
    all_ok = True
    for child_token, child_hash in fork.children:
        manifest = children_by_token.get(child_token)
        if manifest is None:
            child_verdicts.append(
                (child_token, False, "child manifest not provided"))
            all_ok = False
            continue
        actual = _hash_payload(manifest.canonical_payload())
        if actual != child_hash:
            child_verdicts.append(
                (child_token, False,
                 "child manifest hash mismatch"))
            all_ok = False
        else:
            child_verdicts.append(
                (child_token, True, "hash matches"))

    return ForkVerdict(
        valid=all_ok,
        reason=("signature valid, all children hashes match"
                if all_ok else "one or more children failed"),
        parent_signature_valid=True,
        child_verdicts=child_verdicts,
    )


# =====================================================================
# verify_merge
# =====================================================================

def verify_merge(
    merge: MergeEvent,
    merged_manifest: PersonManifest,
    trusted_parent_a_key: Optional[str] = None,
    trusted_parent_b_key: Optional[str] = None,
) -> MergeVerdict:
    if not HAS_CRYPTO:
        return MergeVerdict(
            valid=False, reason="cryptography not installed",
            parent_a_signature_valid=False,
            parent_b_signature_valid=False,
            merged_manifest_matches=False)
    if not isinstance(merge, MergeEvent):
        return MergeVerdict(
            valid=False, reason="not a MergeEvent",
            parent_a_signature_valid=False,
            parent_b_signature_valid=False,
            merged_manifest_matches=False)

    payload = merge.canonical_payload()
    try:
        sig_a_ok = verify_signature(
            merge.parent_a_public_key, payload,
            merge.signature_a)
    except Exception:
        sig_a_ok = False
    try:
        sig_b_ok = verify_signature(
            merge.parent_b_public_key, payload,
            merge.signature_b)
    except Exception:
        sig_b_ok = False

    if trusted_parent_a_key is not None and \
            trusted_parent_a_key != merge.parent_a_public_key:
        return MergeVerdict(
            valid=False,
            reason="parent_a declared key != trusted key",
            parent_a_signature_valid=sig_a_ok,
            parent_b_signature_valid=sig_b_ok,
            merged_manifest_matches=False)
    if trusted_parent_b_key is not None and \
            trusted_parent_b_key != merge.parent_b_public_key:
        return MergeVerdict(
            valid=False,
            reason="parent_b declared key != trusted key",
            parent_a_signature_valid=sig_a_ok,
            parent_b_signature_valid=sig_b_ok,
            merged_manifest_matches=False)

    if not (sig_a_ok and sig_b_ok):
        return MergeVerdict(
            valid=False,
            reason=("both signatures required; "
                    + ("a valid" if sig_a_ok else "a INVALID")
                    + ", "
                    + ("b valid" if sig_b_ok else "b INVALID")),
            parent_a_signature_valid=sig_a_ok,
            parent_b_signature_valid=sig_b_ok,
            merged_manifest_matches=False)

    # Merged manifest hash
    actual = _hash_payload(merged_manifest.canonical_payload())
    matches = (merged_manifest.person_token == merge.merged_token
               and actual == merge.merged_manifest_hash)
    return MergeVerdict(
        valid=matches,
        reason=("both signatures valid, merged hash matches"
                if matches else "merged manifest hash mismatch"),
        parent_a_signature_valid=True,
        parent_b_signature_valid=True,
        merged_manifest_matches=matches,
    )


# =====================================================================
# Lineage walk
# =====================================================================

Event = Union[ForkEvent, MergeEvent]


@dataclass
class LineageWalk:
    leaf_token: str
    ancestors: List[str] = field(default_factory=list)
    events: List[Event] = field(default_factory=list)
    valid: bool = False
    reason: str = ""

    def format(self) -> str:
        lines = [
            "=" * 70,
            "Lineage Walk",
            "=" * 70,
            f"  leaf:      {self.leaf_token[:16]}...",
            f"  valid:     {self.valid}",
            f"  reason:    {self.reason}",
            f"  ancestors: {len(self.ancestors)}",
            f"  events:    {len(self.events)}",
            "",
        ]
        for ev in self.events:
            if isinstance(ev, ForkEvent):
                lines.append(
                    f"  fork: {ev.parent_name} → "
                    f"[{', '.join(t[:8] + '...' for t, _ in ev.children)}]")
            else:
                lines.append(
                    f"  merge: {ev.parent_a_name} + "
                    f"{ev.parent_b_name} → {ev.merged_name}")
        lines.append("")
        lines.append("  ancestors (leaf → root):")
        for tok in self.ancestors:
            lines.append(f"    · {tok[:16]}...")
        return "\n".join(lines)

    def to_dict(self) -> Dict:
        return {
            "leaf_token": self.leaf_token,
            "ancestors": list(self.ancestors),
            "event_count": len(self.events),
            "valid": self.valid,
            "reason": self.reason,
        }


def build_lineage(
    leaf: PersonManifest,
    manifests_by_token: Dict[str, PersonManifest],
    events: List[Event],
    max_depth: int = 32,
) -> LineageWalk:
    """Walk backward from `leaf`, following fork and merge events.

    Requires the full event set and the ancestor manifests.
    Verifies each event it uses. Never raises.
    """
    if not HAS_CRYPTO:
        return LineageWalk(
            leaf_token=leaf.person_token,
            reason="cryptography not installed", valid=False)
    if not isinstance(leaf, PersonManifest):
        return LineageWalk(
            leaf_token="", reason="not a PersonManifest",
            valid=False)

    ancestors: List[str] = []
    used_events: List[Event] = []
    visited: set = set()
    leaf_hash = _hash_payload(leaf.canonical_payload())

    def walk(token: str, mhash: str, depth: int) -> None:
        if depth > max_depth:
            raise ValueError(
                f"max_depth {max_depth} exceeded")
        key = (token, mhash)
        if key in visited:
            raise ValueError("cycle detected in lineage")
        visited.add(key)

        # Look for a fork producing this child
        for ev in events:
            if not isinstance(ev, ForkEvent):
                continue
            for ct, ch in ev.children:
                if ct == token and ch == mhash:
                    # Verify the fork against the parent's key
                    try:
                        ok = verify_signature(
                            ev.parent_public_key,
                            ev.canonical_payload(),
                            ev.signature)
                    except Exception:
                        ok = False
                    if not ok:
                        raise ValueError(
                            f"fork signature invalid "
                            f"(parent {ev.parent_token[:16]}...)")
                    pm = manifests_by_token.get(ev.parent_token)
                    if pm is None:
                        raise ValueError(
                            f"parent manifest missing: "
                            f"{ev.parent_token[:16]}...")
                    if ev not in used_events:
                        used_events.append(ev)
                    if ev.parent_token not in ancestors:
                        ancestors.append(ev.parent_token)
                    pm_hash = _hash_payload(pm.canonical_payload())
                    walk(ev.parent_token, pm_hash, depth + 1)
                    return

        # Look for a merge producing this leaf
        for ev in events:
            if not isinstance(ev, MergeEvent):
                continue
            if (ev.merged_token == token
                    and ev.merged_manifest_hash == mhash):
                try:
                    a_ok = verify_signature(
                        ev.parent_a_public_key,
                        ev.canonical_payload(),
                        ev.signature_a)
                    b_ok = verify_signature(
                        ev.parent_b_public_key,
                        ev.canonical_payload(),
                        ev.signature_b)
                except Exception:
                    a_ok = b_ok = False
                if not (a_ok and b_ok):
                    raise ValueError(
                        "merge signature invalid "
                        f"(a={a_ok}, b={b_ok})")
                if ev not in used_events:
                    used_events.append(ev)
                for pt in (ev.parent_a_token,
                           ev.parent_b_token):
                    if pt not in ancestors:
                        ancestors.append(pt)
                for pt in (ev.parent_a_token,
                           ev.parent_b_token):
                    pm = manifests_by_token.get(pt)
                    if pm is None:
                        raise ValueError(
                            f"merge parent manifest missing: "
                            f"{pt[:16]}...")
                    pm_hash = _hash_payload(
                        pm.canonical_payload())
                    walk(pt, pm_hash, depth + 1)
                return

        # No parent found — leaf is a root
        return

    try:
        walk(leaf.person_token, leaf_hash, 0)
    except ValueError as e:
        return LineageWalk(
            leaf_token=leaf.person_token,
            reason=str(e), valid=False)

    return LineageWalk(
        leaf_token=leaf.person_token,
        ancestors=ancestors,
        events=used_events,
        valid=True,
        reason=(f"walked {len(used_events)} event(s), "
                f"{len(ancestors)} ancestor(s)"),
    )


# =====================================================================
# Demo — Aria forks, then merges
# =====================================================================

def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Aria forks into Aria-A (poetry) and Aria-B (chemistry).
    The two children then merge into Aria-2. Verify both events
    and walk the lineage.

    Anchor: Emily Dickinson, 'Forever – is composed of Nows –'.
    """
    import json
    from pathlib import Path
    from multiverse_c1 import create_identity
    from multiverse_c36 import create_person, bind_token
    from multiverse_c38 import sign_person_manifest

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    def _build_person(name, token_names):
        person, kp = create_person(name)
        for tn in token_names:
            tok = create_identity(tn)
            person, _ = bind_token(
                person, kp, tok.token, tn,
                KeyPair.generate())
        return person, kp, sign_person_manifest(person, kp)

    # --- Aria (parent) ---
    aria, aria_kp, aria_m = _build_person(
        "Aria", ["Aria@poetry", "Aria@chemistry", "Aria@registry"])

    # --- Children: Aria-A, Aria-B (own tokens) ---
    aria_a, aria_a_kp, aria_a_m = _build_person(
        "Aria-A", ["Aria-A@poetry"])
    aria_b, aria_b_kp, aria_b_m = _build_person(
        "Aria-B", ["Aria-B@chemistry"])

    # Aria forks into Aria-A and Aria-B
    fork = create_fork(aria, aria_kp, [aria_a_m, aria_b_m])

    # --- Merged: Aria-2 ---
    aria_2, aria_2_kp, aria_2_m = _build_person(
        "Aria-2",
        ["Aria-A@poetry", "Aria-B@chemistry"])
    merge = create_merge(
        aria_a, aria_a_kp, aria_b, aria_b_kp, aria_2_m)

    # --- Verify ---
    fork_verdict = verify_fork(
        fork, [aria_a_m, aria_b_m],
        trusted_parent_key=aria.person_public_key)
    merge_verdict = verify_merge(
        merge, aria_2_m,
        trusted_parent_a_key=aria_a.person_public_key,
        trusted_parent_b_key=aria_b.person_public_key)

    manifests_by_token = {
        aria.person.token: aria_m,
        aria_a.person.token: aria_a_m,
        aria_b.person.token: aria_b_m,
        aria_2.person.token: aria_2_m,
    }
    lineage = build_lineage(
        aria_2_m, manifests_by_token, [fork, merge])

    # --- Attack: attacker forks with a fake parent key ---
    attacker, attacker_kp = create_person("Attacker")
    fake_child, _, fake_child_m = _build_person(
        "Fake", ["Fake@x"])
    fake_child_2, _, fake_child_2_m = _build_person(
        "Fake2", ["Fake2@x"])
    # Attacker signs a fork claiming Aria's token as parent, but
    # with attacker's own key. Tamper: build the fork manually.
    fake_payload = canonical_bytes({
        "kind": "fork_event",
        "parent_token": aria.person.token,
        "parent_name": "Aria (impersonated)",
        "parent_public_key": attacker_kp.public_key_hex(),
        "children": sorted([
            (fake_child.person.token,
             _hash_payload(fake_child_m.canonical_payload())),
            (fake_child_2.person.token,
             _hash_payload(fake_child_2_m.canonical_payload())),
        ]),
        "timestamp": "2024-01-01T00:00:00+00:00",
    })
    fake_fork = ForkEvent(
        parent_token=aria.person.token,
        parent_name="Aria (impersonated)",
        parent_public_key=attacker_kp.public_key_hex(),
        children=tuple(sorted([
            (fake_child.person.token,
             _hash_payload(fake_child_m.canonical_payload())),
            (fake_child_2.person.token,
             _hash_payload(fake_child_2_m.canonical_payload())),
        ])),
        timestamp="2024-01-01T00:00:00+00:00",
        signature=attacker_kp.sign(fake_payload).hex(),
    )
    fake_verdict = verify_fork(
        fake_fork, [fake_child_m, fake_child_2_m],
        trusted_parent_key=aria.person_public_key)

    print("=" * 70)
    print("Fork and Merge — demo")
    print("=" * 70)
    print()
    print("  Aria (3 bindings) forks into Aria-A and Aria-B")
    for line in fork_verdict.format().split("\n"):
        print(f"    {line}")
    print()
    print("  Aria-A and Aria-B merge into Aria-2")
    for line in merge_verdict.format().split("\n"):
        print(f"    {line}")
    print()
    print(lineage.format())
    print()
    print("  Attack: attacker forks, claiming Aria's token but")
    print("  signing with their own key")
    for line in fake_verdict.format().split("\n"):
        print(f"    {line}")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'Forever – is composed of Nows –'")
    print("    'Tis not a different time –'")

    audit = {
        "fork_valid": fork_verdict.valid,
        "merge_valid": merge_verdict.valid,
        "lineage_valid": lineage.valid,
        "lineage_ancestors": len(lineage.ancestors),
        "lineage_events": len(lineage.events),
        "fake_fork_valid_against_real_key":
            fake_verdict.valid,
        "fake_fork_reason": fake_verdict.reason,
    }
    if artifact_dir:
        path = Path(artifact_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / "lineage_demo.json").write_text(
            json.dumps(audit, indent=2))
        print(f"\n  → {path}/lineage_demo.json")
    return audit
