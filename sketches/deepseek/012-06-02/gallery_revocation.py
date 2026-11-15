"""
gallery_revocation.py — key revocation and keeper rotation.

Extends gallery_governance with two record types and a verifier
that walks the keeper timeline.

Design decisions:
  - World id is frozen at construction (= initial keeper's did).
    It identifies the gallery, not the keeper.
  - Record-signing rotates. The current keeper (reconstructed from
    the log) signs each record. Rotation is a mid-log event;
    before it, old keeper signs; after it, new keeper signs.
  - World-keys are signed by their issuer (the keeper who issued
    them). Old keys remain valid after rotation — the subject
    shouldn't have to re-enroll. Revocation is by hash; once a key
    is revoked, requests applied at or after effective_at are
    refused.
  - Verifier tracks current_keeper and revoked_keys as it walks.
    Accepted requests are checked against state-at-apply-time.

Honest limits:
  - Keys issued after rotation are not exercised in this sketch
    (runtime _verify_request still expects issuer == world_id).
    Full post-rotation issuance is a v0.2 concern.
  - No forward secrecy. Records signed by K1 before rotation
    remain signed by K1; compromise of K1 before rotation is not
    retroactively detectable.
  - Verifier does not re-derive *refusal* reasons — it trusts the
    gallery's claim for refused requests. Accepted requests are
    fully re-derived.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    from cryptography.hazmat.primitives import serialization
    from cryptography.exceptions import InvalidSignature
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from gallery_governance import (
    GalleryPolicy, GalleryWorldKey, verify_world_key,
    world_key_has_tier,
    GovernedGalleryWorld,
    GallerySeedRecord, PolicyChangeRecord, MemberAddedRecord,
    MemberRetiredRecord, GalleryCycleRecord,
    RequestRefusedRecord,
    verify_governed_members,
    _did_from_kp, _canonical, _hash, _now, _pubkey_from_did,
    _verify_sig,
)


# =====================================================================
# New record types
# =====================================================================

@dataclass(frozen=True)
class KeeperRotationRecord:
    world_id: str
    old_keeper_id: str
    new_keeper_id: str
    prev: Optional[str]
    ts: str
    sig_old: str
    sig_new: str

    def rotation_body(self):
        return {
            "type": "keeper_rotation",
            "world_id": self.world_id,
            "old_keeper_id": self.old_keeper_id,
            "new_keeper_id": self.new_keeper_id,
            "prev": self.prev,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.rotation_body())


@dataclass(frozen=True)
class WorldKeyRevokedRecord:
    world_id: str
    revoked_subject_id: str
    key_hash: str
    reason: str
    effective_at: str
    prev: Optional[str]
    ts: str
    sig: str

    def body(self):
        return {
            "type": "world_key_revoked",
            "world_id": self.world_id,
            "revoked_subject_id": self.revoked_subject_id,
            "key_hash": self.key_hash,
            "reason": self.reason,
            "effective_at": self.effective_at,
            "prev": self.prev,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


# =====================================================================
# RevocableGalleryWorld
# =====================================================================

class RevocableGalleryWorld(GovernedGalleryWorld):
    def __init__(self, keypair, policy):
        super().__init__(keypair, policy)
        self._current_keeper_id = self._world_id
        self._valid_keepers = {self._world_id}
        self._revoked_keys = {}

    @property
    def current_keeper_id(self):
        return self._current_keeper_id

    def revoke_world_key(self, key, reason=""):
        """Revoke a world-key. Only the current keeper can revoke."""
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        if key.issuer_id != self._current_keeper_id:
            raise ValueError(
                "only the current keeper can revoke a key "
                "issued by themselves")
        key_hash = _hash(key.body())
        body = {
            "type": "world_key_revoked",
            "world_id": self._world_id,
            "revoked_subject_id": key.subject_id,
            "key_hash": key_hash,
            "reason": reason,
            "effective_at": _now(),
            "prev": self._last_hash,
            "ts": _now(),
        }
        rec = WorldKeyRevokedRecord(
            world_id=self._world_id,
            revoked_subject_id=key.subject_id,
            key_hash=key_hash,
            reason=reason,
            effective_at=body["effective_at"],
            prev=self._last_hash,
            ts=body["ts"],
            sig=self._keypair.sign(
                _canonical(body)).hex(),
        )
        self._records.append(rec)
        self._revoked_keys[key_hash] = body["effective_at"]
        self._last_hash = rec.record_hash()
        return rec

    def rotate_keeper(self, new_keeper_kp):
        """Rotate to a new keeper. Both old and new co-sign."""
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        new_id = _did_from_kp(new_keeper_kp)
        if new_id == self._current_keeper_id:
            raise ValueError("new keeper equals current keeper")
        body = {
            "type": "keeper_rotation",
            "world_id": self._world_id,
            "old_keeper_id": self._current_keeper_id,
            "new_keeper_id": new_id,
            "prev": self._last_hash,
            "ts": _now(),
        }
        sig_old = self._keypair.sign(
            _canonical(body)).hex()
        sig_new = new_keeper_kp.sign(
            _canonical(body)).hex()
        rec = KeeperRotationRecord(
            world_id=self._world_id,
            old_keeper_id=self._current_keeper_id,
            new_keeper_id=new_id,
            prev=self._last_hash,
            ts=body["ts"],
            sig_old=sig_old,
            sig_new=sig_new,
        )
        self._records.append(rec)
        self._keypair = new_keeper_kp
        self._current_keeper_id = new_id
        self._valid_keepers.add(new_id)
        self._last_hash = rec.record_hash()
        return rec

    def is_key_revoked(self, key):
        return _hash(key.body()) in self._revoked_keys

    # Fix (ours): the module's docstring says requests made with a
    # revoked world-key are refused, and its demo expects it, but no
    # request method checked; each now does, before the governed one.
    def request_add(self, request, member):
        if self.is_key_revoked(request.world_key):
            return self._refuse(request, "add_member_request",
                                "world-key revoked")
        return super().request_add(request, member)

    def request_retire(self, request):
        if self.is_key_revoked(request.world_key):
            return self._refuse(request, "retire_member_request",
                                "world-key revoked")
        return super().request_retire(request)

    def request_change_policy(self, request):
        if self.is_key_revoked(request.world_key):
            return self._refuse(request, "change_policy_request",
                                "world-key revoked")
        return super().request_change_policy(request)


# =====================================================================
# Verification
# =====================================================================

def _verify_accepted_request(
    request_dict, world_id, valid_keepers,
    revoked_keys, apply_ts, expected_type,
):
    """Verify an embedded request that was *accepted*. All checks
    including revocation at apply-time. Returns (ok, reason)."""
    if not isinstance(request_dict, dict):
        return (False, "request not a dict")
    if request_dict.get("type") != expected_type:
        return (False,
                 f"request type {request_dict.get('type')!r} "
                 f"!= {expected_type!r}")
    if request_dict.get("world_id") != world_id:
        return (False, "request targets another gallery")
    try:
        wk = GalleryWorldKey.from_dict(request_dict["world_key"])
    except (KeyError, ValueError):
        return (False, "malformed world-key")
    if wk.issuer_id not in valid_keepers:
        return (False,
                 f"world-key issuer {wk.issuer_id[:16]}... "
                 f"is not a valid keeper")
    if not verify_world_key(wk, wk.issuer_id):
        return (False, "world-key signature invalid")
    if wk.subject_id != request_dict["requester_id"]:
        return (False, "world-key subject mismatch")
    if wk.valid_until <= request_dict["ts"]:
        return (False, "world-key expired at request time")
    key_hash = _hash(wk.body())
    if key_hash in revoked_keys:
        if revoked_keys[key_hash] <= apply_ts:
            return (False,
                     f"world-key revoked at "
                     f"{revoked_keys[key_hash]}, "
                     f"applied at {apply_ts}")
    body = {k: v for k, v in request_dict.items()
             if k != "sig"}
    if not _verify_sig(request_dict["requester_id"],
                        body, request_dict["sig"]):
        return (False, "request signature invalid")
    return (True, "request verifies")


def _verify_refused_request(
    request_dict, world_id, valid_keepers,
):
    """Verify an embedded request that was *refused*.
    Verifies the request is well-formed; does not re-derive
    the refusal reason (gallery's claim). Returns (ok, reason)."""
    if not isinstance(request_dict, dict):
        return (False, "request not a dict")
    if request_dict.get("world_id") != world_id:
        return (False, "request targets another gallery")
    try:
        wk = GalleryWorldKey.from_dict(request_dict["world_key"])
    except (KeyError, ValueError):
        return (False, "malformed world-key")
    if not verify_world_key(wk, wk.issuer_id):
        return (False, "world-key signature invalid")
    body = {k: v for k, v in request_dict.items()
             if k != "sig"}
    if not _verify_sig(request_dict["requester_id"],
                        body, request_dict["sig"]):
        return (False, "request signature invalid")
    return (True, "refused request verifies")


def verify_revocable_governed_log(gallery, extend=None):
    """Extended verifier: keeper timeline + revocation set.

    extend: optional callback(rec, i, state) -> None | (ok, reason).
    None = base handles this record. (True, "") = extender handled
    it, skip base. (False, reason) = fail. state is a shared dict
    the extender can read/write; base populates 'occupied' if
    present but does not depend on it.
    """
    # Fix (ours): DeepSeek's hook for extenders (gallery_attention.py,
    # gallery_burst.py), which the record gives as an outline with
    # "# ... existing ..." in place of this function's body
    # (gallery_revocation.py@16659), merged into it by hand.
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    seed = gallery.seed_body()
    current_keeper = seed["world_id"]
    valid_keepers = {current_keeper}
    revoked_keys = {}

    if not _verify_sig(current_keeper, seed,
                        gallery.seed_sig()):
        return (False, "seed signature invalid")
    try:
        policy = GalleryPolicy(
            max_members=seed["initial_policy"]["max_members"],
            allowed_kinds=tuple(
                seed["initial_policy"]["allowed_kinds"]))
    except (KeyError, ValueError, TypeError) as e:
        return (False, f"malformed initial policy: {e}")

    occupied = {}
    cycle = 0
    prev = None
    accepted_hashes = set()
    refused_hashes = set()
    state = {"occupied": occupied, "valid_keepers": valid_keepers,
             "revoked_keys": revoked_keys, "policy": policy}

    for i, rec in enumerate(gallery.records()):
        if rec.world_id != gallery.world_id:
            return (False, f"record {i}: world_id mismatch")
        if rec.prev != prev:
            return (False, f"record {i}: prev mismatch")

        if isinstance(rec, KeeperRotationRecord):
            if rec.old_keeper_id != current_keeper:
                return (False,
                         f"record {i}: old keeper "
                         f"{rec.old_keeper_id[:16]}... "
                         f"!= current "
                         f"{current_keeper[:16]}...")
            body = rec.rotation_body()
            if not _verify_sig(rec.old_keeper_id, body,
                                rec.sig_old):
                return (False,
                         f"record {i}: sig_old invalid")
            if not _verify_sig(rec.new_keeper_id, body,
                                rec.sig_new):
                return (False,
                         f"record {i}: sig_new invalid")
            valid_keepers.add(rec.new_keeper_id)
            current_keeper = rec.new_keeper_id
        else:
            if not _verify_sig(current_keeper,
                                rec.body(), rec.sig):
                return (False,
                         f"record {i}: signature invalid "
                         f"against keeper "
                         f"{current_keeper[:16]}...")

            if extend is not None:
                result = extend(rec, i, state)
                if result is not None:
                    ok, reason = result
                    if not ok:
                        return (False, reason)
                    prev = rec.record_hash()
                    continue

            if isinstance(rec, WorldKeyRevokedRecord):
                revoked_keys[rec.key_hash] = rec.effective_at

            elif isinstance(rec, PolicyChangeRecord):
                if rec.old_policy_hash != policy.policy_hash():
                    return (False,
                             f"record {i}: old_policy mismatch")
                try:
                    new_policy = GalleryPolicy(
                        max_members=rec.new_policy["max_members"],
                        allowed_kinds=tuple(
                            rec.new_policy["allowed_kinds"]))
                except (KeyError, ValueError, TypeError):
                    return (False,
                             f"record {i}: malformed policy")
                if new_policy.policy_hash() != rec.new_policy_hash:
                    return (False,
                             f"record {i}: new_policy hash "
                             f"mismatch")
                if rec.request_hash is not None:
                    if rec.request_hash in accepted_hashes \
                            or rec.request_hash in refused_hashes:
                        return (False,
                                 f"record {i}: request hash "
                                 f"reused")
                    ok, reason = _verify_accepted_request(
                        rec.request, gallery.world_id,
                        valid_keepers, revoked_keys,
                        rec.ts, "change_policy_request")
                    if not ok:
                        return (False,
                                 f"record {i}: {reason}")
                    accepted_hashes.add(rec.request_hash)
                policy = new_policy
                state["policy"] = policy

            elif isinstance(rec, MemberAddedRecord):
                if rec.slot in occupied:
                    return (False,
                             f"record {i}: slot occupied")
                if not policy.allows_kind(rec.member_kind):
                    return (False,
                             f"record {i}: kind not allowed")
                if len(occupied) >= policy.max_members:
                    return (False,
                             f"record {i}: capacity exceeded")
                if rec.request_hash is not None:
                    if rec.request_hash in accepted_hashes \
                            or rec.request_hash in refused_hashes:
                        return (False,
                                 f"record {i}: request hash "
                                 f"reused")
                    ok, reason = _verify_accepted_request(
                        rec.request, gallery.world_id,
                        valid_keepers, revoked_keys,
                        rec.ts, "add_member_request")
                    if not ok:
                        return (False,
                                 f"record {i}: {reason}")
                    accepted_hashes.add(rec.request_hash)
                occupied[rec.slot] = rec.member_id

            elif isinstance(rec, MemberRetiredRecord):
                if occupied.get(rec.slot) != rec.member_id:
                    return (False,
                             f"record {i}: retirement mismatch")
                if rec.request_hash is not None:
                    if rec.request_hash in accepted_hashes \
                            or rec.request_hash in refused_hashes:
                        return (False,
                                 f"record {i}: request hash "
                                 f"reused")
                    ok, reason = _verify_accepted_request(
                        rec.request, gallery.world_id,
                        valid_keepers, revoked_keys,
                        rec.ts, "retire_member_request")
                    if not ok:
                        return (False,
                                 f"record {i}: {reason}")
                    accepted_hashes.add(rec.request_hash)
                del occupied[rec.slot]

            elif isinstance(rec, GalleryCycleRecord):
                if rec.cycle != cycle + 1:
                    return (False,
                             f"record {i}: cycle not monotonic")
                cycle = rec.cycle
                mentioned = {a["slot"] for a in rec.advances}
                if mentioned != set(occupied.keys()):
                    return (False,
                             f"record {i}: advances do not "
                             f"match occupied slots")

            elif isinstance(rec, RequestRefusedRecord):
                if rec.request_hash in refused_hashes:
                    pass  # duplicate refusal — no-op
                elif rec.request_hash in accepted_hashes:
                    return (False,
                             f"record {i}: refused a request "
                             f"already accepted")
                else:
                    refused_hashes.add(rec.request_hash)
                    ok, reason = _verify_refused_request(
                        rec.request, gallery.world_id,
                        valid_keepers)
                    if not ok:
                        return (False,
                                 f"record {i}: {reason}")
                if rec.requester_id != rec.request.get(
                        "requester_id"):
                    return (False,
                             f"record {i}: requester mismatch")
            else:
                return (False, f"record {i}: unknown type")

        prev = rec.record_hash()

    return (True, "revocable governed log verifies")


def verify_revocable_full(gallery):
    v = verify_revocable_governed_log(gallery)
    if not v[0]:
        return (False, f"log: {v[1]}")
    v = verify_governed_members(gallery)
    if not v[0]:
        return (False, f"members: {v[1]}")
    return (True, "full verification passes")


# =====================================================================
# Rendering
# =====================================================================

def render_log_summary(gallery):
    """Compact log view with markers for rotation and revocation."""
    lines = []
    for i, rec in enumerate(gallery.records()):
        if isinstance(rec, KeeperRotationRecord):
            lines.append(
                f"    [{i}] ROTATE  {rec.old_keeper_id[:12]}... "
                f"→ {rec.new_keeper_id[:12]}...")
        elif isinstance(rec, WorldKeyRevokedRecord):
            lines.append(
                f"    [{i}] REVOKE  {rec.revoked_subject_id[:16]}... "
                f"({rec.reason})")
        elif isinstance(rec, MemberAddedRecord):
            marker = "REQ" if rec.request_hash else "KEEP"
            lines.append(
                f"    [{i}] {marker:5s}  add slot {rec.slot}: "
                f"{rec.member_kind}")
        elif isinstance(rec, MemberRetiredRecord):
            marker = "REQ" if rec.request_hash else "KEEP"
            lines.append(
                f"    [{i}] {marker:5s}  retire slot {rec.slot}")
        elif isinstance(rec, PolicyChangeRecord):
            marker = "REQ" if rec.request_hash else "KEEP"
            lines.append(
                f"    [{i}] {marker:5s}  policy → "
                f"max_members={rec.new_policy['max_members']}")
        elif isinstance(rec, RequestRefusedRecord):
            lines.append(
                f"    [{i}] REFUS  {rec.request_type} "
                f"({rec.reason})")
        elif isinstance(rec, GalleryCycleRecord):
            lines.append(f"    [{i}] cycle {rec.cycle} "
                          f"({len(rec.advances)} members)")
    return "\n".join(lines) if lines else "    (empty)"


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir=None):
    from pathlib import Path
    import json as _json
    from gallery_world import (
        AtomicFractalMember, FractalGridMember,
        ChaosGameMember, CoupledCAMember,
    )
    from fractal_world_v3 import AtomicFractalWorld, WorldTemplate
    from fractal_grid_world import FractalGridWorld, GridParams
    from chaos_game_world import ChaosGameWorld, SIERPINSKI
    from coupled_ca_world import CoupledCAWorld

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")
    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "gallery_revocation"
    path.mkdir(parents=True, exist_ok=True)

    keeper_kp_1 = Ed25519PrivateKey.generate()
    keeper_kp_2 = Ed25519PrivateKey.generate()
    initial_policy = GalleryPolicy(
        max_members=3,
        allowed_kinds=("atomic_fractal", "fractal_grid"))
    gallery = RevocableGalleryWorld(keeper_kp_1, initial_policy)

    x_kp = Ed25519PrivateKey.generate()
    x_id = _did_from_kp(x_kp)
    y_kp = Ed25519PrivateKey.generate()
    y_id = _did_from_kp(y_kp)
    z_kp = Ed25519PrivateKey.generate()
    z_id = _did_from_kp(z_kp)

    x_key = gallery.issue_world_key(x_id, "control")
    y_key = gallery.issue_world_key(y_id, "observe")
    z_key = gallery.issue_world_key(z_id, "terminal")

    # Members
    def make_plant():
        return AtomicFractalMember(AtomicFractalWorld(
            template=WorldTemplate(
                template_id="t", branch_length=2, max_depth=2),
            pot=(0, 0, 10, 10), initial_tip=(5, 8, 0),
            keypair=Ed25519PrivateKey.generate()))

    def make_grid():
        return FractalGridMember(FractalGridWorld(
            params=GridParams(rule_number=90, max_gen=5),
            initial_row=[0],
            keypair=Ed25519PrivateKey.generate()), max_gen=5)

    def make_chaos():
        return ChaosGameMember(ChaosGameWorld(
            preset=SIERPINSKI, growth_mode="seeded_random",
            initial_point=(500, 500),
            keypair=Ed25519PrivateKey.generate(),
            prng_seed=0xABCD), max_steps=20)

    # 1. K1 adds plant directly
    gallery.add(0, make_plant())

    # 2. X (control) requests add grid → accepted
    from gallery_governance import (
        sign_add_member, sign_retire_member,
        sign_change_policy,
    )
    grid1 = make_grid()
    req = sign_add_member(
        gallery.world_id, 1, grid1, x_kp, x_key)
    gallery.request_add(req, grid1)

    # 3. Y (observe) requests add grid → refused (tier)
    grid2 = make_grid()
    req = sign_add_member(
        gallery.world_id, 2, grid2, y_kp, y_key)
    gallery.request_add(req, grid2)

    # 4. K1 revokes Y's key
    gallery.revoke_world_key(y_key, "policy violation")

    # 5. Y retries → refused (revoked)
    grid2b = make_grid()
    req = sign_add_member(
        gallery.world_id, 2, grid2b, y_kp, y_key)
    gallery.request_add(req, grid2b)

    # 6. K1 rotates to K2
    gallery.rotate_keeper(keeper_kp_2)

    # 7. Z (terminal) requests policy change → accepted (K2 signs)
    new_policy = GalleryPolicy(
        max_members=5,
        allowed_kinds=("atomic_fractal", "fractal_grid",
                        "chaos_game"))
    req = sign_change_policy(
        gallery.world_id, new_policy.to_dict(), z_kp, z_key)
    gallery.request_change_policy(req)

    # 8. X (control) requests add chaos → accepted
    chaos = make_chaos()
    req = sign_add_member(
        gallery.world_id, 2, chaos, x_kp, x_key)
    gallery.request_add(req, chaos)

    # 9. X retires the grid from slot 1 → accepted
    grid1_id = gallery.members()[1].world_id()
    req = sign_retire_member(
        gallery.world_id, 1, grid1_id, "done",
        x_kp, x_key)
    gallery.request_retire(req)

    # 10. Grow
    gallery.grow_n(5)

    v_log = verify_revocable_governed_log(gallery)
    v_full = verify_revocable_full(gallery)

    print("=" * 74)
    print("Revocation + Rotation — the gallery endures")
    print("=" * 74)
    print()
    print(f"  Gallery:        {gallery.world_id[:32]}...")
    print(f"  Initial keeper: {gallery.world_id[:24]}...")
    print(f"  Current keeper: {gallery.current_keeper_id[:24]}...")
    print(f"  Cycles:         {gallery.cycle()}")
    print(f"  Members:        {len(gallery.members())}")
    print()
    print("  Log:")
    print(render_log_summary(gallery))
    print()
    print("  Verification:")
    print(f"    revocable log:  {v_log[0]}  ({v_log[1]})")
    print(f"    full:           {v_full[0]}  ({v_full[1]})")
    print()
    print("  What this establishes:")
    print("    - The verifier walks the keeper timeline. Records")
    print("      before rotation verify against K1; records after")
    print("      verify against K2. Rotation is signed by both.")
    print("    - Revocation is a signed record. Requests using a")
    print("      revoked key are refused by the gallery *and*")
    print("      caught by the verifier independently.")
    print("    - Revocation is temporal: requests applied before")
    print("      effective_at remain valid; those after are")
    print("      refused. The verifier checks state-at-apply-time.")
    print("    - Old keys survive rotation (they were issued by")
    print("      K1, which was a valid keeper at issue time).")
    print("      Rotation doesn't invalidate prior grants.")
    print()
    print("  Honest limits:")
    print("    - Post-rotation key issuance is out of scope here.")
    print("    - Compromise of K1 before rotation is not")
    print("      retroactively detectable.")
    print("    - Verifier trusts refusals' stated reasons.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'After great pain, a formal feeling comes –'")
    print("    'The Nerves sit ceremonious, like Tombs –'")

    audit = {
        "gallery_id": gallery.world_id,
        "initial_keeper": gallery.world_id,
        "current_keeper": gallery.current_keeper_id,
        "rotated": gallery.current_keeper_id != gallery.world_id,
        "cycles": gallery.cycle(),
        "members": [
            {"slot": s, "kind": m.kind, "steps": m.steps()}
            for s, m in sorted(gallery.members().items())
        ],
        "revoked_key_count": len(gallery._revoked_keys),
        "refusal_count": sum(
            1 for r in gallery.records()
            if isinstance(r, RequestRefusedRecord)),
        "verification": {
            "revocable_log": v_log[0],
            "full": v_full[0],
        },
    }
    (path / "gallery_revocation_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {path}/gallery_revocation_demo.json")
    return audit
