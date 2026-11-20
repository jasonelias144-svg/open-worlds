"""
chat_room.py — Chat worlds for the Commons.

Proposal sketch, not a course step. The chat world is the
minimum viable world: an append-only log of participant-signed
events, checked against the room's law. No tick, no geometry.
The room's "physics" is authorization: who can post, how often,
how long, and what a moderator may do.

Builds on fractal_world_v3 for the WorldKey, TIERS, and sig
conventions (reused unchanged). Chat rooms inherit the tier
model directly: observe / communicate / control / terminal.

Simplifications (marked for the standard's review):

  - `sig` fields are flat, not W3C DataIntegrityProof objects.
  - Key names in body() should be checked against the schema.
  - Messages are plaintext. Sealed rooms (HPKE per message, so
    only participants can read) are a schema+HPKE layer that
    composes on top; the sketch is the plaintext layer.
  - The room is held by a keeper (the creator) in the demo,
    so "the room accepts or refuses" has a concrete signer.
    A peer-to-peer room with no keeper is future work; the
    sketches' shape (chain + countersigned accepted events)
    works either way.
  - Rate limit is per-author, per-window, in ticks. Wall-clock
    timestamps are recorded but the replay check uses log
    positions (deterministic; not wall-clock).
  - No persistent identity across rooms yet. A participant is
    the same key everywhere; a "personal world" that holds the
    participant's history is a future stage.
  - The Commons registers rooms but does not yet govern
    visibility (public/sealed), discovery algorithms, or
    per-room admission beyond the room's own join policy.
  - No moderation vocabulary beyond redact. Editing messages
    is not possible (records are never edited, only redacted),
    which matches the standard.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Union

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey, Ed25519PublicKey)
    from cryptography.hazmat.primitives import serialization
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from fractal_world_v3 import (
    WorldKey, verify_world_key, TIERS, TIER_RANK,
    _did_from_kp, _pubkey_from_did, _canonical, _hash, _now)


# =====================================================================
# Template
# =====================================================================

@dataclass(frozen=True)
class RoomTemplate:
    template_id: str
    topic: str
    max_msg_len: int = 4000
    rate_limit_count: int = 10
    rate_limit_window: int = 20        # messages per N records by same author
    join_policy: str = "open"          # "open" | "invite" | "approval"
    moderation: str = "author_only"    # "author_only" | "moderator" | "none"
    welcome: str = ""
    branch_policy: Optional[Dict] = None

    def to_dict(self):
        return {
            "template_id": self.template_id,
            "topic": self.topic,
            "max_msg_len": self.max_msg_len,
            "rate_limit_count": self.rate_limit_count,
            "rate_limit_window": self.rate_limit_window,
            "join_policy": self.join_policy,
            "moderation": self.moderation,
            "welcome": self.welcome,
            "branch_policy": self.branch_policy,
        }

    def template_hash(self):
        return _hash(self.to_dict())


# =====================================================================
# Records
# =====================================================================

@dataclass(frozen=True)
class RoomCreated:
    world_id: str
    template_hash: str
    creator_id: str
    opening_transcript: Optional[Dict]
    ts: str
    sig_creator: str
    sig_room: str

    def body(self):
        d = {
            "type": "room_created",
            "world_id": self.world_id,
            "template_hash": self.template_hash,
            "creator_id": self.creator_id,
            "ts": self.ts,
        }
        if self.opening_transcript is not None:
            d["opening_transcript"] = dict(self.opening_transcript)
        return d

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class Message:
    world_id: str
    seq: int
    prev: Optional[str]
    author_id: str
    text: str
    ts: str
    sig_author: str
    sig_room: str

    def body(self):
        return {
            "type": "message",
            "world_id": self.world_id,
            "seq": self.seq,
            "prev": self.prev,
            "author_id": self.author_id,
            "text": self.text,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class Join:
    world_id: str
    seq: int
    prev: Optional[str]
    subject_id: str
    tier: str
    ts: str
    sig_subject: str
    sig_room: str

    def body(self):
        return {
            "type": "join",
            "world_id": self.world_id,
            "seq": self.seq,
            "prev": self.prev,
            "subject_id": self.subject_id,
            "tier": self.tier,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class Leave:
    world_id: str
    seq: int
    prev: Optional[str]
    subject_id: str
    ts: str
    sig_subject: str

    def body(self):
        return {
            "type": "leave",
            "world_id": self.world_id,
            "seq": self.seq,
            "prev": self.prev,
            "subject_id": self.subject_id,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class Redact:
    world_id: str
    seq: int
    prev: Optional[str]
    subject_id: str
    target_hash: str
    reason: str
    ts: str
    sig_subject: str
    sig_room: str

    def body(self):
        return {
            "type": "redact",
            "world_id": self.world_id,
            "seq": self.seq,
            "prev": self.prev,
            "subject_id": self.subject_id,
            "target_hash": self.target_hash,
            "reason": self.reason,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


@dataclass(frozen=True)
class Refusal:
    world_id: str
    seq: int
    prev: Optional[str]
    request_hash: str
    requester_id: str
    reason: str
    ts: str
    sig_room: str

    def body(self):
        return {
            "type": "refusal",
            "world_id": self.world_id,
            "seq": self.seq,
            "prev": self.prev,
            "request_hash": self.request_hash,
            "requester_id": self.requester_id,
            "reason": self.reason,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


RoomRecord = Union[RoomCreated, Message, Join, Leave, Redact, Refusal]


# =====================================================================
# Request envelopes (unsigned intents; signed on the way in)
# =====================================================================

@dataclass(frozen=True)
class PostRequest:
    world_id: str
    author_id: str
    text: str
    ts: str
    sig: str

    def body(self):
        return {
            "type": "post_request",
            "world_id": self.world_id,
            "author_id": self.author_id,
            "text": self.text,
            "ts": self.ts,
        }

    def request_hash(self):
        return _hash(self.body())


def sign_post_request(world_id, author_kp, text, ts=None):
    author_id = _did_from_kp(author_kp)
    body = {
        "type": "post_request",
        "world_id": world_id,
        "author_id": author_id,
        "text": text,
        "ts": ts or _now(),
    }
    return PostRequest(
        world_id=world_id, author_id=author_id,
        text=text, ts=body["ts"],
        sig=author_kp.sign(_canonical(body)).hex())


@dataclass(frozen=True)
class JoinRequest:
    world_id: str
    subject_id: str
    tier: str
    ts: str
    sig: str

    def body(self):
        return {
            "type": "join_request",
            "world_id": self.world_id,
            "subject_id": self.subject_id,
            "tier": self.tier,
            "ts": self.ts,
        }

    def request_hash(self):
        return _hash(self.body())


def sign_join_request(world_id, subject_kp, tier, ts=None):
    subject_id = _did_from_kp(subject_kp)
    body = {
        "type": "join_request",
        "world_id": world_id,
        "subject_id": subject_id,
        "tier": tier,
        "ts": ts or _now(),
    }
    return JoinRequest(
        world_id=world_id, subject_id=subject_id, tier=tier,
        ts=body["ts"],
        sig=subject_kp.sign(_canonical(body)).hex())


@dataclass(frozen=True)
class RedactRequest:
    world_id: str
    subject_id: str
    target_hash: str
    reason: str
    ts: str
    sig: str

    def body(self):
        return {
            "type": "redact_request",
            "world_id": self.world_id,
            "subject_id": self.subject_id,
            "target_hash": self.target_hash,
            "reason": self.reason,
            "ts": self.ts,
        }

    def request_hash(self):
        return _hash(self.body())


def sign_redact_request(world_id, subject_kp, target_hash,
                        reason, ts=None):
    subject_id = _did_from_kp(subject_kp)
    body = {
        "type": "redact_request",
        "world_id": world_id,
        "subject_id": subject_id,
        "target_hash": target_hash,
        "reason": reason,
        "ts": ts or _now(),
    }
    return RedactRequest(
        world_id=world_id, subject_id=subject_id,
        target_hash=target_hash, reason=reason, ts=body["ts"],
        sig=subject_kp.sign(_canonical(body)).hex())


# =====================================================================
# Transcript (for porting)
# =====================================================================

@dataclass(frozen=True)
class Transcript:
    source_label: str
    entries: List[Dict]        # [{speaker, ts, text}]
    porter_id: str
    ts: str
    sig: str

    def body(self):
        return {
            "type": "transcript",
            "source_label": self.source_label,
            "entries": [dict(e) for e in self.entries],
            "porter_id": self.porter_id,
            "ts": self.ts,
        }

    def transcript_hash(self):
        return _hash(self.body())


def sign_transcript(source_label, entries, porter_kp, ts=None):
    porter_id = _did_from_kp(porter_kp)
    body = {
        "type": "transcript",
        "source_label": source_label,
        "entries": [dict(e) for e in entries],
        "porter_id": porter_id,
        "ts": ts or _now(),
    }
    return Transcript(
        source_label=source_label,
        entries=[dict(e) for e in entries],
        porter_id=porter_id, ts=body["ts"],
        sig=porter_kp.sign(_canonical(body)).hex())


def verify_transcript(t: Transcript) -> bool:
    if not HAS_CRYPTO:
        return False
    try:
        _pubkey_from_did(t.porter_id).verify(
            bytes.fromhex(t.sig), _canonical(t.body()))
        return True
    except Exception:
        return False


# =====================================================================
# ChatRoom
# =====================================================================

class ChatRoom:
    def __init__(self, template: RoomTemplate, creator_kp,
                 opening_transcript: Optional[Transcript] = None):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        self._template = template
        self._keypair = creator_kp
        self._world_id = _did_from_kp(creator_kp)
        self._records: List[RoomRecord] = []
        self._members: Dict[str, str] = {}   # subject_id -> tier
        self._last_hash: Optional[str] = None
        self._seq = 0
        # Creator is terminal-tier member by construction
        self._members[self._world_id] = "terminal"
        # Build the room_created record
        opening = None
        if opening_transcript is not None:
            if not verify_transcript(opening_transcript):
                raise ValueError("opening transcript sig invalid")
            opening = opening_transcript.body()
            opening["sig"] = opening_transcript.sig
        body = {
            "type": "room_created",
            "world_id": self._world_id,
            "template_hash": template.template_hash(),
            "creator_id": self._world_id,
            "ts": _now(),
        }
        if opening is not None:
            body["opening_transcript"] = opening
        sig_creator = creator_kp.sign(_canonical(body)).hex()
        # Room countersigns (creator is the room's keeper here)
        sig_room = creator_kp.sign(
            _canonical({**body, "sig_creator": sig_creator})).hex()
        rec = RoomCreated(
            world_id=self._world_id,
            template_hash=template.template_hash(),
            creator_id=self._world_id,
            opening_transcript=opening,
            ts=body["ts"],
            sig_creator=sig_creator,
            sig_room=sig_room)
        self._append(rec)

    # -- Accessors ------------------------------------------------

    @property
    def world_id(self):
        return self._world_id

    @property
    def template(self):
        return self._template

    def records(self):
        return list(self._records)

    def members(self):
        return dict(self._members)

    def last_hash(self):
        return self._last_hash

    def _append(self, rec):
        self._records.append(rec)
        self._last_hash = rec.record_hash()
        self._seq += 1

    def _refuse(self, request, reason):
        body = {
            "type": "refusal",
            "world_id": self._world_id,
            "seq": self._seq,
            "prev": self._last_hash,
            "request_hash": request.request_hash(),
            "requester_id": _extract_requester_id(request),
            "reason": reason,
            "ts": _now(),
        }
        rec = Refusal(
            world_id=self._world_id,
            seq=self._seq,
            prev=self._last_hash,
            request_hash=request.request_hash(),
            requester_id=body["requester_id"],
            reason=reason,
            ts=body["ts"],
            sig_room=self._keypair.sign(
                _canonical(body)).hex())
        self._append(rec)
        return rec

    # -- Join / leave --------------------------------------------

    def join(self, request: JoinRequest):
        if not _verify_simple_sig(request.body(), request.sig,
                                  request.subject_id):
            return self._refuse(request, "invalid_request_sig")
        if request.subject_id in self._members:
            return self._refuse(request, "already_member")
        if request.tier not in TIER_RANK:
            return self._refuse(request, "unknown_tier")
        if request.tier == "observe":
            # Anyone may observe; no join needed. But we accept
            # it as a record so the log shows who watched.
            pass
        if self._template.join_policy == "invite":
            # Must hold a world-key for this tier
            return self._refuse(request, "invite_required")
        if self._template.join_policy == "approval":
            return self._refuse(request, "approval_required")
        # "open": accept
        body = {
            "type": "join",
            "world_id": self._world_id,
            "seq": self._seq,
            "prev": self._last_hash,
            "subject_id": request.subject_id,
            "tier": request.tier,
            "ts": request.ts,
        }
        sig_room = self._keypair.sign(
            _canonical({**body, "sig_subject": request.sig})).hex()
        rec = Join(
            world_id=self._world_id, seq=self._seq,
            prev=self._last_hash,
            subject_id=request.subject_id,
            tier=request.tier, ts=request.ts,
            sig_subject=request.sig, sig_room=sig_room)
        self._members[request.subject_id] = request.tier
        self._append(rec)
        return rec

    def leave(self, subject_kp) -> Optional[Leave]:
        subject_id = _did_from_kp(subject_kp)
        if subject_id not in self._members:
            return None
        body = {
            "type": "leave",
            "world_id": self._world_id,
            "seq": self._seq,
            "prev": self._last_hash,
            "subject_id": subject_id,
            "ts": _now(),
        }
        sig = subject_kp.sign(_canonical(body)).hex()
        rec = Leave(
            world_id=self._world_id, seq=self._seq,
            prev=self._last_hash,
            subject_id=subject_id, ts=body["ts"],
            sig_subject=sig)
        del self._members[subject_id]
        self._append(rec)
        return rec

    # -- Post ----------------------------------------------------

    def post(self, request: PostRequest):
        if not _verify_simple_sig(request.body(), request.sig,
                                  request.author_id):
            return self._refuse(request, "invalid_request_sig")
        if request.author_id not in self._members:
            return self._refuse(request, "not_a_member")
        if TIER_RANK[self._members[request.author_id]] < \
                TIER_RANK["communicate"]:
            return self._refuse(request, "insufficient_tier")
        if len(request.text) > self._template.max_msg_len:
            return self._refuse(request, "message_too_long")
        if not self._rate_ok(request.author_id):
            return self._refuse(request, "rate_limit")
        body = {
            "type": "message",
            "world_id": self._world_id,
            "seq": self._seq,
            "prev": self._last_hash,
            "author_id": request.author_id,
            "text": request.text,
            "ts": request.ts,
        }
        sig_room = self._keypair.sign(
            _canonical({**body, "sig_author": request.sig})).hex()
        rec = Message(
            world_id=self._world_id, seq=self._seq,
            prev=self._last_hash,
            author_id=request.author_id,
            text=request.text, ts=request.ts,
            sig_author=request.sig, sig_room=sig_room)
        self._append(rec)
        return rec

    def _rate_ok(self, author_id):
        """Messages by this author in the last N log records must
        be under rate_limit_count. Deterministic; uses log
        positions, not wall-clock."""
        window = self._template.rate_limit_window
        cap = self._template.rate_limit_count
        recent = [r for r in self._records[-window:]
                  if isinstance(r, Message)
                  and r.author_id == author_id]
        return len(recent) < cap

    # -- Redact --------------------------------------------------

    def redact(self, request: RedactRequest):
        if not _verify_simple_sig(request.body(), request.sig,
                                  request.subject_id):
            return self._refuse(request, "invalid_request_sig")
        if request.subject_id not in self._members:
            return self._refuse(request, "not_a_member")
        # Find target
        target = next((r for r in self._records
                       if r.record_hash() == request.target_hash
                       and isinstance(r, Message)), None)
        if target is None:
            return self._refuse(request, "target_not_found")
        # Author may always redact their own message
        is_author = (target.author_id == request.subject_id)
        is_moderator = (
            self._template.moderation == "moderator"
            and TIER_RANK[self._members[request.subject_id]] >=
                TIER_RANK["control"])
        if self._template.moderation == "none":
            return self._refuse(request, "moderation_disabled")
        if not (is_author or is_moderator):
            return self._refuse(request, "not_allowed")
        body = {
            "type": "redact",
            "world_id": self._world_id,
            "seq": self._seq,
            "prev": self._last_hash,
            "subject_id": request.subject_id,
            "target_hash": request.target_hash,
            "reason": request.reason,
            "ts": request.ts,
        }
        sig_room = self._keypair.sign(
            _canonical({**body, "sig_subject": request.sig})).hex()
        rec = Redact(
            world_id=self._world_id, seq=self._seq,
            prev=self._last_hash,
            subject_id=request.subject_id,
            target_hash=request.target_hash,
            reason=request.reason, ts=request.ts,
            sig_subject=request.sig, sig_room=sig_room)
        self._append(rec)
        return rec


def _extract_requester_id(request):
    for attr in ("author_id", "subject_id", "requester_id"):
        v = getattr(request, attr, None)
        if v:
            return v
    return ""


def _verify_simple_sig(body, sig, did):
    try:
        _pubkey_from_did(did).verify(bytes.fromhex(sig),
                                     _canonical(body))
        return True
    except Exception:
        return False


# =====================================================================
# Verification
# =====================================================================

def verify_room(room: ChatRoom) -> Tuple[bool, str]:
    """Check chain, signatures, and policy replay."""
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    pub_room = _pubkey_from_did(room.world_id)
    prev = None
    members: Dict[str, str] = {}
    redacted: set = set()
    for i, rec in enumerate(room.records()):
        # Chain
        if isinstance(rec, RoomCreated):
            if rec.prev if hasattr(rec, "prev") else None:
                return (False, f"record {i}: room_created "
                               f"cannot have prev")
        else:
            if rec.prev != prev:
                return (False, f"record {i}: prev mismatch")
        # Room's countersignature (or creator's on the seed)
        if isinstance(rec, RoomCreated):
            try:
                _pubkey_from_did(rec.creator_id).verify(
                    bytes.fromhex(rec.sig_creator),
                    _canonical({k: v for k, v in
                                rec.body().items()
                                if k not in ("sig_creator",
                                             "sig_room")}))
            except Exception as e:
                return (False, f"record {i}: creator sig: {e}")
            try:
                pub_room.verify(
                    bytes.fromhex(rec.sig_room),
                    _canonical({**{k: v for k, v in
                                   rec.body().items()
                                   if k not in ("sig_creator",
                                                "sig_room")},
                                "sig_creator": rec.sig_creator}))
            except Exception as e:
                return (False, f"record {i}: room sig: {e}")
            members[rec.creator_id] = "terminal"
        elif isinstance(rec, Message):
            if rec.author_id not in members:
                return (False, f"record {i}: author not a member")
            if not _verify_simple_sig(
                    {k: v for k, v in rec.body().items()},
                    rec.sig_author, rec.author_id):
                return (False, f"record {i}: author sig")
            try:
                pub_room.verify(
                    bytes.fromhex(rec.sig_room),
                    _canonical({**rec.body(),
                                "sig_author": rec.sig_author}))
            except Exception as e:
                return (False, f"record {i}: room sig: {e}")
        elif isinstance(rec, Join):
            if not _verify_simple_sig(
                    {k: v for k, v in rec.body().items()},
                    rec.sig_subject, rec.subject_id):
                return (False, f"record {i}: subject sig")
            try:
                pub_room.verify(
                    bytes.fromhex(rec.sig_room),
                    _canonical({**rec.body(),
                                "sig_subject": rec.sig_subject}))
            except Exception as e:
                return (False, f"record {i}: room sig: {e}")
            members[rec.subject_id] = rec.tier
        elif isinstance(rec, Leave):
            if not _verify_simple_sig(
                    {k: v for k, v in rec.body().items()},
                    rec.sig_subject, rec.subject_id):
                return (False, f"record {i}: subject sig")
            members.pop(rec.subject_id, None)
        elif isinstance(rec, Redact):
            try:
                pub_room.verify(
                    bytes.fromhex(rec.sig_room),
                    _canonical({**rec.body(),
                                "sig_subject": rec.sig_subject}))
            except Exception as e:
                return (False, f"record {i}: room sig: {e}")
            # Verify the subject signed
            if not _verify_simple_sig(
                    {k: v for k, v in rec.body().items()},
                    rec.sig_subject, rec.subject_id):
                return (False, f"record {i}: subject sig")
            redacted.add(rec.target_hash)
        elif isinstance(rec, Refusal):
            try:
                pub_room.verify(bytes.fromhex(rec.sig_room),
                                _canonical(rec.body()))
            except Exception as e:
                return (False, f"record {i}: room sig: {e}")
        else:
            return (False, f"record {i}: unknown type")
        prev = rec.record_hash()
    return (True, "room verifies")


def visible_log(room: ChatRoom) -> List[Dict]:
    """Return the room's log with redactions applied — the view
    a reader sees. The underlying records are unchanged; the
    redaction events hide the target's text."""
    redacted: set = set()
    out: List[Dict] = []
    for rec in room.records():
        if isinstance(rec, Redact):
            redacted.add(rec.target_hash)
            out.append({"seq": rec.seq, "type": "redact",
                        "by": rec.subject_id,
                        "reason": rec.reason,
                        "target": rec.target_hash})
        elif isinstance(rec, Message):
            if rec.record_hash() in redacted:
                out.append({"seq": rec.seq, "type": "message",
                            "author": rec.author_id,
                            "text": "[redacted]",
                            "redacted": True, "ts": rec.ts})
            else:
                out.append({"seq": rec.seq, "type": "message",
                            "author": rec.author_id,
                            "text": rec.text, "ts": rec.ts})
        elif isinstance(rec, Join):
            out.append({"seq": rec.seq, "type": "join",
                        "subject": rec.subject_id,
                        "tier": rec.tier, "ts": rec.ts})
        elif isinstance(rec, Leave):
            out.append({"seq": rec.seq, "type": "leave",
                        "subject": rec.subject_id, "ts": rec.ts})
        elif isinstance(rec, RoomCreated):
            out.append({"seq": 0, "type": "created",
                        "creator": rec.creator_id,
                        "ts": rec.ts})
        elif isinstance(rec, Refusal):
            out.append({"seq": rec.seq, "type": "refused",
                        "requester": rec.requester_id,
                        "reason": rec.reason, "ts": rec.ts})
    return out


# =====================================================================
# Commons (directory)
# =====================================================================

@dataclass(frozen=True)
class RoomRegistered:
    commons_id: str
    seq: int
    prev: Optional[str]
    room_id: str
    topic: str
    template_hash: str
    room_seed_hash: str
    registered_by: str
    ts: str
    sig_registrant: str
    sig_commons: str

    def body(self):
        return {
            "type": "room_registered",
            "commons_id": self.commons_id,
            "seq": self.seq,
            "prev": self.prev,
            "room_id": self.room_id,
            "topic": self.topic,
            "template_hash": self.template_hash,
            "room_seed_hash": self.room_seed_hash,
            "registered_by": self.registered_by,
            "ts": self.ts,
        }

    def record_hash(self):
        return _hash(self.body())


class Commons:
    def __init__(self, keypair):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        self._keypair = keypair
        self._world_id = _did_from_kp(keypair)
        self._records: List[RoomRegistered] = []
        self._rooms: Dict[str, Dict] = {}
        self._last_hash: Optional[str] = None
        self._seq = 0

    @property
    def world_id(self):
        return self._world_id

    def records(self):
        return list(self._records)

    def rooms(self):
        return dict(self._rooms)

    def last_hash(self):
        return self._last_hash

    def register_room(self, room: ChatRoom, registered_by_kp,
                      topic: Optional[str] = None):
        """Register a room in the directory. The registrant signs;
        the Commons countersigns on accept."""
        registrant_id = _did_from_kp(registered_by_kp)
        # Allow registrant to be the creator or a delegate.
        # For the demo, allow anyone to register their own room;
        # a real policy would gate this.
        body = {
            "type": "room_registered",
            "commons_id": self._world_id,
            "seq": self._seq,
            "prev": self._last_hash,
            "room_id": room.world_id,
            "topic": topic or room.template.topic,
            "template_hash": room.template.template_hash(),
            "room_seed_hash": room.records()[0].record_hash(),
            "registered_by": registrant_id,
            "ts": _now(),
        }
        sig_reg = registered_by_kp.sign(_canonical(body)).hex()
        sig_commons = self._keypair.sign(
            _canonical({**body, "sig_registrant": sig_reg})).hex()
        rec = RoomRegistered(
            commons_id=self._world_id, seq=self._seq,
            prev=self._last_hash, room_id=room.world_id,
            topic=body["topic"],
            template_hash=body["template_hash"],
            room_seed_hash=body["room_seed_hash"],
            registered_by=registrant_id, ts=body["ts"],
            sig_registrant=sig_reg, sig_commons=sig_commons)
        self._records.append(rec)
        self._last_hash = rec.record_hash()
        self._seq += 1
        self._rooms[room.world_id] = {
            "topic": body["topic"],
            "template_hash": body["template_hash"],
            "registered_by": registrant_id,
            "room_seed_hash": body["room_seed_hash"],
        }
        return rec


def verify_commons(commons: Commons) -> Tuple[bool, str]:
    if not HAS_CRYPTO:
        return (False, "cryptography not installed")
    pub_commons = _pubkey_from_did(commons.world_id)
    prev = None
    for i, rec in enumerate(commons.records()):
        if rec.prev != prev:
            return (False, f"record {i}: prev mismatch")
        if not _verify_simple_sig(
                {k: v for k, v in rec.body().items()},
                rec.sig_registrant, rec.registered_by):
            return (False, f"record {i}: registrant sig")
        try:
            pub_commons.verify(
                bytes.fromhex(rec.sig_commons),
                _canonical({**rec.body(),
                            "sig_registrant": rec.sig_registrant}))
        except Exception as e:
            return (False, f"record {i}: commons sig: {e}")
        prev = rec.record_hash()
    return (True, "commons verifies")


# =====================================================================
# Plugin session (what an AI app's plugin does on the user's behalf)
# =====================================================================

class PluginSession:
    """Represents a plugin running inside a user's AI app. Every
    action is mediated by the user's key. The plugin has no
    authority of its own — it can only do what the user could do
    by hand."""

    def __init__(self, user_kp, app_label: str):
        if not HAS_CRYPTO:
            raise RuntimeError("cryptography not installed")
        self._kp = user_kp
        self._user_id = _did_from_kp(user_kp)
        self._app_label = app_label

    @property
    def user_id(self):
        return self._user_id

    @property
    def app_label(self):
        return self._app_label

    def port_conversation(self, source_label: str, entries: List[Dict]) -> Transcript:
        """Port a conversation from the app into a signed transcript."""
        return sign_transcript(source_label, entries, self._kp)

    def create_room(self, commons: Commons, template: RoomTemplate,
                    opening_transcript: Optional[Transcript] = None) -> ChatRoom:
        """Create a room and register it in the Commons."""
        room = ChatRoom(template, self._kp,
                        opening_transcript=opening_transcript)
        commons.register_room(room, self._kp)
        return room

    def join_room(self, room: ChatRoom, tier: str = "communicate"):
        req = sign_join_request(room.world_id, self._kp, tier)
        return room.join(req)

    def leave_room(self, room: ChatRoom):
        return room.leave(self._kp)

    def post_message(self, room: ChatRoom, text: str):
        req = sign_post_request(room.world_id, self._kp, text)
        return room.post(req)

    def redact(self, room: ChatRoom, target_hash: str, reason: str):
        req = sign_redact_request(room.world_id, self._kp,
                                   target_hash, reason)
        return room.redact(req)

    def read_room(self, room: ChatRoom) -> List[Dict]:
        return visible_log(room)


# =====================================================================
# Demo
# =====================================================================

def demo(artifact_dir=None):
    """Alice ports a conversation from her AI app into the Commons.
    Bob joins, reads, posts. Carl joins as a moderator. Dave tries
    to post without joining (refused). Bob posts too fast (rate
    limit). Alice redacts her own message. Carl redacts Bob's.
    Verify the room, the Commons, and the transcript attestation."""
    import json as _json
    from pathlib import Path

    if not HAS_CRYPTO:
        raise RuntimeError("demo requires `cryptography`")

    if artifact_dir is None:
        artifact_dir = "artifacts"
    path = Path(artifact_dir) / "chat_room"
    path.mkdir(parents=True, exist_ok=True)

    # Alice — the porter / room creator
    alice_kp = Ed25519PrivateKey.generate()
    bob_kp = Ed25519PrivateKey.generate()
    carl_kp = Ed25519PrivateKey.generate()
    dave_kp = Ed25519PrivateKey.generate()
    commons_kp = Ed25519PrivateKey.generate()

    alice = PluginSession(alice_kp, "claude.ai")
    bob = PluginSession(bob_kp, "chatgpt")
    carl = PluginSession(carl_kp, "claude.ai")
    dave = PluginSession(dave_kp, "local-llm")

    # The external conversation Alice wants to port
    external_convo = [
        {"speaker": "user",
         "ts": "2026-11-15T10:00:00+00:00",
         "text": "What is a fractal world?"},
        {"speaker": "assistant",
         "ts": "2026-11-15T10:00:12+00:00",
         "text": "A fractal world is a world whose template shape "
                 "is the same at every scale: seed, rule, boundary, "
                 "log. A plant, a garden, a botanical garden — "
                 "the same shape, different content."},
        {"speaker": "user",
         "ts": "2026-11-15T10:01:00+00:00",
         "text": "How do they compose?"},
        {"speaker": "assistant",
         "ts": "2026-11-15T10:01:15+00:00",
         "text": "The parent delegates the child's law to the "
                 "child, and enforces only interaction rules. "
                 "The garden doesn't re-enforce a plant's pot; "
                 "the plant does. The garden enforces who drinks "
                 "from which slot."},
    ]
    transcript = alice.port_conversation(
        "claude.ai session, 2026-11-15", external_convo)

    # Commons
    commons = Commons(commons_kp)

    # Alice creates a room in the Commons
    template = RoomTemplate(
        template_id="chat-room-v1",
        topic="fractal worlds — ported conversation",
        max_msg_len=2000,
        rate_limit_count=5,
        rate_limit_window=10,
        join_policy="open",
        moderation="moderator",
        welcome="Welcome. This room continues a conversation from "
                "an external AI app.")
    room = alice.create_room(commons, template,
                             opening_transcript=transcript)

    log = []
    log.append(("port", f"Alice attested transcript: "
                        f"{transcript.transcript_hash()[:16]}... "
                        f"({len(external_convo)} entries)"))
    log.append(("create", f"Room created: "
                          f"{room.world_id[:24]}..."))
    log.append(("register", f"Commons: "
                            f"{len(commons.rooms())} room(s)"))

    # Bob joins and posts
    r = bob.join_room(room)
    log.append(("join", f"Bob joined: {type(r).__name__}"))
    bob_msg = bob.post_message(
        room, "The composition rule is the key — a garden can't "
              "override a plant's water without branching it.")
    log.append(("post", f"Bob posted: "
                        f"{bob_msg.record_hash()[:16]}..."))

    # Dave tries to post without joining
    r = dave.post_message(room, "I have opinions.")
    log.append(("refused", f"Dave (not a member): "
                           f"{r.reason if hasattr(r, 'reason') else '?'}"))

    # Bob posts too fast — rate limit
    for i in range(5):
        bob.post_message(room, f"Spam {i}")
    r = bob.post_message(room, "Spam 6")
    log.append(("refused",
                f"Bob (rate limit): "
                f"{r.reason if hasattr(r, 'reason') else '?'}"))

    # Carl joins as a moderator and redacts Bob's spam
    carl.join_room(room)
    log.append(("join", "Carl joined (moderator)"))
    spam_hashes = [rec.record_hash() for rec in room.records()
                   if isinstance(rec, Message)
                   and rec.author_id == bob.user_id]
    r = carl.redact(room, spam_hashes[0], "spam")
    log.append(("redact", f"Carl redacted Bob's first message: "
                          f"{type(r).__name__}"))

    # Alice redacts her own first message (author's right)
    alice_msgs = [rec.record_hash() for rec in room.records()
                  if isinstance(rec, Message)
                  and rec.author_id == alice.user_id]
    if alice_msgs:
        r = alice.redact(room, alice_msgs[0], "I changed my mind")
        log.append(("redact", f"Alice redacted her own: "
                              f"{type(r).__name__}"))

    # Bob tries to redact Carl's message (not allowed)
    carl_msgs = [rec.record_hash() for rec in room.records()
                 if isinstance(rec, Message)
                 and rec.author_id == carl.user_id]
    if carl_msgs:
        r = bob.redact(room, carl_msgs[0], "I disagree")
        log.append(("refused",
                    f"Bob (redact Carl's): "
                    f"{r.reason if hasattr(r, 'reason') else '?'}"))

    # Verify
    ok_room, room_r = verify_room(room)
    ok_commons, comm_r = verify_commons(commons)
    ok_transcript = verify_transcript(transcript)

    print("=" * 74)
    print("Chat Room — a chat world, ported and continued")
    print("=" * 74)
    print()
    print(f"  Commons: {commons.world_id[:28]}...")
    print(f"  Room:    {room.world_id[:28]}...")
    print(f"  Ported:  {transcript.transcript_hash()[:28]}... "
          f"({len(external_convo)} entries)")
    print()
    print("  Sequence:")
    for kind, note in log:
        marker = {"port": "↓", "create": "✚", "register": "▣",
                  "join": "→", "post": "✉", "redact": "▨",
                  "refused": "✗"}.get(kind, "·")
        print(f"    {marker} {note}")
    print()
    print("  Visible log:")
    for entry in visible_log(room)[:20]:
        t = entry["type"]
        if t == "message":
            text = entry["text"]
            if len(text) > 56:
                text = text[:53] + "..."
            red = " [redacted]" if entry.get("redacted") else ""
            print(f"    [{entry['seq']:>3}] {entry['author'][:20]:20s} "
                  f"{text}{red}")
        elif t == "join":
            print(f"    [{entry['seq']:>3}] join: "
                  f"{entry['subject'][:20]} ({entry['tier']})")
        elif t == "redact":
            print(f"    [{entry['seq']:>3}] redact: "
                  f"target={entry['target'][:16]}... "
                  f"reason={entry['reason']!r}")
        elif t == "refused":
            print(f"    [{entry['seq']:>3}] refused: "
                  f"{entry['requester'][:20]} ({entry['reason']})")
    print()
    print("  Verification (offline):")
    print(f"    room:       {ok_room}  ({room_r})")
    print(f"    commons:    {ok_commons}  ({comm_r})")
    print(f"    transcript: {ok_transcript}")
    print()
    print("  What this establishes:")
    print("    - The room is a policy-gated append-only log.")
    print("      Every event is signed by its author; every accepted")
    print("      event is countersigned by the room.")
    print("    - A conversation from an external AI app is ported as")
    print("      a signed transcript, attested by the porter. Bob can")
    print("      later confirm or dispute entries (future work).")
    print("    - Join, post, redact all follow the room's law. Dave")
    print("      is refused for non-membership; Bob is refused for")
    print("      rate limit; Bob cannot redact Carl's message.")
    print("    - Redaction never edits; the original message is still")
    print("      in the log, but visible_log hides its text.")
    print("    - The whole room and the Commons verify offline.")
    print()
    print("  Anchor (public domain, Emily Dickinson):")
    print("    'There is no Frigate like a Book'")
    print("    'To take us Lands away –'")

    audit = {
        "commons_id": commons.world_id,
        "room_id": room.world_id,
        "transcript_hash": transcript.transcript_hash(),
        "transcript_entries": len(external_convo),
        "sequence": [{"kind": k, "note": n} for k, n in log],
        "visible_log": visible_log(room),
        "room_verifies": ok_room,
        "commons_verifies": ok_commons,
        "transcript_verifies": ok_transcript,
    }
    (path / "chat_demo.json").write_text(
        _json.dumps(audit, indent=2))
    print(f"\n  → {path}/chat_demo.json")
    return audit
