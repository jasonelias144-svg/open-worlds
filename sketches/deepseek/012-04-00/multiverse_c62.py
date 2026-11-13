"""
multiverse_c62.py — Component 62: The Reference LCS Implementation.

A working instance of C61's ledger-as-commitment-store spec.

What it provides:
  - CommitmentRecord: one signed append to the log.
  - CommitmentLog: append + three queries (get_commit,
    get_commits_by_kind, get_commit_chain).
  - Merkle tree helpers: leaf_hash, internal_hash, merkle_root,
    inclusion_proof, verify_inclusion.
  - SignedTreeHead: a federation-signed checkpoint over a
    specific tree size.
  - CheckpointPublisher: signs the current root.
  - verify_commitment: single-record offline check.
  - verify_commitment_chain: whole-log chain check
    (previous_commit_hash linkage).
  - verify_tree_head: check a checkpoint against a federation
    public key.
  - verify_inclusion: check that a commit is in a checkpoint.

What it deliberately does NOT provide:
  - Consensus (C61 §11, §13).
  - Persistence to disk (serialization is trivial; kept out).
  - Network transport (in-process).
  - Consistency proofs (C61 §13 — real CT property, not in
    scope for the reference; inclusion proofs are).
  - Artifact verification (that's C13–C60's job).
  - Data availability (the caller must retain artifacts).

Composition:
  - Uses C13's Ed25519 for commitment signatures and
    tree-head signatures.
  - Commitments reference artifact hashes computed by the
    artifact's own canonical_payload() / *_hash() methods.
  - A tree head is a signed blob that a caller can pin or
    publish; commits are included via Merkle proofs against
    the head's root.

House rules honored:
  - "Every behaviour has a test that fails if the behaviour
    breaks" — one per: append/order, query by hash, query by
    kind, chain integrity, empty root, one-leaf root, odd-leaf
    root, inclusion proof verify, tampered proof rejected,
    tree head sign/verify, full flow.
  - "A world never raises on what a visitor sends" — verifiers
    return verdicts; append raises only on caller error.
  - "History, not rank" — the log is append-only; commits are
    factual.

Honest limits (documented, tested):
  - No consistency proofs. A log operator who rewinds and
    re-signs a *different* tree with the same size would need
    an out-of-band check to detect. Inclusion proofs alone
    prove a commit is in *a* tree, not that the tree is
    consistent with earlier ones.
  - No fork detection. Two operators could sign two different
    trees of the same size. The federation's checkpoint
    policy (C61 §12.C) is what prevents this; the reference
    implementation just produces the signed head.
  - No data availability. The commitment record is not the
    artifact; a caller that lost the artifact can still prove
    it *was* committed, but cannot re-verify its content.
  - commit_index is a client-visible number. In a real
    distributed log, indices would be agreed by the log's
    consensus. Here they are `len(entries)` because the log
    is single-writer.
  - No time verification. `timestamp_claimed` is a claim
    covered by the committer's signature but not checked
    against any clock.
"""

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from multiverse_c13 import (
    HAS_CRYPTO, KeyPair, canonical_bytes, verify_signature,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_payload(p: bytes) -> str:
    return hashlib.sha256(p).hexdigest()


# =====================================================================
# CommitmentRecord
# =====================================================================

@dataclass(frozen=True)
class CommitmentRecord:
    """One append to the log. Signed by the committer.

    The signature covers (artifact_hash, artifact_kind,
    committer_world_id, committer_public_key,
    timestamp_claimed, previous_commit_hash). Not commit_index
    — the log assigns that.
    """
    commit_index: int
    artifact_hash: str
    artifact_kind: str
    committer_world_id: str
    committer_public_key: str
    timestamp_claimed: str
    signature: str
    previous_commit_hash: Optional[str]

    def __post_init__(self):
        if self.commit_index < 0:
            raise ValueError("commit_index must be >= 0")
        for f in ("artifact_hash", "artifact_kind",
                  "committer_world_id", "committer_public_key",
                  "timestamp_claimed", "signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if len(self.artifact_hash) != 64:
            raise ValueError(
                "artifact_hash must be 64 hex chars")
        if len(self.committer_public_key) != 64:
            raise ValueError(
                "committer_public_key must be 64 hex chars")
        if self.previous_commit_hash is not None:
            if len(self.previous_commit_hash) != 64:
                raise ValueError(
                    "previous_commit_hash must be 64 hex chars "
                    "or None")

    def commitment_payload(self) -> bytes:
        """The bytes the committer signs. Not commit_index."""
        return canonical_bytes({
            "kind": "commitment_signature",
            "artifact_hash": self.artifact_hash,
            "artifact_kind": self.artifact_kind,
            "committer_world_id": self.committer_world_id,
            "committer_public_key": self.committer_public_key,
            "timestamp_claimed": self.timestamp_claimed,
            "previous_commit_hash": self.previous_commit_hash,
        })

    def ledger_commit_hash(self) -> str:
        """The hash of the whole record (includes commit_index)."""
        return _hash_payload(canonical_bytes({
            "kind": "commitment",
            "commit_index": self.commit_index,
            "artifact_hash": self.artifact_hash,
            "artifact_kind": self.artifact_kind,
            "committer_world_id": self.committer_world_id,
            "committer_public_key": self.committer_public_key,
            "timestamp_claimed": self.timestamp_claimed,
            "signature": self.signature,
            "previous_commit_hash": self.previous_commit_hash,
        }))

    def to_dict(self) -> Dict:
        return {
            "commit_index": self.commit_index,
            "artifact_hash": self.artifact_hash,
            "artifact_kind": self.artifact_kind,
            "committer_world_id": self.committer_world_id,
            "committer_public_key": self.committer_public_key,
            "timestamp_claimed": self.timestamp_claimed,
            "signature": self.signature,
            "previous_commit_hash": self.previous_commit_hash,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "CommitmentRecord":
        return cls(
            commit_index=d["commit_index"],
            artifact_hash=d["artifact_hash"],
            artifact_kind=d["artifact_kind"],
            committer_world_id=d["committer_world_id"],
            committer_public_key=d["committer_public_key"],
            timestamp_claimed=d["timestamp_claimed"],
            signature=d["signature"],
            previous_commit_hash=d.get("previous_commit_hash"),
        )


def verify_commitment(record: CommitmentRecord) -> bool:
    """Verify one commitment's signature. Never raises."""
    if not HAS_CRYPTO:
        return False
    try:
        if not isinstance(record, CommitmentRecord):
            return False
        return verify_signature(
            record.committer_public_key,
            record.commitment_payload(),
            record.signature)
    except Exception:
        return False


# =====================================================================
# Merkle helpers
# =====================================================================

def _leaf_hash(commit_hash: str) -> str:
    """Leaf domain separator: 0x00 prefix prevents second-preimage
    attacks where a leaf is confused with an internal node."""
    return _hash_payload(
        b"\x00" + bytes.fromhex(commit_hash))


def _internal_hash(left: str, right: str) -> str:
    """Internal domain separator: 0x01 prefix."""
    return _hash_payload(
        b"\x01" + bytes.fromhex(left) + bytes.fromhex(right))


def _level_sizes(n: int) -> List[int]:
    """The size of each Merkle level. Sizes shrink by half, rounded
    up, until 1. E.g., n=3 → [3, 2, 1]; n=5 → [5, 3, 2, 1]."""
    if n <= 0:
        return []
    sizes = [n]
    while sizes[-1] > 1:
        sizes.append((sizes[-1] + 1) // 2)
    return sizes


def merkle_root(leaves: List[str]) -> str:
    """Compute the Merkle root of a list of commit hashes.

    Odd-sized levels promote their last node up without hashing
    it (CT-style, not Bitcoin-style). Empty input → empty string.
    """
    if not leaves:
        return ""
    level = [_leaf_hash(l) for l in leaves]
    while len(level) > 1:
        next_level: List[str] = []
        for i in range(0, len(level), 2):
            if i + 1 < len(level):
                next_level.append(
                    _internal_hash(level[i], level[i + 1]))
            else:
                next_level.append(level[i])  # promote
        level = next_level
    return level[0]


def inclusion_proof(leaves: List[str], index: int) -> List[str]:
    """The sibling hashes needed to prove leaves[index] is in the
    tree with the given leaves.

    The proof has no fixed length — promoted nodes contribute
    no sibling at their level. The verifier derives the same
    shape from `len(leaves)`.
    """
    n = len(leaves)
    if n == 0:
        raise ValueError("empty tree has no inclusion proofs")
    if index < 0 or index >= n:
        raise IndexError(
            f"index {index} out of range for tree of size {n}")
    proof: List[str] = []
    level = [_leaf_hash(l) for l in leaves]
    i = index
    while len(level) > 1:
        # Sibling exists unless this is the last node on an
        # odd-sized level (promoted).
        is_last = (i == len(level) - 1)
        is_odd_level = (len(level) % 2 == 1)
        if not (is_last and is_odd_level):
            if i % 2 == 0:
                proof.append(level[i + 1])
            else:
                proof.append(level[i - 1])
        # Move up
        next_level: List[str] = []
        for j in range(0, len(level), 2):
            if j + 1 < len(level):
                next_level.append(
                    _internal_hash(level[j], level[j + 1]))
            else:
                next_level.append(level[j])
        level = next_level
        i //= 2
    return proof


def verify_inclusion(
    leaf: str, proof: List[str], index: int, n: int,
    expected_root: str,
) -> bool:
    """Verify that `leaf` at position `index` (of a tree with
    `n` leaves) hashes up to `expected_root` using `proof`.

    The verifier computes the tree shape from `n`, so it knows
    whether each level has a sibling for this node or is a
    promoted last node. Never raises.
    """
    try:
        if not HAS_CRYPTO:
            return False
        if n <= 0 or index < 0 or index >= n:
            return False
        if not isinstance(leaf, str) or len(leaf) != 64:
            return False
        sizes = _level_sizes(n)
        h = _leaf_hash(leaf)
        i = index
        proof_iter = iter(proof)
        for level_idx in range(len(sizes) - 1):
            size_at_level = sizes[level_idx]
            is_last = (i == size_at_level - 1)
            is_odd_level = (size_at_level % 2 == 1)
            is_promoted = is_last and is_odd_level
            if not is_promoted:
                sibling = next(proof_iter, None)
                if sibling is None:
                    return False
                if i % 2 == 0:
                    h = _internal_hash(h, sibling)
                else:
                    h = _internal_hash(sibling, h)
            i //= 2
        # No extra hashes allowed in the proof
        if next(proof_iter, None) is not None:
            return False
        return h == expected_root
    except Exception:
        return False


# =====================================================================
# CommitmentLog
# =====================================================================

class CommitmentLog:
    """The append-only log.

    The reference implementation is single-writer. A production
    ledger with multiple writers needs consensus (C61 §12); the
    log's interface here is what the consensus would produce.
    """

    def __init__(self):
        self._entries: List[CommitmentRecord] = []

    def size(self) -> int:
        return len(self._entries)

    def entries(self) -> List[CommitmentRecord]:
        return list(self._entries)

    def append(
        self,
        artifact_hash: str,
        artifact_kind: str,
        committer_world_id: str,
        committer_kp: KeyPair,
        timestamp_claimed: Optional[str] = None,
    ) -> CommitmentRecord:
        """Append a commitment. Signs it with the committer's key.

        The caller supplies `artifact_hash` — computed from the
        actual artifact using the artifact's own canonical hash
        method. The log does not (and cannot) compute it, since
        it does not know the artifact's kind's hash semantics.
        """
        if not HAS_CRYPTO:
            raise RuntimeError(
                "CommitmentLog.append requires cryptography")
        if not isinstance(artifact_hash, str) \
                or len(artifact_hash) != 64:
            raise ValueError(
                "artifact_hash must be 64 hex chars")
        if not isinstance(artifact_kind, str) or not artifact_kind:
            raise ValueError("artifact_kind required")
        if not isinstance(committer_world_id, str) \
                or not committer_world_id:
            raise ValueError("committer_world_id required")
        if timestamp_claimed is None:
            timestamp_claimed = _now()
        commit_index = len(self._entries)
        previous_hash = (
            self._entries[-1].ledger_commit_hash()
            if self._entries else None)
        public_key = committer_kp.public_key_hex()
        payload = canonical_bytes({
            "kind": "commitment_signature",
            "artifact_hash": artifact_hash,
            "artifact_kind": artifact_kind,
            "committer_world_id": committer_world_id,
            "committer_public_key": public_key,
            "timestamp_claimed": timestamp_claimed,
            "previous_commit_hash": previous_hash,
        })
        record = CommitmentRecord(
            commit_index=commit_index,
            artifact_hash=artifact_hash,
            artifact_kind=artifact_kind,
            committer_world_id=committer_world_id,
            committer_public_key=public_key,
            timestamp_claimed=timestamp_claimed,
            signature=committer_kp.sign(payload).hex(),
            previous_commit_hash=previous_hash,
        )
        self._entries.append(record)
        return record

    # -- Queries -------------------------------------------------

    def get_commit(
        self, artifact_hash: str,
    ) -> List[CommitmentRecord]:
        """All commitments of a given artifact hash, by index."""
        return [e for e in self._entries
                if e.artifact_hash == artifact_hash]

    def get_commits_by_kind(
        self, artifact_kind: str, since_index: int = 0,
    ) -> List[CommitmentRecord]:
        return [e for e in self._entries
                if e.artifact_kind == artifact_kind
                and e.commit_index >= since_index]

    def get_commit_chain(
        self, start_index: int, end_index: int,
    ) -> List[CommitmentRecord]:
        """Entries in [start, end). Indices are clamped to bounds."""
        start = max(0, start_index)
        end = min(len(self._entries), end_index)
        if start >= end:
            return []
        return list(self._entries[start:end])

    def first_commit_index(
        self, artifact_hash: str,
    ) -> Optional[int]:
        """The earliest commit index for an artifact, or None."""
        for e in self._entries:
            if e.artifact_hash == artifact_hash:
                return e.commit_index
        return None

    # -- Merkle / checkpoint -------------------------------------

    def all_leaf_hashes(self) -> List[str]:
        return [e.ledger_commit_hash() for e in self._entries]

    def merkle_root(self) -> str:
        return merkle_root(self.all_leaf_hashes())

    def inclusion_proof_for(
        self, commit_index: int,
    ) -> List[str]:
        return inclusion_proof(
            self.all_leaf_hashes(), commit_index)


# =====================================================================
# Chain verification
# =====================================================================

@dataclass
class ChainVerdict:
    valid: bool
    reason: str
    bad_index: Optional[int] = None

    def to_dict(self) -> Dict:
        return {
            "valid": self.valid,
            "reason": self.reason,
            "bad_index": self.bad_index,
        }


def verify_commitment_chain(
    entries: List[CommitmentRecord],
) -> ChainVerdict:
    """Verify a whole log's chain of commitments. Never raises.

    Checks, in order:
      1. Each record's commit_index equals its position.
      2. Record 0's previous_commit_hash is None.
      3. Record i>0's previous_commit_hash equals
         record i-1's ledger_commit_hash.
      4. Each record's signature verifies.
    """
    if not HAS_CRYPTO:
        return ChainVerdict(
            valid=False, reason="cryptography not installed")
    if not isinstance(entries, list):
        return ChainVerdict(
            valid=False, reason="entries must be a list")
    for i, e in enumerate(entries):
        if not isinstance(e, CommitmentRecord):
            return ChainVerdict(
                valid=False,
                reason=f"entry {i} is not a CommitmentRecord",
                bad_index=i)
        if e.commit_index != i:
            return ChainVerdict(
                valid=False,
                reason=(f"entry {i} has commit_index "
                         f"{e.commit_index}"),
                bad_index=i)
        if i == 0:
            if e.previous_commit_hash is not None:
                return ChainVerdict(
                    valid=False,
                    reason="first entry has "
                            "previous_commit_hash",
                    bad_index=0)
        else:
            prev = entries[i - 1]
            if e.previous_commit_hash != \
                    prev.ledger_commit_hash():
                return ChainVerdict(
                    valid=False,
                    reason=(f"entry {i} previous_commit_hash "
                             f"does not match entry {i-1}"),
                    bad_index=i)
        if not verify_commitment(e):
            return ChainVerdict(
                valid=False,
                reason=f"entry {i} signature INVALID",
                bad_index=i)
    return ChainVerdict(
        valid=True, reason="chain verifies")


# =====================================================================
# SignedTreeHead
# =====================================================================

@dataclass(frozen=True)
class SignedTreeHead:
    """A federation-signed checkpoint over a specific tree size."""
    tree_size: int
    root_hash: str
    timestamp: str
    federation_public_key: str
    signature: str

    def __post_init__(self):
        if self.tree_size < 0:
            raise ValueError("tree_size must be >= 0")
        if self.tree_size == 0 and self.root_hash != "":
            raise ValueError(
                "empty tree must have empty root")
        if self.tree_size > 0 and len(self.root_hash) != 64:
            raise ValueError(
                "root_hash must be 64 hex chars")
        for f in ("timestamp", "federation_public_key",
                  "signature"):
            v = getattr(self, f)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{f} required")
        if len(self.federation_public_key) != 64:
            raise ValueError(
                "federation_public_key must be 64 hex chars")

    def canonical_payload(self) -> bytes:
        return canonical_bytes({
            "kind": "signed_tree_head",
            "tree_size": self.tree_size,
            "root_hash": self.root_hash,
            "timestamp": self.timestamp,
            "federation_public_key": self.federation_public_key,
        })

    def to_dict(self) -> Dict:
        return {
            "tree_size": self.tree_size,
            "root_hash": self.root_hash,
            "timestamp": self.timestamp,
            "federation_public_key": self.federation_public_key,
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, d: Dict) -> "SignedTreeHead":
        return cls(
            tree_size=d["tree_size"],
            root_hash=d["root_hash"],
            timestamp=d["timestamp"],
            federation_public_key=d["federation_public_key"],
            signature=d["signature"],
        )


def verify_tree_head(
    head: SignedTreeHead,
    expected_public_key: Optional[str] = None,
) -> bool:
    """True iff the tree head's signature verifies. Never raises."""
    if not HAS_CRYPTO:
        return False
    try:
        if not isinstance(head, SignedTreeHead):
            return False
        key = (expected_public_key
                or head.federation_public_key)
        return verify_signature(
            key, head.canonical_payload(), head.signature)
    except Exception:
        return False


# =====================================================================
# CheckpointPublisher
# =====================================================================

class CheckpointPublisher:
    """Sign the current state of a log as a tree head.

    Each call produces a new SignedTreeHead for the log's current
    size. Old heads stay valid; new heads cover a superset of
    commits. (Consistency proofs between heads are future work —
    see the module docstring.)
    """

    def __init__(
        self, log: CommitmentLog, federation_kp: KeyPair,
    ):
        if not HAS_CRYPTO:
            raise RuntimeError(
                "CheckpointPublisher requires cryptography")
        self._log = log
        self._kp = federation_kp

    def publish(self) -> SignedTreeHead:
        timestamp = _now()
        size = self._log.size()
        root = self._log.merkle_root()
        public_key = self._kp.public_key_hex()
        payload = canonical_bytes({
            "kind": "signed_tree_head",
            "tree_size": size,
            "root_hash": root,
            "timestamp": timestamp,
            "federation_public_key": public_key,
        })
        return SignedTreeHead(
            tree_size=size,
            root_hash=root,
            timestamp=timestamp,
            federation_public_key=public_key,
            signature=self._kp.sign(payload).hex(),
        )


# =====================================================================
# Artifact hash helpers (convenience, not core)
# =====================================================================

def artifact_hash(artifact: Any) -> str:
    """Compute a canonical hash for an arc artifact.

    Dispatches on the artifact's own shape: if it has
    `.canonical_payload()`, hash that; elif it has
    `.ledger_commit_hash()`, use that; elif it has
    `.content_hash`, use that; elif it has `.offer_hash()`, use
    that; else raise. This lets a caller compute a stable hash
    for any of the arc's artifacts with one function, while
    keeping the *ledger* ignorant of artifact kinds.
    """
    if hasattr(artifact, "offer_hash") \
            and callable(artifact.offer_hash):
        return artifact.offer_hash()
    if hasattr(artifact, "ledger_commit_hash") \
            and callable(artifact.ledger_commit_hash):
        return artifact.ledger_commit_hash()
    if hasattr(artifact, "announcement_hash") \
            and callable(artifact.announcement_hash):
        return artifact.announcement_hash()
    if hasattr(artifact, "binding_hash") \
            and callable(artifact.binding_hash):
        return artifact.binding_hash()
    if hasattr(artifact, "link_hash") \
            and callable(artifact.link_hash):
        return artifact.link_hash()
    if hasattr(artifact, "content_hash"):
        v = artifact.content_hash
        if isinstance(v, str) and len(v) == 64:
            return v
    if hasattr(artifact, "canonical_payload") \
            and callable(artifact.canonical_payload):
        return _hash_payload(artifact.canonical_payload())
    raise TypeError(
        f"cannot compute canonical hash for "
        f"{type(artifact).__name__}")


def demo(artifact_dir: Optional[str] = None) -> Dict:
    """Appendix A of C61, as a working example.

    Alice's world and Bob's world establish a contract (commit
    at some index). Carol's world cites the contract (commit
    at a later index). Alice and Bob revoke the contract (commit
    at a still later index). The ledger gives the *order of
    commits*, which is what a reader needs.

    Two versions of the same three events:

      Case A — commit order matches claimed order.
      Case B — commit order differs from claimed order.

    Case B is the point of the ledger: the two orders are
    different facts, and the ledger makes the *commit order*
    checkable without claiming the *claimed order* is wrong.

    Anchor: Dickinson, 'Forever – is composed of Nows –'
    (the ledger orders the Nows).
    """
    import json
    from pathlib import Path
    from multiverse_c1 import create_identity
    from multiverse_c13 import KeyPair

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir)
    path.mkdir(parents=True, exist_ok=True)

    # Fake but representative hashes for the three artifacts
    # (in a real run, these would come from C57/C59/C60 artifacts)
    establishment_hash = _hash_payload(b"establishment")
    citation_hash = _hash_payload(b"citation")
    revocation_hash = _hash_payload(b"revocation")

    # -- Case A: commit order matches claimed order ------------
    log_a = CommitmentLog()
    alice_kp = KeyPair.generate()
    bob_kp = KeyPair.generate()
    carol_kp = KeyPair.generate()

    # Commit 0: establishment
    log_a.append(
        establishment_hash,
        "contract_announcement",
        "world:poetry",
        alice_kp,
        timestamp_claimed="2024-03-01T12:00:00+00:00",
    )
    # Commit 1: citation
    log_a.append(
        citation_hash,
        "citation_act",
        "world:other",
        carol_kp,
        timestamp_claimed="2024-03-05T17:00:00+00:00",
    )
    # Commit 2: revocation
    log_a.append(
        revocation_hash,
        "contract_revocation",
        "world:poetry",
        alice_kp,
        timestamp_claimed="2024-03-05T18:00:00+00:00",
    )

    # Publish a checkpoint
    federation_kp = KeyPair.generate()
    publisher_a = CheckpointPublisher(log_a, federation_kp)
    head_a = publisher_a.publish()

    # Generate and verify inclusion proofs for all three
    proofs_a = []
    for i in range(3):
        proof = log_a.inclusion_proof_for(i)
        leaf = log_a.all_leaf_hashes()[i]
        ok = verify_inclusion(
            leaf, proof, i, log_a.size(), head_a.root_hash)
        proofs_a.append({
            "index": i,
            "kind": log_a.entries()[i].artifact_kind,
            "claimed": log_a.entries()[i].timestamp_claimed,
            "proof_length": len(proof),
            "verified": ok,
        })

    # -- Case B: same events, different commit order ----------
    log_b = CommitmentLog()
    # Commit 0: establishment
    log_b.append(
        establishment_hash,
        "contract_announcement",
        "world:poetry",
        alice_kp,
        timestamp_claimed="2024-03-01T12:00:00+00:00",
    )
    # Commit 1: revocation (claimed LATER but committed FIRST)
    log_b.append(
        revocation_hash,
        "contract_revocation",
        "world:poetry",
        alice_kp,
        timestamp_claimed="2024-03-05T18:00:00+00:00",
    )
    # Commit 2: citation (claimed EARLIER but committed LATER)
    log_b.append(
        citation_hash,
        "citation_act",
        "world:other",
        carol_kp,
        timestamp_claimed="2024-03-05T17:00:00+00:00",
    )
    publisher_b = CheckpointPublisher(log_b, federation_kp)
    head_b = publisher_b.publish()
    proofs_b = []
    for i in range(3):
        proof = log_b.inclusion_proof_for(i)
        leaf = log_b.all_leaf_hashes()[i]
        ok = verify_inclusion(
            leaf, proof, i, log_b.size(), head_b.root_hash)
        proofs_b.append({
            "index": i,
            "kind": log_b.entries()[i].artifact_kind,
            "claimed": log_b.entries()[i].timestamp_claimed,
            "proof_length": len(proof),
            "verified": ok,
        })

    # Verify both chains and both heads
    chain_a = verify_commitment_chain(log_a.entries())
    chain_b = verify_commitment_chain(log_b.entries())
    head_a_ok = verify_tree_head(
        head_a, federation_kp.public_key_hex())
    head_b_ok = verify_tree_head(
        head_b, federation_kp.public_key_hex())

    # First-seen queries
    first_seen = {
        "establishment": log_a.first_commit_index(
            establishment_hash),
        "citation": log_a.first_commit_index(citation_hash),
        "revocation": log_a.first_commit_index(revocation_hash),
    }
    first_seen_b = {
        "establishment": log_b.first_commit_index(
            establishment_hash),
        "citation": log_b.first_commit_index(citation_hash),
        "revocation": log_b.first_commit_index(revocation_hash),
    }

    # -- Print -----------------------------------------------
    print("=" * 70)
    print("LCS Reference Implementation — order is what the ledger adds")
    print("=" * 70)
    print()
    print(f"  Case A: commit order matches claimed order")
    print(f"    chain valid:  {chain_a.valid}")
    print(f"    head signed:  {head_a_ok}")
    print(f"    entries:")
    for p in proofs_a:
        print(f"      [{p['index']}] {p['kind']:25s} "
              f"claimed={p['claimed'][:19]} "
              f"proof_ok={p['verified']}")
    print(f"    first-seen: {first_seen}")
    print()
    print(f"  Case B: commit order differs from claimed order")
    print(f"    chain valid:  {chain_b.valid}")
    print(f"    head signed:  {head_b_ok}")
    print(f"    entries:")
    for p in proofs_b:
        print(f"      [{p['index']}] {p['kind']:25s} "
              f"claimed={p['claimed'][:19]} "
              f"proof_ok={p['verified']}")
    print(f"    first-seen: {first_seen_b}")
    print()
    print("  What this demonstrates:")
    print("    - The ledger commits to *artifact hashes*, not artifacts.")
    print("    - The ledger records the *order of commits*, not the")
    print("      order of events. In Case B, the citation was claimed")
    print("      before the revocation but committed after it.")
    print("    - Inclusion proofs let a client prove a specific")
    print("      commit is in a specific tree head without trusting")
    print("      the log operator.")
    print("    - The tree head is federation-signed; a client that")
    print("      pins the federation key knows the head is authentic.")
    print("    - The artifact itself (its meaning, its signature,")
    print("      its truth) is NOT in the ledger's scope. That's")
    print("      C13–C60's job.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'Forever – is composed of Nows –'")
    print("    'Tis not a different time –'")

    audit = {
        "case_a": {
            "chain_valid": chain_a.valid,
            "head_signed": head_a_ok,
            "tree_size": log_a.size(),
            "root_hash": head_a.root_hash,
            "proofs": proofs_a,
            "first_seen": first_seen,
        },
        "case_b": {
            "chain_valid": chain_b.valid,
            "head_signed": head_b_ok,
            "tree_size": log_b.size(),
            "root_hash": head_b.root_hash,
            "proofs": proofs_b,
            "first_seen": first_seen_b,
        },
    }
    (path / "lcs_demo.json").write_text(
        json.dumps(audit, indent=2))
    print(f"\n  → {path}/lcs_demo.json")
    return audit
